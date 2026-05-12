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
    host=os.getenv('POSTGRES_HOST', 'localhost')
)

st.title("FIX Trade Monitor Dashboard")

@st.cache_data(ttl=10)
def load_data():
    cur = conn.cursor()
    cur.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 100")
    rows = cur.fetchall()
    columns = [desc[0] for desc in (cur.description or [])]
    cur.close()
    return pd.DataFrame(rows, columns=columns)

df = load_data()
st.dataframe(df)

st.metric("Total Trades", len(df))
if not df.empty and 'symbol' in df.columns:
    st.bar_chart(df['symbol'].value_counts())
