import pandas as pd

DATA_PATH = os.getenv("DATA_PATH", "raw_data/WELFake_Dataset.csv")

df = pd.read_csv(DATA_PATH)
data = df.copy()
