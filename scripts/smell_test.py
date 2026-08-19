"""
Smell test: pipeline outputs next to reality, for a human to read.

77 passing tests mean the code does what the code intends. They do not mean the
numbers are right. The 2.67x debt double-count surfaced because a human looked
at Ford's $435.67B and found it absurd -- not because a test failed. Ford's own
filings say $163.30B, and no unit test was ever going to know that.

Two kinds of check, deliberately:

  INVARIANTS  Relationships that must hold for any firm, at any date, whatever
              the filings say: total debt cannot exceed total liabilities;
              asset volatility cannot exceed equity volatility under positive
              leverage; asset value cannot be below equity value; the solved
              (V, sigma_V) must reproduce observed equity through the call
              equation. These never go stale and catch real regressions.

  REFERENCES  Hand-entered figures from public filings, compared AT THE SAME
              REPORTING PERIOD. These do go stale, and a drift flag is a
              prompt to open the filing, not a build failure.

Run:  python -m scripts.smell_test [--verbose]
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from src.config import DEFAULT_HORIZON_T
from src.data import edgar, prices
from src.models import merton

# `period` is the exact XBRL period end the reference figures come from, so the
# comparison is like-for-like rather than against whatever the latest filing is.
# VERIFY THESE AGAINST THE FILING before treating a flag as a code bug.
REFERENCES = [
    {
        "cik": "0000320193", "name": "Apple", "ticker": "AAPL",
        "period": "2024-09-28", "liabilities_usd_b": 308.03,
        "source": "FY2024 10-K", "note": "low leverage, deep liquidity",
    },
    {
        "cik": "0000037996", "name": "Ford", "ticker": "F",
        "period": "2024-12-31", "liabilities_usd_b": 236.02,
        "source": "FY2024 10-K",
        "note": "captive finance; debt in custom extension tags. "
                "THE 2.67x double-count case",
    },
    {
        "cik": "0000104169", "name": "Walmart", "ticker": "WMT",
        "period": "2025-01-31", "liabilities_usd_b": 163.13,
        "source": "FY2025 10-K", "note": "large, stable, moderate leverage",
    },
    {
        "cik": "0000012927", "name": "Boeing", "ticker": "BA",
        "period": "2024-12-31", "liabilities_usd_b": 175.29,
        "source": "FY2024 10-K", "note": "negative equity; Merton strained",
    },
    {
        "cik": "0000034088", "name": "Exxon Mobil", "ticker": "XOM",
        "period": "2024-12-31", "liabilities_usd_b": 165.43,
        "source": "FY2024 10-K", "note": "very low leverage",
    },
    {
        "cik": "0001004980", "name": "PG&E", "ticker": "PCG",
        "period": "2024-12-31", "liabilities_usd_b": 103.99,
        "source": "FY2024 10-K", "note": "utility; emerged from Ch11 2020",
    },
    {
        "cik": "0000098222", "name": "Tidewater", "ticker": "TDW",
        "period": "2024-12-31", "liabilities_usd_b": 0.86,
        "source": "FY2024 10-K", "note": "small cap; sanity floor",
    },
    {
        "cik": "0000886158", "name": "Bed Bath & Beyond", "ticker": "BBBYQ",
        "period": "2023-02-25", "liabilities_usd_b": 5.03,
        "source": "FY2022 10-K, last before Ch11",
        "note": "DEFAULTER. Ticker MUST be BBBYQ; BBBY is recycled to Beyond Inc",
    },
    {
        "cik": "0000719739", "name": "SVB Financial", "ticker": "SIVBQ",
        "period": "2022-12-31", "liabilities_usd_b": 195.50,
        "source": "FY2022 10-K, last before failure",
        "note": "DEFAULTER, bank. Merton assumptions do not hold",
    },
]

TOLERANCE = 0.10
RISK_FREE = 0.04


def _b(value) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "       n/a"
    return f"{value:,.2f}B".rjust(10)


def _pct(value) -> str:
    if value is None or not np.isfinite(value):
        return "       n/a"
    return f"{value:.1%}".rjust(10)


def examine(ref: dict, verbose: bool) -> list[str]:
    name = ref["name"]
    flags: list[str] = []
    period = pd.Timestamp(ref["period"])

    print(f"\n  {name} ({ref['ticker']})  --  reference period {period.date()}")
    print(f"    {ref['note']}")

    facts = edgar.get_company_facts(ref["cik"])
    if not facts:
        return [f"{name}: no XBRL company facts"]

    history = edgar.debt_history(ref["cik"], facts)
    shares = edgar.shares_history(ref["cik"], facts)
    if history.empty:
        return [f"{name}: debt_history empty"]

    # Look up AT the reference period, not at the latest filing, so the
    # comparison is like-for-like. Allow a small window for period-end drift.
    window = history[(history["end"] >= period - pd.Timedelta(days=20))
                     & (history["end"] <= period + pd.Timedelta(days=20))]
    if window.empty:
        return [f"{name}: no balance sheet near {period.date()} "
                f"(have {history['end'].min().date()}..{history['end'].max().date()})"]
    row = window.iloc[-1]

    liabilities = None if pd.isna(row["total_liabilities"]) else row["total_liabilities"]
    total_debt = None if pd.isna(row["total_debt"]) else row["total_debt"]
    kmv = None if pd.isna(row["kmv_barrier"]) else row["kmv_barrier"]

    print(f"    {'period matched':<24s}{str(row['end'].date()):>10s}"
          f"   filed {row['filed'].date()}")
    print(f"    {'total liabilities':<24s}{_b(None if liabilities is None else liabilities / 1e9)}"
          f"   filing says {_b(ref['liabilities_usd_b'])}  [{ref['source']}]")
    print(f"    {'total debt':<24s}{_b(None if total_debt is None else total_debt / 1e9)}")
    print(f"    {'KMV barrier':<24s}{_b(None if kmv is None else kmv / 1e9)}")
    print(f"    {'liabilities source':<24s}{str(row['liabilities_source']):>10s}")
    if verbose:
        print(f"    {'debt source':<24s}{row['debt_source']}")

    # ---------------------------------------------------------- references
    if liabilities is not None and ref.get("liabilities_usd_b"):
        got = liabilities / 1e9
        drift = abs(got - ref["liabilities_usd_b"]) / ref["liabilities_usd_b"]
        if drift > TOLERANCE:
            flags.append(
                f"{name}: liabilities {got:,.2f}B vs filing {ref['liabilities_usd_b']:,.2f}B "
                f"({drift:+.0%}) at {row['end'].date()} -- open the 10-K"
            )

    # ---------------------------------------------------------- invariants
    if total_debt is not None and liabilities is not None:
        if total_debt > liabilities * 1.02:
            flags.append(
                f"{name}: INVARIANT total_debt {total_debt / 1e9:,.1f}B > total "
                f"liabilities {liabilities / 1e9:,.1f}B -- double counting is back"
            )
    if kmv is not None and total_debt is not None and kmv > total_debt * 1.001:
        flags.append(f"{name}: INVARIANT KMV barrier exceeds total debt")
    if liabilities is not None and liabilities <= 0:
        flags.append(f"{name}: INVARIANT non-positive total liabilities")

    # ---------------------------------------------------------- Merton
    if shares.empty:
        print(f"    {'shares':<24s}{'unavailable':>10s}")
        return flags
    share_count = edgar.as_of(shares, row["end"], ["shares_outstanding"])
    if not share_count:
        return flags

    barrier = kmv if kmv else liabilities
    if not barrier or barrier <= 0:
        return flags

    series = prices.fetch_prices(
        ref["ticker"],
        (row["end"] - pd.Timedelta(days=420)).date().isoformat(),
        row["end"].date().isoformat(),
        order=("yahoo",),
    )
    if not series.ok:
        print(f"    {'prices':<24s}{'unavailable':>10s}  {series.reason[:40]}")
        return flags

    equity = series.closes * float(share_count["shares_outstanding"])
    solution = merton.solve_iterative(equity.to_numpy(), float(barrier),
                                      RISK_FREE, DEFAULT_HORIZON_T)

    # Equity volatility over EXACTLY the window the solver consumed, otherwise
    # the sigma_V <= sigma_E comparison is meaningless. (This mismatch is what
    # made Apple appear to violate the invariant on the first run.)
    equity_returns = np.diff(np.log(equity.to_numpy(dtype=float)))
    sigma_e = float(np.std(equity_returns, ddof=1) * np.sqrt(252))

    print(f"    {'market cap':<24s}{_b(float(equity.iloc[-1]) / 1e9)}"
          f"   ({len(equity)} obs to {equity.index[-1].date()})")
    print(f"    {'equity vol (same win)':<24s}{_pct(sigma_e)}")

    if not solution.usable:
        print(f"    {'merton solve':<24s}{'FAILED':>10s}  {'; '.join(solution.notes)}")
        flags.append(f"{name}: Merton solve failed -- {'; '.join(solution.notes)}")
        return flags

    dd = merton.distance_to_default(solution.V, solution.sigma_V, float(barrier),
                                    RISK_FREE, DEFAULT_HORIZON_T)
    print(f"    {'asset value V':<24s}{_b(solution.V / 1e9)}")
    print(f"    {'asset vol sigma_V':<24s}{_pct(solution.sigma_V)}")
    print(f"    {'distance to default':<24s}{dd:>9.2f}s   "
          f"PD {merton.default_probability(dd):>7.3%}   "
          f"spread {merton.credit_spread(dd, DEFAULT_HORIZON_T):>6.0f}bp")
    if verbose:
        print(f"    {'solver':<24s}{solution.method}, {solution.iterations} iters")

    equity_now = float(equity.iloc[-1])
    if solution.V < equity_now * 0.999:
        flags.append(
            f"{name}: INVARIANT asset value {solution.V / 1e9:,.1f}B below equity "
            f"{equity_now / 1e9:,.1f}B"
        )
    if solution.sigma_V > sigma_e * 1.02:
        flags.append(
            f"{name}: INVARIANT asset vol {solution.sigma_V:.1%} > equity vol "
            f"{sigma_e:.1%} -- leverage must dampen, not amplify"
        )
    # The call equation must hold at the returned pair.
    implied = merton.equity_from_assets(solution.V, float(barrier), RISK_FREE,
                                        DEFAULT_HORIZON_T, solution.sigma_V)
    if not np.isfinite(implied) or abs(implied - equity_now) > max(equity_now * 1e-4, 1.0):
        flags.append(
            f"{name}: INVARIANT call equation not satisfied "
            f"({implied / 1e9:,.2f}B vs observed {equity_now / 1e9:,.2f}B)"
        )
    if np.isfinite(dd) and abs(dd) > 40:
        flags.append(f"{name}: DD {dd:.1f} implausible")
    return flags


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    print("=" * 78)
    print("SMELL TEST -- read these numbers; do not just check the exit code")
    print("=" * 78)

    flags: list[str] = []
    for ref in REFERENCES:
        try:
            flags += examine(ref, args.verbose)
        except Exception as exc:  # noqa: BLE001 - one bad firm must not hide the rest
            flags.append(f"{ref['name']}: {type(exc).__name__}: {exc}")

    print("\n" + "=" * 78)
    invariants = [f for f in flags if "INVARIANT" in f]
    others = [f for f in flags if "INVARIANT" not in f]

    if invariants:
        print(f"{len(invariants)} INVARIANT VIOLATION(S) -- these are bugs:\n")
        for flag in invariants:
            print(f"  !! {flag}")
    if others:
        print(f"\n{len(others)} reference drift / availability flag(s) -- "
              "check the filing before changing code:\n")
        for flag in others:
            print(f"  ?  {flag}")
    if not flags:
        print("No flags. The numbers still need reading.")
    print("=" * 78)
    return 1 if invariants else 0


if __name__ == "__main__":
    raise SystemExit(main())
