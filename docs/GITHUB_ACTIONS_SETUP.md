# GitHub Actions Setup Guide

This guide explains how to set up and configure the automated GitHub Actions for the FIX Trade System.

## Overview

Two automated workflows run daily:

1. **Daily FIX Producer** (`daily_fix_producer.yml`)
   - Time: 9:00 AM UTC daily
   - Fetches top 5 cryptocurrencies and stocks
   - Generates FIX messages
   - Saves artifacts

2. **Dashboard Screenshot Update** (`update_dashboard_screenshot.yml`)
   - Time: 9:30 AM UTC daily (after producer completes)
   - Captures dashboard screenshot
   - Updates repository

## Prerequisites

1. **GitHub Repository Access**
   - Push `.github/workflows/` directory with both YAML files
   - Ensure GitHub Actions is enabled (Settings → Actions)

2. **Required Secrets (Optional)**
   - For external Kafka servers, set `KAFKA_BOOTSTRAP_SERVERS` as a secret
   - How to set: Settings → Secrets and variables → Actions → New repository secret

## Workflow Configurations

### Daily FIX Producer Workflow

**File:** `.github/workflows/daily_fix_producer.yml`

**Schedule:**
- Default: Daily at 9:00 AM UTC (`0 9 * * *`)
- Edit the `cron` expression to change timing

**Cron Format (UTC):**
```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday - Saturday)
│ │ │ │ │
│ │ │ │ │
0 9 * * *
```

**Examples:**
- `0 9 * * *` - Every day at 9:00 AM UTC
- `0 9 * * 1` - Every Monday at 9:00 AM UTC
- `0 9 1 * *` - Every 1st of month at 9:00 AM UTC
- `0 */6 * * *` - Every 6 hours at minute 0

**Manual Trigger:**
```bash
gh workflow run daily_fix_producer.yml
```

### Dashboard Screenshot Workflow

**File:** `.github/workflows/update_dashboard_screenshot.yml`

**Schedule:**
- Default: Daily at 9:30 AM UTC (`30 9 * * *`)
- Runs 30 minutes after producer completes

**Manual Trigger:**
```bash
gh workflow run update_dashboard_screenshot.yml
```

## Configuration Options

### Changing Execution Time

Edit the `cron` value in the workflow file:

```yaml
on:
  schedule:
    - cron: '0 14 * * *'  # Change to 2:00 PM UTC
```

### Using External Kafka Server

For production deployments with external Kafka:

1. Add GitHub Secret:
   - Go to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `KAFKA_BOOTSTRAP_SERVERS`
   - Value: `your-kafka-server:9092`

2. The workflow automatically uses the secret if set

### Customizing Data Sources

#### Top Cryptocurrencies

Edit `producer/top_crypto_stocks_to_fix.py`:

```python
def get_top_cryptocurrencies(limit: int = 5) -> List[Dict]:
    # Change limit parameter to fetch more/fewer cryptocurrencies
    cryptos = get_top_cryptocurrencies(limit=10)  # Fetch top 10 instead
```

Available APIs:
- **CoinGecko** (current, free): Most comprehensive
- **CoinMarketCap**: Alternative (requires API key)

#### Top Stocks

Edit `producer/top_crypto_stocks_to_fix.py`:

```python
def get_top_stocks(limit: int = 5) -> List[Dict]:
    stock_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'BRK.B', ...]
    # Modify this list to track different stocks
```

Alternative sources:
- **Alpha Vantage API**: More comprehensive data
- **IEX Cloud**: Real-time quote data
- **Financial Modeling Prep**: Fundamentals data

## Monitoring & Troubleshooting

### View Workflow Runs

1. Go to repository on GitHub
2. Click **Actions** tab
3. Click the workflow name to see runs
4. Click a run to see logs

### Common Issues

#### Issue: Workflow doesn't run on schedule

**Solution:**
- Workflows don't run if repository is inactive for 60 days
- Make a commit to re-enable
- Verify Actions are enabled in Settings

#### Issue: Database connection timeout

**Solution (Dashboard Screenshot workflow):**
- Increase sleep time in the workflow:
  ```yaml
  - run: sleep 15  # Increase from 2 to 15 seconds
  ```

#### Issue: Screenshot is blank

**Solution:**
- Streamlit might not be fully loaded
- Increase wait time in Python script:
  ```python
  page.goto('http://localhost:8501', wait_until='networkidle')
  time.sleep(5)  # Increase from 3 to 5 seconds
  ```

#### Issue: API rate limiting

**Solution (for crypto/stock data):**
- CoinGecko: Free tier allows ~50 calls/min
- Add retry logic in producer:
  ```python
  import time
  time.sleep(60)  # Rate limit: wait before retry
  ```

### View Artifacts

1. Go to Actions tab
2. Click on a workflow run
3. Scroll down to "Artifacts" section
4. Download `daily-fix-messages` artifact
5. Extract `daily_fix_messages.json`

### Logs

Access detailed logs:
1. Actions → Workflow run → Step name
2. Expand any step to see full output
3. Look for errors marked with ❌

## Advanced Configuration

### Conditional Execution

Run workflow only for specific branches:

```yaml
on:
  schedule:
    - cron: '0 9 * * *'
  push:
    branches:
      - main
      - production
```

### Parallel Workflows

Use `jobs.needs` to create dependencies:

```yaml
jobs:
  producer:
    runs-on: ubuntu-latest
    # ... producer job
  
  screenshot:
    runs-on: ubuntu-latest
    needs: producer  # Wait for producer to complete
    # ... screenshot job
```

### Notifications

Add Slack/email notifications on failure:

```yaml
- name: Notify on failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {"text": "Daily FIX Producer failed!"}
```

### Performance Optimization

**Reduce execution time:**

```yaml
- name: Install dependencies (cached)
  run: |
    pip install --upgrade pip
    pip install -r requirements_lite.txt  # Smaller requirements file
```

## Security Best Practices

1. **Never commit secrets** in code or .env files
2. **Use GitHub Secrets** for sensitive data
3. **Review workflow permissions** in Settings → Actions
4. **Rotate credentials regularly** if using external services
5. **Audit action usage** for third-party actions

## Updating Workflows

To update workflows:

1. Make changes to `.github/workflows/*.yml`
2. Commit and push to main branch
3. Changes take effect immediately
4. Next scheduled run uses new configuration

## Support

For issues with:
- **FIX message generation**: See `producer/top_crypto_stocks_to_fix.py`
- **Dashboard**: See `dashboard/streamlit_app.py`
- **GitHub Actions**: Refer to [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Resources

- [GitHub Actions Cron Syntax](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [CoinGecko API](https://www.coingecko.com/api/documentations/v3)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [FIX Protocol Specification](https://en.wikipedia.org/wiki/Financial_Information_eXchange)

