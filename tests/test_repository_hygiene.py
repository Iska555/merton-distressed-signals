from __future__ import annotations

import importlib
from pathlib import Path

import dotenv


ROOT = Path(__file__).resolve().parents[1]


def test_legacy_backend_is_not_part_of_the_supported_checkout():
    assert not (ROOT / "backend").exists()


def test_tests_do_not_leave_visualization_pngs_at_repository_root():
    assert not list(ROOT.glob("output_*.png"))


def test_config_loads_credentials_from_root_env(monkeypatch):
    import src.config as config

    calls: list[Path] = []
    monkeypatch.setattr(dotenv, "load_dotenv", lambda path: calls.append(Path(path)))

    importlib.reload(config)

    assert calls == [config.ROOT / ".env"]
