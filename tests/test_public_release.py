from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SOURCE = [
    ROOT / "frontend" / "app" / "page.tsx",
    ROOT / "frontend" / "app" / "discrimination" / "page.tsx",
    ROOT / "frontend" / "app" / "case-studies" / "page.tsx",
    ROOT / "frontend" / "components" / "Nav.tsx",
]


def test_public_release_contains_no_unfinished_module_copy():
    text = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC_SOURCE)
    for phrase in ("Awaiting sample", "In progress", "Not yet computed", "does not exist yet"):
        assert phrase not in text


def test_evidence_route_is_not_published_before_results_exist():
    assert not (ROOT / "frontend" / "app" / "evidence" / "page.tsx").exists()
    nav = (ROOT / "frontend" / "components" / "Nav.tsx").read_text(encoding="utf-8")
    assert "href: '/evidence'" not in nav
