"""
Resolution-rate audit for the treatment cohort.

Answers two questions that determine what this study can claim:

  1. What is the effective earliest resolvable event date? The identity
     resolver reads dei:TradingSymbol out of XBRL instance documents. XBRL was
     phased in for US filers between 2009 and 2011, so any firm that delisted
     before then is structurally invisible -- not missing from one vendor, but
     absent from the only durable record of what it traded as.

  2. Is exclusion random? If resolution failure correlates with size, sector or
     era, the treatment cohort is a biased sample of defaults and every
     downstream number inherits that bias.

Size is measured from EDGAR's dei:EntityPublicFloat, deliberately NOT from
prices: using prices to explain why prices are missing would condition on the
very thing under study.

Run:  python -m scripts.audit_resolution [--start 2004] [--end 2024] [--per-year 12]
Out:  data/processed/resolution_audit.csv
      data/processed/resolution_by_year.csv
"""
from __future__ import annotations

import argparse
import sys
import time

import pandas as pd

from src.config import DATA_PROCESSED, RANDOM_SEED
from src.data import edgar, identity

# SIC division boundaries (SEC's own scheme), used for the sector cross-tab.
SIC_DIVISIONS = [
    (100, 999, "Agriculture, Forestry, Fishing"),
    (1000, 1499, "Mining"),
    (1500, 1799, "Construction"),
    (2000, 3999, "Manufacturing"),
    (4000, 4999, "Transport & Utilities"),
    (5000, 5199, "Wholesale Trade"),
    (5200, 5999, "Retail Trade"),
    (6000, 6799, "Finance, Insurance, Real Estate"),
    (7000, 8999, "Services"),
    (9100, 9999, "Public Administration"),
]


def sic_division(sic) -> str:
    try:
        code = int(sic)
    except (TypeError, ValueError):
        return "Unknown"
    for low, high, label in SIC_DIVISIONS:
        if low <= code <= high:
            return label
    return "Unknown"


def _concept(cik: str, taxonomy: str, concept: str) -> list | None:
    """
    One XBRL concept via the companyconcept endpoint.

    Deliberately not companyfacts: that returns every concept a filer has ever
    tagged (multi-megabyte, ~2MB+ each) and the audit needs two fields. Using
    companyconcept cut the audit's transfer volume by well over an order of
    magnitude.
    """
    cik = str(cik).zfill(10)
    try:
        payload = edgar._cached_json(
            f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{concept}.json",
            f"concept/{cik}_{taxonomy}_{concept}.json",
        )
    except Exception:  # noqa: BLE001 - 404 means the filer never tagged it
        return None
    observations = []
    for unit, values in payload.get("units", {}).items():
        if unit == "USD":
            observations.extend(values)
    return observations or None


def public_float(cik: str) -> float | None:
    """
    Latest reported public float, as a price-independent size proxy.

    dei:EntityPublicFloat is a 10-K cover-page fact, so it exists for filers
    whose price history has vanished. That is exactly the population whose size
    distribution we need in order to test whether exclusion is size-related.
    """
    observations = _concept(cik, "dei", "EntityPublicFloat")
    if not observations:
        return None
    observations.sort(key=lambda o: (o.get("end", ""), o.get("filed", "")))
    return float(observations[-1].get("val") or 0) or None


def has_xbrl_fundamentals(cik: str) -> bool:
    """Cheap probe: does this filer expose usable balance-sheet XBRL at all?"""
    for taxonomy, concept in (("us-gaap", "Liabilities"),
                              ("us-gaap", "LiabilitiesAndStockholdersEquity")):
        if _concept(cik, taxonomy, concept):
            return True
    return False


def collect_candidates(start_year: int, end_year: int, per_year: int) -> pd.DataFrame:
    """Bankruptcy candidates from 8-K Item 1.03, one row per CIK."""
    frames = []
    for year in range(start_year, end_year + 1):
        filings = edgar.search_bankruptcy_filings(
            f"{year}-01-01", f"{year}-12-31",
            max_pages_per_window=max(2, (per_year // 10) + 2),
        )
        frame = edgar.first_filing_per_cik(filings)
        if frame.empty:
            continue
        frame["event_year"] = year
        # Deterministic subsample: sorted by CIK, then evenly spaced, so the
        # audit is reproducible and not biased toward early-in-year filings.
        frame = frame.sort_values("cik").reset_index(drop=True)
        if len(frame) > per_year:
            step = len(frame) / per_year
            picks = [int(i * step) for i in range(per_year)]
            frame = frame.iloc[picks].reset_index(drop=True)
        frames.append(frame)
        print(f"  {year}: {len(frame)} candidates sampled", flush=True)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def audit(start_year: int, end_year: int, per_year: int) -> pd.DataFrame:
    print(f"Collecting 8-K Item 1.03 candidates, {start_year}-{end_year}...", flush=True)
    candidates = collect_candidates(start_year, end_year, per_year)
    if candidates.empty:
        return pd.DataFrame()

    print(f"\nResolving {len(candidates)} CIKs...", flush=True)
    rows = []
    for position, row in enumerate(candidates.itertuples(index=False), start=1):
        cik = row.cik
        event = pd.Timestamp(row.filed_date)
        try:
            ident = identity.resolve(cik, event_date=event, name=row.company)
        except Exception as exc:  # noqa: BLE001 - one bad filer must not stop the audit
            ident = identity.Identity(
                cik=cik, name=row.company, reason_code="ERROR",
                notes=(f"{type(exc).__name__}: {exc}",),
            )
        try:
            float_usd = public_float(cik)
        except Exception:  # noqa: BLE001
            float_usd = None

        has_facts = has_xbrl_fundamentals(cik)

        rows.append(
            {
                "cik": cik,
                "company": row.company,
                "event_date": event.date().isoformat(),
                "event_year": row.event_year,
                "sic": row.sic,
                "sic_division": sic_division(row.sic),
                "resolved": ident.resolved,
                "ticker": ident.ticker,
                "provenance": ident.provenance,
                "reason_code": ident.reason_code,
                "xbrl_instances_seen": ident.xbrl_instances_seen,
                "has_xbrl_fundamentals": has_facts,
                "public_float_usd": float_usd,
                "listing_start": ident.listing_start,
                "listing_end": ident.listing_end,
                "notes": " | ".join(ident.notes[:3]),
            }
        )
        if position % 10 == 0:
            done = sum(1 for r in rows if r["resolved"])
            print(f"  {position}/{len(candidates)} ... {done} resolved so far", flush=True)

    frame = pd.DataFrame(rows)

    # Size deciles computed only where a float is reported, so firms without
    # one are visible as their own group rather than silently pooled.
    with_float = frame["public_float_usd"].notna()
    frame["size_decile"] = pd.NA
    if with_float.sum() >= 10:
        frame.loc[with_float, "size_decile"] = pd.qcut(
            frame.loc[with_float, "public_float_usd"], 10,
            labels=list(range(1, 11)), duplicates="drop",
        )
    return frame


def summarise(frame: pd.DataFrame) -> None:
    total = len(frame)
    resolved = int(frame["resolved"].sum())
    print("\n" + "=" * 74)
    print(f"RESOLUTION AUDIT: {resolved}/{total} resolved ({resolved / total:.1%})")
    print("=" * 74)

    print("\n-- exclusion reason codes --")
    counts = frame["reason_code"].value_counts()
    for code, n in counts.items():
        print(f"   {str(code):26s} {n:5d}  ({n / total:5.1%})")

    print("\n-- resolution rate by event year --")
    by_year = frame.groupby("event_year").agg(
        n=("cik", "size"),
        resolved=("resolved", "sum"),
        any_xbrl=("xbrl_instances_seen", lambda s: int((s > 0).sum())),
    )
    by_year["rate"] = by_year["resolved"] / by_year["n"]
    for year, row in by_year.iterrows():
        bar = "#" * int(row["rate"] * 40)
        print(f"   {year}  n={int(row['n']):3d}  resolved={int(row['resolved']):3d} "
              f"({row['rate']:5.1%})  xbrl_present={int(row['any_xbrl']):3d}  {bar}")

    resolvable = by_year[by_year["resolved"] > 0]
    if not resolvable.empty:
        print(f"\n   EFFECTIVE EARLIEST RESOLVABLE EVENT YEAR: {int(resolvable.index.min())}")

    print("\n-- resolution rate by SIC division --")
    by_sector = frame.groupby("sic_division").agg(
        n=("cik", "size"), resolved=("resolved", "sum")
    )
    by_sector["rate"] = by_sector["resolved"] / by_sector["n"]
    for sector, row in by_sector.sort_values("rate", ascending=False).iterrows():
        print(f"   {sector:34s} n={int(row['n']):4d}  {row['rate']:6.1%}")

    if frame["size_decile"].notna().any():
        print("\n-- resolution rate by public-float decile (1=smallest) --")
        by_size = frame.dropna(subset=["size_decile"]).groupby("size_decile", observed=True).agg(
            n=("cik", "size"), resolved=("resolved", "sum")
        )
        by_size["rate"] = by_size["resolved"] / by_size["n"]
        for decile, row in by_size.iterrows():
            print(f"   decile {decile:>2}  n={int(row['n']):4d}  {row['rate']:6.1%}")
        missing = frame["public_float_usd"].isna().sum()
        print(f"   (no public float reported: {missing} firms, "
              f"{frame.loc[frame['public_float_usd'].isna(), 'resolved'].mean():.1%} resolved)")

    return by_year


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=2004)
    parser.add_argument("--end", type=int, default=2024)
    parser.add_argument("--per-year", type=int, default=12)
    args = parser.parse_args()

    started = time.time()
    frame = audit(args.start, args.end, args.per_year)
    if frame.empty:
        print("No candidates found.", file=sys.stderr)
        return 1

    by_year = summarise(frame)

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    frame.sort_values(["event_year", "cik"]).to_csv(
        DATA_PROCESSED / "resolution_audit.csv", index=False
    )
    by_year.to_csv(DATA_PROCESSED / "resolution_by_year.csv")
    print(f"\nWrote data/processed/resolution_audit.csv ({len(frame)} rows)")
    print(f"Elapsed: {time.time() - started:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
