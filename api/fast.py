import pickle
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data.preprocessing import clean, translate_if_needed, load_translate_model

label_mapping = {0: "REAL", 1: "FAKE"}


class PredictRequest(BaseModel):
    text_to_analyze: str


class ChromeRequest(BaseModel):
    url: str


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("model/model.pkl", "rb") as f:
    app.state.model = pickle.load(f)

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
    response_url = req.get(request.url)
    soup = BeautifulSoup(response_url.content, "lxml")
    text = " ".join([p.text for p in soup.find_all("p")])
    translated = translate_if_needed(text, app.state.translator_model, app.state.translator_tokenizer)
    cleaned = clean(translated)
    proba = app.state.model.predict_proba([cleaned])[0]
    confidence = round(float(max(proba)), 4)
    label = label_mapping[int(app.state.model.predict([cleaned])[0])]
    verdict = "NON CONCLUANT" if confidence < 0.85 else label
    return {"Verdict": verdict, "Indice de confiance": confidence, "Label": label}
