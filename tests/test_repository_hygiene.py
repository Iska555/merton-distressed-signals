from __future__ import annotations

import importlib
from pathlib import Path

import dotenv


ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE_SURFACES = (
    Path("README.md"),
    Path(".env.example"),
    Path("src"),
    Path("scripts"),
    Path("frontend"),
    Path(".github"),
    Path("Makefile"),
)
IGNORED_DIRECTORIES = {".next", "node_modules", "dist", "out"}


def _backend_references(root: Path) -> list[Path]:
    paths: list[Path] = []
    for relative in ACCEPTANCE_SURFACES:
        surface = root / relative
        if surface.is_file():
            candidates = (surface,)
        elif surface.is_dir():
            candidates = (
                path
                for path in surface.rglob("*")
                if path.is_file() and not IGNORED_DIRECTORIES.intersection(path.parts)
            )
        else:
            continue
        for path in candidates:
            try:
                if "backend/" in path.read_text(encoding="utf-8"):
                    paths.append(path)
            except (OSError, UnicodeDecodeError):
                continue
    return paths


def test_legacy_backend_is_not_part_of_the_supported_checkout():
    assert not (ROOT / "backend").exists()


def test_backend_recovery_references_are_limited_to_the_data_inventory():
    assert not _backend_references(ROOT)


def test_backend_hygiene_recurses_and_ignores_dependency_build_and_binary_files(tmp_path):
    source = tmp_path / "src" / "nested" / "reference.py"
    source.parent.mkdir(parents=True)
    source.write_text("legacy = 'backend/'\n", encoding="utf-8")

    for path in (
        tmp_path / "frontend" / "node_modules" / "package.js",
        tmp_path / "frontend" / ".next" / "server.js",
    ):
        path.parent.mkdir(parents=True)
        path.write_text("legacy = 'backend/'\n", encoding="utf-8")

    binary = tmp_path / "scripts" / "legacy.bin"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"backend/\xff")

    assert _backend_references(tmp_path) == [source]


def test_tests_do_not_leave_visualization_pngs_at_repository_root():
    assert not list(ROOT.glob("output_*.png"))


def test_config_loads_credentials_from_root_env(monkeypatch):
    import src.config as config

    calls: list[Path] = []
    monkeypatch.setattr(dotenv, "load_dotenv", lambda path: calls.append(Path(path)))

    importlib.reload(config)

    assert calls == [config.ROOT / ".env"]
