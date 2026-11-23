#!/usr/bin/env python3
import numpy as np
import yfinance as yf
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

Path("plots").mkdir(exist_ok=True)

def equity_curve(returns):
    return (1 + returns).cumprod()

def load_prices(ticker, startpoint):
    csvPath = Path(f"data/{ticker}-{startpoint}.csv")
    csvPath.parent.mkdir(exist_ok=True)
    if csvPath.is_file():
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

def metrics_count(all_results,metrics_name):
    metrics_table = {}
    for ticker, results in all_results.items():
        row = {}
        for name, m in results.items():
            row[name] = m[metrics_name]
        metrics_table[ticker] = row
    return metrics_table

def run_ticker(ticker,startpoint,cost):
    px = load_prices(ticker,startpoint)
    ret = px.pct_change().fillna(0.0)
    signals = {
        "MA 50/200": rolling_strategy(px,50,200),
        "MA 20/100": rolling_strategy(px,20,100),
        "Turtle 55/20": turtle_trading(px,55,20),
    }
    equities = {"Buy&Hold": equity_curve(ret)}

    ones = pd.Series(1.0,index=ret.index)
    results = {"Buy&Hold": metrics(ret,ones)}

    for name, sig in signals.items():
        results[name] = strategy(ret,sig,cost)
        equities[name] = equity_curve(backtest(ret,sig,cost))
    return results,equities

def plot_ticker(ticker,equities,filename=None, show=True):
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12,8), sharex=True, gridspec_kw={"height_ratios": [3,1]})

    for name, curve in equities.items():
        dd = curve / curve.cummax() - 1
        if name == "Buy&Hold":
            ax1.plot(curve.index, curve, label=name, color="black", linewidth=1)
            ax2.fill_between(dd.index, dd, 0, color="gray", alpha=0.3)
        else:
            ax1.plot(curve.index, curve, label=name, linewidth=1.5)
            ax2.plot(dd.index, dd, linewidth=1.2)

    ax1.set_yscale("log")
    ax1.set_title(f"{ticker}: Equity(log scale)")
    ax1.set_ylabel("Equity")
    ax1.grid(True,alpha=0.3)
    ax1.legend(loc="upper left")

    ax2.set_title("Drawdown (grey filling: Buy&Hold)")
    ax2.set_ylabel("Drawdown")
    ax2.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    if filename:
        fig.savefig(filename,dpi=150,bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)

tickers = ["SPY","QQQ","GLD","TLT","EEM"]
startpoint = "2005-01-01"
cost = 0.001

all_results = {}
all_equities = {}
for ticker in tickers:
    all_results[ticker], all_equities[ticker] = run_ticker(ticker,startpoint,cost)

print("Sharpe")
print(pd.DataFrame(metrics_count(all_results,"Sharpe")).round(3))
print("")
print("MaxDD")
print(pd.DataFrame(metrics_count(all_results,"MaxDD")).round(3))
print("")
print("CAGR")
print(pd.DataFrame(metrics_count(all_results,"CAGR")).round(3))
print("")
print("Trades")
print(pd.DataFrame(metrics_count(all_results,"Trades")).round(3))

for ticker in tickers:
    plot_ticker(ticker,all_equities[ticker],filename=f"plots/{ticker}.png", show=False)
plot_ticker("SPY", all_equities["SPY"])
