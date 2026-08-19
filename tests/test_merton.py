"""
Merton engine tests.

These check analytical properties that must hold regardless of implementation
(round-tripping, monotonicity, limiting cases), not merely that functions run.
"""
from __future__ import annotations

import numpy as np
import pytest

from src.models import merton


R = 0.04
T = 1.0


class TestCallRelation:
    def test_deep_in_the_money_equity_approaches_v_minus_pv_debt(self):
        """With tiny leverage and low vol, equity -> V - D e^{-rT}."""
        V, D, sigma = 1000.0, 1.0, 0.05
        got = merton.equity_from_assets(V, D, R, T, sigma)
        assert got == pytest.approx(V - D * np.exp(-R * T), rel=1e-6)

    def test_equity_increases_with_asset_value(self):
        vals = [merton.equity_from_assets(v, 100.0, R, T, 0.3)
                for v in (80, 100, 120, 200)]
        assert vals == sorted(vals)

    def test_equity_increases_with_volatility(self):
        """Equity is a call: more asset vol is worth more to shareholders."""
        vals = [merton.equity_from_assets(100.0, 100.0, R, T, s)
                for s in (0.1, 0.2, 0.4, 0.8)]
        assert vals == sorted(vals)


class TestInversionRoundTrip:
    @pytest.mark.parametrize("V,D,sigma", [
        (150.0, 100.0, 0.25),
        (1000.0, 400.0, 0.15),
        (105.0, 100.0, 0.60),   # distressed
        (5000.0, 50.0, 0.30),   # near-unlevered
    ])
    def test_invert_call_recovers_v(self, V, D, sigma):
        E = merton.equity_from_assets(V, D, R, T, sigma)
        recovered = merton._invert_call(E, D, R, T, sigma)
        assert recovered == pytest.approx(V, rel=1e-6)


class TestDistanceToDefault:
    def test_dd_falls_as_leverage_rises(self):
        dds = [merton.distance_to_default(200.0, 0.3, d, R, T)
               for d in (50, 100, 150, 190)]
        assert dds == sorted(dds, reverse=True)

    def test_dd_falls_as_volatility_rises(self):
        dds = [merton.distance_to_default(150.0, s, 100.0, R, T)
               for s in (0.1, 0.2, 0.4, 0.8)]
        assert dds == sorted(dds, reverse=True)

    def test_dd_is_nan_on_degenerate_inputs(self):
        assert np.isnan(merton.distance_to_default(0.0, 0.3, 100.0, R, T))
        assert np.isnan(merton.distance_to_default(150.0, 0.0, 100.0, R, T))
        assert np.isnan(merton.distance_to_default(150.0, 0.3, 0.0, R, T))

    def test_pd_is_monotone_decreasing_in_dd(self):
        pds = [merton.default_probability(dd) for dd in (-2, -1, 0, 1, 2, 5)]
        assert pds == sorted(pds, reverse=True)

    def test_pd_at_zero_dd_is_one_half(self):
        assert merton.default_probability(0.0) == pytest.approx(0.5)


class TestCreditSpread:
    def test_spread_rises_as_dd_falls(self):
        spreads = [merton.credit_spread(dd, T) for dd in (5, 3, 2, 1, 0)]
        assert spreads == sorted(spreads)

    def test_safe_firm_has_near_zero_spread(self):
        assert merton.credit_spread(8.0, T) < 1.0  # bps

    def test_higher_recovery_lowers_spread(self):
        low = merton.credit_spread(1.0, T, recovery_rate=0.2)
        high = merton.credit_spread(1.0, T, recovery_rate=0.8)
        assert high < low


class TestSimultaneousSolver:
    @pytest.mark.parametrize("V,D,sigma_V", [
        (150.0, 100.0, 0.25),
        (1_000.0, 500.0, 0.20),
        (120.0, 100.0, 0.45),
    ])
    def test_recovers_known_inputs(self, V, D, sigma_V):
        """Generate E and sigma_E from known truth, then solve back to it."""
        E = merton.equity_from_assets(V, D, R, T, sigma_V)
        d1, _ = merton._d1_d2(V, D, R, T, sigma_V)
        from scipy.stats import norm
        sigma_E = (V / E) * norm.cdf(d1) * sigma_V

        sol = merton.solve_simultaneous(E, sigma_E, D, R, T)
        assert sol.usable
        assert sol.V == pytest.approx(V, rel=1e-3)
        assert sol.sigma_V == pytest.approx(sigma_V, rel=1e-3)

    def test_invalid_inputs_return_unusable_not_exception(self):
        for args in [(0.0, 0.3, 100.0, R, T), (100.0, 0.0, 100.0, R, T),
                     (100.0, 0.3, 0.0, R, T), (np.nan, 0.3, 100.0, R, T)]:
            sol = merton.solve_simultaneous(*args)
            assert not sol.usable

    def test_never_silently_substitutes_a_fallback_value(self):
        """
        The predecessor returned a naive fallback labelled as a solve.
        A failed solve must report converged=False, not a plausible number.
        """
        sol = merton.solve_simultaneous(np.nan, 0.3, 100.0, R, T)
        assert sol.converged is False
        assert np.isnan(sol.V)


class TestIterativeSolver:
    def _equity_path(self, V0, D, sigma_V, n=260, seed=7):
        """Simulate a GBM asset path, convert to observed equity."""
        rng = np.random.default_rng(seed)
        dt = 1.0 / 252
        shocks = rng.normal((R - 0.5 * sigma_V**2) * dt,
                            sigma_V * np.sqrt(dt), size=n)
        path = V0 * np.exp(np.cumsum(shocks))
        return np.array([merton.equity_from_assets(v, D, R, T, sigma_V) for v in path])

    def test_recovers_asset_volatility_from_simulated_path(self):
        V0, D, sigma_V = 200.0, 100.0, 0.30
        equity = self._equity_path(V0, D, sigma_V)
        sol = merton.solve_iterative(equity, D, R, T)
        assert sol.usable
        # Sampling error on 260 draws is real; 25% tolerance is honest.
        assert sol.sigma_V == pytest.approx(sigma_V, rel=0.25)

    def test_recovers_asset_value_at_observation_date(self):
        V0, D, sigma_V = 200.0, 100.0, 0.30
        equity = self._equity_path(V0, D, sigma_V)
        sol = merton.solve_iterative(equity, D, R, T)
        implied_equity = merton.equity_from_assets(sol.V, D, R, T, sol.sigma_V)
        assert implied_equity == pytest.approx(equity[-1], rel=1e-4)

    def test_is_deterministic(self):
        equity = self._equity_path(200.0, 100.0, 0.30)
        a = merton.solve_iterative(equity, 100.0, R, T)
        b = merton.solve_iterative(equity, 100.0, R, T)
        assert (a.V, a.sigma_V, a.iterations) == (b.V, b.sigma_V, b.iterations)

    def test_short_series_is_rejected_not_guessed(self):
        sol = merton.solve_iterative(np.full(10, 100.0), 100.0, R, T)
        assert not sol.usable
        assert "insufficient" in " ".join(sol.notes)

    def test_flat_equity_series_rejected(self):
        sol = merton.solve_iterative(np.full(200, 100.0), 100.0, R, T)
        assert not sol.usable


class TestNaiveEstimator:
    def test_matches_published_formula(self):
        E, sigma_E, D = 100.0, 0.40, 50.0
        sol = merton.naive_dd(E, sigma_E, D, 0.0)
        expected_sigma_debt = 0.05 + 0.25 * sigma_E
        expected = (E * sigma_E + D * expected_sigma_debt) / (E + D)
        assert sol.V == pytest.approx(E + D)
        assert sol.sigma_V == pytest.approx(expected)

    def test_always_converges(self):
        assert merton.naive_dd(100.0, 0.4, 50.0, 0.0).converged

    def test_orders_firms_the_same_way_as_leverage(self):
        dds = []
        for D in (10.0, 50.0, 150.0, 400.0):
            sol = merton.naive_dd(100.0, 0.4, D, 0.0)
            dds.append(merton.distance_to_default(sol.V, sol.sigma_V, D, R, T))
        assert dds == sorted(dds, reverse=True)
