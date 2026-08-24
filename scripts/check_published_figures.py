"""
Assert that the numbers written in prose still match the committed data.

Tests verify that the code does what the code intends. They do not verify that
a sentence in the README is still true after a re-run, and that failure has
already happened here twice: a sector table in RESOLUTION_AUDIT.md kept
pre-repass figures while the site rebuilt correctly from the CSV, and two
claims about within-era orderings were written from a glance at a console table
and were wrong -- "four of five" for a thing that is five of five, "three of
four" for a thing that is two of four.

Every claim below is stated the way it appears in visible UI or in the docs,
next to the computation that has to reproduce it. When a re-run moves a number,
this script says which sentence is now false and where it lives.

Run:  python -m scripts.check_published_figures
Exit: 0 if every published figure reproduces, 1 otherwise.
"""
from __future__ import annotations

import sys

import pandas as pd

from src.analysis import crosstabs as X
from src.config import DATA_PROCESSED

FIN = "Finance, Insurance, Real Estate"


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.checked = 0

    def claim(self, holds: bool, statement: str, where: str) -> None:
        self.checked += 1
        if holds:
            print(f"  ok    {statement}")
        else:
            self.failures.append(f"{statement}  [{where}]")
            print(f"  FALSE {statement}\n        appears in: {where}")


def rate(chunk: pd.DataFrame) -> float:
    return float(chunk["resolved"].mean()) if len(chunk) else float("nan")


def check(frame: pd.DataFrame) -> Report:
    d = X.normalise(frame)
    r = Report()

    print("\n-- headline --")
    r.claim(len(d) == 346 and int(d["resolved"].sum()) == 149,
            "149 of 346 candidates resolved (43.1%)",
            "README, /measurement, RESOLUTION_AUDIT.md §1")

    print("\n-- the era gradient is monotone --")
    rates = [rate(d[d["era"] == label]) for _, _, label in X.ERAS]
    r.claim(rates == sorted(rates),
            "resolution rises monotonically across all five eras",
            "README finding 1, /measurement, DECISIONS.md D5")
    r.claim(abs(rates[0] - 0.128) < 0.001 and abs(rates[-1] - 0.687) < 0.001,
            "the era gradient runs 12.8% to 68.7%",
            "README, /data, /measurement, RESOLUTION_AUDIT.md §2")

    print("\n-- float availability is an XBRL artefact --")
    avail = X.float_availability(d)
    grid = {g["any_xbrl"]: g for g in avail["grid"]}
    r.claim(abs(avail["agreement"] - 0.867) < 0.001,
            "float availability and XBRL presence agree on 86.7% of candidates",
            "README, /measurement, RESOLUTION_AUDIT.md §5.1")
    r.claim(grid[True]["n"] == 279 and grid[True]["reports_float"] == 243,
            "279 filers have XBRL; 243 of them (87.1%) report a float",
            "/measurement, RESOLUTION_AUDIT.md §5.1")
    r.claim(grid[False]["n"] == 67 and grid[False]["reports_float"] == 10,
            "67 filers have no XBRL; only 10 of them (14.9%) report a float",
            "/measurement, RESOLUTION_AUDIT.md §5.1")

    print("\n-- size: no ordering survives conditioning --")
    bands = X.FLOAT_ORDER[:3]
    readable = []
    for _, _, era in X.ERAS:
        cells = [X.cell(d[(d["era"] == era) & (d["float_band"] == b)]) for b in bands]
        if all(c["reportable"] for c in cells):
            readable.append((era, [c["rate"] for c in cells]))
    r.claim(len(readable) == 4,
            "all three float bands can be read in exactly four eras",
            "RESOLUTION_AUDIT.md §5, DECISIONS.md D5, /measurement")
    rising = [e for e, v in readable if v == sorted(v)]
    r.claim(rising == ["2022-24"],
            "the rate rises with size in exactly one era, 2022-24",
            "README, RESOLUTION_AUDIT.md §5, DECISIONS.md D5, /measurement")
    middle_high = [e for e, v in readable if v[1] == max(v)]
    r.claim(len(middle_high) == 2,
            "the middle band is highest in two of those four eras",
            "RESOLUTION_AUDIT.md §5, DECISIONS.md D5, /measurement")
    middle_low = [e for e, v in readable if v[1] == min(v)]
    r.claim(middle_low == ["2012-14"],
            "the middle band is lowest in 2012-14",
            "RESOLUTION_AUDIT.md §5, DECISIONS.md D5, /measurement")
    pooled = [rate(d[d["float_band"] == b]) for b in bands]
    r.claim(all(abs(a - b) < 0.001 for a, b in zip(pooled, (0.455, 0.607, 0.585))),
            "pooled float bands are 45.5% / 60.7% / 58.5%",
            "README, DECISIONS.md D5, RESOLUTION_AUDIT.md §5")

    print("\n-- sector: what survives, what does not --")
    mining = d[d["sic_division"] == "Mining"]
    below = [label for _, _, label in X.ERAS
             if X.cell(mining[mining["era"] == label])["reportable"]
             and rate(mining[mining["era"] == label]) < rate(d[d["era"] == label])]
    readable_mining = [label for _, _, label in X.ERAS
                       if X.cell(mining[mining["era"] == label])["reportable"]]
    r.claim(below == readable_mining and len(below) >= 4,
            "mining resolves below its own era in every era where the cell can be read",
            "README, /data, /measurement, RESOLUTION_AUDIT.md §4, DECISIONS.md D5")

    manuf = d[d["sic_division"] == "Manufacturing"]
    above = [label for _, _, label in X.ERAS
             if rate(manuf[manuf["era"] == label]) > rate(d[d["era"] == label])]
    all_readable = all(X.cell(manuf[manuf["era"] == label])["reportable"]
                       for _, _, label in X.ERAS)
    r.claim(len(above) == 5 and all_readable,
            "manufacturing sits above its era in all five, every cell reportable",
            "/measurement, RESOLUTION_AUDIT.md §4, DECISIONS.md D5")

    fin = d[d["sic_division"] == FIN]
    fin_early = fin[fin["era"] == "2010-11"]
    r.claim(len(fin_early) == 14 and int(fin_early["resolved"].sum()) == 1,
            "the financials claim rested on one cell of fourteen firms in 2010-11",
            "README, /measurement, RESOLUTION_AUDIT.md §4, DECISIONS.md D5")
    later = [X.cell(fin[fin["era"] == label])["reportable"]
             for _, _, label in X.ERAS if label != "2010-11"]
    r.claim(not any(later),
            "every financials cell after 2010-11 is too small to report",
            "/measurement, RESOLUTION_AUDIT.md §4, DECISIONS.md D5")
    resolved = d[d["resolved"]]
    r.claim(abs(len(fin) / len(d) - 0.118) < 0.001
            and abs((resolved["sic_division"] == FIN).mean() - 0.094) < 0.001,
            "financials are 11.8% of candidates and 9.4% of the resolved set",
            "README, /measurement, RESOLUTION_AUDIT.md §4, DECISIONS.md D5")

    print("\n-- the no-float band is mostly era --")
    no_float = d[d["float_band"] == X.NO_FLOAT]
    r.claim(len(no_float[no_float["era"] == "2010-11"]) == 37 and len(no_float) == 93,
            "37 of the 93 no-float firms sit in 2010-11",
            "RESOLUTION_AUDIT.md §5.1")
    r.claim(abs(rate(no_float[no_float["era"] == "2012-14"])
                - rate(d[d["era"] == "2012-14"])) < 0.02,
            "in 2012-14 the no-float band matches the era average -- no gap",
            "RESOLUTION_AUDIT.md §5.1")

    print("\n-- the retracted cell, and the limit of the suppression rule --")
    lo, hi = X.wilson_interval(19, 24)
    r.claim(abs(lo - 0.595) < 0.005 and abs(hi - 0.908) < 0.005,
            "the retracted cell's 95% bounds ran 60% to 91%",
            "README, /measurement, RESOLUTION_AUDIT.md §7.1, DECISIONS.md D5")
    r.claim(X.cell(pd.DataFrame({"resolved": [True] * 19 + [False] * 5}))["reportable"],
            "that cell would still be reportable today -- the rule is a floor",
            "RESOLUTION_AUDIT.md §7.1, DECISIONS.md D5, tests/test_crosstabs.py")

    print("\n-- exclusion families --")
    fams = d["exclusion_family"].value_counts()
    r.claim(int(fams.get("data_unavailability", 0)) == 186
            and int(fams.get("model_inapplicability", 0)) == 11,
            "186 excluded by source limits against 11 non-Merton objects",
            "/measurement, RESOLUTION_AUDIT.md §6, DECISIONS.md D5")
    ch22 = d["is_chapter_22"].astype(str).str.lower().isin(["true", "1"]).sum()
    r.claim(int(ch22) == 29,
            "Chapter 22 runs at 29 of 346 (8.4%)",
            "/measurement, RESOLUTION_AUDIT.md §6")

    return r


def main() -> int:
    path = DATA_PROCESSED / "resolution_audit.csv"
    if not path.exists():
        print(f"{path} absent; run python -m scripts.audit_resolution first")
        return 1
    report = check(pd.read_csv(path, dtype={"cik": str}))

    print(f"\n{'=' * 70}")
    if report.failures:
        print(f"{len(report.failures)} of {report.checked} published figures no "
              "longer reproduce:\n")
        for f in report.failures:
            print(f"  - {f}")
        print("\nFix the prose, or fix the pipeline. Do not fix the threshold.")
        return 1
    print(f"All {report.checked} published figures reproduce from "
          f"{path.name}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
