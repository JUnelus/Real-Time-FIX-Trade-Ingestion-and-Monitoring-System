"""
Daily Top Crypto and Stocks FIX Producer
Fetches top 5 cryptocurrencies and top 5 stocks, converts to FIX messages.
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict
import logging

# Third-party imports
try:
    import requests
except ImportError:
    requests = None

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    from kafka import KafkaProducer
except ImportError:
    KafkaProducer = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def to_fix(fix_dict: Dict) -> str:
    """
    Convert dictionary to FIX message format.
    Format: TAG1=VALUE1|TAG2=VALUE2|...
    """
    return '|'.join([f"{k}={v}" for k, v in fix_dict.items()]) + '|'


def encode_fix(fix_str: str) -> bytes:
    """Encode FIX string replacing | with SOH delimiter."""
    return fix_str.replace('|', '\x01').encode()


def get_top_cryptocurrencies(limit: int = 5) -> List[Dict]:
    """
    Fetch top cryptocurrencies by market cap from CoinGecko API.
    Returns list of dicts with symbol, price, market_cap.
    """
    if not requests:
        logger.error("requests library not installed. Skipping crypto data.")
        return []

    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': limit,
            'sparkline': False
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        cryptos = []
        for coin in response.json():
            cryptos.append({
                'symbol': coin['symbol'].upper(),
                'name': coin['name'],
                'price': coin['current_price'],
                'market_cap': coin['market_cap'] or 0,
                'type': 'CRYPTO'
            })

        logger.info(f"Fetched {len(cryptos)} cryptocurrencies")
        return cryptos
    except Exception as e:
        logger.error(f"Error fetching cryptocurrencies: {e}")
        return []


def get_top_stocks(limit: int = 5) -> List[Dict]:
    """
    Fetch top stocks by market cap.
    Uses yfinance to get popular stocks.
    """
    if not yf:
        logger.error("yfinance library not installed. Skipping stock data.")
        return []

    try:
        # Popular large-cap stocks
        stock_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'BRK.B', 'NVDA', 'TSLA', 'JNJ', 'V', 'WMT']

        stocks = []
        for symbol in stock_symbols[:limit]:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period='1d')

                if data.empty:
                    continue

                current_price = data['Close'].iloc[-1]

                stocks.append({
                    'symbol': symbol,
                    'name': ticker.info.get('longName', symbol),
                    'price': float(current_price),
                    'market_cap': ticker.info.get('marketCap', 0),
                    'type': 'STOCK'
                })
            except Exception as e:
                logger.warning(f"Error fetching stock {symbol}: {e}")
                continue

        logger.info(f"Fetched {len(stocks)} stocks")
        return stocks
    except Exception as e:
        logger.error(f"Error fetching stocks: {e}")
        return []


def create_fix_messages(cryptos: List[Dict], stocks: List[Dict]) -> List[str]:
    """
    Convert crypto and stock data to FIX ExecutionReport messages (MsgType=8).
    """
    messages = []
    order_id = 1000

    # FIX message template for ExecutionReport (35=8)
    def create_execution_report(order_id, symbol, qty, price, asset_type):
        fix_dict = {
            '8': 'FIX.4.2',           # BeginString
            '35': '8',                # MsgType: ExecutionReport
            '49': 'DAILY-PRODUCER',   # SenderCompID
            '56': 'TRADE-SYSTEM',     # TargetCompID
            '34': str(order_id),      # MsgSeqNum
            '52': datetime.utcnow().strftime('%Y%m%d-%H:%M:%S'),  # SendingTime
            '11': str(order_id),      # ClOrdID
            '17': str(order_id),      # ExecID
            '20': '0',                # ExecTransType
            '150': '2',               # ExecType: Trade
            '39': '2',                # OrdStatus: Filled
            '55': symbol,             # Symbol
            '54': '1',                # Side: Buy
            '38': str(qty),           # OrderQty
            '44': str(price),         # Price
            '60': datetime.utcnow().strftime('%Y%m%d-%H:%M:%S'),  # TransactTime
            '200': asset_type,        # MaturityMonthYear (reusing for asset type)
            '10': '000'               # CheckSum
        }
        return to_fix(fix_dict)

    # Create messages for cryptocurrencies
    for crypto in cryptos:
        msg = create_execution_report(
            order_id,
            f"{crypto['symbol']}-USD",
            0.1,  # Small quantity for crypto
            crypto['price'],
            'CRYPTO'
        )
        messages.append(msg)
        order_id += 1

    # Create messages for stocks
    for stock in stocks:
        msg = create_execution_report(
            order_id,
            stock['symbol'],
            100,  # Standard stock quantity
            stock['price'],
            'STOCK'
        )
        messages.append(msg)
        order_id += 1

    return messages


def send_to_kafka(messages: List[str], bootstrap_servers: str = 'localhost:9092'):
    """Send FIX messages to Kafka."""
    if not KafkaProducer:
        logger.error("kafka-python not installed")
        return

    try:
        producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
        for msg in messages:
            encoded = encode_fix(msg)
            producer.send('fix-trades', value=encoded)
            logger.info(f"Produced FIX message: {msg[:80]}...")

        producer.flush()
        producer.close()
        logger.info(f"Successfully sent {len(messages)} messages to Kafka")
    except Exception as e:
        logger.error(f"Error sending to Kafka: {e}")


def save_to_file(messages: List[str], filename: str = 'daily_fix_messages.json'):
    """Save FIX messages to a JSON file as backup."""
    try:
        data = {
            'timestamp': datetime.utcnow().isoformat(),
            'messages': messages,
            'count': len(messages)
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(messages)} messages to {filename}")
    except Exception as e:
        logger.error(f"Error saving to file: {e}")


def main():
    """Main function to orchestrate the daily FIX message generation."""
    logger.info("Starting daily top crypto and stocks FIX producer...")

    # Fetch data
    cryptos = get_top_cryptocurrencies(limit=5)
    stocks = get_top_stocks(limit=5)

    # Combine and log
    logger.info(f"Fetched {len(cryptos)} cryptos and {len(stocks)} stocks")

    # Create FIX messages
    messages = create_fix_messages(cryptos, stocks)
    logger.info(f"Created {len(messages)} FIX messages")

    # Log the messages for verification
    for i, msg in enumerate(messages, 1):
        logger.info(f"Message {i}: {msg[:100]}...")

    # Try to send to Kafka if available
    if env_flag('SKIP_KAFKA', default=False):
        logger.info("Skipping Kafka publish because SKIP_KAFKA is enabled")
    else:
        bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        send_to_kafka(messages, bootstrap_servers)

    # Always save to file
    save_to_file(messages)

    logger.info("Daily FIX producer completed successfully!")


if __name__ == "__main__":
    main()

