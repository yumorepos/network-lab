"""Public working tree hygiene without removing historic research evidence.

Career-writing drafts belong in private/local files, not in this public repo.
Historical Git commits may still contain old content; this checks main only.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERSONAL_DRAFTS = (
    "docs/interview_story.md",
    "docs/resume_material.md",
    "docs/linkedin_posts.md",
)


def test_personal_career_drafts_not_in_public_working_tree():
    for rel in PERSONAL_DRAFTS:
        assert not (ROOT / rel).exists(), f"Personal career draft still public: {rel}"


def test_research_docs_are_independent_of_personal_career_drafts():
    # This must remain a source-data/evidence contract, not a personal-CV test.
    checks = (ROOT / "tests" / "test_consistency.py").read_text()
    index = (ROOT / "docs" / "README.md").read_text()
    for rel in PERSONAL_DRAFTS:
        assert rel not in checks, rel
        assert f"]({Path(rel).name})" not in index, rel
    for rel in ("docs/FINAL_SCOPE_CONTRACT.md", "docs/LIMITATIONS.md",
                "docs/STAGE_2R0_RESOLUTION.md", "docs/validation.md",
                "docs/reconciliation.md", "docs/backtest.md"):
        assert (ROOT / rel).is_file(), rel


def test_public_introduction_exposes_scope_and_sources():
    readme = (ROOT / "README.md").read_text()
    for term in ("fixed-gauge", "demand-only", "limitations",
                 "Streamlit", "LAUNCH", "MONITOR", "PASS"):
        assert term.lower() in readme.lower(), term
