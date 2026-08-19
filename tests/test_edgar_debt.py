"""
Debt-resolution tests, run against synthetic XBRL facts so they are offline,
fast and deterministic.

The bug being guarded: backend/data/equity_fetcher.py summed "Total Debt" AND
its own components, overstating Ford's debt by 2.67x. Any regression that
re-introduces double counting must fail here.
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.data import edgar


def _facts(**concepts) -> dict:
    """Build a minimal companyfacts payload. Values keyed by concept name."""
    us_gaap = {}
    for concept, value in concepts.items():
        us_gaap[concept] = {
            "units": {
                "USD": [
                    {
                        "end": "2023-12-31",
                        "val": value,
                        "filed": "2024-02-15",
                        "form": "10-K",
                        "accn": "0000000000-24-000001",
                    }
                ]
            }
        }
    return {"facts": {"us-gaap": us_gaap}}


def _row(**concepts) -> pd.Series:
    out = edgar.debt_history("0000000001", _facts(**concepts))
    assert len(out) == 1, f"expected one period, got {len(out)}"
    return out.iloc[0]


class TestNoDoubleCounting:
    def test_total_ltd_is_not_added_to_its_own_noncurrent_part(self):
        """LongTermDebt and LongTermDebtNoncurrent overlap; never add them."""
        row = _row(
            DebtCurrent=10.0,
            LongTermDebtNoncurrent=90.0,
            LongTermDebt=100.0,          # includes the current portion
            LongTermDebtCurrent=10.0,
        )
        assert row.long_term_debt == 90.0
        assert row.total_debt == 100.0   # not 190, not 200

    def test_long_term_derived_by_subtracting_current_portion(self):
        """When only the total LTD is tagged, strip the current portion once."""
        row = _row(LongTermDebt=100.0, LongTermDebtCurrent=25.0)
        assert row.long_term_debt == 75.0
        assert row.short_term_debt == 25.0
        assert row.total_debt == 100.0

    def test_debt_current_preferred_over_its_components(self):
        """DebtCurrent is the total; components must not be added on top."""
        row = _row(
            DebtCurrent=50.0,
            ShortTermBorrowings=30.0,
            LongTermDebtCurrent=20.0,
            LongTermDebtNoncurrent=100.0,
        )
        assert row.short_term_debt == 50.0   # not 100
        assert row.total_debt == 150.0

    def test_disjoint_short_term_components_are_summed(self):
        """Without DebtCurrent, the two disjoint parts DO add up."""
        row = _row(
            ShortTermBorrowings=30.0,
            LongTermDebtCurrent=20.0,
            LongTermDebtNoncurrent=100.0,
        )
        assert row.short_term_debt == 50.0
        assert row.total_debt == 150.0


class TestBarrierConventions:
    def test_kmv_barrier_is_short_plus_half_long(self):
        row = _row(DebtCurrent=20.0, LongTermDebtNoncurrent=100.0)
        assert row.total_debt == 120.0
        assert row.kmv_barrier == 70.0    # 20 + 0.5*100

    def test_all_three_barriers_emitted(self):
        row = _row(DebtCurrent=20.0, LongTermDebtNoncurrent=100.0, Liabilities=500.0)
        assert row.kmv_barrier == 70.0
        assert row.total_debt == 120.0
        assert row.total_liabilities == 500.0


class TestTotalLiabilities:
    def test_direct_tag_preferred(self):
        row = _row(Liabilities=400.0, LiabilitiesAndStockholdersEquity=600.0,
                   StockholdersEquity=150.0)
        assert row.total_liabilities == 400.0
        assert row.liabilities_source == "Liabilities"

    def test_derived_from_accounting_identity(self):
        row = _row(LiabilitiesAndStockholdersEquity=600.0, StockholdersEquity=200.0)
        assert row.total_liabilities == 400.0
        assert row.liabilities_source == "assets_minus_equity"

    def test_equity_including_nci_preferred(self):
        """Assets = Liabilities + TOTAL equity. Parent-only overstates liabilities."""
        row = _row(
            LiabilitiesAndStockholdersEquity=600.0,
            StockholdersEquity=180.0,
            StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest=200.0,
        )
        assert row.total_liabilities == 400.0   # not 420


class TestPointInTime:
    def test_as_of_excludes_unfiled_data(self):
        """A period that ended but had not yet been FILED must be invisible."""
        history = pd.DataFrame(
            {
                "end": pd.to_datetime(["2023-06-30", "2023-12-31"]),
                "filed": pd.to_datetime(["2023-08-01", "2024-02-15"]),
                "total_debt": [100.0, 200.0],
            }
        )
        # 2024-01-15: the Dec period has ended but is not yet public.
        got = edgar.as_of(history, "2024-01-15", ["total_debt"])
        assert got["total_debt"] == 100.0

        got = edgar.as_of(history, "2024-03-01", ["total_debt"])
        assert got["total_debt"] == 200.0

    def test_as_of_reports_reporting_lag(self):
        history = pd.DataFrame(
            {
                "end": pd.to_datetime(["2023-12-31"]),
                "filed": pd.to_datetime(["2024-02-15"]),
                "total_debt": [200.0],
            }
        )
        got = edgar.as_of(history, "2024-03-01", ["total_debt"])
        assert got["reporting_lag_days"] == 46

    def test_as_of_returns_none_before_any_filing(self):
        history = pd.DataFrame(
            {
                "end": pd.to_datetime(["2023-12-31"]),
                "filed": pd.to_datetime(["2024-02-15"]),
                "total_debt": [200.0],
            }
        )
        assert edgar.as_of(history, "2020-01-01", ["total_debt"]) is None

    def test_as_of_handles_empty(self):
        assert edgar.as_of(pd.DataFrame(), "2024-01-01", ["total_debt"]) is None


class TestDegenerate:
    def test_no_facts_returns_empty(self):
        """Pre-XBRL filers (e.g. Lehman) yield None facts; must not raise."""
        assert edgar.debt_history("0000806085", {}).empty is True

    def test_unusable_facts_return_empty(self):
        assert edgar.debt_history("0000000001", {"facts": {"us-gaap": {}}}).empty is True
