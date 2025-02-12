import alpaca_trade_api as tradeapi
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Alpaca API credentials
ALPACA_API_KEY = 'PKX3NNMATUOO2MA4JFJF'
ALPACA_SECRET_KEY = 'y0SPRGmWXNBRHp1RhljnP2cYSgWcaMLy1byER2JH'
ALPACA_BASE_URL = 'https://paper-api.alpaca.markets/v2'  # Use paper trading URL for testing

# Initialize the Alpaca API
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, api_version='v2')

# RSI calculation function
def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Momentum calculation function
def calculate_momentum(data, period=10):
    return data['Close'].diff(period)

# Define the trading logic
symbol = 'CELH'  # Stock symbol to trade
rsi_period = 9
rsi_overbought = 70
rsi_oversold = 30
momentum_period = 10  # Momentum calculation period
trade_amount = 1  # Number of shares to trade
max_trades_per_day = 10  # Maximum trades per day

# Track the number of trades executed today
trades_today = 0
last_trade_date = datetime.now().date()

# Function to check if the date has changed (new day)
def reset_trade_count():
    global trades_today, last_trade_date
    current_date = datetime.now().date()
    if current_date != last_trade_date:
        trades_today = 0
        last_trade_date = current_date

# Main trading loop
try:
    while True:
        # Reset trade count if a new day starts
        reset_trade_count()

        # If we've reached the max trades for the day, wait
        if trades_today >= max_trades_per_day:
            print(f"Max trades reached for today ({max_trades_per_day}). Waiting until tomorrow.")
            time.sleep(60 * 60 * 24)  # Wait until the next day
            continue

        # Fetch historical data for the stock from Yahoo Finance
        data = yf.download(symbol, period="1d", interval="1m")

        # Ensure the data is sorted by time
        data = data.sort_index()

        # Calculate RSI and Momentum
        data['rsi'] = calculate_rsi(data, rsi_period)
        data['momentum'] = calculate_momentum(data, momentum_period)

        # Get the most recent RSI and Momentum values
        latest_rsi = data['rsi'].iloc[-1]
        latest_momentum = data['momentum'].iloc[-1]

        # Get current position
        position = None
        try:
            position = api.get_account().cash  # Check if we have any cash, no open positions
        except Exception:
            position = None

        # Trading logic based on RSI and Momentum
        if latest_rsi < rsi_oversold and latest_momentum > 0 and position == '0.00':
            # Buy signal: RSI indicates oversold and momentum is positive
            print(f"RSI is {latest_rsi:.2f}, Momentum is {latest_momentum:.2f}. Placing a BUY order.")
            api.submit_order(
                symbol=symbol,
                qty=trade_amount,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            trades_today += 1

        elif latest_rsi > rsi_overbought and latest_momentum < 0 and position != '0.00':
            # Sell signal: RSI indicates overbought and momentum is negative
            print(f"RSI is {latest_rsi:.2f}, Momentum is {latest_momentum:.2f}. Placing a SELL order.")
            api.submit_order(
                symbol=symbol,
                qty=trade_amount,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            trades_today += 1

        else:
            print(f"No trade action. RSI: {latest_rsi:.2f}, Momentum: {latest_momentum:.2f}.")

        # Sleep for a minute before the next check
        time.sleep(5)

except KeyboardInterrupt:
    print("Trading bot stopped.")
