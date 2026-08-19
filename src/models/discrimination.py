"""
Discriminatory power, base rates, and calibration.

The contribution of this study is not "distance to default falls before
bankruptcies". Anyone can show that on defaulters alone. It is what the model
does on firms that do NOT fail, and what that costs at a realistic base rate.

Three things this module insists on:

1. **AUC, not accuracy.** Accuracy on a sample selected for defaulting is
   meaningless: a model that shorts every firm on earth scores 100%. The
   predecessor hardcoded exactly that (`'100%' if had_warning else '0%'`).

2. **Bootstrap over firms, not firm-months.** Consecutive months of the same
   firm are not independent observations. Resampling months would shrink
   confidence intervals by roughly sqrt(months per firm) and manufacture
   precision that does not exist.

3. **Base-rate adjustment.** A good AUC on a balanced study sample says almost
   nothing about production precision when defaults run 1-2% a year. That gap
   is the most important honest finding the study can report, so it gets a
   first-class function rather than a footnote.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

__all__ = [
    "AUCResult",
    "ConfusionMatrix",
    "auc",
    "auc_with_ci",
    "auc_difference",
    "roc_curve",
    "confusion_at_threshold",
    "base_rate_precision",
    "calibration_table",
    "lead_time_distribution",
]


# --------------------------------------------------------------------------
# AUC
# --------------------------------------------------------------------------

def auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """
    Area under the ROC curve, via the Mann-Whitney U rank statistic.

    `scores` are ordered so that HIGHER means MORE likely to default. Distance
    to default runs the other way, so callers pass -DD. Keeping that inversion
    at the call site rather than hiding it here means the orientation is
    visible in the analysis code where mistakes would be silent.

    Ties contribute 0.5, which is what the rank-based form gives for free.
    """
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels).astype(int)
    mask = np.isfinite(scores)
    scores, labels = scores[mask], labels[mask]

    n_pos = int((labels == 1).sum())
    n_neg = int((labels == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")

    order = np.argsort(scores, kind="mergesort")
    ranked = np.empty(len(scores), dtype=float)
    sorted_scores = scores[order]
    i = 0
    while i < len(sorted_scores):
        j = i
        while j + 1 < len(sorted_scores) and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        ranked[order[i:j + 1]] = 0.5 * (i + j) + 1.0   # average rank for ties
        i = j + 1

    rank_sum_pos = ranked[labels == 1].sum()
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


@dataclass
class AUCResult:
    auc: float
    ci_low: float
    ci_high: float
    n_firms: int
    n_defaults: int
    n_controls: int
    n_bootstrap: int
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __str__(self) -> str:
        return (
            f"AUC {self.auc:.3f} [{self.ci_low:.3f}, {self.ci_high:.3f}] "
            f"(n={self.n_firms}: {self.n_defaults} defaults, "
            f"{self.n_controls} controls)"
        )


def _firm_bootstrap_indices(
    firm_ids: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    """Resample FIRMS with replacement, returning row indices."""
    unique = np.unique(firm_ids)
    drawn = rng.choice(unique, size=len(unique), replace=True)
    lookup: dict = {}
    for firm in unique:
        lookup[firm] = np.flatnonzero(firm_ids == firm)
    return np.concatenate([lookup[firm] for firm in drawn])


def auc_with_ci(
    scores,
    labels,
    firm_ids,
    *,
    n_bootstrap: int = 2000,
    seed: int = 20260819,
    alpha: float = 0.05,
) -> AUCResult:
    """
    AUC with a percentile bootstrap interval, resampling firms.

    One row per firm at a given horizon is the normal input. If a firm appears
    more than once, `firm_ids` keeps its rows together through resampling, so
    the interval reflects the number of independent firms rather than the
    number of rows.
    """
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels).astype(int)
    firm_ids = np.asarray(firm_ids)

    mask = np.isfinite(scores)
    scores, labels, firm_ids = scores[mask], labels[mask], firm_ids[mask]

    point = auc(scores, labels)
    n_firms = len(np.unique(firm_ids))
    n_pos = int((labels == 1).sum())
    n_neg = int((labels == 0).sum())

    if not np.isfinite(point) or n_pos == 0 or n_neg == 0:
        return AUCResult(point, float("nan"), float("nan"), n_firms, n_pos, n_neg,
                         0, ("degenerate sample: one class absent",))

    rng = np.random.default_rng(seed)
    draws = np.empty(n_bootstrap, dtype=float)
    for b in range(n_bootstrap):
        idx = _firm_bootstrap_indices(firm_ids, rng)
        draws[b] = auc(scores[idx], labels[idx])

    usable = draws[np.isfinite(draws)]
    notes: tuple[str, ...] = ()
    if usable.size < n_bootstrap:
        notes = (f"{n_bootstrap - usable.size} bootstrap draws degenerate "
                 "(one class absent) and were dropped",)
    if usable.size == 0:
        return AUCResult(point, float("nan"), float("nan"), n_firms, n_pos, n_neg,
                         0, notes + ("all bootstrap draws degenerate",))

    low, high = np.percentile(usable, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return AUCResult(point, float(low), float(high), n_firms, n_pos, n_neg,
                     int(usable.size), notes)


def auc_difference(
    scores_a,
    scores_b,
    labels,
    firm_ids,
    *,
    n_bootstrap: int = 2000,
    seed: int = 20260819,
    alpha: float = 0.05,
) -> dict:
    """
    Paired bootstrap for the difference between two estimators' AUCs.

    This is the horse race: KMV iterative vs simultaneous vs Bharath & Shumway
    naive, on identical samples. Bharath & Shumway (2008) found the naive
    approximation forecasts default about as well as the full solve. If that
    replicates here, the honest headline is that the machinery buys little.

    PAIRED matters: both estimators are evaluated on the same resampled firms
    each replication, so the interval reflects the difference's uncertainty and
    not the sum of two independent ones, which would be far too wide.
    """
    scores_a = np.asarray(scores_a, dtype=float)
    scores_b = np.asarray(scores_b, dtype=float)
    labels = np.asarray(labels).astype(int)
    firm_ids = np.asarray(firm_ids)

    mask = np.isfinite(scores_a) & np.isfinite(scores_b)
    scores_a, scores_b = scores_a[mask], scores_b[mask]
    labels, firm_ids = labels[mask], firm_ids[mask]

    point_a, point_b = auc(scores_a, labels), auc(scores_b, labels)
    rng = np.random.default_rng(seed)
    deltas = np.empty(n_bootstrap, dtype=float)
    for b in range(n_bootstrap):
        idx = _firm_bootstrap_indices(firm_ids, rng)
        deltas[b] = auc(scores_a[idx], labels[idx]) - auc(scores_b[idx], labels[idx])

    usable = deltas[np.isfinite(deltas)]
    if usable.size == 0:
        return {"auc_a": point_a, "auc_b": point_b, "delta": float("nan"),
                "ci_low": float("nan"), "ci_high": float("nan"),
                "excludes_zero": False, "n_bootstrap": 0,
                "n_compared": int(mask.sum())}

    low, high = np.percentile(usable, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {
        "auc_a": point_a,
        "auc_b": point_b,
        "delta": float(point_a - point_b),
        "ci_low": float(low),
        "ci_high": float(high),
        "excludes_zero": bool(low > 0 or high < 0),
        "n_bootstrap": int(usable.size),
        "n_compared": int(mask.sum()),
    }


def roc_curve(scores, labels) -> pd.DataFrame:
    """ROC points. `scores` oriented so higher means more likely to default."""
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels).astype(int)
    mask = np.isfinite(scores)
    scores, labels = scores[mask], labels[mask]

    n_pos = int((labels == 1).sum())
    n_neg = int((labels == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return pd.DataFrame(columns=["threshold", "tpr", "fpr"])

    order = np.argsort(-scores, kind="mergesort")
    sorted_scores, sorted_labels = scores[order], labels[order]
    tps = np.cumsum(sorted_labels == 1)
    fps = np.cumsum(sorted_labels == 0)

    # One point per distinct threshold value.
    distinct = np.flatnonzero(np.diff(sorted_scores)) if len(sorted_scores) > 1 else []
    keep = np.r_[distinct, len(sorted_scores) - 1].astype(int)

    return pd.DataFrame(
        {
            "threshold": sorted_scores[keep],
            "tpr": tps[keep] / n_pos,
            "fpr": fps[keep] / n_neg,
        }
    )


# --------------------------------------------------------------------------
# Thresholds, base rates
# --------------------------------------------------------------------------

@dataclass
class ConfusionMatrix:
    threshold: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int

    @property
    def tpr(self) -> float:
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom else float("nan")

    @property
    def fpr(self) -> float:
        denom = self.false_positives + self.true_negatives
        return self.false_positives / denom if denom else float("nan")

    @property
    def sample_precision(self) -> float:
        """
        Precision ON THE STUDY SAMPLE.

        Almost always misleadingly high, because the study sample is roughly
        balanced while reality is not. Use `base_rate_precision` for anything
        quoted as a production number.
        """
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom else float("nan")

    def as_dict(self) -> dict:
        return {
            "threshold": self.threshold,
            "tp": self.true_positives, "fp": self.false_positives,
            "tn": self.true_negatives, "fn": self.false_negatives,
            "tpr": self.tpr, "fpr": self.fpr,
            "sample_precision": self.sample_precision,
        }


def confusion_at_threshold(dd_values, labels, threshold: float) -> ConfusionMatrix:
    """
    Confusion matrix for the rule "flag if DD < threshold".

    Takes DISTANCE TO DEFAULT directly (not a flipped score), because that is
    what the interactive slider on /discrimination exposes to the reader, and
    the two should not be able to drift apart.
    """
    dd_values = np.asarray(dd_values, dtype=float)
    labels = np.asarray(labels).astype(int)
    mask = np.isfinite(dd_values)
    dd_values, labels = dd_values[mask], labels[mask]

    flagged = dd_values < threshold
    return ConfusionMatrix(
        threshold=float(threshold),
        true_positives=int(np.sum(flagged & (labels == 1))),
        false_positives=int(np.sum(flagged & (labels == 0))),
        true_negatives=int(np.sum(~flagged & (labels == 0))),
        false_negatives=int(np.sum(~flagged & (labels == 1))),
    )


def base_rate_precision(tpr: float, fpr: float, base_rate: float) -> dict:
    """
    Translate sensitivity and false-positive rate into production precision.

        PPV = (TPR * pi) / (TPR * pi + FPR * (1 - pi))

    THE exhibit of this study. A model with AUC 0.85 can look excellent and
    still be near-useless in production: at a 1.5% annual default rate, a rule
    catching 80% of defaults with a 20% false-positive rate yields precision of
    about 5.7% -- roughly seventeen false alarms per real default.

    Structural credit models are not thereby worthless; they are just not
    standalone alarms. Saying so plainly is the difference between a study and
    a sales pitch.
    """
    if not (0.0 <= base_rate <= 1.0):
        raise ValueError(f"base_rate must be in [0, 1], got {base_rate}")
    if not np.isfinite(tpr) or not np.isfinite(fpr):
        return {"precision": float("nan"), "false_alarms_per_true": float("nan"),
                "base_rate": base_rate, "tpr": tpr, "fpr": fpr,
                "flagged_share": float("nan")}

    true_pos = tpr * base_rate
    false_pos = fpr * (1.0 - base_rate)
    flagged = true_pos + false_pos
    precision = true_pos / flagged if flagged > 0 else float("nan")
    per_true = false_pos / true_pos if true_pos > 0 else float("inf")

    return {
        "base_rate": float(base_rate),
        "tpr": float(tpr),
        "fpr": float(fpr),
        "precision": float(precision),
        "false_alarms_per_true": float(per_true),
        "flagged_share": float(flagged),
    }


# --------------------------------------------------------------------------
# Calibration
# --------------------------------------------------------------------------

def calibration_table(predicted_pd, labels, *, n_bins: int = 10) -> pd.DataFrame:
    """
    Predicted probability against realised default frequency, by decile.

    Structural models are known to be ordinally informative but badly
    calibrated in levels, typically understating short-horizon PD by an order
    of magnitude. Demonstrating that on this study's own data is a result, not
    an embarrassment -- and it is why the site reports PD as a ranking rather
    than a probability.
    """
    predicted_pd = np.asarray(predicted_pd, dtype=float)
    labels = np.asarray(labels).astype(int)
    mask = np.isfinite(predicted_pd)
    predicted_pd, labels = predicted_pd[mask], labels[mask]
    if predicted_pd.size == 0:
        return pd.DataFrame(columns=["bin", "n", "mean_predicted_pd",
                                     "realised_default_rate", "ratio"])

    frame = pd.DataFrame({"pd": predicted_pd, "label": labels})
    try:
        frame["bin"] = pd.qcut(frame["pd"], n_bins, labels=False, duplicates="drop")
    except ValueError:
        frame["bin"] = 0

    grouped = frame.groupby("bin", observed=True).agg(
        n=("label", "size"),
        mean_predicted_pd=("pd", "mean"),
        realised_default_rate=("label", "mean"),
    ).reset_index()
    grouped["ratio"] = grouped["realised_default_rate"] / grouped["mean_predicted_pd"].replace(0, np.nan)
    return grouped


# --------------------------------------------------------------------------
# Lead time
# --------------------------------------------------------------------------

def lead_time_distribution(panel: pd.DataFrame, threshold: float, *,
                           firm_col: str = "cik",
                           month_col: str = "months_to_event",
                           dd_col: str = "dd") -> pd.DataFrame:
    """
    Months between the FIRST breach of a DD threshold and the event.

    Replaces the single fabricated "3.4 months average lead time" with a
    distribution, and reports it CONDITIONAL ON DETECTION -- firms never
    flagged have no lead time, and averaging them in as zero would flatter the
    model while averaging them out inflates the mean. Both counts are returned
    so the reader can see the conditioning.

    `months_to_event` is negative before the event (t-36 .. 0).
    """
    if panel.empty:
        return pd.DataFrame(columns=[firm_col, "lead_months", "detected"])

    rows = []
    for firm, group in panel.groupby(firm_col):
        group = group.sort_values(month_col)
        breaches = group[(group[dd_col] < threshold) & group[dd_col].notna()]
        if breaches.empty:
            rows.append({firm_col: firm, "lead_months": np.nan, "detected": False})
        else:
            first = breaches.iloc[0][month_col]
            rows.append({firm_col: firm, "lead_months": abs(float(first)),
                         "detected": True})
    return pd.DataFrame(rows)
