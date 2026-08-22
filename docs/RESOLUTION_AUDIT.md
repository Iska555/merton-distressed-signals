# Resolution Audit — who gets into the treatment cohort, and who doesn't

**Run:** 2026-08-22 · **Sample:** 346 bankruptcy candidates, 25 per year, 2010–2024
**Source:** 8-K Item 1.03 filings via EDGAR full-text search
**Output:** `data/processed/resolution_audit.csv`

Exclusion that correlates with size, sector or era makes the treatment cohort a
biased sample of defaults, and every downstream number inherits that bias. It is
published whichever way it comes out.

> **Supersedes the 2026-08-20 run at N = 190.** Two findings changed materially
> and are called out in §6, because both reached the README and the site before
> being corrected.

---

## 1. Headline

**149 of 346 candidates resolved to a usable ticker (43.1%).**

| Tier | N | How |
|---|---|---|
| `xbrl` | 109 | `dei:TradingSymbol` from the filing's XBRL instance |
| `filing_text` | 40 | Trading symbol from Item 5 prose of the 10-K |

---

## 2. The era gradient — the strongest and only monotone effect

| Era | N | Resolved |
|---|---|---|
| 2010–2011 | 47 | **12.8%** |
| 2012–2014 | 71 | 19.7% |
| 2015–2018 | 96 | 47.9% |
| 2019–2021 | 65 | 56.9% |
| 2022–2024 | 67 | **68.7%** |

Two structural thresholds produce this:

1. **~2011 — XBRL instance documents begin to exist.** Six pre-2010 bankruptcies
   (Lyondell, Nortel, Sharper Image, TOUSA, Buffets, Lehman) returned *zero*
   instance documents across all their filings.

2. **2019–2021 — `dei:TradingSymbol` becomes tagged.** The SEC's FAST Act
   Modernization rule introduced cover-page Inline XBRL.

**Verified directly:** Kodak's 2011 10-K cover page carries only *"Title of each
Class"* and *"Name of each exchange on which registered"*. There is **no trading
symbol on the page at all** — that column was created by the 2019 rule.
Cover-page extraction is therefore not merely unreliable before 2019: the datum
does not exist. Item 5 prose is the only surviving route, and it carries the
`filing_text` tier.

### Practical floor

**The usable window is 2012–2024.** The 2008–09 default cluster cannot be studied
with free data. Period selection is a named limitation alongside survivorship
bias.

---

## 3. Sector

| SIC division | N | Resolved |
|---|---|---|
| Manufacturing | 105 | 56.2% |
| Wholesale Trade | 9 | 55.6% |
| Transport & Utilities | 29 | 44.8% |
| Retail Trade | 31 | 38.7% |
| Services | 53 | 37.7% |
| Mining | 73 | 30.1% |
| Finance, Insurance, Real Estate | 41 | **26.8%** |

Financials resolve worst among the large groups and are 41 of 346 candidates.
The cohort under-samples exactly the sector where Merton is least applicable,
which flatters the headline result and weakens the sector panel. Both directions
are stated.

---

## 4. Size — no measurable gradient

| Public float at last 10-K | N | Resolved |
|---|---|---|
| under $50M | 132 | 45.5% |
| $50–200M | 56 | 60.7% |
| $200M and above | 65 | 58.5% |
| **none reported** | 93 | **18.3%** |

Among firms reporting a float there is **no monotone trend**. The only real gap
is for registrants reporting no public float at all, which is a *filer-type*
effect — shells, liquidating trusts and partnerships — rather than a size effect,
and those are excluded on modelling grounds regardless.

---

## 5. Where the losses are

| Reason code | N | Share | Family |
|---|---|---|---|
| `SYMBOL_NOT_LISTED` | 70 | 20.2% | unavailability |
| `LISTING_EXCLUDES_EVENT` | 56 | 16.2% | unavailability |
| `NO_TRADING_SYMBOL_TAG` | 24 | 6.9% | unavailability |
| `AMBIGUOUS_OVERLAPPING` | 21 | 6.1% | unavailability |
| `NO_XBRL_INSTANCE` | 15 | 4.3% | unavailability |
| `NO_COMMON_EQUITY` | 11 | 3.2% | **inapplicability** |

**186 excluded by source limits** (a limitation) against **11 excluded as
non-Merton objects** (a scope definition).

`LISTING_EXCLUDES_EVENT` is largely a *correct* rejection: it catches symbol
changes across bankruptcy, such as Kodak's pre-bankruptcy **EK** against the
post-emergence **KODK** listing that begins 2013-09-23.

`AMBIGUOUS_OVERLAPPING` — the mutual-exclusivity guard — independently caught
**American Airlines (CIK 0000004515)**, the AAL/AMR ticker splice found by hand
in Phase 0. A registrant cannot trade under two symbols at once, so candidates
whose windows overlap are flagged rather than auto-ranked.

**Chapter 22: 29 of 346 (8.4%)** filed Item 1.03 more than once. The first filing
is the event (spec 1.2.2); subsequent dates are recorded.

---

## 6. Two corrections to the N = 190 run

Both reached the README and the site before being caught. Recorded rather than
quietly overwritten.

### 6.1 The size gradient was small-sample noise

At N = 190 this was reported as *"float ≥ $200M resolves at 79%, < $200M at 51%"*
and written up as "the cohort skews large". At N = 346 the bands are 45.5% /
60.7% / 58.5% — no monotone trend, and not even the same ordering. Roughly 10–25
observations per cell was never enough to support the claim.

**Cross-tabs are now published only with their cell counts beside them.**

### 6.2 `NO_COMMON_EQUITY` was misclassifying pre-XBRL filers

The structural gate excluding registrants with no common shares outstanding ran
*before* checking whether the filer had any XBRL at all. A pre-2011 filer with no
XBRL looks identical to a partnership with no common equity — so 72% of 2010–11
candidates were labelled non-Merton objects, including **Corus Bankshares** and
**AMCORE Financial**, both banks with ordinary common stock.

This corrupted precisely the distinction the two exclusion families exist to
draw: *"the firm does not belong in the study"* versus *"the data does not
exist"*.

Fixed by making the check tri-state — `present` / `absent` / `no_xbrl` — and only
short-circuiting on `absent`. Re-adjudicating the 59 affected rows (provably
equivalent to a full re-run, since the gate fired only on them) changed **48 of
59**:

| Was | Became | N |
|---|---|---|
| `NO_COMMON_EQUITY` | `SYMBOL_NOT_LISTED` | 23 |
| `NO_COMMON_EQUITY` | `NO_XBRL_INSTANCE` | 15 |
| `NO_COMMON_EQUITY` | `LISTING_EXCLUDES_EVENT` | 5 |
| `NO_COMMON_EQUITY` | `RESOLVED_FILING_TEXT` | 5 |

The model-inapplicability count fell from 59 to 11, and five firms wrongly
excluded entered the sample.

---

## 7. Cost

The full pass took **90 minutes for 346 CIKs**, down from 11.1 hours for 190
before the text tier moved to EDGAR full-text search. FTS returns the exact
`accession:filename` containing the phrase, replacing a blind multi-megabyte
download per filing with one API call plus one targeted fetch.
