import re
import string
import os
import json
from langdetect import detect
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

def load_translate_model():
    # Plus utilisé — conservé pour ne pas casser fast.py
    return None, None

def translate_if_needed(text, model=None, tokenizer=None):
    if not text or len(text.strip()) < 10:
        return text
    lang = detect(text)
    print("Langue détectée :", lang)
    if lang == "fr":
        gcp_creds = os.getenv("GCP_SERVICE_ACCOUNT")
        if not gcp_creds:
            return text
        creds_json = json.loads(gcp_creds)
        creds = Credentials.from_service_account_info(creds_json)
        client = translate.Client(credentials=creds)
        result = client.translate(text, target_language="en", source_language="fr")
        return result["translatedText"]
    return text
