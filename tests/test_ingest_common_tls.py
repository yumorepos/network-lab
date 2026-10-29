"""Shared ingest download must enforce verified HTTPS and propagate TLS failures."""
from pathlib import Path

import pytest
import requests

from ingest import common


def test_shared_download_requires_certificate_verification(monkeypatch, tmp_path):
    captured = []

    class Response:
        status_code = 200

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size=1 << 20):
            yield b"source-bytes"

    def fake_get(url, **kwargs):
        captured.append({"url": url, **kwargs})
        return Response()

    monkeypatch.setattr(common.requests, "get", fake_get)
    target = tmp_path / "download.bin"
    assert common.download_file("https://example.org/source.zip", target)
    assert target.read_bytes() == b"source-bytes"
    assert captured[0]["verify"] is True
    assert captured[0]["timeout"] == 600


def test_invalid_certificate_fails_closed(monkeypatch, tmp_path):
    def tls_failure(*args, **kwargs):
        assert kwargs["verify"] is True
        raise requests.exceptions.SSLError("certificate verification failed")

    monkeypatch.setattr(common.requests, "get", tls_failure)
    target = tmp_path / "untrusted.zip"
    with pytest.raises(requests.exceptions.SSLError, match="certificate"):
        common.download_file("https://untrusted.example/source.zip",
                             target, retries=1)
    assert not target.exists()
    assert not target.with_suffix(".zip.part").exists()


def test_no_process_wide_suppression_of_tls_warnings():
    text = (Path(__file__).resolve().parents[1] /
            "ingest/common.py").read_text(encoding="utf-8")
    assert "urllib3.disable_warnings()" not in text
    assert "verify=False" not in text
