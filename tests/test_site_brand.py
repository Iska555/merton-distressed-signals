from __future__ import annotations

import html as html_module
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
        ("/measurement", "measurement"),
        ("/evidence", "evidence"),
        ("/discrimination", "discrimination"),
        ("/case-studies", "cases"),
        ("/data", "data"),
    ],
)
def test_each_route_first_heading_has_a_hidden_section_mark(route: str, mark: str):
    page = _page(route)

    assert f'src="/marks/{mark}.svg"' in page
    image_start = page.index(f'src="/marks/{mark}.svg"')
    image = page[page.rfind("<img", 0, image_start) : page.index(">", image_start) + 1]
    assert 'aria-hidden="true"' in image
    assert 'alt=""' in image


def test_homepage_cards_have_all_six_module_marks():
    page = _page("/")

    for mark in ("model", "mispricing", "measurement", "evidence", "discrimination", "data"):
        assert f'src="/marks/{mark}.svg"' in page


def test_sample_field_is_the_requested_numbered_figure_on_both_pages():
    home = _page("/")
    measurement = _page("/measurement")

    assert 'src="/figures/sample-field.svg"' in home
    assert 'src="/figures/sample-field.svg"' in measurement
    assert '<span class="fignum">Figure 2</span>' in home
    assert '<span class="fignum">Figure 1</span>' in measurement
    assert "n = 346 candidates" in home
    assert "n = 346 candidates" in measurement
