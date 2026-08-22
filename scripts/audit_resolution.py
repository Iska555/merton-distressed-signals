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

from src.analysis import crosstabs as X
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
    combined = pd.concat(frames, ignore_index=True)

    # Spec T1: event date is the EARLIEST Item 1.03 filing PER CIK. Dedup must
    # be global, not per-year: Walter Investment filed in 2017 and again in
    # 2018, then again in 2019 under its new name Ditech Holding, all on CIK
    # 0001040719. Per-year dedup let one registrant enter the cohort three
    # times, where it would be double-counted and could consume controls twice.
    combined = combined.sort_values(["cik", "filed_date"])

    # Spec 1.2.2 -- Chapter 22. A firm filing Item 1.03 more than once has gone
    # bankrupt twice; it is not a duplicate row. Walter Investment (2017, 2018)
    # re-emerged and filed again as Ditech Holding (2019), all on CIK
    # 0001040719. The FIRST filing is the event, because the research question
    # is about detecting the ONSET of distress; keeping the last would discard
    # exactly the transition under study. Subsequent filings are recorded.
    counts = combined.groupby("cik")["filed_date"].agg(["count", list])
    first = combined.drop_duplicates(subset="cik", keep="first").set_index("cik")
    first["n_bankruptcy_events"] = counts["count"]
    first["subsequent_event_dates"] = counts["list"].apply(
        # filed_date may arrive as Timestamp or str depending on the FTS page;
        # coerce before joining. The smoke test missed this because it happened
        # to contain no Chapter 22 firms, so the join never saw a real element.
        lambda dates: "|".join(str(d)[:10] for d in sorted(dates)[1:])
    )
    first["is_chapter_22"] = first["n_bankruptcy_events"] > 1
    return first.reset_index()


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
                "exclusion_family": identity.exclusion_family(ident.reason_code),
                "n_bankruptcy_events": getattr(row, "n_bankruptcy_events", 1),
                "is_chapter_22": getattr(row, "is_chapter_22", False),
                "subsequent_event_dates": getattr(row, "subsequent_event_dates", ""),
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

    print("\n-- exclusions by family (spec 8.1) --")
    families = frame["exclusion_family"].value_counts()
    for family, n in families.items():
        print(f"   {str(family):24s} {n:5d}  ({n / total:5.1%})")
    unavail = int((frame["exclusion_family"] == "data_unavailability").sum())
    inapp = int((frame["exclusion_family"] == "model_inapplicability").sum())
    print(f"   -> {unavail} excluded by SOURCE LIMITS (a limitation)")
    print(f"   -> {inapp} excluded as NOT MERTON OBJECTS (a scope definition)")
    if "is_chapter_22" in frame:
        ch22 = int(frame["is_chapter_22"].sum())
        print(f"\n-- Chapter 22 (spec 1.2.2): {ch22} of {total} "
              f"({ch22 / total:.1%}) filed Item 1.03 more than once --")

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

    # Every cross-tab is reported WITHIN era as well as pooled. Era is the
    # dominant axis here -- two filing-rule changes drive resolution from 13%
    # to 69% across the window -- so a pooled gradient in size or sector is
    # era measured a second time until conditioning shows otherwise. A pooled
    # size gradient published at N=190 turned out to be exactly that.
    strata = X.normalise(frame)

    print("\n-- resolution by SIC division, WITHIN era --")
    print(X.format_crosstab(X.conditional_crosstab(strata, "sic_division")))

    print("\n-- resolution by public-float band, WITHIN era --")
    print(X.format_crosstab(
        X.conditional_crosstab(strata, "float_band", X.FLOAT_ORDER)))

    avail = X.float_availability(strata)
    if avail:
        print("\n-- is 'reports no public float' just 'has no XBRL'? --")
        for g in avail["grid"]:
            print(f"   any_xbrl={str(g['any_xbrl']):5s} n={g['n']:4d}  "
                  f"reports float {g['reports_float']:4d} ({g['share']:5.1%})")
        print(f"   the two agree on {avail['agreement']:.1%} of rows. "
              "dei:EntityPublicFloat is an XBRL tag, so a pre-XBRL filer lands "
              "in 'none reported' by construction, not by being small.")

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
