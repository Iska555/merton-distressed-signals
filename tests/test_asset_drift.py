from __future__ import annotations

from scripts.check_assets import GENERATED_ASSETS, compare_assets


def test_generated_inventory_contains_every_public_asset():
    assert GENERATED_ASSETS == (
        "brand/apple-touch-icon.png",
        "brand/favicon-32.png",
        "brand/icon-512.png",
        "brand/icon.svg",
        "brand/lockup-dark.svg",
        "brand/lockup.svg",
        "brand/logo-dark.svg",
        "brand/logo.svg",
        "figures/hero-paths-dark.png",
        "figures/hero-paths-light.png",
        "figures/sample-field.svg",
        "marks/cases.svg",
        "marks/data.svg",
        "marks/discrimination.svg",
        "marks/evidence.svg",
        "marks/measurement.svg",
        "marks/mispricing.svg",
        "marks/model.svg",
    )


def test_compare_assets_reports_missing_extra_and_changed_files(tmp_path):
    committed = tmp_path / "committed"
    generated = tmp_path / "generated"
    committed.mkdir()
    generated.mkdir()

    (committed / "same.svg").write_bytes(b"same")
    (generated / "same.svg").write_bytes(b"same")
    (committed / "changed.svg").write_bytes(b"old")
    (generated / "changed.svg").write_bytes(b"new")
    (committed / "missing.svg").write_bytes(b"committed only")
    (generated / "extra.svg").write_bytes(b"generated only")

    assert compare_assets(
        committed,
        generated,
        ("changed.svg", "extra.svg", "missing.svg", "same.svg"),
    ) == [
        "changed: changed.svg",
        "uncommitted: extra.svg",
        "missing from generation: missing.svg",
    ]
