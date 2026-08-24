"""
Accounting-only shadow credit rating.

This module exists to break a circularity. The predecessor assigned a benchmark
rating with `_estimate_rating_from_merton_leverage(V, D)` -- a function of the
model's own solved asset value -- then looked up a cohort spread for that rating
and called the difference a mispricing. Both sides of the comparison descended
from the same model output, so the gap was partly the model arguing with itself.

The fix is structural, not cosmetic: **nothing in this module may touch a Merton
quantity.** Inputs are filing fundamentals only. There is deliberately no
parameter through which V, sigma_V, distance to default or implied spread could
enter, and `tests/test_shadow_rating.py` asserts that property directly rather
than trusting the convention.

Mapping follows Damodaran's published synthetic-rating table (NYU Stern), which
maps interest coverage to rating with separate large-cap and small-cap variants.
Coverage is the primary axis; at most ONE notch of adjustment is applied on the
secondary ratios, and the notch and its reason are recorded so every assignment
is auditable.

WHAT THIS IS NOT: an agency rating. A real rating incorporates analyst judgement,
management access and private information that a coverage ratio cannot see. It
is a cohort assignment for benchmarking, and the page says so.

Threshold values below are transcribed from the published table and should be
re-checked against the current version before publication; `verified_against`
records what they were checked against and when.
"""
from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "DAMODARAN_SPREAD_BPS_JAN2026",
    "RATING_SCALE",
    "SOURCE",
    "ShadowRating",
    "shadow_rating",
]

SOURCE = {
    "table": "Damodaran synthetic rating, interest coverage to rating",
    "publisher": "NYU Stern, Aswath Damodaran",
    "large_url": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ratings.html",
    "small_url": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/smallrating.htm",
    "large_vintage": "January 2026",
    "small_vintage": "January 2017",
    "large_verified": "2026-08-22, all 14 threshold rows checked against source, "
                      "zero mismatches",
    "small_verified": "2026-08-22, all 14 threshold rows checked against source, "
                      "zero mismatches, but the table itself is a January 2017 "
                      "analysis and is NINE YEARS older than the large-firm table",
    "financial_table": "A separate table for financial service firms exists "
                       "(January 2026, AAA above coverage 3.0, BBB at 0.9-1.2, "
                       "D at or below 0.05). It is deliberately NOT used: "
                       "financials are excluded from the pre-registered primary "
                       "metric on Merton-inapplicability grounds.",
}

# Damodaran publishes a January 2026 default spread beside each large-company
# synthetic rating. This periodic table is the permitted public benchmark for
# the illustrative divergence screen. It is not a live credit price, an index
# observation or an issuer bond quote.
DAMODARAN_SPREAD_BPS_JAN2026 = {
    "AAA": 40, "AA": 55, "A+": 70, "A": 78, "A-": 89, "BBB": 111,
    "BB+": 138, "BB": 184, "B+": 275, "B": 321, "B-": 509,
    "CCC": 885, "CC": 1261, "C": 1600, "D": 1900,
}

# ---------------------------------------------------------------------------
# Size band
# ---------------------------------------------------------------------------
# Damodaran's boundary is $5bn of MARKET CAP. This module uses TOTAL ASSETS,
# and the substitution is deliberate and consequential enough to state twice.
#
# Why not market cap: market cap is a price, and the equity-implied spread on
# the other side of this comparison is built from that same price. A market-cap
# band would move both sides together. In a distress event equity collapses,
# the theoretical spread widens, the firm drops a band, the benchmark widens
# too, and the divergence being measured is damped exactly when it should open.
# The bias runs toward FALSE NEGATIVES, the worst direction for a screen.
#
# What the band is worth: at coverage 3.0 the large table returns A- and the
# small table returns BB, a three-notch gap from the same input. Across the
# plausible coverage range the gap runs 1 to 3 notches. It is not a detail.
#
# Why this level: $5bn of assets is NOT equivalent to $5bn of market cap, and
# the two cannot be reconciled without market caps for the whole universe,
# which the price-API symbol quota forbids. So the level is a judgement, stated
# as one. It sits near the 75th percentile of non-financial filers with at
# least $50M of assets (measured 2023Q1: p75 = $4.73bn), so it separates
# roughly the top quartile. The numeral matching Damodaran's is a coincidence,
# not a claimed equivalence.
#
# The real defence is the sensitivity: `shadow_rating(..., force_band=...)`
# flips a firm's band so the effect on any conclusion can be measured directly.
LARGE_CAP_ASSET_THRESHOLD = 5_000_000_000

# Measured on the 2023Q1 point-in-time universe, non-financials, assets >= $50M.
BAND_DIAGNOSTICS = {
    "universe_quarter": "2023Q1",
    "universe_n": 3132,
    "p50_assets_usd": 1_100_000_000,
    "p75_assets_usd": 4_730_000_000,
    "p85_assets_usd": 10_350_000_000,
    "share_large_at_threshold": 0.242,
    "share_within_30pct_of_boundary": 0.085,
}

# (minimum coverage, rating). Descending; first match wins.
_LARGE_CAP = [
    (8.50, "AAA"), (6.50, "AA"), (5.50, "A+"), (4.25, "A"), (3.00, "A-"),
    (2.50, "BBB"), (2.25, "BB+"), (2.00, "BB"), (1.75, "B+"), (1.50, "B"),
    (1.25, "B-"), (0.80, "CCC"), (0.65, "CC"), (0.20, "C"),
]
_SMALL_CAP = [
    (12.50, "AAA"), (9.50, "AA"), (7.50, "A+"), (6.00, "A"), (4.50, "A-"),
    (4.00, "BBB"), (3.50, "BB+"), (3.00, "BB"), (2.50, "B+"), (2.00, "B"),
    (1.50, "B-"), (1.25, "CCC"), (0.80, "CC"), (0.50, "C"),
]

# Ordered best to worst. Notching moves along this scale.
RATING_SCALE = [
    "AAA", "AA", "A+", "A", "A-", "BBB", "BB+", "BB", "B+", "B", "B-",
    "CCC", "CC", "C", "D",
]

# Rating to broad rating bucket. These labels contain no market observations.
COHORT_INDEX = {
    "AAA": "AAA", "AA": "AA", "A+": "A", "A": "A", "A-": "A",
    "BBB": "BBB", "BB+": "BB", "BB": "BB",
    "B+": "B", "B": "B", "B-": "B",
    "CCC": "CCC", "CC": "CCC", "C": "CCC", "D": "CCC",
}


@dataclass
class ShadowRating:
    rating: str
    base_rating: str
    size_band: str
    interest_coverage: float | None
    notch: int = 0
    notch_reason: str = ""
    near_size_boundary: bool = False
    band_forced: bool = False
    cohort_index: str = ""
    usable: bool = True
    notes: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "rating": self.rating,
            "base_rating": self.base_rating,
            "size_band": self.size_band,
            "interest_coverage": self.interest_coverage,
            "notch": self.notch,
            "notch_reason": self.notch_reason,
            "near_size_boundary": self.near_size_boundary,
            "band_forced": self.band_forced,
            "cohort_index": self.cohort_index,
            "usable": self.usable,
            "notes": list(self.notes),
        }


def _base_from_coverage(coverage: float, large_cap: bool) -> str:
    table = _LARGE_CAP if large_cap else _SMALL_CAP
    for minimum, rating in table:
        if coverage >= minimum:
            return rating
    return "D"


def _notch(rating: str, steps: int) -> str:
    """Move along the scale; positive steps mean worse."""
    i = RATING_SCALE.index(rating)
    return RATING_SCALE[max(0, min(len(RATING_SCALE) - 1, i + steps))]


def shadow_rating(
    *,
    ebit: float | None,
    interest_expense: float | None,
    total_assets: float | None,
    total_debt: float | None = None,
    ebitda: float | None = None,
    revenue: float | None = None,
    force_band: str | None = None,
) -> ShadowRating:
    """
    Assign a benchmark rating from filing fundamentals alone.

    Every parameter is keyword-only and comes from the balance sheet or income
    statement. There is no parameter for asset value, asset volatility, distance
    to default or implied spread, and adding one would be a defect: it is exactly
    the circularity this module was written to remove.

    Returns a ShadowRating carrying the base assignment, any notch and its
    stated reason, so a reader can audit how the cohort was chosen.
    """
    notes: list[str] = []

    if not total_assets or total_assets <= 0:
        return ShadowRating(
            rating="", base_rating="", size_band="unknown",
            interest_coverage=None, usable=False,
            notes=("total assets missing or non-positive",),
        )

    if force_band in ("large", "small"):
        # Sensitivity path: flip the band deliberately to measure what the
        # threshold choice is worth. Recorded so a forced result can never be
        # mistaken for a natural one.
        large_cap = force_band == "large"
        notes.append(f"size band FORCED to {force_band} for sensitivity")
    else:
        large_cap = total_assets >= LARGE_CAP_ASSET_THRESHOLD
    size_band = "large" if large_cap else "small"

    # Firms near the boundary have a rating that is partly an artefact of where
    # the cutoff was drawn. Flagged rather than silently assigned.
    distance = abs(total_assets - LARGE_CAP_ASSET_THRESHOLD) / LARGE_CAP_ASSET_THRESHOLD
    near_boundary = distance <= 0.30
    if near_boundary and force_band is None:
        notes.append(
            f"within {distance:.0%} of the size boundary; rating is sensitive "
            "to the threshold choice"
        )

    # Interest coverage, the primary axis.
    if ebit is None or interest_expense is None:
        return ShadowRating(
            rating="", base_rating="", size_band=size_band,
            interest_coverage=None, usable=False,
            notes=("EBIT or interest expense missing; coverage undefined",),
        )

    if interest_expense <= 0:
        # No interest burden at all. Treated as the top of the scale but
        # flagged, because it usually means a debt-free firm the cohort
        # comparison is not informative for.
        coverage = float("inf")
        notes.append("no interest expense reported; coverage unbounded")
    else:
        coverage = ebit / interest_expense

    base = _base_from_coverage(coverage, large_cap)

    # At most ONE notch, on the secondary ratios, with the reason recorded.
    steps, reason = 0, ""
    leverage_ratio = (
        total_debt / ebitda if (total_debt and ebitda and ebitda > 0) else None
    )
    margin = (ebit / revenue) if (revenue and revenue > 0) else None

    if leverage_ratio is not None and leverage_ratio > 6.0:
        steps, reason = 1, f"debt/EBITDA {leverage_ratio:.1f}x above 6.0"
    elif margin is not None and margin < 0:
        steps, reason = 1, f"operating margin {margin:.1%} negative"
    elif leverage_ratio is not None and leverage_ratio < 1.5 and margin is not None and margin > 0.20:
        steps, reason = -1, (
            f"debt/EBITDA {leverage_ratio:.1f}x below 1.5 with "
            f"operating margin {margin:.1%}"
        )

    final = _notch(base, steps) if steps else base

    return ShadowRating(
        rating=final,
        base_rating=base,
        size_band=size_band,
        interest_coverage=None if coverage == float("inf") else coverage,
        notch=steps,
        notch_reason=reason,
        near_size_boundary=near_boundary,
        band_forced=force_band is not None,
        cohort_index=COHORT_INDEX.get(final, "BBB"),
        usable=True,
        notes=tuple(notes),
    )
