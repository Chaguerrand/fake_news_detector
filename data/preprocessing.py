import re
import string

def data_preprocessing(text):

    text = text.strip().lower()
    for p in string.punctuation:
        text = text.replace(p, '')
    text = ' '.join(text.split(' '))
    text = re.sub('<[^<]+?>', '', text)
    text = text.replace('\n','')

    return text
