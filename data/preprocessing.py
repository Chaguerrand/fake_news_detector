import re
import string
from langdetect import detect
from transformers import MarianMTModel, MarianTokenizer

def clean(text):
    text = text.strip().lower()
    for p in string.punctuation:
        text = text.replace(p, '')
    text = ' '.join(text.split(' '))
    text = re.sub('<[^<]+?>', '', text)
    text = text.replace('\n','')
    return text

def data_clean():
    from utils import data
    df = data.copy()
    df = df.fillna("")
    df["article"] = df["title"] + " " + df["text"]
    df["article"] = df["article"].apply(clean)
    return df["article"]

def load_translate_model():
    model_name = "Helsinki-NLP/opus-mt-fr-en"
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)
    return model, tokenizer

def translate_if_needed(text, model, tokenizer):
    if not text or len(text.strip()) < 10:  # texte trop court = rien à détecter
        return text
    lang = detect(text)
    print("Langue détectée :", lang)
    if lang == "fr":
        inputs = tokenizer(text, return_tensors="pt", padding=True)
        outputs = model.generate(**inputs)
        return tokenizer.decode(outputs[0], skip_special_tokens=True)
    else:
        return text
