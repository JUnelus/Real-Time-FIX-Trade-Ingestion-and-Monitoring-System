import os
from kafka import KafkaConsumer
import psycopg2
from parser.fix_parser import parse_fix_message

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

consumer = KafkaConsumer(
    'fix-trades',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',
    value_deserializer=lambda x: x
)

# Postgres connection
conn = psycopg2.connect(
    dbname=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    host="localhost"
)
cur = conn.cursor()

# Ensure table exists
cur.execute("""
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    clordid TEXT,
    symbol TEXT,
    side TEXT,
    qty NUMERIC,
    price NUMERIC,
    raw TEXT
)
""")
conn.commit()

for message in consumer:
    try:
        fix = parse_fix_message(message.value)
        clordid = fix.get("11")
        symbol = fix.get("55")
        side = fix.get("54")
        qty = fix.get("38")
        price = fix.get("44")
        raw = message.value.decode()
        cur.execute("INSERT INTO trades (clordid, symbol, side, qty, price, raw) VALUES (%s, %s, %s, %s, %s, %s)",
                    (clordid, symbol, side, qty, price, raw))
        conn.commit()
        print(f"Ingested trade: {clordid} {symbol} {side} {qty} {price}")
    except Exception as e:
        print("Error parsing or inserting:", e)
