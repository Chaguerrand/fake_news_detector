from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from preprocessing import data_preprocessing
from utils import data
import pickle

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


if __name__ == '__main__':
    X = data["title"].apply(data_preprocessing)
    y = data["label"]

    model = init_model()
    model = train(model, X, y)

    with open("models/model.pkl", "wb") as f:
        pickle.dump(model, f)
