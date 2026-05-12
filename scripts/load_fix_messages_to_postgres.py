import argparse
import json
import os
import sys
from pathlib import Path
from typing import Iterable

import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from parser.fix_parser import parse_fix_message

load_dotenv()


def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
    )


def normalize_fix_message(raw_message: str) -> bytes:
    if "\x01" in raw_message:
        return raw_message.encode()
    return raw_message.replace("|", "\x01").encode()


def load_messages(file_path: str) -> list[str]:
    with open(file_path, "r", encoding="utf-8") as file:
        payload = json.load(file)
    return payload.get("messages", [])


def iter_trade_rows(messages: Iterable[str]):
    for raw in messages:
        parsed = parse_fix_message(normalize_fix_message(raw))
        yield (
            parsed.get("11"),
            parsed.get("55"),
            parsed.get("54"),
            parsed.get("38"),
            parsed.get("44"),
            raw,
        )


def insert_messages(file_path: str, truncate: bool = False) -> int:
    messages = load_messages(file_path)
    rows = list(iter_trade_rows(messages))

    conn = get_connection()
    cur = conn.cursor()

    if truncate:
        cur.execute("TRUNCATE TABLE trades RESTART IDENTITY")

    cur.executemany(
        "INSERT INTO trades (clordid, symbol, side, qty, price, raw) VALUES (%s, %s, %s, %s, %s, %s)",
        rows,
    )
    conn.commit()
    cur.close()
    conn.close()
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description="Load FIX messages JSON into Postgres trades table.")
    parser.add_argument("file_path", help="Path to daily_fix_messages.json")
    parser.add_argument("--truncate", action="store_true", help="Clear existing trades before insert")
    parser.add_argument("--dry-run", action="store_true", help="Parse messages without connecting to Postgres")
    args = parser.parse_args()

    messages = load_messages(args.file_path)
    parsed_rows = list(iter_trade_rows(messages))

    if args.dry_run:
        print(f"Parsed {len(parsed_rows)} FIX messages successfully")
        if parsed_rows:
            first = parsed_rows[0]
            print(f"First trade: clordid={first[0]} symbol={first[1]} side={first[2]} qty={first[3]} price={first[4]}")
        return

    inserted = insert_messages(args.file_path, truncate=args.truncate)
    print(f"Inserted {inserted} trades into Postgres")


if __name__ == "__main__":
    main()


