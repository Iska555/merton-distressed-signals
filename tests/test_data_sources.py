import json
from pathlib import Path

from scripts import build_site_data
from src.models import shadow_rating


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "frontend" / "public" / "data" / "SOURCES.json"
REQUIRED = {
    "id", "publisher", "official_url", "used_for", "access", "terms_url",
    "redistribution", "point_in_time_limit", "known_failure_mode",
}


def test_source_registry_is_complete_and_uses_official_links():
    rows = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert {row["id"] for row in rows} == {
        "sec-edgar-search", "sec-companyfacts", "sec-dera-fsds",
        "fred-ice-bofa-oas", "tiingo-prices", "damodaran-synthetic-rating",
    }
    for row in rows:
        assert REQUIRED <= row.keys()
        assert row["official_url"].startswith("https://")
        assert row["terms_url"].startswith("https://")
        assert all(str(row[field]).strip() for field in REQUIRED)


def test_restricted_top_level_market_data_is_not_publicly_committed():
    public = ROOT / "frontend" / "public" / "data"
    assert not (public / "cohort_spreads.json").exists()
    assert not (public / "spread_corroboration.json").exists()
    builder = (ROOT / "scripts" / "build_site_data.py").read_text(encoding="utf-8")
    assert "BAMLC0A" not in builder
    assert "BAMLH0A" not in builder


def test_generator_removes_stale_restricted_and_withdrawn_public_data(
    tmp_path, monkeypatch
):
    output = tmp_path / "public-data"
    output.mkdir()
    restricted = [
        output / "cohort_spreads.json",
        output / "spread_corroboration.json",
        output / "measurement.json",
        output / "verification.json",
    ]
    for path in restricted:
        path.write_text('{"restricted": true}\n', encoding="utf-8")

    monkeypatch.setattr(build_site_data, "OUT", output)

    assert build_site_data.main() == 0
    assert all(not path.exists() for path in restricted)


def test_site_data_manifest_contains_only_reproducible_provenance(
    tmp_path, monkeypatch
):
    output = tmp_path / "public-data"
    output.mkdir()

    monkeypatch.setattr(build_site_data, "OUT", output)

    assert build_site_data.main() == 0
    first = (output / "MANIFEST.json").read_bytes()
    assert build_site_data.main() == 0
    second = (output / "MANIFEST.json").read_bytes()

    assert first == second
    manifest = json.loads(first)
    assert manifest["schema_version"] == 1
    assert "generated_utc" not in manifest
    assert "git_commit" not in manifest


def test_shadow_rating_payload_carries_the_permitted_periodic_benchmark():
    payload = json.loads(
        (ROOT / "frontend" / "public" / "data" / "shadow_rating.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["benchmark_spread_bps"]["BBB"] == 111
    assert payload["benchmark_source"]["publisher"] == "NYU Stern, Aswath Damodaran"


def test_committed_benchmark_exactly_matches_python_source():
    payload = json.loads(
        (ROOT / "frontend" / "public" / "data" / "shadow_rating.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["benchmark_spread_bps"] == (
        shadow_rating.DAMODARAN_SPREAD_BPS_JAN2026
    )
    assert payload["benchmark_source"] == shadow_rating.SOURCE


def test_committed_band_diagnostics_exactly_match_python_source():
    payload = json.loads(
        (ROOT / "frontend" / "public" / "data" / "shadow_rating.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["band_diagnostics"] == shadow_rating.BAND_DIAGNOSTICS
    assert payload["band_diagnostics"]["within_30pct_of_boundary_n"] == 265
    assert payload["band_diagnostics"]["share_within_30pct_of_boundary"] == (
        265 / 3132
    )
