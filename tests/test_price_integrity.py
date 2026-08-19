"""
Price-series integrity tests, on synthetic series so they run offline.

Each case is modelled on a real series inspected in Phase 0. The shapes are
reproduced from the actual data; see docs/PHASE0_DATA_INVENTORY.md section 1.2.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data import prices


def _series(values, start="2021-01-01", freq="B") -> pd.Series:
    idx = pd.date_range(start, periods=len(values), freq=freq)
    return pd.Series(np.asarray(values, dtype=float), index=idx)


EVENT = "2023-04-23"


def _ramp(a, b, n):
    return list(np.linspace(a, b, n))


class TestRecycledTickerRejection:
    def test_rejects_series_that_recovers_after_the_event(self):
        """The BBBY shape: collapse, then a *different* company's prices."""
        pre = _ramp(30.0, 18.0, 600)      # decline into the filing
        post = _ramp(20.0, 36.0, 700)     # Beyond, Inc. -- rises afterwards
        closes = _series(pre + post)
        event = closes.index[600]
        report = prices.validate_delisted_series(closes, event)
        assert not report.passed
        assert any("recycled" in f or "not distressed" in f for f in report.failures)

    def test_rejects_when_series_starts_after_the_event(self):
        """The SBNY shape: ticker reissued to a new company post-seizure."""
        closes = _series(_ramp(20.0, 25.0, 300), start="2024-08-01")
        report = prices.validate_delisted_series(closes, "2023-03-12")
        assert not report.passed
        assert any("before the event" in f for f in report.failures)

    def test_rejects_a_healthy_survivor(self):
        """A firm that never defaulted must not validate as a defaulter."""
        closes = _series(_ramp(100.0, 180.0, 900))
        event = closes.index[500]
        report = prices.validate_delisted_series(closes, event)
        assert not report.passed


class TestGenuineDistressAccepted:
    def test_accepts_collapse_to_a_worthless_stub(self):
        """
        The FRCB shape: $122 -> $3.51 at seizure -> $0.0006, still quoted.

        Continued quotation must NOT be treated as recycling; delisted equity
        routinely trades as a stub for years.
        """
        pre = _ramp(122.0, 3.5, 600)
        post = [0.0006] * 700
        closes = _series(pre + post)
        event = closes.index[599]   # last pre-event observation
        report = prices.validate_delisted_series(closes, event)
        assert report.passed
        assert any("stub" in f for f in report.flags)

    def test_accepts_series_ending_at_the_event(self):
        closes = _series(_ramp(45.0, 1.2, 500))
        report = prices.validate_delisted_series(closes, closes.index[-1])
        assert report.passed


class TestDeclineRequirement:
    def test_rejects_when_no_material_decline_into_event(self):
        closes = _series(_ramp(100.0, 95.0, 600))
        report = prices.validate_delisted_series(closes, closes.index[-1])
        assert not report.passed
        assert any("below 2y peak" in f for f in report.failures)

    def test_decline_requirement_can_be_relaxed_to_a_flag(self):
        """
        Solvent parents filing about a subsidiary, and prepackaged plans that
        leave equity intact, are real events without an equity collapse. They
        must be adjudicated deliberately rather than silently dropped.
        """
        closes = _series(_ramp(100.0, 95.0, 600))
        report = prices.validate_delisted_series(
            closes, closes.index[-1], require_decline=False
        )
        assert report.passed
        assert any("below 2y peak" in f for f in report.flags)


class TestDegenerate:
    def test_empty_series_fails(self):
        assert not prices.validate_delisted_series(pd.Series(dtype=float), EVENT).passed

    def test_too_few_pre_event_points_fails(self):
        closes = _series(_ramp(50.0, 5.0, 10))
        report = prices.validate_delisted_series(closes, closes.index[-1])
        assert not report.passed
        assert any("pre-event observations" in f for f in report.failures)


class TestRealisedVolatility:
    def test_is_strictly_backward_looking(self):
        """A spike after the as-of date must not affect the estimate."""
        rng = np.random.default_rng(3)
        calm = 100 * np.exp(np.cumsum(rng.normal(0, 0.005, 400)))
        wild = calm[-1] * np.exp(np.cumsum(rng.normal(0, 0.15, 200)))
        closes = _series(list(calm) + list(wild))
        as_of = closes.index[399]

        before = prices.realised_volatility(closes, as_of, 252)
        truncated = prices.realised_volatility(closes.iloc[:400], as_of, 252)
        assert before == pytest.approx(truncated, rel=1e-12)

    def test_detects_a_volatility_increase(self):
        rng = np.random.default_rng(11)
        calm = 100 * np.exp(np.cumsum(rng.normal(0, 0.005, 300)))
        wild = calm[-1] * np.exp(np.cumsum(rng.normal(0, 0.06, 300)))
        closes = _series(list(calm) + list(wild))
        quiet = prices.realised_volatility(closes, closes.index[299], 252)
        loud = prices.realised_volatility(closes, closes.index[-1], 252)
        assert loud > quiet * 3

    def test_returns_nan_when_history_is_too_short(self):
        closes = _series(_ramp(10.0, 12.0, 5))
        assert np.isnan(prices.realised_volatility(closes, closes.index[-1], 252))


class TestMonthly:
    def test_to_monthly_takes_month_end_closes(self):
        closes = _series(_ramp(1.0, 100.0, 400), freq="B")
        monthly = prices.to_monthly(closes)
        assert len(monthly) >= 18
        assert monthly.is_monotonic_increasing

    def test_to_monthly_handles_empty(self):
        assert prices.to_monthly(pd.Series(dtype=float)).empty
