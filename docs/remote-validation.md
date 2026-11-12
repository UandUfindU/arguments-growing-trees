> 历史协议记录；当前树默认规则已由 [Boolean v1](boolean-aggregation-validation.md) 取代。以下旧累计契约/数值状态仅描述当时运行。

# HPC2 live Qwen integration validation

Date: 2026-11-12 UTC. CPU API client only; no training, GPUs, email, recurring monitors, or changes to other campaigns.

Original immutable SHA: `cfcc0a5b06091518b5195c1a755e4b860b806b5b`.
Integration branch: `integration/hpc2-live-qwen-20261112`.
Final executable code SHA: `e431668c074d12355ae8429b1be164e02bdec93a` (this documentation commit changes no code).

HPC2 isolated root: `/hpc2hdd/home/yfeng044/agt-integration-20261112T0625`. Full outputs, environment, install/test logs and API ledger remain outside Git.

## Integration fixes

- Explicit nonempty string null/alternative hypothesis fields and bounded schema repair.
- Allowed edge relations and two-sided Pearson contract; claim-only attachment parent validation.
- Empty verification plans must include a reason; opt-in response ledger on HPC2 only.
- Existing chat_template_kwargs was accepted; model never substituted. trust_env=False; direct campus access, no proxy or API key required.

## Validation

9 unit tests passed, including mocked malformed-plan and attachment repair regressions. Both live runs used Qwen/Qwen3.8-27B, HTTP 200 for every recorded response. Initialization leaf grounding, dataset cutoff, mount-before-S1 ordering, null untrained S1, recomputed SciPy p/e, duplicate skip, and masked-label validation passed.
Lifecycle: initialized → mounted → immediate_update → background_verified → rescored → duplicate_skipped.
training_executed=false. Root probability/e remain null; statistical validity requires domain review and formal root aggregation is not established.

### qwen-investment-05

Executed SHA: `d5c6474ac8aa78288625378869746cb6acbca998`; API requests: 4; usage: `{"prompt_tokens": 4577, "completion_tokens": 692, "total_tokens": 5269}`.
- t_1: pearson on nvda_fy24; p=0.005768989389326018, e=6.582943599976901.
- t_2: pearson on nvda_fy25q1; p=0.0004792263782563918, e=22.84018655260164.
- `/hpc2hdd/home/yfeng044/agt-integration-20261112T0625/runs/qwen-investment-05/index.html` (39594 bytes).
- `/hpc2hdd/home/yfeng044/agt-integration-20261112T0625/runs/qwen-investment-05/run.json` (46173 bytes).
- `/hpc2hdd/home/yfeng044/agt-integration-20261112T0625/runs/qwen-investment-05/manifest.json` (1507 bytes).

### qwen-discovery-04

Executed SHA: `e431668c074d12355ae8429b1be164e02bdec93a`; API requests: 6; usage: `{"prompt_tokens": 7803, "completion_tokens": 605, "total_tokens": 8408}`.
- t_1: chi_square on pathways; p=6.253230532911228e-47, e=6.322921418985236e+22.
Runtime no-test reason: The attached event is a source-review fixture confirming that the data is the same registered table already tested in t_1. It does not introduce new independent observations or a new claim that can be assessed by a registered executable test on the available dataset.
- `/hpc2hdd/home/yfeng044/agt-integration-20261112T0625/runs/qwen-discovery-04/index.html` (36032 bytes).
- `/hpc2hdd/home/yfeng044/agt-integration-20261112T0625/runs/qwen-discovery-04/run.json` (41095 bytes).
- `/hpc2hdd/home/yfeng044/agt-integration-20261112T0625/runs/qwen-discovery-04/manifest.json` (1566 bytes).

## Budget and limitations

Total requests including failed integration attempts: 24 / 40. Ledger: 23 responses, usage `{"prompt_tokens": 25434, "completion_tokens": 3234, "total_tokens": 28668}`. One earlier HTTP200 initialization failed schema validation before the original CLI could persist its response/usage; its max_tokens was 3000. Therefore completion tokens are bounded by 6234 / 120000, while exact total usage for that request is unavailable.

No execution blocker remains for these demos. Model output still requires validation and may exhaust bounded repair on other inputs. Investment is a descriptive serial revenue proxy, not a causal or investment-return conclusion. Discovery runtime event is explicitly a same-table source-review fixture; planner returned no new test with a reason. This fixture event does not replace live Qwen inference.

Full HPC2 evidence: `api-ledger.jsonl`, `audit-summary.json`, `environment.txt`, `install.log`, `tests-fixed.log`, scenario validation logs, and preserved failed-run logs under the isolated root. No full outputs or private service configuration are committed.
