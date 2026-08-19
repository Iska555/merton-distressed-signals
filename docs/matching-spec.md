# Control Matching Specification (pre-registered)

**Status:** pre-registered. Committed **before** any matching code was written and
before any treatment-firm price series was retrieved.

**Written:** 2026-08-20 · **Branch:** `research-rework`

---

## Why this document exists

Control matching is the easiest place in this project to cheat without noticing.
Once treatment distance-to-default paths are visible, every judgement about who
counts as a comparable firm gets pulled, unconsciously, toward the set that makes
the separation look cleaner. Widening a caliper, dropping an "obviously
unsuitable" control, switching the size variable — each is individually
defensible and collectively fatal.

The defence is a specification with an earlier commit timestamp than the data it
governs. This document fixes every free parameter in advance. The implementation
must follow it exactly.

**Amendment rule.** If this spec must change, it changes in a *new* commit that
states what changed and why, and the amendment is disclosed on `/data`. Silent
edits to this file are a research-integrity failure, not a tidy-up.

---

## 1. Populations

### 1.1 Treatment

A firm-event enters the treatment cohort if all hold:

| # | Criterion |
|---|---|
| T1 | An 8-K carrying **Item 1.03** (Bankruptcy or Receivership) filed with the SEC. Event date `t = 0` is the **earliest** such filing per CIK. |
| T2 | Adjudicated as the **registrant's own** bankruptcy, not a subsidiary's (see §5). |
| T3 | SEC XBRL company facts exist covering `t − 24m`. |
| T4 | A ticker resolves under the provenance rules in §6, with a listing window spanning `[t − 36m, t]`. |
| T5 | Price history passes `validate_delisted_series` (post-event recovery, ticker reissue, and absence of decline all reject). |
| T6 | Total assets at `t − 24m` ≥ **$50M**. |

### 1.2 Control

A firm enters the eligible control pool if all hold:

| # | Criterion |
|---|---|
| C1 | Files 10-K/10-Q with the SEC (US domestic filer). **20-F and 40-F filers are excluded** — they report under the IFRS taxonomy and expose none of the us-gaap concepts the pipeline reads (verified: Credit Suisse has zero usable debt concepts). |
| C2 | **Never** appears in the Item 1.03 event list at any date within `[study start − 12m, study end + 12m]`. A firm that defaults later is not a control. |
| C3 | SEC XBRL company facts exist covering `t − 24m` of the treatment firm it is matched to. |
| C4 | Total assets and total liabilities both resolvable at `t − 24m`. |
| C5 | Total assets at `t − 24m` ≥ **$50M**. |
| C6 | A ticker resolves with a listing window spanning `[t − 36m, t]`. |

---

## 2. Matching variables and bucket boundaries

Covariates are measured **as of `t − 24 months`**, calendar-dated from the
treatment firm's event date, using point-in-time EDGAR facts (`as_of`), so only
data already **filed and public** at that date is visible.

| Variable | Definition | Buckets |
|---|---|---|
| **Sector** | SIC division from the EDGAR registrant SIC code | 10 SEC divisions. **Exact match required.** |
| **Size** | `log(total assets)` | Decile, computed on the pooled eligible universe at `t − 24m` |
| **Leverage** | `total liabilities / total assets` | Decile, computed on the same pooled universe |

### 2.1 Why size is measured from assets, not market capitalisation

This is a **quota-forced** decision and is disclosed as such on `/data`.

Matching on market cap would require price data for the entire candidate control
universe — thousands of symbols — before any match could be formed. The Tiingo
free tier permits **500 unique symbols per calendar month**. Fetching prices to
decide who to fetch prices for is not affordable.

Total assets from EDGAR is price-independent, available for every filer including
those whose price history has vanished, and is a standard size control. The cost
is that matching is on book size rather than market size; since market size is
partly a function of the distress being measured, book size is arguably the
sounder choice regardless.

### 2.2 Caliper

- Sector: **exact**.
- Size: exact decile, else within **±1 decile**.
- Leverage: exact decile, else within **±1 decile**.

Candidates outside the caliper are never used, even if that leaves a treatment
firm with fewer controls than the target. Shortfalls are recorded per firm and
reported, not filled.

---

## 3. Ratio

**Target: 5 controls per treatment firm.**

The binding constraint is the Tiingo monthly symbol cap, not statistical power.
The whole study must fit inside **400 unique symbols**, leaving 100 in reserve
against the 500 cap.

The ratio is therefore set by:

```
ratio = max(1, min(5, floor(400 / N_treatment) - 1))
```

| N treatment | Ratio | Total symbols |
|---|---|---|
| ≤ 66 | 5 | ≤ 396 |
| 67–99 | 3 | ≤ 396 |
| 100–133 | 2 | ≤ 399 |
| ≥ 134 | 1 | ≤ 400 |

**The treatment cohort is never truncated to preserve the ratio.** Treatment
firms are the scarce resource and dropping them would reintroduce exactly the
selection problem this study exists to avoid. The ratio absorbs the constraint
instead.

The realised ratio and the fact that it was **quota-constrained rather than
power-constrained** must be stated on `/data`.

---

## 4. Replacement and tie-breaking

### 4.1 Without replacement

Each control firm is used **at most once across the entire study**. With
replacement, one firm could populate many matched sets, narrowing the control
band artificially and understating standard errors.

Treatment firms are processed in ascending event-date order, then ascending CIK.
Earlier events therefore get first claim on the control pool. This is arbitrary
but fixed in advance and deterministic.

### 4.2 Tie-break, in strict order

When several candidates sit in the same (sector, size decile, leverage decile)
cell:

1. Smaller `|log(total assets) − log(total assets of treatment firm)|`
2. Smaller `|leverage − leverage of treatment firm|`
3. Smaller `|reporting lag|` difference at `t − 24m`
4. **Lower CIK**, ascending

Rule 4 guarantees a total order, so no random tie-break is ever needed and the
matched sets are byte-reproducible. `RANDOM_SEED` is not consulted by the
matching procedure at all.

---

## 5. Adjudication: whose bankruptcy is it?

EDGAR full-text search on Item 1.03 has a material false-positive rate. Parents
routinely file an 8-K about a **subsidiary's** filing: RenaissanceRe, LendingTree,
FirstEnergy and NRG all appear in the raw hits and are all alive.

A candidate is rejected as a subsidiary/other filing if **any** of:

| # | Rule |
|---|---|
| A1 | The registrant continues filing 10-K or 10-Q for **more than 24 months** after the event. Firms whose own bankruptcy is at issue stop filing, are acquired, or emerge as a new registrant. |
| A2 | Price history fails `validate_delisted_series` under the default (equity-collapse-required) setting. |
| A3 | The registrant's public float at the first 10-K **after** the event exceeds **50%** of its float at `t − 12m`. Equity that survives essentially intact indicates the filing was not the registrant's own. |

Rule A2 is deliberately strict. Prepackaged reorganisations leaving equity intact
are real events, but they are a different phenomenon from the equity-destroying
default this study is about, and admitting them by relaxing A2 case-by-case is
precisely the discretion this spec removes. Firms rejected under A2 are recorded
with that reason code and reported as a known exclusion, not silently dropped.

---

## 6. Provenance tiers

Identity resolution produces two tiers, which are **never merged**:

| Tier | How the ticker was obtained | Use |
|---|---|---|
| `xbrl` | `dei:TradingSymbol` read from the filing's own XBRL instance, validated against the listing window | **Headline analysis** |
| `name_match` | Fuzzy match of registrant name against an external ticker/name table, validated against the listing window, match score above a threshold fixed before use | **Robustness check only** |

The headline result is computed on the `xbrl` tier alone. The `name_match` tier
is reported separately. If the two disagree, that is reported as a finding.

Tiers are not pooled to improve N.

---

## 7. Pre-registered primary analysis

Fixed now, to remove the temptation to select the most flattering cut later.

- **Primary metric:** AUC of distance to default at the **12-month** horizon,
  `xbrl` provenance tier, **non-financial** firms (SIC outside 6000–6799),
  KMV iterative estimator, KMV default barrier.
- **Uncertainty:** 2,000-replicate bootstrap over firms (not firm-months),
  seeded from `RANDOM_SEED`, percentile intervals.
- **Everything else is secondary and labelled as such**: other horizons (3, 6,
  24m), other estimators (simultaneous, naive), other barriers (total debt,
  total liabilities), financial firms, the `name_match` tier, and sector cuts.

**No threshold is chosen by maximising any performance metric on the study
sample.** Thresholds shown in the interactive confusion matrix on
`/discrimination` are user-driven inputs, not fitted values, and the page must
say so.

---

## 8. Recorded regardless of outcome

The following are published whichever way they come out:

- Count of treatment candidates at every filter stage, with reason codes
- Controls found per treatment firm, and every shortfall against the target
- Covariate balance before and after matching (standardised mean differences)
- Resolution rate cross-tabulated by event year, SIC division and size decile
- The realised ratio and its quota constraint
- Any amendment to this specification
