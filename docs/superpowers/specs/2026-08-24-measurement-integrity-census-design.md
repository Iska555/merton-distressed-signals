# Measurement Integrity Census Rebuild

**Status:** Approved architecture, pending specification review
**Date:** 2026-08-24
**Release state:** Public release remains on hold until every acceptance condition in this document is met.

## 1. Purpose

Rebuild the bankruptcy-candidate evidence base as a reproducible census, then separate two questions that the current site mixes together:

1. **Public-record coverage:** What share of SEC Item 1.03 registrant-case candidates can be connected to the public market data required for a structural credit study?
2. **Investment evidence:** Within an investable, size-qualified subset, does the model discriminate future distress out of sample?

The existing 346-row sample remains useful as evidence of a sampling defect, but it is superseded as an estimator. All rates and repeated-filing claims currently derived from it, including every rate on `/measurement`, are unverified until regenerated under this design.

No branch push, merge, production deployment, or public release is permitted before the rebuilt evidence and all release gates pass.

## 2. Confirmed defect and its measured effect

The legacy collector queried one calendar year at a time and limited each request loop to four pages when the target was 25 rows per year. Its `page_size` default was 10, but the SEC query did not send an explicit result-size parameter. The SEC returned 100 hits per response while the code advanced offsets by 10. The four requests therefore covered overlapping relevance-ranked ranges starting at 0, 10, 20, and 30 rather than enumerating the year.

The results were ordered by `_score` descending, not by filing date. In all 15 annual snapshots, neither ascending nor descending filing-date order explained the result order.

The diagnostic snapshot found:

| Measure | Result |
|---|---:|
| Annual reported hits, 2010 to 2024 | 183 to 647 |
| Unique structured Item 1.03 documents visible through the legacy loop | 40 to 130 |
| Unique CIKs visible through the legacy loop | 32 to 109 |
| Visible structured documents as a share of reported hits | 17.3% to 67.8% |
| 2016 reported hits | 647 |
| 2016 unique structured documents retrieved | 128 |
| 2016 distinct CIKs visible | 99 |
| 2016 rows retained | 25 |

For 2016, roughly 80% of reported hits disappeared before the intended 25-row research selection. Because the first loss depended on full-text relevance, the retained rows did not have known inclusion probabilities.

This diagnosis must appear in the final methodology and correction record. It is the motivating example for the project's central claim that data construction can dominate apparent investment results.

## 3. Units and terminology

The rebuild uses the following units and never substitutes one for another:

- **Reported hit:** A hit counted by the SEC full-text endpoint for the specified query and date window.
- **Retrieved document:** A unique SEC full-text hit identified by its `_id`.
- **Qualifying filing:** A retrieved 8-K with structured Item 1.03 metadata, a CIK, an accession number, and a parseable filing date. Its key is `(CIK, accession)`.
- **Registrant-case candidate:** An operational cluster of qualifying filings for one CIK. It is a research convention, not a claim that the cluster is one court docket or one legally distinct bankruptcy.
- **Event date:** The earliest qualifying filing date in a registrant-case cluster.
- **Resolved case:** A registrant-case candidate connected to a traded symbol with time-valid identity evidence.
- **Usable-price case:** A resolved case with sufficient point-in-time price history for the declared model window.
- **Study case:** A usable-price case that passes all pre-registered analytical eligibility rules.

### 3.1 Registrant-case convention

For each CIK, sort qualifying filings by date and accession. The earliest unassigned filing opens a cluster. Every later filing dated no more than 24 calendar months after that cluster's first filing joins the cluster. The next filing outside the anchored window opens a new cluster. Anchoring the window prevents an indefinitely long cluster created by chains of nearby filings.

The primary convention is 24 months. The pipeline must recompute all cluster counts with 12-month and 36-month windows and report:

- the selected window;
- total clusters under each window;
- the number and share of clusters containing more than one filing;
- the number and share of CIKs with more than one cluster; and
- the sensitivity of all repeat-cluster rates to the three windows.

The label is **repeat-cluster proxy**, not Chapter 22, unless court-docket evidence is added later. No current repeated-filing rate may be described as case-level legal truth.

## 4. Nested populations

### 4.1 Population 1: public-record coverage census

Population 1 contains every registrant-case candidate enumerated from qualifying Item 1.03 filings dated from 2010-01-01 through 2024-12-31. It has no public-float, assets, exchange, or price-history floor.

Population 1 answers a measurement question. It is the denominator for public-record coverage, identity resolution, and price availability. `dei:EntityPublicFloat` may be analyzed descriptively, including its missingness, but must never filter this population. Any float comparison must use only facts filed on or before the event date. The current latest-observation helper is not valid for this purpose because it can introduce look-ahead.

For each case, the study also reports two DERA availability indicators as of the event date:

1. a timely DERA financial-statement submission exists; and
2. a timely, usable total-assets fact exists.

These rates are reported by pre-registered era. They provide an independent measurement of the same disclosure discontinuity seen in identity resolution. They do not determine Population 1 membership.

### 4.2 Population 2: size-qualified investment population

Population 2 is a strict subset of Population 1 and is pre-registered to begin on 2012-01-01. It ends on 2024-12-31.

The 2012 start is fixed before outcomes are observed because the SEC Financial Statement Data Sets are an XBRL product, and XBRL coverage phased in from 2009 through roughly 2011. Applying an XBRL-dependent assets floor during the phase-in period would entangle the investment eligibility rule with the disclosure mechanism under study.

A Population 1 case enters Population 2 only when:

- its event date is within 2012 to 2024;
- a DERA statement was filed on or before the event date;
- the statement period ends on or before the event date;
- the statement period is no more than 450 calendar days before the event date; and
- point-in-time total assets are at least USD 50 million.

Missing or conflicting assets are not imputed. Such rows remain in Population 1 and are shown as explicit exclusions from Population 2.

Population 2 then nests the resolved, usable-price, and final-study subsets. Every downstream row must have an upstream Population 1 key, and automated tests must enforce this relationship.

## 5. Complete SEC enumeration

### 5.1 Query protocol

The enumerator uses calendar-quarter windows initially. Every request sets an explicit supported result size of 100 and advances the next offset by the number of raw hits actually returned, not by a local default.

For each window, the enumerator records the SEC-reported total and continues until the cumulative raw hit count equals that total. A window is complete only if all of the following hold:

- cumulative raw hits equal the reported total;
- no requested range is skipped or unintentionally overlapped;
- all returned `_id` values and request boundaries are recorded;
- repeated requests produce stable totals and document identifiers within the frozen retrieval run; and
- the reported total remains below the endpoint cap.

If a window reaches 10,000 reported hits, has unstable totals, returns an empty page before completion, or produces an offset mismatch, the run fails closed. A capped window is recursively divided into smaller date windows until each child can be proven complete.

Deduplicate retrieved documents by `_id`. Deduplicate qualifying filings by `(CIK, accession)`. Preserve document-level multiplicity separately so that the conversion from search hits to filings remains visible.

### 5.2 Retrieval manifest

Every retrieval run writes a deterministic manifest containing:

- query text, form filter, structured-item rule, and date boundaries;
- request size, offsets, returned counts, reported totals, and retrieval timestamp;
- response hashes and endpoint identifiers;
- unique document, qualifying filing, CIK, and cluster counts;
- software revision and schema version; and
- completion or failure status for every window.

Raw SEC responses and filing documents remain in the ignored data cache. The committed manifest contains hashes and the derived fields needed to reproduce every published count without committing a large archive of SEC documents.

### 5.3 Relevance mechanism fields

For each retrieved hit, preserve `_score`. Retrieve the exact matched archive document and record:

- response byte length;
- normalized visible-text character count;
- content SHA-256;
- archive URL and accession; and
- retrieval status.

The normalized text-length algorithm must be versioned and tested. `_score` is a search-system snapshot rather than a permanent issuer attribute, so the retrieval timestamp, response hashes, and this limitation must accompany the falsification result.

## 6. DERA ingestion and point-in-time assets

The existing DERA module already downloads quarterly archives, joins `sub.txt` to selected `num.txt` facts, keeps instant balance-sheet facts, writes compact Parquet files, and deletes each ZIP. The rebuild hardens this path rather than replacing it.

The study has 60 event quarters from 2010Q1 through 2024Q4. Ingestion begins in 2009Q1, for 64 quarterly archives in total, so early 2010 events can use timely statements from the preceding 450 days. Population 2 has 52 event quarters from 2012Q1 onward, but the complete archive set is required for Population 1 coverage reporting and event-time lookback selection.

### 6.1 Event-time selection

For each case, eligible statements must satisfy `filed <= event_date`, `period <= event_date`, and the 450-day staleness limit. Select the eligible submission with the latest reporting period, then the latest filing date available by the event, then a deterministic accession tie-break.

An amended filing is eligible only if the amendment itself was filed by the event date. A later restatement may not replace information that was unavailable at the event.

Total assets use `Assets` first and `LiabilitiesAndStockholdersEquity` only as a documented accounting-identity fallback. Values must be in USD and strictly positive.

### 6.2 Conflict handling

The current `pivot_table(..., aggfunc="first")` behavior is not acceptable for eligibility. The retained data must include every field needed to explain duplicate facts, including taxonomy version, units, decimals, accession, filing type, period, and filed date where available.

Exact duplicates may collapse. Conflicting qualified facts must be resolved by a written priority rule with provenance, or the case must be marked conflicting and excluded from Population 2. Row order may never decide the USD 50 million floor.

Archive schema, required columns, expected units, and row counts must be validated per quarter. A missing or malformed quarter fails the evidence build rather than silently reducing coverage.

### 6.3 DERA coverage outputs

Within Population 1, report timely submission availability and timely usable-assets availability for the fixed eras in Section 9. Publish both the numerator and denominator. This result is descriptive evidence about disclosure coverage and does not retroactively change the census.

## 7. Census fallback, pre-registered before resolution

Enumeration, document retrieval, qualifying-filing identification, and clustering remain censuses. There is no fallback to convenience sampling for these stages.

After a 200-case identity-resolution pilot, a probability-sample fallback may be triggered only if either:

- the census contains more than 7,500 registrant-case clusters; or
- measured pilot throughput projects more than 12 hours for one serial full-resolution run.

The pilot exposes timing and completion status only; outcome labels and aggregate rates remain hidden until the trigger decision is recorded. If triggered, cases are sampled within era by one-digit SIC division by DERA-availability strata, with Population 2 eligibility included as an explicit stratum so the investment population is represented by design. Every row receives a known inclusion probability. Population estimates use Horvitz-Thompson weights and design-based confidence intervals. Sampling code, seed, stratum counts, inclusion probabilities, and finite-population corrections are committed.

The complete enumerated census and funnel counts are still published. Only the expensive identity and price-resolution stages may use the probability sample.

## 8. Falsification of the legacy 346-row sample

The old sample is preserved as a superseded artifact and matched back to Population 1. The test asks whether relevance-ranked truncation created a detectably different sample from the population the legacy design intended to represent.

### 8.1 Variables

Compare legacy membership on:

- event year;
- DERA submission and usable-assets availability;
- public float and a separate public-float-missing indicator, conditioned by era;
- one-digit and two-digit SIC, including missing SIC;
- qualifying filing count per CIK and filing count per 24-month cluster;
- maximum search `_score` within the cluster; and
- log normalized length of the document carrying that maximum score.

Use accession and `_id` as deterministic tie-breaks when multiple documents share the maximum score. Median cluster-document length is a declared robustness measure, not a replacement for the primary max-score-document field.

Public float is descriptive only. Its XBRL dependence is handled by reporting missingness and era-conditioned comparisons rather than treating missing values as small firms.

### 8.2 Tests and thresholds

Run both an overall comparison and within-year comparisons that isolate relevance ranking from the intended equal-year allocation. The reference distribution uses 10,000 deterministic randomizations that preserve 25 selections per year where available and preserve the legacy global CIK deduplication rule.

Use standardized mean differences and Kolmogorov-Smirnov statistics for continuous fields, Cramer's V for categorical fields, and Holm-adjusted p-values across the pre-registered family.

The legacy sample passes only if the omnibus randomization test has `p >= 0.05` and every absolute standardized mean difference or Cramer's V is below 0.10.

The proposed document-length mechanism is supported only if all of the following hold:

- the omnibus test rejects at `p < 0.05`;
- legacy rows have higher `_score` and shorter normalized documents;
- both `_score` and log length have absolute standardized mean differences of at least 0.20; and
- both directional tests remain significant at Holm-adjusted `p < 0.05`.

If the omnibus test rejects without this stable directional pattern, report detectable but mechanistically unresolved selection bias. Publish all outcomes, including a null result.

## 9. Pre-registered disclosure-era gradient

The eras remain fixed:

1. 2010 to 2011
2. 2012 to 2014
3. 2015 to 2018
4. 2019 to 2021
5. 2022 to 2024

The directional hypothesis is that symbol resolution and DERA availability rise as structured disclosure matures.

The resolution gradient is declared to survive only when all four conditions hold:

- the latest-era resolution rate exceeds the earliest-era rate by at least 20 percentage points;
- an ordinal-era logistic coefficient is positive with CIK-clustered `p < 0.01`;
- no adjacent era declines by more than 5 percentage points; and
- the 2019 to 2024 rate exceeds the 2012 to 2018 rate with CIK-clustered `p < 0.01`.

Report case counts, resolved counts, rates, and 95% confidence intervals for every era. Apply the same era table to timely DERA submission and assets availability, but describe those as corroborating disclosure measures rather than outcomes. If the criteria fail, narrow or remove the current causal language. Results are published regardless of direction.

## 10. Blinded verification

After census construction, draw a new 80-row verification sample stratified by era, resolution outcome, and major reason family, using a fixed committed seed. Sampling occurs only after the population manifest is frozen.

Generate a blinded evidence packet that:

- randomizes row order;
- hides aggregate rates and stratum labels;
- includes the evidence required to judge symbol identity and event-time validity; and
- contains no pre-filled verdict.

Human verdicts are stored in a separate committed file with an allowed-value schema and adjudication notes. The release fails if any sampled row has a blank or invalid verdict. Publish verification counts and Wilson intervals by stratum before any pooled rate. The current partially blank 80-row file and the older 20-row summary cannot satisfy this gate.

## 11. Published funnel and correction record

A monotone funnel cannot place distinct CIKs before registrant-case clusters because one CIK can generate more than one cluster. The primary figure therefore uses this order:

> SEC hits reported -> unique documents retrieved -> qualifying Item 1.03 filings -> registrant-case clusters -> above the Population 2 assets floor -> resolved to a symbol -> usable prices -> final study

At the cluster stage, annotate the number of distinct CIKs. This preserves every requested count without implying that clusters must be fewer than issuers.

Every stage displays its count, the conversion rate from the preceding stage, and the retained share of reported hits. Population 1 and Population 2 use visibly distinct labels. The assets-floor stage explicitly states that it begins in 2012.

The 2016 legacy path, `647 reported -> 128 unique structured documents -> 99 visible CIKs -> 25 retained`, appears as a dated defect inset, not as part of the corrected funnel.

The site and README include a correction record with:

- the affected versions and claims;
- the omitted-size and overlapping-offset mechanism;
- how the defect was detected;
- before and after counts;
- the consequences for every old `/measurement` rate; and
- the controls added to prevent recurrence.

No public page may present `149 of 346`, `29 of 346`, or an unqualified Chapter 22 statement as current evidence unless a new result independently supports it. The old values may appear only inside a clearly labeled correction history.

## 12. Remaining release-integrity work

The census rebuild also closes the other independent review findings:

- **Deterministic site data:** Build all published data from a versioned manifest. Remove uncontrolled timestamps and source revisions from committed outputs, or inject them from a declared build epoch. CI regenerates and fails on drift.
- **Locked Python environment:** Commit `uv.lock` covering production, research, and test dependencies. CI installs with `uv sync --frozen --all-extras`.
- **Dependency security:** Add `npm audit --omit=dev --audit-level=low` to the release gate alongside lint and build.
- **Homepage scope:** Describe legacy results as sampled and Item 1.03-specific until the census supports broader language.
- **Market-data budget ledger:** Remove the claim that a symbol-level Tiingo ledger is committed. Keep the credential-associated symbol ledger local and ignored, reconcile it with authoritative account usage before each fetch, and commit only aggregate, non-sensitive usage metadata.
- **Spread semantics:** Rename the Python expected-loss approximation and the TypeScript structural debt spread so two different quantities are never presented under one label. Add shared fixtures where the formulas are intended to agree and explicit explanatory copy where they are not.
- **Removed route residue:** Delete the unused evidence route mark and any navigation or asset references left by the removed route.

## 13. Cost and schedule range

DERA is not a greenfield ingestion path, but point-in-time eligibility and conflict handling are new work. The schedule is an effort range, not a release-date commitment.

| Workstream | Estimated effort | Material cost |
|---|---:|---|
| Complete SEC enumerator and manifests | 2 to 3 working days | SEC retrieval time and polite rate limits |
| Clustering, matched-document retrieval, and length metrics | 2 to 4 working days | Archive-document transfer and cache growth |
| DERA hardening and 64-quarter ingestion | 3 to 5 working days | About 7.3 GB sequential ZIP transfer; about 83 MB retained if the cached quarter is representative |
| Identity-resolution census and reliable reruns | 1 to 2 working days | Pilot-dependent; projected 4 to 12 hours per complete unattended run |
| Legacy falsification and era tests | 2 to 3 working days | Compute is modest after data freeze |
| Blinded verification and adjudication | 2 to 4 working days | Human-dependent |
| Site regeneration, correction record, and release review | 2 to 3 working days | Browser and CI verification |
| **Total** | **13 to 20 working days** | **Approximately 2.5 to 4 working weeks** |

No calendar release date is committed until the 200-case pilot measures document-fetch and identity-resolution throughput. The estimate must be revised from observed throughput, not optimism.

## 14. Failure handling

Evidence generation fails closed. A partial census, missing quarter, incomplete search window, unresolved DERA conflict, missing verification verdict, or stale generated artifact blocks publication. A machine-readable status manifest identifies the failed stage and preserves the last valid published version.

External endpoints may change. A valid release therefore records retrieval snapshots and hashes, reproduces every transformation from cached inputs, and clearly distinguishes byte-for-byte regeneration from a fresh external-data refresh.

## 15. Test and acceptance matrix

Implementation is accepted only when all of the following are demonstrated:

- A pagination-completeness regression test fails against the legacy offset logic and passes against explicit-size, actual-count advancement.
- Tests cover overlapping pages, changing totals, empty intermediate pages, 10,000-hit subdivision, duplicate `_id` values, and duplicate accessions.
- Cluster fixtures verify anchored 12-, 24-, and 36-month windows, same-day filings, CIK boundaries, and multi-cluster CIKs.
- Population 2 is mechanically proven to be a strict subset of Population 1.
- DERA fixtures prove no look-ahead, amendment timing, 450-day staleness, tag fallback, unit checks, and deterministic conflict handling.
- DERA availability by era is generated from Population 1 without filtering it.
- Falsification statistics and randomizations reproduce from a fixed seed.
- Every verification row has a schema-valid human verdict.
- Every chart and sentence containing a number is generated from a declared data artifact.
- The funnel contains every specified stage and annotates distinct CIKs without violating monotonicity.
- The correction record identifies the sampler defect and shows before and after counts.
- No chart uses chocolate, burgundy, and red as hue-only categorical encodings.
- Asset regeneration, published-figure reproduction, Python tests, frontend lint, frontend build, npm production audit, em-dash test, and repository drift checks all pass.
- Commit metadata contains only the owner's authorship and no AI co-author trailer.
- A final independent code review finds no critical or important issue before push, merge, and production deployment.

## 16. Decision boundary

Approval of this document authorizes implementation planning, not implementation. The implementation plan must break the work into reviewable, test-first milestones and preserve the release hold. Any change to the population definitions, 2012 start, USD 50 million floor, clustering convention, fallback trigger, falsification thresholds, or era-gradient criteria requires a documented specification amendment before outcomes are used.
