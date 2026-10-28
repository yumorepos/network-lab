"""Research-only DB1C compatibility guards for one U.S. hub-month fixture.

This module does not ingest DB1C into the production DuckDB warehouse.
Input frames use official TranStats field names. It intentionally does NOT
expand the 40% sample, assign marketing brands to operating certificates,
or convert DB1C gross fares into historical DB1B market fares.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile

import pandas as pd
import pyarrow.parquet as pq
import requests

# These column names are the published DB1C TranStats field names, not guesses.
# "MktAmout" is spelled as printed in the BTS DB1CMarket field list.
REQUIRED = {
    "ticket": {"ItinID", "RpYear", "RpMonth", "IssuingCarrier",
               "Passengers", "RoundTrip", "TotalAmount", "TaxAmount"},
    "market": {"ItinID", "MktID", "RpYear", "RpMonth",
               "OriginCityMarketID", "DestCityMarketID",
               "Passengers", "MktAmout", "MktTax", "MktCoupons"},
    "coupon": {"ItinID", "MktID", "SeqNum", "RpYear", "RpMonth",
               "OriginAirportID", "DestAirportID", "Viapoint"},
    "segment": {"ItinID", "MktID", "SeqNum", "RpYear", "RpMonth",
                "SegmentID"},
}
MONTH = (2025, 7)
# Public ZIP links published on BTS's Ticket / Market / Coupon / Segment pages.
# These point to a specific September 2026 release of July 2025 data.
ZIP_BASE = (
    "https://ostrapeispubdownloadprod.blob.core.windows.net/"
    "ostrapeis-pub-download-prod/ond40/products/db1c_public/"
)
ZIP_URLS = {
    table: ZIP_BASE + f"DB1C.{table.upper()}.202507.18SEP2026.zip"
    for table in REQUIRED
}


def _required(name: str, frame: pd.DataFrame) -> None:
    missing = REQUIRED[name] - set(frame.columns)
    if missing:
        raise ValueError(f"{name}: missing fields {sorted(missing)}")
    if frame.empty:
        raise ValueError(f"{name}: empty fixture")
    if frame[["RpYear", "RpMonth"]].isna().any().any():
        raise ValueError(f"{name}: missing reporting vintage")
    if not ((frame["RpYear"].astype(int) == MONTH[0]) &
            (frame["RpMonth"].astype(int) == MONTH[1])).all():
        raise ValueError(f"{name}: mixed reporting months")


def _unique(name: str, frame: pd.DataFrame, keys: list[str]) -> None:
    if frame[keys].isna().any().any():
        raise ValueError(f"{name}: missing identity key")
    if frame.duplicated(keys).any():
        raise ValueError(f"{name}: duplicate key {keys}")


def validate_fixture(
    ticket: pd.DataFrame, market: pd.DataFrame,
    coupon: pd.DataFrame, segment: pd.DataFrame,
) -> dict[str, int | str | bool]:
    """Verify keys and join cardinality without inflating passenger totals."""
    for name, frame in (
        ("ticket", ticket), ("market", market),
        ("coupon", coupon), ("segment", segment)
    ):
        _required(name, frame)

    _unique("ticket", ticket, ["ItinID"])
    _unique("market", market, ["ItinID", "MktID"])
    _unique("coupon", coupon, ["ItinID", "SeqNum"])
    # SegmentID is not assumed globally unique; one coupon may produce
    # multiple rows. The source-specific segment grain needs more validation.

    m = market.merge(ticket[["ItinID"]], on="ItinID", how="left",
                     validate="many_to_one", indicator=True)
    if not m["_merge"].eq("both").all():
        raise ValueError("market: orphan itinerary")
    c = coupon.merge(market[["ItinID", "MktID"]], on=["ItinID", "MktID"],
                     how="left", validate="many_to_one", indicator=True)
    if not c["_merge"].eq("both").all():
        raise ValueError("coupon: orphan market")
    s = segment.merge(coupon[["ItinID", "MktID", "SeqNum", "Viapoint"]],
                      on=["ItinID", "MktID", "SeqNum"], how="left",
                      validate="many_to_one", indicator=True)
    if not s["_merge"].eq("both").all():
        raise ValueError("segment: orphan coupon")

    # BTS says Segment contains only expansions of coupons WITH via points.
    # The non-via coupons are absent from that table and must be added when
    # constructing a full set of leg records, not O&D passenger counts.
    via = s["Viapoint"].fillna("").astype(str).str.strip().ne("")
    if not via.all():
        raise ValueError("segment: coupon without via point")

    # A coupon with a via point must have at least one Segment row. This
    # fixture contract detects silent missing data without guessing count.
    have_segments = set(zip(s["ItinID"], s["MktID"], s["SeqNum"]))
    required_segments = set(zip(
        coupon.loc[coupon["Viapoint"].fillna("").astype(str).str.strip().ne(""), "ItinID"],
        coupon.loc[coupon["Viapoint"].fillna("").astype(str).str.strip().ne(""), "MktID"],
        coupon.loc[coupon["Viapoint"].fillna("").astype(str).str.strip().ne(""), "SeqNum"]
    ))
    if not required_segments.issubset(have_segments):
        raise ValueError("coupon: via point missing segment expansion")

    p = pd.to_numeric(market["Passengers"], errors="raise")
    tp = pd.to_numeric(ticket["Passengers"], errors="raise")
    if (p < 0).any() or (tp < 0).any():
        raise ValueError("negative passengers")
    # This is a synthetic fixture; a market row counts each direction.
    # Do not sum market passengers across a joined coupon or segment table.
    direct_coupon_count = int(
        coupon["Viapoint"].fillna("").astype(str).str.strip().eq("").sum())
    return {
        "reporting_period": "2025-07",
        "ticket_rows": len(ticket),
        "market_rows": len(market),
        "coupon_rows": len(coupon),
        "via_point_segment_rows": len(segment),
        "direct_coupon_rows": direct_coupon_count,
        "materialized_leg_rows": direct_coupon_count + len(segment),
        "ticket_passengers_sample": int(tp.sum()),
        "market_passenger_records_sample": int(p.sum()),
        "sample_expansion_applied": False,
        "market_fare_equivalent_to_db1b": False,
    }


def probe_public_zip_headers(timeout: int = 35) -> dict:
    """Metadata-only HEAD requests, no large DB1C archive download."""
    out = {}
    for table, url in ZIP_URLS.items():
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        out[table] = {
            "url": url,
            "status": r.status_code,
            "content_length_bytes": r.headers.get("Content-Length"),
            "last_modified": r.headers.get("Last-Modified"),
            "content_type": r.headers.get("Content-Type"),
        }
    return out


def inspect_public_segment_sample(
    *, url: str | None = None, max_zip_bytes: int = 16_000_000,
    sample_rows: int = 256,
) -> dict:
    """Inspect actual small Segment ZIP without exporting individual tickets.

    The safety limit applies to compressed bytes. Ticket/Market/Coupon have
    >1 GB ZIP files and must NOT be pulled by this inspection command.
    """
    url = url or ZIP_URLS["segment"]
    headers = requests.head(url, timeout=35, allow_redirects=True)
    headers.raise_for_status()
    expected = int(headers.headers.get("Content-Length", 0))
    if not expected or expected > max_zip_bytes:
        raise ValueError(f"segment ZIP exceeds size cap: {expected} bytes")
    chunks = []
    total = 0
    with requests.get(url, timeout=90, stream=True) as response:
        response.raise_for_status()
        for part in response.iter_content(chunk_size=262144):
            if not part:
                continue
            total += len(part)
            if total > max_zip_bytes:
                raise ValueError("segment ZIP streamed beyond size cap")
            chunks.append(part)
    payload = b"".join(chunks)
    if total != expected:
        raise ValueError(f"segment ZIP truncated: expected {expected}, got {total}")
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        parquet_members = [item for item in z.infolist()
                           if item.filename.lower().endswith(".parquet")]
        if parquet_members:
            member = max(parquet_members, key=lambda i: i.file_size)
            with z.open(member) as raw:
                file = pq.ParquetFile(io.BytesIO(raw.read()))
            columns = list(file.schema_arrow.names)
            row_count = int(file.metadata.num_rows)
            batch = next(file.iter_batches(batch_size=sample_rows), None)
            sample = batch.to_pandas() if batch is not None else pd.DataFrame(
                columns=columns)
        else:
            # Small synthetic archives in offline tests can contain CSV.
            # Actual BTS ZIPs have nested ASCII / CSV ZIPs and Parquet.
            csv_members = [item for item in z.infolist()
                           if item.filename.lower().endswith(".csv")
                           and not item.filename.lower().endswith("documentation.csv")]
            if not csv_members:
                raise ValueError("No readable Parquet/CSV in Segment archive; members: "
                                 + repr(z.namelist()[:20]))
            member = max(csv_members, key=lambda i: i.file_size)
            with z.open(member) as raw:
                sample = pd.read_csv(raw, nrows=sample_rows, dtype=str)
            columns = list(sample.columns)
            row_count = None
    missing = REQUIRED["segment"] - set(columns)
    return {
        "zip_bytes": total,
        "zip_sha256": hashlib.sha256(payload).hexdigest(),
        "selected_member": member.filename,
        "archive_members": [i.filename for i in zipfile.ZipFile(io.BytesIO(payload)).infolist()],
        "source_row_count": row_count,
        "sample_row_count": len(sample),
        "columns": columns,
        "missing_expected_fields": sorted(missing),
        "sample_periods": sorted({
            str(y) + "-" + str(m) for y, m in zip(
                sample.get("RpYear", pd.Series(dtype=str)),
                sample.get("RpMonth", pd.Series(dtype=str)))
        }),
        "segment_row_values_exported": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-public-headers", action="store_true")
    parser.add_argument("--inspect-small-segment", action="store_true")
    args = parser.parse_args()
    if args.probe_public_headers:
        print(json.dumps(probe_public_zip_headers(), indent=2))
    elif args.inspect_small_segment:
        print(json.dumps(inspect_public_segment_sample(), indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
