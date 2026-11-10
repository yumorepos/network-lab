# Network Lab — public repository maintenance policy

Reviewed 2026-11-09. Repository: [yumorepos/network-lab](https://github.com/yumorepos/network-lab). This is a **public research portfolio artifact**, not a private workspace or an actively supported airline dispatch product.

## What stays in this public repository

| Group | Keep public? | Purpose / caveat |
|---|---|---|
| `app/`, `.streamlit/` | **Yes** | Live dashboard code and theme. Reads committed outputs without warehouse access. |
| `models/`, `ingest/`, `warehouse/` | **Yes** | Source-to-decision pipeline, including correctable implementation details. |
| `config/` | **Yes** | Published assumptions and three study definitions; needed for traceability. |
| `backtest/`, `replay/` | **Yes** | Validation, point-in-time protocol, bounded negative finding. |
| `tests/`, `.github/workflows/ci.yml` | **Yes** | Reproducibility contracts; moving data or docs must preserve test results. |
| `data/reference/` | **Yes** | Non-sensitive source-referenced airline research registries and mapping reference, with provenance notes. |
| `data/parquet/outputs/` (tracked only) | **Yes, temporarily essential** | Small canonical precomputed Parquet/CSV/YAML outputs. **Streamlit deployment reads these files directly.** Do not untrack or rename without replacing deployment and updating parity gates. |
| `reports/` | **Yes** | Generated research summaries. Never hand-edit generated reports. |
| `docs/FINAL_SCOPE_CONTRACT.md`, `docs/LIMITATIONS.md`, `docs/PORTFOLIO_NARRATIVE.md`, `docs/STAGE_2R0_RESOLUTION.md`, `docs/STAGE_2R_DECISION.md` | **Yes, front-and-center** | The boundaries and negative finding are more important than a claimed prediction win. |
| `docs/validation.md`, `docs/reconciliation.md`, `docs/backtest.md`, `docs/deploy.md` | **Yes** | Reproducible current research evidence and deployment instructions. |
| `scripts/` and research GitHub workflows | **Keep for now** | Historical source-vintage and audit tools. Reorganize or disable old network-dependent research jobs only with full dependency checks. |
| `experiments/disruption_recovery/` | **Keep until isolated** | An independent *synthetic* MILP experiment already exists; migrate to its own repository with its tests and provenance if a second portfolio project is pursued. |
| `AGENTS.md`, `CLAUDE.md`, `PROGRESS.md` and root audit/plan files | **Keep until tested migration** | Some are hardcoded into tests/agent workflows. Their historical status must be clearly labeled rather than silently rewritten. |

## Content better kept outside the public working tree (conditional)

- **Private Mac-only:** `data/warehouse.duckdb`, `data/raw/`, raw/lookup `data/parquet/` caches not explicitly tracked, audit ZIP archives, account credentials, employer records, and any personal/transcript material. These are not deployed.
- **Career-writing drafts (retired from `main`):** former interview, résumé-bullet, and social-post preparation files have been removed from the current public working tree. Their scientific assertions are now tested against actual research documents instead of personal writing. Public Git history and cached URLs may still expose older revisions; removing files is **not a privacy scrub**. Keep new personal drafts in private storage.
- **Old screenshot assets:** `docs/img/dashboard_route_screen.png` and `docs/img/dashboard_scenario_grid.png` show obsolete pre-final model/UI claims. They are already excluded from current page embeds. Remove only once any surviving reference is updated and the tests pass.
- **Past planning and agent handoffs:** `PLAN.md`, `PHASE_5_6_PLAN.md`, `AUDIT_2026-07-27*.md`, and historical research docs. Preserve provenance in a `docs/history/` index during a controlled link-and-test migration, not a mass rename.

### Important privacy disclaimer

**GitHub does not offer private folders inside a public repository.** A hidden-looking path or `.gitignore` does not conceal a committed file. Moving/deleting an existing file leaves reachable copies in commit history, PRs, forks, or caches. A real sensitive-data exposure requires identifying affected commits, revoking credentials first, then considering history rewriting and GitHub's sensitive-data-removal process; this has consequences for clones, tags, deployed artifacts and collaborators. The initial targeted scan of root docs, career-writing materials, reference CSVs and key setup docs found **no obvious credential tokens**, but that is **not a full Git-history or secret-scanning certification**.

## Proposed navigable structure (keep live imports stable)

```text
network-lab/
  README.md                   # recruiter overview, links, installation, honest verdict
  app/                        # live read-only Streamlit presentation
  .streamlit/                 # presentation tokens
  config/                     # assumptions + 3 airline studies
  ingest/ warehouse/ models/  # source/model pipeline
  replay/ backtest/ reports/  # historical evidence and generated artifacts
  data/
    reference/                # published vetted reference tables
    parquet/outputs/          # only tracked small app dependencies
  tests/                      # correctness, evidence and publication contracts
  scripts/                    # audited research CLI (group later)
  docs/
    README.md                 # curated reader navigation
    maintenance/              # review, branch retirement, privacy policy
    history/                  # OPTIONAL future move, only after tests/link QA
  experiments/                # temporary synthetic MILP, independent of main engine
```

## Scalable maintenance roadmap

1. **Now:** retire stale remote branches after writing a SHA manifest and closing unresolved PRs without merging them. Keep **only `main`** as a remote branch; preserve the existing tag as release history. Protect `main` in GitHub Settings → Branches/Rulesets; require tests before changes.
2. **Now:** keep public source/results stable; make documentation discoverable and mark historical plans as archived. Retire obsolete screenshots with careful reference updates.
3. **Next:** separate optional research workflows from required offline CI and add deterministic fixture-based tests. Prefer a dependency/lockfile strategy after pinning a tested Python version and checking packaging constraints.
4. **Completed:** decouple personal career drafts from research consistency tests and remove them from the active public tree. **Later:** move old research notes under `docs/history/`, privatize optional career-writing drafts, and refactor `scripts/` into focused packages **only after** a file-dependency audit and passing tests. Avoid a sweeping `src/` rewrite.
5. **Separate project:** copy the existing synthetic disruption recovery optimizer into a fresh repository and verify its regression test, baseline and any extended benchmark independently before removing it here.
6. **Stop criterion:** the public Streamlit app, 200 frozen screenings, 463 replay decisions and source/baseline honesty stay unchanged. Any meaningful identity/source correction needs a separate isolated candidate data warehouse and counterfactual.

## Safe branch retirement

See [original remote-branch head manifest](maintenance/BRANCH_RETIREMENT_2026_11_09.md). The two open research/unsafe PRs are not to be merged to resolve the branch count.

### Repository metadata recommendations

- Current GitHub repository description says **"validated end-to-end"**. Replace it in GitHub Settings with **"Open-data fixed-gauge airline route screening, audited source assumptions, historical replay, and a bounded evidence-first Streamlit dashboard."** This avoids implying demonstrated predictive superiority.
- `main` is not protected as of the inventory. Enable protection and required CI *after* completing the requested one-time housekeeping.
- Keep the MIT software LICENSE; verify the separately licensed StatCan/OurAirports/public-source attribution before redistributing raw upstream datasets.
