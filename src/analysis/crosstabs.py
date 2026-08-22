"""
Era-conditional cross-tabs over the resolution audit.

Era is the dominant axis of this dataset. Two SEC filing-rule changes -- XBRL
instances from roughly 2011, cover-page dei:TradingSymbol from 2019 -- decide
whether a delisted firm can be identified at all, and resolution runs from
12.8% to 68.7% across the window because of them. Anything else measured on
this sample is correlated with era until shown otherwise, so a pooled cross-tab
of resolution against size or sector may be reporting era a second time under
another name.

That is not hypothetical. A pooled size gradient reported at N = 190 did not
survive at N = 346, and the float variable that produced it is itself partly an
artefact of the XBRL transition: dei:EntityPublicFloat is an XBRL tag, so a
pre-2011 filer lands in "no float reported" *by construction* rather than by
being small. See float_availability().

Every figure here carries its cell count. Rates are suppressed where the 95%
Wilson interval is too wide to separate one band from another.
"""
from __future__ import annotations

import math
from typing import Sequence

import pandas as pd

# Era boundaries are the filing-rule thresholds, not round numbers:
#   2011  XBRL instance documents begin to exist
#   2019  FAST Act Modernization adds the cover-page trading symbol
# The 2012-14 / 2015-18 split separates early sparse tagging from routine
# tagging; 2022-24 is held apart because it is a distinct rate regime.
ERAS: tuple[tuple[int, int, str], ...] = (
    (2010, 2011, "2010-11"),
    (2012, 2014, "2012-14"),
    (2015, 2018, "2015-18"),
    (2019, 2021, "2019-21"),
    (2022, 2024, "2022-24"),
)

FLOAT_BANDS: tuple[tuple[float, float, str], ...] = (
    (0.0, 50e6, "under $50M"),
    (50e6, 200e6, "$50-200M"),
    (200e6, float("inf"), "$200M and above"),
)
NO_FLOAT = "none reported"
FLOAT_ORDER: tuple[str, ...] = tuple(b[2] for b in FLOAT_BANDS) + (NO_FLOAT,)

# A rate is shown only when its 95% Wilson interval is at least this narrow.
# Fifty points is the width at which a cell stops being able to separate any
# two of the bands above it, which is the entire purpose of the table. The rule
# is on interval width rather than on a flat count because an extreme rate is
# estimated precisely even at small n -- 0 of 13 is informative, 6 of 13 is not.
MAX_REPORTABLE_WIDTH = 0.50


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """
    Wilson score interval.

    Used rather than the normal approximation because the counts here are small
    and several proportions sit near zero, where the normal interval goes
    negative and understates the upper bound.
    """
    if n == 0:
        return (float("nan"), float("nan"))
    p = successes / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def era_label(year) -> str | None:
    try:
        year = int(year)
    except (TypeError, ValueError):
        return None
    for lo, hi, label in ERAS:
        if lo <= year <= hi:
            return label
    return None


def float_band(value) -> str:
    """dei:EntityPublicFloat band. Absent is its own band and is never pooled."""
    if value is None or pd.isna(value):
        return NO_FLOAT
    value = float(value)
    for lo, hi, label in FLOAT_BANDS:
        if lo <= value < hi:
            return label
    return NO_FLOAT


def normalise(frame: pd.DataFrame) -> pd.DataFrame:
    """Add era and float-band columns and coerce the CSV's string booleans."""
    out = frame.copy()
    out["event_year"] = pd.to_numeric(out.get("event_year"), errors="coerce")
    out["resolved"] = out["resolved"].astype(str).str.lower().isin(["true", "1"])
    out["public_float_usd"] = pd.to_numeric(
        out.get("public_float_usd"), errors="coerce")
    out["era"] = out["event_year"].map(era_label)
    out["float_band"] = out["public_float_usd"].map(float_band)
    if "xbrl_instances_seen" in out.columns:
        out["any_xbrl"] = pd.to_numeric(
            out["xbrl_instances_seen"], errors="coerce").fillna(0) > 0
    return out


def cell(chunk: pd.DataFrame) -> dict:
    """One table cell: counts always, rate only when the interval permits."""
    n = len(chunk)
    if n == 0:
        return {"n": 0, "resolved": 0, "rate": None,
                "lo": None, "hi": None, "reportable": False}
    resolved = int(chunk["resolved"].sum())
    lo, hi = wilson_interval(resolved, n)
    return {
        "n": n,
        "resolved": resolved,
        "rate": resolved / n,
        "lo": lo,
        "hi": hi,
        "reportable": (hi - lo) <= MAX_REPORTABLE_WIDTH,
    }


def conditional_crosstab(frame: pd.DataFrame, key: str,
                         order: Sequence[str] | None = None) -> dict:
    """
    Resolution by ``key`` within each era, with the pooled column beside it.

    The pooled column is kept deliberately: the point of the table is to let a
    reader watch a pooled difference dissolve once era is held fixed, and that
    requires both to be visible at once.
    """
    frame = frame if "era" in frame.columns else normalise(frame)
    eras = [label for _, _, label in ERAS if (frame["era"] == label).any()]
    if order is None:
        order = frame[key].value_counts().index.tolist()
    rows = []
    for value in order:
        subset = frame[frame[key] == value]
        if subset.empty:
            continue
        rows.append({
            "label": str(value),
            "cells": [cell(subset[subset["era"] == e]) for e in eras],
            "pooled": cell(subset),
        })
    return {
        "key": key,
        "eras": eras,
        "rows": rows,
        "all": {
            "cells": [cell(frame[frame["era"] == e]) for e in eras],
            "pooled": cell(frame),
        },
    }


def float_availability(frame: pd.DataFrame) -> dict:
    """
    Whether a firm reports a public float at all, against whether it has XBRL.

    dei:EntityPublicFloat exists only inside an XBRL instance. Where the two
    line up, "reports no float" is largely "filed before XBRL" wearing a
    different label, and the no-float band of a size table is measuring the
    filing-rule transition rather than firm size.
    """
    frame = frame if "era" in frame.columns else normalise(frame)
    if "any_xbrl" not in frame.columns:
        return {}
    has_float = frame["float_band"] != NO_FLOAT
    grid = []
    for xbrl in (True, False):
        chunk = frame[frame["any_xbrl"] == xbrl]
        with_float = int((chunk["float_band"] != NO_FLOAT).sum())
        grid.append({
            "any_xbrl": bool(xbrl),
            "n": len(chunk),
            "reports_float": with_float,
            "share": (with_float / len(chunk)) if len(chunk) else None,
        })
    by_era = []
    for _, _, label in ERAS:
        chunk = frame[frame["era"] == label]
        if chunk.empty:
            continue
        by_era.append({
            "label": label,
            "n": len(chunk),
            "reports_float": int((chunk["float_band"] != NO_FLOAT).sum()),
            "any_xbrl": int(chunk["any_xbrl"].sum()),
        })
    return {
        "grid": grid,
        "by_era": by_era,
        "agreement": float((frame["any_xbrl"] == has_float).mean()) if len(frame) else None,
        "n": len(frame),
    }


def format_crosstab(table: dict, width: int = 34) -> str:
    """Fixed-width rendering for the audit script's console summary."""
    eras = table["eras"]
    lines = [f"{table['key']:<{width}}"
             + "".join(f"{e:>14}" for e in eras) + f"{'POOLED':>14}"]

    def fmt(c: dict) -> str:
        if c["n"] == 0:
            return "-"
        rate = f" {c['rate']:.0%}" if c["reportable"] else " ??"
        return f"{c['resolved']}/{c['n']}{rate}"

    for row in table["rows"]:
        lines.append(f"{row['label']:<{width}}"
                     + "".join(f"{fmt(c):>14}" for c in row["cells"])
                     + f"{fmt(row['pooled']):>14}")
    lines.append(f"{'ALL':<{width}}"
                 + "".join(f"{fmt(c):>14}" for c in table["all"]["cells"])
                 + f"{fmt(table['all']['pooled']):>14}")
    lines.append(f"  ?? = 95% Wilson interval wider than {MAX_REPORTABLE_WIDTH:.0%}; "
                 "counts shown, rate withheld")
    return "\n".join(lines)
