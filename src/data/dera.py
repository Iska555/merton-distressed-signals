"""
SEC DERA Financial Statement Data Sets: point-in-time filer universe and bulk
fundamentals.

Why this exists rather than more per-CIK API calls:

**Control survivorship.** A control pool drawn from EDGAR's company_tickers.json
would contain only filers still registered TODAY. A control matched to a 2013
treatment firm would then have had to survive thirteen years, making the control
group systematically healthier than the population and inflating AUC. The bias
runs opposite to the treatment-side bias and would be invisible in the output.

`sub.txt` in each quarterly data set lists every filer that filed that quarter --
including firms later acquired, delisted, or bankrupted. That is a genuine
point-in-time universe.

**Cost.** Each quarter is one 114MB download covering ~5,600 filers. The
per-CIK companyfacts route costs one multi-megabyte request per firm; for a
few thousand controls that is thousands of requests and gigabytes of transfer.

The ZIPs are extracted to compact parquet and deleted, since only a handful of
balance-sheet tags are ever needed.
"""
from __future__ import annotations

import io
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

from ..config import DATA_RAW, SEC_USER_AGENT

_CACHE = DATA_RAW / "dera"
_CACHE.mkdir(parents=True, exist_ok=True)

_BASE = "https://www.sec.gov/files/dera/data/financial-statement-data-sets"

# Balance-sheet tags the study needs. Kept deliberately small: num.txt holds
# millions of rows per quarter and all but these are discarded on extract.
BALANCE_SHEET_TAGS = {
    "Assets",
    "Liabilities",
    "LiabilitiesAndStockholdersEquity",
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    "DebtCurrent",
    "ShortTermBorrowings",
    "LongTermDebtCurrent",
    "LongTermDebtNoncurrent",
    "LongTermDebt",
    "CommonStockSharesOutstanding",
}


def _paths(year: int, quarter: int) -> tuple[Path, Path]:
    return (_CACHE / f"{year}q{quarter}_sub.parquet",
            _CACHE / f"{year}q{quarter}_num.parquet")


def available(year: int, quarter: int) -> bool:
    sub_path, num_path = _paths(year, quarter)
    return sub_path.exists() and num_path.exists()


def download_quarter(year: int, quarter: int, *, refresh: bool = False) -> bool:
    """
    Fetch one quarterly data set, extract the needed slice, discard the ZIP.

    Returns False if the quarter is not published (future or pre-2009).
    """
    sub_path, num_path = _paths(year, quarter)
    if sub_path.exists() and num_path.exists() and not refresh:
        return True

    url = f"{_BASE}/{year}q{quarter}.zip"
    request = urllib.request.Request(url, headers={"User-Agent": SEC_USER_AGENT})
    tmp = Path(tempfile.gettempdir()) / f"dera_{year}q{quarter}.zip"
    try:
        with urllib.request.urlopen(request, timeout=300) as response, \
                open(tmp, "wb") as handle:
            shutil.copyfileobj(response, handle)
    except Exception:  # noqa: BLE001 - unpublished quarters 404, which is normal
        tmp.unlink(missing_ok=True)
        return False

    try:
        with zipfile.ZipFile(tmp) as archive:
            with archive.open("sub.txt") as handle:
                sub = pd.read_csv(handle, sep="\t", dtype=str, low_memory=False)
            sub = sub[["adsh", "cik", "name", "sic", "form", "period", "fye",
                       "filed", "countryba", "fp"]].copy()
            sub = sub[sub["form"].isin(["10-K", "10-Q", "10-K/A", "10-Q/A"])]
            sub.to_parquet(sub_path, index=False)

            with archive.open("num.txt") as handle:
                keep = []
                for chunk in pd.read_csv(handle, sep="\t", dtype=str,
                                         low_memory=False, chunksize=500_000):
                    # qtrs == "0" selects instantaneous balances (point-in-time
                    # stocks) rather than flows over a period.
                    sliced = chunk[
                        chunk["tag"].isin(BALANCE_SHEET_TAGS)
                        & (chunk["qtrs"] == "0")
                        & chunk["segments"].isna()
                        & chunk["coreg"].isna()
                    ]
                    if not sliced.empty:
                        keep.append(sliced[["adsh", "tag", "ddate", "uom", "value"]])
                num = (pd.concat(keep, ignore_index=True) if keep
                       else pd.DataFrame(columns=["adsh", "tag", "ddate", "uom", "value"]))
                num.to_parquet(num_path, index=False)
    finally:
        tmp.unlink(missing_ok=True)
    return True


def filer_universe(year: int, quarter: int) -> pd.DataFrame:
    """
    Every 10-K/10-Q filer that quarter: a point-in-time universe.

    Includes firms later acquired, delisted or bankrupted, which is exactly
    what an unbiased control pool requires.
    """
    sub_path, _ = _paths(year, quarter)
    if not sub_path.exists():
        return pd.DataFrame()
    frame = pd.read_parquet(sub_path)
    frame["cik"] = frame["cik"].astype(str).str.zfill(10)
    frame["filed"] = pd.to_datetime(frame["filed"], format="%Y%m%d", errors="coerce")
    frame["period"] = pd.to_datetime(frame["period"], format="%Y%m%d", errors="coerce")
    return frame


def fundamentals(year: int, quarter: int) -> pd.DataFrame:
    """
    Balance-sheet facts for every filer that quarter, wide by tag.

    Columns: cik, name, sic, form, period, filed, ddate, plus one per tag.
    """
    sub_path, num_path = _paths(year, quarter)
    if not (sub_path.exists() and num_path.exists()):
        return pd.DataFrame()

    sub = filer_universe(year, quarter)
    num = pd.read_parquet(num_path)
    if num.empty or sub.empty:
        return pd.DataFrame()

    num = num[num["uom"].isin(["USD", "shares"])].copy()
    num["value"] = pd.to_numeric(num["value"], errors="coerce")
    num["ddate"] = pd.to_datetime(num["ddate"], format="%Y%m%d", errors="coerce")
    num = num.dropna(subset=["value", "ddate"])

    # Keep the balance date matching the filing's reporting period; a filing
    # also restates prior periods, and mixing them would blur the panel.
    merged = num.merge(sub[["adsh", "cik", "name", "sic", "form", "period", "filed"]],
                       on="adsh", how="inner")
    merged = merged[merged["ddate"] == merged["period"]]
    if merged.empty:
        return pd.DataFrame()

    wide = merged.pivot_table(
        index=["cik", "name", "sic", "form", "period", "filed"],
        columns="tag", values="value", aggfunc="first",
    ).reset_index()
    wide.columns.name = None
    return wide


def ensure_quarters(start_year: int, end_year: int, *, verbose: bool = True) -> list[tuple[int, int]]:
    """Download every quarter in a range. Returns those actually available."""
    got = []
    for year in range(start_year, end_year + 1):
        for quarter in (1, 2, 3, 4):
            if available(year, quarter):
                got.append((year, quarter))
                continue
            if download_quarter(year, quarter):
                got.append((year, quarter))
                if verbose:
                    print(f"  fetched {year}Q{quarter}", flush=True)
            elif verbose:
                print(f"  {year}Q{quarter} unavailable", flush=True)
    return got


def derive_barriers(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the same barrier conventions as edgar.debt_history to a bulk frame.

    Kept consistent with the per-CIK path deliberately: two implementations of
    the debt waterfall would drift, and the drift would be invisible.
    """
    if frame.empty:
        return frame
    out = frame.copy()
    for tag in BALANCE_SHEET_TAGS:
        if tag not in out.columns:
            out[tag] = pd.NA
        out[tag] = pd.to_numeric(out[tag], errors="coerce")

    short = out["DebtCurrent"].where(
        out["DebtCurrent"].notna(),
        out["ShortTermBorrowings"].fillna(0) + out["LongTermDebtCurrent"].fillna(0),
    )
    short = short.where(
        out["DebtCurrent"].notna()
        | out["ShortTermBorrowings"].notna()
        | out["LongTermDebtCurrent"].notna()
    )

    long = out["LongTermDebtNoncurrent"].where(
        out["LongTermDebtNoncurrent"].notna(),
        (out["LongTermDebt"] - out["LongTermDebtCurrent"].fillna(0)).clip(lower=0),
    )

    equity = out[
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"
    ].where(
        out["StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"].notna(),
        out["StockholdersEquity"],
    )
    assets = out["Assets"].where(out["Assets"].notna(),
                                 out["LiabilitiesAndStockholdersEquity"])
    liabilities = out["Liabilities"].where(out["Liabilities"].notna(), assets - equity)

    out["short_term_debt"] = short
    out["long_term_debt"] = long
    out["total_debt"] = short.fillna(0) + long.fillna(0)
    out.loc[short.isna() & long.isna(), "total_debt"] = pd.NA
    out["kmv_barrier"] = short.fillna(0) + 0.5 * long.fillna(0)
    out.loc[short.isna() & long.isna(), "kmv_barrier"] = pd.NA
    # Shell and pre-revenue filers report zero or missing assets. Dividing by
    # them yields inf, which then poisons any decile boundary computed from the
    # column (the first run produced leverage max=inf, mean=inf).
    assets = assets.where(assets > 0)
    out["total_assets"] = assets
    out["total_liabilities"] = liabilities
    out["leverage"] = (liabilities / assets).replace([float("inf"), float("-inf")], pd.NA)
    return out
