# app/app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock vs Moon Phases", layout="wide")
st.title("Stock Prices vs Moon Phases — The Data Weaver")

# ---------- helpers ----------
def moon_phase_fraction(date):
    # Simple approximate algorithm: days since known new moon (2000-01-06)
    diff = date - datetime(2000,1,6)
    days = diff.total_seconds() / 86400.0
    synodic_month = 29.53058867
    phase = (days % synodic_month) / synodic_month  # 0 -> New, 0.25 -> First Quarter, 0.5 -> Full
    return phase

def phase_name(phase_frac):
    if phase_frac < 0.125 or phase_frac >= 0.875:
        return "New"
    if 0.125 <= phase_frac < 0.375:
        return "First Quarter"
    if 0.375 <= phase_frac < 0.625:
        return "Full"
    return "Last Quarter"

def fetch_stock(ticker, start, end):
    df = yf.Ticker(ticker).history(start=start, end=end)
    df = df.reset_index().rename(columns={"Date":"date"})
    df['date'] = pd.to_datetime(df['date']).dt.date
    return df

# ---------- UI ----------
col1, col2 = st.columns([1,3])
with col1:
    ticker = st.text_input("Ticker (yfinance)", "AAPL")
    start = st.date_input("Start date", datetime.now().date() - timedelta(days=365))
    end = st.date_input("End date", datetime.now().date())
    if st.button("Load data"):
        with st.spinner("Fetching data..."):
            df = fetch_stock(ticker, start.isoformat(), (end + timedelta(days=1)).isoformat())
            if df.empty:
                st.error("No data. Try another ticker / timeframe.")
            else:
                st.success(f"Fetched {len(df)} rows")

                # compute moon phase
                df['phase_frac'] = df['date'].apply(lambda d: moon_phase_fraction(datetime(d.year, d.month, d.day)))
                df['moon_phase'] = df['phase_frac'].apply(phase_name)
                df['return'] = df['Close'].pct_change()

                # Time series
                import plotly.express as px
                fig = px.line(df, x='date', y='Close', title=f"{ticker} Close Price")
                # annotate full moons visually
                fulls = df[df['moon_phase']=="Full"]
                fig.add_scatter(x=fulls['date'], y=fulls['Close'], mode='markers', name='Full Moon', marker=dict(size=8, symbol='circle-open'))

                st.plotly_chart(fig, use_container_width=True)

                # Aggregation
                agg = df.groupby('moon_phase')['return'].mean().reset_index().sort_values('return', ascending=False)
                st.subheader("Average daily returns by moon phase")
                st.dataframe(agg.style.format({'return': '{:.4%}'}))

                bar = px.bar(agg, x='moon_phase', y='return', title="Average Return by Moon Phase")
                st.plotly_chart(bar, use_container_width=True)

                # small stats
                st.metric("Overall avg daily return", f"{df['return'].mean():.4%}")
                st.metric("Std dev daily return", f"{df['return'].std():.4%}")

                # show sample table
                st.subheader("Sample rows")
                st.dataframe(df[['date','Close','moon_phase','return']].tail(10))
