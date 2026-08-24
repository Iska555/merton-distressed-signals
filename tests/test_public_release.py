import html as html_module
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SOURCE = sorted(
    path
    for directory in (
        ROOT / "frontend" / "app",
        ROOT / "frontend" / "components",
        ROOT / "frontend" / "lib",
    )
    for path in directory.rglob("*")
    if path.suffix in {".ts", ".tsx"}
)
BENCHMARK_COPY = [
    ROOT / "frontend" / "app" / "page.tsx",
    ROOT / "frontend" / "app" / "mispricing" / "page.tsx",
    ROOT / "frontend" / "app" / "mispricing" / "MispricingClient.tsx",
    ROOT / "frontend" / "components" / "Footer.tsx",
]


def source_text(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_public_release_contains_no_unfinished_module_copy():
    text = "\n".join(source_text(path) for path in PUBLIC_SOURCE).lower()
    for phrase in (
        "awaiting sample",
        "in progress",
        "not yet computed",
        "does not exist yet",
    ):
        assert phrase not in text


def test_evidence_route_is_not_published_before_results_exist():
    assert not (ROOT / "frontend" / "app" / "evidence" / "page.tsx").exists()
    nav = (ROOT / "frontend" / "components" / "Nav.tsx").read_text(encoding="utf-8")
    assert "href: '/evidence'" not in nav


def test_public_copy_frames_the_benchmark_as_periodic_not_live_credit():
    text = "\n".join(source_text(path) for path in BENCHMARK_COPY).lower()
    for stale in (
        "credit investors are charging",
        "credit implies more risk",
        "credit cohort",
        "rating-cohort index average",
        "fred ice oas",
        "fred ice bofa option-adjusted spread indices",
    ):
        assert stale not in text
    assert "january 2026 periodic synthetic-rating default-spread benchmark" in text


def test_retracted_wilson_interval_uses_the_computed_rounded_bounds():
    sources = (
        ROOT / "frontend" / "app" / "measurement" / "page.tsx",
        ROOT / "docs" / "DECISIONS.md",
        ROOT / "docs" / "RESOLUTION_AUDIT.md",
        ROOT / "scripts" / "check_published_figures.py",
    )

    for path in sources:
        text = source_text(path)
        assert "60% to 91%" in text
        assert "61% to 93%" not in text


def test_homepage_figure_one_renders_all_measurement_era_cell_counts():
    measurement = json.loads(
        (ROOT / "frontend" / "public" / "data" / "measurement.json").read_text(
            encoding="utf-8"
        )
    )
    page = ROOT / "frontend" / ".next" / "server" / "app" / "index.html"
    assert page.exists(), "frontend build is absent; run npm run build before this test"
    rendered = html_module.unescape(page.read_text(encoding="utf-8"))
    expected = [
        f"{era['resolved']} of {era['n']} ({era['rate'] * 100:.1f}%)"
        for era in measurement["by_era"]
    ]

    assert expected == [
        "6 of 47 (12.8%)",
        "14 of 71 (19.7%)",
        "46 of 96 (47.9%)",
        "37 of 65 (56.9%)",
        "46 of 67 (68.7%)",
    ]
    for text in expected:
        assert text in rendered


def test_public_empirical_copy_includes_the_specified_cell_counts():
    homepage = source_text(ROOT / "frontend" / "app" / "page.tsx")
    data_page = source_text(ROOT / "frontend" / "app" / "data" / "page.tsx")
    measurement = source_text(ROOT / "frontend" / "app" / "measurement" / "page.tsx")
    mispricing = source_text(
        ROOT / "frontend" / "app" / "mispricing" / "MispricingClient.tsx"
    )

    for phrase in (
        "149 of 346 (43.1%)",
        "6 of 47 (12.8%) to 46 of 67 (68.7%)",
        "29 of 346 (8.4%)",
    ):
        assert phrase in homepage
    assert "6 of 47 (12.8%) to 46 of 67 (68.7%)" in data_page
    for phrase in (
        "Measurement data unavailable.",
        "6 of 47 (12.8%) and 46 of 67 (68.7%)",
        "14 of 47 (30%) and 5 of 96 (5%)",
        "0 of 13; 13 of 34 (38%) against 46 of 96 (48%); 9 of 19 (47%) against 37 of 65 (57%)",
        "2 of 9 (22%) against 6 of 47 (13%) through 27 of 33 (82%) against 46 of 67 (69%)",
        "1 of 14 (7%) against the 6 of 47 (13%) era",
        "41 of 346 (11.8%) candidates and 14 of 149 (9.4%) resolved",
        "19 of 24 (79%)",
        "60% to 91%",
    ):
        assert phrase in measurement
    assert "51%" not in measurement
    assert "61% to 93%" not in measurement
    assert "3,132-filer 2023 Q1 universe" in mispricing
