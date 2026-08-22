"""
==============================================================
MERTON CREDIT SCANNER: EVENTS ROUTER
backend/api/events.py

Registered in main.py as:
    app.include_router(events_router, prefix="/api/v1/events", tags=["Event Scanner"])

Endpoints (all relative to /api/v1/events):
    GET  /scan/latest
    GET  /scan/history?days=30
    POST /scan/manual
    GET  /scan/stream       ← SSE
==============================================================
"""
import asyncio
import json
import logging
from dataclasses import asdict
from datetime import datetime, date, timedelta

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from signals.event_scanner import (
    MertonResult,
    ScanSession,
    scan_ticker,
    run_daily_scan,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# ── In-memory session cache ────────────────────────────────────────
# Shared with scheduler.py via direct import of this module.
# Swap for Redis in production: serialize ScanSession → JSON.
_scan_cache: dict[str, ScanSession]  = {}
_latest_session_id: str | None       = None


def update_cache(session: ScanSession) -> None:
    """Called by both the router (manual scans) and the scheduler (daily scan)."""
    global _latest_session_id
    _scan_cache[session.session_id] = session
    _latest_session_id = session.session_id


# ── Request models ─────────────────────────────────────────────────
class ManualScanRequest(BaseModel):
    tickers: list[str]
    risk_free_rate: float = 0.045


# ── Endpoints ──────────────────────────────────────────────────────
@router.get("/scan/latest")
async def get_latest_scan():
    """Returns most recent daily scan session."""
    if not _latest_session_id or _latest_session_id not in _scan_cache:
        raise HTTPException(
            status_code=404,
            detail="No scan data available. Trigger a manual scan or wait for market close."
        )
    session = _scan_cache[_latest_session_id]
    return {
        "session_id":     session.session_id,
        "scan_date":      session.scan_date,
        "triggered_at":   session.triggered_at,
        "total_screened": session.total_screened,
        "signals_fired":  session.signals_fired,
        "results":        [asdict(r) for r in session.results],
    }


@router.get("/scan/history")
async def get_scan_history(days: int = Query(default=30, le=90)):
    """Returns all scan sessions within last N days, sorted newest first."""
    cutoff   = date.today() - timedelta(days=days)
    sessions = [
        {
            "session_id":     s.session_id,
            "scan_date":      s.scan_date,
            "signals_fired":  s.signals_fired,
            "total_screened": s.total_screened,
        }
        for s in _scan_cache.values()
        if date.fromisoformat(s.scan_date) >= cutoff
    ]
    sessions.sort(key=lambda x: x["scan_date"], reverse=True)
    return {"sessions": sessions}


@router.post("/scan/manual")
async def trigger_manual_scan(
    req: ManualScanRequest,
    background_tasks: BackgroundTasks,
):
    """Manually trigger Merton scan for specific tickers (max 20)."""
    if len(req.tickers) > 20:
        raise HTTPException(status_code=400, detail="Max 20 tickers per manual scan.")

    async def _run():
        results: list[MertonResult] = await asyncio.gather(
            *[scan_ticker(t, req.risk_free_rate, "MANUAL") for t in req.tickers]
        )
        valid = [r for r in results if r.error is None]
        valid.sort(key=lambda x: x.alpha_gap_bps, reverse=True)
        signals_fired = sum(1 for r in valid if r.signal in ("SHORT_CREDIT", "CRITICAL_SHORT"))

        session = ScanSession(
            session_id    =f"manual_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            scan_date     =date.today().isoformat(),
            triggered_at  =datetime.utcnow().isoformat(),
            total_screened=len(req.tickers),
            signals_fired =signals_fired,
            results       =valid,
        )
        update_cache(session)
        logger.info(f"Manual scan complete: {signals_fired} signals for {req.tickers}")

    background_tasks.add_task(_run)
    return {"status": "scan_initiated", "tickers": req.tickers}


@router.get("/scan/stream")
async def stream_scan_results():
    """
    SSE endpoint. Pushes scan updates every 5 seconds when new sessions land.
    Frontend connects via: new EventSource('/api/v1/events/scan/stream')
    """
    async def event_generator():
        last_id = _latest_session_id

        # Immediately push current state on connect (avoids blank terminal)
        if last_id and last_id in _scan_cache:
            session = _scan_cache[last_id]
            yield f"data: {_session_payload(session)}\n\n"

        while True:
            await asyncio.sleep(5)
            if _latest_session_id and _latest_session_id != last_id:
                last_id = _latest_session_id
                session = _scan_cache[last_id]
                yield f"data: {_session_payload(session)}\n\n"
            else:
                # Keepalive ping so proxies don't drop the connection
                yield ": keepalive\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":       "keep-alive",
        },
    )


def _session_payload(session: ScanSession) -> str:
    return json.dumps({
        "session_id":     session.session_id,
        "scan_date":      session.scan_date,
        "triggered_at":   session.triggered_at,
        "total_screened": session.total_screened,
        "signals_fired":  session.signals_fired,
        "results":        [asdict(r) for r in session.results[:20]],
    })