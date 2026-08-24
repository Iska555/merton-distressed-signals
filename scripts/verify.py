"""Run every supported repository check in one deterministic sequence."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys


@dataclass(frozen=True)
class Check:
    """A named command that belongs to the supported verification release gate."""

    name: str
    argv: tuple[str, ...]
    cwd: Path


def verification_commands(root: Path) -> tuple[Check, ...]:
    """Return the portable, test-facing verification plan for *root*."""
    python = "python"
    frontend = root / "frontend"
    return (
        Check("generated assets", (python, "-m", "scripts.check_assets"), root),
        Check(
            "published figures",
            (python, "-m", "scripts.check_published_figures"),
            root,
        ),
        Check("frontend lint", ("npm", "run", "lint"), frontend),
        Check("frontend build", ("npm", "run", "build"), frontend),
        Check("root tests", (python, "-m", "pytest", "tests", "-q"), root),
    )


def executable_argv(check: Check) -> tuple[str, ...]:
    """Resolve portable Python command labels to the running interpreter."""
    if check.argv[0] == "python":
        return (sys.executable, *check.argv[1:])
    if check.argv[0] == "npm" and sys.platform == "win32":
        return ("cmd.exe", "/d", "/s", "/c", "call", "npm.cmd", *check.argv[1:])
    return check.argv


def run_checks(root: Path) -> int:
    """Run release checks in order, returning immediately when one fails."""
    for check in verification_commands(root):
        print(f"\n== {check.name} ==")
        try:
            subprocess.run(executable_argv(check), cwd=check.cwd, check=True)
        except subprocess.CalledProcessError as error:
            return error.returncode
    return 0


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    return run_checks(root)


if __name__ == "__main__":
    raise SystemExit(main())
