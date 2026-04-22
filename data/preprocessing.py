import re
import string
from utils import data
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

    df = data.copy()

    df = df.fillna("")
    df["article"] = df["title"] + " " + df["text"]

    df["article"] = df["article"].apply(clean)

    return df["article"]

def translate_if_needed(text):

    model_name = "Helsinki-NLP/opus-mt-fr-en"

    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)
    lang = detect(text)

    print("Langue détectée :", lang)

    if lang == "fr":
        inputs = tokenizer(text, return_tensors="pt", padding=True)
        outputs = model.generate(**inputs)
        return tokenizer.decode(outputs[0], skip_special_tokens=True)

    else:
        return text
