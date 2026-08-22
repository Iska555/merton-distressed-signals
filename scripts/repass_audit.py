"""
Re-adjudicate audit rows carrying a given reason code, in place.

Used when a resolver fix can only affect firms that landed on one code. Because
the changed gate fires exclusively on those rows, re-running them is provably
equivalent to re-running the whole audit, at a fraction of the cost -- a full
pass is ~90 minutes for 346 CIKs.

The equivalence claim is only valid when the fix is a strict relaxation or
tightening of one short-circuit. If a change could alter rows that did NOT carry
the code, run scripts.audit_resolution in full instead.

Run:  python -m scripts.repass_audit --reason NO_COMMON_EQUITY
"""
from __future__ import annotations

import argparse

import pandas as pd

from src.config import DATA_PROCESSED
from src.data import identity
from scripts.audit_resolution import sic_division


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    path = DATA_PROCESSED / "resolution_audit.csv"
    frame = pd.read_csv(path, dtype=str)
    target = frame[frame["reason_code"] == args.reason]
    if target.empty:
        print(f"No rows with reason_code == {args.reason}")
        return 0

    print(f"Re-adjudicating {len(target)} rows with {args.reason}...")
    changes: list[tuple[str, str, str]] = []

    for position, row in enumerate(target.itertuples(index=False), start=1):
        cik = str(row.cik).zfill(10)
        try:
            ident = identity.resolve(
                cik, event_date=row.event_date, name=row.company
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  {cik}: {type(exc).__name__}")
            continue

        mask = frame["cik"] == row.cik
        old = row.reason_code
        frame.loc[mask, "resolved"] = str(ident.resolved)
        frame.loc[mask, "ticker"] = ident.ticker
        frame.loc[mask, "provenance"] = ident.provenance
        frame.loc[mask, "reason_code"] = ident.reason_code
        frame.loc[mask, "exclusion_family"] = identity.exclusion_family(
            ident.reason_code
        )
        frame.loc[mask, "xbrl_instances_seen"] = ident.xbrl_instances_seen
        frame.loc[mask, "listing_start"] = ident.listing_start
        frame.loc[mask, "listing_end"] = ident.listing_end
        frame.loc[mask, "notes"] = " | ".join(ident.notes[:3])

        if ident.reason_code != old:
            changes.append((str(row.company)[:40], old, ident.reason_code))
        if position % 10 == 0:
            print(f"  {position}/{len(target)}", flush=True)

    print(f"\n{len(changes)} of {len(target)} rows changed code:")
    summary: dict[str, int] = {}
    for _, _, new in changes:
        summary[new] = summary.get(new, 0) + 1
    for code, n in sorted(summary.items(), key=lambda kv: -kv[1]):
        print(f"   {args.reason} -> {code:26s} {n}")

    resolved_now = sum(1 for _, _, new in changes if new.startswith("RESOLVED"))
    print(f"\n{resolved_now} newly resolved.")

    if args.dry_run:
        print("Dry run; nothing written.")
        return 0

    frame.to_csv(path, index=False)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
