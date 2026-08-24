from pathlib import Path

import sys

from scripts.verify import Check, executable_argv, verification_commands


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


def test_execution_uses_cmd_to_wait_for_npm_on_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    check = Check("frontend lint", ("npm", "run", "lint"), Path("/repo/frontend"))

    assert executable_argv(check) == (
        "cmd.exe",
        "/d",
        "/s",
        "/c",
        "call",
        "npm.cmd",
        "run",
        "lint",
    )
