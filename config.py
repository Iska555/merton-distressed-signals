"""
Global configuration for Merton Signal Generator
Current as of: January 2026
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ========== API KEYS ==========
FRED_API_KEY = os.getenv('FRED_API_KEY')

# ========== MARKET PARAMETERS (Jan 2026) ==========
# Source: https://fred.stlouisfed.org/series/DGS1
# Last updated: 2026-01-28
RISK_FREE_RATE = 0.0352  # 3.52% (1Y Treasury)

DEFAULT_TIME_HORIZON = 1.0      # 1-year horizon
DEFAULT_RECOVERY_RATE = 0.40    # 40% (Moody's avg)

# ========== VOLATILITY ESTIMATION ==========
HISTORICAL_VOL_WINDOW = 60  # 60 days (stable for credit)
MIN_VOLATILITY = 0.05       # 5% floor
MAX_VOLATILITY = 2.5        # 250% cap

# ========== DATA VALIDATION ==========
MIN_MARKET_CAP = 100_000_000  # $100M
MIN_DEBT = 1_000_000          # $1M
MAX_LEVERAGE = 0.90           # 90% D/V hard cap

# ========== FRED CREDIT INDICES ==========
FRED_SPREAD_SERIES = {
    'AAA': 'BAMLC0A1CAAA',
    'AA':  'BAMLC0A2CAA',
    'A':   'BAMLC0A3CA',
    'BBB': 'BAMLC0A4CBBB',
    'BB':  'BAMLH0A1HYBB',
    'B':   'BAMLH0A2HYB',
    'CCC': 'BAMLH0A3HYC',
    'IG_MASTER': 'BAMLC0A0CM',
    'HY_MASTER': 'BAMLH0A0HYM2'
}

# ========== SIGNAL THRESHOLDS (bps) ==========
SIGNAL_THRESHOLD_STRONG = 150   # ±150 bps = Strong signal
SIGNAL_THRESHOLD_MODERATE = 75  # ±75 bps = Moderate signal

# ========== LOGGING ==========
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ========== METADATA ==========
VERSION = "1.0.0"
LAST_UPDATED = "2026-01-28"