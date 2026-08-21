"""
Hand-verification sample for the `filing_text` provenance tier.

The listing-window check catches a symbol from the wrong era. It does NOT catch
a symbol that is contemporaneous but belongs to the wrong company -- a peer
named in a comparison, a subsidiary, a predecessor, an exchange-listed
affiliate. Extraction from megabytes of prose produces exactly that class of
error, and the window check waves it through.

So a random seeded sample is pulled, each resolution is printed with the
surrounding sentence and the registrant name, and a human confirms it by eye.
Above roughly 5% error the extraction rule needs tightening before the tier is
trusted, because it currently carries about a third of the sample.

Run:  python -m scripts.verify_filing_text [--n 20] [--seed 20260819]
Out:  data/processed/filing_text_verification.csv
"""
from __future__ import annotations

import argparse
import json
import re

import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, RANDOM_SEED
from src.data import identity

CONTEXT = 130


def _registrant_tokens(name: str) -> set[str]:
    """Meaningful words of a company name, for the initials heuristic."""
    stop = {"inc", "corp", "corporation", "company", "co", "llc", "lp", "ltd",
            "holdings", "holding", "group", "the", "of", "and", "plc", "sa",
            "nv", "ag", "trust", "partners", "international", "industries"}
    words = re.findall(r"[A-Za-z]+", (name or "").lower())
    return {w for w in words if w not in stop and len(w) > 1}


def _plausible(symbol: str, name: str) -> str:
    """
    Cheap heuristic, to focus the human's attention rather than replace it.

    A symbol whose letters open the registrant's words is very likely right;
    anything else needs a look. Never used to filter -- only to sort.
    """
    if not symbol or not name:
        return "unknown"
    tokens = _registrant_tokens(name)
    if not tokens:
        return "unknown"
    initials = "".join(sorted({w[0] for w in tokens}))
    letters = symbol.rstrip("Q").lower()
    if any(w.startswith(letters[:3]) for w in tokens if len(letters) >= 3):
        return "likely"
    if all(c in initials for c in letters):
        return "likely"
    return "CHECK"


def sample_and_verify(n: int, seed: int) -> pd.DataFrame:
    audit_path = DATA_PROCESSED / "resolution_audit.csv"
    if not audit_path.exists():
        raise SystemExit("Run scripts.audit_resolution first.")

    audit = pd.read_csv(audit_path, dtype=str)
    tier = audit[audit["reason_code"] == "RESOLVED_FILING_TEXT"].copy()
    if tier.empty:
        raise SystemExit("No filing_text resolutions in the audit.")

    rng = np.random.default_rng(seed)
    take = min(n, len(tier))
    picks = rng.choice(len(tier), size=take, replace=False)
    sample = tier.iloc[sorted(picks)].reset_index(drop=True)

    print("=" * 78)
    print(f"FILING_TEXT VERIFICATION -- {take} of {len(tier)} resolutions, seed {seed}")
    print("Confirm each by eye. The sentence is quoted verbatim from the filing.")
    print("=" * 78)

    rows = []
    for i, record in enumerate(sample.itertuples(index=False), start=1):
        cik, symbol, name = record.cik, record.ticker, record.company
        # Re-resolve with CURRENT code rather than trusting the stored symbol,
        # so the measured error rate describes the tier as it stands now.
        current = [sym for sym, _ in identity.ticker_from_filing_text(
            cik, registrant=str(name))]
        symbol = current[0] if current else None
        documents = identity._fts_documents(cik)
        sentence, source_doc = "", ""

        for document in documents[:3]:
            accession = document["accession"].replace("-", "")
            try:
                raw = identity._get(
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{int(cik.lstrip('0'))}/{accession}/{document['filename']}"
                )
            except Exception:  # noqa: BLE001
                continue
            text = identity._strip_markup(raw.decode("utf-8", "replace"))
            for pattern in identity._TEXT_SYMBOL_PATTERNS:
                match = pattern.search(text)
                if match and match.group(1).strip().upper() == str(symbol).upper():
                    start = max(0, match.start() - CONTEXT)
                    sentence = text[start:match.end() + 40].strip()
                    source_doc = f"{document['accession']} {document['filename']}"
                    break
            if sentence:
                break

        verdict = _plausible(str(symbol), str(name))
        window = identity.listing_window(str(symbol)) or {}
        rows.append({
            "cik": cik, "company": name, "symbol": symbol,
            "symbol_in_audit": record.ticker,
            "all_current_candidates": "|".join(current),
            "public_float_usd": record.public_float_usd,
            "heuristic": verdict,
            "listing_start": window.get("start"), "listing_end": window.get("end"),
            "exchange": window.get("exchange"),
            "source_document": source_doc,
            "sentence": sentence,
            "human_verdict": "",     # filled in by hand
        })

        flag = "  " if verdict == "likely" else ">>"
        print(f"\n{flag} [{i}/{take}] {str(name)[:52]}")
        print(f"     symbol {symbol}   heuristic={verdict}   "
              f"listed {window.get('start')} -> {window.get('end')} "
              f"({window.get('exchange')})")
        print(f"     doc: {source_doc or 'NOT RE-FOUND'}")
        if sentence:
            print(f'     "...{sentence[-190:]}"')
        else:
            print("     (sentence not recovered -- verify manually)")

    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = parser.parse_args()

    frame = sample_and_verify(args.n, args.seed)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    out = DATA_PROCESSED / "filing_text_verification.csv"
    frame.to_csv(out, index=False)

    flagged = int((frame["heuristic"] == "CHECK").sum())
    missing = int((frame["source_document"] == "").sum())
    print("\n" + "=" * 78)
    print(f"{len(frame)} sampled. {flagged} flagged CHECK by heuristic, "
          f"{missing} sentence not re-found.")
    print(f"Wrote {out}")
    print("The heuristic sorts attention; it does not decide. Read the "
          "sentences and fill in human_verdict.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
