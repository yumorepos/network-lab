"""Bounded actual DB1C Segment ZIP inspection with in-memory mock archives."""
from __future__ import annotations

import io
import zipfile

import pytest

from scripts import stage_c_db1c_compat as spike


class Response:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.headers = {"Content-Length": str(len(payload))}
    def raise_for_status(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def iter_content(self, chunk_size):
        yield self.payload


def small_archive(header: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("DB1C.SEGMENT.synthetic.csv",
                   header + "\nA,A1,1,2025,7,1\n")
    return buffer.getvalue()


def test_small_segment_probe_metadata_no_ticket_rows_exported(monkeypatch):
    data = small_archive("ItinID,MktID,SeqNum,RpYear,RpMonth,SegmentID")
    monkeypatch.setattr(spike.requests, "head", lambda *_a, **_kw: Response(data))
    monkeypatch.setattr(spike.requests, "get", lambda *_a, **_kw: Response(data))
    out = spike.inspect_public_segment_sample(url="https://example.invalid/test.zip")
    assert out["zip_bytes"] == len(data)
    assert out["sample_row_count"] == 1
    assert out["missing_expected_fields"] == []
    assert out["segment_row_values_exported"] is False
    assert out["sample_periods"] == ["2025-7"]


def test_negative_control_compressed_archive_exceeds_cap(monkeypatch):
    data = small_archive("ItinID,MktID,SeqNum,RpYear,RpMonth,SegmentID")
    monkeypatch.setattr(spike.requests, "head", lambda *_a, **_kw: Response(data))
    def should_not_get(*_args, **_kwargs):
        raise AssertionError("Should not download above size cap")
    monkeypatch.setattr(spike.requests, "get", should_not_get)
    with pytest.raises(ValueError, match="exceeds size cap"):
        spike.inspect_public_segment_sample(max_zip_bytes=1)


def test_negative_control_truncated_source_zip(monkeypatch):
    data = small_archive("ItinID,MktID,SeqNum,RpYear,RpMonth,SegmentID")
    class LongerHead(Response):
        def __init__(self, data):
            super().__init__(data)
            self.headers["Content-Length"] = str(len(data) + 10)
    monkeypatch.setattr(spike.requests, "head", lambda *_a, **_kw: LongerHead(data))
    monkeypatch.setattr(spike.requests, "get", lambda *_a, **_kw: Response(data))
    with pytest.raises(ValueError, match="segment ZIP truncated"):
        spike.inspect_public_segment_sample()


def test_negative_control_schema_missing_field_is_reported(monkeypatch):
    data = small_archive("ItinID,MktID,SeqNum,RpYear,RpMonth,WrongID")
    monkeypatch.setattr(spike.requests, "head", lambda *_a, **_kw: Response(data))
    monkeypatch.setattr(spike.requests, "get", lambda *_a, **_kw: Response(data))
    out = spike.inspect_public_segment_sample()
    assert "SegmentID" in out["missing_expected_fields"]
