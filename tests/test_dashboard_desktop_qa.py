"""Display-only desktop QA checks based on the Nov 9 live screenshots.

Guard readability without modifying canonical research artifacts or statuses.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "app" / "streamlit_app.py").read_text()


def test_study_selector_is_short_but_full_research_names_remain():
    for pair in (
        ('"WestJet YYC transborder (flagship)"', '"WestJet · YYC"'),
        ('"Alaska SEA domestic (validation)"', '"Alaska · SEA"'),
        ('"Porter YYZ transborder (portability)"', '"Porter · YYZ"'),
    ):
        assert all(x in SRC for x in pair)
    assert 'format_func=lambda value: SIDEBAR_STUDY_LABELS[value]' in SRC
    assert "sid = STUDIES[study_label]" in SRC


def test_detailed_research_is_accessible_without_wall_of_text():
    assert 'st.expander("Launch backtest: full study tables and named routes")' in SRC
    assert 'st.expander("Complete README, source references and audit history")' in SRC
    assert '("validation.md", "Model validation and transfer-factor evidence")' in SRC
    assert '("reconciliation.md", "Source reconciliation: computed vs published")' in SRC
    assert '"| not recorded |"' in SRC
    assert "Original " in SRC
    assert "https://github.com/yumorepos/network-lab/blob/main/docs/" in SRC
    assert "https://github.com/yumorepos/network-lab/blob/main/data/" in SRC


def test_no_research_model_or_output_mutation():
    assert 'return pd.read_parquet(p) if p.exists() else None' in SRC
    assert 'evidence = scr.loc[scr["metro_name"] == mkt].iloc[0]' in SRC
    assert "to_parquet(" not in SRC
    assert "to_sql(" not in SRC
    assert 'warehouse.duckdb' not in SRC
    assert (ROOT / "docs" / "backtest.md").is_file()
