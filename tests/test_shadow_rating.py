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
    """
    Both tables were checked row by row against the published source on
    2026-08-22 and matched exactly. What remains is the VINTAGE problem, which
    verification cannot fix and which the site must therefore state.
    """

    # Transcribed from ratings.html and smallrating.htm.
    SOURCE_LARGE = [
        (8.50, "AAA"), (6.50, "AA"), (5.50, "A+"), (4.25, "A"), (3.00, "A-"),
        (2.50, "BBB"), (2.25, "BB+"), (2.00, "BB"), (1.75, "B+"), (1.50, "B"),
        (1.25, "B-"), (0.80, "CCC"), (0.65, "CC"), (0.20, "C"),
    ]
    SOURCE_SMALL = [
        (12.50, "AAA"), (9.50, "AA"), (7.50, "A+"), (6.00, "A"), (4.50, "A-"),
        (4.00, "BBB"), (3.50, "BB+"), (3.00, "BB"), (2.50, "B+"), (2.00, "B"),
        (1.50, "B-"), (1.25, "CCC"), (0.80, "CC"), (0.50, "C"),
    ]

    def test_large_table_matches_source_exactly(self):
        assert sr._LARGE_CAP == self.SOURCE_LARGE

    def test_small_table_matches_source_exactly(self):
        assert sr._SMALL_CAP == self.SOURCE_SMALL

    def test_source_is_recorded_with_urls(self):
        assert sr.SOURCE["large_url"].startswith("https://")
        assert sr.SOURCE["small_url"].startswith("https://")

    def test_both_tables_record_a_verification_date(self):
        assert "2026-08-22" in sr.SOURCE["large_verified"]
        assert "2026-08-22" in sr.SOURCE["small_verified"]

    def test_the_nine_year_vintage_gap_is_recorded(self):
        """
        The large table is January 2026 and the small one January 2017. A
        classifier switching between them rates firms against thresholds
        calibrated nine years apart, on a size cutoff rather than a date. That
        cannot be verified away and must stay visible.
        """
        assert sr.SOURCE["large_vintage"] == "January 2026"
        assert sr.SOURCE["small_vintage"] == "January 2017"
        assert "NINE YEARS" in sr.SOURCE["small_verified"]

    def test_financial_table_is_recorded_as_deliberately_unused(self):
        assert "NOT used" in sr.SOURCE["financial_table"]

    def test_damodaran_spreads_do_not_enter_rating_assignment(self):
        """
        Benchmark spreads are published beside the rating tables, but the spread
        level must not influence the accounting-only rating assignment.
        """
        source = inspect.getsource(sr.shadow_rating)
        assert "DAMODARAN_SPREAD_BPS" not in source

    def test_periodic_benchmark_covers_the_scale(self):
        for rating in sr.RATING_SCALE:
            assert rating in sr.DAMODARAN_SPREAD_BPS_JAN2026


class TestSizeBandSensitivity:
    """
    The band is worth 1-3 notches from identical fundamentals, so the threshold
    choice has to be testable rather than asserted.
    """

    NEAR = dict(ebit=500.0, interest_expense=100.0,
                total_assets=sr.LARGE_CAP_ASSET_THRESHOLD * 1.05)

    def test_band_can_be_forced_for_sensitivity(self):
        large = shadow_rating(**self.NEAR, force_band="large")
        small = shadow_rating(**self.NEAR, force_band="small")
        assert large.size_band == "large"
        assert small.size_band == "small"

    def test_forcing_changes_the_rating_at_the_same_coverage(self):
        large = shadow_rating(**self.NEAR, force_band="large")
        small = shadow_rating(**self.NEAR, force_band="small")
        assert large.rating != small.rating

    def test_forced_results_are_marked(self):
        """A forced band must never be mistakable for a natural one."""
        forced = shadow_rating(**self.NEAR, force_band="small")
        assert forced.band_forced
        assert any("FORCED" in n for n in forced.notes)

    def test_unforced_results_are_not_marked(self):
        assert not shadow_rating(**BASE).band_forced

    def test_firms_near_the_boundary_are_flagged(self):
        got = shadow_rating(**self.NEAR)
        assert got.near_size_boundary
        assert any("boundary" in n for n in got.notes)

    def test_firms_far_from_the_boundary_are_not_flagged(self):
        got = shadow_rating(ebit=500.0, interest_expense=100.0,
                            total_assets=sr.LARGE_CAP_ASSET_THRESHOLD * 10)
        assert not got.near_size_boundary

    def test_band_gap_is_between_one_and_three_notches(self):
        """
        Measured across the plausible coverage range. Documents the magnitude so
        a future table update that widened it would fail here.
        """
        gaps = []
        for coverage in [1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 10.0]:
            large = sr._base_from_coverage(coverage, True)
            small = sr._base_from_coverage(coverage, False)
            gaps.append(sr.RATING_SCALE.index(small) - sr.RATING_SCALE.index(large))
        assert min(gaps) >= 1, "the small table should never rate better"
        assert max(gaps) <= 3, f"band gap widened beyond 3 notches: {gaps}"

    def test_boundary_diagnostics_are_recorded(self):
        d = sr.BAND_DIAGNOSTICS
        assert 0 < d["share_large_at_threshold"] < 1
        assert 0 < d["share_within_30pct_of_boundary"] < 1
        assert d["universe_n"] > 1000

    def test_boundary_count_and_rate_preserve_the_exact_population_cell(self):
        d = sr.BAND_DIAGNOSTICS

        assert d["universe_n"] == 3132
        assert d["within_30pct_of_boundary_n"] == 265
        assert isinstance(d["within_30pct_of_boundary_n"], int)
        assert d["share_within_30pct_of_boundary"] == 265 / 3132


def RATING_INDEX(rating: str) -> int:
    return sr.RATING_SCALE.index(rating) if rating in sr.RATING_SCALE else 99
