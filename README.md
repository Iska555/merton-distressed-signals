# Distressed Credit Signals

**149 of 346 sampled US bankruptcy candidates from 2010 to 2024, or 43.1%, can be resolved to a traded symbol from free public data.** The result is a measurement finding before it is a modelling result: resolution rises from 6 of 47 (12.8%) in 2010 to 2011 to 46 of 67 (68.7%) in 2022 to 2024 as structured filings and cover-page symbol disclosure improve.

## Why it matters

Credit research datasets can look complete while silently selecting issuers that are easier to identify, price and model. That selection changes with disclosure rules, era and issuer type. This project makes the failure boundary visible, preserves the exclusions, and treats a structural credit screen as a decision aid rather than a claim of tradable precision.

## Current release

- **Model:** a client-side Merton solver with inputs and assumptions shown.
- **Mispricing:** an equity-implied screen against the **January 2026 Damodaran periodic synthetic-rating default-spread benchmark**. It is a periodic analytical input, not live market, index, or issuer-bond data.
- **Measurement:** a reproducible audit of all 346 candidates, including resolution status, disclosure-era effects, sector limits and cell counts.
- **Discrimination:** an interactive base-rate precision exhibit that demonstrates why a ranker is not automatically an alarm.
- **Cases and data:** completed boundary case studies, provenance, source policy and downloadable derived artifacts.

The site publishes six completed research modules: Model, Mispricing, Measurement, Discrimination, Cases and Data. Every published rate carries its cell count. No route requires a running API server.

## Next research milestone

The next release will add a pre-specified, point-in-time matched control cohort and report out-of-sample discrimination with confidence intervals, precision at a realistic base rate and false-positive cost. Those results are intentionally not claimed before the cohort exists.

## Research boundaries

This is not an issuer-bond pricing system or an arbitrage signal. The periodic benchmark is not a contemporaneous bond quote, and the screen reports direction rather than capture-ready basis points.

The study window is constrained by public disclosure. Pre-2011 filings often lack XBRL, and cover pages did not gain a structured trading-symbol field until 2019. The 2008 to 2009 default cluster is unreachable under this free-public-data design.

The current release does not make an empirical model-accuracy claim. Measuring accuracy requires a matched survivor cohort, not only firms selected because they defaulted.

## Data and source policy

The public site commits derived research artifacts, not raw third-party feeds. SEC EDGAR provides event candidates, filing facts and the point-in-time filer universe. Tiingo supports delisted-price research subject to its plan terms, and starter or trial raw responses are handled only in memory. FRED ICE BofA OAS was reviewed and excluded from public output because its series notes restrict publication of exact observations.

Read the full [data-source and licensing policy](docs/DATA_SOURCES.md) and download the machine-readable [source registry](frontend/public/data/SOURCES.json).

## Install and verify

Use Python 3.11 or later and Node 22 or later.

```bash
python -m pip install -e ".[dev,assets]"
python -m playwright install chromium
cd frontend && npm ci && cd ..
```

Copy `.env.example` to `.env` and add only the credentials needed for a local research run. Credentials are never committed or exposed to the browser.

Run the complete release gate from the repository root:

```bash
python -m scripts.verify
```

This regenerates and compares public assets, reproduces published figures, lints and builds the frontend, then runs the supported Python tests. `make verify` delegates to the same command.

## Architecture

```
src/
  data/       identity resolution, source adapters, quota ledger, sample construction
  models/     Merton, synthetic rating, discrimination and event-study logic
scripts/      audits, public-data generation and release verification
data/
  processed/  committed research outputs
frontend/     Next.js site that reads committed data at build time
docs/         methods, decisions and source policy
```

Generated site data carry a manifest with source and commit provenance. A published figure must trace to a committed input or to a computation whose inputs and assumptions are shown.

## References

- Merton, R. C. (1974). On the pricing of corporate debt: the risk structure of interest rates. *Journal of Finance* 29(2).
- Bharath, S. T. and Shumway, T. (2008). Forecasting default with the Merton distance to default model. *Review of Financial Studies* 21(3).
- Campbell, J. Y., Hilscher, J. and Szilagyi, J. (2008). In search of distress risk. *Journal of Finance* 63(6).
- Eom, Y. H., Helwege, J. and Huang, J.-Z. (2004). Structural models of corporate bond pricing: an empirical analysis. *Review of Financial Studies* 17(2).
- Huang, J.-Z. and Huang, M. (2012). How much of the corporate-treasury yield spread is due to credit risk? *Review of Asset Pricing Studies* 2(2).
