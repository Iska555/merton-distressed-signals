# Distressed Credit Signals

**Equity-implied credit risk from a structural model, and what it costs to act on it.**

---

## Research question

> Does distance to default, computed from the Merton (1974) structural model on
> equity data alone, separate firms that subsequently default from comparable
> firms that do not — and what false-positive rate does that separation cost at
> realistic base rates?

The second clause is the contribution. Anyone can show distance to default falls
before a bankruptcy; the sample of failed firms guarantees it. The question worth
asking is what the model does on firms that survive.

---

## Status

Sample construction is in progress. Pages that need it say so rather than
showing a placeholder.

| Component | State |
|---|---|
| Merton model + interactive solver | Complete, client-side |
| Mispricing screen (shadow rating, cohort benchmark) | Complete |
| Measurement study (resolution audit) | Complete |
| Base-rate precision exhibit | Complete |
| Event-time DD paths | Awaiting sample |
| ROC / AUC / estimator horse race | Awaiting sample |

---

## What this is not

**Not an arbitrage signal.** Issuer-level bond pricing requires TRACE, which is
not freely available. The mispricing module compares an equity-implied spread
against a *rating-cohort index average* — hundreds of unrelated issuers, not this
firm's bond. It reports direction and disagreement, never basis points anyone
could capture.

**Not a study of the financial crisis.** The usable window is 2012–2024. Before
roughly 2011 filings carry no XBRL; before 2019 they carry no trading symbol on
the cover page at all. The 2008–09 default cluster is not merely absent — it is
unreachable with free data.

**Not an accuracy claim.** A sample selected on the outcome cannot measure
accuracy: a model flagging every firm on earth scores 100% on it. Discrimination
is reported as AUC against a matched control cohort, with the false-positive rate
stated.

> An earlier version of this project advertised perfect signal accuracy across
> seven major corporate collapses. That figure was a tautology: the code computed
> it as *"perfect if a warning fired, zero otherwise"*, on a sample of seven firms
> selected precisely because they defaulted, with `false_positives` hardcoded to
> `0` beside a comment conceding it "would need non-event data to calculate." The
> claim has been removed along with the reasoning that produced it.

---

## The three findings so far

### 1. The measurement problem

Constructing a survivorship-free sample of defaulted US firms from free public
data is far harder than the literature admits, and the difficulty is *structured*.

Two SEC filing-rule changes govern whether a delisted firm can be identified at
all:

| Threshold | Effect |
|---|---|
| ~2011 | XBRL instance documents begin to exist |
| 2019 | FAST Act Modernization adds the cover-page trading symbol and its tag |

Verified directly: Kodak's 2011 10-K cover page carries only *"Title of each
Class"* and *"Name of each exchange on which registered"*. There is **no trading
symbol on the page**. Cover-page extraction — the obvious fallback for older
filings — is not unreliable before 2019; the datum does not exist. What survives
is Item 5 prose: *"traded on the New York Stock Exchange under the symbol EK."*

Resolution rises steeply and monotonically across the window — **12.8%** in
2010–11 to **68.7%** in 2022–24, on 346 sampled filings. It also varies by
sector: financials resolve at 26.8% against 56.2% for manufacturing, so the
cohort under-samples exactly the sector where Merton is least applicable.

It does **not** vary with size in the way an earlier draft of this README
claimed. That figure was measured on 190 candidates and did not survive at 346;
the corrected bands show no monotone trend. What remains is a filer-type effect:
registrants reporting no public float at all — shells, trusts and partnerships —
resolve at 18.3%. Full cross-tabs, with cell counts, on `/measurement`.

### 2. Two data traps that would have poisoned the study silently

**The spliced ticker.** Bed Bath & Beyond traded near **$0.07** before its April
2023 filing. A major free price source returns a continuous "BBBY" series showing
**$19–36 and rising** straight through the bankruptcy — Overstock/Beyond Inc.
prices retro-mapped onto the recycled ticker. A pipeline trusting it would compute
a healthy firm through a bankruptcy and record it as a model failure.

**The concurrent symbol.** A registrant cannot trade under two symbols at once, so
two candidate symbols whose trading windows *overlap* cannot both be its. A genuine
re-ticker shows a handoff: Walter Investment's WAC ends 2018-02-09 as Ditech's DHCP
begins 2018-02-06. Overlapping candidates are flagged and never auto-ranked.

### 3. The base-rate result

A model with respectable discriminatory power can still be near-useless as a
standalone alarm. Catching 80% of defaults while flagging 20% of survivors, against
a 1.5% annual default rate, yields **precision of about 5.7%** — roughly sixteen
false alarms per real default.

That is not an argument that structural models are worthless. It is an argument
that they rank rather than alarm. Live exhibit on `/discrimination`.

---

## The circularity, and how it was fixed

The predecessor generated its signal as `theoretical_spread − market_spread`, where
the market spread came from `get_spread_by_rating(rating)` and the rating came from
`_estimate_rating_from_merton_leverage(V, D)` — a function of the model's own solved
asset value. Both sides descended from the same output, so the gap was partly the
model arguing with itself.

Worse, for any firm classified as a bank or "shadow bank" — a set that included
Boeing — *both* sides were hardcoded: debt as `max(E * 9.0, 1.0)` and the benchmark
as 80/120/200 bps by market-cap bucket.

**The fix.** `src/models/shadow_rating.py` assigns the benchmark rating from filing
fundamentals only: interest coverage as the primary axis, size band from total
assets, at most one notch on debt/EBITDA or operating margin with the reason
recorded. `tests/test_shadow_rating.py` asserts that the function signature admits
no Merton-derived argument, that the module does not import the solver, and that its
output is unchanged while asset value and volatility vary. The circularity cannot
return by convention drift.

**What remains limited.** A cohort index is not an issuer's bond, and structural
models understate observed investment-grade spreads at short horizons because a real
spread also pays for liquidity and tax — the documented credit spread puzzle (Eom,
Helwege and Huang 2004; Huang and Huang 2012). The divergence is therefore read as
direction, not level, and the page says so.

---

## Data sources

| Source | Used for | Access |
|---|---|---|
| SEC EDGAR full-text search | Bankruptcy events (8-K Item 1.03) | Public, no key, 2001+ |
| SEC XBRL company facts | Debt, shares, float, trading symbol | Public, no key |
| SEC DERA Financial Statement Data Sets | Point-in-time filer universe, bulk fundamentals | Public, no key |
| FRED ICE BofA OAS indices | Cohort benchmark spreads | API key, build time only |
| Price vendor listing file | Symbol trading windows, delisting dates | Public file, no key |

Controls are drawn from a **point-in-time** filer universe rather than from firms
listed today. Sampling current filers would have required a 2013 control to survive
thirteen years, making the control group systematically healthier than the
population and biasing the false-positive rate low — the mirror image of the
treatment-side bias, and invisible in the output.

---

## Method

`docs/matching-spec.md` was committed **before** any matching code was written and
before any treatment-firm price series was retrieved. It fixes in advance: matching
variables and bucket boundaries, caliper, ratio, covariate measurement date,
replacement policy, tie-break order, subsidiary adjudication, provenance tiers and
the primary analysis.

Four amendments have been made since, each in its own commit with a stated reason
and disclosed on `/data`. The consequential one reversed control eligibility so that
firms defaulting *after* a treatment firm's event are retained and censored rather
than excluded — excluding them uses future information to make a present selection.

Thresholds are never chosen by maximising a metric on the study sample. Sliders on
the site are reader-driven inputs, not fitted values.

---

## Reproduction

```bash
pip install -r backend/requirements.txt

python -m scripts.audit_resolution --start 2010 --end 2024 --per-year 25
python -m scripts.verify_filing_text --n 80
python -m scripts.build_site_data
python -m scripts.smell_test          # read the numbers; do not just check exit code

cd frontend && npm install && npm run build
```

Model scripts write deterministic CSVs to `data/processed/`. Random seeds are fixed;
the matching procedure consults no RNG at all, because its tie-break is a total
order ending in ascending CIK.

`scripts/smell_test.py` prints pipeline inputs beside figures from public filings.
It exists because the 2.67× debt double-count that shipped in the predecessor was
caught by a human reading Ford's `$435.67B` and finding it absurd, not by a test.
Tests verify the code does what the code intends; they do not verify the numbers.

### Environment

```bash
cp .env.example backend/.env   # then fill in
```

| Variable | Required | Purpose |
|---|---|---|
| `FRED_API_KEY` | For cohort spreads | Read at build time only; never reaches a browser |
| `TIINGO_API_KEY` | For delisted prices | Metered: 500 unique symbols per calendar month |

> **Security note.** A FRED API key was committed to this repository's history in
> commit `6ca8476`. It must be revoked and reissued at
> <https://fredstlouisfed.org/docs/api/api_key.html>. Removing the file from the
> working tree does not remove it from history.

---

## Architecture

```
src/
  data/       fetchers, identity resolution, budget ledger, sample construction
  models/     merton, shadow_rating, discrimination, event_study
scripts/      audit, verification, smell test, site data build
data/
  raw/        cached API pulls (gitignored)
  processed/  committed CSV outputs — the site's data source
frontend/     Next.js; research pages read committed JSON at build time
backend/      FastAPI, now optional
```

Every route renders with the backend stopped. Research pages read static JSON
produced by `scripts/build_site_data.py`, which writes a `MANIFEST.json` carrying
the git commit and per-file provenance. A figure that cannot be traced back through
that manifest to a committed CSV, or to a computation from inputs shown on screen,
is a bug.

---

## Limitations

- **Period selection.** 2012–2024 only, a span of historically low default rates
  with no systemic credit event. Discriminatory power measured on it does not
  generalise to a crisis.
- **Non-random selection into the cohort**, by era, size and sector.
- **Cohort benchmark, not issuer pricing.** Direction, not level.
- **Quota-constrained design.** The control ratio was set by an API symbol cap, not
  by statistical power, and size is matched on book assets rather than market cap
  for the same reason.
- **Merton does not describe banks.** Deposit funding is callable on demand; SVB and
  Credit Suisse were liquidity runs, not asset-value insolvencies. Financials are
  reported separately and excluded from the pre-registered primary metric.
- **Partnerships and trusts are not Merton objects** and are excluded on modelling
  grounds, not data grounds.

---

## References

Merton, R. C. (1974). On the pricing of corporate debt: the risk structure of
interest rates. *Journal of Finance* 29(2).

Bharath, S. T. and Shumway, T. (2008). Forecasting default with the Merton distance
to default model. *Review of Financial Studies* 21(3).

Campbell, J. Y., Hilscher, J. and Szilagyi, J. (2008). In search of distress risk.
*Journal of Finance* 63(6).

Eom, Y. H., Helwege, J. and Huang, J.-Z. (2004). Structural models of corporate bond
pricing: an empirical analysis. *Review of Financial Studies* 17(2).

Huang, J.-Z. and Huang, M. (2012). How much of the corporate-treasury yield spread
is due to credit risk? *Review of Asset Pricing Studies* 2(2).
