# SwingTrade
This project is a Python-based automated trading bot that leverages the Alpaca API for order execution and Yahoo Finance for real-time stock data. The bot uses a Relative Strength Index (RSI), MACD and Momentum-based strategy to identify potential buy and sell signals.

Key Features:
Calculates RSI (Relative Strength Index) to detect overbought/oversold conditions.
Computes Momentum to gauge price trend direction.
Finds MACD and adds as a condition to trade when it crosses above trading line.

Automatically executes trades via Alpaca API.
Limits trades to 10 per day to manage risk.
Runs continuously and resets trading count daily.
Fetches real-time stock data using Yahoo Finance.

Currently working on:
Optimizing for specific market conditions
Backtesting
