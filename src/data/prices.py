"""
Equity price retrieval, with integrity guards against ticker recycling.

Phase 0 established that price data is the binding constraint of this study,
and that the failure mode is not absence but *silent substitution*: Yahoo
serves Overstock/Beyond Inc. prices as continuous "Bed Bath & Beyond" history
straight through BBBY's April 2023 bankruptcy, showing $19-36 and rising where
the real stock traded near $0.07. A pipeline that trusted it would compute a
healthy firm through a bankruptcy and record it as a model failure.

So every series fetched here is validated before use, and a series that fails
validation is dropped with a recorded reason rather than repaired.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..config import DATA_RAW, TIINGO_API_KEY

_CACHE = DATA_RAW / "prices"
_CACHE.mkdir(parents=True, exist_ok=True)


@dataclass
class PriceSeries:
    """A validated daily close series, or an explanation of why there isn't one."""
    ticker: str
    provider: str
    closes: pd.Series | None = None
    ok: bool = False
    reason: str = ""
    warnings_raised: tuple[str, ...] = field(default_factory=tuple)

    @property
    def n(self) -> int:
        return 0 if self.closes is None else int(self.closes.size)


# --------------------------------------------------------------------------
# Providers
# --------------------------------------------------------------------------

def _cache_path(provider: str, ticker: str) -> "object":
    safe = ticker.replace("/", "_").replace("\\", "_").upper()
    return _CACHE / provider / f"{safe}.json"


def fetch_yahoo(ticker: str, start: str, end: str, *, refresh: bool = False) -> PriceSeries:
    """
    Daily adjusted closes from Yahoo.

    Suitable for currently-listed firms (the control cohort). Unreliable for
    anything delisted: Phase 0 found 9/45 defaulted tickers returned data at
    all, and several of those were the wrong company.
    """
    path = _cache_path("yahoo", ticker)
    payload: dict | None = None
    if path.exists() and not refresh:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            payload = None

    if payload is None:
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?period1=0&period2=2000000000&interval=1d&events=div,split"
        )
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        try:
            with urllib.request.urlopen(req, timeout=40) as resp:
                payload = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            return PriceSeries(ticker, "yahoo", None, False, f"http {exc.code}")
        except Exception as exc:  # noqa: BLE001
            return PriceSeries(ticker, "yahoo", None, False, f"{type(exc).__name__}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    result = (payload or {}).get("chart", {}).get("result")
    if not result:
        return PriceSeries(ticker, "yahoo", None, False, "no result (likely delisted)")

    node = result[0]
    stamps = node.get("timestamp") or []
    if not stamps:
        return PriceSeries(ticker, "yahoo", None, False, "empty timestamp array")

    quote = (node.get("indicators", {}).get("quote") or [{}])[0]
    adj = (node.get("indicators", {}).get("adjclose") or [{}])
    closes = adj[0].get("adjclose") if adj and adj[0].get("adjclose") else quote.get("close")
    if not closes:
        return PriceSeries(ticker, "yahoo", None, False, "no close array")

    series = pd.Series(
        closes, index=pd.to_datetime(pd.Series(stamps), unit="s").dt.tz_localize(None)
    ).dropna()
    series = series[~series.index.duplicated(keep="last")].sort_index()
    series = series.loc[str(start):str(end)]
    if series.empty:
        return PriceSeries(ticker, "yahoo", None, False, "no data in requested window")
    return PriceSeries(ticker, "yahoo", series, True, "")


def fetch_tiingo(ticker: str, start: str, end: str, *, refresh: bool = False) -> PriceSeries:
    """
    Daily adjusted closes from Tiingo, which retains delisted tickers.

    Requires TIINGO_API_KEY. Without it this returns a not-configured result
    rather than raising, so the pipeline still runs on the control cohort.
    """
    if not TIINGO_API_KEY:
        return PriceSeries(ticker, "tiingo", None, False, "TIINGO_API_KEY not configured")

    path = _cache_path("tiingo", ticker)
    payload: list | None = None
    if path.exists() and not refresh:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            payload = None

    if payload is None:
        url = (
            f"https://api.tiingo.com/tiingo/daily/{ticker.lower()}/prices"
            f"?startDate={start}&endDate={end}&format=json&resampleFreq=daily"
        )
        req = urllib.request.Request(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Token {TIINGO_API_KEY}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                payload = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            return PriceSeries(ticker, "tiingo", None, False, f"http {exc.code}")
        except Exception as exc:  # noqa: BLE001
            return PriceSeries(ticker, "tiingo", None, False, f"{type(exc).__name__}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    if not payload:
        return PriceSeries(ticker, "tiingo", None, False, "empty response")

    frame = pd.DataFrame(payload)
    if "date" not in frame.columns:
        return PriceSeries(ticker, "tiingo", None, False, "unexpected schema")
    price_col = "adjClose" if "adjClose" in frame.columns else "close"
    series = pd.Series(
        frame[price_col].to_numpy(),
        index=pd.to_datetime(frame["date"]).dt.tz_localize(None),
    ).dropna().sort_index()
    if series.empty:
        return PriceSeries(ticker, "tiingo", None, False, "no usable rows")
    return PriceSeries(ticker, "tiingo", series, True, "")


PROVIDERS = {"tiingo": fetch_tiingo, "yahoo": fetch_yahoo}


def fetch_prices(
    ticker: str,
    start: str,
    end: str,
    *,
    order: tuple[str, ...] = ("tiingo", "yahoo"),
    refresh: bool = False,
) -> PriceSeries:
    """
    Try providers in order, returning the first usable series.

    Tiingo leads because it retains delisted tickers; Yahoo is the fallback and
    is sufficient for the control cohort.
    """
    attempts = []
    for name in order:
        provider = PROVIDERS.get(name)
        if provider is None:
            continue
        got = provider(ticker, start, end, refresh=refresh)
        if got.ok:
            return got
        attempts.append(f"{name}: {got.reason}")
    return PriceSeries(ticker, "|".join(order), None, False, "; ".join(attempts))


# --------------------------------------------------------------------------
# Integrity validation
# --------------------------------------------------------------------------

@dataclass
class IntegrityReport:
    passed: bool
    failures: tuple[str, ...] = field(default_factory=tuple)
    flags: tuple[str, ...] = field(default_factory=tuple)


def validate_delisted_series(
    closes: pd.Series,
    event_date: str | pd.Timestamp,
    *,
    max_days_trading_after_event: int = 400,
    min_decline_into_event: float = 0.50,
    require_decline: bool = True,
) -> IntegrityReport:
    """
    Reject price series that cannot belong to the firm that failed.

    Three checks, each targeting a failure actually observed in Phase 0:

    1. Trading long after the event.
       Equity in a firm that filed Chapter 11 and delisted does not keep
       trading for years afterwards. BBBY's Yahoo series runs to 2026 because
       the ticker was recycled to Beyond, Inc.

    2. Price rising through and after the event.
       BBBY's series shows $18.73 in the month of filing rising to $35.91 the
       following February. Real distressed equity collapses.

    3. No material decline into the event.
       A firm that reaches Chapter 11 has, essentially without exception, lost
       most of its equity value first. Absence of that decline means the series
       is not tracking the entity that filed.

    `require_decline` can be relaxed for events that are not equity-destroying
    (a solvent parent filing about a subsidiary, a prepackaged reorganisation
    leaving equity intact). Those cases must be adjudicated deliberately, not
    by accident.
    """
    failures: list[str] = []
    flags: list[str] = []

    if closes is None or closes.empty:
        return IntegrityReport(False, ("empty series",))

    event = pd.Timestamp(event_date)
    if event.tzinfo is not None:
        event = event.tz_localize(None)

    pre = closes[closes.index <= event]
    if pre.empty:
        return IntegrityReport(False, ("no observations at or before the event date",))

    after = closes[closes.index > event]
    at_event = float(pre.iloc[-1])

    # Check 1: prolonged trading after the event AT A MEANINGFUL PRICE.
    #
    # Continued quotation on its own is not evidence of recycling: delisted
    # equity routinely trades as a worthless OTC stub for years. First Republic
    # still quotes at $0.0006 against $122.75 two years before seizure, and is
    # unambiguously the same entity. What identifies a recycled ticker is
    # trading afterwards at a price comparable to the pre-event level.
    if not after.empty:
        days_after = (after.index[-1] - event).days
        post_median = float(after.median())
        ratio = post_median / at_event if at_event > 0 else np.inf
        if days_after > max_days_trading_after_event:
            if ratio > 0.25:
                failures.append(
                    f"trades {days_after}d after event at {ratio:.0%} of the "
                    "event-date price - recycled ticker, not the failed entity"
                )
            else:
                flags.append(
                    f"quotes for {days_after}d after event but at {ratio:.1%} of "
                    "the event-date price - consistent with a delisted stub"
                )

    # Check 2: value should not recover materially after the event.
    if not after.empty:
        peak_after = float(after.max())
        if at_event > 0 and peak_after > 2.0 * at_event:
            failures.append(
                f"price rises {peak_after / at_event:.1f}x after the event "
                "- not distressed equity"
            )

    # Check 3: material decline from the pre-event peak.
    lookback = pre[pre.index >= event - pd.Timedelta(days=730)]
    if len(lookback) >= 20:
        peak = float(lookback.max())
        at_event = float(lookback.iloc[-1])
        if peak > 0:
            decline = 1.0 - at_event / peak
            if decline < min_decline_into_event:
                message = (
                    f"only {decline:.0%} below 2y peak at event "
                    f"(expect >={min_decline_into_event:.0%})"
                )
                (failures if require_decline else flags).append(message)

    if len(pre) < 30:
        failures.append(f"only {len(pre)} pre-event observations")

    return IntegrityReport(not failures, tuple(failures), tuple(flags))


def to_monthly(closes: pd.Series) -> pd.Series:
    """Month-end closes, for the event-time panel."""
    if closes is None or closes.empty:
        return pd.Series(dtype=float)
    return closes.resample("ME").last().dropna()


def realised_volatility(
    closes: pd.Series, as_of: str | pd.Timestamp, window_days: int, *, trading_days: int = 252
) -> float:
    """
    Annualised realised volatility of log returns over the trailing window.

    Strictly backward-looking from `as_of`: no observation after the date can
    influence the estimate.
    """
    if closes is None or closes.empty:
        return np.nan
    as_of = pd.Timestamp(as_of)
    if as_of.tzinfo is not None:
        as_of = as_of.tz_localize(None)

    history = closes[closes.index <= as_of]
    if history.size < 20:
        return np.nan
    window = history.iloc[-(window_days + 1):]
    if window.size < 20:
        return np.nan
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        returns = np.diff(np.log(window.to_numpy(dtype=float)))
    returns = returns[np.isfinite(returns)]
    if returns.size < 15:
        return np.nan
    return float(np.std(returns, ddof=1) * np.sqrt(trading_days))
