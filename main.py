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
signal2 = rolling_strategy(px,20,100)
signal3 = turtle_trading(px,20,10)

cost = 0.001
ret_noncost = backtest(ret, signal, 0.0)
ret_cost = backtest(ret, signal, cost)
ret2 = backtest(ret,signal2,cost)
ret3 = backtest(ret,signal3, cost)

eq_bh = equity_curve(ret)
eq_ma50200 = equity_curve(ret_cost)
eq_ma20100 = equity_curve(ret2)
eq_turtle_trading = equity_curve(ret3)

position = signal.shift(1).fillna(0.0)
position2 = signal2.shift(1).fillna(0.0)
position3 = signal3.shift(1).fillna(0.0)

ones = pd.Series(1.0, index=ret.index)

results = {
    "Buy&Hold": metrics(ret,ones),
    "MA 50/200": metrics(ret_cost, position),
    "MA 20/100": metrics(ret2,position2),
    "Turtle Trading": metrics(ret3,position3)
}

print(f"Buy&Hold: {eq_bh.iloc[-1]:.2f} | "
      f"MA 50/200: {eq_ma50200.iloc[-1]:.2f} | "
      f"MA 20/100: {eq_ma20100.iloc[-1]:.2f} | "
      f"Turtle Trading: {eq_turtle_trading.iloc[-1]:.2f}")

print(pd.DataFrame(results).round(3))

plt.figure(figsize=(12, 6))
eq_bh.plot(label="Buy & hold")
eq_ma50200.plot(label="MA 50/200")
eq_ma20100.plot(label="MA 20/100")
eq_turtle_trading.plot(label="Turtle trading")
plt.title(ticker)
plt.yscale("log")
plt.legend()
plt.show()
