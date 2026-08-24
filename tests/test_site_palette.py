from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "frontend" / "app" / "globals.css"

LIGHT = {
    "ground": "#FFFFFF",
    "tint": "#FAF5F2",
    "tint-warm": "#F3E9E4",
    "deep": "#5C0F1D",
    "deep-2": "#43101A",
    "ink": "#2B1A17",
    "body": "#4A3830",
    "muted": "#7B675C",
    "signal": "#C0272D",
    "rule": "#E7DCD6",
    "rule-strong": "#CDBAB1",
    "burgundy": "#7A1B2E",
    "chocolate": "#6B3F23",
    "on-deep": "#FFFFFF",
    "on-deep-mute": "#E0BDB6",
    "on-deep-sig": "#F0A868",
    "fig-primary": "#A81C2A",
    "fig-recessive": "#E8DCD6",
    "fig-third": "#6B3F23",
}

DARK = {
    "ground": "#16100E",
    "tint": "#1F1613",
    "tint-warm": "#261B17",
    "deep": "#43101A",
    "deep-2": "#2E0B12",
    "ink": "#F2E7E2",
    "body": "#CDB8B0",
    "muted": "#9C8479",
    "signal": "#E4564F",
    "rule": "#33241F",
    "rule-strong": "#4A352E",
    "burgundy": "#C05A6B",
    "chocolate": "#B98A5A",
}

FORBIDDEN = {
    "#0D4A47", "#0A3B39", "#0F8A66", "#12604A", "#74AC94", "#2FA37E",
    "#1E3033", "#3E5257", "#5F7176", "#DCE3E1", "#B9C6C3", "#F2F5F4",
    "#FBF6EF", "#9DC4BF", "#E6ECEA", "#0F1618", "#16211F", "#1C1E1A",
    "#072E2C", "#E9EFEC", "#B5C4C2", "#8698A0", "#253232", "#3A4B4A",
    "#223030", "#34D399", "#10B981", "#2DD4BF", "#14B8A6", "#B4530C",
    "#E08A3C", "#C2610F", "#D0722A",
}


def _tokens(selector: str) -> dict[str, str]:
    text = CSS.read_text(encoding="utf-8")
    match = re.search(rf"{re.escape(selector)}\s*\{{(.*?)\n\}}", text, re.DOTALL)
    assert match, f"missing {selector} token block"
    return {
        name: value.strip()
        for name, value in re.findall(r"--([a-z0-9-]+):\s*([^;]+);", match.group(1))
    }


def _linear(channel: int) -> float:
    value = channel / 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _luminance(colour: str) -> float:
    channels = [int(colour[index : index + 2], 16) for index in (1, 3, 5)]
    red, green, blue = (_linear(channel) for channel in channels)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast(first: str, second: str) -> float:
    high, low = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def test_theme_tokens_match_the_approved_palette():
    """
    Dark is the default, so it is bare :root that must carry the dark values.
    Light is the opt-in and lives under [data-theme="light"]. Asserting the
    values against those two selectors specifically is what keeps the default
    from silently flipping back.
    """
    dark = _tokens(":root")
    light = _tokens(':root[data-theme="light"]')

    for name, value in DARK.items():
        assert dark[name].upper() == value, name
    for name, value in LIGHT.items():
        # The band foregrounds are shared, so they resolve from :root.
        expected = light.get(name, dark.get(name, ""))
        assert expected.upper() == value, name


def test_dark_is_the_default_theme():
    """
    Three things have to agree or the first paint is wrong: the cascade, the
    restore script, and the toggle. The cascade is checked above. Here we pin
    the other two to the light opt-in.
    """
    css = CSS.read_text(encoding="utf-8")
    assert ':root[data-theme="dark"]' not in css, (
        "a dark-attribute selector means dark is no longer the base theme"
    )
    assert "color-scheme: dark;" in css

    layout = (ROOT / "frontend" / "app" / "layout.tsx").read_text(encoding="utf-8")
    assert "getItem('dcs-theme')==='light'" in layout
    assert "dataset.theme='light'" in layout

    toggle = (ROOT / "frontend" / "components" / "ThemeToggle.tsx").read_text(
        encoding="utf-8"
    )
    assert "dataset.theme === 'light' ? 'dark' : 'light'" in toggle


def test_the_default_ground_is_dark_in_rendered_html():
    """The built page must not ship a light theme attribute on the document."""
    page = (ROOT / "frontend" / ".next" / "server" / "app" / "index.html").read_text(
        encoding="utf-8"
    )
    assert 'data-theme="light"' not in page.split("<body")[0]


def test_body_and_band_text_clear_wcag_aa():
    for foreground, backgrounds in (
        (LIGHT["body"], (LIGHT["ground"], LIGHT["tint"], LIGHT["tint-warm"])),
        (DARK["body"], (DARK["ground"], DARK["tint"], DARK["tint-warm"])),
    ):
        for background in backgrounds:
            assert _contrast(foreground, background) >= 4.5

    for foreground in (LIGHT["on-deep"], LIGHT["on-deep-mute"], LIGHT["on-deep-sig"]):
        assert _contrast(foreground, LIGHT["deep"]) >= 4.5


def test_no_superseded_palette_hex_remains_in_scoped_files():
    offenders: list[str] = []
    for folder in (ROOT / "frontend", ROOT / "src", ROOT / "docs"):
        for path in folder.rglob("*"):
            if not path.is_file() or {"node_modules", ".next"} & set(path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8").upper()
            except UnicodeDecodeError:
                continue
            hits = sorted(colour for colour in FORBIDDEN if colour in text)
            if hits:
                offenders.append(f"{path.relative_to(ROOT)}: {', '.join(hits)}")
    assert not offenders, "\n".join(offenders)


def test_homepage_two_series_chart_uses_texture_not_hue_alone():
    home = (ROOT / "frontend" / ".next" / "server" / "app" / "index.html").read_text(
        encoding="utf-8"
    )
    debt_path = re.search(r'<path[^>]+stroke="var\(--series-2\)"[^>]*>', home)
    assert debt_path
    assert "stroke-dasharray" in debt_path.group(0)
