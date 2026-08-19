"""
Bulk barrier-derivation tests.

The bulk path (src/data/dera.py) and the per-CIK path (src/data/edgar.py) must
agree. Two implementations of the debt waterfall would drift, and the drift
would be silent, so these tests assert equivalence on identical inputs.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data import dera, edgar


def _bulk(**tags) -> pd.Series:
    frame = pd.DataFrame([{**{t: np.nan for t in dera.BALANCE_SHEET_TAGS}, **tags}])
    return dera.derive_barriers(frame).iloc[0]


def _per_cik(**tags) -> pd.Series:
    facts = {
        "facts": {
            "us-gaap": {
                tag: {"units": {"USD": [{"end": "2023-12-31", "val": value,
                                         "filed": "2024-02-15", "form": "10-K",
                                         "accn": "x"}]}}
                for tag, value in tags.items()
            }
        }
    }
    return edgar.debt_history("0000000001", facts).iloc[0]


class TestBulkBarriers:
    def test_kmv_is_short_plus_half_long(self):
        row = _bulk(DebtCurrent=20.0, LongTermDebtNoncurrent=100.0)
        assert row["total_debt"] == pytest.approx(120.0)
        assert row["kmv_barrier"] == pytest.approx(70.0)

    def test_total_ltd_never_added_to_its_noncurrent_part(self):
        row = _bulk(DebtCurrent=10.0, LongTermDebtNoncurrent=90.0,
                    LongTermDebt=100.0, LongTermDebtCurrent=10.0)
        assert row["total_debt"] == pytest.approx(100.0)

    def test_long_term_derived_by_subtracting_current_portion(self):
        row = _bulk(LongTermDebt=100.0, LongTermDebtCurrent=25.0)
        assert row["long_term_debt"] == pytest.approx(75.0)
        assert row["total_debt"] == pytest.approx(100.0)

    def test_liabilities_from_accounting_identity_uses_equity_including_nci(self):
        row = _bulk(
            Assets=600.0, StockholdersEquity=180.0,
            StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest=200.0,
        )
        assert row["total_liabilities"] == pytest.approx(400.0)

    def test_direct_liabilities_tag_wins(self):
        row = _bulk(Assets=600.0, Liabilities=410.0, StockholdersEquity=200.0)
        assert row["total_liabilities"] == pytest.approx(410.0)

    def test_leverage_is_liabilities_over_assets(self):
        row = _bulk(Assets=1000.0, Liabilities=400.0)
        assert row["leverage"] == pytest.approx(0.4)


class TestDegenerateAssets:
    def test_zero_assets_do_not_produce_infinite_leverage(self):
        """
        Shell filers report zero assets. The first run produced leverage=inf
        and mean=inf, which would poison any decile boundary computed from the
        column.
        """
        row = _bulk(Assets=0.0, Liabilities=50.0)
        assert pd.isna(row["leverage"])

    def test_negative_assets_are_rejected(self):
        row = _bulk(Assets=-10.0, Liabilities=50.0)
        assert pd.isna(row["leverage"])

    def test_no_infinities_survive_in_a_mixed_frame(self):
        frame = pd.DataFrame([
            {**{t: np.nan for t in dera.BALANCE_SHEET_TAGS},
             "Assets": a, "Liabilities": 100.0}
            for a in (0.0, 1000.0, -5.0, 250.0)
        ])
        out = dera.derive_barriers(frame)
        assert not np.isinf(out["leverage"].astype(float).fillna(0)).any()

    def test_empty_frame_passes_through(self):
        assert dera.derive_barriers(pd.DataFrame()).empty


class TestAgreementWithPerCikPath:
    """The bulk and per-CIK waterfalls must not drift apart."""

    CASES = [
        {"DebtCurrent": 20.0, "LongTermDebtNoncurrent": 100.0},
        {"LongTermDebt": 100.0, "LongTermDebtCurrent": 25.0},
        {"ShortTermBorrowings": 30.0, "LongTermDebtCurrent": 20.0,
         "LongTermDebtNoncurrent": 100.0},
        {"DebtCurrent": 50.0, "ShortTermBorrowings": 30.0,
         "LongTermDebtCurrent": 20.0, "LongTermDebtNoncurrent": 100.0},
    ]

    @pytest.mark.parametrize("tags", CASES)
    def test_total_debt_matches(self, tags):
        assert _bulk(**tags)["total_debt"] == pytest.approx(_per_cik(**tags)["total_debt"])

    @pytest.mark.parametrize("tags", CASES)
    def test_kmv_barrier_matches(self, tags):
        assert _bulk(**tags)["kmv_barrier"] == pytest.approx(_per_cik(**tags)["kmv_barrier"])

    @pytest.mark.parametrize("tags", CASES)
    def test_short_and_long_split_matches(self, tags):
        bulk, per_cik = _bulk(**tags), _per_cik(**tags)
        assert bulk["short_term_debt"] == pytest.approx(per_cik["short_term_debt"])
        assert bulk["long_term_debt"] == pytest.approx(per_cik["long_term_debt"])

    def test_liabilities_identity_matches(self):
        tags = {"LiabilitiesAndStockholdersEquity": 600.0, "StockholdersEquity": 200.0}
        per_cik = _per_cik(**tags)
        bulk = _bulk(Assets=600.0, LiabilitiesAndStockholdersEquity=600.0,
                     StockholdersEquity=200.0)
        assert bulk["total_liabilities"] == pytest.approx(per_cik["total_liabilities"])
