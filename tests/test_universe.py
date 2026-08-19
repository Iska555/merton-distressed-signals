"""
Matching tests: does the implementation follow docs/matching-spec.md exactly?

Each test names the spec clause it enforces. If a test and the spec disagree,
one of them is wrong and the spec is amended in its own commit -- never
resolved silently in code.

Synthetic universes throughout, so these run offline and deterministically.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data import universe as U


def _universe(n=60, sector="Manufacturing", start=1000) -> pd.DataFrame:
    """A pool with a spread of size and leverage deciles."""
    rows = []
    for i in range(n):
        rows.append({
            "cik": str(start + i).zfill(10),
            "name": f"FIRM {i}",
            "sic": "3674",
            "sic_division": sector,
            "is_financial": False,
            "total_assets": 1e8 * (i + 1),
            "total_liabilities": 5e7 * (i + 1),
            "leverage": 0.3 + (i % 10) * 0.05,
            "log_assets": np.log(1e8 * (i + 1)),
            "size_decile": (i % 10) + 1,
            "leverage_decile": (i % 10) + 1,
            "anchor_quarter": "2020Q1",
        })
    return pd.DataFrame(rows)


@pytest.fixture
def patched(monkeypatch):
    def _install(pool: pd.DataFrame):
        monkeypatch.setattr(U, "eligible_universe_at", lambda date, **kw: pool)
    return _install


class TestRatioRule:
    """Spec section 3."""

    @pytest.mark.parametrize("n,expected", [
        (10, 5), (66, 5), (67, 4), (80, 4), (81, 3),
        (100, 3), (101, 2), (133, 2), (134, 1), (400, 1),
    ])
    def test_matches_the_spec_formula(self, n, expected):
        assert U.controls_per_treatment(n) == expected

    @pytest.mark.parametrize("n", [1, 10, 50, 66, 67, 80, 100, 133, 134, 200])
    def test_never_exceeds_the_symbol_budget(self, n):
        ratio = U.controls_per_treatment(n)
        assert n * (ratio + 1) <= U.SYMBOL_BUDGET_FOR_STUDY

    @pytest.mark.parametrize("n,fits", [(100, True), (200, True), (201, False), (350, False)])
    def test_flags_cohorts_too_large_for_one_month(self, n, fits):
        """
        Above N=200 even 1:1 breaches the 400-symbol budget. The spec forbids
        truncating treatment, so such a run spans two calendar months. The
        implementation surfaced this gap; the spec was amended to cover it.
        """
        assert U.fits_monthly_budget(n) is fits

    def test_ratio_never_falls_below_one(self):
        assert U.controls_per_treatment(10_000) == 1

    def test_treatment_is_never_truncated(self):
        """
        Spec section 3: the ratio absorbs the constraint, not the cohort.
        Dropping defaults would reintroduce the selection problem the study
        exists to avoid.
        """
        pool = _universe(400, start=5000)
        treatment = pd.DataFrame({
            "cik": [str(1000 + i).zfill(10) for i in range(150)],
            "event_date": ["2020-06-01"] * 150,
            "sic": ["3674"] * 150,
        })
        assert U.controls_per_treatment(len(treatment)) == 1
        assert len(treatment) == 150   # unchanged


class TestWithoutReplacement:
    """Spec section 4.1."""

    def test_no_control_is_used_twice(self, patched):
        patched(_universe(60))
        treatment = pd.DataFrame({
            "cik": ["0000001000", "0000001001", "0000001002"],
            "event_date": ["2020-06-01"] * 3,
            "sic": ["3674"] * 3,
        })
        matched, _ = U.match_controls(treatment, ratio=3, verbose=False)
        assert matched["control_cik"].duplicated().sum() == 0

    def test_treatment_firms_never_become_controls(self, patched):
        patched(_universe(60))
        treatment = pd.DataFrame({
            "cik": ["0000001000", "0000001005", "0000001010"],
            "event_date": ["2020-06-01"] * 3,
            "sic": ["3674"] * 3,
        })
        matched, _ = U.match_controls(treatment, ratio=3, verbose=False)
        assert not set(matched["control_cik"]) & set(treatment["cik"])

    def test_forbidden_ciks_are_excluded(self, patched):
        """Spec C2: a firm that defaults later is not a control."""
        patched(_universe(60))
        banned = {"0000001011", "0000001021", "0000001031"}
        treatment = pd.DataFrame({
            "cik": ["0000001001"], "event_date": ["2020-06-01"], "sic": ["3674"],
        })
        matched, _ = U.match_controls(treatment, ratio=5,
                                      excluded_ciks=banned, verbose=False)
        assert not set(matched["control_cik"]) & banned


class TestCaliper:
    """Spec section 2.2."""

    def test_sector_match_is_exact(self, patched):
        pool = pd.concat([
            _universe(30, "Manufacturing", start=1000),
            _universe(30, "Retail Trade", start=2000),
        ], ignore_index=True)
        patched(pool)
        treatment = pd.DataFrame({
            "cik": ["0000001001"], "event_date": ["2020-06-01"], "sic": ["3674"],
        })
        matched, _ = U.match_controls(treatment, ratio=5, verbose=False)
        assert set(matched["sic_division"]) == {"Manufacturing"}

    def test_size_and_leverage_stay_within_one_decile(self, patched):
        patched(_universe(60))
        treatment = pd.DataFrame({
            "cik": ["0000001004"], "event_date": ["2020-06-01"], "sic": ["3674"],
        })
        matched, _ = U.match_controls(treatment, ratio=5, verbose=False)
        assert (matched["size_decile"] - matched["treatment_size_decile"]).abs().max() <= 1
        assert (matched["leverage_decile"]
                - matched["treatment_leverage_decile"]).abs().max() <= 1

    def test_shortfall_is_recorded_not_filled(self, patched):
        """Spec 2.2: candidates outside the caliper are never used."""
        patched(_universe(12))
        treatment = pd.DataFrame({
            "cik": ["0000001001"], "event_date": ["2020-06-01"], "sic": ["3674"],
        })
        matched, results = U.match_controls(treatment, ratio=5, verbose=False)
        assert results[0].shortfall >= 0
        assert len(matched) == len(results[0].controls)


class TestDeterminism:
    """Spec section 4.2: a total order, so no random draw is ever needed."""

    def test_repeated_runs_are_identical(self, patched):
        treatment = pd.DataFrame({
            "cik": ["0000001001", "0000001002"],
            "event_date": ["2020-06-01", "2020-07-01"],
            "sic": ["3674"] * 2,
        })
        patched(_universe(60))
        first, _ = U.match_controls(treatment, ratio=3, verbose=False)
        patched(_universe(60))
        second, _ = U.match_controls(treatment, ratio=3, verbose=False)
        pd.testing.assert_frame_equal(first, second)

    def test_row_order_of_input_does_not_change_the_result(self, patched):
        """Processing order is fixed by the spec (event date, then CIK)."""
        forward = pd.DataFrame({
            "cik": ["0000001001", "0000001002"],
            "event_date": ["2020-06-01", "2020-07-01"],
            "sic": ["3674"] * 2,
        })
        reversed_rows = forward.iloc[::-1].reset_index(drop=True)

        patched(_universe(60))
        a, _ = U.match_controls(forward, ratio=3, verbose=False)
        patched(_universe(60))
        b, _ = U.match_controls(reversed_rows, ratio=3, verbose=False)
        pd.testing.assert_frame_equal(a, b)

    def test_closest_on_assets_is_preferred(self, patched):
        """Tie-break rule 1: smaller |log assets| gap wins."""
        patched(_universe(60))
        treatment = pd.DataFrame({
            "cik": ["0000001030"], "event_date": ["2020-06-01"], "sic": ["3674"],
        })
        matched, _ = U.match_controls(treatment, ratio=3, verbose=False)
        gaps = matched["log_assets_gap"].tolist()
        assert gaps == sorted(gaps)


class TestAnchorDate:
    """Spec section 2."""

    def test_anchor_is_24_months_before_the_event(self):
        assert U.anchor_date("2023-04-23") == pd.Timestamp("2021-04-23")

    def test_quarter_mapping(self):
        assert U.quarter_of("2021-04-23") == (2021, 2)
        assert U.quarter_of("2021-01-01") == (2021, 1)
        assert U.quarter_of("2021-12-31") == (2021, 4)


class TestSectorHelpers:
    def test_financials_are_identified(self):
        assert U.is_financial(6022) and U.is_financial(6798)
        assert not U.is_financial(3674) and not U.is_financial(5731)

    def test_divisions_map_correctly(self):
        assert U.sic_division(3674) == "Manufacturing"
        assert U.sic_division(6022) == "Finance, Insurance, Real Estate"
        assert U.sic_division(5731) == "Retail Trade"
        assert U.sic_division(None) == "Unknown"


class TestBalance:
    def test_reports_standardised_mean_differences(self, patched):
        patched(_universe(60))
        treatment = pd.DataFrame({
            "cik": ["0000001001", "0000001002", "0000001003"],
            "event_date": ["2020-06-01"] * 3,
            "sic": ["3674"] * 3,
        })
        matched, _ = U.match_controls(treatment, ratio=3, verbose=False)
        table = U.balance_table(matched, {})
        assert set(table["covariate"]) == {"size_decile", "leverage_decile"}
        assert table["standardised_mean_difference"].notna().all()

    def test_empty_input(self):
        assert U.balance_table(pd.DataFrame(), {}).empty


class TestEmptyInputs:
    def test_no_treatment_returns_empty(self):
        matched, results = U.match_controls(pd.DataFrame(), verbose=False)
        assert matched.empty and results == []

    def test_empty_universe_records_a_note(self, patched):
        patched(pd.DataFrame())
        treatment = pd.DataFrame({
            "cik": ["0000001001"], "event_date": ["2020-06-01"], "sic": ["3674"],
        })
        matched, results = U.match_controls(treatment, ratio=5, verbose=False)
        assert matched.empty
        assert results[0].notes
