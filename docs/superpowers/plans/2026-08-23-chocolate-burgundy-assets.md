# Chocolate, Burgundy, and Red Assets Implementation Plan

> **SUPERSEDED IN PART:** Do not execute the sample-field or `/measurement`
> publication tasks in this historical plan. Current authority:
> `docs/superpowers/specs/2026-08-24-measurement-integrity-census-design.md`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the chocolate, burgundy, and red site identity with one deterministic generator and fully wired, accessible assets.

**Architecture:** A Python generator owns brand, mark, and figure outputs under `frontend/public`. Next.js consumes those files by stable public paths, while CSS custom properties own theme switching and chart roles. Python acceptance tests and CI verify output behavior and drift.

**Tech Stack:** Python 3, csv, NumPy, Pillow, Playwright, Next.js 16, React 19, TypeScript, CSS, pytest, GitHub Actions

**Spec:** `docs/superpowers/specs/2026-08-23-chocolate-burgundy-assets-design.md`

## Global Constraints

- Use `break` as the only shipped logo.
- No petrol or green hex may remain in `frontend/`, `src/`, or `docs/`.
- Body text contrast must be at least 4.5:1 on every ground in both themes.
- No chart may encode categories by neighboring warm hue alone.
- Every generated SVG must contain both `<title>` and `<desc>`.
- Every decorative section mark at a use site must have `aria-hidden="true"`.
- The hero caption must state sigma, mu, horizon, barrier, and seed.
- Copy and existing figure number, title, source, and cell-count conventions remain unchanged.
- No em dash may be introduced.

---

### Task 1: Deterministic consolidated asset generator

**Files:**
- Create: `scripts/assets.py`
- Create: `tests/test_assets.py`
- Create: `requirements-assets.txt`

**Interfaces:**
- Consumes: `data/processed/resolution_audit.csv` with `event_year`, `resolved`, and `exclusion_family`
- Produces: `load_audit(path) -> list[tuple[int, str]]`, accessible SVG builders, and `python -m scripts.assets --out PATH --audit PATH`

- [ ] **Step 1: Write failing generator tests**

Create tests with a literal three-row CSV fixture. Assert that `True/resolved`, `False/data_unavailability`, and `False/model_inapplicability` map to the three states and preserve event years. Generate SVGs twice into separate temporary directories and assert byte equality. Parse every SVG and assert one title and one description.

- [ ] **Step 2: Run the focused tests and verify the expected import failure**

Run: `python -m pytest tests/test_assets.py -v`

Expected: collection fails because `scripts.assets` does not exist.

- [ ] **Step 3: Add the supplied generator with compatibility corrections**

Place the supplied implementation in `scripts/assets.py`. Read both the supplied generic columns and this repo's concrete columns. Classify `model_inapplicability` as inapplicable. Remove wall-clock dates from generated comments. Add descriptions to `_svg` and every caller. Keep all three logo functions and retain `break` as the default.

- [ ] **Step 4: Pin generation dependencies and run tests green**

Pin compatible NumPy, Pillow, and Playwright versions in `requirements-assets.txt`. Run `python -m pytest tests/test_assets.py -v` and confirm all tests pass.

- [ ] **Step 5: Commit the generator unit**

Commit message: `feat: consolidate deterministic site assets`

### Task 2: Generate and verify the complete public asset inventory

**Files:**
- Create: `frontend/public/brand/*`
- Create: `frontend/public/marks/*`
- Create: `frontend/public/figures/*`
- Create: `frontend/public/manifest.webmanifest`
- Modify: `tests/test_assets.py`
- Create: `Makefile`
- Create: `.github/workflows/assets.yml`

**Interfaces:**
- Consumes: the Task 1 command line interface and audit CSV
- Produces: stable public paths used by Next.js and `make assets`, `make assets-check`

- [ ] **Step 1: Add a failing inventory and drift test**

Assert the required brand, mark, and figure filenames are generated. Run the generator in two temporary roots and compare every relative path and byte. Assert `sample-field.svg` reports 346 candidates and the resolved count from the audit.

- [ ] **Step 2: Run the focused test and verify missing outputs fail**

Run: `python -m pytest tests/test_assets.py -v`

Expected: failure names absent generated files or incomplete command behavior.

- [ ] **Step 3: Generate committed files and add build automation**

Install pinned dependencies and Chromium, then run `python -m scripts.assets --out frontend/public --audit data/processed/resolution_audit.csv`. Add the web manifest. Add `assets` and non-mutating `assets-check` make targets. Add CI steps for Python setup, pinned dependencies, Chromium, drift check, Python tests, frontend lint, and frontend build.

- [ ] **Step 4: Run generation and drift checks green**

Run: `make assets-check` where make is available, plus the underlying comparison command directly on Windows. Confirm no committed asset changes after regeneration.

- [ ] **Step 5: Commit generated outputs and automation**

Commit message: `build: generate and verify public assets`

### Task 3: Wire metadata, lockup, hero, and route marks

**Files:**
- Create: `frontend/components/SectionMark.tsx`
- Modify: `frontend/components/Nav.tsx`
- Modify: `frontend/app/layout.tsx`
- Modify: `frontend/app/page.tsx`
- Modify: all seven interior `frontend/app/*/page.tsx` route files
- Modify: `frontend/app/globals.css`

**Interfaces:**
- Consumes: `/brand/*`, `/marks/*`, `/figures/hero-paths-*.png`
- Produces: `SectionMark({ name, className? })` with decorative image semantics

- [ ] **Step 1: Add a failing production rendering acceptance test**

Build the frontend and inspect rendered route HTML. Assert metadata references the icon and manifest, navigation exposes generated lockup images, each route contains its mark path with hidden semantics, and the homepage caption contains the five hero parameters.

- [ ] **Step 2: Run the acceptance test and verify missing asset wiring fails**

Run: `python -m pytest tests/test_site_brand.py -v`

Expected: failures identify missing metadata, lockup, marks, and caption.

- [ ] **Step 3: Implement shared mark and global brand wiring**

Add `SectionMark` with an allowlisted route-name union and `<img aria-hidden="true" alt="">`. Update layout metadata with icon, Apple icon, and manifest. Replace the navigation text brand with light and dark lockups. Add marks to all homepage cards and each route's first kicker. Add light and dark hero pictures behind the homepage masthead and the exact parameter caption.

- [ ] **Step 4: Run focused tests, lint, and build green**

Run: `python -m pytest tests/test_site_brand.py -v`, `npm run lint`, and `npm run build` from `frontend`.

- [ ] **Step 5: Commit integration**

Commit message: `feat: wire brand assets across the site`

### Task 4: Replace palette and chart semantics

**Files:**
- Modify: `frontend/app/globals.css`
- Modify: `frontend/components/Heatmap.tsx`
- Modify: `frontend/components/FigureBars.tsx`
- Modify: `frontend/components/PayoffDiagram.tsx`
- Modify: `frontend/app/model/page.tsx`
- Modify: `frontend/app/mispricing/MispricingClient.tsx`
- Modify: `frontend/tailwind.config.ts`
- Create: `tests/test_site_palette.py`

**Interfaces:**
- Consumes: the exact palette and chart-role requirements from the spec
- Produces: theme custom properties and accessible lightness, texture, and dash encodings

- [ ] **Step 1: Add failing palette and contrast tests**

Scan the scoped files for every forbidden hex. Parse theme token literals and calculate WCAG contrast for body text on ground, tint, and tint-warm, and band text on burgundy. Assert heatmap endpoints are white and deep red and that category-three styling includes a 45 degree hatch.

- [ ] **Step 2: Run tests and verify old palette failures**

Run: `python -m pytest tests/test_site_palette.py -v`

Expected: failures list the current petrol and green tokens and old heatmap endpoint.

- [ ] **Step 3: Apply exact theme tokens and semantic chart roles**

Replace light and dark variables with the specified values. Add chocolate, burgundy, figure-primary, figure-recessive, figure-third, and figure-signal roles. Change the heatmap to a white-to-deep-red ramp. Use lightness and dash patterns for two-series charts and a hatch anywhere a third warm category appears. Remove obsolete Tailwind emerald and teal extensions.

- [ ] **Step 4: Run palette tests, lint, and build green**

Run: `python -m pytest tests/test_site_palette.py -v`, `npm run lint`, and `npm run build`.

- [ ] **Step 5: Commit the repalette**

Commit message: `style: repalette site and chart semantics`

### Task 5: Place sample-field figures and preserve figure contracts

**Files:**
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/app/measurement/page.tsx`
- Modify: `frontend/app/globals.css`
- Modify: `tests/test_site_brand.py`

**Interfaces:**
- Consumes: `/figures/sample-field.svg`
- Produces: homepage second figure and measurement hero figure with existing figure title, source, and cell-count conventions

- [ ] **Step 1: Add failing route assertions**

Assert both rendered routes reference the sample field. Assert surrounding figure captions retain a figure number, title, and source line and include the audit cell count.

- [ ] **Step 2: Run focused tests and verify the missing figure references fail**

Run: `python -m pytest tests/test_site_brand.py -v`

- [ ] **Step 3: Replace the relevant existing figure bodies**

Use the generated sample field at the requested two positions without changing the page's claims. Keep visible figure numbering, titles, source attribution, and counts. Add responsive figure container styles.

- [ ] **Step 4: Run focused tests, lint, and build green**

Run: `python -m pytest tests/test_site_brand.py -v`, `npm run lint`, and `npm run build`.

- [ ] **Step 5: Commit figure placement**

Commit message: `feat: publish the generated sample field`

### Task 6: Full acceptance and browser verification

**Files:**
- Modify only files required by failures discovered in this task

**Interfaces:**
- Consumes: all prior tasks
- Produces: a clean feature branch meeting the complete acceptance list

- [ ] **Step 1: Run the complete automated suite**

Run the asset drift command, `python -m pytest -q`, `npm run lint`, and `npm run build`. Regenerate committed assets once more and confirm `git diff --exit-code` for generated directories.

- [ ] **Step 2: Audit static acceptance conditions**

Search `frontend/`, `src/`, and `docs/` for forbidden hex values and em dashes. Confirm the three superseded generator filenames are absent. Confirm every expected asset exists.

- [ ] **Step 3: Inspect the running site in a browser**

Run the production server and check desktop and mobile widths. Verify the 16 pixel favicon on light and dark tab bars, light and dark navigation lockups, hero cropping and caption, all route marks, both sample-field placements, and chart legibility without hue.

- [ ] **Step 4: Re-run all affected gates after visual fixes**

Repeat drift, pytest, lint, and build. Confirm the working tree contains only this feature's intended files.

- [ ] **Step 5: Commit final verification fixes if any**

Commit message: `test: enforce brand asset acceptance`
