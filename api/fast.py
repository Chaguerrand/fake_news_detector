import pickle
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data.preprocessing import clean, translate_if_needed, load_translate_model
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent

MODEL_PATH="model/model_SVC.pkl"

class PredictRequest(BaseModel):
    text_to_analyze: str

class ChromeRequest(BaseModel):
    url: str

class FactCheckRequest(BaseModel):
    text_to_analyze: str

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


@app.get("/")
def root():
    return {"greeting": "Hello"}


#PREDICT TF-IDF
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
    return {"Verdict": verdict, "Indice de confiance": confidence, "Label": label}

#PREDICT CHROME
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
    return {"Verdict": verdict, "Indice de confiance": confidence, "Label": label}


#FACT CHECK
@app.post("/fact_check")
def fact_check(request: FactCheckRequest):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"))
    search_tool = TavilySearchResults(max_results=5)
    fact_checker = create_react_agent(llm, [search_tool], prompt=FACT_CHECK_PROMPT)
    result = fact_checker.invoke({"messages": [("user", f"Classification ML : FAKE\n\nArticle : {request.text_to_analyze}")]})

    last_message = result["messages"][-1]
    if isinstance(last_message.content, list):
        for block in last_message.content:
            if isinstance(block, dict) and block.get("type") == "text":
                return {"result": block["text"]}
    return {"result": last_message.content}
