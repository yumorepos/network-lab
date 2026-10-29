"""BTS downloads must verify HTTPS certificates; offline regression guard."""
from __future__ import annotations

import ast
from pathlib import Path


def test_transtats_downloads_never_disable_certificate_checks():
    src = Path(__file__).resolve().parents[1] / "ingest" / "transtats.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    http_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"get", "post"}
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "s"
    ]
    assert len(http_calls) == 2  # Protect both the form GET and ZIP POST.
    for call in http_calls:
        verify = [kw.value for kw in call.keywords if kw.arg == "verify"]
        assert len(verify) == 1
        assert isinstance(verify[0], ast.Constant) and verify[0].value is True
