"""
Symbol-budget ledger tests.

Tiingo's free tier allows 500 unique symbols per CALENDAR MONTH. Exhausting it
locks the project out until the 1st, so the budget must hard-stop rather than
warn, and a pipeline rerun must consume zero new symbols.
"""
from __future__ import annotations

import json

import pytest

from src.data import budget as budget_mod
from src.data.budget import BudgetExhausted, SymbolBudget


@pytest.fixture
def ledger(tmp_path):
    return SymbolBudget("tiingo", cap=10, reserve=2, path=tmp_path / "ledger.json")


class TestSpending:
    def test_new_symbol_costs_a_slot(self, ledger):
        assert ledger.status().used == 0
        ledger.spend("AAPL")
        assert ledger.status().used == 1

    def test_repeat_symbol_is_free(self, ledger):
        for _ in range(5):
            ledger.spend("AAPL")
        assert ledger.status().used == 1

    def test_symbols_are_case_insensitive(self, ledger):
        ledger.spend("aapl")
        ledger.spend("AAPL")
        assert ledger.status().used == 1
        assert ledger.is_free("AaPl")

    def test_reserve_is_held_back(self, ledger):
        """cap=10, reserve=2 -> only 8 spendable without allow_reserve."""
        for i in range(8):
            ledger.spend(f"S{i}")
        assert ledger.status().spendable == 0
        with pytest.raises(BudgetExhausted):
            ledger.spend("OVERFLOW")

    def test_reserve_can_be_deliberately_released(self, ledger):
        for i in range(8):
            ledger.spend(f"S{i}")
        ledger.spend("EMERGENCY", allow_reserve=True)
        assert ledger.status().used == 9

    def test_hard_cap_cannot_be_exceeded_even_with_reserve(self, ledger):
        for i in range(10):
            ledger.spend(f"S{i}", allow_reserve=True)
        with pytest.raises(BudgetExhausted):
            ledger.spend("OVER", allow_reserve=True)

    def test_exhaustion_raises_not_warns(self, ledger):
        """A warning would let a run silently overrun the provider cap."""
        for i in range(8):
            ledger.spend(f"S{i}")
        with pytest.raises(BudgetExhausted) as exc:
            ledger.spend("NEXT")
        assert "does not reset until" in str(exc.value)


class TestPreflight:
    def test_require_passes_when_batch_fits(self, ledger):
        ledger.require([f"S{i}" for i in range(8)])

    def test_require_fails_before_spending_anything(self, ledger):
        """Failing early beats exhausting the budget mid-run."""
        with pytest.raises(BudgetExhausted):
            ledger.require([f"S{i}" for i in range(9)])
        assert ledger.status().used == 0

    def test_require_ignores_already_spent_symbols(self, ledger):
        for i in range(6):
            ledger.spend(f"S{i}")
        ledger.require([f"S{i}" for i in range(6)] + ["NEW1", "NEW2"])

    def test_would_exceed_lists_only_new_symbols(self, ledger):
        ledger.spend("AAPL")
        assert ledger.would_exceed(["AAPL", "MSFT", "MSFT", "NVDA"]) == ["MSFT", "NVDA"]


class TestPersistence:
    def test_ledger_survives_reload(self, tmp_path):
        path = tmp_path / "ledger.json"
        first = SymbolBudget("tiingo", cap=10, reserve=2, path=path)
        first.spend("AAPL")
        first.spend("MSFT")

        second = SymbolBudget("tiingo", cap=10, reserve=2, path=path)
        assert second.status().used == 2
        assert second.is_free("AAPL")

    def test_rerun_consumes_zero_new_symbols(self, tmp_path):
        """The property the whole design exists to guarantee."""
        path = tmp_path / "ledger.json"
        symbols = [f"SYM{i}" for i in range(6)]

        first = SymbolBudget("tiingo", cap=100, reserve=10, path=path)
        for symbol in symbols:
            first.spend(symbol)
        after_first = first.status().used

        second = SymbolBudget("tiingo", cap=100, reserve=10, path=path)
        assert second.would_exceed(symbols) == []
        for symbol in symbols:
            second.spend(symbol)
        assert second.status().used == after_first

    def test_corrupt_ledger_refuses_rather_than_resetting(self, tmp_path):
        """Silently starting from zero would risk breaching the provider cap."""
        path = tmp_path / "ledger.json"
        path.write_text("{ not json", encoding="utf-8")
        with pytest.raises(RuntimeError, match="unreadable"):
            SymbolBudget("tiingo", path=path)

    def test_ledger_is_deterministic_on_disk(self, tmp_path):
        """Sorted keys and symbols, so the committed file has stable diffs."""
        path = tmp_path / "ledger.json"
        ledger = SymbolBudget("tiingo", cap=10, reserve=2, path=path)
        for symbol in ("ZZZ", "AAA", "MMM"):
            ledger.spend(symbol)
        payload = json.loads(path.read_text(encoding="utf-8"))
        month = next(iter(payload["providers"]["tiingo"]["months"].values()))
        assert month["symbols"] == ["AAA", "MMM", "ZZZ"]


class TestRateLimiter:
    def test_allows_requests_under_the_cap(self):
        limiter = budget_mod.RateLimiter(5, 3600.0, name="test")
        for _ in range(5):
            limiter.acquire(verbose=False)   # must not block

    def test_tiingo_limiter_stays_under_the_published_cap(self):
        limiter = budget_mod.tiingo_rate_limiter()
        assert limiter.max_requests < budget_mod.TIINGO_HOURLY_REQUEST_CAP
        assert limiter.per_seconds == 3600.0


class TestCacheIntegration:
    """The guarantee: a cached symbol never spends a slot."""

    def test_cache_hit_does_not_spend(self, tmp_path, monkeypatch):
        import json as _json
        from src.data import prices

        monkeypatch.setattr(prices, "_CACHE", tmp_path)
        monkeypatch.setattr(prices, "TIINGO_API_KEY", "fake-key-must-not-be-used")

        cached = [
            {"date": "2023-01-03T00:00:00.000Z", "adjClose": 10.0},
            {"date": "2023-01-04T00:00:00.000Z", "adjClose": 11.0},
        ]
        path = prices._cache_path("tiingo", "TEST", "2023-01-01", "2023-12-31")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_json.dumps(cached), encoding="utf-8")

        ledger = SymbolBudget("tiingo", cap=10, reserve=2, path=tmp_path / "l.json")
        got = prices.fetch_tiingo(
            "TEST", "2023-01-01", "2023-12-31", budget=ledger
        )
        assert got.ok
        assert got.n == 2
        assert ledger.status().used == 0      # nothing spent

    def test_missing_key_does_not_spend(self, tmp_path, monkeypatch):
        from src.data import prices

        monkeypatch.setattr(prices, "_CACHE", tmp_path)
        monkeypatch.setattr(prices, "TIINGO_API_KEY", None)

        ledger = SymbolBudget("tiingo", cap=10, reserve=2, path=tmp_path / "l.json")
        got = prices.fetch_tiingo("NOKEY", "2023-01-01", "2023-12-31", budget=ledger)
        assert not got.ok
        assert "not configured" in got.reason
        assert ledger.status().used == 0

    def test_exhausted_budget_degrades_rather_than_crashing(self, tmp_path, monkeypatch):
        from src.data import prices

        monkeypatch.setattr(prices, "_CACHE", tmp_path)
        monkeypatch.setattr(prices, "TIINGO_API_KEY", "fake")

        ledger = SymbolBudget("tiingo", cap=2, reserve=2, path=tmp_path / "l.json")
        got = prices.fetch_tiingo("ANY", "2023-01-01", "2023-12-31", budget=ledger)
        assert not got.ok
        assert got.reason.startswith("budget:")
