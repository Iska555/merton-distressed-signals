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
| C2 | Has **no** Item 1.03 event on or before the matched treatment firm's `t = 0`. A firm that defaults **later** is retained — see §1.3. |
| C3 | SEC XBRL company facts exist covering `t − 24m` of the treatment firm it is matched to. |
| C4 | Total assets and total liabilities both resolvable at `t − 24m`. |
| C5 | Total assets at `t − 24m` ≥ **$50M**. |
| C6 | A ticker resolves with a listing window spanning `[t − 36m, t]`. |

### 1.3 Controls that default later are kept and censored

> **Amendment, 2026-08-20.** C2 originally excluded any firm appearing in the
> event list anywhere in the study window. That was wrong, and this amendment
> reverses it. Matched sets **do** change, which is why it is recorded here in
> its own commit before the sample is built.

Excluding a control because it defaults *after* the treatment firm's event uses
future information to make a present selection. The surviving control group
would then consist of firms known ex post never to have failed — unusually
durable ones. Their distance-to-default distributions would separate from the
treatment cohort more cleanly than they should, and the **false-positive rate,
the single number this whole rework exists to produce, would come out biased
low**. That is the same survivorship bias the study exists to avoid, re-entering
through the control side.

The rule is therefore:

- A control must be alive and **not yet in default at the treatment firm's
  `t = 0`**.
- A control that defaults **after** `t = 0` is **retained**.
- Every control's observation window is **censored at the treatment firm's
  `t = 0`** regardless of what happens afterwards.
- Its later outcome is recorded in two fields, `control_defaulted_later` and
  `control_event_date`, and reported — never used to filter.

---

## 2. Matching variables and bucket boundaries

Covariates are measured **as of `t − 24 months`**, calendar-dated from the
treatment firm's event date, using point-in-time EDGAR facts (`as_of`), so only
data already **filed and public** at that date is visible.

| Variable | Definition | Buckets |
|---|---|---|
| **Calendar time** | Fiscal quarter containing `t − 24m` | **Exact match required.** See §2.0 |
| **Sector** | SIC division from the EDGAR registrant SIC code | 10 SEC divisions. **Exact match required.** |
| **Size** | `log(total assets)` | Decile, computed on the pooled eligible universe at `t − 24m` |
| **Leverage** | `total liabilities / total assets` | Decile, computed on the same pooled universe |

### 2.0 Calendar time is a hard matching variable

> **Amendment, 2026-08-20.** Calendar time was absent from the original table.
> The implementation already enforced it — controls are drawn from the filer
> universe of the anchor quarter — so the code was stricter than the spec. This
> amendment pre-registers the behaviour rather than leaving it an
> implementation accident. No matched set changes.

Resolution rate rises steeply across the window (37% in 2012–18, 50% in
2019–21, 90% in 2022–24), so the treatment cohort piles up in 2022–24. That is
a specific and unusual credit regime: the fastest tightening cycle in forty
years, the March 2023 regional bank failures, and a concentrated wave of
rate-sensitive bankruptcies. 2012–2021 is a near-zero-rate era with suppressed
default rates.

Without calendar matching, a 2023 defaulter would be compared against a 2016
survivor. Market-wide equity volatility differs enormously between those dates,
distance to default is a direct function of volatility, and the cohorts would
appear to separate for reasons having nothing to do with firm-specific credit
risk. **That would publish a confound as a finding.**

Controls are therefore drawn only from the filer universe of the treatment
firm's anchor quarter, and both cohorts are aligned in event time on the
treatment firm's event date.

### 2.0.1 Era-stratified reporting is mandatory

Every headline metric is reported **stratified by era cohort** — 2012–18,
2019–21, 2022–24 — with N for each, in addition to any pooled figure.

**If the strata disagree, that is the result.** "Distance to default
discriminates well in a tightening cycle and poorly under ZIRP" is a more
useful finding than a pooled AUC describing no actual regime, and it must not
be averaged away. The era gradient appears on `/data` as a chart, not a
sentence.

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

| N treatment | Ratio | Max total symbols |
|---|---|---|
| ≤ 66 | 5 | 396 |
| 67–80 | 4 | 400 |
| 81–100 | 3 | 400 |
| 101–133 | 2 | 399 |
| ≥ 134 | 1 | 400 |

> **Amendment, 2026-08-20** (commit following the original). The table as first
> committed jumped from 5:1 to 3:1 and omitted the 4:1 band for N = 67–80. The
> **formula above is normative and is unchanged**; only this illustrative table
> was wrong. Every band stays within the 400-symbol budget either way, so no
> value that governs the study changed. Recorded here rather than silently
> corrected, per the amendment rule.

**Above N = 200 the budget cannot be met at any ratio.** Even 1:1 needs 400+
symbols. The treatment cohort is still not truncated: the run instead spans two
calendar months, which the symbol ledger already tracks, and the split is
disclosed on `/data`. `universe.fits_monthly_budget()` reports this case.

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
| `filing_text` | Trading symbol read from Item 5 prose of the registrant's 10-K ("traded on the New York Stock Exchange under the symbol EK"), validated against the listing window | **Robustness check only** |

The headline result is computed on the `xbrl` tier alone. The `filing_text`
tier is reported separately. If the two disagree, that is reported as a finding.

Tiers are not pooled to improve N.

> **Amendment, 2026-08-20.** The tier originally specified as `name_match`
> (fuzzy match of registrant name against an external ticker/name table) is
> **not implementable and has been replaced by `filing_text`.**
>
> Two independent reasons. Tiingo's public listing file carries only
> `ticker, exchange, assetType, priceCurrency, startDate, endDate` — **no
> company names at all**, so there is nothing to match a name against.
> OpenFIGI, the obvious substitute, returns "No identifier found" for every
> delisted bankruptcy symbol tested (HTZGQ, BBBYQ, SIVBQ, LEHMQ, WAMUQ, RADCQ,
> WEWKQ, JCPNQ) while resolving live symbols normally.
>
> `filing_text` is a strictly **stronger** second tier than the one it
> replaces: it is document-sourced from the registrant's own filing rather
> than inferred from a name similarity score, so no match threshold has to be
> chosen. It remains tier 2 because it is a regular expression over prose
> rather than a tagged fact.
>
> This is why the tier exists at all: the SEC's 2019 FAST Act Modernization
> rule introduced both the cover-page "Trading Symbol(s)" column and its
> Inline XBRL tag. Before 2019 the ticker appears **nowhere on the cover
> page** — verified directly on Kodak's 2011 10-K — so the `xbrl` tier cannot
> reach 2011-2021 events at all, and Item 5 prose is the only remaining route.

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
