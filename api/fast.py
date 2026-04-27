import pickle
import os
import json
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data.preprocessing import clean, translate_if_needed, load_translate_model
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent

MODEL_PATH = "model/model_SVC.pkl"

class PredictRequest(BaseModel):
    text_to_analyze: str
    source: str = "streamlit_txt"

class ChromeRequest(BaseModel):
    url: str

class FactCheckRequest(BaseModel):
    text_to_analyze: str
    row_index: int = None

class FeedbackRequest(BaseModel):
    row_index: int
    feedback: str

app = FastAPI()
label_mapping = {0: "REAL", 1: "FAKE"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

with open(MODEL_PATH, "rb") as f:
    app.state.model = pickle.load(f)

with open("api/fact_check_prompt.txt", "r") as f:
    FACT_CHECK_PROMPT = f.read()

app.state.translator_model = None
app.state.translator_tokenizer = None

# Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
gcp_creds = os.getenv("GCP_SERVICE_ACCOUNT")
if gcp_creds:
    creds_json = json.loads(gcp_creds)
    creds = Credentials.from_service_account_info(creds_json, scopes=scope)
    gs_client = gspread.authorize(creds)
    sheet2 = gs_client.open("FakeNewsDB").worksheet("Sheet2")
else:
    sheet2 = None

def log_analysis(url, text, verdict, confidence, source):
    if sheet2 is None:
        return None
    try:
        sheet2.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            url,
            text[:500],
            verdict,
            confidence,
            source,
            "",     # feedback vide
            False   # fact_check
        ])
        return len(sheet2.get_all_values())
    except Exception:
        return None


@app.get("/")
def root():
    return {"greeting": "Hello"}


# PREDICT TF-IDF
@app.post("/predict")
def predict(request: PredictRequest):
    if app.state.translator_model is None:
        app.state.translator_model, app.state.translator_tokenizer = load_translate_model()
    model = app.state.model
    translate = translate_if_needed(request.text_to_analyze, app.state.translator_model, app.state.translator_tokenizer)
    cleaned = clean(translate)
    proba = model.predict_proba([cleaned])[0]
    confidence = round(float(max(proba)), 4)
    label = label_mapping[int(model.predict([cleaned])[0])]
    verdict = "NON CONCLUANT" if confidence < 0.85 else label
    row_index = log_analysis("", request.text_to_analyze, verdict, confidence, request.source)
    return {"Verdict": verdict, "Indice de confiance": confidence, "Label": label, "row_index": row_index}


# PREDICT CHROME
@app.post("/predict_chrome")
def predict_chrome(request: ChromeRequest):
    if app.state.translator_model is None:
        app.state.translator_model, app.state.translator_tokenizer = load_translate_model()
    import requests as req
    from bs4 import BeautifulSoup
    response_url = req.get(request.url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})
    soup = BeautifulSoup(response_url.content, "lxml")
    text = " ".join([p.text for p in soup.find_all("p")])
    translated = translate_if_needed(text, app.state.translator_model, app.state.translator_tokenizer)
    cleaned = clean(translated)
    proba = app.state.model.predict_proba([cleaned])[0]
    confidence = round(float(max(proba)), 4)
    label = label_mapping[int(app.state.model.predict([cleaned])[0])]
    verdict = "NON CONCLUANT" if confidence < 0.85 else label
    row_index = log_analysis(request.url, text, verdict, confidence, "chrome")
    return {"Verdict": verdict, "Indice de confiance": confidence, "Label": label, "row_index": row_index}


# FACT CHECK
@app.post("/fact_check")
def fact_check(request: FactCheckRequest):
    if request.row_index and sheet2:
        try:
            sheet2.update_cell(request.row_index, 8, True)
        except Exception:
            pass

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"))
    search_tool = TavilySearchResults(max_results=5)
    fact_checker = create_react_agent(llm, [search_tool], state_modifier=FACT_CHECK_PROMPT)
    result = fact_checker.invoke({"messages": [("user", f"Classification ML : FAKE\n\nArticle : {request.text_to_analyze}")]})

    last_message = result["messages"][-1]
    if isinstance(last_message.content, list):
        for block in last_message.content:
            if isinstance(block, dict) and block.get("type") == "text":
                return {"result": block["text"]}
    return {"result": last_message.content}


# FEEDBACK
@app.post("/feedback")
def feedback(request: FeedbackRequest):
    if sheet2:
        try:
            sheet2.update_cell(request.row_index, 7, request.feedback)
        except Exception:
            pass
    return {"status": "ok"}
