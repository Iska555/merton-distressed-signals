import sys
from pathlib import Path
import subprocess

from scripts.verify import executable_argv, run_checks, verification_commands


def test_verification_covers_assets_figures_frontend_and_tests():
    root = Path("/repo")
    checks = verification_commands(root)

    assert [check.name for check in checks] == [
        "generated assets",
        "published figures",
        "frontend lint",
        "frontend build",
        "root tests",
    ]
    assert checks[0].argv[:3] == ("python", "-m", "scripts.check_assets")
    assert checks[-1].argv == ("python", "-m", "pytest", "tests", "-q")
    assert checks[2].cwd == root / "frontend"
    assert checks[3].cwd == root / "frontend"


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
        ((custom_python, "-m", "scripts.check_published_figures"), root, True),
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
