"""
FastAPI app with endpoints:
  POST /api/scan   — SSE stream with progress + top 10 results
  GET  /api/health — health check
  GET  /api/logs   — request tracker summary stats
"""
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse

from logger import get_logger
from request_tracker import tracker
from scanner import run_scan

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
