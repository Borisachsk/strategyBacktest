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

def turtle_trading(prices,entry_window,exit_window):
    upper = prices.rolling(entry_window).max().shift(1)
    lower = prices.rolling(exit_window).min().shift(1)
    entry = prices > upper
    exit_ = prices < lower
    signal = pd.Series(np.nan, index=prices.index)
    signal[entry] = 1.0
    signal[exit_] = 0.0
    signal = signal.ffill()
    signal = signal.fillna(0.0)
    return signal

def backtest(ret, signal, commission_cost):
    position = signal.shift(1).fillna(0.0)
    commission = abs(position.diff()).fillna(0.0) * commission_cost
    return position * ret - commission

def metrics(returns, positions):
    equity = equity_curve(returns)
    cagr = equity.iloc[-1]**(1/(len(equity)/252)) - 1
    maxdd = (equity / equity.cummax() - 1).min()
    mean = returns.mean()
    std = returns.std()
    sharpe = mean / std * np.sqrt(252)
    trades = (abs(positions.diff()).fillna(0.0) > 0).sum()
    return {"CAGR": cagr, "MaxDD": maxdd, "Sharpe": sharpe,"Trades": trades}

def strategy(ret,signal,cost):
    position = signal.shift(1).fillna(0.0)
    ret_cost = backtest(ret,signal,cost)
    return metrics(ret_cost,position)

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

cost = 0.001

signals = {
    "MA 50/200": rolling_strategy(px,50,200),
    "MA 20/100": rolling_strategy(px,20,100),
    "Turtle 55/20": turtle_trading(px,55,20),
}

ones = pd.Series(1.0, index=ret.index)
results = {"Buy&Hold": metrics(ret,ones)}
equities = {"Buy&Hold": equity_curve(ret)}

for name, sig in signals.items():
    equities[name] = equity_curve(backtest(ret,sig,cost))
    results[name] = strategy(ret,sig,cost)


print(pd.DataFrame(results).round(3))

plt.figure(figsize=(12, 6))
for name, curve in equities.items():
    curve.plot(label=name)
plt.title(ticker)
plt.yscale("log")
plt.legend()
plt.show()
