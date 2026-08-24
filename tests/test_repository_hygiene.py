from __future__ import annotations

import importlib
from pathlib import Path

import dotenv


ROOT = Path(__file__).resolve().parents[1]


def test_legacy_backend_is_not_part_of_the_supported_checkout():
    assert not (ROOT / "backend").exists()


def test_backend_recovery_references_are_limited_to_the_data_inventory():
    inventory = ROOT / "docs" / "PHASE0_DATA_INVENTORY.md"
    supported_sources = (
        ROOT / ".env.example",
        ROOT / "src" / "data" / "edgar.py",
        ROOT / "src" / "models" / "merton.py",
    )

    assert "backend/" in inventory.read_text(encoding="utf-8")
    for path in supported_sources:
        assert "backend/" not in path.read_text(encoding="utf-8")


def test_tests_do_not_leave_visualization_pngs_at_repository_root():
    assert not list(ROOT.glob("output_*.png"))


def test_config_loads_credentials_from_root_env(monkeypatch):
    import src.config as config

    calls: list[Path] = []
    monkeypatch.setattr(dotenv, "load_dotenv", lambda path: calls.append(Path(path)))

    importlib.reload(config)

    assert calls == [config.ROOT / ".env"]
