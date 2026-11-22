#!/usr/bin/env python3
import numpy as np
import yfinance as yf
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import os

def equity_curve(returns):
    return (1 + returns).cumprod()

print("Input the ticker(default: SPY)")
ticker = input().strip().upper() or "SPY"

print("Input the start point(default: 2005-01-01)")
startpoint = input() or "2005-01-01"

csvPath = Path(f"data/{ticker}-{startpoint}.csv")
csvPath.parent.mkdir(exist_ok=True)

if csvPath.is_file():
    print("Data already downloaded")
    px = pd.read_csv(f"data/{ticker}-{startpoint}.csv", index_col=0, parse_dates=True).squeeze("columns")
else:
    print("No csv found. Downloading")
    px = yf.download(ticker, start=startpoint, auto_adjust=True)["Close"].squeeze("columns")
    px.to_csv(f"data/{ticker}-{startpoint}.csv")

ret = px.pct_change()
ret = ret.fillna(0.0)
equity = (1 + ret).cumprod()
assert np.isclose(equity.iloc[-1], px.iloc[-1] / px.iloc[0])
print("Check passed")

fast = px.rolling(50).mean()
slow = px.rolling(200).mean()

signal = (fast > slow).astype(float)

position = signal.shift(1).fillna(0.0)

cost = 0.001
commission = abs(position.diff()).fillna(0.0) * cost

strat_ret = position * ret
leaky_ret = signal * ret
strat_ret_commission = position * ret - commission


eq_bh = equity_curve(ret)
eq_strat = equity_curve(strat_ret)
eq_leaky = equity_curve(leaky_ret)
eq_strat_commission = equity_curve(strat_ret_commission)

print(f"Buy&Hold: {eq_bh.iloc[-1]:.2f} |"
      f"Со сдвигом: {eq_strat.iloc[-1]:.2f} |"
      f"без сдвига: {eq_leaky.iloc[-1]:.2f} |"
      f"С коммисией: {eq_strat_commission.iloc[-1]:.2f}")
plt.figure(figsize=(12, 6))
eq_bh.plot(label="Buy & hold")
eq_strat.plot(label="MA 50/200 (со сдвигом)")
eq_leaky.plot(label="MA 50/200 (без сдвига, нечестно)")
eq_strat_commission.plot(label="MA 50/200 (со сдвигом и коммисией)")

plt.yscale("log")
plt.legend()
plt.show()
