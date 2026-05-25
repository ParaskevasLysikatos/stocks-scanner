"""
Fetches the combined ticker universe: S&P 500 + NASDAQ 100 + Russell 2000.
All sourced from public web pages via pandas.read_html() and requests.
"""
import random
import time
from io import StringIO

import pandas as pd
from bs4 import BeautifulSoup

from logger import get_logger
from request_tracker import tracker

logger = get_logger(__name__)

SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
NASDAQ100_URL = "https://en.wikipedia.org/wiki/Nasdaq-100"
RUSSELL2000_CSV_URL = (
    "https://www.ishares.com/us/products/239710/"
    "ishares-russell-2000-etf/1467271812596.ajax"
    "?fileType=csv&fileName=IWM_holdings&dataType=fund"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def get_sp500_tickers() -> list[str]:
    try:
        resp = tracker.get(SP500_URL, source="wikipedia", headers=HEADERS, timeout=30)
        resp.raise_for_status()
        tables = pd.read_html(StringIO(resp.text), header=0)
        df = tables[0]
        tickers = df["Symbol"].str.strip().tolist()
        tickers = [t.replace(".", "-") for t in tickers]
        logger.info(f"Fetched {len(tickers)} S&P 500 tickers")
        return tickers
    except Exception as e:
        logger.error(f"Failed to fetch S&P 500 tickers: {e}")
        return []


def get_nasdaq100_tickers() -> list[str]:
    try:
        resp = tracker.get(NASDAQ100_URL, source="wikipedia", headers=HEADERS, timeout=30)
        resp.raise_for_status()
        tables = pd.read_html(StringIO(resp.text), header=0)
        for table in tables:
            if "Ticker" in table.columns:
                tickers = table["Ticker"].str.strip().tolist()
                logger.info(f"Fetched {len(tickers)} NASDAQ 100 tickers")
                return tickers
        logger.warning("No 'Ticker' column found in NASDAQ 100 tables")
        return []
    except Exception as e:
        logger.error(f"Failed to fetch NASDAQ 100 tickers: {e}")
        return []


def get_russell2000_tickers() -> list[str]:
    try:
        resp = tracker.get(
            RUSSELL2000_CSV_URL, source="ishares", headers=HEADERS, timeout=30
        )
        resp.raise_for_status()

        lines = resp.text.strip().split("\n")
        start_idx = 0
        for i, line in enumerate(lines):
            if "Ticker" in line:
                start_idx = i
                break

        csv_data = "\n".join(lines[start_idx:])
        df = pd.read_csv(StringIO(csv_data))

        ticker_col = [c for c in df.columns if "ticker" in c.lower()]
        if not ticker_col:
            logger.warning("No ticker column in iShares CSV")
            return _get_russell2000_fallback()

        tickers = df[ticker_col[0]].dropna().astype(str).str.strip().tolist()
        tickers = [t for t in tickers if t and (t.isalpha() or "-" in t)]
        tickers = [t.replace(".", "-") for t in tickers]
        logger.info(f"Fetched {len(tickers)} Russell 2000 tickers from iShares")
        return tickers
    except Exception as e:
        logger.warning(f"Failed to fetch Russell 2000 tickers: {e}. Using fallback.")
        return _get_russell2000_fallback()


def _get_russell2000_fallback() -> list[str]:
    """Fallback: scrape small-cap tickers from Finviz."""
    tickers = []
    try:
        base_url = "https://finviz.com/screener.ashx?v=111&f=cap_smallover&r={}"

        for start in range(1, 2001, 20):
            url = base_url.format(start)
            try:
                resp = tracker.get(
                    url, source="finviz", headers=HEADERS, timeout=15
                )
                if resp.status_code != 200:
                    break
            except Exception:
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.find_all("a", class_="screener-link-primary")
            if not links:
                break
            for link in links:
                tickers.append(link.text.strip())

            time.sleep(random.uniform(0.5, 1.0))

        logger.info(f"Fetched {len(tickers)} small-cap tickers from Finviz fallback")
    except Exception as e:
        logger.error(f"Finviz fallback also failed: {e}")

    return tickers


def get_universe() -> list[str]:
    """Returns deduplicated, sorted list of all tickers."""
    sp500 = get_sp500_tickers()
    nasdaq100 = get_nasdaq100_tickers()
    russell2000 = get_russell2000_tickers()

    all_tickers = set(sp500 + nasdaq100 + russell2000)
    all_tickers = {t for t in all_tickers if t and len(t) <= 5}

    universe = sorted(all_tickers)
    logger.info(f"Total universe: {len(universe)} unique tickers")
    return universe
