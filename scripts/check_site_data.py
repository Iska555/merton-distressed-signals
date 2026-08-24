#!/usr/bin/env python3
"""Regenerate live public site data and fail when committed bytes drift."""
from __future__ import annotations

import tempfile
from pathlib import Path

from scripts import build_site_data


STATIC_FILES = {"SOURCES.json"}


def compare_site_data(committed_root: Path, generated_root: Path) -> list[str]:
    committed = {
        path.name: path
        for path in committed_root.iterdir()
        if path.is_file() and path.name not in STATIC_FILES
    }
    generated = {
        path.name: path for path in generated_root.iterdir() if path.is_file()
    }
    differences: list[str] = []
    for name in sorted(committed.keys() | generated.keys()):
        if name not in committed:
            differences.append(f"uncommitted: {name}")
        elif name not in generated:
            differences.append(f"not generated: {name}")
        elif committed[name].read_bytes() != generated[name].read_bytes():
            differences.append(f"changed: {name}")
    return differences


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    committed_root = root / "frontend" / "public" / "data"
    with tempfile.TemporaryDirectory(prefix="dcs-site-data-") as temporary:
        generated_root = Path(temporary)
        previous_out = build_site_data.OUT
        try:
            build_site_data.OUT = generated_root
            build_site_data.main()
        finally:
            build_site_data.OUT = previous_out
        differences = compare_site_data(committed_root, generated_root)
        generated_count = len(tuple(generated_root.glob("*")))

    if differences:
        print("public site data have drifted:")
        for difference in differences:
            print(f"  {difference}")
        raise SystemExit(1)
    print(f"{generated_count} site data files are current")


if __name__ == "__main__":
    main()
