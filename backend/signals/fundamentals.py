"""
Fundamentals signal: P/E ratio and earnings catalyst.
Returns a float 0.0 - 1.0.
"""
from datetime import datetime

import yfinance as yf

from logger import get_logger
from request_tracker import track_request

logger = get_logger(__name__)


@track_request("yfinance")
def compute_fundamentals_score(ticker: str) -> float:
    """
    Compute fundamentals score based on valuation and earnings catalyst.

    Components:
      - P/E ratio (0.60 weight): Lower is better, capped at P/E 40
      - Earnings catalyst (0.40 weight): Earnings date within 7 days
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
    except Exception as e:
        logger.debug(f"Failed to fetch info for {ticker}: {e}")
        return 0.0

    pe_score = _score_pe(info)
    earnings_score = _score_earnings_catalyst(t)

    return pe_score * 0.60 + earnings_score * 0.40


def _score_pe(info: dict) -> float:
    """
    P/E ratio scoring.

      P/E 0-15   -> 1.0
      P/E 15-25  -> 0.8
      P/E 25-35  -> 0.5
      P/E 35-40  -> 0.2
      P/E > 40   -> 0.0
      P/E < 0    -> 0.0 (negative earnings)
      P/E None   -> 0.3
    """
    pe = info.get("trailingPE") or info.get("forwardPE")

    if pe is None:
        return 0.3

    try:
        pe = float(pe)
    except (ValueError, TypeError):
        return 0.3

    if pe < 0:
        return 0.0
    elif pe <= 15:
        return 1.0
    elif pe <= 25:
        return 0.8
    elif pe <= 35:
        return 0.5
    elif pe <= 40:
        return 0.2
    else:
        return 0.0


def _score_earnings_catalyst(ticker_obj) -> float:
    """
    Earnings date proximity scoring.

      Within 7 days  -> 1.0 (strong catalyst)
      Within 14 days -> 0.5 (moderate catalyst)
      Otherwise      -> 0.0
    """
    try:
        cal = ticker_obj.calendar
        if cal is None or not isinstance(cal, dict):
            return 0.0

        earnings_dates = cal.get("Earnings Date", [])
        if not earnings_dates:
            return 0.0

        now = datetime.now()

        for ed in earnings_dates:
            if hasattr(ed, "date"):
                ed = ed.date()
            elif isinstance(ed, str):
                from dateutil import parser
                ed = parser.parse(ed).date()
            else:
                continue

            days_until = (ed - now.date()).days

            if 0 <= days_until <= 7:
                return 1.0
            elif 0 <= days_until <= 14:
                return 0.5

        return 0.0

    except Exception as e:
        logger.debug(f"Earnings date lookup failed: {e}")
        return 0.0
