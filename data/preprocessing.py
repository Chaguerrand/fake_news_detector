import re
import string
import os
import json
from google.cloud import translate_v2 as translate
from google.oauth2.service_account import Credentials

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

def translate_if_needed(text):
    if not text or len(text.strip()) < 10:
        return text
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return text
    import requests as req
    response = req.post(
        "https://translation.googleapis.com/language/translate/v2",
        params={"key": api_key},
        json={"q": text, "target": "en", "source": "fr", "format": "text"}
    )
    response.raise_for_status()
    return response.json()["data"]["translations"][0]["translatedText"]
