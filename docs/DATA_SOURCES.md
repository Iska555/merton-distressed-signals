# Data sources and licensing

This project selects sources for research fit, historical coverage, reproducibility and permission to retain the resulting artifact. Public access is not the same as unrestricted redistribution. A dataset that anyone can view or retrieve can still carry source-specific publication limits.

The machine-readable policy is [SOURCES.json](../frontend/public/data/SOURCES.json). It records the official page, access method, terms, redistribution boundary, point-in-time limitation and known failure mode for every external source used or reviewed.

## Source selection

SEC EDGAR supplies bankruptcy-event candidates and filing text. SEC Company Facts supplies issuer fundamentals, shares and historical filing metadata. SEC DERA Financial Statement Data Sets supply the quarterly filer universe and bulk facts used to avoid sampling only firms that survive today. Government-created SEC content and public EDGAR filings may be reused with citation, but this repository commits derived research artifacts rather than mirror copies of SEC feeds.

Tiingo is used where delisted equity histories cannot be obtained reliably from free current-listing sources. Its use is constrained by symbol identity, plan quotas and storage terms. Starter and trial data may not be persisted as raw data. Only non-reconstructable derived products may be retained or distributed under the terms.

Damodaran's current data are used as an analytical starting point for synthetic-rating thresholds and the January 2026 periodic default-spread benchmark. The benchmark is a cited periodic input to a derived screen. It is not a live market price.

FRED's ICE BofA option-adjusted spread series was reviewed and then excluded from committed public output. The series notes state that exact index observations are copyrighted, for internal use only, and may not be published without approval. The two previously committed JSON files containing those observations were removed.

## Credentials

SEC access requires no key, but requests identify the project through a descriptive User-Agent. Tiingo access requires an API key and remains subject to the selected plan's quotas and terms. No FRED credential is used by the supported public-data build.

Credentials belong in a local `.env` file and must never be committed or sent to the browser. The repository's `.env.example` lists only credentials used by supported code.

## Raw-data retention

Raw external data are not public release artifacts. Local caches exist to control request volume and make research runs resumable, but retention must follow the source plan and terms. In particular, Tiingo starter and trial responses must not be persisted as a reusable raw-price archive.

Committed outputs are compact derived research artifacts: classifications, audits, aggregate counts, model inputs that terms permit, and non-reconstructable results. They are not substitutes for the originating feeds.

## Point-in-time rules

An observation is available to the study only after it was filed or published. SEC facts are filtered by filing date, not only by the financial period they describe. Control firms come from the DERA archive for the relevant quarter, not from today's listed universe.

A ticker is never treated as a permanent issuer identifier. Tickers are reused, and a delisted symbol can later belong to another company. Price histories are accepted only after the issuer, symbol and trading window are reconciled using contemporaneous filings and listing dates.

Historical SEC coverage is limited by what registrants disclosed and by XBRL adoption. Full-text search begins in 2001, while structured financial-statement coverage is sparse before roughly 2009. These are source limits, not missing values to be inferred.

The January 2026 Damodaran benchmark is a periodic snapshot. It must not be described as contemporaneous with an earlier bankruptcy event, a live ICE index, a live credit price or an issuer bond quote.

## Publication boundary

The public site may publish outputs only when the linked terms permit the retained form. Source citation is required but does not override a publication restriction.

Exact ICE BofA observations are not committed. Tiingo raw histories are not distributed or retained under starter or trial terms. SEC-derived research outputs carry citation. Damodaran inputs and derived screens carry source and vintage metadata. Any future source must be added to the registry and reviewed before its values enter a public artifact.
