import pandas as pd
import os

DATA_PATH = os.getenv("DATA_PATH", "raw_data/WELFake_Dataset.csv")

def load_data():
    return pd.read_csv(DATA_PATH).copy()
