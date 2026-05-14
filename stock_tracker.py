import yfinance as yf
import pandas as pd
import ta
import schedule
import time
import resend
import json
import os

# =========================
# CONFIG
# =========================

import os

resend.api_key = os.getenv("RESEND_API_KEY")

TO_EMAIL = "sabgarian16@gmail.com"

STARTING_CASH = 1000

WATCHLIST = [
    "NVDA",
    "MSFT",
    "AMZN",
    "AAPL",
    "TSM"
]

PORTFOLIO_FILE = "portfolio.json"

# =========================
# LOAD / CREATE PORTFOLIO
# =========================

if not os.path.exists(PORTFOLIO_FILE):

    portfolio = {
        "cash": STARTING_CASH,
        "holdings": {},
        "trade_history": []
    }

    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f)

with open(PORTFOLIO_FILE, "r") as f:
    portfolio = json.load(f)

if "trade_history" not in portfolio:
    portfolio["trade_history"] = []

# =========================
# EMAIL FUNCTION
# =========================

def send_email(subject, body):

    resend.Emails.send({
        "from": "Stock Bot <onboarding@resend.dev>",
        "to": [TO_EMAIL],
        "subject": subject,
        "text": body
    })

# =========================
# SAVE PORTFOLIO
# =========================

def save_portfolio():
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=4)

# =========================
# BUY STOCK
# =========================

def buy_stock(ticker, price):

    allocation = 250

    if portfolio["cash"] < allocation:
        print(f"Not enough cash to buy {ticker}")
        return

    shares = allocation / price

    portfolio["cash"] -= allocation

    portfolio["trade_history"].append({
        "action": "BUY",
        "ticker": ticker,
        "price": price,
        "shares": shares,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

    save_portfolio()

    subject = f"BUY SIGNAL: {ticker}"

    body = f"""
BUY SIGNAL

Ticker: {ticker}
Buy Price: ${price:.2f}

Shares Purchased: {shares:.4f}

Remaining Cash:
${portfolio['cash']:.2f}
"""

    send_email(subject, body)

    print(body)

# =========================
# SELL STOCK
# =========================

def sell_stock(ticker, price):

    holding = portfolio["holdings"][ticker]

    shares = holding["shares"]

    value = shares * price

    buy_price = holding["buy_price"]

    profit = value - (shares * buy_price)

    portfolio["cash"] += value

    del portfolio["holdings"][ticker]

    portfolio["trade_history"].append({
        "action": "SELL",
        "ticker": ticker,
        "price": price,
        "shares": shares,
        "profit": profit,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

    save_portfolio()

    subject = f"SELL SIGNAL: {ticker}"

    body = f"""
SELL SIGNAL

Ticker: {ticker}
Sell Price: ${price:.2f}

Profit/Loss:
${profit:.2f}

Updated Cash Balance:
${portfolio['cash']:.2f}
"""

    send_email(subject, body)

    print(body)

# =========================
# STRATEGY LOGIC
# =========================

def analyze_stock(ticker):

    print(f"Analyzing {ticker}...")

    data = yf.download(ticker, period="3mo", interval="1d")

    if data.empty:
        return

    close_prices = data["Close"].squeeze()

    rsi = ta.momentum.RSIIndicator(close_prices).rsi()

    latest_rsi = rsi.iloc[-1]

    current_price = float(close_prices.iloc[-1])

    print(f"{ticker} RSI: {latest_rsi:.2f}")

    # BUY CONDITION
    if latest_rsi < 30 and ticker not in portfolio["holdings"]:

        print(f"BUY SIGNAL for {ticker}")

        buy_stock(ticker, current_price)

    # SELL CONDITION
    elif latest_rsi > 70 and ticker in portfolio["holdings"]:

        print(f"SELL SIGNAL for {ticker}")

        sell_stock(ticker, current_price)

# =========================
# RUN BOT
# =========================

def run_bot():

    print("Running stock analysis...\n")

    for ticker in WATCHLIST:
        analyze_stock(ticker)

    print("\nAnalysis complete.\n")

# =========================
# MARKET HOURS CHECK
# =========================

def is_market_open():

    current_time = time.localtime()

    current_hour = current_time.tm_hour

    current_day = current_time.tm_wday

    # Monday-Friday only
    is_weekday = current_day < 5

    # Market hours: 9 AM - 4 PM
    is_market_hours = 9 <= current_hour < 16

    return is_weekday and is_market_hours

# =========================
# SCHEDULED BOT RUN
# =========================

def scheduled_run():

    if is_market_open():

        print("\nMarket is open. Running bot...\n")

        run_bot()

    else:

        print("\nMarket closed. Skipping scan.\n")

# Run immediately once
run_bot()

# Run every hour
schedule.every().hour.do(scheduled_run)

# Keep program alive
while True:

    schedule.run_pending()

    time.sleep(60)
