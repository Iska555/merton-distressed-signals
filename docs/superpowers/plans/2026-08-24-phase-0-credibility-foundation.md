# Phase 0 Credibility Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current research branch into a complete, reproducible and professionally scoped public release without entering the matched-sample research phase.

**Architecture:** Retain the static research architecture under `src/`, `scripts/`, committed data and `frontend/`. Remove the unsupported FastAPI predecessor, expose only complete public routes, add a machine-readable source registry and route every quality check through one cross-platform Python command shared by local development and CI.

**Tech Stack:** Python 3.11+, NumPy, pandas, SciPy, pytest, Pillow, Playwright, Next.js 16, React 19, TypeScript and GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-24-phase-0-credibility-foundation.md`

## Global Constraints

- Preserve the chocolate, burgundy and red visual system already committed.
- Do not change any published bankruptcy-study number in Phase 0.
- Do not add predictive performance results before the matched sample exists.
- Do not use em dashes in source or rendered copy.
- Keep generated brand and figure assets byte-identical.
- Keep every current rate accompanied by its cell count.
- Do not require a running API server for any route.
- Do not commit credentials, raw API responses, dependency folders or build output.
- Use test-first implementation for behavior and regression guards.

---

### Task 1: Define the supported Python project and retire the legacy backend

**Files:**
- Create: `pyproject.toml`
- Create: `tests/test_repository_hygiene.py`
- Modify: `.env.example`
- Modify: `src/config.py`
- Modify: `scripts/build_site_data.py`
- Delete: `backend/`

**Interfaces:**
- Consumes: root checkout and current `src.config.ROOT`
- Produces: root optional dependency groups `dev` and `assets`; root `.env` loading; a repository guard that rejects a restored legacy backend or root-level test PNGs

- [ ] **Step 1: Write failing repository-hygiene and environment tests**

```python
from __future__ import annotations

import importlib
from pathlib import Path

import dotenv


ROOT = Path(__file__).resolve().parents[1]


def test_legacy_backend_is_not_part_of_the_supported_checkout():
    assert not (ROOT / "backend").exists()


def test_tests_do_not_leave_visualization_pngs_at_repository_root():
    assert not list(ROOT.glob("output_*.png"))


def test_config_loads_credentials_from_root_env(monkeypatch):
    calls: list[Path] = []
    monkeypatch.setattr(dotenv, "load_dotenv", lambda path: calls.append(Path(path)))
    import src.config as config

    importlib.reload(config)

    assert calls == [config.ROOT / ".env"]
```

- [ ] **Step 2: Run the focused test and confirm the expected failures**

Run: `python -m pytest tests/test_repository_hygiene.py -q`

Expected: failures because `backend/` exists and `src.config` loads `backend/.env`.

- [ ] **Step 3: Add root project metadata**

Create `pyproject.toml` with `requires-python = ">=3.11"`, runtime dependencies on
NumPy, pandas, SciPy and python-dotenv, an `assets` extra for Pillow and Playwright,
a `dev` extra for pytest, setuptools package discovery for `src*` and `scripts*`,
and pytest configured to collect only `tests/`.

- [ ] **Step 4: Move credential loading to root `.env`**

Change both current `ROOT / "backend" / ".env"` calls to `ROOT / ".env"`. Update
`.env.example` to say `Copy to .env`, preserve the revoked-key history note, and
keep all variable descriptions unchanged.

- [ ] **Step 5: Remove the unsupported backend tree**

Delete the 37 tracked files under `backend/`. Do not move them elsewhere. Git history
is the recovery mechanism, and `docs/PHASE0_DATA_INVENTORY.md` remains the record of
why the predecessor was retired.

- [ ] **Step 6: Run the focused and root tests**

Run: `python -m pytest tests/test_repository_hygiene.py -q`

Expected: all tests in the file pass.

Run: `python -m pytest tests -q`

Expected: all supported tests pass.

- [ ] **Step 7: Commit Task 1**

```text
git add pyproject.toml .env.example src/config.py scripts/build_site_data.py tests/test_repository_hygiene.py backend
git commit -m "chore: retire unsupported legacy backend"
```

### Task 2: Expose only complete public research modules

**Files:**
- Create: `tests/test_public_release.py`
- Modify: `frontend/components/Nav.tsx`
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/app/discrimination/page.tsx`
- Modify: `frontend/app/case-studies/page.tsx`
- Modify: `tests/test_site_brand.py`
- Delete: `frontend/app/evidence/page.tsx`

**Interfaces:**
- Consumes: six complete module routes and generated section marks
- Produces: public navigation and homepage cards for Model, Mispricing, Measurement, Discrimination, Cases and Data; no unfinished public route or copy

- [ ] **Step 1: Write failing release-boundary tests**

```python
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
```

- [ ] **Step 2: Run the focused tests and confirm the expected failures**

Run: `python -m pytest tests/test_public_release.py -q`

Expected: failures identify the existing Evidence route and unfinished copy.

- [ ] **Step 3: Replace the homepage Evidence card with Cases**

Keep six cards. The Cases card links to `/case-studies`, uses the `cases` mark, and
describes the completed boundary cases as evidence about data reach and model
applicability. Change `Six modules, built to be checked` to `Six completed modules,
built to be checked`. Change `Not accurate, yet` to `Not an accuracy claim` and state
that the current release makes no empirical discrimination claim.

- [ ] **Step 4: Remove unfinished route and sections**

Remove Evidence from `LINKS` and delete its page. On Discrimination, retain the
interactive base-rate exhibit and fixed rules but remove the `Measured discrimination`
callout. On Cases, remove `Computed cases` and rewrite the introduction around three
completed exclusion case studies.

- [ ] **Step 5: Update built-site brand expectations**

Remove `/evidence` from the route-mark parameterization. Change the homepage mark
inventory to `model`, `mispricing`, `measurement`, `discrimination`, `cases`, `data`.

- [ ] **Step 6: Run release tests and frontend lint**

Run: `python -m pytest tests/test_public_release.py -q`

Expected: pass.

Run: `npm run lint` from `frontend/`.

Expected: exit 0 with no ESLint findings.

- [ ] **Step 7: Commit Task 2**

```text
git add frontend tests/test_public_release.py tests/test_site_brand.py
git commit -m "content: publish only completed research modules"
```

### Task 3: Enforce source licensing and add a data-source registry

**Files:**
- Create: `frontend/public/data/SOURCES.json`
- Create: `docs/DATA_SOURCES.md`
- Create: `tests/test_data_sources.py`
- Modify: `.env.example`
- Modify: `src/config.py`
- Modify: `src/models/shadow_rating.py`
- Modify: `scripts/build_site_data.py`
- Modify: `frontend/app/data/page.tsx`
- Modify: `frontend/app/mispricing/page.tsx`
- Modify: `frontend/app/mispricing/MispricingClient.tsx`
- Modify: `frontend/lib/shadowRating.ts`
- Modify: `frontend/public/data/shadow_rating.json`
- Modify: `frontend/public/data/MANIFEST.json`
- Delete: `frontend/public/data/cohort_spreads.json`
- Delete: `frontend/public/data/spread_corroboration.json`

**Interfaces:**
- Consumes: official SEC, FRED, ICE, Tiingo and Damodaran source terms; the verified `DAMODARAN_SPREAD_BPS_JAN2026` mapping
- Produces: a downloadable JSON array whose records contain `id`, `publisher`, `official_url`, `used_for`, `access`, `terms_url`, `redistribution`, `point_in_time_limit` and `known_failure_mode`; `shadow_rating.json.benchmark_spread_bps`; a Mispricing module that consumes only redistributable benchmark data

- [ ] **Step 1: Write failing registry and redistribution tests**

```python
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "frontend" / "public" / "data" / "SOURCES.json"
REQUIRED = {
    "id", "publisher", "official_url", "used_for", "access", "terms_url",
    "redistribution", "point_in_time_limit", "known_failure_mode",
}


def test_source_registry_is_complete_and_uses_official_links():
    rows = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert {row["id"] for row in rows} == {
        "sec-edgar-search", "sec-companyfacts", "sec-dera-fsds",
        "fred-ice-bofa-oas", "tiingo-prices", "damodaran-synthetic-rating",
    }
    for row in rows:
        assert REQUIRED <= row.keys()
        assert row["official_url"].startswith("https://")
        assert row["terms_url"].startswith("https://")
        assert all(str(row[field]).strip() for field in REQUIRED)


def test_restricted_top_level_market_data_is_not_publicly_committed():
    public = ROOT / "frontend" / "public" / "data"
    assert not (public / "cohort_spreads.json").exists()
    assert not (public / "spread_corroboration.json").exists()
    builder = (ROOT / "scripts" / "build_site_data.py").read_text(encoding="utf-8")
    assert "BAMLC0A" not in builder
    assert "BAMLH0A" not in builder


def test_shadow_rating_payload_carries_the_permitted_periodic_benchmark():
    payload = json.loads(
        (ROOT / "frontend" / "public" / "data" / "shadow_rating.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["benchmark_spread_bps"]["BBB"] == 111
    assert payload["benchmark_source"]["publisher"] == "NYU Stern, Aswath Damodaran"
```

- [ ] **Step 2: Run the focused test and confirm the expected failures**

Run: `python -m pytest tests/test_data_sources.py -q`

Expected: failures because `SOURCES.json` and the benchmark payload fields do not
exist, while restricted public spread files and FRED series retrieval still exist.

- [ ] **Step 3: Remove restricted exact observations from public outputs**

Delete the two public spread JSON files and their MANIFEST entries. Remove the FRED
series IDs, API retrieval and corroboration writer from `scripts/build_site_data.py`.
Remove `FRED_API_KEY` from `.env.example` and `src/config.py`; retain the public-domain
risk-free identifier only if another supported module consumes it.

- [ ] **Step 4: Emit the permitted periodic benchmark from one source of truth**

Export `DAMODARAN_SPREAD_BPS_JAN2026` from `src.models.shadow_rating`. Add it to
`shadow_rating.json` as `benchmark_spread_bps` with `benchmark_source` copied from the
existing verified source metadata. Update `RatingTables` to expose those fields.

- [ ] **Step 5: Reframe the Mispricing module around the periodic benchmark**

Remove the separate `spreads` prop and `cohort_spreads.json` reader. Compute the
benchmark from `tables.benchmarkSpreadBps[rating.rating]`. Describe it as the January
2026 Damodaran synthetic-rating default spread, not an ICE index, live credit price or
issuer bond. Preserve the independent equity and accounting input paths, the size-band
sensitivity and the warning that the divergence is a screening direction rather than
tradable basis points.

- [ ] **Step 6: Create the source registry**

Add one record for each required source. State that committed outputs are derived
research artifacts rather than redistributed raw feeds. The FRED row records ICE OAS
as reviewed but excluded from public output because its series notes restrict
publication. The Tiingo row states that starter and trial plans prohibit persistent
raw storage and that only non-reconstructable derived products may be retained or
distributed under its terms. Record ticker-reuse and delisted-history risks for the
price source and historical disclosure limits for SEC sources.

- [ ] **Step 7: Document provenance policy and update the Data page**

Create `docs/DATA_SOURCES.md` explaining source selection, credentials, raw-data
retention, committed-output policy, point-in-time rules and the difference between
public access and unrestricted redistribution. Link to `SOURCES.json`. Remove the
FRED-versus-Damodaran exact-value table and FRED credential statement from the Data
page. Add a source-line link labelled `Download the source and licensing registry`.
Preserve every bankruptcy-study number.

- [ ] **Step 8: Run focused tests, frontend lint and production build**

Run: `python -m pytest tests/test_data_sources.py -q`

Expected: pass.

Run: `npm run lint` from `frontend/`.

Expected: exit 0.

Run: `npm run build` from `frontend/`.

Expected: a static `/mispricing` and `/data` route with no restricted JSON request.

- [ ] **Step 9: Commit Task 3**

```text
git add .env.example src scripts frontend docs/DATA_SOURCES.md tests/test_data_sources.py
git commit -m "fix: enforce public data licensing boundaries"
```

### Task 4: Add one cross-platform verification entry point and professional documentation

**Files:**
- Create: `scripts/verify.py`
- Create: `tests/test_verify.py`
- Modify: `Makefile`
- Modify: `.github/workflows/assets.yml`
- Modify: `README.md`
- Modify: `frontend/README.md`

**Interfaces:**
- Consumes: `scripts.check_assets`, `scripts.check_published_figures`, npm scripts and pytest
- Produces: `python -m scripts.verify`; `verification_commands(root: Path) -> tuple[Check, ...]`; CI and Makefile delegating to the same command

- [ ] **Step 1: Write failing verification-command tests**

```python
from pathlib import Path

from scripts.verify import verification_commands


def test_verification_covers_assets_figures_frontend_and_tests():
    root = Path("/repo")
    checks = verification_commands(root)
    assert [check.name for check in checks] == [
        "generated assets", "published figures", "frontend lint",
        "frontend build", "root tests",
    ]
    assert checks[0].argv[:3] == ("python", "-m", "scripts.check_assets")
    assert checks[-1].argv == ("python", "-m", "pytest", "tests", "-q")
    assert checks[2].cwd == root / "frontend"
    assert checks[3].cwd == root / "frontend"
```

- [ ] **Step 2: Run the focused test and confirm the import failure**

Run: `python -m pytest tests/test_verify.py -q`

Expected: import failure because `scripts.verify` does not exist.

- [ ] **Step 3: Implement the verification runner**

Define an immutable `Check` dataclass with `name`, `argv` and `cwd`. Build commands
using `Path(sys.executable).name` normalized to `python` for the test-facing plan,
but execute Python checks with `sys.executable`. Run checks sequentially with
`subprocess.run(..., check=True)`, print a concise heading for each, stop on the
first failure and return its exit status.

- [ ] **Step 4: Route Make and CI through the runner**

Add a `verify` target that invokes `$(PYTHON) -m scripts.verify`. Rename the workflow
display name to `Quality`, install the project with `python -m pip install -e
'.[dev,assets]'`, install Chromium, install frontend dependencies and run only the
canonical verification command.

- [ ] **Step 5: Rewrite the documentation entry points**

Open the root README with the 149 of 346, 43.1 percent finding and a short `Why it
matters` paragraph. Replace the unfinished status table with `Current release` and
`Next research milestone`. Update installation to use the root project extras, root
`.env`, and the canonical verification command. Remove `backend/` from architecture
and supported commands. Link `docs/DATA_SOURCES.md`.

Replace the generated Next.js `frontend/README.md` with a concise site-development
guide covering static inputs, development, lint, build and the rule that unfinished
research routes stay unpublished.

- [ ] **Step 6: Run focused tests and documentation guards**

Run: `python -m pytest tests/test_verify.py tests/test_repository_hygiene.py tests/test_public_release.py tests/test_data_sources.py tests/test_no_em_dash.py -q`

Expected: pass.

- [ ] **Step 7: Run the canonical verification command**

Run: `python -m scripts.verify`

Expected: generated assets current, published figures current, frontend lint clean,
frontend production build successful and all supported tests passing.

- [ ] **Step 8: Commit Task 4**

```text
git add scripts/verify.py tests/test_verify.py Makefile .github/workflows/assets.yml README.md frontend/README.md
git commit -m "build: add canonical project verification"
```

### Task 5: Release verification and deployment handoff

**Files:**
- Modify only if verification or review identifies a Phase 0 defect

**Interfaces:**
- Consumes: completed Tasks 1 through 4
- Produces: reviewed branch, clean working tree, exact deployment handoff

- [ ] **Step 1: Run source-policy searches**

Run: `rg -n -i "awaiting sample|in progress|not yet computed|does not exist yet" README.md frontend`

Expected: no matches.

Run: `rg -n "backend/" README.md .env.example src scripts frontend .github Makefile`

Expected: no supported-path matches.

- [ ] **Step 2: Run the canonical verification command from a clean build state**

Run: `python -m scripts.verify`

Expected: all five checks pass.

- [ ] **Step 3: Review the complete Phase 0 diff**

Review from the Phase 0 merge base through `HEAD` for spec compliance, destructive
scope, research-number drift, command correctness and public copy quality. Address
all critical or important findings and re-run the affected checks.

- [ ] **Step 4: Confirm repository state**

Run: `git status --short --branch`

Expected: clean working tree on `codex/chocolate-burgundy-assets`.

- [ ] **Step 5: Prepare the external deployment handoff**

Report the commits, tests, removed legacy scope and recovery path. Do not push, merge,
open a pull request or publish the site without explicit user approval because each
changes external state.
