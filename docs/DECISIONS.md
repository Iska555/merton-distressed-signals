# Research decisions and their evidence

Consequential choices, each with the finding that forced it. Every one of these
must surface on `/data`. Dated so a reader can see what was decided before the
data was seen.

---

## D1 — The "alpha gap" is demoted from a finding to an illustration

**Decided 2026-08-20. Irreversible without a paid data source.**

### The problem

The predecessor generated its trading signal as:

```
signal = theoretical_spread − market_spread
```

where `market_spread` came from `get_spread_by_rating(rating)` and `rating` came
from `_estimate_rating_from_merton_leverage(V, D)` — a function of the model's
own solved asset value. The model was being compared against a benchmark derived
from its own output. Worse, for any firm classified as a bank or "shadow bank"
(`{"F", "GM", "BA"}` — which includes Boeing, a published case study), *both*
sides were hardcoded: debt as `max(E * 9.0, 1.0)` and the benchmark as 80/120/200
bps by market-cap bucket.

### Can it be fixed with an exogenous benchmark?

**No, not with free data.** Every route was tested live:

| Source | Result |
|---|---|
| FRED ICE BofA OAS | Available, but a **rolling 3-year window** (from 2023-08-21). Also an *aggregate index* of hundreds of unrelated issuers, not the firm's own spread |
| FINRA TRACE (issuer-level bond prints) | HTTP 307 redirect to an authenticated flow; requires FINRA API credentials and a licensing review |
| SEC XBRL `DebtInstrumentInterestRateStatedPercentage` | Returns data, but it is a **stated coupon** fixed at issuance, not a market spread. Using it as a benchmark would be a different error, not a fix |
| Exogenous credit ratings (S&P / Moody's / Fitch) | Licensed. Not obtainable |

### Decision

The research question drops the spread-comparison clause entirely and becomes a
question purely about discrimination:

> Does equity-implied distance to default separate firms that subsequently
> default from comparable firms that do not — and what false-positive rate does
> that separation cost at realistic base rates?

This **eliminates the circularity by construction** rather than disclosing it and
carrying on. The spread comparison survives only as a present-day module on
`/screen`, labelled illustrative, with the circularity stated in visible UI.

No exhibit anywhere on the site presents a model-versus-market spread gap in
event time, because no honest one can be built.

---

## D2 — Lehman, SVB and Credit Suisse sit outside the study

**Decided 2026-08-20.**

### Why they cannot be computed

| Case | Fundamentals | Prices | Verdict |
|---|---|---|---|
| Lehman Brothers (2008) | **None.** CIK 806085 returns 404 from `companyfacts`; zero XBRL instances in any filing. Pre-XBRL | Purged | **Impossible** |
| SVB Financial (2023) | Available through 2022-12-31 | `SIVB` and `SIVBQ` both 404 on Yahoo; `SIVBQ` exists in the vendor listing table but needs a key | Blocked on prices |
| Credit Suisse (2023) | **None usable.** 20-F filer; 608 us-gaap concepts but no `Liabilities` and no standard debt concept | Purged | **Impossible** |

Lehman additionally falls outside the study window entirely (§D3).

### Decision

They are **retained**, but in a section that is visually distinct and explicitly
outside the computed study, under a standing `ILLUSTRATIVE — not sourced`
label, with a stated reason per firm.

They must not sit in `/case-studies` alongside computed firms with hand-authored
constants formatted to look identical. That inconsistency is the first thing a
hostile reader finds, and it would contaminate the credibility of the cases that
*are* computed.

The SVB and Credit Suisse entries become the natural home for the panel on why
Merton does not apply cleanly to banks: both were liquidity runs, not
asset-value insolvencies in the Merton sense.

---

## D3 — The study window is 2012–2024, and excludes the financial crisis

**Forced by data, 2026-08-20.**

Resolution rate by era (`docs/RESOLUTION_AUDIT.md`):

| Era | Resolved |
|---|---|
| 2006–2011 | **5%** |
| 2012–2018 | 37% |
| 2019–2021 | 50% |
| 2022–2024 | 90% |

Two structural thresholds cause this: XBRL instance documents begin ~2011, and
`dei:TradingSymbol` becomes tagged only under the SEC's 2019 FAST Act
Modernization rule. Kodak's 2011 10-K cover page carries **no trading symbol at
all** — the column did not exist before that rule.

### Consequence, which must appear in visible UI

The sample covers a period of **historically low default rates with no systemic
credit event**. Discriminatory power measured on 2012–2024 does not generalise
to a crisis, and the site must say so on the exhibit itself rather than in a
footnote.

**Period selection is therefore a named limitation on `/data`, alongside
survivorship bias.** The 2008–09 default cluster — the richest concentration of
corporate failure in modern history, and the one every reader will look for — is
not merely absent; it is unreachable with free data.

---

## D4 — Two provenance tiers, never merged

**Decided 2026-08-20. Amends `docs/matching-spec.md` §6.**

| Tier | Source | Use |
|---|---|---|
| `xbrl` | `dei:TradingSymbol` from the filing's XBRL instance | Headline analysis |
| `filing_text` | Trading symbol from Item 5 prose of the 10-K | Robustness check only |

The originally specified `name_match` tier is **not implementable**: the vendor
listing file carries no company names, and OpenFIGI returns "No identifier
found" for every delisted bankruptcy symbol tested (HTZGQ, BBBYQ, SIVBQ, LEHMQ,
WAMUQ, RADCQ, WEWKQ, JCPNQ) while resolving live symbols normally.

`filing_text` is strictly stronger evidence than a name-similarity score,
because it is document-sourced from the registrant's own filing and needs no
match threshold. It remains tier 2 only because it is a regular expression over
prose rather than a tagged fact.

Headline results run on `xbrl` alone (49 of 71 resolutions). `filing_text` (22)
is reported separately. Disagreement between tiers is a finding, not an
embarrassment.

---

## D5 — Known exclusion biases, published either way

From `docs/RESOLUTION_AUDIT.md`, all reaching visible UI:

- **Size.** Public float ≥ $200M resolves at 79%; < $200M at 51%; none reported
  at 9%. The cohort skews large.
- **Sector.** Financials resolve at 29.7% and retail at 20%, against 60% for
  transport and utilities. The cohort under-samples exactly the sector where
  Merton is least applicable — which flatters the headline result and weakens
  the sector panel. Both directions stated.
- **Era.** See D3.

---

## D6 — The project is a measurement-and-discrimination study, not a detector

**Decided 2026-08-20, following from D1.**

Demoting the circularity (D1) removes the alpha gap entirely. There is no
model-versus-market exhibit anywhere on the site, by that decision. So the
project **no longer detects credit mispricing, and cannot, with free data.**

What remains — "distance to default predicts default" — is legitimate and also
crowded. Bharath & Shumway (2008), Campbell, Hilscher & Szilagyi (2008), and
Duffie, Saita & Wang (2007) all covered it. A site headlining that finding in
2026 reads as a competent replication and nothing more.

The contribution has moved to what the rework itself produced, in order:

1. **The measurement problem.** A quantified, tiered, reason-coded account of
   why studying delisted bankrupt firms from free public data is far harder
   than the literature admits: the two XBRL thresholds, the 2019 FAST Act
   cover-page change, the era gradient, the float gradient, the vendor coverage
   floor, and the ticker-recycling traps. Most papers dispose of sample
   construction in a paragraph and none publish the exclusion cross-tab.
2. **The base-rate and precision result.** At a realistic default rate, a
   respectable AUC still yields poor precision. The sharpest practical finding.
3. **The three-estimator horse race on 2012–2024.** Bharath & Shumway ran
   1980–2003. The naive-versus-iterative comparison has not been replicated
   across ZIRP into the tightening cycle.

Consequences:

- **Rename the project.** "Distressed Credit Detector" describes something the
  code does not do.
- **Rewrite the research question on `/`** around measurement and the cost of
  discrimination, not arbitrage.
- **`/data` is promoted to a primary exhibit**, built with the same care as
  `/discrimination`. Under the old framing it was an appendix; under this one
  it carries the first contribution.

---

## D7 — Two-month run at 3:1, rather than cutting controls

**Decided 2026-08-20.**

The full cohort will not fit one month's 500 unique-symbol allowance. The
choice was between cutting the control ratio to 1:1–2:1 and splitting the fetch
across two calendar months.

**Controls win the trade.** The marginal treatment firm beyond roughly 100 adds
little: the event-time DD path is already tightly estimated there. The marginal
control buys two things the study actually needs — precision on the
false-positive rate, and **match quality**. At 1:1 the nearest available firm is
taken whether or not it is a good match, because there is no alternative. Bad
matches on sector, size and leverage contaminate every downstream comparison,
and no amount of treatment N repairs that.

Sequencing:

| | |
|---|---|
| **Month 1** | Resolve the cohort, fetch treatment prices, construct match candidates |
| **Month 2** | Fetch control prices at 3:1 |

This ordering is natural rather than a workaround: matching cannot be finalised
until the treatment cohort is fixed. Analysis modules and the frontend are
built against the treatment panel and clearly-labelled placeholder controls in
the interval, so nothing is idle.

**If treatment is ever capped, it is capped by random draw with a committed
seed** — never by matchability, which would select for ordinary mid-cap
non-financials and add a fifth selection layer on top of the four already
documented (era, size, sector, vendor coverage).
