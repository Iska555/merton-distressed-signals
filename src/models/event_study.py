"""
Event-time alignment and cohort bands.

The headline exhibit on /evidence: median distance to default and its
interquartile band from t-36 to t=0, treatment against matched control, in
event time.

Two things this module is careful about, because both can manufacture a
finding that is not there:

**Composition drift.** Firms enter and leave the panel at different event-time
months -- a firm listed 20 months before its bankruptcy contributes nothing at
t-36. If the median is taken over whoever happens to be present, a rising or
falling line can reflect the changing membership rather than any change in the
firms. Every band therefore carries its own `n`, and a balanced-panel variant
is provided that keeps only firms present throughout.

**Median, not mean.** Distance to default is heavily skewed and unbounded
above; a single safe firm can move a mean visibly. Medians and quartiles are
reported, with means available only as a secondary column.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = [
    "to_event_time",
    "cohort_bands",
    "balanced_panel",
    "composition_table",
    "difference_in_medians",
]


def to_event_time(
    panel: pd.DataFrame,
    events: pd.DataFrame,
    *,
    firm_col: str = "cik",
    date_col: str = "date",
    event_col: str = "event_date",
) -> pd.DataFrame:
    """
    Add `months_to_event`, negative before the event and 0 at it.

    Controls inherit the event date of the treatment firm they were matched to,
    so both cohorts are aligned on the same calendar window. Aligning controls
    on their own (nonexistent) event would compare different calendar periods
    and confound the comparison with market conditions.
    """
    if panel.empty:
        return panel.assign(months_to_event=pd.Series(dtype=float))

    merged = panel.merge(events[[firm_col, event_col]], on=firm_col, how="left")
    merged[date_col] = pd.to_datetime(merged[date_col])
    merged[event_col] = pd.to_datetime(merged[event_col])

    delta = (merged[date_col].dt.year - merged[event_col].dt.year) * 12 + (
        merged[date_col].dt.month - merged[event_col].dt.month
    )
    merged["months_to_event"] = delta.astype("Float64")
    return merged


def cohort_bands(
    panel: pd.DataFrame,
    *,
    value_col: str = "dd",
    group_col: str = "cohort",
    month_col: str = "months_to_event",
    lower_q: float = 0.25,
    upper_q: float = 0.75,
) -> pd.DataFrame:
    """
    Median and interquartile band per cohort per event month.

    `n` is returned for every cell. A band whose `n` collapses toward the edges
    of the window is not evidence about firms; it is evidence about who is
    still in the sample, and the chart must show that.
    """
    if panel.empty:
        return pd.DataFrame(columns=[group_col, month_col, "n", "median",
                                     "q_low", "q_high", "mean"])

    working = panel[[group_col, month_col, value_col]].dropna(
        subset=[month_col, value_col]
    )
    if working.empty:
        return pd.DataFrame(columns=[group_col, month_col, "n", "median",
                                     "q_low", "q_high", "mean"])

    grouped = working.groupby([group_col, month_col])[value_col]
    out = grouped.agg(
        n="size",
        median="median",
        mean="mean",
        q_low=lambda s: s.quantile(lower_q),
        q_high=lambda s: s.quantile(upper_q),
    ).reset_index()
    return out.sort_values([group_col, month_col]).reset_index(drop=True)


def balanced_panel(
    panel: pd.DataFrame,
    *,
    firm_col: str = "cik",
    month_col: str = "months_to_event",
    value_col: str = "dd",
    first_month: int = -36,
    last_month: int = 0,
    min_coverage: float = 1.0,
) -> pd.DataFrame:
    """
    Keep only firms observed across the whole window.

    The balanced variant removes composition drift entirely, at the cost of
    sample size. Publishing both, with the N of each, lets a reader see whether
    any separation depends on which firms are present when.

    `min_coverage` of 1.0 demands every month; 0.8 allows a fifth missing.
    """
    if panel.empty:
        return panel

    window = panel[
        (panel[month_col] >= first_month) & (panel[month_col] <= last_month)
    ].dropna(subset=[value_col])
    if window.empty:
        return window

    required = int(round((last_month - first_month + 1) * min_coverage))
    counts = window.groupby(firm_col)[month_col].nunique()
    keep = counts[counts >= required].index
    return window[window[firm_col].isin(keep)].copy()


def composition_table(
    panel: pd.DataFrame,
    *,
    firm_col: str = "cik",
    group_col: str = "cohort",
    month_col: str = "months_to_event",
    value_col: str = "dd",
) -> pd.DataFrame:
    """
    Firms contributing at each event month, per cohort.

    Published alongside every event-time chart. If the treatment line rises
    near t=0 while its `n` halves, the rise may be survivorship within the
    window rather than anything about credit risk.
    """
    if panel.empty:
        return pd.DataFrame(columns=[group_col, month_col, "n_firms"])
    working = panel.dropna(subset=[month_col, value_col])
    out = working.groupby([group_col, month_col])[firm_col].nunique().reset_index()
    return out.rename(columns={firm_col: "n_firms"}).sort_values(
        [group_col, month_col]
    ).reset_index(drop=True)


def difference_in_medians(
    panel: pd.DataFrame,
    *,
    value_col: str = "dd",
    group_col: str = "cohort",
    month_col: str = "months_to_event",
    treatment_label: str = "treatment",
    control_label: str = "control",
    n_bootstrap: int = 2000,
    seed: int = 20260819,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """
    Treatment-minus-control median gap per event month, with a bootstrap band.

    Resamples FIRMS within each cohort, for the same reason the AUC bootstrap
    does: a firm's consecutive months are not independent observations.
    """
    if panel.empty:
        return pd.DataFrame()

    working = panel.dropna(subset=[month_col, value_col])
    rng = np.random.default_rng(seed)
    rows = []

    for month, chunk in working.groupby(month_col):
        treat = chunk[chunk[group_col] == treatment_label]
        control = chunk[chunk[group_col] == control_label]
        if treat.empty or control.empty:
            continue

        point = float(treat[value_col].median() - control[value_col].median())
        treat_values = treat[value_col].to_numpy(dtype=float)
        control_values = control[value_col].to_numpy(dtype=float)

        draws = np.empty(n_bootstrap, dtype=float)
        for b in range(n_bootstrap):
            a = rng.choice(treat_values, size=treat_values.size, replace=True)
            c = rng.choice(control_values, size=control_values.size, replace=True)
            draws[b] = np.median(a) - np.median(c)

        low, high = np.percentile(draws, [100 * alpha / 2, 100 * (1 - alpha / 2)])
        rows.append({
            month_col: month,
            "n_treatment": int(treat_values.size),
            "n_control": int(control_values.size),
            "median_gap": point,
            "ci_low": float(low),
            "ci_high": float(high),
            "excludes_zero": bool(low > 0 or high < 0),
        })

    return pd.DataFrame(rows).sort_values(month_col).reset_index(drop=True)
