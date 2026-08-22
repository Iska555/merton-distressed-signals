"""
Turn committed CSVs under data/processed/ into JSON the site reads at build time.

The site must render with the FastAPI backend entirely stopped. Every research
page therefore reads a static file produced here, never an API. The only thing
allowed to call a backend is the live single-name screen, and it degrades to a
stated unavailable state.

Writes a MANIFEST.json alongside, carrying the run date, the git commit the
figures were produced at, row counts, and a provenance line per file. A number
on the site that cannot be traced back through this manifest to a committed CSV
is a bug.

Run:  python -m scripts.build_site_data
Out:  frontend/public/data/*.json
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis import crosstabs as X
from src.config import DATA_PROCESSED, ROOT

OUT = ROOT / "frontend" / "public" / "data"

def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def _clean(obj):
    """NaN is not valid JSON; emit null so the page can branch on it."""
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return None if not np.isfinite(obj) else float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if obj is pd.NA or obj is pd.NaT:
        return None
    return obj


def build_measurement(audit: pd.DataFrame) -> dict:
    """Everything the /measurement page renders."""
    audit = X.normalise(audit)

    total = len(audit)
    resolved = int(audit["resolved"].sum())

    by_year = []
    for year, chunk in audit.groupby("event_year"):
        if not np.isfinite(year):
            continue
        by_year.append({
            "year": int(year),
            "n": len(chunk),
            "resolved": int(chunk["resolved"].sum()),
            "rate": float(chunk["resolved"].mean()),
        })
    by_year.sort(key=lambda r: r["year"])

    by_era = []
    for lo, hi, label in X.ERAS:
        chunk = audit[audit["event_year"].between(lo, hi)]
        if chunk.empty:
            continue
        by_era.append({
            "label": label,
            "n": len(chunk),
            "resolved": int(chunk["resolved"].sum()),
            "rate": float(chunk["resolved"].mean()),
            "via_xbrl": int((chunk["reason_code"] == "RESOLVED_XBRL").sum()),
            "via_text": int((chunk["reason_code"] == "RESOLVED_FILING_TEXT").sum()),
        })

    by_size = []
    for label in X.FLOAT_ORDER:
        chunk = audit[audit["float_band"] == label]
        if chunk.empty:
            continue
        by_size.append({
            "label": label, "n": len(chunk),
            "resolved": int(chunk["resolved"].sum()),
            "rate": float(chunk["resolved"].mean()),
        })

    by_sector = []
    for sector, chunk in audit.groupby("sic_division"):
        if len(chunk) < 3:
            continue
        by_sector.append({
            "sector": str(sector), "n": len(chunk),
            "resolved": int(chunk["resolved"].sum()),
            "rate": float(chunk["resolved"].mean()),
        })
    by_sector.sort(key=lambda r: -r["rate"])

    reasons = [
        {"code": str(code), "n": int(n), "share": float(n / total),
         "family": str(audit.loc[audit["reason_code"] == code, "exclusion_family"].iloc[0])
         if "exclusion_family" in audit.columns else "unknown"}
        for code, n in audit["reason_code"].value_counts().items()
    ]

    families = {}
    if "exclusion_family" in audit.columns:
        families = {str(k): int(v)
                    for k, v in audit["exclusion_family"].value_counts().items()}

    chapter22 = 0
    if "is_chapter_22" in audit.columns:
        chapter22 = int(
            audit["is_chapter_22"].astype(str).str.lower().isin(["true", "1"]).sum()
        )

    return {
        "total_candidates": total,
        "resolved": resolved,
        "resolution_rate": float(resolved / total) if total else None,
        "by_year": by_year,
        "by_era": by_era,
        "by_size": by_size,
        "by_sector": by_sector,
        # Era-conditional versions of the two tables above. Era is the dominant
        # axis of this sample, so a pooled gradient in size or sector may be
        # era measured a second time. Publishing both lets a reader see a
        # pooled difference dissolve when era is held fixed.
        "by_size_era": X.conditional_crosstab(audit, "float_band", X.FLOAT_ORDER),
        "by_sector_era": X.conditional_crosstab(
            audit, "sic_division",
            [r["sector"] for r in sorted(by_sector, key=lambda r: -r["n"])]),
        "float_availability": X.float_availability(audit),
        "min_reportable": {
            "max_wilson_width": X.MAX_REPORTABLE_WIDTH,
        },
        "reason_codes": reasons,
        "exclusion_families": families,
        "chapter_22_count": chapter22,
        "window": {
            "sampled_from": int(audit["event_year"].min()),
            "sampled_to": int(audit["event_year"].max()),
        },
    }


def build_verification(frame: pd.DataFrame) -> dict:
    """
    The symbol-resolution error rate, by stratum.

    Two numbers per stratum, deliberately kept apart. The **flag** rate is a
    name-similarity heuristic that sorts attention and decides nothing; many
    correct tickers are not derivable from a company name, so it runs high and
    means little. The **error** rate is hand-adjudicated against the sentence in
    the filing, and is the published statistic. Reporting only the first would
    overstate the error rate by a factor of several.

    Strata are reported separately because the risk is concentrated: prose
    extraction before the 2019 cover-page rule is the variable case, and a
    pooled figure dominated by clean recent XBRL would understate it there.
    """
    verdicts = frame.get("human_verdict", pd.Series(dtype=str)).fillna("")
    errors = verdicts.isin(["wrong_company", "wrong_era"])
    adjudicated = verdicts.isin(
        ["correct", "wrong_company", "wrong_era", "unverifiable"])

    def block(chunk: pd.DataFrame, mask: pd.Series) -> dict:
        done = chunk[mask.loc[chunk.index]]
        n = len(done)
        bad = int(errors.loc[done.index].sum()) if n else 0
        lo, hi = X.wilson_interval(bad, n) if n else (None, None)
        return {
            "n_sampled": len(chunk),
            "n_adjudicated": n,
            "errors": bad,
            "error_rate": (bad / n) if n else None,
            "ci_low": lo, "ci_high": hi,
            "unverifiable": int(
                (verdicts.loc[done.index] == "unverifiable").sum()) if n else 0,
            "flagged": int((chunk.get("heuristic") == "CHECK").sum()),
        }

    strata = []
    if "stratum" in frame.columns:
        for name, chunk in frame.groupby("stratum"):
            strata.append({"stratum": str(name), **block(chunk, adjudicated)})
    return {
        "n": len(frame),
        "strata": strata,
        "pooled": block(frame, adjudicated),
        "verdict_counts": {str(k): int(v)
                           for k, v in verdicts[adjudicated].value_counts().items()},
        "note": ("Flag rate is a name-similarity heuristic and decides nothing. "
                 "The error rate is hand-adjudicated against the sentence in the "
                 "filing and is published whatever it says."),
    }


FRED_SERIES = {
    "AAA": "BAMLC0A1CAAA",
    "AA": "BAMLC0A2CAA",
    "A": "BAMLC0A3CA",
    "BBB": "BAMLC0A4CBBB",
    "BB": "BAMLH0A1HYBB",
    "B": "BAMLH0A2HYB",
    "CCC": "BAMLH0A3HYC",
}


def build_cohort_spreads() -> dict | None:
    """
    Latest ICE BofA option-adjusted spread per rating cohort, from FRED.

    Fetched at BUILD time, not in the browser: the page must render with no
    backend and no credential, and an API key must never reach a client. The
    retrieval date is stamped into the payload and shown on the page, because a
    spread without a date is not a fact about anything.

    These are COHORT INDEX AVERAGES across hundreds of unrelated issuers, not
    any single firm's bond. The page says so; the field name says so here too.
    """
    import os
    import urllib.parse
    import urllib.request
    from datetime import date, timedelta

    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / "backend" / ".env")
    except Exception:  # noqa: BLE001
        pass

    key = os.getenv("FRED_API_KEY")
    if not key:
        print("  FRED_API_KEY not set; cohort spreads will be marked illustrative")
        return None

    start = (date.today() - timedelta(days=45)).isoformat()
    cohorts, retrieved = {}, None
    for label, series_id in FRED_SERIES.items():
        query = urllib.parse.urlencode({
            "series_id": series_id, "api_key": key, "file_type": "json",
            "observation_start": start, "sort_order": "desc", "limit": 5,
        })
        try:
            with urllib.request.urlopen(
                f"https://api.stlouisfed.org/fred/series/observations?{query}",
                timeout=30,
            ) as response:
                payload = json.loads(response.read().decode())
            observations = [
                o for o in payload.get("observations", [])
                if o.get("value") not in (".", "", None)
            ]
            if not observations:
                continue
            latest = observations[0]
            cohorts[label] = {
                "series_id": series_id,
                "oas_bps": round(float(latest["value"]) * 100, 1),
                "observation_date": latest["date"],
            }
            retrieved = retrieved or latest["date"]
        except Exception as exc:  # noqa: BLE001
            print(f"  FRED {label} ({series_id}) failed: {type(exc).__name__}")

    if not cohorts:
        return None
    return {
        "cohorts": cohorts,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "latest_observation": retrieved,
        "source": "ICE BofA option-adjusted spread indices via FRED",
        "caveat": (
            "Cohort index averages across many unrelated issuers, not any single "
            "firm's bond. Issuer-level pricing requires TRACE, which is not freely "
            "available."
        ),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "files": {},
    }

    audit_path = DATA_PROCESSED / "resolution_audit.csv"
    if audit_path.exists():
        audit = pd.read_csv(audit_path, dtype=str)
        payload = build_measurement(audit)
        (OUT / "measurement.json").write_text(
            json.dumps(_clean(payload), indent=2) + "\n", encoding="utf-8"
        )
        manifest["files"]["measurement.json"] = {
            "source": "data/processed/resolution_audit.csv",
            "rows_in": len(audit),
            "description": (
                "Symbol-resolution audit of 8-K Item 1.03 bankruptcy candidates: "
                "resolution rate by era, public-float band and SIC division, with "
                "exclusion reason codes split into data unavailability vs model "
                "inapplicability."
            ),
            "retrieved": "SEC EDGAR full-text search and XBRL company facts",
        }
        print(f"  measurement.json  <- {len(audit)} audit rows")
    else:
        print("  resolution_audit.csv absent; skipping measurement.json")

    verification = DATA_PROCESSED / "filing_text_verification.csv"
    if verification.exists():
        frame = pd.read_csv(verification, dtype=str)
        (OUT / "verification.json").write_text(
            json.dumps(_clean(build_verification(frame)), indent=2) + "\n",
            encoding="utf-8",
        )
        manifest["files"]["verification.json"] = {
            "source": "data/processed/filing_text_verification.csv",
            "rows_in": len(frame),
            "description": "Hand-verification sample for symbol resolution accuracy.",
        }
        print(f"  verification.json <- {len(frame)} rows")

    # Emit the rating tables rather than letting the browser keep its own copy.
    # Two transcriptions of the same thresholds would drift, and the drift would
    # be invisible: the page would quietly disagree with the study.
    from src.models import shadow_rating as sr

    (OUT / "shadow_rating.json").write_text(
        json.dumps(_clean({
            "large_cap": sr._LARGE_CAP,
            "small_cap": sr._SMALL_CAP,
            "large_cap_asset_threshold": sr.LARGE_CAP_ASSET_THRESHOLD,
            "scale": sr.RATING_SCALE,
            "cohort_index": sr.COHORT_INDEX,
            "source": sr.SOURCE,
        }), indent=2) + "\n",
        encoding="utf-8",
    )
    manifest["files"]["shadow_rating.json"] = {
        "source": "src/models/shadow_rating.py",
        "rows_in": len(sr.RATING_SCALE),
        "description": (
            "Coverage-to-rating thresholds, emitted from the Python module so the "
            "browser cannot hold a divergent copy. Accounting inputs only: no "
            "Merton quantity enters the benchmark rating."
        ),
    }
    print(f"  shadow_rating.json <- {len(sr.RATING_SCALE)} rating grades")

    spreads = build_cohort_spreads()
    if spreads:
        (OUT / "cohort_spreads.json").write_text(
            json.dumps(_clean(spreads), indent=2) + "\n", encoding="utf-8"
        )
        manifest["files"]["cohort_spreads.json"] = {
            "source": "FRED ICE BofA option-adjusted spread indices",
            "rows_in": len(spreads["cohorts"]),
            "description": (
                "Latest OAS per rating cohort. Index averages across many "
                "unrelated issuers, NOT any single firm's bond."
            ),
            "retrieved": spreads["retrieved_utc"],
        }
        print(f"  cohort_spreads.json <- {len(spreads['cohorts'])} cohorts, "
              f"latest observation {spreads['latest_observation']}")

        # Independent corroboration of the unit conversion. Damodaran's spread
        # column is built from traded bonds and is unrelated to FRED. Agreement
        # across investment grade is evidence there is no factor-of-100 error
        # hiding in the percent-to-basis-point step.
        rows = []
        for grade in ("AAA", "AA", "A", "BBB", "BB", "B", "CCC"):
            fred = spreads["cohorts"].get(grade, {}).get("oas_bps")
            dam = sr.DAMODARAN_SPREAD_BPS_JAN2026.get(grade)
            if fred is None or dam is None:
                continue
            rows.append({
                "grade": grade,
                "fred_bps": fred,
                "damodaran_bps": dam,
                "difference_bps": round(fred - dam, 1),
                "ratio": round(fred / dam, 3) if dam else None,
            })
        (OUT / "spread_corroboration.json").write_text(
            json.dumps(_clean({
                "rows": rows,
                "fred_observation": spreads["latest_observation"],
                "damodaran_vintage": sr.SOURCE["large_vintage"],
                "note": (
                    "Two unrelated sources. Damodaran's column is a periodic "
                    "snapshot from traded bonds; FRED is a daily index. "
                    "High-yield tails move fast, so CCC divergence is expected "
                    "and is not evidence of an error."
                ),
            }), indent=2) + "\n",
            encoding="utf-8",
        )
        manifest["files"]["spread_corroboration.json"] = {
            "source": "FRED ICE BofA OAS vs Damodaran synthetic-rating spreads",
            "rows_in": len(rows),
            "description": (
                "Validation check on the percent-to-basis-point conversion, "
                "against an independent source."
            ),
        }
        print(f"  spread_corroboration.json <- {len(rows)} grades compared")

    (OUT / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nWrote {len(manifest['files'])} file(s) + MANIFEST.json to {OUT}")
    print(f"git commit: {manifest['git_commit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
