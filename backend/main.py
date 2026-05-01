"""
FastAPI application entry point — Merton Credit Scanner
"""
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from api.events import router as events_router
from scheduler import scheduler

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Merton Credit Signal Generator API",
    description="Real-time credit arbitrage signals using the Merton structural model",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://merton-signals.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Existing analysis routes — untouched
app.include_router(router, prefix="/api/v1", tags=["analysis"])

# Event scanner routes → /api/v1/events/scan/*
app.include_router(events_router, prefix="/api/v1/events", tags=["Event Scanner"])


@app.get("/")
async def root():
    return {"message": "Merton Credit Signal Generator API", "docs": "/docs", "version": "1.0.0"}


@app.on_event("startup")
async def startup_event():
    scheduler.start()
    logger.info("APScheduler started. Daily scan fires at 16:30 ET Mon–Fri.")


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown(wait=False)
    logger.info("APScheduler shut down.")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)