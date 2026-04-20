import os
import joblib
from langdetect import detect, DetectorFactory
from data.preprocessing import data_preprocessing
from model.model import pred

DetectorFactory.seed = 42

MODEL_PATH = os.getenv("MODEL_PATH", "models/model.joblib")

pipeline = None

def load_model():
    global pipeline
    try:
        pipeline = joblib.load(MODEL_PATH)
        print(f"✅ Modèle chargé depuis {MODEL_PATH}")
    except Exception as e:
        print(f"⚠️ Impossible de charger le modèle : {e}")

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "unknown"

def predict(text: str) -> dict:
    if pipeline is None:
        raise RuntimeError("Modèle non chargé. Vérifiez MODEL_PATH.")

    cleaned = data_preprocessing(text)
    label = pred(pipeline, cleaned)
    proba = pipeline.predict_proba([cleaned])[0]
    score = round(float(max(proba)), 4)

    return {
        "label": str(label),
        "score": score,
        "lang":  detect_language(text),
    }
