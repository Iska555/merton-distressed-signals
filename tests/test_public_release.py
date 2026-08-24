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
        "not yet computed",
        "does not exist yet",
    ):
        assert phrase not in text


def test_unfinished_research_routes_are_not_published():
    assert not (ROOT / "frontend" / "app" / "evidence" / "page.tsx").exists()
    assert not (ROOT / "frontend" / "app" / "measurement" / "page.tsx").exists()
    assert not (ROOT / "frontend" / "public" / "marks" / "evidence.svg").exists()
    nav = (ROOT / "frontend" / "components" / "Nav.tsx").read_text(encoding="utf-8")
    assert "href: '/evidence'" not in nav
    assert "href: '/measurement'" not in nav


def test_withdrawn_measurement_artifacts_are_not_in_the_public_directory():
    public = ROOT / "frontend" / "public"
    for relative in (
        "data/measurement.json",
        "data/verification.json",
        "figures/sample-field.svg",
    ):
        assert not (public / relative).exists(), relative


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
        ROOT / "docs" / "DECISIONS.md",
        ROOT / "docs" / "RESOLUTION_AUDIT.md",
        ROOT / "scripts" / "check_published_figures.py",
    )

    for path in sources:
        text = source_text(path)
        assert "60% to 91%" in text
        assert "61% to 93%" not in text


def test_release_build_ships_five_routes_and_holds_measurement():
    build = ROOT / "frontend" / ".next" / "server" / "app"
    for route in ("model", "mispricing", "discrimination", "case-studies", "data"):
        assert (build / f"{route}.html").exists(), route
    assert not (build / "measurement.html").exists()


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


def test_public_release_exposes_the_withdrawal_without_current_sample_claims():
    build = ROOT / "frontend" / ".next" / "server" / "app"
    route_files = (
        "index.html",
        "model.html",
        "mispricing.html",
        "discrimination.html",
        "case-studies.html",
        "data.html",
    )
    pages = {
        name: html_module.unescape((build / name).read_text(encoding="utf-8"))
        for name in route_files
    }
    homepage = pages["index.html"]
    data_page = pages["data.html"]

    assert 'data-research-status="withdrawn"' in homepage
    assert 'data-research-status="withdrawn"' in data_page
    for correction_fact in (
        "offsets by 10 while the SEC returned 100 results per response",
        "stopped after four requests",
        "647 reported hits",
        "128 unique retrieved documents",
        "99 visible registrants",
        "25-row selection",
        "no known inclusion probability",
        "Every rate derived from that set is withdrawn",
    ):
        assert correction_fact in homepage
        assert correction_fact in data_page
    assert "relevance-ranked, not chronological" in homepage
    assert "ranked results by relevance rather than filing date" in data_page

    built_text = " ".join(pages.values())
    public_text = " ".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (ROOT / "frontend" / "public").rglob("*")
        if path.is_file() and path.suffix in {".json", ".svg", ".txt", ".webmanifest"}
    )
    shipped = f"{built_text} {public_text}"
    for withdrawn_claim in (
        "149 of 346",
        "43.1%",
        "29 of 346",
        "8.4%",
        "12.8%",
        "19.7%",
        "47.9%",
        "56.9%",
        "68.7%",
        'href="/measurement"',
        '"/data/measurement.json"',
        '"/data/verification.json"',
        '"/figures/sample-field.svg"',
    ):
        assert withdrawn_claim not in shipped


def test_current_reproduction_guidance_uses_the_frozen_python_environment():
    current_guidance = (
        ROOT / "README.md",
        ROOT / "frontend" / "README.md",
        ROOT / "frontend" / "app" / "data" / "page.tsx",
        ROOT / "frontend" / "app" / "mispricing" / "page.tsx",
    )
    ambient_python = re.compile(r"(?<!uv run --frozen )python -m scripts\.")

    for path in current_guidance:
        text = path.read_text(encoding="utf-8")
        assert not ambient_python.search(text), path


def test_superseded_release_specs_cannot_be_mistaken_for_current_instructions():
    current = "docs/superpowers/specs/2026-08-24-measurement-integrity-census-design.md"
    historical = (
        ROOT
        / "docs"
        / "superpowers"
        / "specs"
        / "2026-08-24-phase-0-credibility-foundation.md",
        ROOT
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-08-24-phase-0-credibility-foundation.md",
        ROOT
        / "docs"
        / "superpowers"
        / "specs"
        / "2026-08-23-chocolate-burgundy-assets-design.md",
        ROOT
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-08-23-chocolate-burgundy-assets.md",
    )

    for path in historical:
        heading = "\n".join(path.read_text(encoding="utf-8").splitlines()[:12])
        assert "SUPERSEDED" in heading
        assert current in heading


def test_withdrawn_measurement_has_no_dormant_publication_api():
    python_builder = (ROOT / "scripts" / "build_site_data.py").read_text(
        encoding="utf-8"
    )
    typescript_loader = (ROOT / "frontend" / "lib" / "siteData.ts").read_text(
        encoding="utf-8"
    )

    assert "def build_measurement" not in python_builder
    assert "def build_verification" not in python_builder
    assert "getMeasurement" not in typescript_loader
