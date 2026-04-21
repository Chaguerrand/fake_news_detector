import os
import pickle
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langdetect import detect, DetectorFactory
from data.preprocessing import data_preprocessing
from api.schemas import PredictRequest, PredictResponse

DetectorFactory.seed = 42

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = os.getenv("MODEL_PATH", "models/model.pkl")

with open(MODEL_PATH, "rb") as f:
    app.state.model = pickle.load(f)

@app.get("/")
def root():
    return {"greeting": "Hello"}

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    model = app.state.model
    cleaned = data_preprocessing(request.text)

    predict_label = model.predict([cleaned])[0]
    proba = model.predict_proba([cleaned])[0]
    predict_score = round(float(max(proba)), 4)

    try:
        predict_langue = detect(request.text)
    except Exception:
        predict_langue = "inconnue"

    return {"Verdict": str(predict_label), "Indice de confiance": predict_score, "Langue": predict_langue}
