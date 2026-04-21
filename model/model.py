from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from data.preprocessing import data_clean
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

def train_final():
    y = data['label']
    X = data_clean()

    model = init_model()
    model = train(model, X, y)

    print("modèle entraîné")

    return model


if __name__ == "__main__":
    print("START TRAIN")
    model = train_final()

    with open("model/model.pkl", "wb") as f:
        pickle.dump(model, f)
