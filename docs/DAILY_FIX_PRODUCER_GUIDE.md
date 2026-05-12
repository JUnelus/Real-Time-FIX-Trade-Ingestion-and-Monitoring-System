# Daily FIX Producer - Technical Documentation

## Overview

The daily FIX producer (`producer/top_crypto_stocks_to_fix.py`) automatically fetches market data for the top 5 cryptocurrencies and top 5 stocks, then converts this data into FIX ExecutionReport messages for ingestion into the trading system.

## Data Sources

### Cryptocurrencies

**API:** CoinGecko (Free)
- **Endpoint:** `/api/v3/coins/markets`
- **Authentication:** None required
- **Rate Limit:** ~50 requests/minute
- **Data:** Top 50+ cryptocurrencies by market cap

**Fields Extracted:**
- Symbol (e.g., "BTC", "ETH")
- Name (e.g., "Bitcoin", "Ethereum")
- Current Price (USD)
- Market Cap (USD)

### Stocks

**Tool:** yfinance
- **Underlying Data:** Yahoo Finance
- **Authentication:** None required
- **Rate Limit:** Depends on Yahoo Finance
- **Default Symbols:** AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, JNJ, V, WMT, BRK.B

**Fields Extracted:**
- Symbol
- Long Name
- Current Price (USD)
- Market Cap (USD)

## FIX Message Format

All messages are generated as **ExecutionReport (MsgType=8)** messages.

### Message Structure

```
BeginString|MsgType|SenderCompID|TargetCompID|MsgSeqNum|SendingTime|ClOrdID|ExecID|ExecTransType|ExecType|OrdStatus|Symbol|Side|OrderQty|Price|TransactTime|AssetType|CheckSum
```

### Field Reference

| Tag | Field Name | Example | Description |
|-----|-----------|---------|-------------|
| 8 | BeginString | FIX.4.2 | FIX protocol version |
| 35 | MsgType | 8 | ExecutionReport |
| 49 | SenderCompID | DAILY-PRODUCER | System generating the message |
| 56 | TargetCompID | TRADE-SYSTEM | Target system |
| 34 | MsgSeqNum | 1000 | Sequential message number |
| 52 | SendingTime | 20260512-090000 | UTC timestamp (YYYYMMdd-HHmmss) |
| 11 | ClOrdID | 1000 | Client Order ID (unique per message) |
| 17 | ExecID | 1000 | Execution ID |
| 20 | ExecTransType | 0 | Execution Transaction Type |
| 150 | ExecType | 2 | Execution Type (Trade) |
| 39 | OrdStatus | 2 | Order Status (Filled) |
| 55 | Symbol | BTC-USD | Security symbol |
| 54 | Side | 1 | Side (1=Buy) |
| 38 | OrderQty | 0.1 | Order quantity |
| 44 | Price | 45000.0 | Price per unit |
| 60 | TransactTime | 20260512-090000 | Transaction timestamp |
| 200 | MaturityMonthYear | CRYPTO | Asset type (reused field)|
| 10 | CheckSum | 000 | Message checksum |

### Example FIX Messages

#### Bitcoin Example
```
8=FIX.4.2|35=8|49=DAILY-PRODUCER|56=TRADE-SYSTEM|34=1000|52=20260512-090000|11=1000|17=1000|20=0|150=2|39=2|55=BTC-USD|54=1|38=0.1|44=45000.0|60=20260512-090000|200=CRYPTO|10=000|
```

#### Apple Stock Example
```
8=FIX.4.2|35=8|49=DAILY-PRODUCER|56=TRADE-SYSTEM|34=1005|52=20260512-090000|11=1005|17=1005|20=0|150=2|39=2|55=AAPL|54=1|38=100|44=175.50|60=20260512-090000|200=STOCK|10=000|
```

### Quantities

- **Cryptocurrencies:** 0.1 units (e.g., 0.1 BTC = ~$4,500)
- **Stocks:** 100 shares (standard lot)

These quantities are configurable in the producer script.

## Message Generation Flow

```
┌─────────────────────────────────────┐
│  Daily GitHub Actions Trigger       │
│  (9:00 AM UTC)                      │
└──────────────────┬──────────────────┘
                   │
        ┌──────────▼──────────┐
        │ Run Producer Script │
        └──────────┬──────────┘
                   │
      ┌────────────┴────────────┐
      │                         │
  ┌───▼────────┐         ┌─────▼─────┐
  │   Fetch    │         │   Fetch   │
  │ Crypto Top 5│         │ Stocks Top 5│
  └───┬────────┘         └─────┬─────┘
      │ CoinGecko API         │ yfinance
      │ (Free)                │ (Free)
      └────────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │ Create FIX Messages │
        │ (ExecutionReport)   │
        └──────────┬──────────┘
                   │
      ┌────────────┴────────────┐
      │                         │
  ┌───▼────────┐         ┌─────▼──────────┐
  │  Try Send  │         │  Save to File  │
  │ to Kafka   │         │ (JSON backup)  │
  └────────────┘         │ daily_fix_..json│
                         └────────────────┘
                   │
        ┌──────────▼──────────┐
        │ Generate Report     │
        │ Upload Artifacts    │
        └─────────────────────┘
```

## Output Files

### Daily FIX Messages JSON

**Filename:** `daily_fix_messages.json`

**Format:**
```json
{
  "timestamp": "2026-05-12T09:00:00.000000",
  "messages": [
    "8=FIX.4.2|35=8|49=DAILY-PRODUCER|...",
    "8=FIX.4.2|35=8|49=DAILY-PRODUCER|...",
    ...
  ],
  "count": 10
}
```

**Location:** GitHub Actions artifacts (30-day retention)

### GitHub Actions Archive

**Location:** `docs/daily_reports/fix_messages_YYYY-MM-DD.json`

**Purpose:** Long-term historical archive committed to repository

## Integration with Existing System

### Kafka Consumer Integration

The FIX messages can be consumed by the existing consumer:

```bash
# Consumer will parse messages and insert into database
python -m consumer.kafka_fix_parser_consumer
```

### Database Insertion

Messages flow: Producer → Kafka → Consumer → PostgreSQL

**Parsed fields in database:**
- clordid: Order ID (11)
- symbol: Security symbol (55)
- side: Buy/Sell (54)
- qty: Quantity (38)
- price: Price (44)
- raw: Full FIX message

### Dashboard Display

The Streamlit dashboard automatically displays:
- Latest 100 trades
- Trade count metric
- Chart of trades by symbol

## Running Standalone

To run the producer without Kafka:

```bash
# Manual execution
python producer/top_crypto_stocks_to_fix.py

# Output: daily_fix_messages.json in current directory
# Also prints logs to console
```

**Environment Variables:**
- `KAFKA_BOOTSTRAP_SERVERS`: Optional, defaults to `localhost:9092`

## Error Handling

The producer includes robust error handling:

```python
# Gracefully handles:
- API connection timeouts
- Missing library dependencies
- Invalid stock symbols
- Kafka connection failures
- JSON serialization errors
```

All errors are logged with detailed messages and context.

## Performance Metrics

- **Execution Time:** ~5-10 seconds
  - API calls: ~3-4 seconds
  - Message generation: ~1 second
  - Kafka send (if available): ~1 second
- **Data Volume:** ~10 FIX messages per run
- **File Size:** ~5-10 KB (daily_fix_messages.json)
- **API Calls:** 2 (CoinGecko + yfinance)

## Customization

### Fetch More Securities

```python
# In top_crypto_stocks_to_fix.py
cryptos = get_top_cryptocurrencies(limit=10)  # Instead of 5
stocks = get_top_stocks(limit=10)  # Instead of 5
```

### Different Stocks

```python
# Modify stock_symbols list
stock_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'JNJ', 'V', 'WMT', 'GOOG']
```

### Custom Quantities

```python
# In create_execution_report()
# For crypto
qty = 0.5  # Instead of 0.1 BTC
# For stocks
qty = 50  # Instead of 100 shares
```

### Different FIX Version

```python
# Change in create_execution_report()
'8': 'FIX.4.4',  # Instead of FIX.4.2
```

## Troubleshooting

### No Crypto Data

- Check internet connection
- Verify CoinGecko API is accessible: `https://api.coingecko.com/api/v3`
- Check logs for specific error messages

### No Stock Data

- Verify yfinance is installed: `pip install yfinance`
- Check if Yahoo Finance is accessible
- Verify stock symbols are correct

### Messages Not Sent to Kafka

- Verify Kafka broker is running: `localhost:9092`
- Check Kafka logs for connection errors
- Verify topic `fix-trades` exists

### JSON File Not Created

- Check write permissions in working directory
- Verify disk space is available
- Check logs for file I/O errors

## Security Considerations

- **Data:** Uses public APIs (no sensitive data)
- **Rate Limiting:** Respects API rate limits
- **Credentials:** No authentication needed
- **Data Retention:** JSON files don't contain PII

## Future Enhancements

- Support for multiple cryptocurrencies sources
- Real-time price updates (instead of daily)
- Additional FIX message types (NewOrderSingle, etc.)
- Machine learning-based price predictions
- WebSocket stream integration
- Data persistence for analysis

