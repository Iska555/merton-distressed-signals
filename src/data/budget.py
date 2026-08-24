"""
Unique-symbol budget ledger for metered price APIs.

Tiingo's free tier allows 500 UNIQUE SYMBOLS PER CALENDAR MONTH, alongside
50 requests/hour and 1,000/day. The monthly symbol cap is the dangerous one:
it does not reset on a new run, and exhausting it locks the project out until
the 1st of the following month. Exploratory fetching would burn it silently.

So symbol spend is treated as a budget with a hard stop rather than a warning,
and the ledger is committed to the repository. A symbol already fetched this
month costs nothing to fetch again; a symbol never fetched costs one slot,
permanently, until the month rolls over.

The ledger is deliberately conservative: it records a symbol as spent BEFORE
the request is issued. A failed request still consumed the slot as far as the
provider is concerned, and assuming otherwise is how a budget gets overrun.
"""
from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..config import ROOT

LEDGER_PATH = ROOT / "data" / "symbol_budget_ledger.json"

# Tiingo free tier, verified from the pricing page 2026-08-20.
TIINGO_MONTHLY_SYMBOL_CAP = 500
TIINGO_HOURLY_REQUEST_CAP = 50
TIINGO_DAILY_REQUEST_CAP = 1000

# Slots held back so an emergency re-pull is always possible.
DEFAULT_RESERVE = 100

_lock = threading.Lock()


class BudgetExhausted(RuntimeError):
    """Raised instead of issuing a request that would breach the monthly cap."""


@dataclass
class BudgetStatus:
    month: str
    used: int
    cap: int
    reserve: int

    @property
    def spendable(self) -> int:
        return max(self.cap - self.reserve - self.used, 0)

    @property
    def remaining_to_hard_cap(self) -> int:
        return max(self.cap - self.used, 0)

    def __str__(self) -> str:
        return (
            f"{self.month}: {self.used}/{self.cap} unique symbols used, "
            f"{self.spendable} spendable (reserve {self.reserve})"
        )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _current_month() -> str:
    return _now().strftime("%Y-%m")


class SymbolBudget:
    """
    Persistent per-month unique-symbol ledger.

    Usage:
        budget = SymbolBudget("tiingo")
        if budget.is_free(symbol):        # already fetched this month
            ...
        budget.spend(symbol)              # raises BudgetExhausted at the cap
    """

    def __init__(
        self,
        provider: str = "tiingo",
        *,
        cap: int = TIINGO_MONTHLY_SYMBOL_CAP,
        reserve: int = DEFAULT_RESERVE,
        path: Path | None = None,
    ):
        self.provider = provider
        self.cap = cap
        self.reserve = reserve
        self.path = path or LEDGER_PATH
        self._data = self._load()

    # ------------------------------------------------------------------ io
    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001 - a corrupt ledger must not be silently reset
                raise RuntimeError(
                    f"Symbol budget ledger at {self.path} is unreadable. Refusing to "
                    "continue: overwriting it would lose the record of symbols already "
                    "spent this month and risk breaching the provider cap."
                )
        return {"providers": {}}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._data, indent=2, sort_keys=True) + "\n"
        self.path.write_text(payload, encoding="utf-8")

    def _month_node(self, month: str | None = None) -> dict:
        month = month or _current_month()
        providers = self._data.setdefault("providers", {})
        provider = providers.setdefault(self.provider, {"cap": self.cap, "months": {}})
        return provider["months"].setdefault(
            month, {"symbols": [], "first_spend": None, "last_spend": None}
        )

    # --------------------------------------------------------------- query
    def status(self, month: str | None = None) -> BudgetStatus:
        month = month or _current_month()
        node = self._month_node(month)
        return BudgetStatus(month, len(node["symbols"]), self.cap, self.reserve)

    def is_free(self, symbol: str) -> bool:
        """True if this symbol was already spent this month, so re-fetch is free."""
        return symbol.upper() in set(self._month_node()["symbols"])

    def would_exceed(self, symbols) -> list[str]:
        """Which of these symbols are new this month, i.e. would cost a slot."""
        spent = set(self._month_node()["symbols"])
        seen, new = set(), []
        for symbol in symbols:
            upper = symbol.upper()
            if upper in spent or upper in seen:
                continue
            seen.add(upper)
            new.append(upper)
        return new

    # --------------------------------------------------------------- spend
    def spend(self, symbol: str, *, allow_reserve: bool = False) -> None:
        """
        Record a symbol as spent, or refuse.

        Recorded BEFORE the request is issued: a failed request still consumes
        the provider's slot, and pretending otherwise overruns the budget.
        """
        symbol = symbol.upper()
        with _lock:
            node = self._month_node()
            if symbol in set(node["symbols"]):
                return  # already spent this month; free

            used = len(node["symbols"])
            ceiling = self.cap if allow_reserve else self.cap - self.reserve
            if used >= ceiling:
                status = self.status()
                raise BudgetExhausted(
                    f"Refusing to fetch '{symbol}'. {status}. "
                    f"{'Hard cap' if allow_reserve else 'Soft cap (reserve held back)'} "
                    f"of {ceiling} reached for {self.provider} in {status.month}. "
                    "The unique-symbol cap does not reset until the 1st of next month. "
                    "Narrow the sample or wait for the monthly reset."
                )

            node["symbols"].append(symbol)
            node["symbols"].sort()
            stamp = _now().isoformat(timespec="seconds")
            node["first_spend"] = node["first_spend"] or stamp
            node["last_spend"] = stamp
            self._save()

    def require(self, symbols, *, allow_reserve: bool = False) -> None:
        """
        Pre-flight check for a whole batch, before spending any of it.

        Failing early on a 300-symbol run is far better than exhausting the
        budget 280 symbols in and leaving the sample half-built.
        """
        new = self.would_exceed(symbols)
        status = self.status()
        capacity = status.remaining_to_hard_cap if allow_reserve else status.spendable
        if len(new) > capacity:
            raise BudgetExhausted(
                f"Batch needs {len(new)} new symbols but only {capacity} are "
                f"available. {status}. Reduce the sample (e.g. a lower control "
                "ratio) or wait for the monthly reset."
            )


class RateLimiter:
    """
    Sliding-window request throttle.

    Tiingo allows 50 requests/hour on the free tier, so a naive loop stalls or
    starts erroring within a minute. This blocks until a slot is genuinely
    free rather than retrying into a wall.
    """

    def __init__(self, max_requests: int, per_seconds: float, *, name: str = ""):
        self.max_requests = max_requests
        self.per_seconds = per_seconds
        self.name = name
        self._times: list[float] = []

    def acquire(self, *, verbose: bool = True) -> None:
        now = time.monotonic()
        self._times = [t for t in self._times if now - t < self.per_seconds]
        if len(self._times) >= self.max_requests:
            wait = self.per_seconds - (now - self._times[0]) + 0.5
            if wait > 0:
                if verbose:
                    print(
                        f"  [rate limit] {self.name}: {self.max_requests} requests in "
                        f"{self.per_seconds / 60:.0f}m reached; sleeping {wait / 60:.1f}m",
                        flush=True,
                    )
                time.sleep(wait)
            now = time.monotonic()
            self._times = [t for t in self._times if now - t < self.per_seconds]
        self._times.append(time.monotonic())


def tiingo_rate_limiter() -> RateLimiter:
    # One under the cap, so a concurrent manual call cannot tip it over.
    return RateLimiter(TIINGO_HOURLY_REQUEST_CAP - 1, 3600.0, name="tiingo")
