#!/usr/bin/env python3
"""
Generate every brand and figure asset for Distressed Credit Signals.

One entry point, one palette, deterministic output. Same inputs always produce
byte-identical files, so assets diff in git like code and cannot drift from the
numbers beside them.

    python -m scripts.assets --out frontend/public --logo divergence
    python -m scripts.assets --out frontend/public --audit data/processed/resolution_audit.csv
    python -m scripts.assets --out /tmp/preview --demo

Chocolate, burgundy and red sit close in hue, so they cannot carry categorical
meaning in a chart. Charts separate categories by lightness and texture, never
by warm hue alone. The full warm range is used freely everywhere else.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import html
import os
import subprocess
import sys
from collections import Counter, OrderedDict
from pathlib import Path


P = {
    "ink": "#2B1A17",
    "body": "#4A3830",
    "muted": "#7B675C",
    "rule": "#E7DCD6",
    "rule_strong": "#CDBAB1",
    "ground": "#FFFFFF",
    "tint": "#FAF5F2",
    "tint2": "#F3E9E4",
    "burgundy": "#7A1B2E",
    "red": "#C0272D",
    "chocolate": "#6B3F23",
    "deep": "#5C0F1D",
    "deep2": "#43101A",
    "paper": "#FFFFFF",
}
P_DARK = {
    "ink": "#F2E7E2",
    "body": "#CDB8B0",
    "muted": "#9C8479",
    "rule": "#33241F",
    "rule_strong": "#4A352E",
    "ground": "#16100E",
    "tint": "#1F1613",
    "tint2": "#261B17",
    "burgundy": "#C05A6B",
    "red": "#E4564F",
    "chocolate": "#B98A5A",
    "deep": "#43101A",
    "deep2": "#2E0B12",
    "paper": "#FFFFFF",
}

FIG = {
    "primary": "var(--fig-primary, #A81C2A)",
    "recessive": "var(--fig-recessive, #E8DCD6)",
    "third": "var(--fig-third, #6B3F23)",
    "ink": "var(--fig-ink, #2B1A17)",
    "muted": "var(--fig-muted, #7B675C)",
    "rule": "var(--fig-rule, #E7DCD6)",
    "signal": "var(--fig-signal, #C0272D)",
}


def _svg(
    body: str,
    *,
    vb: str = "0 0 32 32",
    label: str = "Distressed Credit Signals",
    description: str = "Distressed Credit Signals brand mark.",
) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" '
        f'aria-label="{html.escape(label)}"><title>{html.escape(label)}</title>'
        f'<desc>{html.escape(description)}</desc>{body}</svg>\n'
    )


def logo_divergence(c: str) -> str:
    """Two strokes leaving one origin and opening rightward."""
    return (
        f'<g fill="none" stroke="{c}" stroke-width="2.6" stroke-linecap="round">'
        '<path d="M4 16 L28 7"/><path d="M4 16 L28 25"/></g>'
    )


def logo_breach(c: str) -> str:
    """A threshold with one mark already through it."""
    return (
        f'<g stroke="{c}" stroke-width="2.4" stroke-linecap="round">'
        '<path d="M3 14 L29 14" fill="none"/></g>'
        f'<rect x="17" y="19" width="9" height="9" fill="{c}"/>'
    )


def logo_break(c: str) -> str:
    """A solid bar interrupted. The discontinuity itself."""
    return (
        f'<rect x="6" y="3" width="8" height="26" fill="{c}"/>'
        f'<rect x="18" y="3" width="8" height="11" fill="{c}"/>'
        f'<rect x="18" y="21" width="8" height="8" fill="{c}"/>'
    )


LOGOS = {
    "divergence": logo_divergence,
    "breach": logo_breach,
    "break": logo_break,
}


def icon_svg(kind: str, pal: dict) -> str:
    inner = LOGOS[kind](pal["paper"])
    return _svg(
        f'<rect width="32" height="32" rx="3" fill="{pal["red"]}"/>'
        f'<g transform="translate(16,16) scale(0.8) translate(-16,-16)">{inner}</g>',
        label="Distressed Credit Signals icon",
        description="White interrupted bar on a solid red square.",
    )


def lockup_svg(kind: str, pal: dict) -> str:
    mark = LOGOS[kind](pal["red"])
    return _svg(
        f'<g transform="scale(0.8) translate(0,3.6)">{mark}</g>'
        f'<text x="34" y="23" fill="{pal["ink"]}" font-family="Newsreader, Georgia, serif" '
        'font-size="20" font-weight="600" letter-spacing="-0.3">'
        'Distressed Credit Signals</text>',
        vb="0 0 300 32",
        description="Interrupted bar logo followed by the Distressed Credit Signals wordmark.",
    )


def _m(body: str) -> str:
    return (
        '<g fill="none" stroke="var(--mark, #C0272D)" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round">' + body + "</g>"
    )


MARKS: "OrderedDict[str, str]" = OrderedDict(
    [
        ("model", _m('<path d="M3 17 L12 17 L21 6"/>')),
        (
            "mispricing",
            _m('<path d="M3 12 L21 5"/><path d="M3 12 L21 19"/>'),
        ),
        (
            "measurement",
            _m(
                '<rect x="3" y="4" width="5" height="5"/>'
                '<rect x="10" y="4" width="5" height="5"/>'
                '<rect x="17" y="11" width="5" height="5"/>'
                '<rect x="3" y="11" width="5" height="5"/>'
                '<rect x="10" y="18" width="5" height="5"/>'
            ),
        ),
        (
            "evidence",
            _m(
                '<path d="M3 6 L21 6"/>'
                '<path d="M3 6 C10 6 12 13 21 14"/>'
                '<path d="M3 6 C9 7 11 19 21 21"/>'
            ),
        ),
        (
            "discrimination",
            _m(
                '<path d="M12 3 L12 21"/>'
                '<path d="M3 17 C6 17 6 9 9 9"/>'
                '<path d="M15 9 C18 9 18 17 21 17"/>'
            ),
        ),
        (
            "cases",
            _m(
                '<path d="M3 12 L21 12"/>'
                '<path d="M8 9 L8 15"/>'
                '<path d="M16 7 L16 17"/>'
            ),
        ),
        (
            "data",
            _m(
                '<path d="M3 6 L21 6"/>'
                '<path d="M3 12 L16 12"/>'
                '<path d="M3 18 L11 18"/>'
            ),
        ),
    ]
)


def mark_svg(name: str) -> str:
    return _svg(
        MARKS[name],
        vb="0 0 24 24",
        label=f"{name} section mark",
        description=f"Decorative line symbol for the {name} section.",
    )


RESOLVED, UNREACHABLE, INAPPLICABLE = "resolved", "unreachable", "inapplicable"
STATE_ORDER = [RESOLVED, UNREACHABLE, INAPPLICABLE]
STATE_LABEL = {
    RESOLVED: "Resolved to a traded symbol",
    UNREACHABLE: "Unreachable from public data",
    INAPPLICABLE: "Not a Merton object",
}
THRESHOLDS = [(2011, "XBRL instances appear"), (2019, "Cover page gains a symbol column")]


def _classify(row: dict) -> str:
    outcome = (
        row.get("outcome") or row.get("status") or row.get("resolved") or ""
    ).strip().lower()
    family = (
        row.get("reason_family") or row.get("exclusion_family") or ""
    ).strip().lower()
    if outcome in ("resolved", "ok", "true", "1"):
        return RESOLVED
    if "inapplic" in family or "model" in family:
        return INAPPLICABLE
    return UNREACHABLE


def load_audit(path: str) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            raw = (
                row.get("event_date")
                or row.get("filing_date")
                or row.get("event_year")
                or ""
            ).strip()
            if len(raw) < 4 or not raw[:4].isdigit():
                continue
            rows.append((int(raw[:4]), _classify(row)))
    rows.sort(key=lambda item: (item[0], STATE_ORDER.index(item[1])))
    return rows


def demo_rows() -> list[tuple[int, str]]:
    shape = {
        2010: (24, 0.08), 2011: (21, 0.14), 2012: (19, 0.18),
        2013: (17, 0.19), 2014: (16, 0.20), 2015: (23, 0.21),
        2016: (28, 0.22), 2017: (21, 0.24), 2018: (19, 0.26),
        2019: (22, 0.47), 2020: (34, 0.52), 2021: (18, 0.55),
        2022: (17, 0.65), 2023: (26, 0.69), 2024: (21, 0.71),
    }
    out: list[tuple[int, str]] = []
    for year, (count, share) in sorted(shape.items()):
        resolved = int(round(count * share))
        absent = count - resolved
        inapplicable = max(1, absent // 6)
        out += [(year, RESOLVED)] * resolved
        out += [(year, INAPPLICABLE)] * inapplicable
        out += [(year, UNREACHABLE)] * (absent - inapplicable)
    out.sort(key=lambda item: (item[0], STATE_ORDER.index(item[1])))
    return out


def sample_field_svg(rows: list[tuple[int, str]], *, demo: bool = False) -> str:
    by_year: "OrderedDict[int, Counter]" = OrderedDict()
    for year, state in rows:
        by_year.setdefault(year, Counter())[state] += 1
    if not by_year:
        raise SystemExit("no rows to plot")
    years = sorted(by_year)

    cell, gap, stack, year_gap = 9, 2, 8, 14
    step = cell + gap
    pad_l = pad_r = 24
    pad_t, pad_b = 88, 78

    blocks, x = [], pad_l
    for year in years:
        columns = max(1, -(-sum(by_year[year].values()) // stack))
        width = columns * step - gap
        blocks.append((year, x, width))
        x += width + year_gap
    plot_w = x - year_gap - pad_l
    plot_h = stack * step - gap
    width, height = pad_l + plot_w + pad_r, pad_t + plot_h + pad_b
    base = pad_t + plot_h

    output: list[str] = []
    output.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        'width="100%" role="img" aria-labelledby="sf-t sf-d" '
        'font-family="Archivo, system-ui, sans-serif">'
    )
    output.append('<title id="sf-t">Every bankruptcy candidate, by filing year and outcome</title>')
    output.append(
        f'<desc id="sf-d">{len(rows)} candidates, one square each, grouped into the year of '
        'filing. Block width tracks how many firms failed that year. Colour and texture show '
        'whether the firm could be matched to a traded security.</desc>'
    )
    output.append(
        '<defs><pattern id="hatch" width="4" height="4" patternUnits="userSpaceOnUse" '
        f'patternTransform="rotate(45)"><rect width="4" height="4" fill="{FIG["recessive"]}"/>'
        f'<line x1="0" y1="0" x2="0" y2="4" stroke="{FIG["third"]}" '
        'stroke-width="2.2"/></pattern></defs>'
    )

    fill_for = {
        RESOLVED: FIG["primary"],
        UNREACHABLE: FIG["recessive"],
        INAPPLICABLE: "url(#hatch)",
    }
    for year, x0, _width in blocks:
        sequence: list[str] = []
        for state in STATE_ORDER:
            sequence += [state] * by_year[year].get(state, 0)
        for index, state in enumerate(sequence):
            column, row = divmod(index, stack)
            output.append(
                f'<rect x="{x0 + column * step}" y="{base - cell - row * step}" '
                f'width="{cell}" height="{cell}" fill="{fill_for[state]}"/>'
            )

    for level, (threshold_year, label) in enumerate(THRESHOLDS):
        if threshold_year not in years:
            continue
        line_x = blocks[years.index(threshold_year)][1] - year_gap / 2
        top = pad_t - 16 - level * 26
        output.append(
            f'<line x1="{line_x:.1f}" y1="{top + 6:.1f}" x2="{line_x:.1f}" '
            f'y2="{base + 6}" stroke="{FIG["signal"]}" stroke-width="1.5" '
            'stroke-dasharray="4 3"/>'
        )
        anchor = "end" if line_x > pad_l + plot_w * 0.72 else "start"
        text_x = line_x - 7 if anchor == "end" else line_x + 7
        output.append(
            f'<text x="{text_x:.1f}" y="{top:.1f}" fill="{FIG["signal"]}" '
            f'font-size="10.5" font-weight="700" letter-spacing="0.11em" '
            f'text-anchor="{anchor}">{html.escape(label.upper())}</text>'
        )

    output.append(
        f'<line x1="{pad_l}" y1="{base + 12}" x2="{pad_l + plot_w}" '
        f'y2="{base + 12}" stroke="{FIG["rule"]}" stroke-width="1"/>'
    )
    for year, x0, block_width in blocks:
        output.append(
            f'<text x="{x0 + block_width / 2:.1f}" y="{base + 30}" '
            f'fill="{FIG["muted"]}" font-size="10" text-anchor="middle" '
            f'font-family="IBM Plex Mono, monospace">{str(year)[2:]}</text>'
        )

    legend_x, legend_y = pad_l, base + 58
    for state in STATE_ORDER:
        count = sum(1 for _, item_state in rows if item_state == state)
        label = f"{STATE_LABEL[state]} ({count})"
        legend_width = 18 + len(label) * 6.05
        if legend_x > pad_l and legend_x + legend_width > pad_l + plot_w:
            legend_x, legend_y = pad_l, legend_y + 20
        output.append(
            f'<rect x="{legend_x}" y="{legend_y - 9}" width="10" height="10" '
            f'fill="{fill_for[state]}" stroke="{FIG["rule"]}" stroke-width="0.5"/>'
        )
        output.append(
            f'<text x="{legend_x + 16}" y="{legend_y}" fill="{FIG["muted"]}" '
            f'font-size="11.5">{html.escape(label)}</text>'
        )
        legend_x += legend_width + 16

    if demo:
        output.append(
            f'<text x="{pad_l}" y="20" fill="{FIG["signal"]}" font-size="11" '
            'font-weight="700" letter-spacing="0.12em">'
            'SYNTHETIC PREVIEW. NOT REAL DATA.</text>'
        )
    output.append("</svg>")
    return "\n".join(output)


def hero(
    out_dir: str,
    *,
    paths_n: int = 58,
    seed: int = 1974,
    width: int = 2000,
    height: int = 680,
) -> None:
    try:
        import numpy as np
        from PIL import Image, ImageDraw
    except ImportError:
        print("  SKIPPED hero images: needs numpy and pillow.")
        print("     pip install numpy pillow")
        return

    supersample = 3
    themes = {
        "light": {
            "bg": (255, 255, 255), "survive": (107, 63, 35),
            "default_": (192, 39, 45), "barrier": (123, 103, 92),
            "a_s": 120, "a_d": 245,
        },
        "dark": {
            "bg": (22, 16, 14), "survive": (168, 124, 82),
            "default_": (228, 86, 79), "barrier": (156, 132, 121),
            "a_s": 125, "a_d": 245,
        },
    }
    v0, mu, sigma, horizon, barrier, steps = 100.0, 0.05, 0.34, 3.0, 56.0, 300

    rng = np.random.default_rng(seed)
    dt = horizon / steps
    increments = (
        (mu - 0.5 * sigma**2) * dt
        + sigma * np.sqrt(dt) * rng.standard_normal((4000, steps))
    )
    population = v0 * np.exp(
        np.concatenate(
            [np.zeros((4000, 1)), np.cumsum(increments, axis=1)], axis=1
        )
    )

    rate = float((population[:, -1] < barrier).mean())
    default_count = max(1, round(paths_n * rate))
    sample_rng = np.random.default_rng(seed + 1)
    default_paths = sample_rng.choice(
        np.flatnonzero(population[:, -1] < barrier), default_count, replace=False
    )
    surviving_paths = sample_rng.choice(
        np.flatnonzero(population[:, -1] >= barrier),
        paths_n - default_count,
        replace=False,
    )
    paths = population[np.sort(np.concatenate([default_paths, surviving_paths]))]

    low = float(np.percentile(paths, 0.4))
    high = float(np.percentile(paths, 99.6))
    log_low, span = np.log(low), np.log(high) - np.log(low)
    point_count = paths.shape[1]

    for name, theme in themes.items():
        pixel_width, pixel_height = width * supersample, height * supersample
        image = Image.new("RGB", (pixel_width, pixel_height), theme["bg"])
        layer = Image.new("RGBA", (pixel_width, pixel_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        def xy(index, value):
            return (
                index / (point_count - 1) * pixel_width,
                float(
                    max(
                        min(
                            pixel_height
                            - (np.log(max(value, 1e-9)) - log_low) / span * pixel_height,
                            pixel_height * 2,
                        ),
                        -pixel_height,
                    )
                ),
            )

        endpoints = paths[:, -1]
        for path_index in np.argsort(endpoints)[::-1]:
            defaulted = endpoints[path_index] < barrier
            alpha = theme["a_d"] if defaulted else theme["a_s"]
            colour = theme["default_"] if defaulted else theme["survive"]
            draw.line(
                [xy(index, float(paths[path_index, index])) for index in range(point_count)],
                fill=colour + (alpha,),
                width=int(2.1 * supersample) if defaulted else int(1.3 * supersample),
                joint="curve",
            )
        barrier_y = xy(0, barrier)[1]
        for x in range(0, pixel_width, 16 * supersample):
            draw.line(
                [(x, barrier_y), (min(x + 10 * supersample, pixel_width), barrier_y)],
                fill=theme["barrier"] + (255,),
                width=max(2, int(1.8 * supersample)),
            )
        rendered = Image.alpha_composite(image.convert("RGBA"), layer).convert("RGB")
        rendered = rendered.resize((width, height), Image.Resampling.LANCZOS)
        output_path = os.path.join(out_dir, f"hero-paths-{name}.png")
        rendered.save(output_path, optimize=True)
        print(f"  wrote {output_path}  {os.path.getsize(output_path) / 1024:.0f} KB")

    print(f"  population default rate {rate:.1%}; showing {paths_n} paths, {default_count} below barrier")
    print(f"  sigma {sigma:.0%}, mu {mu:.0%}, T {horizon:.0f}y, barrier {barrier:.0f}, seed {seed}")
    print("  caption these parameters. the image asserts them.")


def _write(path: str, body: str, source: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(
            f"<!-- generated by scripts/assets.py from {source}. do not edit by hand. -->\n"
            + body
        )
    print("  wrote", path)


def rasterise(svg_path: str, png_path: str, size: int) -> None:
    with open(svg_path, encoding="utf-8") as fh:
        svg = fh.read()
    wrapper = (
        "<!doctype html><meta charset='utf-8'>"
        "<style>html,body{margin:0;background:transparent}"
        f"svg{{display:block;width:{size}px;height:{size}px}}</style>" + svg
    )
    temporary = png_path + ".html"
    with open(temporary, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(wrapper)
    file_url = Path(temporary).resolve().as_uri()
    code = (
        "from playwright.sync_api import sync_playwright\n"
        "with sync_playwright() as p:\n"
        "    browser = p.chromium.launch()\n"
        f"    page = browser.new_page(viewport={{'width': {size}, 'height': {size}}}, device_scale_factor=1)\n"
        f"    page.goto({file_url!r})\n"
        f"    page.screenshot(path={png_path!r}, omit_background=True)\n"
        "    browser.close()\n"
    )
    try:
        subprocess.run(
            [sys.executable, "-c", code], check=True, capture_output=True, text=True
        )
        print("  wrote", png_path)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        if "playwright" in detail.lower() or isinstance(exc, FileNotFoundError):
            print(f"  SKIPPED {os.path.basename(png_path)}: playwright not available.")
            print("     pip install playwright && python -m playwright install chromium")
        else:
            last_line = detail.strip().splitlines()[-1:] or ["unknown error"]
            print(f"  SKIPPED {os.path.basename(png_path)}: {last_line}")
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="public dir, e.g. frontend/public")
    parser.add_argument(
        "--logo",
        default="break",
        choices=sorted(LOGOS) + ["all"],
        help="which mark to ship; --logo all writes every candidate for review",
    )
    parser.add_argument("--audit", help="resolution audit CSV")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    brand = os.path.join(args.out, "brand")
    figures = os.path.join(args.out, "figures")
    marks = os.path.join(args.out, "marks")
    for directory in (brand, figures, marks):
        os.makedirs(directory, exist_ok=True)

    print("brand")
    kinds = sorted(LOGOS) if args.logo == "all" else [args.logo]
    for kind in kinds:
        suffix = "" if len(kinds) == 1 else f"-{kind}"
        _write(
            os.path.join(brand, f"logo{suffix}.svg"),
            _svg(
                LOGOS[kind](P["red"]),
                description="Red interrupted bar brand mark.",
            ),
            "assets.py",
        )
        _write(
            os.path.join(brand, f"logo{suffix}-dark.svg"),
            _svg(
                LOGOS[kind](P_DARK["red"]),
                description="Light red interrupted bar brand mark for dark grounds.",
            ),
            "assets.py",
        )
        _write(os.path.join(brand, f"icon{suffix}.svg"), icon_svg(kind, P), "assets.py")
        _write(os.path.join(brand, f"lockup{suffix}.svg"), lockup_svg(kind, P), "assets.py")
        _write(
            os.path.join(brand, f"lockup{suffix}-dark.svg"),
            lockup_svg(kind, P_DARK),
            "assets.py",
        )
    if len(kinds) == 1:
        rasterise(os.path.join(brand, "icon.svg"), os.path.join(brand, "favicon-32.png"), 32)
        rasterise(os.path.join(brand, "icon.svg"), os.path.join(brand, "apple-touch-icon.png"), 180)
        rasterise(os.path.join(brand, "icon.svg"), os.path.join(brand, "icon-512.png"), 512)

    print("marks")
    for name in MARKS:
        _write(os.path.join(marks, f"{name}.svg"), mark_svg(name), "assets.py")

    print("figures")
    if args.demo:
        rows, source = demo_rows(), "SYNTHETIC DEMO DATA"
    elif args.audit:
        rows, source = load_audit(args.audit), args.audit
    else:
        rows, source = None, None
    if rows:
        _write(
            os.path.join(figures, "sample-field.svg"),
            sample_field_svg(rows, demo=args.demo),
            source,
        )
        resolved = sum(1 for _, state in rows if state == RESOLVED)
        print(f"  {len(rows)} candidates, {resolved} resolved ({resolved / len(rows):.1%})")
    else:
        print("  skipped sample field: pass --audit PATH or --demo")

    print("hero")
    hero(figures)

    print("\ndone. assets live under:")
    for directory, description in (
        (brand, "logo, lockup, favicon"),
        (marks, "section marks"),
        (figures, "figures and hero"),
    ):
        count = len([name for name in os.listdir(directory) if not name.endswith(".html")])
        print(f"  {directory}  ({count} files: {description})")


if __name__ == "__main__":
    main()
