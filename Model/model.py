from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from data.clean import data_clean, data

def init_model():

    model = Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("clf", LogisticRegression())
    ])

    return model

def train(model, X, y):

    model.fit(X,y)

    return model

def pred(model, text):

    return model.predict([text])[0]
