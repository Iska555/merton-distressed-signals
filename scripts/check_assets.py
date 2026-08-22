#!/usr/bin/env python3
"""Regenerate public assets in a temporary directory and detect drift."""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable


GENERATED_ASSETS = (
    "brand/apple-touch-icon.png",
    "brand/favicon-32.png",
    "brand/icon-512.png",
    "brand/icon.svg",
    "brand/lockup-dark.svg",
    "brand/lockup.svg",
    "brand/logo-dark.svg",
    "brand/logo.svg",
    "figures/hero-paths-dark.png",
    "figures/hero-paths-light.png",
    "figures/sample-field.svg",
    "marks/cases.svg",
    "marks/data.svg",
    "marks/discrimination.svg",
    "marks/evidence.svg",
    "marks/measurement.svg",
    "marks/mispricing.svg",
    "marks/model.svg",
)


def compare_assets(
    committed_root: Path,
    generated_root: Path,
    relative_paths: Iterable[str] = GENERATED_ASSETS,
) -> list[str]:
    differences: list[str] = []
    for relative in relative_paths:
        committed = committed_root / relative
        generated = generated_root / relative
        if not committed.exists() and generated.exists():
            differences.append(f"uncommitted: {relative}")
        elif committed.exists() and not generated.exists():
            differences.append(f"missing from generation: {relative}")
        elif committed.exists() and generated.exists():
            if committed.read_bytes() != generated.read_bytes():
                differences.append(f"changed: {relative}")
    return differences


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="frontend/public")
    parser.add_argument("--audit", default="data/processed/resolution_audit.csv")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    committed_root = root / args.out
    with tempfile.TemporaryDirectory(prefix="dcs-assets-") as temporary:
        generated_root = Path(temporary)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.assets",
                "--out",
                str(generated_root),
                "--audit",
                args.audit,
            ],
            cwd=root,
            check=True,
        )
        differences = compare_assets(committed_root, generated_root)

    if differences:
        print("generated assets have drifted:")
        for difference in differences:
            print(f"  {difference}")
        raise SystemExit(1)
    print(f"{len(GENERATED_ASSETS)} generated assets are current")


if __name__ == "__main__":
    main()
