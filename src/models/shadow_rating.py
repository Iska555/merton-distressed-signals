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

__all__ = ["ShadowRating", "shadow_rating", "RATING_SCALE", "SOURCE"]

SOURCE = {
    "table": "Damodaran synthetic rating, interest coverage to rating",
    "publisher": "NYU Stern, Aswath Damodaran",
    "url": "https://pages.stern.nyu.edu/~adamodar/",
    "verified_against": "PENDING - re-check thresholds against the current "
                        "published file before publication",
}

# Assets, not market cap: market cap is a price, and prices are what the Merton
# side of the comparison is built from. Using it here would reintroduce a
# common input to both sides. Damodaran's bands are stated on market cap, so
# this is a documented substitution, not a transcription.
LARGE_CAP_ASSET_THRESHOLD = 5_000_000_000

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

# Rating -> the FRED ICE BofA cohort index it maps to. The site reads the live
# series; these are the bucket assignments, not spread levels.
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

    large_cap = total_assets >= LARGE_CAP_ASSET_THRESHOLD
    size_band = "large" if large_cap else "small"

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
        cohort_index=COHORT_INDEX.get(final, "BBB"),
        usable=True,
        notes=tuple(notes),
    )
