#!/usr/bin/env python3
import numpy as np
import yfinance as yf
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import os
csvPath = Path("data/spy.csv")

if csvPath.is_file():
    print("Data already downloaded")
    csvPath.parent.mkdir(exist_ok=True)
    px = pd.read_csv("data/spy.csv", index_col=0, parse_dates=True).squeeze("columns")
else:
    print("No csv found. Downloading")
    px = yf.download('SPY', start="2005-01-01", auto_adjyst=True)["Close"].squeeze("columns")
    px.to_csv("data/spy.csv")

ret = px.pct_change()
ret = ret.fillna(0.0)
equity = (1 + ret).cumprod()
assert np.isclose(equity.iloc[-1], px.iloc[-1] / px.iloc[0])
print("Check passed")

fast = px.rolling(50).mean()
slow = px.rolling(200).mean()

