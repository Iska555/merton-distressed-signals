import html as html_module
from html.parser import HTMLParser
import json
from pathlib import Path
import re


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


class _ClassTextParser(HTMLParser):
    def __init__(self, class_name: str):
        super().__init__()
        self.class_name = class_name
        self.depth = 0
        self.current: list[str] = []
        self.rows: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        classes = dict(attrs).get("class", "") or ""
        if self.depth:
            self.depth += 1
        elif self.class_name in classes.split():
            self.depth = 1

    def handle_endtag(self, tag: str):
        if not self.depth:
            return
        self.depth -= 1
        if not self.depth:
            self.rows.append(" ".join(" ".join(self.current).split()))
            self.current = []

    def handle_data(self, data: str):
        if self.depth:
            self.current.append(data)


def texts_by_class(rendered: str, class_name: str) -> list[str]:
    parser = _ClassTextParser(class_name)
    parser.feed(rendered)
    return parser.rows


def barrow_pairs(rendered: str) -> list[tuple[str, str]]:
    pairs = []
    pattern = re.compile(
        r"^(?P<label>\d{4} to \d{4}) "
        r"(?P<value>\d+ of \d+ \(\d+\.\d+%\))$"
    )
    for row in texts_by_class(rendered, "barrow"):
        match = pattern.fullmatch(row)
        if match:
            pairs.append((match["label"], match["value"]))
    return pairs


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
        (
            era["label"].replace("-", " to 20", 1),
            f"{era['resolved']} of {era['n']} ({era['rate'] * 100:.1f}%)",
        )
        for era in measurement["by_era"]
    ]

    assert expected == [
        ("2010 to 2011", "6 of 47 (12.8%)"),
        ("2012 to 2014", "14 of 71 (19.7%)"),
        ("2015 to 2018", "46 of 96 (47.9%)"),
        ("2019 to 2021", "37 of 65 (56.9%)"),
        ("2022 to 2024", "46 of 67 (68.7%)"),
    ]
    assert barrow_pairs(rendered) == expected


def test_mispricing_renders_checked_source_metadata_without_a_pending_flag():
    payload = json.loads(
        (ROOT / "frontend" / "public" / "data" / "shadow_rating.json").read_text(
            encoding="utf-8"
        )
    )
    rendered = html_module.unescape(
        (
            ROOT / "frontend" / ".next" / "server" / "app" / "mispricing.html"
        ).read_text(encoding="utf-8")
    )
    normalised = " ".join(re.sub(r"<!--.*?-->", "", rendered).split())

    assert "pending-verification" not in normalised.lower()
    for field in ("large_verified", "small_verified"):
        assert payload["source"][field] in normalised
    assert "checked against source" in normalised
    assert "zero mismatches" in normalised


def test_mispricing_renders_exact_boundary_count_and_derived_rate():
    payload = json.loads(
        (ROOT / "frontend" / "public" / "data" / "shadow_rating.json").read_text(
            encoding="utf-8"
        )
    )
    diagnostics = payload["band_diagnostics"]
    expected = (
        f"{diagnostics['within_30pct_of_boundary_n']:,} of "
        f"{diagnostics['universe_n']:,} "
        f"({diagnostics['share_within_30pct_of_boundary'] * 100:.1f}%)"
    )
    quarter = diagnostics["universe_quarter"].replace("Q", " Q")
    rendered = html_module.unescape(
        (
            ROOT / "frontend" / ".next" / "server" / "app" / "mispricing.html"
        ).read_text(encoding="utf-8")
    )
    normalised = " ".join(re.sub(r"<!--.*?-->", "", rendered).split())

    assert expected in normalised
    assert f"{quarter} universe" in normalised


def test_base_rate_copy_frames_slider_values_as_illustrative_assumptions():
    text = source_text(
        ROOT / "frontend" / "app" / "discrimination" / "BaseRateExplorer.tsx"
    ).lower()

    assert "us corporate default rates have run roughly" not in text
    assert "illustrative user-selected assumptions" in text
    assert "not historical estimates or fitted study values" in text
    assert "low-base-rate through severe-stress scenarios" in text


def test_public_empirical_copy_includes_the_specified_cell_counts():
    homepage = source_text(ROOT / "frontend" / "app" / "page.tsx")
    data_page = source_text(ROOT / "frontend" / "app" / "data" / "page.tsx")
    measurement = source_text(ROOT / "frontend" / "app" / "measurement" / "page.tsx")

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
