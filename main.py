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

cost = 0.001
ret_noncost = backtest(ret, signal, 0.0)
ret_cost = backtest(ret, signal, cost)
ret2 = backtest(ret,signal2,cost)

eq_bh = equity_curve(ret)
eq_strat = equity_curve(ret_noncost)
eq_leaky = equity_curve(signal * ret)
eq_strat_commission = equity_curve(ret_cost)

position = signal.shift(1).fillna(0.0)
position2 = signal2.shift(1).fillna(0.0)

ones = pd.Series(1.0, index=ret.index)

results = {
    "Buy&Hold": metrics(ret,ones),
    "Со сдвигом": metrics(ret_noncost, position),
    "Без сдвига": metrics(signal * ret, signal),
    "C Коммисией": metrics(ret_cost, position),
    "MA 20/100": metrics(ret2,position2)
}

print(f"Buy&Hold: {eq_bh.iloc[-1]:.2f} |"
      f"Со сдвигом: {eq_strat.iloc[-1]:.2f} |"
      f"без сдвига: {eq_leaky.iloc[-1]:.2f} |"
      f"С коммисией: {eq_strat_commission.iloc[-1]:.2f}")

print(pd.DataFrame(results).round(3))

plt.figure(figsize=(12, 6))
eq_bh.plot(label="Buy & hold")
eq_strat.plot(label="MA 50/200 (со сдвигом)")
eq_leaky.plot(label="MA 50/200 (без сдвига, нечестно)")
eq_strat_commission.plot(label="MA 50/200 (со сдвигом и коммисией)")
plt.title(ticker)
plt.yscale("log")
plt.legend()
plt.show()
