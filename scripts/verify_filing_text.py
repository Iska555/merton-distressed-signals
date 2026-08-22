"""
Hand-verification sample for symbol resolution.

The listing-window check catches a symbol from the wrong ERA. It does not catch
a symbol that is contemporaneous but belongs to the wrong COMPANY -- a peer
named in a comparison, a subsidiary, a general partner, a predecessor.
Extraction from prose produces that class of error and the window check waves
it through.

Three design points, each learned the hard way:

**Sample size.** An earlier run measured 2 errors in 14 and asked whether that
cleared 5%. It cannot: at n=14, 2 errors gives a 95% interval of roughly
1.8%-42.8%, and even a clean 0-in-14 has an upper bound near 19%. Nothing at
that size distinguishes 3% from 30%. Default is now 80.

**Stratification.** `filing_text` is the risky tier and pre-2019 prose is the
most variable, because the SEC's 2019 cover-page rule standardised the later
format. A pooled sample dominated by clean recent XBRL resolutions understates
the error rate in precisely the stratum where it is highest. Strata are drawn
and reported separately.

**The number is a statistic, not a gate.** Fix once, measure on a fresh sample
that informed no fix, and publish whatever comes out. Fixing and re-measuring
on the same firms until the number looks acceptable is threshold-mining against
the test set -- the identical failure mode this project exists to avoid, and
harder to see because it feels like diligence. A disclosed 8% is worth more
than a 4% obtained after four rounds of fitting, because the second number is
not really 4% and nobody can say what it is.

Run:  python -m scripts.verify_filing_text [--n 80] [--seed 20260819]
Out:  data/processed/filing_text_verification.csv
"""
from __future__ import annotations

import argparse
import math
import re

import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, RANDOM_SEED
from src.data import identity

CONTEXT = 150


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """
    Wilson score interval.

    Used rather than the normal approximation because the counts here are small
    and the proportions near zero, where the normal interval famously goes
    negative and understates the upper bound -- the bound that matters when
    asking whether an error rate could be unacceptably high.
    """
    if n == 0:
        return (float("nan"), float("nan"))
    p = successes / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


_STOP = {"inc", "corp", "corporation", "company", "co", "llc", "lp", "ltd",
         "holdings", "holding", "group", "the", "of", "and", "plc", "sa",
         "nv", "ag", "trust", "partners", "international", "industries", "cik"}


def _tokens(name: str) -> set[str]:
    words = re.findall(r"[A-Za-z]+", (name or "").lower())
    return {w for w in words if w not in _STOP and len(w) > 2}


def _plausible(symbol: str, name: str) -> str:
    """Sorts attention only. Never decides."""
    if not symbol or symbol == "None" or not name:
        return "unknown"
    tokens = _tokens(name)
    if not tokens:
        return "unknown"
    letters = symbol.rstrip("Q").lower()
    if any(w.startswith(letters[:3]) for w in tokens if len(letters) >= 3):
        return "likely"
    initials = {w[0] for w in tokens}
    if all(c in initials for c in letters):
        return "likely"
    return "CHECK"


def stratified_sample(audit: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    """
    Draw separately from each (tier x era) stratum.

    Equal allocation across strata rather than proportional: the point is to
    measure the risky strata precisely, not to mirror the population.
    """
    resolved = audit[audit["reason_code"].str.startswith("RESOLVED", na=False)].copy()
    if resolved.empty:
        raise SystemExit("No resolutions in the audit.")

    resolved["tier"] = np.where(
        resolved["reason_code"] == "RESOLVED_FILING_TEXT", "filing_text", "xbrl")
    resolved["era"] = np.where(
        pd.to_numeric(resolved["event_year"], errors="coerce") >= 2019,
        "post_2019", "pre_2019")
    resolved["stratum"] = resolved["tier"] + " / " + resolved["era"]

    strata = sorted(resolved["stratum"].unique())
    rng = np.random.default_rng(seed)

    # Equal allocation, then redistribute the shortfall.
    #
    # A first run of this asked for 80 and returned 69 without saying so: one
    # stratum, filing_text/post_2019, contains only 9 resolutions in the whole
    # pool, and `min(per, len(rows))` silently absorbed the difference. A
    # sample size that quietly becomes whatever the smallest stratum permits is
    # the same failure as an unreported exclusion. The shortfall now moves to
    # the strata that still have capacity, and the caller is told when even
    # that cannot reach n.
    #
    # The top-up draws from rows NOT already picked, so enlarging n only adds
    # firms. It never re-rolls a sample that has been looked at, which would be
    # indistinguishable from redrawing until the number is agreeable.
    per = max(1, n // len(strata))
    picks: dict[str, pd.DataFrame] = {}
    for stratum in strata:
        rows = resolved[resolved["stratum"] == stratum]
        take = min(per, len(rows))
        idx = rng.choice(len(rows), size=take, replace=False)
        picks[stratum] = rows.iloc[sorted(idx)]

    shortfall = n - sum(len(p) for p in picks.values())
    while shortfall > 0:
        room = {s: resolved[resolved["stratum"] == s].drop(picks[s].index)
                for s in strata}
        room = {s: rows for s, rows in room.items() if len(rows)}
        if not room:
            print(f"  only {n - shortfall} resolutions exist to sample; "
                  f"asked for {n}")
            break
        for stratum in sorted(room, key=lambda s: -len(room[s])):
            if shortfall <= 0:
                break
            rows = room[stratum]
            take = min(max(1, shortfall // len(room)), len(rows), shortfall)
            idx = rng.choice(len(rows), size=take, replace=False)
            picks[stratum] = pd.concat([picks[stratum], rows.iloc[sorted(idx)]])
            shortfall -= take

    return pd.concat([picks[s] for s in strata], ignore_index=True)


def verify(sample: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total = len(sample)
    for i, record in enumerate(sample.itertuples(index=False), start=1):
        cik, name = record.cik, record.company
        event = record.event_date

        # Re-resolve through the PIPELINE, not the raw extractor, so the
        # measured rate describes what the study will actually use.
        try:
            ident = identity.resolve(cik, event_date=event, name=str(name))
        except Exception as exc:  # noqa: BLE001
            ident = identity.Identity(cik=cik, name=name,
                                      reason_code=f"ERROR:{type(exc).__name__}")
        symbol = ident.ticker

        sentence, source_doc = "", ""
        if symbol:
            for document in identity._fts_documents(cik)[:3]:
                try:
                    raw = identity._get(
                        f"https://www.sec.gov/Archives/edgar/data/"
                        f"{int(str(cik).lstrip('0'))}/"
                        f"{document['accession'].replace('-', '')}/{document['filename']}"
                    )
                except Exception:  # noqa: BLE001
                    continue
                text = identity._strip_markup(raw.decode("utf-8", "replace"))
                for pattern in identity._TEXT_SYMBOL_PATTERNS:
                    for match in pattern.finditer(text):
                        if match.group(1).strip().upper() == symbol.upper().rstrip("Q"):
                            sentence = text[max(0, match.start() - CONTEXT):
                                            match.end() + 50].strip()
                            source_doc = f"{document['accession']} {document['filename']}"
                            break
                    if sentence:
                        break
                if sentence:
                    break

        window = identity.listing_window(str(symbol)) if symbol else None
        rows.append({
            "cik": cik, "company": name, "event_date": event,
            "stratum": record.stratum, "tier": record.tier, "era": record.era,
            "symbol_resolved": symbol,
            "symbol_in_audit": record.ticker,
            "reason_code": ident.reason_code,
            "heuristic": _plausible(str(symbol), str(name)),
            "listing_start": (window or {}).get("start"),
            "listing_end": (window or {}).get("end"),
            "source_document": source_doc,
            "sentence": sentence,
            "human_verdict": "",
        })
        if i % 10 == 0:
            print(f"  {i}/{total}", flush=True)
    return pd.DataFrame(rows)


def report(frame: pd.DataFrame) -> None:
    print("\n" + "=" * 78)
    print("VERIFICATION SAMPLE -- read the sentences, fill in human_verdict")
    print("=" * 78)

    for record in frame.itertuples(index=False):
        flag = "  " if record.heuristic == "likely" else ">>"
        print(f"\n{flag} {str(record.company)[:50]}  [{record.stratum}]")
        print(f"     resolved {record.symbol_resolved}  ({record.reason_code})"
              f"   was {record.symbol_in_audit}")
        if record.sentence:
            print(f'     "...{record.sentence[-165:]}"')
        else:
            print("     (sentence not recovered -- verify manually)")

    print("\n" + "=" * 78)
    print("HEURISTIC FLAGS BY STRATUM (not verdicts -- they sort attention)")
    print("=" * 78)
    for stratum, chunk in frame.groupby("stratum"):
        flagged = int((chunk["heuristic"] == "CHECK").sum())
        low, high = wilson_interval(flagged, len(chunk))
        print(f"  {stratum:26s} n={len(chunk):3d}  flagged={flagged:3d} "
              f"({flagged / len(chunk):5.1%})  95% CI [{low:.1%}, {high:.1%}]")

    flagged = int((frame["heuristic"] == "CHECK").sum())
    low, high = wilson_interval(flagged, len(frame))
    print(f"  {'POOLED':26s} n={len(frame):3d}  flagged={flagged:3d} "
          f"({flagged / len(frame):5.1%})  95% CI [{low:.1%}, {high:.1%}]")
    print("\n  Pooled figures describe no single stratum. Report strata.")
    print("  A flag is a name-similarity mismatch and nothing more. Many correct")
    print("  tickers are not derivable from the company name, so a high flag")
    print("  rate is not a high error rate.")
    report_verdicts(frame)


VERDICTS = DATA_PROCESSED.parent / "verification_verdicts.csv"

#: An adjudicated row is one of these. "unverifiable" is a verdict, not a
#: missing value: it means the filings do not settle the question, which is a
#: real outcome and is reported rather than dropped.
VERDICT_VALUES = ("correct", "wrong_company", "wrong_era", "unverifiable")
ERROR_VERDICTS = ("wrong_company", "wrong_era")


def attach_verdicts(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Join hand-adjudicated verdicts, if any have been recorded.

    Kept in a separate committed file rather than in the generated CSV, because
    re-running the extraction would otherwise wipe the adjudication -- and the
    temptation would then be to re-adjudicate against a number already seen.
    """
    frame = frame.copy()
    frame["human_verdict"] = ""
    frame["verdict_note"] = ""
    if not VERDICTS.exists():
        return frame
    verdicts = pd.read_csv(VERDICTS, dtype=str).set_index("cik")
    unknown = set(verdicts["verdict"].dropna()) - set(VERDICT_VALUES)
    if unknown:
        raise SystemExit(f"Unknown verdict(s) in {VERDICTS.name}: {sorted(unknown)}")
    frame["human_verdict"] = frame["cik"].map(verdicts["verdict"]).fillna("")
    if "note" in verdicts.columns:
        frame["verdict_note"] = frame["cik"].map(verdicts["note"]).fillna("")
    return frame


def report_verdicts(frame: pd.DataFrame) -> None:
    """The published statistic. Strata first; the pooled line describes nobody."""
    adjudicated = frame[frame["human_verdict"].isin(VERDICT_VALUES)]
    if adjudicated.empty:
        print("\n  No hand verdicts recorded. The flag rate above is NOT an error"
              "\n  rate. Fill in data/verification_verdicts.csv and re-run.")
        return

    print("\n" + "=" * 78)
    print("HAND-ADJUDICATED ERROR RATE -- this is the published statistic")
    print("=" * 78)

    def line(label: str, chunk: pd.DataFrame) -> None:
        errors = int(chunk["human_verdict"].isin(ERROR_VERDICTS).sum())
        unver = int((chunk["human_verdict"] == "unverifiable").sum())
        low, high = wilson_interval(errors, len(chunk))
        print(f"  {label:26s} n={len(chunk):3d}  errors={errors:3d} "
              f"({errors / len(chunk):5.1%})  95% CI [{low:.1%}, {high:.1%}]"
              f"   unverifiable={unver}")

    for stratum, chunk in adjudicated.groupby("stratum"):
        line(str(stratum), chunk)
    line("POOLED", adjudicated)

    missing = len(frame) - len(adjudicated)
    if missing:
        print(f"\n  {missing} of {len(frame)} rows not yet adjudicated.")
    print(f"\n  Verdicts: {adjudicated['human_verdict'].value_counts().to_dict()}")
    print("  A statistic, not a gate. Published whatever it says, and NOT")
    print("  re-measured on these same firms after a fix.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=80)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = parser.parse_args()

    audit_path = DATA_PROCESSED / "resolution_audit.csv"
    if not audit_path.exists():
        raise SystemExit("Run scripts.audit_resolution first.")

    audit = pd.read_csv(audit_path, dtype=str)
    sample = stratified_sample(audit, args.n, args.seed)
    print(f"Sampled {len(sample)} across {sample['stratum'].nunique()} strata "
          f"(seed {args.seed}); resolving...", flush=True)

    frame = verify(sample)
    frame = attach_verdicts(frame)
    report(frame)

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    out = DATA_PROCESSED / "filing_text_verification.csv"
    frame.to_csv(out, index=False)
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
