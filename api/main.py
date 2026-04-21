from fastapi import FastAPI, HTTPException
from api.schemas import PredictRequest, PredictResponse
from api.predict import predict, load_model

app = FastAPI(title="Fake News Detector API", version="1.0.0")

@app.on_event("startup")
def startup_event():
    load_model()

@app.get("/")
def root():
    return {"message": "En cours"}

@app.post("/predict", response_model=PredictResponse)
def predict_route(request: PredictRequest):
    try:
        return predict(request.text)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de prédiction : {e}")
