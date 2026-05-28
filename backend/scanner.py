"""
Orchestrates the full scan pipeline:
1. Fetch ticker universe
2. Batch-download price/volume data via yfinance
3. Compute technical + volume scores (from batch data)
4. For top candidates, fetch sentiment + fundamentals (per-ticker)
5. Compute composite scores, return top 10
"""
import asyncio
import glob
import json
import os
import random
from typing import AsyncGenerator, Any

import yfinance as yf
import pandas as pd

from logger import get_logger
from request_tracker import tracker, track_request
from universe import get_universe
from signals.technical import compute_technical_score
from signals.volume import compute_volume_score
from signals.sentiment import compute_sentiment_score
from signals.fundamentals import compute_fundamentals_score

logger = get_logger(__name__)

BATCH_SIZE = 50
PRICE_PERIOD = "3mo"
TOP_CANDIDATES = 200
MAX_RESULTS = 50


async def run_scan() -> AsyncGenerator[dict, None]:
    """
    Async generator that yields SSE events during the scan.

    Yields:
      {"event": "progress", "data": json_str}
      {"event": "result",   "data": json_str}
      {"event": "error",    "data": json_str}
    """
    # Reset request tracker and clear old log files
    tracker.reset()
    _clear_logs()

    # --- Phase 0: Fetch universe ---
    yield _progress(0, "Fetching ticker universe...")

    universe = await asyncio.to_thread(get_universe)
    if not universe:
        yield _progress(0, "ERROR: Could not fetch ticker universe")
        yield {"event": "error", "data": json.dumps({"message": "Failed to fetch ticker universe"})}
        return

    total = len(universe)
    yield _progress(2, f"Found {total} tickers. Starting price data download...")

    # --- Phase 1: Batch download + tech/volume scores ---
    batches = [universe[i:i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    all_scores: dict[str, dict[str, Any]] = {}

    for batch_idx, batch in enumerate(batches):
        pct = 2 + int((batch_idx / len(batches)) * 60)
        yield _progress(pct, f"Downloading batch {batch_idx + 1}/{len(batches)} ({len(batch)} tickers)...")

        try:
            batch_data = await asyncio.to_thread(_download_batch, batch)
        except Exception as e:
            logger.warning(f"Batch {batch_idx + 1} failed: {e}")
            continue

        for ticker in batch:
            try:
                df = _extract_ticker_df(batch_data, ticker)
                if df is None or len(df) < 50:
                    continue

                tech_score = compute_technical_score(df)
                vol_score = compute_volume_score(df)

                all_scores[ticker] = {
                    "technical": tech_score,
                    "volume": vol_score,
                    "preliminary": tech_score * 0.35 + vol_score * 0.25,
                }
            except Exception as e:
                logger.debug(f"Skipping {ticker}: {e}")
                continue

        await asyncio.sleep(random.uniform(1.0, 2.0))

    yield _progress(62, f"Phase 1 complete. {len(all_scores)} tickers scored. Selecting top candidates...")

    # --- Phase 2: Select top candidates ---
    sorted_tickers = sorted(
        all_scores.keys(),
        key=lambda t: all_scores[t]["preliminary"],
        reverse=True,
    )
    candidates = sorted_tickers[:TOP_CANDIDATES]

    yield _progress(65, f"Analyzing sentiment & fundamentals for top {len(candidates)} candidates...")

    # --- Phase 3: Per-ticker deep analysis ---
    for i, ticker in enumerate(candidates):
        pct = 65 + int((i / len(candidates)) * 30)

        if i % 20 == 0:
            yield _progress(pct, f"Deep analysis: {i}/{len(candidates)} ({ticker})...")

        try:
            sent_score = await asyncio.to_thread(compute_sentiment_score, ticker)
            fund_score = await asyncio.to_thread(compute_fundamentals_score, ticker)

            all_scores[ticker]["sentiment"] = sent_score
            all_scores[ticker]["fundamentals"] = fund_score

        except Exception as e:
            logger.debug(f"Deep analysis failed for {ticker}: {e}")
            all_scores[ticker].setdefault("sentiment", 0.0)
            all_scores[ticker].setdefault("fundamentals", 0.0)

        # Compute final composite
        s = all_scores[ticker]
        s["composite"] = (
            s["technical"] * 0.35
            + s["volume"] * 0.25
            + s.get("sentiment", 0.0) * 0.25
            + s.get("fundamentals", 0.0) * 0.15
        ) * 100

        await asyncio.sleep(random.uniform(0.3, 0.7))

    # --- Phase 4: Build results (up to MAX_RESULTS with valid price data) ---
    yield _progress(96, "Computing final rankings...")

    final_sorted = sorted(
        candidates,
        key=lambda t: all_scores[t].get("composite", 0),
        reverse=True,
    )

    results = []
    for ticker in final_sorted:
        if len(results) >= MAX_RESULTS:
            break

        s = all_scores[ticker]
        info = await asyncio.to_thread(_get_ticker_info, ticker)

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        if current_price is None:
            continue

        target_price = info.get("targetMeanPrice")
        upside_pct = None
        if target_price and current_price:
            upside_pct = round(((target_price / current_price) - 1) * 100, 1)

        results.append({
            "rank": len(results) + 1,
            "ticker": ticker,
            "company": info.get("shortName", ticker),
            "sector": info.get("sector", "N/A"),
            "score": round(s["composite"], 1),
            "technical_score": round(s["technical"] * 35, 1),
            "volume_score": round(s["volume"] * 25, 1),
            "sentiment_score": round(s.get("sentiment", 0) * 25, 1),
            "fundamentals_score": round(s.get("fundamentals", 0) * 15, 1),
            "current_price": current_price,
            "target_price": target_price,
            "target_low": info.get("targetLowPrice"),
            "target_high": info.get("targetHighPrice"),
            "week52_low": info.get("fiftyTwoWeekLow"),
            "week52_high": info.get("fiftyTwoWeekHigh"),
            "upside_pct": upside_pct,
            "recommendation": info.get("recommendationKey", "N/A"),
            "num_analysts": info.get("numberOfAnalystOpinions", 0),
            "notes": _build_notes(s, info),
        })

    logger.info(f"Built {len(results)} results from {len(final_sorted)} candidates")

    # Log scan summary
    summary = tracker.get_summary()
    logger.info(f"Scan complete. Request tracker summary: {json.dumps(summary)}")

    yield _progress(100, "Scan complete!")
    yield {"event": "summary", "data": json.dumps({"request_summary": summary})}
    yield {"event": "result", "data": json.dumps({"stocks": results})}


@track_request("yfinance")
def _download_batch(tickers: list[str]) -> pd.DataFrame:
    data = yf.download(
        tickers,
        period=PRICE_PERIOD,
        group_by="ticker",
        threads=True,
        progress=False,
    )
    return data


def _extract_ticker_df(batch_data: pd.DataFrame, ticker: str) -> pd.DataFrame | None:
    try:
        if isinstance(batch_data.columns, pd.MultiIndex):
            df = batch_data[ticker].dropna()
        else:
            df = batch_data.dropna()

        if df.empty:
            return None
        return df
    except (KeyError, TypeError):
        return None


@track_request("yfinance")
def _get_ticker_info(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        return t.info or {}
    except Exception:
        return {}


def _build_notes(scores: dict, info: dict) -> str:
    notes = []
    if scores.get("volume", 0) > 0.8:
        notes.append("High volume spike")
    if scores.get("technical", 0) > 0.7:
        notes.append("Strong technicals")
    if scores.get("sentiment", 0) > 0.6:
        notes.append("Positive sentiment")
    if scores.get("fundamentals", 0) > 0.5:
        notes.append("Earnings catalyst")

    # Bargain indicators from price data
    current = info.get("currentPrice") or info.get("regularMarketPrice")
    low52 = info.get("fiftyTwoWeekLow")
    target = info.get("targetMeanPrice")
    rec = info.get("recommendationKey", "")

    if current and low52 and low52 > 0:
        if current <= low52 * 1.10:
            notes.append("Near 52W low")

    if current and target and current > 0:
        upside = ((target / current) - 1) * 100
        if upside >= 20:
            notes.append(f"Analyst upside +{upside:.0f}%")

    if rec in ("strong_buy", "buy"):
        notes.append("Analyst Buy")

    return "; ".join(notes) if notes else "Moderate signals"


def _clear_logs():
    """Remove old log files before a new scan."""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    for f in glob.glob(os.path.join(log_dir, "*.log*")):
        try:
            os.remove(f)
        except OSError:
            pass
    logger.info("Cleared old log files")


async def run_custom_scan(tickers: list[str]) -> AsyncGenerator[dict, None]:
    """
    Scan a specific list of tickers (up to 10).
    Simplified pipeline: download → score all signals → build results.
    """
    yield _progress(0, f"Downloading data for {len(tickers)} tickers...")

    try:
        batch_data = await asyncio.to_thread(_download_batch, tickers)
    except Exception as e:
        logger.error(f"Custom scan download failed: {e}")
        yield {"event": "error", "data": json.dumps({"message": f"Download failed: {e}"})}
        return

    yield _progress(10, "Scoring tickers...")

    scored = []
    for i, ticker in enumerate(tickers):
        pct = 10 + int((i / len(tickers)) * 75)
        yield _progress(pct, f"Analyzing {ticker} ({i + 1}/{len(tickers)})...")

        try:
            df = _extract_ticker_df(batch_data, ticker)
            if df is None or len(df) < 50:
                logger.debug(f"Custom scan: skipping {ticker} (insufficient data)")
                continue

            tech_score = compute_technical_score(df)
            vol_score = compute_volume_score(df)
            sent_score = await asyncio.to_thread(compute_sentiment_score, ticker)
            fund_score = await asyncio.to_thread(compute_fundamentals_score, ticker)

            composite = (
                tech_score * 0.35
                + vol_score * 0.25
                + sent_score * 0.25
                + fund_score * 0.15
            ) * 100

            info = await asyncio.to_thread(_get_ticker_info, ticker)
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            if current_price is None:
                continue

            target_price = info.get("targetMeanPrice")
            upside_pct = None
            if target_price and current_price:
                upside_pct = round(((target_price / current_price) - 1) * 100, 1)

            scored.append({
                "ticker": ticker,
                "company": info.get("shortName", ticker),
                "sector": info.get("sector", "N/A"),
                "score": round(composite, 1),
                "technical_score": round(tech_score * 35, 1),
                "volume_score": round(vol_score * 25, 1),
                "sentiment_score": round(sent_score * 25, 1),
                "fundamentals_score": round(fund_score * 15, 1),
                "current_price": current_price,
                "target_price": target_price,
                "target_low": info.get("targetLowPrice"),
                "target_high": info.get("targetHighPrice"),
                "week52_low": info.get("fiftyTwoWeekLow"),
                "week52_high": info.get("fiftyTwoWeekHigh"),
                "upside_pct": upside_pct,
                "recommendation": info.get("recommendationKey", "N/A"),
                "num_analysts": info.get("numberOfAnalystOpinions", 0),
                "notes": _build_notes(
                    {"technical": tech_score, "volume": vol_score,
                     "sentiment": sent_score, "fundamentals": fund_score},
                    info,
                ),
            })
        except Exception as e:
            logger.debug(f"Custom scan: failed for {ticker}: {e}")
            continue

    # Sort by score and assign ranks
    scored.sort(key=lambda s: s["score"], reverse=True)
    for rank, stock in enumerate(scored, 1):
        stock["rank"] = rank

    logger.info(f"Custom scan complete: {len(scored)}/{len(tickers)} tickers scored")

    yield _progress(100, "Scan complete!")
    yield {"event": "result", "data": json.dumps({"stocks": scored})}


def _progress(percent: int, message: str) -> dict:
    return {
        "event": "progress",
        "data": json.dumps({"percent": percent, "message": message}),
    }
