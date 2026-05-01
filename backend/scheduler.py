"""
==============================================================
MERTON CREDIT SCANNER — SCHEDULER
backend/scheduler.py

Registered in main.py:
    @app.on_event("startup")
    async def startup_event():
        scheduler.start()
        logger.info("APScheduler running. Daily scan fires at 16:30 ET.")
==============================================================
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from signals.event_scanner import run_daily_scan
from api.events import update_cache           # shared cache writer

logger    = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="America/New_York")


@scheduler.scheduled_job(
    CronTrigger(
        day_of_week="mon-fri",
        hour=16,
        minute=30,
        timezone="America/New_York",
    )
)
async def daily_market_close_scan():
    """Fires at 16:30 ET Monday–Friday after market close."""
    logger.info("Daily close scan triggered by APScheduler.")
    try:
        session = await run_daily_scan()
        update_cache(session)
        logger.info(
            f"Daily scan stored: {session.session_id} — "
            f"{session.signals_fired} signals / {session.total_screened} screened"
        )
    except Exception as e:
        logger.error(f"Daily scan failed: {e}", exc_info=True)