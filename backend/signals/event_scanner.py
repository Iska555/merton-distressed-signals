"""
MERTON CREDIT SCANNER — EVENT SCANNER SERVICE
backend/signals/event_scanner.py

Pure service layer. No FastAPI. No scheduler.
Imported by: backend/api/events.py, backend/scheduler.py
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional

import numpy as np
import yfinance as yf
from scipy.optimize import fsolve
from scipy.stats import norm

logger = logging.getLogger(__name__)

# ── Signal thresholds ──────────────────────────────────────────────
SHORT_SIGNAL_THRESHOLD_BPS    = 200
CRITICAL_SIGNAL_THRESHOLD_BPS = 500
PRICE_MOVE_THRESHOLD          = 0.05
VOL_SPIKE_THRESHOLD           = 0.50
MIN_MARKET_CAP_B              = 0.5
DEFAULT_DEBT_MATURITY         = 1.0

# For banks: if reported debt < this multiple of equity, use structural override
BANK_MIN_DEBT_TO_EQUITY_RATIO = 2.0
# Standard structural leverage proxy for banks (Basel III avg ~9–12x)
BANK_STRUCTURAL_LEVERAGE      = 9.0

BANK_SECTORS = {"Financial Services", "Banking", "Financial"}


# ── Core data structures ───────────────────────────────────────────
@dataclass
class NewsItem:
    title:      str
    publisher:  str
    timestamp:  str   # ISO 8601 UTC
    url:        str


@dataclass
class MertonResult:
    ticker:                  str
    company_name:            str
    scan_timestamp:          str
    share_price:             float
    equity_value_b:          float
    face_value_debt_b:       float
    risk_free_rate:          float
    equity_vol:              float
    implied_asset_value_b:   float
    implied_asset_vol:       float
    distance_to_default:     float
    default_probability_pct: float
    theoretical_spread_bps:  float
    market_spread_bps:       float
    alpha_gap_bps:           float
    signal:                  str   # NEUTRAL | LONG_CREDIT | SHORT_CREDIT | CRITICAL_SHORT
    trigger_type:            str   # PRICE_MOVE | VOL_SPIKE | MANUAL
    price_change_pct:        float
    vol_change_pct:          float
    solver_converged:        bool
    debt_override_applied:   bool = False   # True when bank structural proxy was used
    recent_news:             list[NewsItem] = field(default_factory=list)
    error:                   Optional[str]  = None


@dataclass
class ScanSession:
    session_id:     str
    scan_date:      str
    triggered_at:   str
    total_screened: int
    signals_fired:  int
    results:        list[MertonResult] = field(default_factory=list)


# ── Merton solver ──────────────────────────────────────────────────
def _merton_equations(
    params: list[float], V_E: float, sigma_E: float,
    F: float, r: float, T: float,
) -> list[float]:
    V_A, sigma_A = params
    if V_A <= 0 or sigma_A <= 0:
        return [1e10, 1e10]
    d1 = (np.log(V_A / F) + (r + 0.5 * sigma_A ** 2) * T) / (sigma_A * np.sqrt(T))
    d2 = d1 - sigma_A * np.sqrt(T)
    eq1 = V_A * norm.cdf(d1) - F * np.exp(-r * T) * norm.cdf(d2) - V_E
    eq2 = V_A * norm.cdf(d1) * sigma_A - V_E * sigma_E
    return [eq1, eq2]


def solve_merton(V_E: float, sigma_E: float, F: float, r: float, T: float = 1.0) -> dict:
    V_A_init   = V_E + F * np.exp(-r * T)
    sig_A_init = sigma_E * V_E / V_A_init

    try:
        solution, _, ier, _ = fsolve(
            _merton_equations,
            x0=[V_A_init, sig_A_init],
            args=(V_E, sigma_E, F, r, T),
            full_output=True,
        )
        converged  = ier == 1
        V_A, sig_A = solution

        if V_A <= 0 or sig_A <= 0:
            raise ValueError("Non-positive solution")

        d1 = (np.log(V_A / F) + (r + 0.5 * sig_A ** 2) * T) / (sig_A * np.sqrt(T))
        d2 = d1 - sig_A * np.sqrt(T)

        N_d2            = norm.cdf(d2)
        N_neg_d2        = norm.cdf(-d2)
        theo_spread_bps = (-np.log(N_d2) / T * 10_000) if N_d2 > 0 else 99_999.0

        return {
            "V_A":                     round(V_A, 4),
            "sigma_A":                 round(sig_A, 4),
            "distance_to_default":     round(d2, 4),
            "default_probability_pct": round(N_neg_d2 * 100, 4),
            "theoretical_spread_bps":  round(theo_spread_bps, 1),
            "converged":               converged,
        }

    except Exception as exc:
        logger.warning(f"Merton solver failed: {exc}")
        return {
            "V_A": V_A_init, "sigma_A": sig_A_init,
            "distance_to_default": 0.0,
            "default_probability_pct": 50.0,
            "theoretical_spread_bps": 9_999.0,
            "converged": False,
        }


# ── DIRECTIVE 1: Bank structural debt fix ─────────────────────────
def _get_face_value_debt(info: dict, equity_value_b: float) -> tuple[float, bool]:
    sector = info.get("sector", "")

    if sector in BANK_SECTORS:
        st = (info.get("shortTermDebt") or 0)
        lt = (info.get("longTermDebt")  or 0)
        reported_debt_b = (st + lt) / 1e9

        if reported_debt_b < (BANK_MIN_DEBT_TO_EQUITY_RATIO * equity_value_b):
            override_debt = equity_value_b * BANK_STRUCTURAL_LEVERAGE
            logger.debug(
                f"Bank debt override: reported=${reported_debt_b:.1f}B "
                f"→ structural proxy=${override_debt:.1f}B "
                f"({BANK_STRUCTURAL_LEVERAGE}x equity)"
            )
            return max(override_debt, 1.0), True

        return max(reported_debt_b, 1.0), False

    total_debt = (info.get("totalDebt") or 0) / 1e9
    return max(total_debt, 1.0), False


# ── Market spread proxy ────────────────────────────────────────────
def _get_market_spread_bps(ticker: str, info: dict) -> float:
    mkt_cap = (info.get("marketCap") or 0) / 1e9
    sector = info.get("sector", "")
    
    if sector in BANK_SECTORS:
        if mkt_cap > 100: return 80.0   # Mega-cap (JPM, BAC) ~ AA Rating
        if mkt_cap > 10:  return 120.0  # Mid-cap ~ A Rating
        return 200.0                    # Regional ~ BBB Rating

    total_debt = (info.get("totalDebt") or 0) / 1e9
    de = total_debt / max(mkt_cap, 0.1)

    if de < 0.5:  return 80.0
    if de < 1.5:  return 150.0
    if de < 3.0:  return 280.0
    if de < 6.0:  return 420.0
    return 650.0


# ── Realized vol ───────────────────────────────────────────────────
def _compute_realized_vol(ticker: str, window: int = 30) -> tuple[float, float]:
    try:
        hist = yf.download(ticker, period="90d", interval="1d",
                           progress=False, auto_adjust=True)
        if len(hist) < window + 5:
            return 0.30, 0.30
        log_ret     = np.log(hist["Close"] / hist["Close"].shift(1)).dropna()
        current_vol = float(log_ret.iloc[-window:].std()              * np.sqrt(252))
        prior_vol   = float(log_ret.iloc[-(window * 2):-window].std() * np.sqrt(252))
        return current_vol, prior_vol
    except Exception as exc:
        logger.warning(f"Vol calculation failed for {ticker}: {exc}")
        return 0.30, 0.30


# ── DIRECTIVE 2: Catalyst news fetcher ────────────────────────────
def _fetch_recent_news(ticker_obj: yf.Ticker, ticker: str, n: int = 3) -> list[NewsItem]:
    try:
        raw_news = ticker_obj.news
        if not isinstance(raw_news, list):
            raw_news = []
            
        items: list[NewsItem] = []
        for article in raw_news[:n]:
            title = (article.get("title") or "").strip()
            publisher = (article.get("publisher") or "Market Feed").strip()
            url = article.get("link") or article.get("url") or "#"
            unix_ts = article.get("providerPublishTime")
            
            if not unix_ts:
                unix_ts = int(datetime.utcnow().timestamp())
                
            iso_ts = datetime.utcfromtimestamp(unix_ts).isoformat() + "Z"

            if title:
                items.append(NewsItem(
                    title=title,
                    publisher=publisher,
                    timestamp=iso_ts,
                    url=url,
                ))

        if not items:
            items.append(NewsItem(
                title=f"Monitoring structural volatility and credit lags for {ticker}.",
                publisher="Merton Internal",
                timestamp=datetime.utcnow().isoformat() + "Z",
                url="#"
            ))

        return items

    except Exception as exc:
        logger.debug(f"News fetch failed for {ticker}: {exc}")
        return [NewsItem(
            title=f"Data link interrupted. Calculating baseline default risks for {ticker}.",
            publisher="System Log",
            timestamp=datetime.utcnow().isoformat() + "Z",
            url="#"
        )]


# ── THE FIX: Synchronous Core isolated from Event Loop ───────────────
def _scan_ticker_sync(
    ticker:         str,
    risk_free_rate: float = 0.045,
    trigger_type:   str   = "MANUAL",
) -> MertonResult:
    """Core logic. Runs synchronously in a background thread."""
    try:
        t    = yf.Ticker(ticker)
        info = t.info

        company_name       = info.get("longName") or info.get("shortName") or ticker
        current_price      = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
        prev_price         = info.get("regularMarketPreviousClose") or current_price
        shares_outstanding = (info.get("sharesOutstanding") or 0) / 1e9

        if shares_outstanding < 0.001:
            raise ValueError(f"Insufficient share data for {ticker}")

        equity_value_b = current_price * shares_outstanding
        if equity_value_b < MIN_MARKET_CAP_B:
            raise ValueError(f"Market cap ${equity_value_b:.2f}B below minimum")

        face_value_debt_b, debt_override_applied = _get_face_value_debt(info, equity_value_b)

        current_vol, prior_vol = _compute_realized_vol(ticker)
        price_change_pct       = (current_price - prev_price) / prev_price if prev_price else 0.0
        vol_change_pct         = (current_vol - prior_vol) / prior_vol if prior_vol else 0.0

        merton = solve_merton(
            V_E=equity_value_b, sigma_E=current_vol,
            F=face_value_debt_b, r=risk_free_rate, T=DEFAULT_DEBT_MATURITY,
        )

        market_spread_bps      = _get_market_spread_bps(ticker, info)
        theoretical_spread_bps = merton["theoretical_spread_bps"]
        alpha_gap_bps          = theoretical_spread_bps - market_spread_bps

        if   alpha_gap_bps > CRITICAL_SIGNAL_THRESHOLD_BPS: signal = "CRITICAL_SHORT"
        elif alpha_gap_bps > SHORT_SIGNAL_THRESHOLD_BPS:    signal = "SHORT_CREDIT"
        elif alpha_gap_bps < -150:                          signal = "LONG_CREDIT"
        else:                                               signal = "NEUTRAL"

        recent_news = _fetch_recent_news(t, ticker, n=3)

        return MertonResult(
            ticker=ticker,
            company_name=company_name,
            scan_timestamp=datetime.utcnow().isoformat(),
            share_price=round(current_price, 2),
            equity_value_b=round(equity_value_b, 3),
            face_value_debt_b=round(face_value_debt_b, 3),
            risk_free_rate=risk_free_rate,
            equity_vol=round(current_vol, 4),
            implied_asset_value_b=round(merton["V_A"], 3),
            implied_asset_vol=round(merton["sigma_A"], 4),
            distance_to_default=round(merton["distance_to_default"], 3),
            default_probability_pct=round(merton["default_probability_pct"], 3),
            theoretical_spread_bps=round(theoretical_spread_bps, 1),
            market_spread_bps=round(market_spread_bps, 1),
            alpha_gap_bps=round(alpha_gap_bps, 1),
            signal=signal,
            trigger_type=trigger_type,
            price_change_pct=round(price_change_pct, 4),
            vol_change_pct=round(vol_change_pct, 4),
            solver_converged=merton["converged"],
            debt_override_applied=debt_override_applied,
            recent_news=recent_news,
        )

    except Exception as exc:
        logger.error(f"scan_ticker({ticker}) failed: {exc}")
        return MertonResult(
            ticker=ticker, company_name=ticker,
            scan_timestamp=datetime.utcnow().isoformat(),
            share_price=0.0, equity_value_b=0.0, face_value_debt_b=0.0,
            risk_free_rate=risk_free_rate, equity_vol=0.0,
            implied_asset_value_b=0.0, implied_asset_vol=0.0,
            distance_to_default=0.0, default_probability_pct=0.0,
            theoretical_spread_bps=0.0, market_spread_bps=0.0,
            alpha_gap_bps=0.0, signal="NEUTRAL", trigger_type=trigger_type,
            price_change_pct=0.0, vol_change_pct=0.0,
            solver_converged=False, debt_override_applied=False,
            recent_news=[], error=str(exc),
        )


# ── THE FIX: Asynchronous Router Wrapper ──────────────────────────────
async def scan_ticker(
    ticker: str,
    risk_free_rate: float = 0.045,
    trigger_type: str = "MANUAL",
) -> MertonResult:
    """Offloads the blocking yfinance scrape to a background thread pool."""
    return await asyncio.to_thread(_scan_ticker_sync, ticker, risk_free_rate, trigger_type)


# ── Daily mover screener ───────────────────────────────────────────
async def get_daily_movers(
    universe:        list[str] | None = None,
    price_threshold: float = PRICE_MOVE_THRESHOLD,
    vol_threshold:   float = VOL_SPIKE_THRESHOLD,
) -> dict[str, str]:
    if universe is None:
        universe = [
            "JPM", "BAC", "C", "WFC", "GS", "MS", "BX", "KKR", "AXP",
            "USB", "PNC", "TFC", "FITB", "RF", "ZION", "NYCB",
            "BA", "GE", "F", "GM", "X", "CLF", "NUE",
            "HUM", "CNC", "DVA", "MPW",
            "AMC", "DISH", "LUMN", "CHK", "CPE", "SM", "RRC",
        ]

    movers: dict[str, str] = {}
    try:
        data = yf.download(
            tickers=universe, period="5d", interval="1d",
            progress=False, auto_adjust=True, group_by="ticker",
        )
    except Exception as exc:
        logger.error(f"Batch download failed: {exc}")
        return {}

    for ticker in universe:
        try:
            if ticker not in data.columns.get_level_values(0):
                continue
            close = data[ticker]["Close"].dropna()
            if len(close) < 2:
                continue
            today_px, yest_px = float(close.iloc[-1]), float(close.iloc[-2])
            if abs((today_px - yest_px) / yest_px) >= price_threshold:
                movers[ticker] = "PRICE_MOVE"
                continue
            log_ret = np.log(close / close.shift(1)).dropna()
            if len(log_ret) >= 4:
                recent_vol = log_ret.iloc[-2:].std() * np.sqrt(252)
                prior_v    = log_ret.iloc[:-2].std()  * np.sqrt(252)
                if prior_v > 0 and (recent_vol / prior_v - 1) >= vol_threshold:
                    movers[ticker] = "VOL_SPIKE"
        except Exception as exc:
            logger.debug(f"Screener skipped {ticker}: {exc}")

    return movers


# ── Daily scan orchestrator ────────────────────────────────────────
async def run_daily_scan(
    risk_free_rate: float = 0.045,
    universe: list[str] | None = None,
) -> ScanSession:
    session_id = f"scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"Starting scan session {session_id}")

    movers = await get_daily_movers(universe=universe)
    logger.info(f"Screener flagged {len(movers)} tickers")

    semaphore = asyncio.Semaphore(5)

    async def _guarded(ticker: str, trigger: str) -> MertonResult:
        async with semaphore:
            return await scan_ticker(ticker, risk_free_rate, trigger)

    results: list[MertonResult] = await asyncio.gather(
        *[_guarded(t, tr) for t, tr in movers.items()]
    )

    valid         = sorted([r for r in results if r.error is None],
                            key=lambda x: x.alpha_gap_bps, reverse=True)
    signals_fired = sum(1 for r in valid if r.signal in ("SHORT_CREDIT", "CRITICAL_SHORT"))

    logger.info(f"Scan complete — {len(valid)} valid, {signals_fired} SHORT signals")
    return ScanSession(
        session_id=session_id,
        scan_date=date.today().isoformat(),
        triggered_at=datetime.utcnow().isoformat(),
        total_screened=len(movers),
        signals_fired=signals_fired,
        results=valid,
    )