# Chocolate, Burgundy, and Red Site Design

## Goal

Replace the existing petrol and green identity with a chocolate, burgundy, and red system, generate every visual asset from one deterministic script, and wire those assets into the Next.js site.

## Asset pipeline

`scripts/assets.py` is the single generator for the break logo, lockups, favicon files, route marks, sample field, and light and dark hero paths. It consumes `data/processed/resolution_audit.csv` and writes directly to `frontend/public`. The loader supports this repository's `event_year`, `resolved`, and `exclusion_family` columns. Generated files contain stable provenance without a wall-clock timestamp so running the command on another date produces the same bytes.

The generator keeps the two rejected logo functions for later comparison, but only the break logo is committed. Every generated SVG has a title and description. Figure SVGs expose their figure text to assistive technology; decorative route marks remain hidden at the use site.

`make assets` regenerates the committed files. `make assets-check` regenerates into a temporary directory and compares all expected outputs without changing the working tree. CI installs pinned image dependencies and Chromium, then runs the drift check.

## Site integration

The root metadata points to `/brand/icon.svg` and `/brand/apple-touch-icon.png`, and a web manifest points to the 512 pixel icon. The navigation uses generated light and dark lockups selected with CSS. The homepage masthead uses the generated light and dark hero paths as ambient full-bleed picture sources with overlaid copy. Its visible caption states sigma 34 percent, mu 5 percent, horizon 3 years, barrier 56, and seed 1974.

Each homepage module card displays its matching 28 pixel section mark. Each interior route displays the same decorative mark beside its first eyebrow while preserving a visible text label. `/measurement` uses the sample field as its hero figure, and the homepage uses it as the second numbered figure.

## Palette and chart semantics

Global light and dark theme tokens use the exact values in the user brief. The burgundy band uses white text, `#E0BDB6` muted text, and `#F0A868` accent text. Legacy token aliases remain only where existing components still consume them.

Charts do not use neighboring warm hues as the sole category distinction. Primary observations use deep red, absence uses a pale warm fill, and a third category uses chocolate with a 45 degree hatch. The era-by-sector heatmap uses a single light-to-deep red ramp. Existing two-series line charts use strong lightness contrast and dash pattern, with legends retaining text labels.

## Quality gates

Automated checks cover audit classification, deterministic output, SVG accessibility, the required asset inventory, forbidden colours, chart texture rules, and manifest metadata. Final verification runs the generator drift check, Python tests, the em dash test, frontend lint, and the production build. A local browser pass checks the 16 pixel favicon, both themes, the navigation lockup, hero crop, route marks, and responsive layouts.

## Repository note

`brand.py`, `hero_paths.py`, and `make_figures.py` do not exist in this checkout or its git history, so their requested deletion is already satisfied.
