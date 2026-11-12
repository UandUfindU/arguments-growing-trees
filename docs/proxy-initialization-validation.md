> 历史协议记录；当前树默认规则已由 [Boolean v1](boolean-aggregation-validation.md) 取代。以下旧累计契约/数值状态仅描述当时运行。

# 可执行代理初始化与 Prompt 验证

2026-11-12；全部修改、CPU 测试、API 客户端与演示在授权 HPC2 完成。仓库仍 private；没有 CI、训练、权重下载、GPU、邮件、监控或网络改动。

## 固定交接与结果

- 原始 main SHA：`124525c7db2ca0fd00528d79b83f055fadd94b2a`。
- 最终实际执行代码 SHA：`1b9898df730342b04647a4925906e55940fa2e09`；分支：`greencloud/proxy-initialization`。
- 本报告及 curated HTML 的交付提交只修改文档/录制回放；其代码与上述执行 SHA 相同。最终交付 SHA 另保存在 HPC final-delivery-sha.txt。
- 两个真实 Qwen 初始化均为 root → c_proxy → t_measure，共三个节点。所有已提交论断逐支落到真实执行叶；没有初始 TextualEvidence、空检验、pending 或无代理限制分支。
- 这表示已提交的代理范围执行完整，不表示投资原始假设完整覆盖，更不表示学习有效或投资结论成立。

## 发现与修复的真实缺陷

原代码把长 prompt 混在 API 客户端内；schema 重试、方法方向和语义有效性边界不清。
真实首轮进一步暴露：模型重复输出 root，把限制写成无代理分支，并尝试用关联检验验证表格式。
这些候选均失败，没有成功树。修订没有丢弃检查器来迁就 HTTP200：

| 模块 | 职责与本轮变化 |
| --- | --- |
| agt/prompts.py | proxy-v1/v2 可追溯；初始化、位置选择、实验规划、修复独立纯函数，明确输入/输出、约束与小例子 |
| agt/planning.py | 解析 JSON/schema；不声称完成语义审查 |
| agt/proxy.py | 注册 H0/H1/方向、真实 schema、类型/缺失/有限值、观测唯一性、代理规格与覆盖检查 |
| agt/scenarios.py | 真实 catalog 增补列类型、观测键、实体/时期/单位、数据可用时间、样本要求/假设、testable_claim |
| agt/statistics.py | Pearson 与列联表独立执行函数，TestOutcome DTO；只由 SciPy 产生数值 |
| agt/tree.py | 结构检查与初始叶执行检查分离；逐论断 proxy_trace |
| agt/engine.py | 私有候选→执行/覆盖/结构检查→原子成功快照；一次有界语义修复；槽位替换与训练配对独立函数 |
| agt/qwen.py | 仅使用已授权 Qwen/Qwen3.8-27B；持久请求预留、usage/失败记录，schema 与语义修复分开 |

直接承接检验的论断必须精确匹配注册 testable_claim；这限制了当前小场景的可测含义，
不是通用自然语言蕴涵验证器。中间 Claim 可以继续拆分，初始化所有非根边均保留具体适配理由。
注册检验的证据边采用 context，未审查的统计显著性不能变成已接受的支持/挑战。

## 逐论断到叶代理的最终追溯

| 场景 | 论断 ID | 实际执行叶 |
| --- | --- | --- |
| investment | `root` | `t_measure` |
| investment | `c_proxy` | `t_measure` |
| discovery | `root` | `t_measure` |
| discovery | `c_proxy` | `t_measure` |

两个 root 均原样保留原始假设。完整各边 rationale、代理规格及执行记录可在回放节点详情和 HPC run.json 查看。

投资：c_proxy 测 NVIDIA 历史季度序号与收入的非零线性关联，只对应原假设中的历史收入代理；
不是未来经营前景、盈利、股价或投资回报检验。根到 c_proxy 为 context。
coverage.full_hypothesis_covered=false，明确列出 Future business prospects、Investment returns 未覆盖；
这些缺口不被塞进成功树伪装为完成的待执行分支。

Discovery：c_proxy 测注册 Catalonia 表内引入时期与途径的关联，
不是表格式验证、因果机制或整体 DiscoveryBench 复现。领域独立性仍待审查；
模型保守列出的因果、方向、生态含义与外推限制保留在 coverage，不作为已验证结论。

## 数据、方法和执行结果

| 场景/时点 | 数据 / 列映射 | 样本 | 方法/方向 | p | 局部 e |
| --- | --- | ---: | --- | ---: | ---: |
| investment 初始化 | nvda_fy24：quarter_index / revenue_musd | 4 | pearson / two-sided | 0.005768989389 | 6.5829436 |
| investment 真实新闻后 | nvda_fy25q1：quarter_index / revenue_musd | 5 | pearson / two-sided | 0.0004792263783 | 22.84018655 |
| discovery 初始化 | pathways：introduction.period / pathway / n | 1046 | chi_square / association | 6.253230533e-47 | 6.322921419e+22 |

投资初始截止 2024-02-22，仅 FY2024 四季度；2024-05-23 才开放五季度数据。
观测键 quarter_index；单位 USD millions。H0=零线性相关，H1=双侧非零线性相关。
实际显式调用 pearsonr(alternative='two-sided')。四/五个季度样本很少，独立双变量正态前提未确立，
序列依赖未校正；不能据此确认未来前景。后一次数据包含前四季度，overlapping_family_with 明确指向旧叶，不能连乘为独立贡献。

Discovery 的 12 个时期×途径单元、总计 1046 个计数；观测键为时期+途径，
H0=独立，H1=关联；自由度 6，最小期望频数约 16.4694，观测独立性仍需领域审查。稀疏表若任一格期望频数 <5 则拒绝，不能仅因 SciPy 返回有限 p 值而完成初始化。
所有结果 validity_status=requires_review、evidence_direction=undetermined_requires_review。
e=.5/sqrt(p) 的统计有效性依赖有效 p；不报告根 e、根概率或投资建议。

## 真实新闻链路与 System1

最终 investment 使用真实 NVIDIA FY2025Q1 公告的人工规范化事实摘录，沿用 SOURCES.md 的来源与保守时间回放。
真实 Qwen 完成 initialized → mounted → immediate_update → background_verified → measured_replacement → duplicate_skipped。
S2 先选择挂载位置并生成 Claim+Text；S1 输入完整树、目标论断、真实文本/来源/时间，
只返回一个局部 log-e，未训练值始终 null。后台五季度检验将同一槽位替换为实测 log-e=3.1285215526。
训练样本只导出一条局部对齐记录，未执行训练；路径及同源/同数据族结果遮蔽只防泄漏，不训练祖先目标。
累计契约未建立，所以累计值保持 unset，预测与实测不重复累计。

Discovery 的初始化也是真实 Qwen API。其 runtime 明确是同表 source-review fixture，最终模型返回无新检验与原因，
槽位保持 null，导出零训练样本；不冒充真实新闻或新独立数据。

## 测试、API 与失败记录

最终 compileall、27 项 CPU 单元测试通过。边界覆盖：未落地中间论断、无效父/重复 ID/循环、
伪造列/未来数据/样本不足/缺失/非有限值/恒定序列/重复观测、H0/H1与方向不符、
无关工具不能验证父论断含义、未审查支持边、半失败初始化回滚、重复源与祖先泄漏、
单个局部目标、同槽位替换、无契约不累计、持久预算和传输失败计数。

本轮全部请求 24/36，HTTP200 24；usage={"prompt_tokens": 45713, "completion_tokens": 11371, "total_tokens": 57084}。
保守请求输出预留 72000/108000 tokens，实计输出 11371。
API 联调至审计约 740.2 秒/2400秒；最终 investment 3 请求，Discovery 4 请求（一次覆盖声明语义修复），无 schema 修复。
全轮 schema 修复 2 次；首轮 investment 有一次语义修复，但两个候选仍因重复 root/未落地结构被拒；
首轮 Discovery schema 修复后仍失败。最终 Discovery 初次候选把非空 unresolved 与 full_hypothesis_covered=true 并列，检查器拒绝并经一次语义修复后通过。全轮共两次实际语义修复调用、三个被拒候选。HTTP200 本身从未被当作初始化成功。
中间 v2 与 ffe2188 联调成功记录保留但不替代最终 SHA 的 validated-* 证据。早期本轮开发检查发现的字符串语法错误、
循环报错测试顺序和 attachment context 缺字段均在提交/最终联调前修正；未推送语法错误。

## HPC 证据与边界

完整证据：`/hpc2hdd/home/yfeng044/agt-proxy-evidence`。最终目录 validated-investment/、validated-discovery/；
各有 run.json、training.jsonl、index.html；validated-*.log、api-ledger.jsonl、audit-summary.json、
final-executed-sha.txt、preflight/compileall.log、preflight/tests.log 留在 HPC。
investment/、discovery/ 为失败首轮；investment-v2/、discovery-v2/ 及 final-investment/、final-discovery/ 为中间成功记录；旧任务证据目录完全保留。

VPS 只派发并保存 URL/SHA/任务摘要；没有克隆仓库、安装实验环境、运行测试/API或保存数据结果。
Git 仅提交代码、文档与小型脱敏录制 HTML；没有原始响应、完整日志或服务配置。

无软件执行或外部访问阻塞。仍有明确科学边界：仅支持注册代理/列映射；任意自然语言的上层
语义适配、观测独立性、时间序列推断和完整投资假设覆盖未解决。可执行性不等同于学习效果或投资结论。

[真实 Qwen 投资录制回放](../demo/index.html)；[数据出处](../SOURCES.md)。
