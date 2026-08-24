import sys
from pathlib import Path
import subprocess

from scripts.verify import executable_argv, run_checks, verification_commands


ROOT = Path(__file__).resolve().parents[1]


def test_python_environment_is_locked_and_ci_uses_the_frozen_lockfile():
    assert (ROOT / "uv.lock").is_file()

    workflow = (ROOT / ".github" / "workflows" / "assets.yml").read_text(
        encoding="utf-8"
    )
    assert "astral-sh/setup-uv@" in workflow
    assert "uv lock --check" in workflow
    assert "uv sync --frozen --all-extras" in workflow
    assert "uv run --frozen python -m playwright install --with-deps chromium" in workflow
    assert "uv run --frozen python -m scripts.verify" in workflow
    assert "python -m pip install" not in workflow

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "uv sync --frozen --all-extras" in readme
    assert "uv run --frozen python -m scripts.verify" in readme


def test_verification_covers_live_assets_data_frontend_security_and_tests():
    root = Path("/repo")
    checks = verification_commands(root)

    assert [check.name for check in checks] == [
        "generated assets",
        "site data",
        "frontend lint",
        "frontend build",
        "frontend dependency audit",
        "root tests",
    ]
    assert checks[0].argv[:3] == ("python", "-m", "scripts.check_assets")
    assert checks[1].argv[:3] == ("python", "-m", "scripts.check_site_data")
    assert checks[-1].argv == ("python", "-m", "pytest", "tests", "-q")
    assert checks[2].cwd == root / "frontend"
    assert checks[3].cwd == root / "frontend"
    assert checks[4].argv == (
        "npm",
        "audit",
        "--omit=dev",
        "--audit-level=low",
    )
    assert checks[4].cwd == root / "frontend"


def test_python_marker_is_stable_for_custom_python_executables(monkeypatch):
    root = Path("/repo")
    custom_python = "/opt/custom/bin/python3.14"
    monkeypatch.setattr(sys, "executable", custom_python)

    check = verification_commands(root)[0]

    assert check.argv[:3] == ("python", "-m", "scripts.check_assets")
    assert executable_argv(check) == (custom_python, "-m", "scripts.check_assets")


def test_run_checks_stops_at_the_second_failure_and_returns_its_status(monkeypatch):
    root = Path("/repo")
    custom_python = "/opt/custom/bin/python3.14"
    calls: list[tuple[tuple[str, ...], Path, bool]] = []

    def fake_run(argv, *, cwd, check):
        calls.append((tuple(argv), cwd, check))
        if len(calls) == 2:
            raise subprocess.CalledProcessError(23, argv)

    monkeypatch.setattr(sys, "executable", custom_python)
    monkeypatch.setattr(subprocess, "run", fake_run)

    assert run_checks(root) == 23
    assert calls == [
        ((custom_python, "-m", "scripts.check_assets"), root, True),
        ((custom_python, "-m", "scripts.check_site_data"), root, True),
    ]


def test_run_checks_returns_a_windows_npm_failure_after_the_python_checks(monkeypatch):
    root = Path("/repo")
    calls: list[tuple[tuple[str, ...], Path, bool]] = []

    def fake_run(argv, *, cwd, check):
        calls.append((tuple(argv), cwd, check))
        if len(calls) == 3:
            raise subprocess.CalledProcessError(29, argv)

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(subprocess, "run", fake_run)

    assert run_checks(root) == 29
    assert calls[2] == (
        ("cmd.exe", "/d", "/s", "/c", "call", "npm.cmd", "run", "lint"),
        root / "frontend",
        True,
    )
