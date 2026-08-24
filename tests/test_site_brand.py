from __future__ import annotations

import html as html_module
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "frontend" / ".next" / "server" / "app"


def _page(route: str) -> str:
    path = BUILD / ("index.html" if route == "/" else f"{route.strip('/')}.html")
    if not path.exists():
        pytest.fail("frontend build is absent; run npm run build before this test")
    return html_module.unescape(path.read_text(encoding="utf-8"))


def test_root_metadata_and_navigation_use_generated_brand_assets():
    page = _page("/")

    assert 'href="/manifest.webmanifest"' in page
    assert 'href="/brand/icon.svg"' in page
    assert 'href="/brand/apple-touch-icon.png"' in page
    assert 'src="/brand/lockup.svg"' in page
    assert 'src="/brand/lockup-dark.svg"' in page
    assert 'data-theme-toggle="true"' in page
    assert 'aria-label="Toggle colour theme"' in page


def test_homepage_uses_hero_paths_and_states_the_asserted_parameters():
    page = _page("/")

    assert 'srcSet="/figures/hero-paths-dark.png"' in page
    assert 'src="/figures/hero-paths-light.png"' in page
    for text in ("sigma 34%", "mu 5%", "horizon 3 years", "barrier 56", "seed 1974"):
        assert text in page


@pytest.mark.parametrize(
    ("route", "mark"),
    [
        ("/model", "model"),
        ("/mispricing", "mispricing"),
        ("/discrimination", "discrimination"),
        ("/case-studies", "cases"),
        ("/data", "data"),
    ],
)
def test_each_route_first_heading_has_a_theme_coloured_hidden_section_mark(
    route: str, mark: str
):
    page = _page(route)

    assert f'data-mark="{mark}"' in page
    mark_start = page.index(f'data-mark="{mark}"')
    element = page[page.rfind("<span", 0, mark_start) : page.index(">", mark_start) + 1]
    assert 'aria-hidden="true"' in element
    assert f'url(/marks/{mark}.svg)' in element


def test_homepage_cards_have_all_six_module_marks():
    page = _page("/")

    for mark in ("model", "mispricing", "measurement", "discrimination", "cases", "data"):
        assert f"url(/marks/{mark}.svg)" in page


def test_withdrawn_sample_field_is_not_rendered_or_published():
    home = _page("/")

    assert 'src="/figures/sample-field.svg"' not in home
    assert not (ROOT / "frontend" / "public" / "figures" / "sample-field.svg").exists()


def test_every_inline_chart_svg_has_title_and_description():
    for route in ("/", "/model"):
        page = _page(route)
        svgs = re.findall(r"<svg\b.*?</svg>", page, flags=re.DOTALL)
        assert svgs
        for svg in svgs:
            assert "<title" in svg
            assert "<desc" in svg
