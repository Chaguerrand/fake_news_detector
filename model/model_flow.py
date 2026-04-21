import mlflow
import mlflow.sklearn

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

from data.preprocessing import data_clean
from utils import data


# ---------------------------
# MODEL
# ---------------------------

def build_model():
    return Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("clf", LogisticRegression(max_iter=1000))
    ])


# ---------------------------
# TRAIN
# ---------------------------

def train():

    X = data_clean()
    y = data["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42
    )

    model = build_model()
    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    acc = accuracy_score(y_test, preds)
    f1 = f1_score(y_test, preds, average="weighted")

    return model, acc, f1


# ---------------------------
# MAIN + MLFLOW
# ---------------------------

if __name__ == "__main__":

    mlflow.set_experiment("fake_news")

    model, acc, f1 = train()

    with mlflow.start_run():

        # 🔥 metrics
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1", f1)

        # 🔥 model
        mlflow.sklearn.log_model(model, "model")

        print("🚀 Training terminé")
        print("📊 accuracy:", acc)
        print("📊 f1:", f1)
