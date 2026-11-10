# Remote branch retirement manifest — 2026-11-09

This document records the original remote branch tips **before** the owner's requested one-main-branch cleanup. The repository's primary source of truth is `main`. The exact branch commits are provided for auditability, not as a promise that commits remain indefinitely available after branch deletion. The user requested deletion of every non-`main` remote branch.

**Do not change:** the original 5.19 GB Mac DuckDB, source cache, frozen 200 screen results or 463 replay decision history.

**Critical unmerged work:** [PR #28](https://github.com/yumorepos/network-lab/pull/28) contains an unsafe airport-label change and must NOT be merged as part of cleanup. [PR #35](https://github.com/yumorepos/network-lab/pull/35) contains read-only source-geography research tools that were validated but never accepted into the application. Both PR discussions and the measured findings are referenced in [docs/NETWORK_LAB_AUDIT_HANDOFF_2026_11_09.md](../NETWORK_LAB_AUDIT_HANDOFF_2026_11_09.md) and [issue #14](https://github.com/yumorepos/network-lab/issues/14). If these become necessary again, review the PR diff and historic SHA, do not blindly apply either branch.

**Before cleanup:** 35 remote branches (one `main` and 34 non-main). `main` starting SHA `4f7fca40700b1674f56ffda5db3d0d400f4d5def`.

| Branch to retire | Exact 40-character head SHA | Disposition |
|---|---|---|
| `audit/airport-impact-db1c-stop-portfolio-2026-10-28` | `71a8cde580890ee1d225af0f92acd5e7fc96542c` | Retired historical branch; inspect SHA if needed |
| `audit/airport-label-consistency-20261029` | `5d0a1aa3e4e779f78c87d932edbde6f9681f18af` | Retired historical branch; inspect SHA if needed |
| `audit/carrier-vintage-source-correction-2026-10-28` | `e3e16f38094c8f5a964036492c0e21cfa7e70d48` | Retired historical branch; inspect SHA if needed |
| `audit/economics-sanity-2026-10-28` | `d88eacd6689b9e112d653d996aa04cc5fe1eff4a` | Retired historical branch; inspect SHA if needed |
| `audit/hub-cbsa-source-exposure-20261109` | `2edd2c3bb3e6ea6dbff8c4858f5e06f6991b64b6` | [PR #35: research-only, do NOT merge](https://github.com/yumorepos/network-lab/pull/35) |
| `audit/live-artifact-parity-source-coverage-2026-10-28` | `4aba060f320447097e4bff2dd002d8c2f114d6e0` | Retired historical branch; inspect SHA if needed |
| `audit/local-warehouse-country-preflight-20261029` | `d19050fa928bc80480f7d967495867f87fb20b84` | Retired historical branch; inspect SHA if needed |
| `audit/mac-airport-label-counterfactual-20261029` | `c8e0a5a44c9c7f681b8f586314eaa159ba979d88` | Retired historical branch; inspect SHA if needed |
| `audit/mac-country-conflict-fact-exposure-20261029` | `2edcbcc9957ab4204fb567397f133cc0e6201c21` | Retired historical branch; inspect SHA if needed |
| `audit/negative-controls-and-doc-conventions-2026-10-28` | `339283a760f6687d90f8fb427c9863938f99bde2` | Retired historical branch; inspect SHA if needed |
| `audit/preserved-mac-warehouse-readonly-2026-10-28` | `155bb9055da5fedc3311cab39b37dc6c0b9a6d6b` | Retired historical branch; inspect SHA if needed |
| `claude/network-lab-finalization` | `5a97bdcc71f2b7d600e30cb8d4d7fb6b39a488ed` | Retired historical branch; inspect SHA if needed |
| `design/dark-dashboard-preview-20261028` | `a786c79ed4e3bcf099f96cf97d5a87ad983c6687` | Retired historical branch; inspect SHA if needed |
| `design/dashboard-desktop-qa-20261109` | `933a126ea112e9a0cf38167d9ff4eb652f126898` | Retired historical branch; inspect SHA if needed |
| `design/dashboard-portfolio-alignment-20261109` | `3a7260000e62e324792a7ad85dc923d76465b459` | Retired historical branch; inspect SHA if needed |
| `docs/network-lab-audit-handoff-20261109` | `993894a7fcc334e65fb7e0b069925625c4f0d164` | Retired historical branch; inspect SHA if needed |
| `experiment/disruption-recovery-correctness-20261029` | `78494a9f6bcf821c32efff3cb64600359e381748` | Retired historical branch; inspect SHA if needed |
| `fix/paired-airport-market-label-20261029` | `f795ee512b29b8b0ac664c316e48424533222398` | [PR #28: unsafe, do NOT merge](https://github.com/yumorepos/network-lab/pull/28) |
| `phase5/milestone-a-integrity` | `e5f0e550c62c6ac19044f9c8593c6a55e061cf40` | Retired historical branch; inspect SHA if needed |
| `research/airport-identity-archive-audit-20261029` | `d840d0f7576841364b66d10ebcf0bf9051576ab0` | Retired historical branch; inspect SHA if needed |
| `research/cross-source-country-exposure-20261029` | `5e75ee4a700dc60b3bb53a915a07b402d3a42326` | Retired historical branch; inspect SHA if needed |
| `research/derived-cbsa-preflight-20261029` | `8dbba643e0df13e04d7c8f70c2f33a855e0b8618` | Retired historical branch; inspect SHA if needed |
| `research/source-id-vs-legacy-market-audit-20261029` | `967462e060b4fd4b3f8cd9d1b0d015203f06aacb` | Retired historical branch; inspect SHA if needed |
| `research/source-stable-airport-id-20261029` | `e22db762663d7e250117cfbfbfda890226408bc0` | Retired historical branch; inspect SHA if needed |
| `research/stage-b-t100-july-2026` | `f1405a9611ef6d6c3f5d5c8a695ece081855ca19` | Retired historical branch; inspect SHA if needed |
| `research/stage-c-db1c-compat-2026-10-28` | `d969e90814f3a81b8f6f2f5edfa7515b8e15127d` | Retired historical branch; inspect SHA if needed |
| `research/t100-2024-consumer-envelope-20261029` | `68626d8045e57f8b4cd3d2c1555a701b161668aa` | Retired historical branch; inspect SHA if needed |
| `research/t100-2024-exact-field-parity-20261029` | `35ac87ceecb66a6b0ba7196d1a2c61d9b52c3ee3` | Retired historical branch; inspect SHA if needed |
| `research/t100-cross-vintage-ids-20261029` | `1a2bf0e2d0532c04be05fbf86a115821ed9126b9` | Retired historical branch; inspect SHA if needed |
| `research/t100-multivintage-airport-identity-20261029` | `4350e50b9cdd844a5cf05eca88b42b9d226eaa11` | Retired historical branch; inspect SHA if needed |
| `security/bts-tls-verification-20261029` | `43267f7f2a362a3f8afb2dfd1dd8e4a4b8d4e9c0` | Retired historical branch; inspect SHA if needed |
| `security/ingest-common-tls-20261029` | `fa6c55213cd496648de5418f95c9491641c4c43e` | Retired historical branch; inspect SHA if needed |
| `ui/mobile-header-typography-2026-10-28` | `c25f45975915b6dbbf8220c2547b068dfe8e4efe` | Retired historical branch; inspect SHA if needed |
| `upgrade/provenance-gates-20261028` | `03d3b62ea939c9ac1927b11c363251a6c304f70c` | Retired historical branch; inspect SHA if needed |

**Operational precautions:** close open PRs before deleting their head branches, never delete `main`, and abort a branch deletion if its current head SHA differs from this inventory. Protected/updated branches should be skipped. Confirm the repository still runs its existing CI after cleanup. A deleted remote branch may remain in local Git clones until `git fetch --prune`; no local files on the Mac were touched by this remote-only inventory.
