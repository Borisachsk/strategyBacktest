#!/usr/bin/env python3
import numpy as np
import yfinance as yf
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import os

def equity_curve(returns):
    return (1 + returns).cumprod()

def load_prices(ticker, startpoint):
    csvPath = Path(f"data/{ticker}-{startpoint}.csv")
    csvPath.parent.mkdir(exist_ok=True)
    if csvPath.is_file():
        print("Data already downloaded")
        px = pd.read_csv(csvPath, index_col=0, parse_dates=True).squeeze("columns")
    else:
        print("No csv found. Downloading")
        px = yf.download(ticker, start=startpoint, auto_adjust=True)["Close"].squeeze("columns")
        px.to_csv(csvPath)
    return px

def rolling_strategy(prices,fast_window,slow_window):
    fast = prices.rolling(fast_window).mean()
    slow = prices.rolling(slow_window).mean()
    return (fast > slow).astype(float)

def backtest(ret, signal, commission_cost):
    position = signal.shift(1).fillna(0.0)
    commission = abs(position.diff()).fillna(0.0) * commission_cost
    return position * ret - commission

print("Input the ticker(default: SPY)")
ticker = input().strip().upper() or "SPY"

print("Input the start point(default: 2005-01-01)")
startpoint = input().strip() or "2005-01-01"

px = load_prices(ticker, startpoint)
ret = px.pct_change()
ret = ret.fillna(0.0)

equity = equity_curve(ret)

assert np.isclose(equity.iloc[-1], px.iloc[-1] / px.iloc[0])

print("Check passed")

signal = rolling_strategy(px,50,200)
cost = 0.0001


eq_bh = equity_curve(ret)
eq_strat = equity_curve(backtest(ret,signal, 0.0))
eq_leaky = equity_curve(signal * ret)
eq_strat_commission = equity_curve(backtest(ret,signal,cost))

print(f"Buy&Hold: {eq_bh.iloc[-1]:.2f} |"
      f"Со сдвигом: {eq_strat.iloc[-1]:.2f} |"
      f"без сдвига: {eq_leaky.iloc[-1]:.2f} |"
      f"С коммисией: {eq_strat_commission.iloc[-1]:.2f}")
plt.figure(figsize=(12, 6))
eq_bh.plot(label="Buy & hold")
eq_strat.plot(label="MA 50/200 (со сдвигом)")
eq_leaky.plot(label="MA 50/200 (без сдвига, нечестно)")
eq_strat_commission.plot(label="MA 50/200 (со сдвигом и коммисией)")
plt.title(ticker)
plt.yscale("log")
plt.legend()
plt.show()
