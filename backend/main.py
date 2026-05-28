"""
FastAPI app with endpoints:
  POST /api/scan   — SSE stream with progress + top 10 results
  GET  /api/health — health check
  GET  /api/logs   — request tracker summary stats
"""
from fastapi import FastAPI, Request
from pydantic import BaseModel, field_validator
from sse_starlette.sse import EventSourceResponse

from logger import get_logger
from request_tracker import tracker
from scanner import run_scan, run_custom_scan

logger = get_logger(__name__)

app = FastAPI(title="Stock Speculation Scanner", version="1.0.0")


@app.post("/api/scan")
async def scan(request: Request):
    """
    Initiates a full market scan. Returns an SSE stream.

    Event types:
      - "progress": {"percent": int, "message": str}
      - "result":   {"stocks": list[dict]}
      - "error":    {"message": str}
    """
    logger.info("Scan requested")

    async def event_generator():
        try:
            async for event in run_scan():
                if await request.is_disconnected():
                    logger.info("Client disconnected, stopping scan")
                    break
                yield event
        except Exception as e:
            logger.exception("Scan failed")
            yield {"event": "error", "data": f'{{"message": "{e}"}}'}

    return EventSourceResponse(event_generator())


class CustomScanRequest(BaseModel):
    tickers: list[str]

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v):
        v = [t.strip().upper() for t in v if t.strip()]
        if len(v) > 10:
            raise ValueError("Maximum 10 tickers allowed")
        if len(v) == 0:
            raise ValueError("At least 1 ticker required")
        return v


@app.post("/api/scan/custom")
async def custom_scan(request: Request, body: CustomScanRequest):
    """Scan specific tickers. Returns an SSE stream."""
    logger.info(f"Custom scan requested for {body.tickers}")

    async def event_generator():
        try:
            async for event in run_custom_scan(body.tickers):
                if await request.is_disconnected():
                    logger.info("Client disconnected, stopping custom scan")
                    break
                yield event
        except Exception as e:
            logger.exception("Custom scan failed")
            yield {"event": "error", "data": f'{{"message": "{e}"}}'}

    return EventSourceResponse(event_generator())


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/logs")
async def logs():
    """Returns request tracker summary stats and recent failures."""
    return {
        "status": "ok",
        "request_summary": tracker.get_summary(),
        "recent_failures": tracker.get_recent_failures(50),
    }
