"""
Sentiment signal: aggregates news/social sentiment from three sources.
Returns a float 0.0 - 1.0.

Sources:
  1. Yahoo Finance news headlines (via yfinance)
  2. Reddit r/stocks + r/wallstreetbets (public .json API)
  3. Finviz news headlines (web scraping)

All sources are optional — if any fail, they are skipped gracefully.
"""
import random
import time

from bs4 import BeautifulSoup
from textblob import TextBlob
import yfinance as yf

from logger import get_logger
from request_tracker import tracker, track_request

logger = get_logger(__name__)

REDDIT_SUBREDDITS = ["stocks", "wallstreetbets"]
REDDIT_SEARCH_URL = "https://www.reddit.com/r/{}/search.json"
FINVIZ_QUOTE_URL = "https://finviz.com/quote.ashx?t={}&ty=c&p=d&b=1"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def compute_sentiment_score(ticker: str) -> float:
    """
    Aggregate sentiment score from all available sources.

    1. Collect headlines/titles from each source
    2. Run TextBlob sentiment on each
    3. Compute weighted average polarity
    4. Boost based on mention count
    5. Normalize to 0.0-1.0
    """
    all_texts: list[str] = []

    yahoo_texts = _fetch_yahoo_news(ticker)
    all_texts.extend(yahoo_texts)

    reddit_texts = _fetch_reddit_mentions(ticker)
    all_texts.extend(reddit_texts)

    finviz_texts = _fetch_finviz_news(ticker)
    all_texts.extend(finviz_texts)

    if not all_texts:
        return 0.5  # Neutral — no data

    polarities = []
    for text in all_texts:
        try:
            blob = TextBlob(text)
            polarities.append(blob.sentiment.polarity)
        except Exception:
            continue

    if not polarities:
        return 0.5

    avg_polarity = sum(polarities) / len(polarities)

    # Normalize from [-1, 1] to [0, 1]
    base_score = (avg_polarity + 1.0) / 2.0

    # Coverage boost: more mentions = higher conviction
    mention_count = len(all_texts)
    if mention_count >= 20:
        coverage_multiplier = 1.2
    elif mention_count >= 5:
        coverage_multiplier = 1.0 + (mention_count - 5) / 15 * 0.2
    else:
        coverage_multiplier = 0.8 + mention_count / 5 * 0.2

    return min(1.0, base_score * coverage_multiplier)


@track_request("yfinance")
def _fetch_yahoo_news(ticker: str) -> list[str]:
    try:
        t = yf.Ticker(ticker)
        news = t.news
        if not news:
            return []

        headlines = []
        for item in news[:15]:
            title = item.get("title", "")
            if title:
                headlines.append(title)

        logger.debug(f"Yahoo news: {len(headlines)} headlines for {ticker}")
        return headlines
    except Exception as e:
        logger.debug(f"Yahoo news failed for {ticker}: {e}")
        return []


def _fetch_reddit_mentions(ticker: str) -> list[str]:
    texts = []

    for subreddit in REDDIT_SUBREDDITS:
        try:
            url = REDDIT_SEARCH_URL.format(subreddit)
            params = {
                "q": ticker,
                "restrict_sr": "on",
                "sort": "new",
                "t": "week",
                "limit": 10,
            }
            headers = {"User-Agent": "StockScanner/1.0 (educational project)"}

            resp = tracker.get(
                url,
                source="reddit",
                ticker=ticker,
                params=params,
                headers=headers,
                timeout=10,
            )

            if resp.status_code == 429:
                logger.warning(f"Reddit rate limited for r/{subreddit}")
                continue
            if resp.status_code != 200:
                continue

            data = resp.json()
            posts = data.get("data", {}).get("children", [])

            for post in posts:
                post_data = post.get("data", {})
                title = post_data.get("title", "")
                selftext = post_data.get("selftext", "")[:200]

                combined = f"{title} {selftext}"
                if f"${ticker}" in combined or f" {ticker} " in combined:
                    texts.append(title)

            time.sleep(random.uniform(0.3, 0.7))

        except Exception as e:
            logger.debug(f"Reddit search failed for r/{subreddit} '{ticker}': {e}")
            continue

    return texts


def _fetch_finviz_news(ticker: str) -> list[str]:
    try:
        url = FINVIZ_QUOTE_URL.format(ticker)
        resp = tracker.get(
            url,
            source="finviz",
            ticker=ticker,
            headers=HEADERS,
            timeout=10,
        )

        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        news_table = soup.find("table", {"id": "news-table"})
        if not news_table:
            return []

        headlines = []
        rows = news_table.find_all("tr")
        for row in rows[:10]:
            link = row.find("a")
            if link:
                headlines.append(link.text.strip())

        logger.debug(f"Finviz news: {len(headlines)} headlines for {ticker}")
        return headlines
    except Exception as e:
        logger.debug(f"Finviz news failed for {ticker}: {e}")
        return []
