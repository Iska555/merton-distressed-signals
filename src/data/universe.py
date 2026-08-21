"""
Sample construction: treatment adjudication and control matching.

This module implements `docs/matching-spec.md` and nothing else. The spec was
committed before this file existed, deliberately: control matching is the
easiest place in the project to cheat without noticing, and a specification
with an earlier timestamp than the data is the only real defence.

Where the code must make a choice the spec did not anticipate, that is a bug in
one of the two. Fix the spec in its own commit, state why, and disclose the
amendment on /data. Do not resolve it silently here.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..config import (
    CONTROLS_PER_TREATMENT,
    MATCH_ANCHOR_MONTHS_BEFORE,
)
from . import dera, edgar

# spec section 3: the whole study must fit inside this many unique symbols,
# leaving 100 of Tiingo's 500/month in reserve.
SYMBOL_BUDGET_FOR_STUDY = 400

# spec sections 1.1 T6 / 1.2 C5
MIN_TOTAL_ASSETS = 50_000_000

SIC_DIVISIONS = [
    (100, 999, "Agriculture, Forestry, Fishing"),
    (1000, 1499, "Mining"),
    (1500, 1799, "Construction"),
    (2000, 3999, "Manufacturing"),
    (4000, 4999, "Transport & Utilities"),
    (5000, 5199, "Wholesale Trade"),
    (5200, 5999, "Retail Trade"),
    (6000, 6799, "Finance, Insurance, Real Estate"),
    (7000, 8999, "Services"),
    (9100, 9999, "Public Administration"),
]

FINANCIAL_SIC_RANGE = (6000, 6799)


def sic_division(sic) -> str:
    try:
        code = int(sic)
    except (TypeError, ValueError):
        return "Unknown"
    for low, high, label in SIC_DIVISIONS:
        if low <= code <= high:
            return label
    return "Unknown"


def is_financial(sic) -> bool:
    try:
        code = int(sic)
    except (TypeError, ValueError):
        return False
    return FINANCIAL_SIC_RANGE[0] <= code <= FINANCIAL_SIC_RANGE[1]


# --------------------------------------------------------------------------
# Ratio (spec section 3)
# --------------------------------------------------------------------------

def fits_monthly_budget(n_treatment: int,
                        *, budget: int = SYMBOL_BUDGET_FOR_STUDY) -> bool:
    """
    Can this treatment cohort plus at least one control each fit one month?

    Above roughly 200 treatment firms even a 1:1 ratio breaches the 400-symbol
    budget. The spec forbids truncating the treatment cohort, so the run spans
    two calendar months instead, which the symbol ledger already supports. See
    spec section 3.
    """
    return n_treatment * 2 <= budget


def controls_per_treatment(n_treatment: int,
                           *, budget: int = SYMBOL_BUDGET_FOR_STUDY,
                           target: int = CONTROLS_PER_TREATMENT) -> int:
    """
    ratio = max(1, min(target, floor(budget / n_treatment) - 1))

    The binding constraint is Tiingo's monthly unique-symbol cap, not
    statistical power. The treatment cohort is never truncated to preserve the
    ratio: treatment firms are the scarce resource and dropping them would
    reintroduce exactly the selection problem this study exists to avoid, so
    the ratio absorbs the constraint instead.
    """
    if n_treatment <= 0:
        return target
    return max(1, min(target, budget // n_treatment - 1))


# --------------------------------------------------------------------------
# Adjudication (spec section 5)
# --------------------------------------------------------------------------

class Adjudication:
    OWN_BANKRUPTCY = "OWN_BANKRUPTCY"
    STILL_FILING = "REJECTED_STILL_FILING"          # A1
    NO_EQUITY_COLLAPSE = "REJECTED_NO_COLLAPSE"     # A2
    FLOAT_SURVIVED = "REJECTED_FLOAT_SURVIVED"      # A3
    INSUFFICIENT_DATA = "INDETERMINATE_NO_DATA"


@dataclass
class AdjudicationResult:
    cik: str
    verdict: str
    evidence: dict = field(default_factory=dict)

    @property
    def accepted(self) -> bool:
        return self.verdict == Adjudication.OWN_BANKRUPTCY


def adjudicate_still_filing(cik: str, event_date, *, months: int = 24) -> AdjudicationResult:
    """
    Spec A1: reject if the registrant keeps filing 10-K/10-Q well past the event.

    A parent filing an 8-K about a subsidiary's bankruptcy carries on reporting
    as though nothing happened -- RenaissanceRe, LendingTree, FirstEnergy and
    NRG all appear in the raw Item 1.03 hits and are all alive. A firm whose own
    bankruptcy is at issue stops filing, is acquired, or re-emerges as a new
    registrant.
    """
    from . import identity  # local import: identity imports edgar, avoid a cycle

    event = pd.Timestamp(event_date)
    filings = identity._all_filings(cik)
    if filings.empty:
        return AdjudicationResult(cik, Adjudication.INSUFFICIENT_DATA,
                                  {"reason": "no filing index"})

    periodic = filings[filings["form"].isin(["10-K", "10-Q"])]
    after = periodic[periodic["filingDate"] > event + pd.DateOffset(months=months)]
    evidence = {
        "periodic_filings_after_window": int(len(after)),
        "last_periodic_filing": (str(periodic["filingDate"].max().date())
                                 if not periodic.empty else None),
        "months_checked": months,
    }
    if len(after) >= 2:
        return AdjudicationResult(cik, Adjudication.STILL_FILING, evidence)
    return AdjudicationResult(cik, Adjudication.OWN_BANKRUPTCY, evidence)


# --------------------------------------------------------------------------
# Covariates (spec section 2)
# --------------------------------------------------------------------------

def anchor_date(event_date, months: int = MATCH_ANCHOR_MONTHS_BEFORE) -> pd.Timestamp:
    """Covariate measurement date: t - 24 months."""
    return pd.Timestamp(event_date) - pd.DateOffset(months=months)


def quarter_of(date) -> tuple[int, int]:
    stamp = pd.Timestamp(date)
    return stamp.year, (stamp.month - 1) // 3 + 1


def eligible_universe_at(date, *, min_assets: float = MIN_TOTAL_ASSETS) -> pd.DataFrame:
    """
    Point-in-time pool of filers with usable covariates, with deciles.

    Deciles are computed WITHIN this quarter's pool, per spec section 2, so
    "size decile 7" means the same thing for a 2013 event as for a 2022 one
    even though the dollar boundaries differ.
    """
    year, quarter = quarter_of(date)
    frame = dera.fundamentals(year, quarter)
    if frame.empty:
        return pd.DataFrame()

    frame = dera.derive_barriers(frame)
    frame = frame[
        frame["total_assets"].notna()
        & frame["total_liabilities"].notna()
        & frame["leverage"].notna()
        & (frame["total_assets"] >= min_assets)
    ].copy()
    if frame.empty:
        return frame

    frame["sic_division"] = frame["sic"].map(sic_division)
    frame["is_financial"] = frame["sic"].map(is_financial)
    frame["log_assets"] = np.log(frame["total_assets"].astype(float))

    # Deterministic decile assignment; duplicates="drop" guards against a
    # degenerate quarter with fewer than ten distinct values.
    frame["size_decile"] = pd.qcut(frame["log_assets"], 10,
                                   labels=False, duplicates="drop") + 1
    frame["leverage_decile"] = pd.qcut(frame["leverage"].astype(float), 10,
                                       labels=False, duplicates="drop") + 1
    frame["anchor_quarter"] = f"{year}Q{quarter}"
    return frame.reset_index(drop=True)


# --------------------------------------------------------------------------
# Matching (spec sections 2.2, 4)
# --------------------------------------------------------------------------

@dataclass
class MatchResult:
    treatment_cik: str
    event_date: str
    controls: list[str]
    shortfall: int
    anchor_quarter: str
    notes: tuple[str, ...] = field(default_factory=tuple)


def match_controls(
    treatment: pd.DataFrame,
    *,
    ratio: int | None = None,
    event_dates: dict | None = None,
    caliper: int = 1,
    verbose: bool = True,
) -> tuple[pd.DataFrame, list[MatchResult]]:
    """
    Match controls to treatment firms per the pre-registered spec.

    `treatment` needs columns: cik, event_date, sic.

    Order (spec 4.1): ascending event date, then ascending CIK. Earlier events
    get first claim on the pool, which is arbitrary but fixed in advance.

    Selection is WITHOUT REPLACEMENT across the whole study (spec 4.1): one
    firm populating many matched sets would narrow the control band
    artificially and understate standard errors.

    Tie-break (spec 4.2) is a total order ending in ascending CIK, so no random
    draw is ever needed and matched sets are byte-reproducible. RANDOM_SEED is
    deliberately not consulted.
    """
    if treatment.empty:
        return pd.DataFrame(), []

    treatment = treatment.copy()
    treatment["event_date"] = pd.to_datetime(treatment["event_date"])
    treatment = treatment.sort_values(["event_date", "cik"]).reset_index(drop=True)

    if ratio is None:
        ratio = controls_per_treatment(len(treatment))
    if verbose:
        print(f"Matching {len(treatment)} treatment firms at {ratio}:1 "
              f"({len(treatment) * (ratio + 1)} symbols)", flush=True)

    # Spec C2 (amended 2026-08-20): a control must be alive and not yet in
    # default at the matched treatment firm's t=0. A firm that defaults LATER
    # is retained and censored, because excluding it would use future
    # information to make a present selection -- leaving a control group known
    # ex post never to have failed, and biasing the false-positive rate low.
    known_events = {str(k).zfill(10): pd.Timestamp(v)
                    for k, v in (event_dates or {}).items()}
    treatment_ciks = set(treatment["cik"])
    used: set[str] = set()

    rows, results = [], []
    universe_cache: dict[str, pd.DataFrame] = {}

    for record in treatment.itertuples(index=False):
        anchor = anchor_date(record.event_date)
        key = f"{quarter_of(anchor)[0]}Q{quarter_of(anchor)[1]}"
        if key not in universe_cache:
            universe_cache[key] = eligible_universe_at(anchor)
        pool = universe_cache[key]

        if pool.empty:
            results.append(MatchResult(record.cik, str(record.event_date.date()),
                                       [], ratio, key,
                                       ("no filer universe for anchor quarter",)))
            continue

        own = pool[pool["cik"] == record.cik]
        if own.empty:
            results.append(MatchResult(record.cik, str(record.event_date.date()),
                                       [], ratio, key,
                                       ("treatment firm absent from anchor universe",)))
            continue
        own = own.iloc[0]

        # Already-defaulted-by-t0 firms are ineligible; later defaulters are not.
        defaulted_by_now = {
            cik for cik, when in known_events.items()
            if when <= record.event_date
        }
        candidates = pool[
            (pool["sic_division"] == own["sic_division"])          # exact sector
            & (~pool["cik"].isin(treatment_ciks))
            & (~pool["cik"].isin(defaulted_by_now))
            & (~pool["cik"].isin(used))
            & ((pool["size_decile"] - own["size_decile"]).abs() <= caliper)
            & ((pool["leverage_decile"] - own["leverage_decile"]).abs() <= caliper)
        ].copy()

        if candidates.empty:
            results.append(MatchResult(record.cik, str(record.event_date.date()),
                                       [], ratio, key, ("no candidate in caliper",)))
            continue

        # Spec 4.2 tie-break, in strict order.
        candidates["gap_assets"] = (candidates["log_assets"] - own["log_assets"]).abs()
        candidates["gap_leverage"] = (
            candidates["leverage"].astype(float) - float(own["leverage"])
        ).abs()
        candidates = candidates.sort_values(
            ["gap_assets", "gap_leverage", "cik"], ascending=[True, True, True]
        )

        chosen = candidates.head(ratio)
        used.update(chosen["cik"])

        for control in chosen.itertuples(index=False):
            later_event = known_events.get(control.cik)
            rows.append({
                # Recorded, never used to filter (spec 1.3).
                "control_defaulted_later": later_event is not None,
                "control_event_date": (str(later_event.date())
                                       if later_event is not None else None),
                "censored_at": str(record.event_date.date()),
                "treatment_cik": record.cik,
                "event_date": str(record.event_date.date()),
                "control_cik": control.cik,
                "control_name": control.name,
                "anchor_quarter": key,
                "sic_division": control.sic_division,
                "size_decile": control.size_decile,
                "leverage_decile": control.leverage_decile,
                "treatment_size_decile": own["size_decile"],
                "treatment_leverage_decile": own["leverage_decile"],
                "log_assets_gap": float(control.gap_assets),
                "leverage_gap": float(control.gap_leverage),
            })

        results.append(MatchResult(
            record.cik, str(record.event_date.date()),
            list(chosen["cik"]), max(0, ratio - len(chosen)), key,
        ))

    return pd.DataFrame(rows), results


def balance_table(matched: pd.DataFrame, universe_by_quarter: dict) -> pd.DataFrame:
    """
    Standardised mean differences between treatment and matched controls.

    Published regardless of outcome (spec section 8). A matched design that
    does not actually balance is a finding, not something to quietly re-tune.
    """
    if matched.empty:
        return pd.DataFrame()
    rows = []
    for column, treat_col in (("size_decile", "treatment_size_decile"),
                              ("leverage_decile", "treatment_leverage_decile")):
        control_values = matched[column].astype(float)
        treat_values = matched[treat_col].astype(float)
        pooled = np.sqrt((control_values.var(ddof=1) + treat_values.var(ddof=1)) / 2)
        smd = (treat_values.mean() - control_values.mean()) / pooled if pooled else np.nan
        rows.append({
            "covariate": column,
            "treatment_mean": float(treat_values.mean()),
            "control_mean": float(control_values.mean()),
            "standardised_mean_difference": float(smd),
            "balanced_at_0.1": bool(abs(smd) < 0.1) if np.isfinite(smd) else False,
        })
    return pd.DataFrame(rows)
