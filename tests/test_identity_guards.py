"""
Identity guards: mutual exclusivity, structural scope, exclusion taxonomy.

These encode two lessons from hand-verification:

  A registrant cannot trade under two symbols at once, so two candidate
  symbols whose windows OVERLAP cannot both be its. A genuine re-ticker shows
  a handoff. That test needs no prose heuristic and cannot be argued with.

  Limited partnerships, trusts and special-purpose entities are a population,
  not an incident. They have no common stock of their own, their filings
  discuss the parent's, and Merton does not price their units anyway.
"""
from __future__ import annotations

import pytest

from src.data import identity
from src.data.identity import ReasonCode


class TestWindowOverlap:
    def test_clean_handoff_is_not_an_overlap(self):
        """Walter's WAC ends 2018-02-09 as Ditech's DHCP begins 2018-02-06."""
        wac = {"start": "1998-03-24", "end": "2018-02-09"}
        dhcp = {"start": "2018-02-06", "end": "2019-10-14"}
        assert identity.windows_overlap(wac, dhcp) == 0

    def test_concurrent_listings_overlap(self):
        a = {"start": "2013-05-01", "end": "2026-08-18"}
        b = {"start": "2013-05-01", "end": "2025-06-30"}
        assert identity.windows_overlap(a, b) > 4000

    def test_disjoint_windows_do_not_overlap(self):
        a = {"start": "2000-01-01", "end": "2005-01-01"}
        b = {"start": "2010-01-01", "end": "2015-01-01"}
        assert identity.windows_overlap(a, b) == 0

    def test_grace_absorbs_a_short_transition(self):
        """A few weeks of dual quotation during a symbol change is normal."""
        a = {"start": "2000-01-01", "end": "2010-02-01"}
        b = {"start": "2010-01-10", "end": "2015-01-01"}
        assert identity.windows_overlap(a, b, grace_days=45) == 0

    def test_open_ended_window_treated_as_still_listed(self):
        a = {"start": "2000-01-01", "end": None}
        b = {"start": "2005-01-01", "end": None}
        assert identity.windows_overlap(a, b) > 0


class TestExclusionTaxonomy:
    """Two families with opposite implications, never pooled on /data."""

    @pytest.mark.parametrize("code", [
        ReasonCode.NO_FILINGS,
        ReasonCode.NO_XBRL_INSTANCE,
        ReasonCode.NO_TRADING_SYMBOL_TAG,
        ReasonCode.SYMBOL_NOT_LISTED,
        ReasonCode.LISTING_EXCLUDES_EVENT,
        ReasonCode.AMBIGUOUS_OVERLAPPING,
    ])
    def test_source_limits_are_unavailability(self, code):
        assert identity.exclusion_family(code) == "data_unavailability"

    def test_non_merton_objects_are_inapplicability(self):
        assert identity.exclusion_family(
            ReasonCode.NO_COMMON_EQUITY) == "model_inapplicability"

    @pytest.mark.parametrize("code", [
        ReasonCode.RESOLVED_XBRL, ReasonCode.RESOLVED_FILING_TEXT,
    ])
    def test_resolutions_are_neither(self, code):
        assert identity.exclusion_family(code) == "resolved"

    def test_families_are_disjoint(self):
        assert not (identity.UNAVAILABILITY_CODES & identity.INAPPLICABILITY_CODES)


class TestOverlapFlagging:
    """resolve() must refuse to auto-rank genuinely ambiguous candidates."""

    def _stub(self, monkeypatch, windows: dict, candidates: list[str]):
        monkeypatch.setattr(identity, "has_common_equity", lambda cik: True)
        monkeypatch.setattr(identity.edgar, "company_profile",
                            lambda cik: {"name": "TEST CO", "tickers": []})
        monkeypatch.setattr(identity, "ticker_from_filings",
                            lambda cik, near_date=None, **kw:
                            ([(c, "xbrl") for c in candidates], 5))
        monkeypatch.setattr(identity, "listing_window", lambda t: windows.get(t))
        monkeypatch.setattr(identity, "covers_event", lambda t, d, **kw: (True, ""))
        monkeypatch.setattr(identity, "_variants", lambda s: [s])

    def test_overlapping_candidates_are_flagged_not_ranked(self, monkeypatch):
        self._stub(monkeypatch, {
            "AAA": {"ticker": "AAA", "exchange": "NYSE",
                    "start": "2010-01-01", "end": "2025-01-01"},
            "BBB": {"ticker": "BBB", "exchange": "NYSE",
                    "start": "2011-01-01", "end": "2024-01-01"},
        }, ["AAA", "BBB"])
        got = identity.resolve("0000000001", event_date="2015-01-01")
        assert got.ticker is None
        assert got.reason_code == ReasonCode.AMBIGUOUS_OVERLAPPING
        assert any("concurrently" in n for n in got.notes)

    def test_handoff_candidates_still_resolve(self, monkeypatch):
        self._stub(monkeypatch, {
            "OLD": {"ticker": "OLD", "exchange": "NYSE",
                    "start": "2000-01-01", "end": "2016-03-01"},
            "NEW": {"ticker": "NEW", "exchange": "NYSE",
                    "start": "2016-02-25", "end": "2020-01-01"},
        }, ["OLD", "NEW"])
        got = identity.resolve("0000000001", event_date="2016-01-01")
        assert got.reason_code == ReasonCode.RESOLVED_XBRL
        # The symbol that died with the firm, not the successor.
        assert got.ticker == "OLD"

    def test_single_candidate_is_never_flagged(self, monkeypatch):
        self._stub(monkeypatch, {
            "ONLY": {"ticker": "ONLY", "exchange": "NYSE",
                     "start": "2000-01-01", "end": "2016-03-01"},
        }, ["ONLY"])
        got = identity.resolve("0000000001", event_date="2016-01-01")
        assert got.ticker == "ONLY"

    def test_flagging_can_be_disabled_for_diagnostics(self, monkeypatch):
        self._stub(monkeypatch, {
            "AAA": {"ticker": "AAA", "exchange": "NYSE",
                    "start": "2010-01-01", "end": "2025-01-01"},
            "BBB": {"ticker": "BBB", "exchange": "NYSE",
                    "start": "2011-01-01", "end": "2024-01-01"},
        }, ["AAA", "BBB"])
        got = identity.resolve("0000000001", event_date="2015-01-01",
                               flag_overlapping=False)
        assert got.ticker is not None


class TestCommonEquityGate:
    """
    The gate must distinguish "has no common equity" from "has no XBRL". They
    look identical to a naive check and land in OPPOSITE exclusion families:
    the first is a scope definition, the second a data limitation.

    Getting this wrong put 72% of 2010-11 candidates in NO_COMMON_EQUITY,
    including Corus Bankshares and AMCORE Financial -- both banks with ordinary
    common stock and simply no XBRL. Re-adjudication changed 48 of 59 rows.
    """

    def _profile(self, monkeypatch):
        monkeypatch.setattr(identity.edgar, "company_profile",
                            lambda cik: {"name": "SOME LP", "tickers": []})

    def test_absent_common_equity_is_excluded_early(self, monkeypatch):
        self._profile(monkeypatch)
        monkeypatch.setattr(identity, "common_equity_status", lambda cik: "absent")

        def _boom(*args, **kwargs):
            raise AssertionError("resolution attempted on a non-Merton object")

        monkeypatch.setattr(identity, "ticker_from_filings", _boom)
        got = identity.resolve("0000000001", event_date="2018-01-01")
        assert got.reason_code == ReasonCode.NO_COMMON_EQUITY
        assert identity.exclusion_family(got.reason_code) == "model_inapplicability"

    def test_no_xbrl_falls_through_to_normal_resolution(self, monkeypatch):
        """
        THE REGRESSION. A pre-XBRL filer must be recorded as missing data, not
        mislabelled a non-Merton object.
        """
        self._profile(monkeypatch)
        monkeypatch.setattr(identity, "common_equity_status", lambda cik: "no_xbrl")
        monkeypatch.setattr(identity, "ticker_from_filings",
                            lambda cik, near_date=None, **kw: ([], 0))
        monkeypatch.setattr(identity, "ticker_from_filing_text",
                            lambda cik, near_date=None, **kw: [])
        got = identity.resolve("0000000001", event_date="2010-01-01")
        assert got.reason_code != ReasonCode.NO_COMMON_EQUITY
        assert identity.exclusion_family(got.reason_code) == "data_unavailability"

    def test_present_common_equity_proceeds(self, monkeypatch):
        self._profile(monkeypatch)
        monkeypatch.setattr(identity, "common_equity_status", lambda cik: "present")
        monkeypatch.setattr(identity, "ticker_from_filings",
                            lambda cik, near_date=None, **kw: ([], 3))
        monkeypatch.setattr(identity, "ticker_from_filing_text",
                            lambda cik, near_date=None, **kw: [])
        got = identity.resolve("0000000001", event_date="2018-01-01")
        assert got.reason_code != ReasonCode.NO_COMMON_EQUITY

    def test_gate_can_be_disabled(self, monkeypatch):
        self._profile(monkeypatch)
        monkeypatch.setattr(identity, "common_equity_status", lambda cik: "absent")
        monkeypatch.setattr(identity, "ticker_from_filings",
                            lambda cik, near_date=None, **kw: ([], 0))
        monkeypatch.setattr(identity, "ticker_from_filing_text",
                            lambda cik, near_date=None, **kw: [])
        got = identity.resolve("0000000001", event_date="2018-01-01",
                               require_common_equity=False)
        assert got.reason_code != ReasonCode.NO_COMMON_EQUITY

    def test_status_returns_no_xbrl_when_nothing_is_tagged(self, monkeypatch):
        monkeypatch.setattr(identity, "has_common_equity", lambda cik: False)
        monkeypatch.setattr(identity.edgar, "_cached_json",
                            lambda url, path: {"units": {}})
        assert identity.common_equity_status("0000000001") == "no_xbrl"

    def test_status_returns_absent_when_other_xbrl_exists(self, monkeypatch):
        monkeypatch.setattr(identity, "has_common_equity", lambda cik: False)
        monkeypatch.setattr(identity.edgar, "_cached_json",
                            lambda url, path: {"units": {"USD": [{"val": 1}]}})
        assert identity.common_equity_status("0000000001") == "absent"
