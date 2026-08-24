# Phase 0 Credibility Foundation

**Status:** Approved for implementation on 2026-08-24

## Objective

Make the current research release safe to show to an investment professional or
technical reviewer before the matched-sample study is complete. The public
release must contain only completed work, reproduce through supported commands,
and clearly distinguish empirical findings from planned research.

## Scope

### Supported project

The supported project consists of:

- `src/` for point-in-time data and credit-model code
- `scripts/` for audit, generation and verification commands
- `data/processed/` for committed research outputs
- `frontend/` for the static Next.js research site
- `tests/` for the supported Python and built-site checks

The legacy FastAPI application under `backend/` is not used by the static site,
contains superseded calculations documented in `docs/PHASE0_DATA_INVENTORY.md`,
and is removed. Its history remains recoverable through git.

### Public release boundary

The release presents six complete modules: Model, Mispricing, Measurement,
Discrimination, Cases and Data. Evidence is removed from public navigation and
routing until the matched event-time panel exists. Discrimination presents the
completed base-rate exhibit without an empty measured-results section. Cases
presents the completed exclusion case studies without an empty computed-cases
section.

The README begins with the measured coverage result: 149 of 346 sampled filings,
or 43.1 percent, resolve to a traded symbol. Planned empirical discrimination is
identified as the next study milestone, not as a current result or a visible
placeholder.

### Reproduction and verification

Python dependencies and supported versions live in root project metadata. Local
credentials load from root `.env`, copied from `.env.example`. The repository
provides one cross-platform verification command:

```text
python -m scripts.verify
```

It checks generated asset drift, published figures, frontend lint, frontend
production build and the root test suite. CI uses the same command after installing
Python, browser and frontend dependencies.

### Data provenance

A committed, machine-readable source registry lists each external source, its
official URL, access method, terms or licensing URL, redistribution boundary,
point-in-time limitation and known failure mode. The Data page exposes the registry
as a downloadable artifact. The README links to the human-readable source policy.

## Global constraints

- Preserve the chocolate, burgundy and red visual system already committed.
- Do not change any published research number in Phase 0.
- Do not add predictive performance results before the matched sample exists.
- Do not use em dashes in source or rendered copy.
- Keep generated brand and figure assets byte-identical.
- Keep every current rate accompanied by its cell count.
- Do not require a running API server for any route.
- Do not commit credentials, raw API responses, dependency folders or build output.
- Use test-first implementation for behavior and regression guards.

## Acceptance criteria

- No supported setup or runtime path points to `backend/`.
- No public page or navigation item contains an unfinished module or work-in-progress
  callout.
- Root and frontend documentation describe the actual project rather than framework
  boilerplate.
- `python -m scripts.verify` is the canonical local and CI verification entry point.
- The data-source registry validates and is downloadable from the site.
- Asset drift, published-figure checks, frontend lint, frontend build and root tests
  pass from a clean supported environment.
- Deployment remains a separate explicit action because it pushes external state.
