"""
Guards on era-conditional reporting.

A pooled size gradient published at N = 190 did not survive at N = 346. The
mechanism worth guarding against is not "small sample" in the abstract: it is
that era is the dominant axis of this dataset, so any other variable correlated
with era reproduces the era gradient under its own name. These tests assert
that the tables can actually detect that, and that the band and era definitions
live in exactly one place.
"""
from __future__ import annotations

import pathlib

import pandas as pd
import pytest

from src.analysis import crosstabs as X

ROOT = pathlib.Path(__file__).resolve().parents[1]


def frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


class TestWilson:
    def test_zero_of_n_has_lower_bound_zero(self):
        lo, hi = X.wilson_interval(0, 13)
        assert lo == 0.0
        assert 0.15 < hi < 0.30

    def test_all_of_n_has_upper_bound_one(self):
        lo, hi = X.wilson_interval(13, 13)
        assert hi == 1.0
        assert 0.70 < lo < 0.80

    def test_midpoint_is_symmetric_about_a_half(self):
        lo, hi = X.wilson_interval(10, 20)
        assert lo + hi == pytest.approx(1.0, abs=1e-9)

    def test_empty_cell_is_not_a_number(self):
        lo, hi = X.wilson_interval(0, 0)
        assert lo != lo and hi != hi  # NaN

    def test_interval_narrows_with_n(self):
        widths = [X.wilson_interval(n // 2, n)[1] - X.wilson_interval(n // 2, n)[0]
                  for n in (10, 40, 160)]
        assert widths == sorted(widths, reverse=True)


class TestReportabilityRule:
    """
    Suppression is on interval width, not on a flat count, because an extreme
    rate is estimated precisely even at small n: 0 of 13 is informative, 6 of
    13 is not.
    """

    def test_extreme_rate_is_reportable_at_small_n(self):
        c = X.cell(frame([{"resolved": False}] * 13))
        assert c["n"] == 13 and c["reportable"]

    def test_middling_rate_is_borderline_at_the_same_n(self):
        c = X.cell(frame([{"resolved": True}] * 6 + [{"resolved": False}] * 7))
        assert c["n"] == 13
        assert c["hi"] - c["lo"] > (X.wilson_interval(0, 13)[1] * 2)

    def test_counts_are_present_even_when_the_rate_is_withheld(self):
        c = X.cell(frame([{"resolved": True}] * 3 + [{"resolved": False}] * 2))
        assert c["resolved"] == 3 and c["n"] == 5
        assert not c["reportable"]
        assert c["rate"] == pytest.approx(0.6)

    def test_empty_cell_reports_nothing(self):
        c = X.cell(frame([]).assign(resolved=pd.Series(dtype=bool)))
        assert c == {"n": 0, "resolved": 0, "rate": None,
                     "lo": None, "hi": None, "reportable": False}

    def test_the_rule_would_NOT_have_caught_the_retracted_claim(self):
        """
        Honesty guard, and the reason this rule is documented as a floor rather
        than a safeguard. The retracted size claim rested on 19 of 24 at 79%,
        whose interval is only 31 points wide -- comfortably reportable here.
        The failure was publishing the point estimate without the interval, not
        publishing a cell that was too small to speak about. Nothing in this
        module prevents a reportable cell from being wrong one time in twenty.
        """
        c = X.cell(frame([{"resolved": True}] * 19 + [{"resolved": False}] * 5))
        assert c["reportable"]
        assert c["hi"] - c["lo"] < 0.35
        # The enlarged estimate, 38/65, sits just outside that interval.
        assert (38 / 65) < c["lo"]


class TestBands:
    @pytest.mark.parametrize("value,expected", [
        (0.0, "under $50M"),
        (49_999_999, "under $50M"),
        (50e6, "$50-200M"),
        (199_999_999, "$50-200M"),
        (200e6, "$200M and above"),
        (9e12, "$200M and above"),
        (None, "none reported"),
        (float("nan"), "none reported"),
    ])
    def test_float_band_boundaries(self, value, expected):
        assert X.float_band(value) == expected

    @pytest.mark.parametrize("year,expected", [
        (2010, "2010-11"), (2011, "2010-11"), (2012, "2012-14"),
        (2018, "2015-18"), (2019, "2019-21"), (2024, "2022-24"),
        (2009, None), (2025, None), (None, None), ("junk", None),
    ])
    def test_era_boundaries(self, year, expected):
        assert X.era_label(year) == expected

    def test_eras_are_contiguous_and_ordered(self):
        for (_, hi, _), (lo, _, _) in zip(X.ERAS, X.ERAS[1:]):
            assert lo == hi + 1

    def test_no_float_is_its_own_band_and_is_last(self):
        assert X.FLOAT_ORDER[-1] == X.NO_FLOAT
        assert X.NO_FLOAT not in [b[2] for b in X.FLOAT_BANDS]


class TestConditionalCrosstab:
    def _sample(self) -> pd.DataFrame:
        return X.normalise(frame([
            {"event_year": 2010, "resolved": False, "public_float_usd": None,
             "sic_division": "Mining", "xbrl_instances_seen": 0},
            {"event_year": 2013, "resolved": True, "public_float_usd": 60e6,
             "sic_division": "Mining", "xbrl_instances_seen": 3},
            {"event_year": 2023, "resolved": True, "public_float_usd": 300e6,
             "sic_division": "Manufacturing", "xbrl_instances_seen": 9},
        ]))

    def test_cells_sum_to_the_pooled_column(self):
        table = X.conditional_crosstab(self._sample(), "sic_division")
        for row in table["rows"]:
            assert sum(c["n"] for c in row["cells"]) == row["pooled"]["n"]
            assert (sum(c["resolved"] for c in row["cells"])
                    == row["pooled"]["resolved"])

    def test_all_row_covers_every_observation(self):
        d = self._sample()
        table = X.conditional_crosstab(d, "sic_division")
        assert table["all"]["pooled"]["n"] == len(d)

    def test_only_populated_eras_become_columns(self):
        table = X.conditional_crosstab(self._sample(), "sic_division")
        assert table["eras"] == ["2010-11", "2012-14", "2022-24"]

    def test_explicit_order_is_honoured(self):
        d = X.normalise(frame([
            {"event_year": 2020, "resolved": True, "public_float_usd": 10e6,
             "sic_division": "Mining", "xbrl_instances_seen": 1},
            {"event_year": 2020, "resolved": False, "public_float_usd": 500e6,
             "sic_division": "Mining", "xbrl_instances_seen": 1},
        ]))
        table = X.conditional_crosstab(d, "float_band", X.FLOAT_ORDER)
        assert [r["label"] for r in table["rows"]] == ["under $50M", "$200M and above"]

    def test_it_dissolves_a_gradient_that_is_only_era(self):
        """
        The whole point. Two groups resolve identically WITHIN every era, but
        one is concentrated in the good era. Pooled, that looks like a group
        effect; conditioned, the cells are flat and the effect disappears.
        """
        rows = []
        for year, rate in ((2010, 0.1), (2023, 0.7)):
            for group, count in (("early_heavy", 100 if year == 2010 else 20),
                                 ("late_heavy", 20 if year == 2010 else 100)):
                hits = round(count * rate)
                rows += [{"event_year": year, "resolved": i < hits,
                          "public_float_usd": 1e6, "sic_division": group,
                          "xbrl_instances_seen": 1} for i in range(count)]
        table = X.conditional_crosstab(X.normalise(frame(rows)), "sic_division",
                                       ["early_heavy", "late_heavy"])
        pooled = {r["label"]: r["pooled"]["rate"] for r in table["rows"]}
        assert abs(pooled["early_heavy"] - pooled["late_heavy"]) > 0.30

        by_era = {r["label"]: [c["rate"] for c in r["cells"]] for r in table["rows"]}
        assert len(by_era["early_heavy"]) == 2
        for early, late in zip(by_era["early_heavy"], by_era["late_heavy"]):
            assert early == pytest.approx(late)


class TestFloatAvailability:
    def test_perfect_agreement_when_float_tracks_xbrl(self):
        d = X.normalise(frame(
            [{"event_year": 2010, "resolved": False, "public_float_usd": None,
              "sic_division": "Mining", "xbrl_instances_seen": 0}] * 5
            + [{"event_year": 2023, "resolved": True, "public_float_usd": 5e8,
                "sic_division": "Mining", "xbrl_instances_seen": 4}] * 5))
        assert X.float_availability(d)["agreement"] == pytest.approx(1.0)

    def test_grid_reports_both_xbrl_states(self):
        d = X.normalise(frame([
            {"event_year": 2010, "resolved": False, "public_float_usd": None,
             "sic_division": "Mining", "xbrl_instances_seen": 0},
            {"event_year": 2023, "resolved": True, "public_float_usd": 5e8,
             "sic_division": "Mining", "xbrl_instances_seen": 4},
        ]))
        grid = {g["any_xbrl"]: g for g in X.float_availability(d)["grid"]}
        assert grid[False]["reports_float"] == 0
        assert grid[True]["reports_float"] == 1

    def test_absent_xbrl_column_yields_nothing_rather_than_guessing(self):
        d = X.normalise(frame([{"event_year": 2020, "resolved": True,
                                "public_float_usd": 1e6, "sic_division": "Mining"}]))
        assert X.float_availability(d) == {}


class TestSingleDefinition:
    """
    The bands and eras must exist once. The stale-number failure mode here is
    real: a sector table in the docs kept pre-repass figures while the site
    rebuilt from the CSV, and the two disagreed for a commit.
    """

    def test_site_build_does_not_redefine_bands(self):
        source = (ROOT / "scripts" / "build_site_data.py").read_text(encoding="utf-8")
        assert "SIZE_BANDS =" not in source
        assert "ERA_BANDS =" not in source
        assert "crosstabs" not in source
        assert "build_measurement" not in source

    def test_audit_script_reports_conditional_tables(self):
        source = (ROOT / "scripts" / "audit_resolution.py").read_text(encoding="utf-8")
        assert "conditional_crosstab" in source
        assert "float_availability" in source

    def test_committed_audit_agrees_with_the_published_site_json(self):
        """A figure on the site must be reproducible from the committed CSV."""
        import json
        csv = ROOT / "data" / "processed" / "resolution_audit.csv"
        js = ROOT / "frontend" / "public" / "data" / "measurement.json"
        if not (csv.exists() and js.exists()):
            pytest.skip("audit or site data not built")
        d = X.normalise(pd.read_csv(csv, dtype={"cik": str}))
        payload = json.loads(js.read_text(encoding="utf-8"))
        assert payload["total_candidates"] == len(d)
        assert payload["resolved"] == int(d["resolved"].sum())
        for row in payload["by_sector"]:
            chunk = d[d["sic_division"] == row["sector"]]
            assert row["n"] == len(chunk)
            assert row["resolved"] == int(chunk["resolved"].sum())
