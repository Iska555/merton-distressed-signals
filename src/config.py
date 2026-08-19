"""
Global configuration for the Merton credit study.

Everything here is a research parameter. Changing a value here changes published
numbers, so each carries its justification and, where relevant, its source.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
FRONTEND_DATA = ROOT / "frontend" / "public" / "data"

for _d in (DATA_RAW, DATA_PROCESSED):
    _d.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT / "backend" / ".env")

# ---------------------------------------------------------------- credentials
FRED_API_KEY = os.getenv("FRED_API_KEY")
TIINGO_API_KEY = os.getenv("TIINGO_API_KEY")
FMP_API_KEY = os.getenv("FMP_API_KEY")

# SEC requires a descriptive User-Agent with contact details, and throttles at
# 10 requests/second. https://www.sec.gov/os/accessing-edgar-data
SEC_USER_AGENT = os.getenv(
    "SEC_USER_AGENT",
    "Merton structural credit study ismayil.huseynov.usa@gmail.com",
)
SEC_RATE_LIMIT_PER_SEC = 8  # deliberately under the published 10/s ceiling

# ---------------------------------------------------------------- determinism
# Every script that samples, bootstraps or shuffles seeds from this. Committed
# CSVs must reproduce byte-for-byte, so no code may call an unseeded RNG.
RANDOM_SEED = 20260819

# ---------------------------------------------------------------- study window
# Lower bound is forced by data, not by preference:
#   - SEC XBRL company facts begin ~2009
#   - 36 months of pre-event history are required for the event study
# See docs/PHASE0_DATA_INVENTORY.md section 6.5.
STUDY_START = "2012-01-01"
STUDY_END = "2024-12-31"

EVENT_WINDOW_PRE_MONTHS = 36   # t-36 .. t=0 event-time panel
EVENT_WINDOW_POST_MONTHS = 0   # equity ceases to be meaningful after filing

# ---------------------------------------------------------------- Merton inputs
DEFAULT_HORIZON_T = 1.0        # years
DEFAULT_RECOVERY_RATE = 0.40   # Moody's long-run senior unsecured average

# Volatility estimation. 252 trading days ~ 1 year, matching the horizon.
# The alternatives are published as a sensitivity exhibit, not buried.
VOL_WINDOW_DAYS_DEFAULT = 252
VOL_WINDOWS_SENSITIVITY = (30, 60, 90, 252)

MIN_VOLATILITY = 0.05
MAX_VOLATILITY = 3.00

# Debt-to-default-barrier convention. "kmv" is short-term debt + half of
# long-term, the Moody's KMV convention; "total" is the full face value.
# Both are computed for every firm-month; this selects the headline series.
DEBT_CONVENTION_DEFAULT = "kmv"
DEBT_CONVENTIONS = ("kmv", "total")

# ---------------------------------------------------------------- sample filters
MIN_MARKET_CAP = 50_000_000    # $50M at t-24m; below this, prices are noise
MIN_DEBT = 1_000_000

# ---------------------------------------------------------------- matching
CONTROLS_PER_TREATMENT = 5
MATCH_ANCHOR_MONTHS_BEFORE = 24  # match on covariates as of t-24m
SIZE_DECILES = 10
LEVERAGE_DECILES = 10

# ---------------------------------------------------------------- base rate
# Applied in the base-rate exhibit to convert AUC/TPR/FPR into precision.
# Source: S&P Global Annual Global Corporate Default Study, long-run average
# all-rated corporate default rate. Range shown as a slider on the site.
ANNUAL_DEFAULT_BASE_RATE = 0.015
BASE_RATE_SLIDER_RANGE = (0.002, 0.05)

# ---------------------------------------------------------------- FRED series
# NOTE: ICE BofA OAS series are served on a ROLLING 3-YEAR WINDOW (verified
# 2026-08-19: observation_start 2023-08-21). They CANNOT be used as a
# contemporaneous benchmark in a historical event study. They appear only in
# the present-day illustrative module on /screen.
FRED_RISK_FREE = "DGS1"
FRED_SPREAD_SERIES = {
    "AAA": "BAMLC0A1CAAA",
    "BBB": "BAMLC0A4CBBB",
    "BB": "BAMLH0A1HYBB",
    "B": "BAMLH0A2HYB",
    "CCC": "BAMLH0A3HYC",
    "IG_MASTER": "BAMLC0A0CM",
    "HY_MASTER": "BAMLH0A0HYM2",
}
FRED_OAS_HISTORY_STARTS = "2023-08-21"  # empirical, re-verify on each rerun

VERSION = "2.0.0-research"
