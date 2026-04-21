import pickle
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data.preprocessing import clean

label_mapping = {0: "REAL", 1: "FAKE"}

class PredictRequest(BaseModel):
    text_to_analyze: str

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

@app.get("/")
def root():
    return {"greeting": "Hello"}

@app.post("/predict")
def predict(request: PredictRequest):
    model = app.state.model
    cleaned = clean(request.text_to_analyze)

    predict_label = label_mapping[int(model.predict([cleaned])[0])]
    proba = model.predict_proba([cleaned])[0]
    predict_score = round(float(max(proba)), 4)

    return {"Verdict": str(predict_label), "Indice de confiance": predict_score}


#ajouter les feedbacks quand on les incluera
