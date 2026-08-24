"""
SEC EDGAR client, keyed on CIK.

Why CIK and never ticker: tickers are recycled. Yahoo serves Overstock/Beyond
Inc. prices as continuous "Bed Bath & Beyond" history straight through BBBY's
2023 bankruptcy; SBNY returns a different company from 2024; AAL's pre-2013
history is US Airways. A ticker is a time-varying attribute of a filer, not an
identity. See docs/PHASE0_DATA_INVENTORY.md section 1.2.

Two things this module provides:
  1. A bankruptcy event list from 8-K Item 1.03 filings (survivorship-bias-free
     by construction, because it is drawn from filings rather than from any list
     of currently-listed companies).
  2. Point-in-time fundamentals from XBRL company facts, respecting filing dates
     so no observation can use data that was not yet public.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path

import pandas as pd

from ..config import DATA_RAW, SEC_RATE_LIMIT_PER_SEC, SEC_USER_AGENT

_CACHE = DATA_RAW / "edgar"
_CACHE.mkdir(parents=True, exist_ok=True)

_last_request_at = 0.0


def _throttled_get(url: str, timeout: int = 45) -> bytes:
    """GET with a global rate limit, honouring SEC's published 10 req/s cap."""
    global _last_request_at
    min_gap = 1.0 / SEC_RATE_LIMIT_PER_SEC
    elapsed = time.monotonic() - _last_request_at
    if elapsed < min_gap:
        time.sleep(min_gap - elapsed)

    req = urllib.request.Request(url, headers={"User-Agent": SEC_USER_AGENT})
    last_err: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                _last_request_at = time.monotonic()
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise  # genuinely absent; caller decides what that means
            last_err = exc
        except Exception as exc:  # noqa: BLE001 - transient network faults
            last_err = exc
        time.sleep(1.5 * (attempt + 1))
    _last_request_at = time.monotonic()
    raise RuntimeError(f"EDGAR request failed after retries: {url}") from last_err


def _cached_json(url: str, cache_name: str, refresh: bool = False) -> dict:
    """Fetch JSON, caching under data/raw/edgar so reruns are offline and fast."""
    path = _CACHE / cache_name
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))
    payload = _throttled_get(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return json.loads(payload.decode("utf-8"))


# --------------------------------------------------------------------------
# Bankruptcy event discovery
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class BankruptcyFiling:
    """One 8-K carrying Item 1.03 (Bankruptcy or Receivership)."""
    cik: str
    company: str
    filed_date: str
    accession: str
    sic: str | None
    state_incorporated: str | None
    items: tuple[str, ...]


def search_bankruptcy_filings(
    start: str,
    end: str,
    *,
    page_size: int = 10,
    max_pages_per_window: int = 100,
    refresh: bool = False,
) -> list[BankruptcyFiling]:
    """
    Enumerate 8-K filings tagged Item 1.03 between two dates.

    EDGAR full-text search caps a result set at 10,000 hits and pages 10 at a
    time, so callers should pass windows narrow enough to stay under that. One
    calendar quarter is comfortably safe (peak observed: ~650 hits/year).

    IMPORTANT: the returned list is *candidates*, not confirmed bankruptcies.
    A parent frequently files an 8-K Item 1.03 about a subsidiary's filing --
    RenaissanceRe, LendingTree, FirstEnergy and NRG all appear here and are all
    alive. Adjudication happens in src/data/universe.py, not here.
    """
    out: dict[tuple[str, str], BankruptcyFiling] = {}
    for page in range(max_pages_per_window):
        frm = page * page_size
        url = (
            "https://efts.sec.gov/LATEST/search-index?q="
            + urllib.parse.quote('"Item 1.03"')
            + f"&forms=8-K&startdt={start}&enddt={end}&from={frm}"
        )
        key = f"fts/{start}_{end}_{frm}.json"
        try:
            payload = _cached_json(url, key, refresh=refresh)
        except Exception:
            break

        hits = payload.get("hits", {}).get("hits", [])
        if not hits:
            break

        for hit in hits:
            src = hit.get("_source", {})
            items = tuple(src.get("items") or ())
            # The query is a phrase match on the document text; require the
            # structured item tag as well, which drops incidental mentions.
            if "1.03" not in items:
                continue
            ciks = src.get("ciks") or []
            if not ciks:
                continue
            cik = str(ciks[0]).zfill(10)
            accession = src.get("adsh", "")
            names = src.get("display_names") or ["?"]
            filing = BankruptcyFiling(
                cik=cik,
                company=names[0],
                filed_date=src.get("file_date", ""),
                accession=accession,
                sic=(src.get("sics") or [None])[0],
                state_incorporated=(src.get("inc_states") or [None])[0],
                items=items,
            )
            out[(cik, accession)] = filing

        total = payload.get("hits", {}).get("total", {}).get("value", 0)
        if frm + page_size >= min(total, 10_000):
            break

    return list(out.values())


def first_filing_per_cik(filings: list[BankruptcyFiling]) -> pd.DataFrame:
    """
    Collapse to one row per CIK at its EARLIEST Item 1.03 filing.

    A single bankruptcy generates many 8-Ks. The first is the event date; later
    ones are plan confirmations and emergences, which are not the event we are
    trying to predict.
    """
    if not filings:
        return pd.DataFrame(
            columns=["cik", "company", "filed_date", "accession", "sic",
                     "state_incorporated", "n_filings"]
        )
    df = pd.DataFrame([asdict(f) for f in filings])
    df["filed_date"] = pd.to_datetime(df["filed_date"], errors="coerce")
    df = df.dropna(subset=["filed_date"])
    counts = df.groupby("cik").size().rename("n_filings")
    df = df.sort_values("filed_date").groupby("cik", as_index=False).first()
    df = df.merge(counts, on="cik", how="left")
    df["items"] = df["items"].apply(lambda t: ",".join(t) if isinstance(t, tuple) else t)
    return df.sort_values("filed_date").reset_index(drop=True)


# --------------------------------------------------------------------------
# Company identity and metadata
# --------------------------------------------------------------------------

def load_ticker_map(refresh: bool = False) -> pd.DataFrame:
    """
    CIK -> current ticker, from EDGAR's company_tickers.json.

    CAUTION: this file lists only CURRENTLY REGISTERED filers. Of 579 bankrupt
    CIKs sampled in Phase 0, only 45 appear here. Survivorship bias is baked
    into the file itself, so it must never be used to define a sample -- only
    to attach a ticker to a CIK already selected on other grounds.
    """
    payload = _cached_json(
        "https://www.sec.gov/files/company_tickers.json",
        "company_tickers.json",
        refresh=refresh,
    )
    rows = [
        {
            "cik": str(v["cik_str"]).zfill(10),
            "ticker": v["ticker"].upper(),
            "title": v["title"],
        }
        for v in payload.values()
    ]
    return pd.DataFrame(rows).drop_duplicates(subset=["cik"], keep="first")


def get_submissions(cik: str, refresh: bool = False) -> dict:
    """
    Company metadata: name, SIC, former names, and every ticker ever attached.

    This is how a delisted filer's historical ticker is recovered, since
    company_tickers.json will not contain it.
    """
    cik = str(cik).zfill(10)
    return _cached_json(
        f"https://data.sec.gov/submissions/CIK{cik}.json",
        f"submissions/CIK{cik}.json",
        refresh=refresh,
    )


def company_profile(cik: str, refresh: bool = False) -> dict:
    """Flatten the fields of `get_submissions` the study actually uses."""
    try:
        sub = get_submissions(cik, refresh=refresh)
    except Exception:
        return {"cik": str(cik).zfill(10)}
    return {
        "cik": str(cik).zfill(10),
        "name": sub.get("name"),
        "sic": sub.get("sic"),
        "sic_description": sub.get("sicDescription"),
        "tickers": sub.get("tickers") or [],
        "exchanges": sub.get("exchanges") or [],
        "former_names": [fn.get("name") for fn in (sub.get("formerNames") or [])],
        "entity_type": sub.get("entityType"),
        "state_of_incorporation": sub.get("stateOfIncorporation"),
        "fiscal_year_end": sub.get("fiscalYearEnd"),
    }


# --------------------------------------------------------------------------
# XBRL company facts -> point-in-time fundamentals
# --------------------------------------------------------------------------

def get_company_facts(cik: str, refresh: bool = False) -> dict | None:
    """All XBRL facts for a filer. Returns None if the filer predates XBRL."""
    cik = str(cik).zfill(10)
    try:
        return _cached_json(
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
            f"companyfacts/CIK{cik}.json",
            refresh=refresh,
        )
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None  # e.g. Lehman (CIK 806085): pre-XBRL, nothing exists
        raise


def _concept_frame(facts: dict, concept: str, taxonomy: str = "us-gaap") -> pd.DataFrame:
    """
    Extract one XBRL concept as a tidy frame.

    Keeps `filed`, which is what makes point-in-time reconstruction possible:
    a fact about period-end 2022-12-31 that was not filed until 2023-03-01 must
    not be visible to an observation dated 2023-01-15.
    """
    node = facts.get("facts", {}).get(taxonomy, {}).get(concept)
    if not node:
        return pd.DataFrame(columns=["end", "val", "filed", "form", "accn"])

    rows = []
    for unit_key, observations in node.get("units", {}).items():
        if unit_key not in ("USD", "shares", "pure"):
            continue
        for obs in observations:
            # Duration facts carry "start"; we want instantaneous balances only.
            if "start" in obs and concept not in _DURATION_OK:
                continue
            rows.append(
                {
                    "end": obs.get("end"),
                    "val": obs.get("val"),
                    "filed": obs.get("filed"),
                    "form": obs.get("form"),
                    "accn": obs.get("accn"),
                }
            )
    if not rows:
        return pd.DataFrame(columns=["end", "val", "filed", "form", "accn"])

    df = pd.DataFrame(rows)
    df["end"] = pd.to_datetime(df["end"], errors="coerce")
    df["filed"] = pd.to_datetime(df["filed"], errors="coerce")
    df = df.dropna(subset=["end", "filed", "val"])
    # Same period restated across filings: keep the earliest filing, because
    # that is what the market actually saw at the time.
    df = df.sort_values(["end", "filed"]).drop_duplicates(subset=["end"], keep="first")
    return df.reset_index(drop=True)


_DURATION_OK: set[str] = set()  # balance-sheet concepts only, for now


# Debt concepts.
#
# The predecessor debt fetcher summed "Total Debt" AND its own components,
# overstating Ford's debt by 2.67x ($435.67B vs $163.30B).
# Here, components that overlap are never added: a total is used if tagged, and
# only otherwise is it built from disjoint parts.
#
# Measured coverage on a 25-firm sample (2019+), Phase 0:
#   LongTermDebt 72% | Liabilities 68% | LongTermDebtNoncurrent 60%
#   LongTermDebtCurrent 48% | ShortTermBorrowings 44% | DebtCurrent 36%
# No single concept is close to universal, hence the combination logic below.
_DEBT_CONCEPTS = [
    # short-term
    "DebtCurrent",                  # total short-term debt, if tagged
    "ShortTermBorrowings",          # disjoint part
    "LongTermDebtCurrent",          # disjoint part (current portion of LTD)
    "LongTermDebtAndCapitalLeaseObligationsCurrent",
    # long-term
    "LongTermDebtNoncurrent",
    "LongTermDebtAndCapitalLeaseObligationsNoncurrent",
    "LongTermDebt",                 # total LTD incl. current portion
    "LongTermDebtAndCapitalLeaseObligations",
    # total-liabilities route
    "Liabilities",
    "LiabilitiesAndStockholdersEquity",
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
]

# Foreign private issuers (20-F filers such as Credit Suisse) report under the
# IFRS taxonomy and expose none of the us-gaap concepts above.
_IFRS_EQUIVALENTS = {
    "Liabilities": "Liabilities",
    "LiabilitiesAndStockholdersEquity": "EquityAndLiabilities",
    "StockholdersEquity": "Equity",
    "LongTermDebt": "NoncurrentPortionOfNoncurrentBorrowings",
    "DebtCurrent": "CurrentBorrowings",
}


def _wide_concepts(facts: dict) -> pd.DataFrame:
    """Every debt-relevant concept as one wide frame keyed on (end, filed)."""
    merged: pd.DataFrame | None = None
    for concept in _DEBT_CONCEPTS:
        frame = _concept_frame(facts, concept)
        if frame.empty and concept in _IFRS_EQUIVALENTS:
            frame = _concept_frame(facts, _IFRS_EQUIVALENTS[concept], taxonomy="ifrs-full")
        if frame.empty:
            continue
        slim = frame[["end", "filed", "val"]].rename(columns={"val": concept})
        merged = slim if merged is None else merged.merge(
            slim, on=["end", "filed"], how="outer"
        )
    if merged is None:
        return pd.DataFrame()
    for concept in _DEBT_CONCEPTS:
        if concept not in merged.columns:
            merged[concept] = pd.NA
        merged[concept] = pd.to_numeric(merged[concept], errors="coerce")
    return merged.sort_values("end").reset_index(drop=True)


def _num(value) -> float | None:
    return float(value) if pd.notna(value) else None


def debt_history(cik: str, facts: dict | None = None) -> pd.DataFrame:
    """
    Point-in-time balance-sheet history for one filer.

    Returns columns:
        cik, end, filed,
        short_term_debt, long_term_debt, total_debt, kmv_barrier,
        total_liabilities, debt_source, liabilities_source

    Three default-barrier conventions are emitted for every period, so the
    choice is a published sensitivity rather than a buried assumption:

        total_debt        short-term debt + long-term debt   (full face value)
        kmv_barrier       short-term debt + 0.5 * long-term  (Moody's KMV;
                          Bharath & Shumway 2008)
        total_liabilities all liabilities (Vassalou & Xing 2004)

    `total_liabilities` has much the widest coverage because it can be derived
    from the accounting identity when not tagged directly.
    """
    if facts is None:
        facts = get_company_facts(cik)
    if not facts:
        return pd.DataFrame()

    wide = _wide_concepts(facts)
    if wide.empty:
        return pd.DataFrame()

    def _resolve(row: pd.Series) -> pd.Series:
        # ---- short-term debt -------------------------------------------
        debt_current = _num(row["DebtCurrent"])
        if debt_current is not None:
            short, short_src = debt_current, "DebtCurrent"
        else:
            stb = _num(row["ShortTermBorrowings"])
            ltc = _num(row["LongTermDebtCurrent"])
            if ltc is None:
                ltc = _num(row["LongTermDebtAndCapitalLeaseObligationsCurrent"])
            if stb is None and ltc is None:
                short, short_src = None, "missing"
            else:
                short = (stb or 0.0) + (ltc or 0.0)
                short_src = "components"

        # ---- long-term debt --------------------------------------------
        ltnc = _num(row["LongTermDebtNoncurrent"])
        if ltnc is None:
            ltnc = _num(row["LongTermDebtAndCapitalLeaseObligationsNoncurrent"])
        if ltnc is not None:
            long, long_src = ltnc, "noncurrent"
        else:
            lt_total = _num(row["LongTermDebt"]) or _num(
                row["LongTermDebtAndCapitalLeaseObligations"]
            )
            if lt_total is not None:
                # The one legitimate subtraction: LongTermDebt includes the
                # current portion, which would otherwise be counted twice.
                current_portion = _num(row["LongTermDebtCurrent"]) or 0.0
                long = max(lt_total - current_portion, 0.0)
                long_src = "total_minus_current"
            else:
                long, long_src = None, "missing"

        # ---- total liabilities -----------------------------------------
        liabilities = _num(row["Liabilities"])
        liab_src = "Liabilities"
        if liabilities is None:
            assets = _num(row["LiabilitiesAndStockholdersEquity"])
            # The identity is Assets = Liabilities + TOTAL equity, so equity
            # must include non-controlling interests. Using the parent-only
            # figure overstates liabilities by the NCI balance.
            equity = _num(
                row["StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]
            )
            if equity is None:
                equity = _num(row["StockholdersEquity"])
            if assets is not None and equity is not None:
                liabilities = assets - equity
                liab_src = "assets_minus_equity"
            else:
                liab_src = "missing"

        if short is None and long is None:
            total_debt = kmv = None
            debt_src = "missing"
        else:
            short_f, long_f = short or 0.0, long or 0.0
            total_debt = short_f + long_f
            kmv = short_f + 0.5 * long_f
            debt_src = f"st:{short_src}|lt:{long_src}"

        return pd.Series(
            {
                "short_term_debt": short,
                "long_term_debt": long,
                "total_debt": total_debt,
                "kmv_barrier": kmv,
                "total_liabilities": liabilities,
                "debt_source": debt_src,
                "liabilities_source": liab_src,
            }
        )

    resolved = wide.apply(_resolve, axis=1)
    out = pd.concat([wide[["end", "filed"]], resolved], axis=1)
    # Keep a row if EITHER barrier route succeeded.
    out = out[(out["debt_source"] != "missing") | (out["liabilities_source"] != "missing")]
    out.insert(0, "cik", str(cik).zfill(10))
    return out.reset_index(drop=True)


_SHARES_CONCEPTS = [
    "CommonStockSharesOutstanding",
    "CommonStockSharesIssued",
    "WeightedAverageNumberOfSharesOutstandingBasic",
]


def shares_history(cik: str, facts: dict | None = None) -> pd.DataFrame:
    """
    Point-in-time common shares outstanding.

    Prefers dei:EntityCommonStockSharesOutstanding (the cover-page count, which
    is dated at the filing itself and so is the most timely), then falls back
    through us-gaap balance-sheet concepts.

    This replaces a predecessor historical-data implementation that applied the
    CURRENT share count to every historical date. That is catastrophic for a firm
    that reorganised, since post-emergence share counts get multiplied by
    pre-bankruptcy prices.
    """
    if facts is None:
        facts = get_company_facts(cik)
    if not facts:
        return pd.DataFrame()

    frame = _concept_frame(facts, "EntityCommonStockSharesOutstanding", taxonomy="dei")
    concept_used = "dei:EntityCommonStockSharesOutstanding"
    if frame.empty:
        for concept in _SHARES_CONCEPTS:
            frame = _concept_frame(facts, concept)
            if not frame.empty:
                concept_used = f"us-gaap:{concept}"
                break
    if frame.empty:
        return pd.DataFrame()

    out = frame[["end", "filed", "val"]].rename(columns={"val": "shares_outstanding"})
    out = out[out["shares_outstanding"] > 0].copy()
    out["shares_concept"] = concept_used
    out["cik"] = str(cik).zfill(10)
    return out.reset_index(drop=True)


def as_of(history: pd.DataFrame, date, value_cols: list[str]) -> dict | None:
    """
    Point-in-time lookup with no look-ahead.

    Selects the most recent row whose reporting period had ENDED and whose
    filing had ALREADY BEEN MADE PUBLIC as of `date`. A balance sheet dated
    2022-12-31 but filed 2023-03-01 is invisible to an observation on
    2023-01-15, which is exactly what a real-time user of the model would face.
    """
    if history is None or history.empty:
        return None
    date = pd.Timestamp(date)
    if date.tzinfo is not None:
        date = date.tz_localize(None)

    eligible = history[(history["end"] <= date) & (history["filed"] <= date)]
    if eligible.empty:
        return None
    row = eligible.sort_values(["end", "filed"]).iloc[-1]
    out = {col: row[col] for col in value_cols if col in row.index}
    out["as_of_period_end"] = row["end"]
    out["as_of_filed"] = row["filed"]
    out["reporting_lag_days"] = int((row["filed"] - row["end"]).days)
    return out
