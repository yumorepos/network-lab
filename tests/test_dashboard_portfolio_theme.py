"""Presentation-only dashboard contract: match the public portfolio design tokens.

These checks do not execute Streamlit or compute route verdicts. Existing
dashboard artifact and source-parity tests remain the authoritative data gates.
"""
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_theme_matches_portfolio_tokens():
    cfg = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text())["theme"]
    expected = {
        "base": "dark",
        "primaryColor": "#3b82f6",
        "backgroundColor": "#0a0a0a",
        "secondaryBackgroundColor": "#141414",
        "textColor": "#ededed",
    }
    for key, value in expected.items():
        assert cfg[key].lower() == value
    css = (ROOT / "app" / "theme.css").read_text()
    for required in ("--nl-accent: #3b82f6", "--nl-bg: #0a0a0a",
                     "--nl-surface: #141414", "--nl-text: #ededed",
                     "family=Inter", "JetBrains+Mono", ".nl-home-link",
                     "@media (max-width: 760px)", ":focus-visible"):
        assert required in css, required
    for outdated in ("#e5a24a", "DM+Sans", "'DM Sans'"):
        assert outdated not in css, outdated


def test_dashboard_stays_read_only_and_keeps_evidence_pages():
    src = (ROOT / "app" / "streamlit_app.py").read_text()
    assert "OUT / name" in src
    assert "pd.read_parquet(p)" in src
    assert '"Route screen", "Market detail"' in src
    assert '"Validation", "Backtest", "About"' in src
    assert 'st.expander("Data sources & verdict evidence")' in src
    assert 'evidence = scr.loc[scr["metro_name"] == mkt].iloc[0]' in src
    assert "https://yumorepos.github.io/network-lab.html" in src
    assert '#3b82f6' in src
    assert "to_parquet(" not in src
    assert "to_sql(" not in src
    assert "warehouse.duckdb" not in src
