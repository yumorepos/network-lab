"""Guard against accidental private material being tracked on public main.

This is a targeted current-tree check, NOT a full secret/history/privacy audit.
It reports only path, line and category, never secret contents.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".toml", ".json", ".csv", ".txt", ".sh"}
FORBIDDEN_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519"}
FORBIDDEN_SUFFIXES = {".duckdb", ".db", ".sqlite", ".sqlite3", ".pdf", ".docx",
                      ".xlsx", ".xls", ".p12", ".pfx", ".pem", ".key", ".zip"}
EXCEPTIONS = set()

# Assemble known token prefixes so example regex source does not self-match.
TOKEN_PATTERNS = (
    ("github-credential", re.compile("gh" + "p_" + r"[A-Za-z0-9]{30,}")),
    ("github-credential", re.compile("github_" + "pat_" + r"[A-Za-z0-9_]{35,}")),
    ("openai-credential", re.compile("sk-" + r"(?:proj-)?[A-Za-z0-9_-]{24,}")),
    ("aws-credential", re.compile("AK" + "IA" + r"[A-Z0-9]{16}")),
    ("private-key", re.compile("-----BEGIN " + "PRIVATE KEY-----")),
)
PERSONAL_EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@(?:gmail|hotmail|outlook|icloud|yahoo|protonmail)\.(?:com|me)\b")
HOME_PATH = re.compile(r"(?<![A-Za-z0-9_])/" + "Users/" + r"[A-Za-z0-9_.-]+/")


def tracked_files():
    completed = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                               capture_output=True, check=True)
    return sorted((ROOT / p.decode()).resolve()
                  for p in completed.stdout.split(b"\x00") if p)


def test_public_repository_contains_no_obvious_private_material():
    findings = []
    for path in tracked_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel in EXCEPTIONS:
            continue
        if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            findings.append(f"{rel}: private/large file type")
            continue
        if not any(rel == x or rel.startswith(x + "/") for x in
                   ("README.md", "AGENTS.md", "CLAUDE.md", "docs", "scripts",
                    "models", "ingest", "warehouse", "app", "replay", "backtest",
                    "config", "data/reference", "tests", "reports")):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        for line_num, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            hits = {name for name, pattern in TOKEN_PATTERNS if pattern.search(line)}
            if PERSONAL_EMAIL.search(line):
                hits.add("personal-email")
            if HOME_PATH.search(line):
                hits.add("absolute-home-path")
            for category in sorted(hits):
                findings.append(f"{rel}:{line_num}: {category}")
    assert not findings, ("Potential public-tree privacy issue (values redacted):\n" +
                          "\n".join(findings[:100]))
