import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
    )


def main():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS trades (
            id SERIAL PRIMARY KEY,
            clordid TEXT,
            symbol TEXT,
            side TEXT,
            qty NUMERIC,
            price NUMERIC,
            raw TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized successfully")


if __name__ == "__main__":
    main()

