import re
import string
from utils import data

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
