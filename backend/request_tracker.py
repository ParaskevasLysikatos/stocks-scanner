import json
import os
import time
import functools
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from threading import Lock
from typing import Any

import logging
import requests as req_lib

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

REQUEST_LOG_FILE = os.path.join(LOG_DIR, "external_requests.log")

# Dedicated JSON-lines logger for external requests
_req_logger = logging.getLogger("external_requests")
_req_logger.setLevel(logging.DEBUG)
_req_logger.propagate = False

_file_handler = RotatingFileHandler(
    REQUEST_LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
_file_handler.setFormatter(logging.Formatter("%(message)s"))
_req_logger.addHandler(_file_handler)


class RequestTracker:
    """Tracks all external HTTP requests with per-source stats."""

    def __init__(self):
        self._lock = Lock()
        self._stats: dict[str, dict[str, Any]] = {}

    def _ensure_source(self, source: str):
        if source not in self._stats:
            self._stats[source] = {
                "total": 0,
                "success": 0,
                "failed": 0,
                "total_latency_ms": 0.0,
            }

    def record(
        self,
        source: str,
        url: str,
        method: str,
        status_code: int | None,
        latency_ms: float,
        success: bool,
        error_message: str = "",
        ticker: str = "",
    ):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "url": url[:200],
            "method": method,
            "status_code": status_code,
            "latency_ms": round(latency_ms, 1),
            "success": success,
            "error_message": error_message,
            "ticker": ticker,
        }
        _req_logger.info(json.dumps(entry))

        with self._lock:
            self._ensure_source(source)
            s = self._stats[source]
            s["total"] += 1
            s["total_latency_ms"] += latency_ms
            if success:
                s["success"] += 1
            else:
                s["failed"] += 1

    def get(self, url: str, source: str, ticker: str = "", **kwargs) -> req_lib.Response:
        """Wrapper around requests.get() with automatic tracking."""
        start = time.perf_counter()
        try:
            resp = req_lib.get(url, **kwargs)
            latency = (time.perf_counter() - start) * 1000
            self.record(
                source=source,
                url=url,
                method="GET",
                status_code=resp.status_code,
                latency_ms=latency,
                success=resp.status_code < 400,
                ticker=ticker,
            )
            return resp
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            self.record(
                source=source,
                url=url,
                method="GET",
                status_code=None,
                latency_ms=latency,
                success=False,
                error_message=str(e),
                ticker=ticker,
            )
            raise

    def get_summary(self) -> dict:
        with self._lock:
            summary = {}
            for source, s in self._stats.items():
                avg_latency = (
                    s["total_latency_ms"] / s["total"] if s["total"] > 0 else 0
                )
                summary[source] = {
                    "total": s["total"],
                    "success": s["success"],
                    "failed": s["failed"],
                    "avg_latency_ms": round(avg_latency, 1),
                }
            return summary

    def get_recent_failures(self, n: int = 50) -> list[dict]:
        """Read the last N failed requests from the JSON-lines log file."""
        failures = []
        try:
            if not os.path.exists(REQUEST_LOG_FILE):
                return []
            with open(REQUEST_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            # Read from end for recency
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if not entry.get("success", True):
                        failures.append(entry)
                        if len(failures) >= n:
                            break
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass
        return failures

    def reset(self):
        with self._lock:
            self._stats.clear()


# Global singleton
tracker = RequestTracker()


def track_request(source: str):
    """Decorator for tracking calls to functions that use their own HTTP
    internally (e.g. yfinance). Logs duration and success/failure."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ticker = kwargs.get("ticker", args[0] if args else "")
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                latency = (time.perf_counter() - start) * 1000
                tracker.record(
                    source=source,
                    url=f"{source}://{func.__name__}",
                    method="INTERNAL",
                    status_code=200,
                    latency_ms=latency,
                    success=True,
                    ticker=str(ticker),
                )
                return result
            except Exception as e:
                latency = (time.perf_counter() - start) * 1000
                tracker.record(
                    source=source,
                    url=f"{source}://{func.__name__}",
                    method="INTERNAL",
                    status_code=None,
                    latency_ms=latency,
                    success=False,
                    error_message=str(e),
                    ticker=str(ticker),
                )
                raise

        return wrapper

    return decorator
