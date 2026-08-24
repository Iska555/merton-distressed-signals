"""Build deterministic JSON for the live public research routes.

The withdrawn measurement payloads are deliberately unsupported. Normal
regeneration removes any stale copies before writing the current manifest.
All output is static, so no backend is required by the published site.

Run:  python -m scripts.build_site_data
Out:  frontend/public/data/*.json
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.config import ROOT

OUT = ROOT / "frontend" / "public" / "data"


def _clean(obj):
    """Convert NumPy/Pandas values into strict JSON-compatible values."""
    if isinstance(obj, dict):
        return {key: _clean(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_clean(value) for value in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return None if not np.isfinite(obj) else float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if obj is pd.NA or obj is pd.NaT:
        return None
    return obj


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for restricted_name in (
        "cohort_spreads.json",
        "spread_corroboration.json",
        "measurement.json",
        "verification.json",
    ):
        (OUT / restricted_name).unlink(missing_ok=True)

    manifest = {"schema_version": 1, "files": {}}

    # Emit the rating tables from the Python source of truth so the browser
    # cannot keep a second, drifting transcription.
    from src.models import shadow_rating as sr

    payload = {
        "large_cap": sr._LARGE_CAP,
        "small_cap": sr._SMALL_CAP,
        "large_cap_asset_threshold": sr.LARGE_CAP_ASSET_THRESHOLD,
        "scale": sr.RATING_SCALE,
        "cohort_index": sr.COHORT_INDEX,
        "source": sr.SOURCE,
        "band_diagnostics": sr.BAND_DIAGNOSTICS,
        "benchmark_spread_bps": sr.DAMODARAN_SPREAD_BPS_JAN2026,
        "benchmark_source": sr.SOURCE,
    }
    (OUT / "shadow_rating.json").write_text(
        json.dumps(_clean(payload), indent=2) + "\n",
        encoding="utf-8",
    )
    manifest["files"]["shadow_rating.json"] = {
        "source": "src/models/shadow_rating.py",
        "rows_in": len(sr.RATING_SCALE),
        "description": (
            "Coverage-to-rating thresholds and the January 2026 Damodaran periodic "
            "benchmark, emitted from the Python module so the browser cannot hold a "
            "divergent copy. Accounting inputs only: no Merton quantity enters the "
            "benchmark rating."
        ),
    }
    print(f"  shadow_rating.json <- {len(sr.RATING_SCALE)} rating grades")

    (OUT / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nWrote {len(manifest['files'])} file(s) + MANIFEST.json to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
