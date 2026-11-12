# Cloud local e-value validation

2026-11-12 UTC. Private repository; CPU/API integration only. No training, weight download, GPUs, email or recurring monitors. Other campaigns unchanged.

Executed immutable code SHA: `00255ed4657e65568c6c72db7245487a6a81b1f4`. Subsequent delivery commit adds only this report and curated HTML. Base: `fe41bdf35322703127b8a2f6ee0e11feb26ca1b7`; branch: `cloud/local-evalue`.

14 CPU unit tests pass. Real Qwen/Qwen3.8-27B investment lifecycle: initialized → mounted → immediate_update → background_verified → measured_replacement → duplicate_skipped. One aligned runtime local-label pair validates; initialization is excluded. Training input uses pre-verification snapshot (no future test nodes), full tree/claim/news/time/source; only the local slot has a regression target.

Campaign requests: 13/16 (12 HTTP 200 responses plus one ConnectError using stale documented service routing). Recorded usage: `{"completion_tokens": 2103, "prompt_tokens": 13905, "total_tokens": 16008}`. Transport failure has no response usage; conservatively adding its 3000-token request maximum bounds output at 5103/48000. API validation wall time including failed route and reruns: 218.2s /1500s. Final pinned run: 4 HTTP200 requests, including bounded schema repair. Prior intermediate runs are preserved, not relabeled as final.

| Executed test | Dataset | p | local e |
| --- | --- | --- | --- |
| t_1 | nvda_fy24 | 0.00576898938932602 | 6.5829435999769 |
| t_2 | nvda_fy25q1 | 0.000479226378256392 | 22.8401865526016 |

System1 remains untrained with scalar null. Background measured log-e replaces the SAME slot; provisional and measured factors are never multiplied together. No sequential contract is valid for these requires_review proxies: cumulative path values and root probability/e are unset. Deterministic explicit-contract fixture tests verify Eold×local and replacement. Serial dependence, statistical validity and generalization remain research limitations.

Discovery live API run omitted to conserve budget. CPU no-test fixture verifies zero supervised pairs with reason and empty_pairing validation; source-review fixtures are excluded even when a test executes.

All full evidence remains on HPC2: `/hpc2hdd/home/yfeng044/agt-local-evalue-evidence/`. Final run: `investment-pinned/` (run.json, training.jsonl, index.html); earlier runs: `investment-02/`, `investment-final/`; failed transport: `investment.log`; `tests.log`, `api-ledger.jsonl`, `audit-summary.json`, `train-validation.log`. The raw API ledger is not committed.

Curated `demo/index.html`: 41318 bytes, self-contained recorded Qwen replay, explicitly System1 untrained; contains no endpoint, key, API configuration or raw ledger. No execution blockers remain.

## HPC-only verification follow-up (2026-11-12 UTC)

Task gc-20261112T062733-ceaa1225 completed before these modifications. Fetched main and cloud/local-evalue at identical SHA 4cf379720d96b0393d0d9a10c674089c3d1b346f on HPC2. Historical 5d0471a SyntaxError (engine.py:147, unclosed parenthesis, before any API) was fixed by 2b3f8041627220bf69470d751ef34f9d183814a0, included in main.

Removed .github/workflows/tests.yml. Workflow 415632826 was confirmed disabled_manually, never re-enabled. GitHub remains private code hosting. Reproducible offline CPU verification is scripts/check-cpu.sh, run on authorized HPC with the existing environment.

HPC2 checks: compileall, 14 unit tests, investment fixture and pair validation passed. Exact final delivery SHA is recorded in /hpc2hdd/home/yfeng044/agt-local-evalue-evidence/hpc-only-final/commit.txt; full logs and fixture remain in that directory. Zero additional API calls: updated-definition Qwen live run at 00255ed4657e65568c6c72db7245487a6a81b1f4 was already validated on HPC2. Curated demo unchanged. No training/GPU/weights/email/recurring monitors or replacement CI. Statistical limitations above remain; no software execution blocker.
