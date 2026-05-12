# System Architecture & Data Flow Diagrams

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GITHUB ACTIONS SCHEDULER                           │
│                            (UTC - Coordinated Time)                          │
└──────┬────────────────────────────────────────────┬────────────────────────┬─┘
       │                                            │                        │
       │ 9:00 AM UTC                               │ 9:30 AM UTC           │ Manual Trigger
       │                                            │                        │
       ▼                                            ▼                        ▼
┌────────────────────────────────────┐  ┌──────────────────────────────┐  ┌──────┐
│   DAILY FIX PRODUCER WORKFLOW      │  │  DASHBOARD SCREENSHOT WKFL   │  │Click │
├────────────────────────────────────┤  ├──────────────────────────────┤  │Run   │
│ Step 1: Check out code             │  │ Step 1: Check out code       │  └───┬──┘
│ Step 2: Set up Python 3.11         │  │ Step 2: Set up Python 3.11   │      │
│ Step 3: Install dependencies       │  │ Step 3: Install dependencies │      │
│         ├─ requests                │  │         ├─ requests          │      │
│         ├─ yfinance               │  │         ├─ yfinance          │      │
│         └─ kafka-python           │  │         ├─ playwright        │      │
│ Step 4: Run producer script        │  │         └─ psycopg2         │      │
│ Step 5: Upload artifacts          │  │ Step 4: Start PostgreSQL     │      │
│ Step 6: Generate summary          │  │         (Docker service)     │      │
└────┬──────────────────────────────┘  │ Step 5: Initialize schema    │      │
     │                                  │ Step 6: Seed sample data     │      │
     │ producer/top_crypto_stocks_...  │ Step 7: Start Streamlit      │      │
     │ to_fix.py                        │ Step 8: Capture screenshot   │      │
     │                                  │ Step 9: Commit to repository │      │
     ▼                                  └────┬──────────────────────┘  └──┬───┘
┌─────────────────────────────────────┐     │                           │
│   DATA FETCHING PHASE               │     │                           │
│                                     │     │                           │
│ API Calls (Parallel):               │     │                           │
│ ├─ CoinGecko:                       │     │                           │
│ │  GET /api/v3/coins/markets        │     │                           │
│ │  Query: top 5 by market cap       │     │                           │
│ │  Response: [BTC, ETH, BNB, ...]   │     │                           │
│ │                                   │     │                           │
│ └─ yfinance:                        │     │                           │
│    Query: AAPL, MSFT, GOOGL, ...    │     │                           │
│    Response: [AAPL, MSFT, GOOGL...] │     │                           │
│                                     │     │                           │
│ Result: 10 Securities Total         │     │                           │
│  ├─ 5 Cryptocurrencies              │     │                           │
│  └─ 5 Stocks                        │     │                           │
└────┬────────────────────────────────┘     │                           │
     │                                      │                           │
     ▼                                      │                           │
┌─────────────────────────────────────┐    │                           │
│   FIX MESSAGE GENERATION PHASE      │    │                           │
│                                     │    │                           │
│ For each security (10 total):       │    │                           │
│  1. Create FIX Dictionary:          │    │                           │
│     {                               │    │                           │
│       '8': 'FIX.4.2'               │    │                           │
│       '35': '8'  # ExecutionRpt    │    │                           │
│       '55': Symbol (e.g., BTC-USD) │    │                           │
│       '54': '1'  # Side: Buy       │    │                           │
│       '38': Qty (crypto: 0.1,      │    │                           │
│              stocks: 100)          │    │                           │
│       '44': Current Price          │    │                           │
│       ...other FIX fields...       │    │                           │
│     }                              │    │                           │
│  2. Convert to FIX string:         │    │                           │
│     "8=FIX.4.2|35=8|49=..."       │    │                           │
│  3. Encode with SOH delimiters:    │    │                           │
│     Replace | with \x01           │    │                           │
│                                     │    │                           │
│ Result: 10 FIX ExecutionReports    │    │                           │
└────┬────────────────────────────────┘    │                           │
     │                                      │                           │
     ▼                                      │                           │
┌─────────────────────────────────────┐    │                           │
│   MESSAGE DISTRIBUTION PHASE        │    │                           │
│                                     │    │                           │
│ Primary Output (if available):      │    │                           │
│ └─ Send to Kafka Topic             │    │                           │
│    ├─ Topic: "fix-trades"          │    │                           │
│    ├─ Partition: auto-assigned     │    │                           │
│    └─ Messages: 10 total           │    │                           │
│                                     │    │                           │
│ Backup Output (always):             │    │                           │
│ └─ Save to local JSON file         │    │                           │
│    ├─ File: daily_fix_messages.json│    │                           │
│    ├─ Format: JSON with metadata   │    │                           │
│    └─ Content:                     │    │                           │
│        {                           │    │                           │
│          "timestamp": "...",       │    │                           │
│          "messages": [...],        │    │                           │
│          "count": 10               │    │                           │
│        }                           │    │                           │
│                                     │    │                           │
│ GitHub Output (always):             │    │                           │
│ └─ Upload as artifacts             │    │                           │
│    ├─ Name: daily-fix-messages     │    │                           │
│    ├─ Retention: 30 days          │    │                           │
│    └─ Format: ZIP with JSON        │    │                           │
└────┬────────────────────────────────┘    │                           │
     │                                      │                           │
     ▼                                      ▼                           ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────────┐
│   KAFKA TOPIC    │  │  JSON BACKUP     │  │   DASHBOARD RENDERING       │
│  fix-trades      │  │ daily_fix_...    │  │                             │
│                  │  │ messages.json    │  │ 1. Database initialized     │
│ Messages:        │  │                  │  │ 2. Sample data seeded       │
│ • BTC-USD (0.1)  │  │ ✓ Timestamped   │  │ 3. Streamlit dashboard     │
│ • ETH-USD (0.1)  │  │ ✓ Validated     │  │    started                  │
│ • BNB-USD (0.1)  │  │ ✓ Complete      │  │ 4. Browser renders view     │
│ • XRP-USD (0.1)  │  │                  │  │ 5. Playwright takes pic     │
│ • ADA-USD (0.1)  │  │ Backup ensures:  │  │                             │
│ • AAPL (100)     │  │ $ no data loss   │  │ Screenshot of:              │
│ • MSFT (100)     │  │ $ audit trail    │  │ ✓ Latest 100 trades        │
│ • GOOGL (100)    │  │ $ debugging      │  │ ✓ Trade count metric       │
│ • AMZN (100)     │  │                  │  │ ✓ Symbol chart             │
│ • NVDA (100)     │  │                  │  │ ✓ All UI elements          │
└────┬─────────────┘  └──────────────────┘  └──────────┬──────────────────┘
     │                                                   │
     │                                                   ▼
     │                                    ┌────────────────────────┐
     │                                    │  COMMIT TO REPOSITORY  │
     │                                    │                        │
     │                                    │ Auto-commit:           │
     │                                    │ • File: dashboard/img. │
     │                                    │         png            │
     │                                    │ • Message: "chore:     │
     │                                    │   update dashboard    │
     │                                    │   screenshot YYYY-MM-DD│
     │                                    │ • Author: GitHub Bot  │
     │                                    │ • Visible in commits  │
     │                                    │   history             │
     │                                    └──┬─────────────────────┘
     │                                       │
     ▼                                       ▼
┌───────────────────────────────────────────────────────────────┐
│                   GITHUB REPOSITORY                           │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ Persisted Outputs:                                           │
│                                                               │
│ 1. dashboard/img.png (UPDATED)                              │
│    └─ Latest screenshot (auto-updated daily)                │
│                                                               │
│ 2. Workflow Artifacts (30-day retention)                    │
│    ├─ daily_fix_messages.json (from producer)              │
│    └─ Available in Actions → Run details                   │
│                                                               │
│ 3. Commit History                                            │
│    └─ Each commit shows update timestamp                    │
│                                                               │
│ 4. Actions Run Logs                                          │
│    ├─ Producer run logs                                     │
│    └─ Screenshot workflow logs                             │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## Cryptocurrency Data Flow

```
┌─────────────────────────────────────────────────────┐
│         CoinGecko Public API (Free Tier)            │
│  https://api.coingecko.com/api/v3/coins/markets    │
├─────────────────────────────────────────────────────┤
│                                                     │
│ No Authentication Required                         │
│ Rate Limit: ~50 requests/minute (plenty for daily) │
│ Response: JSON with market data                    │
│                                                     │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ GET /coins/markets
                  │ params: {
                  │   vs_currency: 'usd',
                  │   order: 'market_cap_desc',
                  │   per_page: 5
                  │ }
                  │
                  ▼
        ┌─────────────────────┐
        │   Parse Response    │
        ├─────────────────────┤
        │ For each coin:      │
        │  • symbol (BTC)     │
        │  • name (Bitcoin)   │
        │  • current_price    │
        │  • market_cap       │
        └─────────────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │  Create 5 Dicts     │
        ├─────────────────────┤
        │ [                   │
        │   {                 │
        │    'symbol': 'BTC', │
        │    'price': 45000,  │
        │    'market_cap': .. │
        │   },                │
        │   {...},            │
        │   {...},            │
        │   {...},            │
        │   {...}             │
        │ ]                   │
        └────────────┬────────┘
                     │
                     ▼
        ┌──────────────────────────────┐
        │ Generate 5 FIX Messages      │
        ├──────────────────────────────┤
        │ For each crypto:             │
        │  Message Type: ExecutionRpt  │
        │  Symbol: {crypto}-USD        │
        │  Quantity: 0.1 units         │
        │  Price: current_price        │
        │  Status: Filled              │
        └──────────────────────────────┘
```

---

## Stock Data Flow

```
┌─────────────────────────────────────────────────────┐
│         yfinance / Yahoo Finance (Free)             │
│      https://query1.finance.yahoo.com               │
├─────────────────────────────────────────────────────┤
│                                                     │
│ No Authentication Required                         │
│ Python Wrapper: yfinance library                   │
│ Response: OHLCV data + company info                │
│                                                     │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ Query symbols:
                  │ ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
                  │
                  ▼
        ┌─────────────────────┐
        │  For Each Stock:    │
        │  1. Create ticker   │
        │  2. Get history     │
        │  3. Get info        │
        │  4. Extract fields  │
        └─────────────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │  Create 5 Dicts     │
        ├─────────────────────┤
        │ [                   │
        │   {                 │
        │    'symbol': 'AAPL',│
        │    'price': 175.50, │
        │    'market_cap': .. │
        │   },                │
        │   {...},            │
        │   {...},            │
        │   {...},            │
        │   {...}             │
        │ ]                   │
        └────────────┬────────┘
                     │
                     ▼
        ┌──────────────────────────────┐
        │ Generate 5 FIX Messages      │
        ├──────────────────────────────┤
        │ For each stock:              │
        │  Message Type: ExecutionRpt  │
        │  Symbol: {ticker} (e.g.,AAPL)│
        │  Quantity: 100 shares        │
        │  Price: current_price        │
        │  Status: Filled              │
        └──────────────────────────────┘
```

---

## FIX Message Structure

```
Complete FIX ExecutionReport Message (MsgType=8):

┌──────────────────────────────────────────────────────────────────────┐
│ Raw String Format (with | as visual separator, actually \x01):       │
│                                                                       │
│ 8=FIX.4.2|35=8|49=DAILY-PRODUCER|56=TRADE-SYSTEM|34=1000|            │
│ 52=20260512-090000|11=1000|17=1000|20=0|150=2|39=2|                 │
│ 55=BTC-USD|54=1|38=0.1|44=45000.0|60=20260512-090000|200=CRYPTO|     │
│ 10=000|                                                              │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘

Field Reference Table:

Tag │ Field Name          │ Example Value      │ Description
────┼─────────────────────┼────────────────────┼──────────────────────────
 8  │ BeginString         │ FIX.4.2           │ FIX Protocol Version
 35 │ MsgType             │ 8                 │ ExecutionReport
 49 │ SenderCompID        │ DAILY-PRODUCER    │ Message Generator
 56 │ TargetCompID        │ TRADE-SYSTEM      │ Message Recipient
 34 │ MsgSeqNum           │ 1000              │ Sequential Number (1-10)
 52 │ SendingTime         │ 20260512-090000   │ UTC Timestamp
 11 │ ClOrdID             │ 1000              │ Client Order ID
 17 │ ExecID              │ 1000              │ Execution ID
 20 │ ExecTransType       │ 0                 │ Transaction Type
150 │ ExecType            │ 2                 │ Execution Type (Trade=2)
 39 │ OrdStatus           │ 2                 │ Order Status (Filled=2)
 55 │ Symbol              │ BTC-USD           │ Security Symbol
 54 │ Side                │ 1                 │ Side (Buy=1, Sell=2)
 38 │ OrderQty            │ 0.1               │ Quantity (crypto: 0.1, stock: 100)
 44 │ Price               │ 45000.0           │ Current Market Price
 60 │ TransactTime        │ 20260512-090000   │ Trade Timestamp
200 │ AssetType           │ CRYPTO or STOCK   │ Security Type
 10 │ CheckSum            │ 000               │ Message Checksum

Message Breakdown:

Header Section (message metadata):
┌─ 8   BeginString: FIX.4.2
├─ 35  MsgType: ExecutionReport (8)
├─ 49  SenderCompID: DAILY-PRODUCER
├─ 56  TargetCompID: TRADE-SYSTEM
├─ 34  MsgSeqNum: 1000, 1001, ... 1009
└─ 52  SendingTime: 20260512-090000

Execution Details (what got executed):
├─ 11  ClOrdID: Unique order reference
├─ 17  ExecID: Execution reference
├─ 20  ExecTransType: 0 (default)
├─150 ExecType: 2 (Trade)
└─ 39  OrdStatus: 2 (Filled)

Security Information (what was traded):
├─ 55  Symbol: BTC-USD, AAPL, etc.
├─ 54  Side: 1 (Buy)
├─ 38  Quantity: 0.1 or 100
├─ 44  Price: Current market price
└─ 200 AssetType: CRYPTO or STOCK

Timestamp & Checksum:
├─ 60  TransactTime: UTC execution time
└─ 10  CheckSum: 000 (simplified)
```

---

## Message Flow Through System

```
FIX ExecutionReport Generated
│
│ "8=FIX.4.2|35=8|49=DAILY-PRODUCER|56=TRADE-SYSTEM|34=1000|..."
│
▼
┌─────────────────────────────────────────────────┐
│   Encode FIX Message (Add SOH Delimiters)      │
│   Replace | with \x01 (ASCII Start of Header)  │
├─────────────────────────────────────────────────┤
│ Input:  "8=FIX.4.2|35=8|49=DAILY-PRODUCER|..." │
│ Output: b"8=FIX.4.2\x0135=8\x0149=DAILY-...   │
│         (binary with SOH characters)           │
└─────────────────────────────────────────────────┘
│
├─────────────────────────┬──────────────────────┐
│                         │                      │
▼                         ▼                      ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐
│ KAFKA PRODUCER  │  │   SAVE JSON  │  │ GITHUB ARTIFACTS│
│                          │                  │
│ Topic: fix-trades│  │ daily_fix_   │  │ Upload & store  │
│ Message: binary │  │ messages.json│  │ for 30 days     │
│ Sent: immediate │  │ Saved: local │  │ Visible in UI    │
└──────────────────┘  └──────────────┘  └──────────────────┘
│                         │                  │
│ ┌─────────────────────┐ │ ┌──────────────┐ │
│ │  Kafka Consumer     │ │ │ File Backup  │ │
│ │ (kafka_fix...parser)│ │ │ (30 days)    │ │
│ └──────┬──────────────┘ │ └──────────────┘ │
│        │                │                  │
│        ▼                ▼                  ▼
│    ┌─────────────────────────────────────────────┐
│    │  Parse FIX Message (fix_parser.py)         │
│    │  Extract fields:                           │
│    │  {                                         │
│    │    '11': '1000'        (clordid)          │
│    │    '55': 'BTC-USD'     (symbol)           │
│    │    '54': '1'           (side)             │
│    │    '38': '0.1'         (qty)              │
│    │    '44': '45000.0'     (price)            │
│    │  }                                        │
│    └──────────┬────────────────────────────────┘
│               │
│               ▼
│    ┌─────────────────────────────────────────────┐
│    │  Insert into PostgreSQL Database           │
│    │  TABLE: trades                             │
│    │  VALUES: (clordid, symbol, side, qty,     │
│    │           price, raw)                      │
│    └──────────┬────────────────────────────────┘
│               │
│               ▼
│    ┌─────────────────────────────────────────────┐
│    │  Streamlit Dashboard Queries Database      │
│    │  SELECT * FROM trades ORDER BY id DESC     │
│    │  LIMIT 100                                 │
│    │                                             │
│    │  Display:                                  │
│    │  • All 100 latest trades                  │
│    │  • Total trades count                     │
│    │  • Bar chart by symbol                    │
│    └──────────┬────────────────────────────────┘
│               │
│               ▼
│    ┌─────────────────────────────────────────────┐
│    │  Playwright Captures Screenshot             │
│    │  • Full page screenshot                    │
│    │  • Includes metrics and charts             │
│    │  • High resolution PNG                     │
│    └──────────┬────────────────────────────────┘
│               │
│               ▼
│    ┌─────────────────────────────────────────────┐
│    │  Auto-Commit to GitHub                     │
│    │  • File: dashboard/img.png                 │
│    │  • Commit message: "chore: update ..."     │
│    │  • Author: GitHub Actions Bot              │
│    └────────────────────────────────────────────┘
```

---

## Daily Timeline (UTC)

```
9:00 AM UTC - DAILY FIX PRODUCER STARTS
│
├─ 9:00:00 - Check out code
├─ 9:00:05 - Set up Python 3.11
├─ 9:00:15 - Install dependencies
├─ 9:00:30 - Start producer script
│           ├─ API Call: CoinGecko (2s)
│           ├─ API Call: yfinance (3s)
│           └─ Generate FIX messages (1s)
├─ 9:00:40 - Attempt Kafka send
├─ 9:00:45 - Save JSON backup
├─ 9:00:50 - Upload artifacts
└─ 9:00:55 - Complete ✅
    Duration: ~55 seconds
    
9:30 AM UTC - DASHBOARD SCREENSHOT STARTS
│
├─ 9:30:00 - Check out code
├─ 9:30:05 - Set up Python 3.11
├─ 9:30:15 - Install dependencies (including Playwright)
├─ 9:30:45 - Get artifacts from producer
├─ 9:30:50 - Start PostgreSQL Docker service
├─ 9:31:00 - Wait for DB to be ready
├─ 9:31:02 - Initialize database schema
├─ 9:31:05 - Seed sample data (20 trades)
├─ 9:31:10 - Start Streamlit dashboard
├─ 9:31:30 - Wait for dashboard to load
├─ 9:31:35 - Screenshot dashboard
├─ 9:31:40 - Commit to repository
└─ 9:31:55 - Complete ✅
    Duration: ~2 minutes (120 seconds)

TOTAL DAILY GITHUB ACTIONS USAGE: ~3 minutes
FREE TIER LIMIT: 2,000 minutes/month
MONTHLY USAGE: ~90 minutes (4.5% of quota)
```

---

## Integration Points

```
FIX Trade System Ecosystem:

┌────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  External Data Sources                                             │
│  ├─ CoinGecko API (Cryptocurrency)                               │
│  └─ Yahoo Finance via yfinance (Stocks)                          │
│                                                                    │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Daily FIX Producer                     │
│  (producer/top_crypto_stocks_to_fix.py) │
│  • Fetches market data                  │
│  • Generates FIX messages               │
│  • Sends to Kafka                       │
│  • Saves JSON backup                    │
└──────────────┬────────────────────┬─────┘
               │                    │
               ▼                    ▼
        ┌─────────────┐      ┌─────────────────┐
        │ Kafka       │      │ JSON File       │
        │ fix-trades  │      │ daily_fix_...json│
        │ topic       │      │                 │
        └──────┬──────┘      └────────┬────────┘
               │                      │
               ▼                      │
┌──────────────────────────────────────────────────────────┐
│  Kafka Consumer + FIX Parser                            │
│  (consumer/kafka_fix_parser_consumer.py)                │
│  • Consume from fix-trades topic                        │
│  • Parse FIX messages (parser/fix_parser.py)           │
│  • Extract fields                                      │
│  • Insert into PostgreSQL                              │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  PostgreSQL Database                                    │
│  (postgres:13 service)                                  │
│  TABLE: trades                                          │
│    • id (SERIAL PRIMARY KEY)                           │
│    • clordid (TEXT) - Order ID                         │
│    • symbol (TEXT) - BTC-USD, AAPL, etc.              │
│    • side (TEXT) - Buy/Sell                            │
│    • qty (NUMERIC) - Quantity                          │
│    • price (NUMERIC) - Price                           │
│    • raw (TEXT) - Full FIX message                     │
│  RECORDS: 100+ daily (10 from producer + history)      │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  Streamlit Dashboard                                    │
│  (dashboard/streamlit_app.py)                           │
│  • Connects to PostgreSQL                              │
│  • Displays:                                           │
│    - Latest 100 trades (table)                        │
│    - Total trades (metric)                            │
│    - Trades by symbol (bar chart)                     │
│  • Auto-refreshes (10-second cache)                   │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  Playwright Screenshot                                  │
│  • Captures full dashboard                             │
│  • Browser: Chromium                                   │
│  • Format: PNG                                         │
│  • Output: dashboard/img.png                           │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  GitHub Repository                                      │
│  • Auto-commit screenshot                              │
│  • Make visible in README                              │
│  • Track history (timestamp in commit)                 │
│  • Display in Actions → Artifacts                      │
└──────────────────────────────────────────────────────────┘
```

---

## Key Statistics

```
Daily Production:
├─ FIX Messages: 10 total
│  ├─ Cryptocurrency: 5 (BTC, ETH, BNB, XRP, ADA)
│  └─ Stocks: 5 (AAPL, MSFT, GOOGL, AMZN, NVDA)
│
├─ API Calls: 2
│  ├─ CoinGecko: 1 (returns top 50+)
│  └─ yfinance: 1 (queries 5 stocks)
│
├─ Database Inserts: 10 (new records daily)
├─ Total Trades in DB: 100+ (with history)
│
├─ File Generation: 2
│  ├─ daily_fix_messages.json (~5-10 KB)
│  └─ dashboard/img.png (~100-500 KB)
│
└─ GitHub Actions Usage: ~3 minutes/day

Monthly Production:
├─ FIX Messages: 300 (10 × 30 days)
├─ Total Trades: 3,000+ (with history)
├─ API Calls: 60 (well under rate limits)
├─ GitHub Actions Minutes: ~90 (4.5% of free tier)
├─ Artifact Storage: ~30 MB × 30 = varies
└─ Repository Commits: 30 (daily screenshot updates)

System Performance:
├─ Producer Execution: ~30 seconds
├─ Screenshot Execution: ~90 seconds
├─ Total Workflow Time: ~2-3 minutes
├─ API Response Time: ~5 seconds
├─ Message Generation Rate: 10 messages/30 seconds
└─ Slack per day: ~20 minutes (margin for retries)
```

---

## System Health Indicators

```
Monitor These to Track System Health:

GitHub Actions:
├─ ✅ Daily FIX Producer runs successfully
├─ ✅ Dashboard Screenshot runs successfully
├─ ⚠️  No consecutive failures
├─ ⚠️  Execution time < 5 minutes
└─ ⚠️  Artifacts generated consistently

Data Quality:
├─ ✅ 10 FIX messages generated daily
├─ ✅ Crypto data includes 5 different symbols
├─ ✅ Stock data includes 5 different symbols
├─ ✅ Prices are positive and reasonable
└─ ✅ Timestamps are recent

Database:
├─ ✅ Records increasing (~10-20/day)
├─ ✅ No duplicate ClOrdIDs
├─ ✅ All fields populated
├─ ✅ Query performance acceptable
└─ ✅ Storage growing at expected rate

Dashboard:
├─ ✅ Displays latest 100 trades
├─ ✅ Charts render correctly
├─ ✅ Metrics update automatically
├─ ✅ Screenshot captures full page
└─ ✅ No rendering errors

API Health:
├─ ✅ CoinGecko API accessible (50+/min)
├─ ✅ Yahoo Finance accessible (no explicit limits)
├─ ✅ No rate limiting errors
├─ ✅ Response times < 5 seconds
└─ ✅ Data freshness < 1 day old
```

---

*End of Architecture & Data Flow Diagrams*

