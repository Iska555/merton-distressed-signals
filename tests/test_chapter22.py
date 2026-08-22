"""
Chapter 22 deduplication (spec 1.2.2).

A firm filing Item 1.03 twice went bankrupt twice; it is not a duplicate row.
Walter Investment (2017, 2018) re-emerged and filed again as Ditech Holding
(2019), all on CIK 0001040719. The FIRST filing is the event.
"""
from __future__ import annotations

import pandas as pd
import pytest

from scripts.audit_resolution import collect_candidates  # noqa: F401  (import check)
import scripts.audit_resolution as audit


@pytest.fixture
def stub_filings(monkeypatch):
    """Two firms: one Chapter 22 across years, one single event."""
    def _search(start, end, **kwargs):
        year = int(str(start)[:4])
        rows = {
            2017: [("0001040719", "WALTER INVESTMENT", "2017-12-01", "6162")],
            2019: [("0001040719", "DITECH HOLDING", "2019-02-11", "6162"),
                   ("0000886158", "BED BATH", "2019-06-01", "5712")],
        }.get(year, [])
        return pd.DataFrame(
            [{"cik": c, "company": n, "filed_date": pd.Timestamp(d), "sic": s}
             for c, n, d, s in rows]
        )

    monkeypatch.setattr(audit.edgar, "search_bankruptcy_filings", _search)
    monkeypatch.setattr(audit.edgar, "first_filing_per_cik", lambda f: f)


class TestChapter22:
    def test_one_row_per_cik(self, stub_filings):
        got = audit.collect_candidates(2017, 2019, 25)
        assert got["cik"].duplicated().sum() == 0

    def test_first_filing_is_the_event(self, stub_filings):
        """
        The question is about detecting ONSET. Keeping the last filing would
        discard the very transition the model is being tested on.
        """
        got = audit.collect_candidates(2017, 2019, 25)
        walter = got[got.cik == "0001040719"].iloc[0]
        assert str(walter["filed_date"])[:10] == "2017-12-01"

    def test_subsequent_events_recorded_not_discarded(self, stub_filings):
        got = audit.collect_candidates(2017, 2019, 25)
        walter = got[got.cik == "0001040719"].iloc[0]
        assert walter["n_bankruptcy_events"] == 2
        assert "2019-02-11" in walter["subsequent_event_dates"]
        assert bool(walter["is_chapter_22"])

    def test_single_event_firms_are_not_flagged(self, stub_filings):
        got = audit.collect_candidates(2017, 2019, 25)
        bbby = got[got.cik == "0000886158"].iloc[0]
        assert bbby["n_bankruptcy_events"] == 1
        assert not bool(bbby["is_chapter_22"])
        assert bbby["subsequent_event_dates"] == ""

    def test_timestamp_dates_join_without_error(self, stub_filings):
        """
        Regression: filed_date arrives as Timestamp, and the join raised
        TypeError. The earlier smoke test missed it by containing no
        Chapter 22 firms, so the join never saw a real element.
        """
        got = audit.collect_candidates(2017, 2019, 25)
        assert isinstance(
            got[got.cik == "0001040719"].iloc[0]["subsequent_event_dates"], str
        )
