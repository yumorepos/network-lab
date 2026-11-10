# Publication and privacy review - November 9, 2026

**Scope:** public current `main` working tree only, reviewed after root-folder reorganization. This is **not a complete privacy, security, licensing, branch-history, Git-history, fork or Internet-cache audit**.

## Verified current-tree decisions

| Content | Action | Reason |
|---|---|---|
| `README.md`, `LICENSE`, `requirements.txt`, `Makefile`, `pytest.ini`, `.gitignore` | Keep root | Essential public project and build entry points |
| `AGENTS.md`, `CLAUDE.md` | Keep root, concise | Conventional coding-agent configuration; contain project rules, not personal records |
| `PROGRESS.md` | Temporarily keep root | Existing consistency tests explicitly read it; archive only with a separate path-and-claim migration |
| Prior root plans, July audits and integrity report | Keep publicly under [history](../history/README.md) | Historical research provenance, not active implementation guidance |
| Scope, limitations, replay, reproducibility and source-reconciliation evidence | Keep public under `docs/` | Technical credibility and scientific accountability |
| App, Python pipeline, tests, approved small output data | Keep public | Needed for working Streamlit site and reproducibility |
| `data/warehouse.duckdb`, raw datasets, untracked intermediate warehouses, local audit ZIPs | Keep local/private | Not necessary in the public tree or dashboard deployment |
| Personal résumé, job application, transcript, insurance/health or employer/client records | Keep in private storage, not public Git | Unrelated to research and potentially personally sensitive |
| Credentials, API tokens, SSH keys, environment secrets | Do not commit; revoke if exposed | High-risk authentication material |

## Current-tree evidence

- The original 12 KB agent guide was reduced to an active root rule set; its retired text is archived with a visible historical warning.
- Five historic root plans/audits were relocated to `docs/history/` with current-scope notices.
- The deterministic guard [tests/test_public_privacy_guard.py](../../tests/test_public_privacy_guard.py) checks **tracked current-tree files** for common credential formats, private file extensions, consumer email domains and absolute Mac home paths. It reports only location/category, never the matched value.
- The guard initially found one contributor-local Mac directory path in `docs/FINAL_INDEPENDENT_REVIEW.md`. It was replaced by a redacted description. The following full CI passed **223 tests, 141 expected warehouse-dependent skips, three warnings** on November 9 (Toronto local date). No new private file was created.
- The former public personal career drafts and old portfolio résumé PDF are absent from the latest public branches. This does **not** erase their old committed versions.

## What this audit **does not** certify

- No public Git *history*, tags, branches outside current `main`, merged PR diffs, caches or forks were exhaustively scanned or rewritten. Old removed content may remain accessible. Do **not** use `git filter-repo` or force-push to hide it without a dedicated signed-off remediation plan, immutable artifact backup and redeployment checks.
- A pattern check cannot prove there are no passwords with novel formats, employer-proprietary language, sensitive personal names/addresses, machine-generated derived microdata, or third-party licensing problems.
- A public GitHub repository has **no private folders**. For genuinely confidential source material, use a **separate private repository or personal storage** from the start. Adding to `.gitignore` later does not conceal previously tracked material.
- If a credential was ever committed, **revoke/rotate it first**; then review GitHub's sensitive-data-removal guidance and any active forks/caches. If the user's prior name or personal documents require removal, handle that through a deliberate historical-privacy workflow, not casual file deletion.

## Long-term governance

1. Keep the published app, canonical output files and fixed-gauge scope frozen unless separately approved and regression-tested.
2. Use temporary short-lived feature branches and pull requests for later work. Preserve any **active** external planning PRs; do not delete a branch just to reach a count of one while work is pending.
3. Enable protection on `main` in GitHub repository Rulesets: require PR review/CI and block force-push/deletion. Account administration permissions are required; the connected research integration cannot change these settings.
4. Re-run the public-tree privacy test and curated link tests before any subsequent publication. Separately review Git author metadata and prior public history before claiming historical privacy clearance.
