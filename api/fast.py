import pickle
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data.preprocessing import clean, translate_if_needed, load_translate_model
#from model.model_hf import load_model_hf, pred_hf

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

app.state.translator_model, app.state.translator_tokenizer = load_translate_model()

@app.get("/")
def root():
    return {"greeting": "Hello"}


#PREDICT TF-IDF
@app.post("/predict")
def predict(request: PredictRequest):
    model = app.state.model
    translate = translate_if_needed(request.text_to_analyze, app.state.translator_model, app.state.translator_tokenizer)
    cleaned = clean(translate)
    predict_label = label_mapping[int(model.predict([cleaned])[0])]
    proba = model.predict_proba([cleaned])[0]
    predict_score = round(float(max(proba)), 4)

    return {"Verdict": str(predict_label), "Indice de confiance": predict_score}

@app.post("/predict_chrome")
def predict_chrome(request: ChromeRequest):
    from newspaper import Article
    art = Article(request.url)
    art.download()
    art.parse()
    text = art.text
    translated = translate_if_needed(text, app.state.translator_model, app.state.translator_tokenizer)
    cleaned = clean(translated)
    predict_label = label_mapping[int(app.state.model.predict([cleaned])[0])]
    proba = app.state.model.predict_proba([cleaned])[0]
    predict_score = round(float(max(proba)), 4)
    return {"Verdict": str(predict_label), "Indice de confiance": predict_score}




#PREDICT BERT
# @app.post("/predict_bert")
# def predict_bert(request: PredictRequest):
#     result_hf = pred_hf(app.state.model_hf, app.state.tokenizer, request.text_to_analyze)
#     return {"Verdict": result_hf["label"], "Indice de confiance": result_hf["confidence"]}

#ajouter les feedbacks quand on les incluera
