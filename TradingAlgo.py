import alpaca_trade_api as tradeapi
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Alpaca API credentials
ALPACA_API_KEY = 'PKX3NNMATUOO2MA4JFJF'
ALPACA_SECRET_KEY = 'y0SPRGmWXNBRHp1RhljnP2cYSgWcaMLy1byER2JH'
ALPACA_BASE_URL = 'https://paper-api.alpaca.markets'

# Initialize the Alpaca API
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, api_version='v2')

# RSI calculation
def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = -delta.clip(upper=0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Momentum calculation
def calculate_momentum(data, period=10):
    return data['Close'].diff(period)

# Parameters
symbol = 'AAPL'
rsi_period = 9
momentum_period = 10
rsi_overbought = 70
rsi_oversold = 30
trade_amount = 1
max_trades_per_day = 10

# Track trades
trades_today = 0
last_trade_date = datetime.now().date()

def reset_trade_count():
    global trades_today, last_trade_date
    current_date = datetime.now().date()
    if current_date != last_trade_date:
        trades_today = 0
        last_trade_date = current_date

def is_market_open():
    clock = api.get_clock()
    return clock.is_open

def get_position_qty(symbol):
    try:
        position = api.get_position(symbol)
        return float(position.qty)
    except tradeapi.rest.APIError:
        return 0.0

# Main loop
try:
    while True:
        reset_trade_count()

        if trades_today >= max_trades_per_day:
            print("Max trades reached. Sleeping until next trading day.")
            while datetime.now().date() == last_trade_date:
                time.sleep(60)
            continue

        if not is_market_open():
            print("Market is closed. Waiting for open...")
            while not is_market_open():
                time.sleep(60)
            continue

        data = yf.download(symbol, period="1d", interval="1m")
        data = data.sort_index()

        if len(data) < rsi_period or len(data) < momentum_period:
            print("Not enough data yet.")
            time.sleep(60)
            continue

        data['rsi'] = calculate_rsi(data, rsi_period)
        data['momentum'] = calculate_momentum(data, momentum_period)

        latest_rsi = data['rsi'].iloc[-1]
        latest_momentum = data['momentum'].iloc[-1]
        position_qty = get_position_qty(symbol)

        if latest_rsi < rsi_oversold and latest_momentum > 0 and position_qty == 0:
            print(f"RSI: {latest_rsi:.2f}, Momentum: {latest_momentum:.2f} → BUY")
            api.submit_order(
                symbol=symbol,
                qty=trade_amount,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            trades_today += 1

        elif latest_rsi > rsi_overbought and latest_momentum < 0 and position_qty > 0:
            print(f"RSI: {latest_rsi:.2f}, Momentum: {latest_momentum:.2f} → SELL")
            api.submit_order(
                symbol=symbol,
                qty=trade_amount,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            trades_today += 1

        else:
            print(f"No trade. RSI: {latest_rsi:.2f}, Momentum: {latest_momentum:.2f}")

        # Sleep until next minute candle
        now = datetime.now()
        next_minute = (now + timedelta(minutes=1)).replace(second=5, microsecond=0)
        time.sleep((next_minute - now).total_seconds())

except KeyboardInterrupt:
    print("Bot stopped.")
