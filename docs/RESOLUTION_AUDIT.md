# Resolution Audit: who gets into the treatment cohort, and who doesn't

> [!CAUTION]
> **Withdrawn 24 August 2026.** The collector behind this audit paginated SEC
> results incorrectly and produced a relevance-truncated sample with no known
> inclusion probability. Every rate below is retained only as correction
> history. It is not current evidence. The replacement design is in
> `docs/superpowers/specs/2026-08-24-measurement-integrity-census-design.md`.

**Run:** 2026-08-22 · **Sample:** 346 bankruptcy candidates, 25 per year, 2010–2024
**Source:** 8-K Item 1.03 filings via EDGAR full-text search
**Output:** `data/processed/resolution_audit.csv`

Exclusion that correlates with size, sector or era makes the treatment cohort a
biased sample of defaults, and every downstream number inherits that bias. It is
published whichever way it comes out.

> **Supersedes the 2026-08-20 run at N = 190.** Two findings changed materially
> and are called out in §7, because both reached the README and the site before
> being corrected, as did the first, wrong, correction of one of them.

---

## 1. Headline

**149 of 346 candidates resolved to a usable ticker (43.1%).**

| Tier | N | How |
|---|---|---|
| `xbrl` | 109 | `dei:TradingSymbol` from the filing's XBRL instance |
| `filing_text` | 40 | Trading symbol from Item 5 prose of the 10-K |

---

## 2. The era gradient, the strongest and only monotone effect

| Era | N | Resolved |
|---|---|---|
| 2010–2011 | 47 | **12.8%** |
| 2012–2014 | 71 | 19.7% |
| 2015–2018 | 96 | 47.9% |
| 2019–2021 | 65 | 56.9% |
| 2022–2024 | 67 | **68.7%** |

Two structural thresholds produce this:

1. **~2011, XBRL instance documents begin to exist.** Six pre-2010 bankruptcies
   (Lyondell, Nortel, Sharper Image, TOUSA, Buffets, Lehman) returned *zero*
   instance documents across all their filings.

2. **2019–2021, `dei:TradingSymbol` becomes tagged.** The SEC's FAST Act
   Modernization rule introduced cover-page Inline XBRL.

**Verified directly:** Kodak's 2011 10-K cover page carries only *"Title of each
Class"* and *"Name of each exchange on which registered"*. There is **no trading
symbol on the page at all**. That column was created by the 2019 rule.
Cover-page extraction is therefore not merely unreliable before 2019: the datum
does not exist. Item 5 prose is the only surviving route, and it carries the
`filing_text` tier.

### Practical floor

**The usable window is 2012–2024.** The 2008–09 default cluster cannot be studied
with free data. Period selection is a named limitation alongside survivorship
bias.

---

## 3. Everything else is reported inside era

Era is the dominant axis of this dataset. Any variable correlated with era will
reproduce the era gradient under its own name, so a pooled cross-tab may be
reporting era a second time. **No cross-tab in this document is published as a
finding until it has been reported within era strata with cell counts.**

Every cell below reads `resolved/candidates` with the rate beneath it. A rate is
shown only when its 95% Wilson interval is 50 points wide or narrower; `±` means
the counts are real but no rate can be read off them. Suppression is on interval
width rather than a count threshold because an extreme rate is estimated
precisely even at small n: 0 of 13 says something, 6 of 13 does not.

Definitions live once, in `src/analysis/crosstabs.py`, shared by the audit
script, the site build and this document.

---

## 4. Sector, within era

| SIC division | 2010–11 | 2012–14 | 2015–18 | 2019–21 | 2022–24 | pooled |
|---|---|---|---|---|---|---|
| Manufacturing | 2/9 · 22% | 5/22 · 23% | 14/27 · 52% | 12/14 · 86% | 27/33 · 82% | 60/105 · **57%** |
| Mining | 0/6 · 0% | 0/13 · 0% | 13/34 · 38% | 9/19 · 47% | 0/1 · ± | 22/73 · **30%** |
| Services | 2/12 · 17% | 1/7 · 14% | 6/11 · ± | 3/10 · 30% | 9/13 · 69% | 21/53 · 40% |
| Finance, Insurance, Real Estate | 1/14 · 7% | 3/9 · ± | 3/5 · ± | 4/5 · ± | 3/8 · ± | 14/41 · 34% |
| Retail Trade | 0/3 · ± | 1/7 · 14% | 1/5 · ± | 5/8 · ± | 5/8 · ± | 12/31 · 39% |
| Transport & Utilities | 1/3 · ± | 3/9 · ± | 5/9 · ± | 4/8 · ± | none | 13/29 · 45% |
| Wholesale Trade | none | 1/2 · ± | 3/4 · ± | 0/1 · ± | 1/2 · ± | 5/9 · ± |
| **all candidates** | 6/47 · 13% | 14/71 · 20% | 46/96 · 48% | 37/65 · 57% | 46/67 · 69% | 149/346 · 43% |

**Survives conditioning.** Mining resolves below its own era in every era where
the cell can be read. Manufacturing sits above its era in **all five**, every
cell reportable, from 22% against 13% to 82% against 69%. Those are sector
effects, not era in disguise.

**Does not survive conditioning.** The claim that financials resolve worst rested
on a single cell of fourteen firms in 2010–11, where the era average is 13%
anyway, and every later financials cell is too small to report. Sector
composition varies sharply across eras: financials are 29.8% of 2010–11
candidates and 5.2% of 2015–18; mining is 35.4% of 2015–18 and 1.5% of 2022–24.
The pooled financials figure is composition.

**Independent of resolution rates**, the cohort still under-samples financials:
they are 11.8% of candidates and 9.4% of the resolved set. That is a fact about
the cohort, it flatters the headline result, and it is stated for that reason.

---

## 5. Size, within era: no gradient survives

| Public float at last 10-K | 2010–11 | 2012–14 | 2015–18 | 2019–21 | 2022–24 | pooled |
|---|---|---|---|---|---|---|
| under $50M | 1/5 · ± | 5/28 · 18% | 22/41 · 54% | 18/33 · 55% | 14/25 · 56% | 60/132 · 45% |
| $50–200M | 0/1 · ± | 0/5 · 0% | 13/20 · 65% | 7/10 · 70% | 14/20 · 70% | 34/56 · 61% |
| $200M and above | 2/4 · ± | 4/11 · 36% | 7/14 · 50% | 10/19 · 53% | 15/17 · 88% | 38/65 · 58% |
| none reported | 3/37 · 8% | 5/27 · 19% | 4/21 · 19% | 2/3 · ± | 3/5 · ± | 17/93 · 18% |
| **all candidates** | 6/47 · 13% | 14/71 · 20% | 46/96 · 48% | 37/65 · 57% | 46/67 · 69% | 149/346 · 43% |

Of the four eras in which all three bands can be read, the rate rises with size
in exactly one (2022–24). In two the middle band is highest; in 2012–14 it is
lowest. There is no consistent ordering at any level of conditioning. **The
cohort does not measurably skew large.**

### 5.1 Float availability is itself an artefact of the XBRL transition

Public float is read from `dei:EntityPublicFloat` through the `companyconcept`
API. That is an XBRL tag, so a filer with no XBRL instance has no float **by
construction**, not because it is small, but because it filed before 2011.

| Filer has XBRL | N | Reports a public float | Share |
|---|---|---|---|
| yes | 279 | 243 | 87.1% |
| no | 67 | 10 | 14.9% |

The two agree on **86.7%** of 346 candidates. So the "none reported" band is
substantially the pre-XBRL population wearing a different label, and its low
pooled rate (18.3%) is mostly era: 37 of its 93 firms sit in 2010–11, where
nothing resolves anyway. Within 2012–14 it resolves at 19% against an era average
of 20%, no gap at all. Only in 2015–18 is there a real one (19% against 48%).

This is a finding about the public record, which is the study's actual subject,
rather than a finding about firm size.

---

## 6. Where the losses are

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

`AMBIGUOUS_OVERLAPPING`, the mutual-exclusivity guard, independently caught
**American Airlines (CIK 0000004515)**, the AAL/AMR ticker splice found by hand
in Phase 0. A registrant cannot trade under two symbols at once, so candidates
whose windows overlap are flagged rather than auto-ranked. It is also the single
largest cause of the difference between this run and the last: see §7.1.

**Chapter 22: 29 of 346 (8.4%)** filed Item 1.03 more than once. The first filing
is the event (spec 1.2.2); subsequent dates are recorded.

---

## 7. Three corrections

All reached the README and the site before being caught. Recorded rather than
quietly overwritten.

### 7.1 The size gradient: retracted, then the retraction corrected

At N = 190 this was reported as *"float ≥ $200M resolves at 79%, < $200M at 51%"*
and written up as "the cohort skews large". At N = 346 the top band is 58.5%, and
the claim was withdrawn **as small-sample noise**. That reached the right
conclusion by the wrong route: three things had changed between the runs, so
nothing was identified. Holding each fixed:

| Candidate cause | Verdict |
|---|---|
| The exclusion-taxonomy fix (§7.2) | **Not implicated.** Re-run on the same 346 candidates before and after, every float band is identical except "none reported". It recovered 5 firms, all in that band. |
| The year range (2006–2024 → 2010–2024) | **Not implicated.** Restricted to 2010–2024 the old top band goes *up*, to 18 of 22 (81.8%). |
| The resolver becoming stricter | **Most of it.** Nine firms present in both runs flipped resolved → unresolved, seven of them to `AMBIGUOUS_OVERLAPPING`, a guard that did not exist for the earlier run. On the 17 top-band firms common to both samples, 15 of 17 became 11 of 17. |
| Ordinary imprecision | **The remainder.** 18 of 22 against 38 of 65 is not a significant difference (Fisher exact, p = 0.07); the intervals overlap. |

So the finding did not collapse. A point estimate was published without its
interval, from a cell whose 95% Wilson bounds ran from 60% to 91%, and several of
the resolutions underneath it were then correctly withdrawn.

**The limit of the fix.** Suppressing rates on wide intervals is a floor, not a
safeguard: 19 of 24 has an interval only 31 points wide and would still be
reported today. `tests/test_crosstabs.py` asserts that explicitly, so the rule is
not later mistaken for protection it does not offer.

### 7.2 `NO_COMMON_EQUITY` was misclassifying pre-XBRL filers

The structural gate excluding registrants with no common shares outstanding ran
*before* checking whether the filer had any XBRL at all. A pre-2011 filer with no
XBRL looks identical to a partnership with no common equity, so 72% of 2010–11
candidates were labelled non-Merton objects, including **Corus Bankshares** and
**AMCORE Financial**, both banks with ordinary common stock.

This corrupted precisely the distinction the two exclusion families exist to
draw: *"the firm does not belong in the study"* versus *"the data does not
exist"*.

Fixed by making the check tri-state (`present` / `absent` / `no_xbrl`) and only
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

### 7.3 Stale sector figures stood for one commit

§3 of the previous version of this document reported financials at 26.8% and
manufacturing at 56.2%. Those were the **pre-repass** numbers: three of the five
firms recovered in §7.2 are financials. The site rebuilt from the CSV and was
correct; this document was hand-edited for size and not for sector, and the two
disagreed until now. `tests/test_crosstabs.py` now asserts that the published
JSON matches the committed CSV row for row.

---

## 8. Cost

The full pass took **90 minutes for 346 CIKs**, down from 11.1 hours for 190
before the text tier moved to EDGAR full-text search. FTS returns the exact
`accession:filename` containing the phrase, replacing a blind multi-megabyte
download per filing with one API call plus one targeted fetch.
