# Phase 0: Data Reality Check

**Run date:** 2026-08-19 · **Branch:** `research-rework`

All findings below are empirical. Every source was called live; nothing is
assumed from documentation.

---

## 1. Source-by-source inventory

| Source | Status | Provides | Hard limit found |
|---|---|---|---|
| yfinance (prices, survivors) | Works | Monthly/daily OHLC to 1985 | none material |
| yfinance (prices, delisted defaulters) | **Fails** | n/a | 9/45 tickers returned data; only 4 had >=36m pre-event history |
| Yahoo raw chart API (`/v8/finance/chart`) | **Fails identically** | n/a | Confirms purge is Yahoo-side, not a yfinance bug |
| yfinance (`get_shares_full`) | Partial | Share count time series | **Starts 2015-10-28.** Nothing earlier |
| yfinance (balance sheet) | **Too shallow** | Debt, liabilities | **5 annual / 6-7 quarterly periods (~18 months)** |
| Stooq CSV endpoint | **Blocked** | n/a | JavaScript proof-of-work anti-bot challenge on every request, incl. `aapl` |
| SEC EDGAR (`companyfacts` XBRL) | **Works well** | Point-in-time debt, shares, liabilities, keyed on CIK | XBRL begins ~2009; sparse for small filers |
| SEC EDGAR (full-text search) | Works | 8-K Item 1.03 bankruptcy events: CIK, date, SIC, state | Coverage 2001+; **material false-positive rate** |
| FRED Treasury (DGS1, DGS10) | Works | Full history 1962/1996+ | none |
| FRED ICE BofA OAS | **Severely truncated** | Rating-bucket OAS | **Rolling 3-year window: 2023-08-21 -> present (793 obs)** |

### 1.1 The binding constraint

**Historical equity prices for firms that subsequently delisted are not
available from any free source tested.**

Everything else is obtainable: the event list, point-in-time debt, share
counts, risk-free rates, sector codes. The study stands or falls on prices for
dead firms.

### 1.2 Yahoo does not merely omit dead firms. It returns the wrong company

This is the most dangerous finding, because it fails silently.

- `BBBY` returns 292 continuous months, 2002-05 to 2026-08, labelled
  "Bed Bath & Beyond, Inc.". Bed Bath & Beyond traded near **$0.07** before its
  April 2023 Chapter 11. The series shows **$19-$36 through 2023, rising after
  the filing**. Those are Overstock / Beyond Inc. prices retro-mapped onto the
  recycled ticker. A pipeline keyed on ticker computes a *healthy* firm straight
  through the bankruptcy.
- `SBNY` (Signature Bank, seized 2023-03) returns data starting **2024-08**, which is a
  different company on the recycled ticker.
- `AAL` shows 75 months before American Airlines' 2011 filing. Those months are
  **US Airways Group**, which held the ticker until the 2013 merger.
- `YELLQ` returns a single month in 2026.

**Consequence:** any pipeline keyed on ticker symbol is unsound. The study must
key on **SEC CIK** and treat ticker as a time-varying attribute.

### 1.3 EDGAR event list needs adjudication

8-K Item 1.03 hits, 2011-2024: **5,693 documents**, **579 unique CIKs** in the
sampled subset. But of 30 sampled CIKs with tickers, confirmed false positives
include **RenaissanceRe, LendingTree, FirstEnergy, NRG**, all alive. These are
parents filing an 8-K about a *subsidiary's* bankruptcy, or unrelated Item 1.03
references. Roughly a third of hits need adjudication.

Separately: only **45 of 579** bankrupt CIKs appear in EDGAR's
`company_tickers.json`, because that file lists only *currently registered*
filers. **Survivorship bias is baked into the ticker map itself.**

---

## 2. Defects found in the existing pipeline

These are live and affect every number the site currently renders.

| # | Location | Defect |
|---|---|---|
| 1 | `equity_fetcher.py:get_total_debt`, `historical_data.py:_get_total_debt` | **Debt double-counted.** Sums `Total Debt` *and* its own components. Ford: reports **$435.67B** vs. correct **$163.30B**, a **2.67x overstatement**. Inflates leverage, depresses DD, inflates spreads, for every firm. |
| 2 | `signals/generator.py:96` | Bank / shadow-bank debt is **fabricated**: `D = max(E * 9.0, 1.0)`. Not measured. |
| 3 | `signals/generator.py:154-158` | Bank / shadow-bank market spread is **hardcoded** to 80/120/200 bps by market-cap bucket. Not FRED, not observed. For banks, both sides of the "alpha gap" are constants. |
| 4 | `backtesting/metrics.py:73` | `'prediction_accuracy': '100%' if had_warning else '0%'`. The headline claim is a tautology in code. Line 74: `'false_positives': 0,  # Would need non-event data to calculate`. |
| 5 | `backtesting/historical_data.py:_get_shares_outstanding` | Uses **current** shares for all historical dates. Post-reorganisation share counts applied to pre-bankruptcy prices. |
| 6 | `data/market_fetcher.py:get_spread_timeseries` | Silently returns empty for any date before 2023-08-21 (see FRED limit). All historical backtests using it are void. |
| 7 | `signals/generator.py:150-152` | **Circularity confirmed** exactly as briefed: `_estimate_rating_from_merton_leverage(V, D)` -> `get_spread_by_rating(rating)` -> `spread_diff = theo_spread - market_spread`. |
| 8 | root `.gitignore` | Was **UTF-16LE**, which git cannot parse, so every rule was silently inert. Root cause of the committed `.env` and 21 committed `.pyc` files. *(Fixed in commit `f778738`.)* |

`SHADOW_BANKS = {"F", "GM", "BA"}`. Boeing is in this set, and Boeing is a
published case study. Its debt and its benchmark are therefore both synthetic.

---

## 3. Recomputability of the seven published case studies

| Case | EDGAR fundamentals | Prices | Recomputable? |
|---|---|---|---|
| Lehman Brothers (2008) | **None**. CIK 806085 returns 404, pre-XBRL | Purged | **No** |
| SVB Financial (2023) | Yes, through 2022-12-31 | **Purged** (`SIVB`, `SIVBQ` both 404) | **No** |
| Credit Suisse (2023) | Yes, through 2023-12-31 | **Purged** (`CS` 404) | **No** |
| Hertz (2020) | From 2015-12-31 | Post-2021 fresh-start equity only | Partial |
| NYCB (2024) | Full | Full | **Yes** |
| Boeing | Full | Full | **Yes** |
| Bed Bath & Beyond (2023) | Yes, through 2023-02-25 | **Wrong company** (see 1.2) | **No** |

**The three cases the site leads with are the three that cannot be recomputed
from free sources.** Under Rule 1 (never fabricate a number) and Rule 2 (label
unsourced exhibits in visible UI), Lehman, SVB and Credit Suisse must either be
dropped or retained with their timelines visibly labelled
`ILLUSTRATIVE, not sourced`.

---

## 4. What is *not* constrained

The control cohort is abundant: 26/30 sampled survivors returned >=60 months of
prices plus a usable `Total Debt` line. Controls are not the binding
constraint. **Treatment is.** This inverts the assumption in the brief
(section 3: "control cohort ... is the binding constraint on the whole study").

---

## 5. Feasible study designs

### Design A: no new credentials

- Treatment: bankruptcies whose genuine pre-event prices survive on Yahoo,
  adjudicated individually. Realistic **N = 15-30**.
- **Second selection problem:** the firms whose prices survive are largely those
  whose *equity survived reorganisation* (PG&E, Tidewater) or parents whose
  subsidiary filed. That is selection on a post-treatment outcome, layered on
  top of the original one. AUC confidence intervals would be very wide.
- Deliverable: an honest study that reports wide intervals and names this bias.

### Design B: one free API key with delisted coverage (recommended)

- Polygon.io, Tiingo, or Financial Modeling Prep retain delisted tickers with
  full history on their free tiers. Requires a signup the user must perform.
- Yields a genuinely survivorship-bias-free treatment cohort, plausibly
  **N = 80-200** for 2012-2024.
- This is the only option that carries the full section 4 design (ROC/AUC with
  bootstrapped CIs, calibration deciles, sector heterogeneity).

### Design C: abandon the spread benchmark as the spine (recommended, orthogonal to A/B)

FRED's 3-year OAS window makes a contemporaneous spread benchmark impossible for
any historical event study. Rather than disclose a circular benchmark, **remove
it from the research question** and study discrimination directly:

> Does equity-implied distance to default separate firms that subsequently
> default from comparable firms that do not, and what false-positive rate does
> that separation cost at realistic base rates?

This eliminates Problem 2 by construction instead of apologising for it. The
spread comparison survives as a **present-day-only, clearly labelled
illustrative module** on `/screen`, with the circularity disclosed in visible UI
as required.

**Recommendation: C as the spine, B for the sample, A as guaranteed fallback.**

---

## 6. Conflicts with the brief

1. **Section 4 assumes historical credit spreads are available.** They are not,
   before 2023-08-21. Any exhibit comparing model spread to market spread in
   event time is impossible. -> Design C.
2. **Section 3 predicts the control cohort is the binding constraint.** It is
   not; treatment is.
3. **Section 6 says "keep and upgrade `backend/backtesting/`".** It is built on
   yfinance historical debt (~18 months) and current-share-count substitution.
   It needs rewriting against EDGAR, not upgrading.
4. **Section 5 requires committed CSVs under `data/processed/`.** The old
   `.gitignore` contained a blanket `*.csv` rule that would have silently
   excluded them. Fixed, with a comment guarding against reintroduction.
5. **Sample window.** XBRL from ~2009 and `get_shares_full` from 2015-10 mean
   the widest defensible window is **2010-2024** using EDGAR share counts (not
   yfinance ones). 2008-era events (Lehman, WaMu) are permanently out of reach.

---

## 7. Credential status

- `backend/.env` contained a live FRED key, committed in `6ca8476` (2026-02-09),
  public at `github.com/Iska555/merton-distressed-signals`.
- Untracked in `f778738`; `.gitignore` rewritten as UTF-8; `.env.example` added.
- **The key is still in git history and on GitHub. Untracking does not revoke
  it. It must be rotated at fred.stlouisfed.org.**
