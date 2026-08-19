"""
Discrimination tests: known-answer checks against analytical results, not
just "it runs".
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.models import discrimination as disc


class TestAUC:
    def test_perfect_separation_is_one(self):
        scores = np.array([1.0, 2.0, 3.0, 10.0, 11.0, 12.0])
        labels = np.array([0, 0, 0, 1, 1, 1])
        assert disc.auc(scores, labels) == pytest.approx(1.0)

    def test_reversed_separation_is_zero(self):
        scores = np.array([10.0, 11.0, 12.0, 1.0, 2.0, 3.0])
        labels = np.array([0, 0, 0, 1, 1, 1])
        assert disc.auc(scores, labels) == pytest.approx(0.0)

    def test_all_ties_is_one_half(self):
        scores = np.ones(10)
        labels = np.array([0, 1] * 5)
        assert disc.auc(scores, labels) == pytest.approx(0.5)

    def test_matches_hand_computed_value(self):
        """
        pos={2,4}, neg={1,3}. Pairs: (2>1)=1 (2<3)=0 (4>1)=1 (4>3)=1 -> 3/4.
        """
        scores = np.array([1.0, 2.0, 3.0, 4.0])
        labels = np.array([0, 1, 0, 1])
        assert disc.auc(scores, labels) == pytest.approx(0.75)

    def test_half_credit_for_ties(self):
        """pos={2}, neg={1,2}: (2>1)=1, (2==2)=0.5 -> 0.75."""
        scores = np.array([1.0, 2.0, 2.0])
        labels = np.array([0, 0, 1])
        assert disc.auc(scores, labels) == pytest.approx(0.75)

    def test_single_class_returns_nan(self):
        assert np.isnan(disc.auc(np.array([1.0, 2.0]), np.array([1, 1])))

    def test_nan_scores_are_dropped_not_imputed(self):
        scores = np.array([1.0, np.nan, 3.0, 10.0])
        labels = np.array([0, 1, 0, 1])
        assert disc.auc(scores, labels) == pytest.approx(1.0)

    def test_agrees_with_sklearn(self):
        sklearn_metrics = pytest.importorskip("sklearn.metrics")
        rng = np.random.default_rng(0)
        for _ in range(5):
            scores = rng.normal(size=200)
            labels = (rng.random(200) < 0.3).astype(int)
            assert disc.auc(scores, labels) == pytest.approx(
                sklearn_metrics.roc_auc_score(labels, scores), abs=1e-12
            )


class TestBootstrap:
    def _sample(self, n=120, seed=1):
        rng = np.random.default_rng(seed)
        labels = np.r_[np.ones(n // 2), np.zeros(n // 2)].astype(int)
        scores = np.r_[rng.normal(1.0, 1.0, n // 2), rng.normal(0.0, 1.0, n // 2)]
        firms = np.arange(n)
        return scores, labels, firms

    def test_interval_contains_point_estimate(self):
        scores, labels, firms = self._sample()
        got = disc.auc_with_ci(scores, labels, firms, n_bootstrap=300)
        assert got.ci_low <= got.auc <= got.ci_high

    def test_is_deterministic_for_a_given_seed(self):
        scores, labels, firms = self._sample()
        a = disc.auc_with_ci(scores, labels, firms, n_bootstrap=200, seed=42)
        b = disc.auc_with_ci(scores, labels, firms, n_bootstrap=200, seed=42)
        assert (a.auc, a.ci_low, a.ci_high) == (b.auc, b.ci_low, b.ci_high)

    def test_larger_samples_give_tighter_intervals(self):
        narrow = disc.auc_with_ci(*self._sample(600, seed=3), n_bootstrap=300)
        wide = disc.auc_with_ci(*self._sample(60, seed=3), n_bootstrap=300)
        assert (narrow.ci_high - narrow.ci_low) < (wide.ci_high - wide.ci_low)

    def test_clustering_by_firm_widens_the_interval(self):
        """
        The reason bootstrapping over firms matters. Twelve firms observed 10
        times each carry the information of 12 firms, not 120 observations.
        Resampling rows would understate the interval.
        """
        rng = np.random.default_rng(5)
        n_firms, per_firm = 12, 10
        firm_effect = rng.normal(0, 1.2, n_firms)
        labels_by_firm = np.r_[np.ones(n_firms // 2), np.zeros(n_firms // 2)].astype(int)

        scores, labels, firms, rows = [], [], [], []
        for f in range(n_firms):
            base = firm_effect[f] + (1.0 if labels_by_firm[f] else 0.0)
            for _ in range(per_firm):
                scores.append(base + rng.normal(0, 0.05))
                labels.append(labels_by_firm[f])
                firms.append(f)
                rows.append(len(rows))

        clustered = disc.auc_with_ci(scores, labels, firms, n_bootstrap=400, seed=7)
        by_row = disc.auc_with_ci(scores, labels, rows, n_bootstrap=400, seed=7)
        assert (clustered.ci_high - clustered.ci_low) > (by_row.ci_high - by_row.ci_low)

    def test_degenerate_sample_reports_rather_than_raises(self):
        got = disc.auc_with_ci([1.0, 2.0], [1, 1], [0, 1], n_bootstrap=10)
        assert np.isnan(got.auc)
        assert got.notes


class TestAUCDifference:
    def test_identical_estimators_give_zero_delta(self):
        rng = np.random.default_rng(2)
        scores = rng.normal(size=100)
        labels = (rng.random(100) < 0.5).astype(int)
        firms = np.arange(100)
        got = disc.auc_difference(scores, scores, labels, firms, n_bootstrap=200)
        assert got["delta"] == pytest.approx(0.0)
        assert not got["excludes_zero"]

    def test_detects_a_genuinely_better_estimator(self):
        rng = np.random.default_rng(4)
        n = 300
        labels = np.r_[np.ones(n // 2), np.zeros(n // 2)].astype(int)
        signal = np.r_[rng.normal(2.0, 1.0, n // 2), rng.normal(0.0, 1.0, n // 2)]
        noise = rng.normal(size=n)
        got = disc.auc_difference(signal, noise, labels, np.arange(n), n_bootstrap=300)
        assert got["delta"] > 0
        assert got["excludes_zero"]

    def test_paired_interval_is_narrower_than_naive_sum(self):
        """Pairing is the point: shared firms cancel much of the variance."""
        rng = np.random.default_rng(6)
        n = 200
        labels = np.r_[np.ones(n // 2), np.zeros(n // 2)].astype(int)
        base = np.r_[rng.normal(1.0, 1.0, n // 2), rng.normal(0.0, 1.0, n // 2)]
        a = base + rng.normal(0, 0.01, n)     # near-identical estimators
        b = base + rng.normal(0, 0.01, n)
        firms = np.arange(n)

        paired = disc.auc_difference(a, b, labels, firms, n_bootstrap=300)
        width = paired["ci_high"] - paired["ci_low"]

        ci_a = disc.auc_with_ci(a, labels, firms, n_bootstrap=300)
        ci_b = disc.auc_with_ci(b, labels, firms, n_bootstrap=300)
        naive = (ci_a.ci_high - ci_a.ci_low) + (ci_b.ci_high - ci_b.ci_low)
        assert width < naive


class TestConfusion:
    def test_counts_are_correct(self):
        dd = np.array([0.5, 1.0, 3.0, 4.0])
        labels = np.array([1, 1, 0, 0])
        got = disc.confusion_at_threshold(dd, labels, 2.0)
        assert (got.true_positives, got.false_positives) == (2, 0)
        assert (got.true_negatives, got.false_negatives) == (2, 0)
        assert got.tpr == pytest.approx(1.0)
        assert got.fpr == pytest.approx(0.0)

    def test_lower_threshold_flags_fewer(self):
        dd = np.array([0.5, 1.5, 2.5, 3.5])
        labels = np.array([1, 1, 0, 0])
        strict = disc.confusion_at_threshold(dd, labels, 1.0)
        loose = disc.confusion_at_threshold(dd, labels, 3.0)
        assert strict.true_positives + strict.false_positives < \
               loose.true_positives + loose.false_positives

    def test_flags_below_threshold_not_above(self):
        """DD is a distance: LOW means distressed."""
        dd = np.array([0.1, 9.0])
        labels = np.array([1, 0])
        got = disc.confusion_at_threshold(dd, labels, 1.0)
        assert got.true_positives == 1 and got.false_positives == 0


class TestBaseRate:
    def test_the_headline_arithmetic(self):
        """
        TPR 0.80, FPR 0.20, base rate 1.5%:
          TP = .8*.015 = .012 ; FP = .2*.985 = .197 ; PPV = .012/.209 = 5.7%
        """
        got = disc.base_rate_precision(0.80, 0.20, 0.015)
        assert got["precision"] == pytest.approx(0.0574, abs=5e-4)
        assert got["false_alarms_per_true"] == pytest.approx(16.42, abs=0.05)

    def test_balanced_sample_precision_is_much_higher(self):
        """Why sample precision must never be quoted as a production number."""
        production = disc.base_rate_precision(0.80, 0.20, 0.015)["precision"]
        balanced = disc.base_rate_precision(0.80, 0.20, 0.50)["precision"]
        assert balanced > production * 10

    def test_precision_rises_with_base_rate(self):
        values = [disc.base_rate_precision(0.8, 0.2, pi)["precision"]
                  for pi in (0.002, 0.01, 0.05, 0.20)]
        assert values == sorted(values)

    def test_perfect_specificity_gives_perfect_precision(self):
        assert disc.base_rate_precision(0.5, 0.0, 0.01)["precision"] == pytest.approx(1.0)

    def test_rejects_impossible_base_rate(self):
        with pytest.raises(ValueError):
            disc.base_rate_precision(0.8, 0.2, 1.5)


class TestCalibration:
    def test_perfectly_calibrated_model_has_ratio_near_one(self):
        rng = np.random.default_rng(8)
        predicted = rng.uniform(0.01, 0.9, 4000)
        labels = (rng.random(4000) < predicted).astype(int)
        table = disc.calibration_table(predicted, labels)
        assert table["ratio"].between(0.6, 1.6).mean() > 0.7

    def test_detects_systematic_understatement(self):
        """The known structural-model failure: PD too low in levels."""
        rng = np.random.default_rng(9)
        predicted = rng.uniform(0.001, 0.02, 3000)
        labels = (rng.random(3000) < predicted * 10).astype(int)
        table = disc.calibration_table(predicted, labels)
        assert table["ratio"].median() > 4

    def test_handles_empty(self):
        assert disc.calibration_table(np.array([]), np.array([])).empty


class TestLeadTime:
    def _panel(self):
        return pd.DataFrame({
            "cik": ["A"] * 4 + ["B"] * 4 + ["C"] * 4,
            "months_to_event": [-36, -24, -12, 0] * 3,
            # A breaches at -24, B only at 0, C never
            "dd": [5.0, 1.0, 0.5, 0.1,
                   6.0, 5.0, 4.0, 0.5,
                   8.0, 7.0, 7.5, 6.0],
        })

    def test_takes_the_first_breach(self):
        got = disc.lead_time_distribution(self._panel(), threshold=2.0)
        assert float(got.loc[got.cik == "A", "lead_months"].iloc[0]) == 24.0

    def test_late_breach_gives_short_lead(self):
        got = disc.lead_time_distribution(self._panel(), threshold=2.0)
        assert float(got.loc[got.cik == "B", "lead_months"].iloc[0]) == 0.0

    def test_undetected_firm_is_flagged_not_zeroed(self):
        """
        Recording a miss as zero lead time would flatter the model; dropping it
        silently would too. It is marked undetected so the conditioning shows.
        """
        got = disc.lead_time_distribution(self._panel(), threshold=2.0)
        row = got.loc[got.cik == "C"].iloc[0]
        assert row["detected"] is False or row["detected"] == False  # noqa: E712
        assert np.isnan(row["lead_months"])

    def test_empty_panel(self):
        assert disc.lead_time_distribution(pd.DataFrame(), 2.0).empty


class TestROCCurve:
    def test_is_monotone(self):
        rng = np.random.default_rng(10)
        scores = rng.normal(size=200)
        labels = (rng.random(200) < 0.4).astype(int)
        curve = disc.roc_curve(scores, labels)
        assert curve["tpr"].is_monotonic_increasing
        assert curve["fpr"].is_monotonic_increasing

    def test_area_under_curve_matches_auc(self):
        rng = np.random.default_rng(12)
        n = 400
        labels = np.r_[np.ones(n // 2), np.zeros(n // 2)].astype(int)
        scores = np.r_[rng.normal(1, 1, n // 2), rng.normal(0, 1, n // 2)]
        curve = disc.roc_curve(scores, labels)
        area = np.trapezoid(
            np.r_[0, curve["tpr"].to_numpy()], np.r_[0, curve["fpr"].to_numpy()]
        )
        assert area == pytest.approx(disc.auc(scores, labels), abs=0.01)
