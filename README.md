# Stock Speculation Scanner

A web-based tool that scans ~2,700 US stocks (S&P 500 + NASDAQ 100 + Russell 2000) and identifies the **top 10 most likely short-term gainers** based on a composite scoring system.

> **DISCLAIMER:** This is an educational/research tool. It does NOT constitute financial advice. All signals are speculative. Always do your own due diligence before making any investment decisions.

## What It Does

Scores each stock 0–100 using four signals:

| Signal | Weight | Logic |
|--------|--------|-------|
| Technical | 35% | RSI recovering (30–50), MACD bullish crossover, price above 50-day MA |
| Volume Spike | 25% | Today's volume > 2x the 20-day average |
| Sentiment | 25% | News + Reddit buzz via TextBlob polarity |
| Fundamentals | 15% | P/E < 40, earnings within 7 days (catalyst) |

Returns the top 10 highest-scoring stocks — these are the tickers showing the strongest short-term bullish signals.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose

That's it. No API keys, no database, no accounts needed.

## How to Run

```bash
docker-compose up --build
```

Then open **http://localhost** in your browser.

## How to Use

1. Click **"Scan Market"**
2. Wait 10–15 minutes (the scanner processes ~2,700 tickers sequentially to avoid rate limiting)
3. View the top 10 results table with scores and breakdowns

**Recommended usage:** Once daily, before US market open (09:30 ET).

## Architecture

```
Frontend (Vue 3 + Nginx, port 80)
  └── /api/* proxied to ──→ Backend (FastAPI + Uvicorn, port 8000)
```

- Real-time progress updates via Server-Sent Events (SSE)
- All external requests are logged to `logs/external_requests.log` (JSON-lines)
- General logs in `logs/scanner.log`

## Data Sources (all free, no API keys)

| Source | Data | Method |
|--------|------|--------|
| yfinance | Price, volume, fundamentals, news | Python library |
| Finviz | News headlines, screener fallback | Web scraping |
| Reddit | r/stocks + r/wallstreetbets mentions | Public .json API |
| Wikipedia / iShares | Ticker universe lists | pandas read_html / CSV |

## Monitoring & Logs

- **`GET /api/logs`** — Returns per-source success/fail stats + recent failures
- **`logs/external_requests.log`** — JSON-lines audit of every external HTTP request
- **`logs/scanner.log`** — General application log (rotating, 5MB max)

## Limitations

- Rate limiting may cause some sources to be skipped (graceful degradation)
- Data is only as fresh as the last scan (no real-time streaming)
- Sentiment analysis uses simple TextBlob polarity (not ML-based)
- This is a speculative screener, not a prediction engine — past signals don't guarantee future price movement
