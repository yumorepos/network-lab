"""Verify public documentation links and research-first release claims.

Offline and deterministic: checks only version-controlled local paths.
External websites, historical Git commits and the actual Streamlit UI are
outside this test's scope.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = (
    "README.md",
    "docs/README.md",
    "docs/REPOSITORY_MAINTENANCE_POLICY.md",
    "docs/FINAL_SCOPE_CONTRACT.md",
    "docs/deploy.md",
)
LINK_PATTERN = re.compile(r"!?(?:\[[^\]\n]*\])\(([^)\s]+)(?:\s+[^)]*)?\)")


def test_curated_public_docs_have_no_broken_local_links():
    broken = []
    for rel in DOCS:
        page = ROOT / rel
        assert page.is_file(), rel
        text = page.read_text(encoding="utf-8")
        for m in LINK_PATTERN.finditer(text):
            href = m.group(1).strip("<>")
            url = urlsplit(href)
            if url.scheme or url.netloc or href.startswith(("#", "mailto:")):
                continue
            target = unquote(url.path)
            if not target:
                continue
            resolved = (page.parent / target).resolve()
            if not resolved.is_relative_to(ROOT.resolve()) or not resolved.exists():
                broken.append(f"{rel}: {href}")
    assert not broken, "Broken public documentation links:\n" + "\n".join(broken)


def test_recruiter_readme_keeps_scientific_claims_bounded():
    text = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for phrase in (
        "fixed-gauge",
        "demand-only",
        "source",
        "limitations",
        "no detectable",
        "200",
        "463",
    ):
        assert phrase in text, phrase
    for unsupported in (
        "no single open-source project combines",
        "validated end to end on a us hub",
    ):
        assert unsupported not in text, unsupported


def test_no_old_personal_documents_in_curated_navigation():
    for rel in ("README.md", "docs/README.md"):
        text = (ROOT / rel).read_text(encoding="utf-8").lower()
        for old in ("docs/interview_story.md", "docs/resume_material.md",
                    "docs/linkedin_posts.md"):
            assert old not in text, f"{rel} still links personal draft {old}"
