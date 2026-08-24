from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SOURCE = [
    ROOT / "frontend" / "app" / "page.tsx",
    ROOT / "frontend" / "app" / "discrimination" / "page.tsx",
    ROOT / "frontend" / "app" / "case-studies" / "page.tsx",
    ROOT / "frontend" / "components" / "Nav.tsx",
]
BENCHMARK_COPY = [
    ROOT / "frontend" / "app" / "page.tsx",
    ROOT / "frontend" / "app" / "mispricing" / "page.tsx",
    ROOT / "frontend" / "app" / "mispricing" / "MispricingClient.tsx",
    ROOT / "frontend" / "components" / "Footer.tsx",
]


def test_public_release_contains_no_unfinished_module_copy():
    text = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC_SOURCE)
    for phrase in ("Awaiting sample", "In progress", "Not yet computed", "does not exist yet"):
        assert phrase not in text


def test_evidence_route_is_not_published_before_results_exist():
    assert not (ROOT / "frontend" / "app" / "evidence" / "page.tsx").exists()
    nav = (ROOT / "frontend" / "components" / "Nav.tsx").read_text(encoding="utf-8")
    assert "href: '/evidence'" not in nav


def test_public_copy_frames_the_benchmark_as_periodic_not_live_credit():
    text = "\n".join(
        path.read_text(encoding="utf-8") for path in BENCHMARK_COPY
    ).lower()
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
