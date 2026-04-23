import pandas as pd
import os

DATA_PATH = os.getenv("DATA_PATH", "../raw_data/WELFake_Dataset.csv")

df = pd.read_csv("/Users/alexdelrieu/code/Chaguerrand/fake_news_detector/raw_data/WELFake_Dataset.csv")
data = df.copy()
