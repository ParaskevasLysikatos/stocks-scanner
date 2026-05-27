# Stock Speculation Scanner

A web-based tool that scans ~2,700 US stocks (S&P 500 + NASDAQ 100 + Russell 2000) and identifies the **top 10 most likely short-term gainers** based on a composite scoring system, with price targets and analyst ratings.

> **DISCLAIMER:** This is an educational/research tool. It does NOT constitute financial advice. All signals are speculative. Always do your own due diligence before making any investment decisions.

## What It Does

Scores each stock 0–100 using four signals:

| Signal | Weight | Logic |
|--------|--------|-------|
| Technical | 35% | RSI recovering (30–50), MACD bullish crossover, price above 50-day MA |
| Volume Spike | 25% | Today's volume > 2x the 20-day average |
| Sentiment | 25% | News + Reddit buzz via TextBlob polarity |
| Fundamentals | 15% | P/E < 40, earnings within 7 days (catalyst) |

Returns the top 10 highest-scoring stocks with:
- **Composite score** and per-signal breakdowns
- **Current price** and **52-week range** (visual position indicator)
- **Analyst price target** with upside/downside percentage
- **Analyst consensus rating** (Strong Buy / Buy / Hold / Sell)
- **Smart notes**: Near 52W low, Analyst upside %, Analyst Buy consensus, volume spikes, earnings catalysts

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose

No API keys, no database, no accounts needed. All data sources are free.

## How to Run

```bash
docker-compose up --build
```

Then open **http://localhost** in your browser.

## How to Use

1. Click **"Scan Market"**
2. Wait 10–15 minutes (the scanner processes ~2,700 tickers sequentially to avoid rate limiting)
3. View the filtered results table with scores, prices, targets, and ratings
4. Adjust filters to narrow or broaden results (no re-scan needed)

**Recommended usage:** Once daily, before US market open (09:30 ET).

## Filters

The results are filtered client-side with these defaults (adjustable after scan):

| Filter | Default | Description |
|--------|---------|-------------|
| Max Price | $500 | Only show stocks priced below this threshold |
| Analyst Rating | Strong Buy, Buy | Only show stocks with green analyst ratings |
| 52W Lower Half | On | Only show stocks trading in the lower half of their 52-week range |

The backend sends up to 50 top-scoring results. Filters are applied instantly in the browser — change any filter and the table updates immediately without re-scanning.

## Results Table Columns

| Column | Description |
|--------|-------------|
| Score | Composite 0–100 score across all signals |
| Price | Current stock price |
| 52W Range | 52-week low — high with dot showing current price position |
| Target | Mean analyst price target with upside % |
| Rating | Analyst consensus: Strong Buy, Buy, Hold, Sell |
| Technical | Technical signal score (out of 35) |
| Volume | Volume spike score (out of 25) |
| Sentiment | News/social sentiment score (out of 25) |
| Fundamentals | P/E + earnings catalyst score (out of 15) |
| Notes | Key signals: volume spikes, analyst buy, near 52W low, etc. |

## Architecture

```
Frontend (Vue 3 + Nginx, port 80)
  └── /api/* proxied to ──→ Backend (FastAPI + Uvicorn, port 8000)
```

- **Frontend**: Vue 3 (Vite build) served by Nginx
- **Backend**: FastAPI + Uvicorn (Python 3.13)
- **Communication**: Server-Sent Events (SSE) for real-time progress
- **Deployment**: Docker Compose (two services, single exposed port :80)

## Project Structure

```
stock-scanner/
├── docker-compose.yml
├── README.md
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── main.py                # FastAPI app: POST /api/scan, GET /api/health, GET /api/logs
│   ├── scanner.py             # Scan orchestrator: batch download → score → top 10
│   ├── universe.py            # Ticker universe: S&P500 + NASDAQ100 + Russell2000
│   ├── logger.py              # Rotating file + console logging
│   ├── request_tracker.py     # External request audit log (JSON-lines)
│   ├── requirements.txt
│   └── signals/
│       ├── technical.py       # RSI, MACD, 50-day MA
│       ├── volume.py          # Volume spike detection
│       ├── sentiment.py       # Yahoo News + Reddit + Finviz headlines via TextBlob
│       └── fundamentals.py    # P/E ratio + earnings catalyst
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf             # Serves dist/, proxies /api/* to backend
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue            # Main layout, SSE handler, disclaimer
│       └── components/
│           ├── ScanButton.vue    # Scan trigger + progress bar
│           └── ResultsTable.vue  # Results table with prices, targets, ratings
└── logs/                      # (gitignored) created at runtime
    ├── scanner.log            # General app logs (rotating, 5MB)
    └── external_requests.log  # Per-request audit log (JSON-lines, 10MB)
```

## Data Sources (all free, no API keys)

| Source | Data | Method |
|--------|------|--------|
| yfinance | Price, volume, fundamentals, news, analyst targets, ratings | Python library |
| Finviz | News headlines, screener fallback (Russell 2000) | Web scraping |
| Reddit | r/stocks + r/wallstreetbets mention frequency & sentiment | Public .json API |
| Wikipedia | S&P 500 and NASDAQ 100 ticker lists | pandas read_html |
| iShares | Russell 2000 ETF holdings | CSV download |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scan` | POST | Start a full market scan (returns SSE stream) |
| `/api/health` | GET | Health check |
| `/api/logs` | GET | Per-source request stats + recent failures |

## Monitoring & Logs

- **`GET /api/logs`** — Returns per-source success/fail stats and the last 50 failed external requests
- **`logs/external_requests.log`** — JSON-lines audit of every external HTTP request with timestamp, source, URL, status code, latency, and success/failure
- **`logs/scanner.log`** — General application log (rotating, 5MB max, 3 backups)
- **SSE summary event** — Per-source request summary sent to frontend at scan completion

## .gitignore

The following are excluded from version control:
- `logs/` — runtime log files
- `node_modules/` — frontend dependencies
- `dist/` — frontend build output
- `__pycache__/`, `*.pyc` — Python bytecode
- `.env` — environment variables

## Limitations

- Rate limiting may cause some sources to be skipped (graceful degradation — Reddit is heavily rate-limited)
- Data is only as fresh as the last scan (no real-time streaming)
- Sentiment analysis uses simple TextBlob polarity (not ML-based)
- Analyst targets are consensus averages — individual analyst accuracy varies
- This is a speculative screener, not a prediction engine — past signals don't guarantee future price movement
