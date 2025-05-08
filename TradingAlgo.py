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
DATA_FEED = 'iex'

# Initialize the Alpaca API
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, api_version='v2')

# === Indicator Functions ===
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = -delta.clip(upper=0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_momentum(series, period=10):
    return series.diff(period)

def calculate_macd(series, short_period=12, long_period=26, signal_period=9):
    ema_short = series.ewm(span=short_period, adjust=False).mean()
    ema_long = series.ewm(span=long_period, adjust=False).mean()
    macd_line = ema_short - ema_long
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    return macd_line, signal_line

# === Parameters ===
symbol = 'AAPL'
rsi_period = 9
momentum_period = 10
rsi_overbought = 70
rsi_oversold = 30
trade_amount = 1
max_trades_per_day = 10

# === Trade tracking ===
trades_today = 0
last_trade_date = datetime.now().date()

def reset_trade_count():
    global trades_today, last_trade_date
    if datetime.now().date() != last_trade_date:
        trades_today = 0
        last_trade_date = datetime.now().date()

def is_market_open():
    return api.get_clock().is_open

def get_position_qty(symbol):
    try:
        pos = api.get_position(symbol)
        return float(pos.qty)
    except tradeapi.rest.APIError:
        return 0.0

def get_recent_data(symbol, limit=1000):
    bars = api.get_bars(symbol, tradeapi.TimeFrame.Minute, limit=limit).df
    bars = bars.sort_index()  # Ensure data is sorted by time
    return bars

# === Main Trading Loop ===
try:
    while True:
        reset_trade_count()

        if trades_today >= max_trades_per_day:
            print("Max trades reached. Sleeping until next day.")
            while datetime.now().date() == last_trade_date:
                time.sleep(60)
            continue

        if not is_market_open():
            print("Market closed. Waiting for open...")
            while not is_market_open():
                time.sleep(60)
            continue

        # Get recent data
        data = get_recent_data(symbol)
        if len(data) < 30:
            print("Not enough data.")
            time.sleep(60)
            continue

        data = data.sort_index()
        close = data['close']

        # Calculate indicators
        data['rsi'] = calculate_rsi(close, rsi_period)
        data['momentum'] = calculate_momentum(close, momentum_period)
        data['macd'], data['signal'] = calculate_macd(close)

        latest = data.iloc[-1]
        latest_rsi = latest['rsi']
        latest_momentum = latest['momentum']
        latest_macd = latest['macd']
        latest_signal = latest['signal']
        position_qty = get_position_qty(symbol)

        print(f"RSI: {latest_rsi:.2f}, Momentum: {latest_momentum:.2f}, MACD: {latest_macd:.2f}, Signal: {latest_signal:.2f}, Position: {position_qty}")

        # === Trade Logic with MACD condition ===
        if latest_rsi < rsi_oversold and latest_momentum > 0 and latest_macd > latest_signal and position_qty == 0:
            print("→ BUY signal (RSI + Momentum + MACD)")
            api.submit_order(symbol=symbol, qty=trade_amount, side='buy', type='market', time_in_force='gtc')
            trades_today += 1

        elif latest_rsi > rsi_overbought and latest_momentum < 0 and latest_macd < latest_signal and position_qty > 0:
            print("→ SELL signal (RSI + Momentum + MACD)")
            api.submit_order(symbol=symbol, qty=trade_amount, side='sell', type='market', time_in_force='gtc')
            trades_today += 1

        else:
            print("No trade condition met.")

        # Sleep until next minute
        now = datetime.now()
        next_minute = (now + timedelta(minutes=1)).replace(second=5, microsecond=0)
        time.sleep((next_minute - now).total_seconds())

except KeyboardInterrupt:
    print("Bot stopped.")