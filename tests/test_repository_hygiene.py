from __future__ import annotations

import importlib
from pathlib import Path
import tomllib

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
IGNORED_DIRECTORIES = {".next", "node_modules", "dist", "out", "build"}


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
                if path.is_file()
                and not IGNORED_DIRECTORIES.intersection(
                    path.relative_to(surface).parts
                )
            )
        else:
            continue
        for path in candidates:
            try:
                content = path.read_bytes()
                if b"\x00" in content:
                    continue
                if "backend/" in content.decode("utf-8"):
                    paths.append(path)
            except (OSError, UnicodeDecodeError):
                continue
    return paths


def test_legacy_backend_is_not_part_of_the_supported_checkout():
    assert not (ROOT / "backend").exists()


def test_backend_recovery_references_are_limited_to_the_data_inventory():
    assert not _backend_references(ROOT)


def test_backend_hygiene_scans_a_checkout_under_an_ignored_ancestor(tmp_path):
    root = tmp_path / "out" / "repo"
    source = root / "src" / "nested" / "reference.py"
    source.parent.mkdir(parents=True)
    source.write_text("legacy = 'backend/'\n", encoding="utf-8")

    assert _backend_references(root) == [source]


def test_backend_hygiene_ignores_repo_local_outputs_and_binary_files(tmp_path):
    root = tmp_path / "repo"
    source = root / "src" / "nested" / "reference.py"
    source.parent.mkdir(parents=True)
    source.write_text("legacy = 'backend/'\n", encoding="utf-8")

    for path in (
        root / "src" / "out" / "generated.py",
        root / "src" / "build" / "generated.py",
        root / "frontend" / "node_modules" / "package.js",
        root / "frontend" / ".next" / "server.js",
    ):
        path.parent.mkdir(parents=True)
        path.write_text("legacy = 'backend/'\n", encoding="utf-8")

    nul_binary = root / "scripts" / "nul.bin"
    nul_binary.parent.mkdir(parents=True)
    nul_binary.write_bytes(b"backend/\x00")

    undecodable_binary = root / "scripts" / "legacy.bin"
    undecodable_binary.write_bytes(b"backend/\xff")

    assert _backend_references(root) == [source]


def test_tests_do_not_leave_visualization_pngs_at_repository_root():
    assert not list(ROOT.glob("output_*.png"))


def test_config_loads_credentials_from_root_env(monkeypatch):
    import src.config as config

    calls: list[Path] = []
    monkeypatch.setattr(dotenv, "load_dotenv", lambda path: calls.append(Path(path)))

    importlib.reload(config)

    assert calls == [config.ROOT / ".env"]


def test_runtime_dependencies_include_the_parquet_engine():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = {
        dependency.split("[", 1)[0].split("=", 1)[0].split("<", 1)[0].split(">", 1)[0]
        for dependency in metadata["project"]["dependencies"]
    }

    assert "pyarrow" in dependencies


def test_site_data_builder_documents_the_static_runtime_boundary():
    docstring = (ROOT / "scripts" / "build_site_data.py").read_text(
        encoding="utf-8"
    ).split('"""', 2)[1]

    assert "no backend is required" in docstring
    assert "allowed to call a backend" not in docstring
