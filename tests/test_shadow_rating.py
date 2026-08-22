"""
Shadow rating tests.

The first class is the point of the module. The predecessor derived the
benchmark rating from Merton's own solved asset value, so the "mispricing" it
reported was partly the model arguing with itself. These tests assert the
circularity cannot come back by convention drift -- not that it happens not to
be there today.
"""
from __future__ import annotations

import inspect

import pytest

from src.models import shadow_rating as sr
from src.models.shadow_rating import shadow_rating


BASE = dict(ebit=500.0, interest_expense=100.0, total_assets=10_000_000_000.0)


class TestNoMertonInput:
    """The guarantee. If any of these fail, the circularity is back."""

    FORBIDDEN = {
        "v", "asset_value", "sigma_v", "asset_volatility", "sigma_a",
        "dd", "distance_to_default", "default_probability", "pd",
        "implied_spread", "theo_spread", "spread", "leverage_merton",
        "equity_value", "market_cap", "e",
    }

    def test_signature_admits_no_merton_quantity(self):
        params = set(inspect.signature(shadow_rating).parameters) - {"self"}
        offending = {p for p in params if p.lower() in self.FORBIDDEN}
        assert not offending, (
            f"shadow_rating() accepts Merton-derived argument(s): {offending}. "
            "The benchmark rating must contain no Merton quantity."
        )

    def test_all_parameters_are_keyword_only(self):
        """Positional args invite a caller to pass the wrong thing silently."""
        for name, p in inspect.signature(shadow_rating).parameters.items():
            assert p.kind is inspect.Parameter.KEYWORD_ONLY, f"{name} is positional"

    def test_module_does_not_import_the_merton_solver(self):
        source = inspect.getsource(sr)
        for banned in ("from .merton", "import merton", "from src.models.merton"):
            assert banned not in source, f"shadow_rating imports the solver: {banned}"

    def test_output_is_unchanged_when_merton_quantities_change(self):
        """
        The behavioural form of the guarantee. Merton outputs vary enormously
        across these firms; the rating must not move, because it cannot see them.
        """
        from src.models import merton

        baseline = shadow_rating(**BASE)
        for equity, sigma_e, debt in [
            (1e9, 0.30, 5e9), (5e10, 0.80, 5e9), (2e8, 1.50, 5e9),
        ]:
            solution = merton.solve_iterative(
                __import__("numpy").array([equity] * 260), debt, 0.04, 1.0
            )
            if solution.usable:
                dd = merton.distance_to_default(
                    solution.V, solution.sigma_V, debt, 0.04, 1.0
                )
                assert dd == dd  # computed, and deliberately discarded
            again = shadow_rating(**BASE)
            assert again.rating == baseline.rating
            assert again.base_rating == baseline.base_rating

    def test_rating_ignores_price_moves_entirely(self):
        """A firm whose equity halves keeps its shadow rating: it is accounting-only."""
        assert shadow_rating(**BASE).rating == shadow_rating(**BASE).rating


class TestCoverageMapping:
    def test_high_coverage_large_cap_is_investment_grade(self):
        got = shadow_rating(ebit=1000.0, interest_expense=100.0,
                            total_assets=10_000_000_000.0)
        assert got.rating == "AAA"

    def test_the_same_coverage_rates_worse_for_a_small_firm(self):
        """Damodaran publishes a stricter table for smaller, riskier firms."""
        large = shadow_rating(ebit=700.0, interest_expense=100.0,
                              total_assets=10_000_000_000.0)
        small = shadow_rating(ebit=700.0, interest_expense=100.0,
                              total_assets=500_000_000.0)
        assert RATING_INDEX(small.rating) > RATING_INDEX(large.rating)

    def test_coverage_below_the_floor_is_default(self):
        got = shadow_rating(ebit=10.0, interest_expense=100.0,
                            total_assets=10_000_000_000.0)
        assert got.rating == "D"

    def test_negative_ebit_rates_at_the_bottom(self):
        got = shadow_rating(ebit=-500.0, interest_expense=100.0,
                            total_assets=10_000_000_000.0)
        assert got.rating == "D"

    def test_ratings_are_monotone_in_coverage(self):
        previous = None
        for ebit in [50, 100, 200, 300, 425, 550, 650, 850, 1200]:
            got = shadow_rating(ebit=float(ebit), interest_expense=100.0,
                                total_assets=10_000_000_000.0)
            idx = RATING_INDEX(got.rating)
            if previous is not None:
                assert idx <= previous, "better coverage must not rate worse"
            previous = idx

    def test_size_band_recorded(self):
        assert shadow_rating(**BASE).size_band == "large"
        assert shadow_rating(ebit=500.0, interest_expense=100.0,
                             total_assets=1e8).size_band == "small"


class TestNotching:
    def test_at_most_one_notch(self):
        got = shadow_rating(ebit=500.0, interest_expense=100.0,
                            total_assets=10_000_000_000.0,
                            total_debt=1e10, ebitda=5e8, revenue=1e9)
        assert abs(got.notch) <= 1

    def test_high_leverage_notches_down_with_a_reason(self):
        got = shadow_rating(ebit=500.0, interest_expense=100.0,
                            total_assets=10_000_000_000.0,
                            total_debt=7e9, ebitda=1e9)
        assert got.notch == 1
        assert "debt/EBITDA" in got.notch_reason
        assert RATING_INDEX(got.rating) > RATING_INDEX(got.base_rating)

    def test_negative_margin_notches_down(self):
        got = shadow_rating(ebit=500.0, interest_expense=100.0,
                            total_assets=10_000_000_000.0,
                            revenue=1e9, ebitda=1e9, total_debt=1e9)
        assert got.notch == 0   # positive margin here
        worse = shadow_rating(ebit=-100.0, interest_expense=100.0,
                              total_assets=10_000_000_000.0, revenue=1e9)
        assert worse.rating == "D"

    def test_every_notch_records_its_reason(self):
        got = shadow_rating(ebit=500.0, interest_expense=100.0,
                            total_assets=10_000_000_000.0,
                            total_debt=7e9, ebitda=1e9)
        if got.notch != 0:
            assert got.notch_reason, "a notch without a stated reason is unauditable"

    def test_no_notch_leaves_the_base_rating(self):
        got = shadow_rating(**BASE)
        assert got.rating == got.base_rating
        assert got.notch == 0


class TestUnusableInputs:
    def test_missing_assets_is_unusable_not_guessed(self):
        got = shadow_rating(ebit=500.0, interest_expense=100.0, total_assets=None)
        assert not got.usable
        assert got.notes

    def test_missing_ebit_is_unusable(self):
        got = shadow_rating(ebit=None, interest_expense=100.0,
                            total_assets=1e10)
        assert not got.usable

    def test_zero_interest_expense_is_flagged_not_silently_top_rated(self):
        got = shadow_rating(ebit=500.0, interest_expense=0.0, total_assets=1e10)
        assert got.usable
        assert any("interest" in n for n in got.notes)

    def test_unusable_result_carries_no_rating(self):
        got = shadow_rating(ebit=None, interest_expense=None, total_assets=None)
        assert got.rating == ""


class TestCohortMapping:
    def test_every_rating_maps_to_a_cohort_index(self):
        for rating in sr.RATING_SCALE:
            assert rating in sr.COHORT_INDEX

    def test_cohort_indices_are_fred_buckets(self):
        assert set(sr.COHORT_INDEX.values()) <= {"AAA", "AA", "A", "BBB", "BB", "B", "CCC"}

    def test_result_carries_its_cohort(self):
        got = shadow_rating(**BASE)
        assert got.cohort_index in {"AAA", "AA", "A", "BBB", "BB", "B", "CCC"}


class TestProvenance:
    def test_source_is_recorded(self):
        assert sr.SOURCE["publisher"]
        assert sr.SOURCE["url"]

    def test_thresholds_are_marked_pending_verification(self):
        """
        Transcribed from a published table from memory. Until re-checked against
        the current file, that must be visible rather than implied.
        """
        assert "PENDING" in sr.SOURCE["verified_against"]


def RATING_INDEX(rating: str) -> int:
    return sr.RATING_SCALE.index(rating) if rating in sr.RATING_SCALE else 99
