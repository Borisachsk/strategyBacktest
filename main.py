#!/usr/bin/env python3
import numpy as np
import yfinance as yf
from pathlib import Path
import pandas as pd
csvPath = Path("data/spy.csv")

if csvPath.is_file():
    print("Data already downloaded")
    px = pd.read_csv("data/spy.csv", index_col=0, parse_dates=True).squeeze()
else:
    print("No csv found. Downloading")
    px = yf.download('SPY', start="2005-01-01")["Close"].squeeze()
    px.to_csv("data/spy.csv")
print(type(px), px.index.dtype, len(px))
