> 历史协议记录；当前树默认规则已由 [Boolean v1](boolean-aggregation-validation.md) 取代。以下旧累计契约/数值状态仅描述当时运行。

# V5：自然语言假设起点与采集范围

继承前任务最终 SHA `a369a6b1320e8062ee8e3d0b91f30b6b13e7217e`，保留其 27 项测试和真实 Qwen 联调成果，证据在 HPC2 `/hpc2hdd/home/yfeng044/agt-proxy-evidence/`。本轮只收敛入口与合同，不重写统计、网络客户端或训练。

## 方法与演示

输入未经验证的自然语言假设、参考时间、目标期限、可用数据环境。CLI 的 `--hypothesis`、`--reference-time`、`--horizon` 直达 Engine.initialize；无历史验证记录输入。S2 基于实际公开 schema 联合生成层级、父子关系与代理规格；候选只有通过执行和逐支覆盖检查才提交。树组织生成、验证、更新，不只是已有记录可视化。

investment 默认假设保留原始前景问题，已操作化部分仅是历史收入关联；未来经营前景、收益等未覆盖方面留在 coverage，不冒充已证实结论。参考时间控制数据可用性，期限只描述研究目标，不能开放未来数据。Discovery 期限由用户按任务指定。

S1 从其他已完成且独立审核配对的历史轨迹学习，非初始化前提，也不每次重训。当前未训练。运行顺序保持 S2 挂载 → S1 单个局部 log e → 已有规则更新 → S2 后台实测 → 同槽替换并重算。无有效统计累计契约时数值仍 unset。

## 实现边界与 provider 合同（统一说明）

已实现：自然语言入口、真实 Qwen 规划客户端、真实注册小数据的 CPU 代理执行、时间/schema/语义落点检查、原子初始化、去重、局部槽更新及防泄漏。材料为预置真实来源摘录或明确标注的 fixture；不是自动采集结果。既有 recorded real Qwen 演示保留原执行 SHA，不把离线 fixture 改标为真实 API。

未实现且本轮不扩建：新闻抓取、爬虫、金融数据库连接及生产采集平台。外接采集只需遵守 `agt/providers.py` 两个窄协议：

- EvidenceProvider.query(query, as_of) 返回截至 as_of 公开的材料：id、lineage_id、published_at（带时区）、source_url、text、text_type。text 是保留来源措辞的材料或明确标注的人工作摘录，不得伪装完整原文；需要完整原文时由 provider 保留并注明。InMemoryEvidenceProvider 使用预置材料和字面检索，返回副本，校验完整来源字段并过滤未来材料。运行时选择/配对可替换该查询入口；审核配对仍走既有 system1.masked_example，不更改标签定义。
- DatasetProvider.catalog(as_of) 返回公开 schema、类型、可用时间、来源、方法及操作化元数据，不能来自 LLM 自报；registered(as_of) 返回同一注册表的执行数据引用。FileDatasetProvider 使用现有小文件，catalog 经 read_registered_rows 核验真实列/类型/有限值/样本/重复观测，向规划器隐藏路径。Engine.catalog 复用此实现；执行仍由既有执行器按截止时间再次核验。外接 provider 需要实现这两个方法，示例 CLI 只传其注册引用给既有 Engine。

没有新增抓取服务、泛化适配平台或训练。注册文件的 source_url 是数据来源；provider 只暴露真实已注册且公开的 schema，不授权任意模型生成代码。

## 可验证路径与检查位置

`cli.run` → provider 筛选 → `Engine.initialize(hypothesis, reference_time, datasets, horizon=...)` → `prompts.initialization_prompt` → `planning` 解析 → `proxy` 数据/规格核验 → `statistics.execute_test` → `Tree.validate_initial/proxy_trace` → 原子成功提交。

`tests/test_providers.py` 检查 provider 可替换、未来材料与数据过滤、来源字段、无验证记录的自然语言入口与期限保留；原有 `test_proxy.py`、`test_local.py` 等继续约束逐支执行、统计边界、局部替换与泄漏。

本轮日志仅在 HPC2 `/hpc2hdd/home/yfeng044/agt-v5-scope-evidence/`；最终 SHA、测试结果与本轮 API 计数见交付记录。无训练、GPU、下载权重、邮件、Actions 或监控。

## 本轮验证交付

可执行代码固定 SHA：`ac71179239d10bd2ebc0083436826289dda45fb2`（已推送独立分支后执行）。
compileall 与 30 项 CPU 测试通过，包含前任务全部 27 项；investment fixture 与配对验证通过。
真实 Qwen3.8 集成：中文原始假设“ NVIDIA未来一个季度的经营前景将改善 ”，期限“未来一个财政季度”。3/8 次请求，全部 HTTP 200，实际输出 1266/24000 tokens；无 schema/语义修复、无失败。
初始化每条已提交分支有实际执行代理；full_hypothesis_covered=false，未来经营前景/回报/因果/预测未覆盖，S1 预测 null，后台实测替换同一局部值。完整阶段、usage 与审计保存在 HPC2 evidence 下的 summary.json、api-ledger.jsonl、qwen-investment/；没有重跑前任务实验。

[更新的真实 Qwen 回放](../demo/index.html) 标明预置材料、真实规划、实际检验及未训练 S1。
前任务的 Discovery 真实联调仍由原验证文档与 HPC2 路径佐证，本轮只做 Discovery 离线回归。
最终交付提交包含文档与回放更新；精确最终 SHA 记入 HPC2 final-sha.txt 与基站短摘要，避免文档自引用哈希。
