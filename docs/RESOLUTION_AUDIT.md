# Resolution Audit — who gets into the treatment cohort, and who doesn't

**Run:** 2026-08-20 · **Sample:** 190 bankruptcy candidates, 10 per year, 2006–2024
**Source:** 8-K Item 1.03 filings via EDGAR full-text search
**Output:** `data/processed/resolution_audit.csv`

This becomes a visible exhibit on `/data`. Exclusion that correlates with size,
sector or era makes the treatment cohort a biased sample of defaults, and every
downstream number inherits that bias. It has to be published whichever way it
comes out.

---

## 1. Headline

**71 of 190 candidates resolved to a usable ticker (37.4%).**

Two provenance tiers, never merged:

| Tier | N | How |
|---|---|---|
| `xbrl` | 49 | `dei:TradingSymbol` from the filing's XBRL instance |
| `filing_text` | 22 | Trading symbol from Item 5 prose of the 10-K |

An earlier run of the same audit resolved only 18.9%. The difference is the
`filing_text` tier plus two bug fixes (see §5), not a change of criteria.

---

## 2. The era floor is real, and it has two causes

| Era band | N | Resolved | via xbrl | via text |
|---|---|---|---|---|
| 2006–2011 | 60 | **5%** | 0 | 3 |
| 2012–2018 | 70 | 37% | 11 | 15 |
| 2019–2021 | 30 | 50% | 13 | 2 |
| 2022–2024 | 30 | **90%** | 25 | 2 |

Two distinct thresholds produce this shape:

1. **~2011 — XBRL instance documents begin to exist.** Six pre-2010
   bankruptcies (Lyondell, Nortel, Sharper Image, TOUSA, Buffets, Lehman)
   returned *zero* instance documents across their filings.

2. **2019–2021 — `dei:TradingSymbol` becomes tagged.** The SEC's FAST Act
   Modernization rule introduced cover-page Inline XBRL. Before it, the tag
   does not exist; after it, resolution jumps to 90%.

**Verified directly:** Kodak's 2011 10-K cover page carries only *"Title of
each Class"* and *"Name of each exchange on which registered"*. There is **no
trading symbol on the page at all** — the "Trading Symbol(s)" column was
created by that same 2019 rule. Cover-page text extraction, the obvious
fallback, is therefore impossible for pre-2019 filings: the datum is absent.

Item 5 prose is the only surviving route, and it works: *"traded on the New
York Stock Exchange under the symbol EK"*. That is the `filing_text` tier, and
it carries most of the 2012–2018 recovery (15 of 26 resolutions in that band).

### Practical floor

**The usable window is 2012–2024.** The 2006–2011 band resolves at 5%, and the
handful that do resolve are firms whose CIK still files today — themselves a
selected group. The 2008–09 default cluster, the richest concentration of
corporate failure in modern history and the one every reader will look for,
**cannot be studied with free data**. This is a period-selection limitation
that must appear in visible UI alongside survivorship bias.

---

## 3. Exclusion is not random

### By size — the clearest bias

| Public float at last 10-K | N | Resolved |
|---|---|---|
| ≥ $200M | 24 | **79%** |
| < $200M | 89 | 51% |
| None reported | 77 | **9%** |

Firms reporting no public float are 41% of all candidates and almost never
resolve. They are shells, liquidating trusts and LPs, and the study's $50M
asset floor removes them regardless — but the resulting cohort is **skewed
toward larger firms**, and that must be stated.

Of the 71 resolved, **36 have a public float ≥ $50M**.

### By sector

| SIC division | N | Resolved |
|---|---|---|
| Transport & Utilities | 15 | 60.0% |
| Manufacturing | 60 | 46.7% |
| Wholesale Trade | 5 | 40.0% |
| Services | 27 | 37.0% |
| Finance, Insurance, Real Estate | 37 | **29.7%** |
| Mining | 27 | 25.9% |
| Retail Trade | 15 | **20.0%** |

Financials resolve poorly *and* are 37 of 190 candidates. The cohort therefore
under-samples exactly the sector where the Merton model is least applicable —
which cuts in the study's favour for the headline result and against it for the
sector-heterogeneity exhibit. Both directions are disclosed.

---

## 4. Where the remaining losses are

| Reason code | N | Share | What it is |
|---|---|---|---|
| `SYMBOL_NOT_LISTED` | 58 | 30.5% | Symbol identified, absent from the price vendor's listing table |
| `LISTING_EXCLUDES_EVENT` | 26 | 13.7% | Symbol's trading window does not span the event |
| `NO_XBRL_INSTANCE` | 24 | 12.6% | Pre-XBRL era |
| `NO_TRADING_SYMBOL_TAG` | 11 | 5.8% | XBRL present, cover-page tag absent |

**The binding constraint has moved.** It is no longer "we cannot find the
ticker" — that was the first audit. It is now vendor coverage: `SYMBOL_NOT_LISTED`
firms have a **median public float of $15M and 62% report none at all**. These
are micro-caps the vendor does not carry, and the $50M asset floor excludes
them anyway.

`LISTING_EXCLUDES_EVENT` (median float $31M) is a genuine rejection and largely
a *correct* one: it catches symbol changes across bankruptcy. Kodak's 2011
equity traded as **EK**; the post-emergence **KODK** listing begins 2013-09-23,
after the January 2012 filing, so it is rejected rather than silently
substituted.

---

## 5. Bugs this audit exposed

| Bug | Effect | Status |
|---|---|---|
| All filing types sorted by proximity to the event | Near a bankruptcy the closest filings are overwhelmingly 8-Ks, which often carry no XBRL, crowding out the 10-K/10-Q that does. Produced `NO_XBRL_INSTANCE` for Dendreon (2015, $636M float), which certainly did file XBRL | Fixed — periodic reports searched first |
| Unguarded `json.loads` on EDGAR index | EDGAR serves an HTML error page rather than a 404 for some older accessions; killed 9 firms (4.7%) as `ERROR` | Fixed |
| `filing_text` tier gated on "no candidates" | Kodak has `KODK` in `company_tickers.json`, so the text tier never ran even though every candidate was rejected | Fixed — tier 2 runs when tier 1 yields no *accepted* symbol |

The `NO_XBRL_INSTANCE` count fell from 88 to 24 once the first bug was fixed,
confirming that most of it was a sampling artefact rather than an era floor.
The genuine floor is the 24 that remain, and they are pre-2011.

---

## 6. Cost

The audit took **11.1 hours for 190 CIKs** (~3.5 min each), dominated by the
`filing_text` tier downloading multi-megabyte 10-K documents.

Enumerating every bankruptcy candidate for 2012–2024 (order 1,500 CIKs) would
take roughly 90 hours at this rate. The fix is to apply the **$50M asset floor
before identity resolution rather than after**: it removes the 41% reporting no
public float, which is exactly the population that fails to resolve anyway.
That is both a performance fix and a closer reading of the specification, which
lists the asset floor as criterion T6.

---

## 7. What this means for the study

- **Window: 2012–2024.** Not 2008. State the exclusion of the global financial
  crisis in visible UI, not a footnote — a period with historically low default
  rates and no systemic credit event cannot support claims about crisis
  behaviour.
- **The cohort skews large and skews late.** Both disclosed on `/data`.
- **Financials are under-represented**, which matters for the sector panel.
- Projecting 37.4% resolution and the asset floor onto a full enumeration
  suggests order **150–250 usable treatment firms**, before adjudication and
  price-integrity validation. Under the 400-symbol budget that implies a
  control ratio of 1:1 or 2:1, or a two-month run.
