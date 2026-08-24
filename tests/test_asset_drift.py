from __future__ import annotations

from pathlib import Path

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
        "marks/cases.svg",
        "marks/data.svg",
        "marks/discrimination.svg",
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


def test_compare_assets_rejects_generated_files_outside_the_inventory(tmp_path):
    committed = tmp_path / "committed"
    generated = tmp_path / "generated"
    committed.mkdir()
    generated.mkdir()
    (committed / "expected.svg").write_bytes(b"same")
    (generated / "expected.svg").write_bytes(b"same")
    figures = generated / "figures"
    figures.mkdir()
    (figures / "sample-field.svg").write_bytes(b"withdrawn")

    assert compare_assets(committed, generated, ("expected.svg",)) == [
        "unexpected generated asset: figures/sample-field.svg"
    ]


def test_compare_assets_rejects_stale_committed_files_in_managed_directories(tmp_path):
    committed = tmp_path / "committed"
    generated = tmp_path / "generated"
    for root in (committed, generated):
        (root / "figures").mkdir(parents=True)
        (root / "figures" / "hero.svg").write_bytes(b"same")
    (committed / "figures" / "sample-field.svg").write_bytes(b"withdrawn")

    assert compare_assets(committed, generated, ("figures/hero.svg",)) == [
        "unexpected committed asset: figures/sample-field.svg"
    ]


def test_supported_asset_cli_cannot_generate_the_withdrawn_sample_field():
    source = (Path(__file__).resolve().parents[1] / "scripts" / "assets.py").read_text(
        encoding="utf-8"
    )
    checker = (
        Path(__file__).resolve().parents[1] / "scripts" / "check_assets.py"
    ).read_text(encoding="utf-8")

    assert 'ap.add_argument("--audit"' not in source
    assert 'ap.add_argument("--demo"' not in source
    assert "def sample_field_svg" not in source
    assert "sample_field_svg(" not in source
    assert '"figures/sample-field.svg"' in source
    assert 'parser.add_argument(\n        "--audit"' not in checker
