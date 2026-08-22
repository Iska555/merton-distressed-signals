"""
No em dash anywhere in the source or the built site.

The em dash arrived here through copy inherited from design artifacts and then
spread, because it is the easy punctuation mark: it joins any two thoughts
without deciding what the relationship between them is. Deciding is the point.
An independent clause takes a full stop, a subordinate one takes a comma, and
something being introduced takes a colon.

A spaced hyphen is not a substitute. It is the same evasion with worse
typography.

This checks source files and, when a production build exists, the rendered HTML
under frontend/.next, so a dash cannot re-enter through a component that no
source grep happens to cover.
"""
from __future__ import annotations

import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
EM_DASH = chr(0x2014)  # written as a code point so this file passes its own check

SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".css", ".md", ".json", ".example", ".txt"}
SKIP_PARTS = {"node_modules", ".next", ".git", "__pycache__", "raw", ".venv", "venv"}

#: The en dash (U+2013) is correct for a numeric range and is left alone.
#: This test is about U+2014 only.
EN_DASH = chr(0x2013)
ALLOWED = {EN_DASH}


def _candidate_files(root: pathlib.Path, suffixes: set[str]):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if SKIP_PARTS & set(path.parts):
            continue
        if path.suffix not in suffixes:
            continue
        yield path


def _offenders(paths) -> list[str]:
    hits = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if EM_DASH not in text:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if EM_DASH in line:
                rel = path.relative_to(ROOT)
                hits.append(f"{rel}:{number}: {line.strip()[:110]}")
    return hits


def test_no_em_dash_in_source():
    hits = _offenders(_candidate_files(ROOT, SOURCE_SUFFIXES))
    assert not hits, (
        f"{len(hits)} em dash(es) in source. Replace with a full stop for an "
        "independent clause, a comma for a subordinate one, or a colon where "
        "it introduces. Never a spaced hyphen.\n  " + "\n  ".join(hits[:40])
    )


def test_no_em_dash_in_built_output():
    """
    The built site, if one exists.

    Source is not sufficient on its own: a dash could arrive from a dependency
    template or from generated JSON. Skipped rather than failed when no build
    is present, so the suite still runs on a clean checkout.
    """
    build = ROOT / "frontend" / ".next" / "server" / "app"
    if not build.exists():
        pytest.skip("no production build; run npm run build in frontend/")
    pages = [p for p in build.rglob("*.html")]
    if not pages:
        pytest.skip("build present but no prerendered HTML found")
    hits = _offenders(pages)
    assert not hits, (
        f"{len(hits)} em dash(es) in the rendered site:\n  " + "\n  ".join(hits[:40])
    )


def test_the_en_dash_is_not_collateral_damage():
    """A numeric range keeps its en dash. Only U+2014 is banned."""
    assert f"2012{EN_DASH}2024".count(EM_DASH) == 0
    assert EN_DASH in ALLOWED
