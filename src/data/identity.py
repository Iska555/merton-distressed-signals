"""
Resolving a CIK to the ticker it actually traded under.

This exists because the obvious routes are all wrong for dead firms:

  - EDGAR's company_tickers.json lists only CURRENTLY REGISTERED filers. Of 579
    bankrupt CIKs sampled in Phase 0, 45 appeared. Using it to attach tickers
    would silently drop 92% of the treatment cohort.
  - EDGAR submissions returns tickers=[] for anything delisted.
  - Guessing the old symbol and appending "Q" is a guess.

What does work is the cover page of the filings themselves: dei:TradingSymbol
is tagged in the XBRL instance of 10-K/10-Q/8-K filings, and it survives
delisting because the filing is immutable. Bed Bath & Beyond's CIK resolves to
BBBYQ this way -- which is exactly the symbol under which its real price
history is retrievable.

A resolved ticker is then checked against Tiingo's public listing file, which
records the trading window of every symbol including delisted ones. If the
symbol's window does not span the event date, the match is rejected: that is
the recycled-ticker trap, caught before any price is fetched.
"""
from __future__ import annotations

import csv
import io
import json
import re
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, field
from functools import lru_cache

import pandas as pd

from ..config import DATA_RAW, SEC_USER_AGENT
from . import edgar

_CACHE = DATA_RAW / "identity"
_CACHE.mkdir(parents=True, exist_ok=True)

_TICKER_TAG = re.compile(
    r"<dei:TradingSymbol[^>]*>([^<]{1,15})</dei:TradingSymbol>", re.IGNORECASE
)
_SKIP_SUFFIXES = ("_cal.xml", "_lab.xml", "_pre.xml", "_def.xml", "_ref.xml")


# Machine-readable outcomes, so the exclusion audit can be cross-tabulated
# rather than read as prose. Every excluded firm carries exactly one of these.
class ReasonCode:
    RESOLVED_XBRL = "RESOLVED_XBRL"
    RESOLVED_FILING_TEXT = "RESOLVED_FILING_TEXT"
    NO_FILINGS = "NO_FILINGS"
    NO_XBRL_INSTANCE = "NO_XBRL_INSTANCE"          # pre-XBRL era: no instance docs exist
    NO_TRADING_SYMBOL_TAG = "NO_TRADING_SYMBOL_TAG"  # XBRL present, tag absent
    SYMBOL_NOT_LISTED = "SYMBOL_NOT_LISTED"        # absent from the listing table
    LISTING_EXCLUDES_EVENT = "LISTING_EXCLUDES_EVENT"  # window does not span the event


@dataclass
class Identity:
    cik: str
    name: str | None = None
    ticker: str | None = None
    source: str = ""
    reason_code: str = ""
    provenance: str = ""          # "xbrl" | "name_match" | ""
    listing_start: str | None = None
    listing_end: str | None = None
    exchange: str | None = None
    candidates: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)
    xbrl_instances_seen: int = 0

    @property
    def resolved(self) -> bool:
        return bool(self.ticker)


# --------------------------------------------------------------------------
# Tiingo public listing file (no API key required)
# --------------------------------------------------------------------------

_LISTING_URL = "https://apimedia.tiingo.com/docs/tiingo/daily/supported_tickers.zip"

# Venues where a delisted US equity continues to be quoted. A bankrupt firm's
# symbol almost always migrates to one of these, which is why they cannot be
# filtered out as "not a real exchange".
_US_VENUES = {
    "NYSE", "NASDAQ", "AMEX", "NYSE ARCA", "BATS",
    "PINK", "OTCMKTS", "OTCGREY", "OTCBB", "OTCQB", "OTCQX", "OTCCE", "EXPM",
}


@lru_cache(maxsize=1)
def load_listing_table(refresh: bool = False) -> pd.DataFrame:
    """
    Every symbol Tiingo knows, with its trading window.

    108,367 rows, of which 16,513 are stocks whose listing has ended. This is a
    public file and needs no credential, so ticker validation works even when
    no price API key is configured.
    """
    path = _CACHE / "tiingo_supported_tickers.csv"
    if not path.exists() or refresh:
        req = urllib.request.Request(_LISTING_URL, headers={"User-Agent": SEC_USER_AGENT})
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read()
        archive = zipfile.ZipFile(io.BytesIO(raw))
        member = archive.namelist()[0]
        with archive.open(member) as handle:
            path.write_bytes(handle.read())

    frame = pd.read_csv(path, dtype=str).fillna("")
    frame["ticker"] = frame["ticker"].str.upper()
    return frame


def listing_window(ticker: str) -> dict | None:
    """Trading window for a symbol, preferring US equity venues."""
    table = load_listing_table()
    rows = table[
        (table["ticker"] == ticker.upper())
        & (table["assetType"] == "Stock")
        & (table["priceCurrency"] == "USD")
    ]
    if rows.empty:
        return None
    venue_rows = rows[rows["exchange"].isin(_US_VENUES)]
    if not venue_rows.empty:
        rows = venue_rows
    # Longest-lived record wins when a symbol appears more than once.
    rows = rows.assign(_span=rows["endDate"].fillna("") .astype(str))
    row = rows.sort_values("_span", ascending=False).iloc[0]
    return {
        "ticker": row["ticker"],
        "exchange": row["exchange"],
        "start": row["startDate"] or None,
        "end": row["endDate"] or None,
    }


def covers_event(ticker: str, event_date, *, grace_days: int = 45) -> tuple[bool, str]:
    """
    Did this symbol actually trade at the event date?

    Rejects the recycled-ticker trap before any price is fetched: SBNY's
    listing record begins after Signature Bank was seized, so it cannot be
    Signature Bank.
    """
    window = listing_window(ticker)
    if window is None:
        return False, "symbol absent from listing table"

    event = pd.Timestamp(event_date)
    start = pd.Timestamp(window["start"]) if window["start"] else None
    end = pd.Timestamp(window["end"]) if window["end"] else None

    if start is not None and start > event:
        return False, f"listing starts {start.date()}, after event {event.date()}"
    if end is not None and end < event - pd.Timedelta(days=grace_days):
        return False, f"listing ended {end.date()}, before event {event.date()}"
    return True, ""


# --------------------------------------------------------------------------
# Ticker extraction from filings
# --------------------------------------------------------------------------

def _get(url: str, timeout: int = 45) -> bytes:
    return edgar._throttled_get(url, timeout=timeout)


def _all_filings(cik: str) -> pd.DataFrame:
    """Full filing index, including the older batches EDGAR pages out."""
    sub = edgar.get_submissions(cik)
    frames = []
    recent = sub.get("filings", {}).get("recent", {})
    if recent:
        frames.append(pd.DataFrame(recent))
    for extra in sub.get("filings", {}).get("files", []) or []:
        try:
            payload = edgar._cached_json(
                f"https://data.sec.gov/submissions/{extra['name']}",
                f"submissions/{extra['name']}",
            )
            frames.append(pd.DataFrame(payload))
        except Exception:  # noqa: BLE001
            continue
    frames = [f for f in frames if not f.empty]
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    out["filingDate"] = pd.to_datetime(out.get("filingDate"), errors="coerce")
    return out.dropna(subset=["filingDate"]).sort_values("filingDate")


def ticker_from_filings(
    cik: str, near_date=None, *, max_filings: int = 8
) -> tuple[list[tuple[str, str]], int]:
    """
    Read dei:TradingSymbol from several filing XBRL instances.

    Returns (symbols, xbrl_instances_seen). The instance count separates two
    very different failures: a pre-XBRL filer, whose filings contain no
    instance documents at all, from a filer whose XBRL exists but omits the
    cover-page tag. Only the first is a hard era floor.

    Returns every (symbol, provenance) pair found, not just the first. A firm
    that goes bankrupt changes symbol -- Bed Bath & Beyond filed as BBBY before
    its Chapter 11 and BBBYQ after -- and only one of those is the symbol its
    full price history is stored under. Both must be offered to the ranker.

    Filings nearest `near_date` are searched first, then outward, so the
    symbols in force around the event are found before any successor's.
    """
    filings = _all_filings(cik)
    if filings.empty:
        return [], 0

    # Periodic reports FIRST. 10-K/10-Q carry XBRL (mandatory for all filers
    # from 2011) and carry the cover page; 8-Ks frequently carry neither. Near
    # a bankruptcy the closest filings are overwhelmingly 8-Ks, so sorting the
    # combined set purely by proximity crowds the periodic reports out. That
    # made the first resolution audit report NO_XBRL_INSTANCE for firms such
    # as Dendreon (2015, $636M float) which certainly did file XBRL.
    periodic = filings[filings["form"].isin(["10-K", "10-Q", "20-F", "40-F"])]
    current = filings[filings["form"] == "8-K"]

    def _by_proximity(frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return frame
        if near_date is None:
            return frame.sort_values("filingDate", ascending=False)
        target = pd.Timestamp(near_date)
        return frame.assign(
            _gap=(frame["filingDate"] - target).abs()
        ).sort_values("_gap")

    ordered = [f for f in (_by_proximity(periodic), _by_proximity(current)) if not f.empty]
    wanted = pd.concat(ordered, ignore_index=True) if ordered else filings

    cik_int = int(str(cik).lstrip("0") or 0)
    found: dict[str, str] = {}
    instances_seen = 0

    for _, row in wanted.head(max_filings).iterrows():
        accession = str(row["accessionNumber"]).replace("-", "")
        try:
            raw = _get(
                f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/index.json"
            )
            listing = json.loads(raw.decode("utf-8", "replace"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # EDGAR serves an HTML error page for some older accessions rather
            # than a 404. Skip that filing, do not abandon the whole firm --
            # this silently cost 4.7% of the resolution audit as ERROR rows.
            continue
        except Exception:  # noqa: BLE001
            continue

        names = [item["name"] for item in listing.get("directory", {}).get("item", [])]
        instances = [
            n for n in names
            if n.endswith(".xml") and not n.endswith(_SKIP_SUFFIXES)
        ]
        instances.sort(key=lambda n: (not n.endswith("_htm.xml"), len(n)))
        instances_seen += len(instances)

        for name in instances[:2]:
            try:
                doc = _get(
                    f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{name}"
                ).decode("utf-8", "replace")
            except Exception:  # noqa: BLE001
                continue
            for raw in _TICKER_TAG.findall(doc):
                symbol = raw.strip().upper()
                if symbol and symbol not in found:
                    found[symbol] = f"{row['form']} filed {row['filingDate'].date()}"
            if found:
                break
    return list(found.items()), instances_seen


# Item 5 of a 10-K ("Market for Registrant's Common Equity") names the trading
# symbol in prose. This is the ONLY route for pre-2019 filings: the SEC's 2019
# FAST Act Modernization rule added both the cover-page "Trading Symbol(s)"
# column and its Inline XBRL tag, so before then the ticker appears nowhere on
# the cover page. Verified directly on Kodak's 2011 10-K, whose cover page
# carries only "Title of each Class" and "Name of each exchange".
_TEXT_SYMBOL_PATTERNS = [
    re.compile(
        r"under the (?:trading )?symbols?\s*[\"'“‘(]*\s*([A-Z]{1,6})\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:NYSE|NASDAQ|NYSE\s*MKT|NYSE\s*Amex|AMEX|OTCQB|OTCQX|OTC\s*Pink)\b"
        r"\s*[:\-]\s*[\"'“]?\s*([A-Z]{1,6})\b"
    ),
]

# Item 5 ("Market for Registrant's Common Equity") is a 10-K item. Including
# 10-Qs would let filings nearer the event consume the search budget without
# ever containing the phrase -- which is why Dendreon first failed to resolve.
_TEXT_FORMS = ["10-K", "10-K/A", "20-F"]

# Language showing the sentence is about the REGISTRANT's own stock. Required,
# because hand-verification found the tier picking up other companies' tickers.
# Rockies Region 2007 LP yielded PDCE from "The common stock of PDC is traded
# ... under the symbol 'PDCE'" -- PDC Energy being its managing general
# partner, while the partnership itself has no listed stock. The listing-window
# check waves such a symbol through, because it IS a real contemporaneous
# ticker; it just belongs to someone else.
_FIRST_PERSON = re.compile(
    r"\b(our|the Company'?s?|the Registrant'?s?|the Partnership'?s?|we|us)\b",
    re.IGNORECASE,
)

# "the common stock of SOMEONE ELSE is traded" -- the construction that failed.
_THIRD_PARTY = re.compile(
    r"(?:common\s+stock|shares|units)\s+of\s+"
    r"([A-Z][A-Za-z0-9&.\- ]{1,40}?)\s+(?:is|are|was|were|trade|trades)"
)

_NAME_STOPWORDS = {
    "inc", "corp", "corporation", "company", "co", "llc", "lp", "ltd", "plc",
    "holdings", "holding", "group", "the", "of", "and", "sa", "nv", "ag",
    "trust", "partners", "partnership", "international", "industries", "cik",
}


def _name_tokens(name: str) -> set[str]:
    words = re.findall(r"[A-Za-z]+", (name or "").lower())
    return {w for w in words if w not in _NAME_STOPWORDS and len(w) > 2}


def _is_about_registrant(window: str, registrant: str | None) -> bool:
    """
    Does this sentence describe the registrant's own security?

    Accepts first-person framing ("our common shares commenced trading ... under
    the symbol XCOO") or the registrant's own name ("Doral Financial's common
    stock ... is traded ... under the symbol DRL"). Rejects a sentence whose
    grammatical subject is a different named company.
    """
    third_party = _THIRD_PARTY.search(window)
    if third_party:
        subject = _name_tokens(third_party.group(1))
        mine = _name_tokens(registrant or "")
        # A named subject sharing no word with the registrant is someone else.
        if subject and mine and not (subject & mine):
            return False

    if _FIRST_PERSON.search(window):
        return True
    return bool(_name_tokens(registrant or "") & _name_tokens(window))


def _strip_markup(document: str) -> str:
    text = re.sub(r"<[^>]+>", " ", document)
    text = re.sub(r"&#\d+;|&[a-z]+;", " ", text)
    return re.sub(r"\s+", " ", text)


def _fts_documents(cik: str, phrase: str = "under the symbol",
                   forms: str = "10-K", limit: int = 8) -> list[dict]:
    """
    Ask EDGAR full-text search which documents contain the phrase.

    Turns the text tier from "download several multi-megabyte 10-Ks and scan
    them" into "one API call, then fetch the single document that actually
    contains the sentence". Measured at 1.6s per firm against ~3.5 minutes for
    the blind-download approach.

    FTS covers 2001 onward, which fully spans the 2012-2024 study window. The
    response carries no highlight snippet, but each hit's `_id` is
    `accession:filename`, which pinpoints the document -- more useful than a
    snippet, since surrounding context is needed to parse the symbol anyway.
    """
    params = urllib.parse.urlencode({
        "q": f'"{phrase}"', "ciks": str(cik).zfill(10), "forms": forms,
    })
    try:
        raw = _get(f"https://efts.sec.gov/LATEST/search-index?{params}")
        payload = json.loads(raw.decode("utf-8", "replace"))
    except Exception:  # noqa: BLE001
        return []

    out = []
    for hit in payload.get("hits", {}).get("hits", []):
        identifier = hit.get("_id", "")
        if ":" not in identifier:
            continue
        accession, filename = identifier.split(":", 1)
        # Exhibits (indentures, credit agreements) name symbols too, but are
        # not the registrant's own market-for-common-equity statement.
        if re.search(r"ex-?\d|_ex\d", filename, re.IGNORECASE):
            continue
        source = hit.get("_source", {})
        out.append({
            "accession": accession,
            "filename": filename,
            "date": source.get("file_date", ""),
            "form": source.get("form", ""),
        })
    out.sort(key=lambda d: d["date"], reverse=True)
    return out[:limit]


def ticker_from_filing_text(
    cik: str, near_date=None, *, max_filings: int = 3, registrant: str | None = None
) -> list[tuple[str, str]]:
    """
    Read the trading symbol from the prose of a periodic report.

    Provenance tier `filing_text`, kept strictly separate from the `xbrl` tier.
    Document-sourced from the registrant's own filing, so far stronger evidence
    than a fuzzy name match against an external table -- but a regex over prose,
    so still a lower tier than a tagged fact.

    Reads the LATEST filings first, not those nearest the event. The price
    vendor stores a delisted firm's entire history under its TERMINAL symbol:
    Bed Bath & Beyond's 31 years sit under BBBYQ, and plain BBBY is absent
    altogether. The pre-bankruptcy 10-K says "BBBY", which is contemporaneously
    accurate and useless for retrieval; the post-filing 10-K says "BBBYQ",
    which is what the data is actually keyed by. Candidates from several
    filings are returned and the listing-window check disambiguates.
    """
    documents = _fts_documents(cik)
    if not documents:
        return []

    cik_int = int(str(cik).lstrip("0") or 0)
    found: dict[str, str] = {}

    for document in documents[:max_filings]:
        accession = document["accession"].replace("-", "")
        try:
            raw = _get(
                f"https://www.sec.gov/Archives/edgar/data/{cik_int}/"
                f"{accession}/{document['filename']}"
            )
        except Exception:  # noqa: BLE001
            continue
        text = _strip_markup(raw.decode("utf-8", "replace"))
        for pattern in _TEXT_SYMBOL_PATTERNS:
            for match in pattern.finditer(text):
                symbol = match.group(1).strip().upper()
                if not symbol or symbol in found:
                    continue
                window = text[max(0, match.start() - 220):match.end() + 60]
                if not _is_about_registrant(window, registrant):
                    continue
                found[symbol] = (
                    f"{document['form']} text, filed {document['date']}"
                )
                break
            if found:
                break
    return list(found.items())


def _variants(symbol: str) -> list[str]:
    """
    Symbol forms to test against the listing table.

    The trailing "Q" is the standard convention for an issuer in bankruptcy,
    and it is under that symbol that a delisted firm's full history is usually
    stored. This is not guesswork: each variant is only accepted if the listing
    table confirms a trading window that spans the event.
    """
    symbol = symbol.upper().strip()
    out = [symbol]
    if not symbol.endswith("Q"):
        out.append(symbol + "Q")
    elif len(symbol) > 1:
        out.append(symbol[:-1])
    return out


def resolve(cik: str, *, event_date=None, name: str | None = None,
            allow_text_tier: bool = True) -> Identity:
    """
    Best available ticker for a CIK, validated against the listing window.

    Candidates come from dei:TradingSymbol in filings (which works for dead
    firms) and from company_tickers.json (alive firms only). Each candidate,
    plus its bankruptcy-suffix variant, is checked against Tiingo's listing
    table; anything whose trading window does not span the event is rejected.

    Among survivors, the candidate with the LONGEST history before the event
    wins, because that is the series that can support a 36-month event window.
    """
    cik = str(cik).zfill(10)
    profile = edgar.company_profile(cik)
    display_name = name or profile.get("name")

    from_filings, instances_seen = ticker_from_filings(cik, near_date=event_date)

    xbrl_candidates: list[tuple[str, str]] = list(from_filings)
    for symbol in profile.get("tickers") or []:
        xbrl_candidates.append((symbol.upper(), "company_tickers.json"))

    seen: set[str] = set()
    notes: list[str] = []

    def _try(candidates: list[tuple[str, str]]) -> list[tuple[str, str, dict]]:
        """Validate a tier's candidates (and bankruptcy variants) in isolation."""
        out: list[tuple[str, str, dict]] = []
        for symbol, source in candidates:
            for variant in _variants(symbol):
                if variant in seen:
                    continue
                seen.add(variant)
                window = listing_window(variant)
                if window is None:
                    notes.append(f"{variant} rejected: not in listing table")
                    continue
                if event_date is not None:
                    ok, why = covers_event(variant, event_date)
                    if not ok:
                        notes.append(f"{variant} rejected: {why}")
                        continue
                out.append((variant, source, window))
        return out

    accepted = _try(xbrl_candidates)
    tier = "xbrl"
    text_candidates: list[tuple[str, str]] = []

    # Tier 2 runs whenever the tagged route produced no ACCEPTED symbol -- not
    # merely no candidate. Kodak is exactly this case: KODK exists in
    # company_tickers.json but its listing begins after the 2012 filing, while
    # the 10-K prose names EK, the symbol the pre-bankruptcy equity traded under.
    if allow_text_tier and not accepted:
        text_candidates = [
            (symbol, f"text:{source}")
            for symbol, source in ticker_from_filing_text(cik, near_date=event_date)
        ]
        if text_candidates:
            accepted = _try(text_candidates)
            if accepted:
                tier = "filing_text"

    raw_candidates = xbrl_candidates + text_candidates

    if not accepted:
        # Distinguish the failure modes: a pre-XBRL filer (no instance
        # documents exist at all) is a hard era floor, not a fixable gap.
        if not raw_candidates:
            if instances_seen == 0:
                code = ReasonCode.NO_XBRL_INSTANCE
            else:
                code = ReasonCode.NO_TRADING_SYMBOL_TAG
        elif any("listing starts" in n or "listing ended" in n for n in notes):
            code = ReasonCode.LISTING_EXCLUDES_EVENT
        else:
            code = ReasonCode.SYMBOL_NOT_LISTED

        return Identity(
            cik=cik, name=display_name, ticker=None, source="unresolved",
            reason_code=code, provenance="",
            candidates=tuple(sorted(seen)),
            notes=tuple(notes) or ("no candidate symbols found",),
            xbrl_instances_seen=instances_seen,
        )

    def _history_before_event(entry) -> float:
        _, _, window = entry
        if not window.get("start"):
            return 0.0
        start = pd.Timestamp(window["start"])
        anchor = pd.Timestamp(event_date) if event_date is not None else pd.Timestamp.today()
        return float((anchor - start).days)

    symbol, source, window = max(accepted, key=_history_before_event)
    code = (ReasonCode.RESOLVED_FILING_TEXT if tier == "filing_text"
            else ReasonCode.RESOLVED_XBRL)
    return Identity(
        cik=cik, name=display_name, ticker=symbol, source=source,
        reason_code=code, provenance=tier,
        listing_start=window["start"], listing_end=window["end"],
        exchange=window["exchange"],
        candidates=tuple(sorted(seen)), notes=tuple(notes),
        xbrl_instances_seen=instances_seen,
    )
