import os
import streamlit as st
import psycopg2
import pandas as pd

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    host="localhost"
)

st.title("FIX Trade Monitor Dashboard")

@st.cache_data(ttl=10)
def load_data():
    return pd.read_sql("SELECT * FROM trades ORDER BY id DESC LIMIT 100", conn)

df = load_data()
st.dataframe(df)

st.metric("Total Trades", len(df))
st.bar_chart(df['symbol'].value_counts())
