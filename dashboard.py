# dashboard.py

import json
import yfinance as yf
import pandas as pd
import streamlit as st

from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")

st_autorefresh(interval=30000, key="refresh")

# Load portfolio
with open("portfolio.json", "r") as f:
    portfolio = json.load(f)

cash = portfolio["cash"]
holdings = portfolio["holdings"]

st.title("📈 Stock Portfolio Dashboard")

st.subheader(f"💵 Available Cash: ${cash:,.2f}")

rows = []

total_value = cash

for ticker, data in holdings.items():

    shares = data["shares"]
    buy_price = data["buy_price"]

    current_price = yf.Ticker(ticker).history(period="1d")["Close"].iloc[-1]

    market_value = shares * current_price
    cost_basis = shares * buy_price
    pnl = market_value - cost_basis

    total_value += market_value

    rows.append({
        "Ticker": ticker,
        "Shares": round(shares, 4),
        "Buy Price": round(buy_price, 2),
        "Current Price": round(current_price, 2),
        "Market Value": round(market_value, 2),
        "P/L": round(pnl, 2)
    })

df = pd.DataFrame(rows)

def color_pnl(val):
    color = "green" if val > 0 else "red"
    return f"color: {color}"

styled_df = df.style.map(
    color_pnl,
    subset=["P/L"]
)

st.dataframe(styled_df, use_container_width=True)

total_pnl = df["P/L"].sum()

st.metric(
    "Total P/L",
    f"${total_pnl:.2f}"
)

st.subheader(f"📊 Total Portfolio Value: ${total_value:,.2f}")

st.subheader("Portfolio Allocation")

chart_df = pd.DataFrame(rows)

st.bar_chart(
    chart_df.set_index("Ticker")["Market Value"]
)