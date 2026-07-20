"""Scripted client for TranStats DL_SelectFields downloads.

TranStats obfuscates query params with a rotate-13 over the 36-character ring
[A-Z0-9]: Table_ID 293 encodes to "FMG". The download form is a plain ASP.NET
webform; we GET the page for its __VIEWSTATE and valid dropdown options, then
POST back the field selection with chkDownloadZip to receive a zipped CSV.
This drives the site's own download mechanism (public-domain data) without a
browser. Posted select values must be valid options or ASP.NET event
validation rejects the request, so options are parsed and checked.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

import requests

from .common import UA, log

RING = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
BASE = "https://www.transtats.bts.gov"

# Table 293: T-100 Segment (All Carriers) — domestic AND international
# segments, every carrier reporting to BTS. 295/297: Form 41 P-1.2 / P-5.2.
# 288/300/304: Master Coordinate, AircraftTypes, Carrier Decode support tables.
T100_SEGMENT_ALL = 293
ALL_FIELDS = "__ALL__"


def enc13(s: str) -> str:
    return "".join(RING[(RING.index(c) + 13) % 36] if c in RING else c
                   for c in s.upper())


def _select_url(table_id: int) -> str:
    # QO_fu146_anzr ("DB short name", encoded) must be present and non-empty
    # for the form to render; its content is display-only.
    return (f"{BASE}/DL_SelectFields.aspx?gnoyr_VQ={enc13(str(table_id))}"
            f"&QO_fu146_anzr=Nrgj14x_Yno")


def _options(page: str, select_name: str) -> list[str]:
    m = re.search(rf'<select[^>]*name="{select_name}".*?</select>', page, re.S)
    return re.findall(r'value="([^"]*)"', m.group(0)) if m else []


def download_table_year(table_id: int, year: int | str, fields, dest: Path,
                        *, geography: str = "All") -> Path:
    """Download one year (or 'All' where offered) of a table as zipped CSV."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        log(f"cached: {dest.name}")
        return dest
    s = requests.Session()
    url = _select_url(table_id)
    r = s.get(url, headers=UA, verify=False, timeout=120)
    r.raise_for_status()
    page = r.text
    if 'id="form1"' not in page:
        raise RuntimeError(f"table {table_id}: download form did not render")
    years = _options(page, "cboYear")
    year = str(year)
    if year not in years:
        raise KeyError(f"table {table_id}: year {year} not in {years[:3]}..."
                       f"{years[-1:]}")
    hidden = dict(re.findall(
        r'<input type="hidden" name="([^"]+)"[^>]*value="([^"]*)"', page))
    all_cols = [c for c in re.findall(
        r'<input[^>]*type="checkbox"[^>]*name="([^"]+)"', page)
        if not c.startswith("chk")]
    cols = all_cols if fields == ALL_FIELDS else fields
    unknown = set(cols) - set(all_cols)
    if unknown:
        raise KeyError(f"table {table_id}: unknown fields {sorted(unknown)}")
    body: dict[str, str] = dict(hidden)
    body.update({
        "cboGeography": geography,
        "cboYear": year,
        "cboPeriod": "All",
        "chkDownloadZip": "on",
        "btnDownload": "Download",
    })
    for c in cols:
        body[c] = "on"
    r2 = s.post(url, data=body, headers={**UA, "Referer": url}, verify=False,
                timeout=900, stream=True)
    r2.raise_for_status()
    tmp = dest.with_suffix(".part")
    with open(tmp, "wb") as f:
        for chunk in r2.iter_content(1 << 20):
            f.write(chunk)
    with open(tmp, "rb") as f:
        head = f.read(2)
    if head != b"PK":
        snippet = open(tmp, "rb").read(300)
        tmp.unlink()
        raise RuntimeError(
            f"table {table_id} year {year}: response not a zip: {snippet!r}")
    tmp.rename(dest)
    log(f"downloaded: {dest.name} ({dest.stat().st_size >> 20} MB)")
    return dest


def data_csv(zip_path: Path, out_dir: Path) -> Path:
    """Extract and return the data CSV (largest; skips Documentation.csv)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        infos = [i for i in z.infolist() if i.filename.lower().endswith(".csv")]
        best = max(infos, key=lambda i: i.file_size)
        z.extract(best, out_dir)
    return out_dir / best.filename
