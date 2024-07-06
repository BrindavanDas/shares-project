import yfinance as yf
import pandas as pd
import DatabaseUpdater
from tkinter import Tk, filedialog

root = Tk()
root.withdraw()
input_file = filedialog.askopenfilename()

df = pd.read_excel(input_file)

df["share_name"] = df["code"].apply(lambda x: yf.Ticker(x).info["longName"])

df = df[["share_name", "code"]]

print(df)

df.to_excel("F:\Projects\shares\data.xlsx", index=False)
