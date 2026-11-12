# Arguments as Growing Trees

**Can Models Learn to Assess Investment Hypotheses from Evolving Evidence?**

可运行的研究 Demo：System 2 将自然语言假设展开为可执行代理检验；新文本到达后，先挂载论断和来源，再调用 System 1 的局部 log-e 预测接口，同时继续后台验证。

System 2 支持 OpenAI-compatible Qwen API。本次用户确认使用 **Qwen/Qwen3.8-27B**。System 1 提供联合遮蔽、数据导出和可选训练入口；**尚未训练，演示中的预测值为空**。

## 五分钟运行

所有测试、集成和 API 演示仅在授权 HPC 执行；GitHub 只托管代码。Python 3.10+，不需要 GPU：

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m agt.cli demo --backend fixture --scenario investment --output runs/investment
python -m agt.train runs/investment/training.jsonl
python -m agt.cli serve --directory runs/investment --port 8765
```

打开 <http://127.0.0.1:8765>。也可以直接打开生成的 `runs/investment/index.html`；页面独立包含本次运行的全部阶段快照，可点击树节点查看执行记录。

`fixture` 是确定性的离线编排，用来验证软件链路；页面会明确显示 offline-fixture。统计工具始终执行真实的 SciPy 计算。

## 使用真实 Qwen System 2

仅在授权 HPC 的环境中设置 `.env.example` 列出的变量。程序读取环境变量，不会自动加载 `.env`，也不记录密钥或带凭据的 URL。

```bash
export AGT_QWEN_BASE_URL='https://your-authorized-endpoint/v1'
export AGT_QWEN_MODEL='Qwen/Qwen3.8-27B'
# If needed, inject AGT_QWEN_API_KEY via your existing secret manager.
python -m agt.cli demo --backend qwen --scenario investment --output runs/qwen-investment
python -m agt.train runs/qwen-investment/training.jsonl
```

每次演示通常调用三次 API：初始化、挂载、验证。单次运行最多 12 次调用，每次最多 3,000 输出 tokens，有界重试。没有模型自动降级。输出目录必须为空，避免覆盖既有记录。日志保留模型 ID、状态、耗时和 token 用量，不保留服务配置。

校园服务只通过客户端专属 `AGT_QWEN_PROXY` 配置代理，默认 `trust_env=False`。GreenCloud 负责派发；项目代码、依赖和运行结果放 HPC。

## 演示内容

| 阶段 | 实际发生的事 |
| --- | --- |
| 初始化 | System 2 生成子论断/代理检验；工具执行后，初始树所有叶节点均为可执行验证记录 |
| 新证据到达 | System 2 根据当前树和真实来源选择位置，挂载新论断与文本节点 |
| 即时更新 | 挂载后调用 System 1，完整树输入，受影响路径联合遮蔽；未训练接口返回空预测 |
| 后台验证 | System 2 选择注册工具、数据和检验，执行得到 p 与转换后的 e |
| 实测替换 | 实测替换同一局部槽位；使用相同显式契约重新计算，保留之前快照 |
| 重复事件 | 以事件及来源链 ID 去重，同一来源不产生新独立证据因子 |

`investment` 是时间回放：2024-02-22 初始化仅使用 FY2024 四个季度；2024-05-23 才开放含 FY2025Q1 的数据。原始公告分别发布于 2 月 21 日、5 月 22 日，演示使用次日 UTC 作为保守可用时间，不声称分钟级历史还原。数据的每个数值来源见 [SOURCES.md](SOURCES.md)。

收入与季度序号的 Pearson 检验只是小样本观测代理。序列依赖未校正，模型选择和事后分析亦会影响推断，结果标记 `requires_review`。该演示展示执行与更新机制，根命题的概率、根 e 和投资回报推断尚未建立。初始树只展开本次注册的数据代理范围，完整投资论证分解是后续工作。

`discovery` 使用 DiscoveryBench 官方真实计数表，执行列联表检验，演示重复数据的显式引用：

```bash
python -m agt.cli demo --scenario discovery --output runs/discovery
```

这张表属于该项目的一项数据子集；本代码没有复现 POPPER 的完整 benchmark。Discovery 的运行时事件是“重新审阅同一来源”的软件夹具，页面及源记录明确标注，不作为历史新闻。

## System 1 的训练入口

System1 的目标是**给定目标论断、完整当前树、真实新闻文本、发布时间/根时间及来源，预测一个局部 log e**。同一新闻对不同论断可有不同证据价值。路径遮蔽仅防泄漏，绝不训练祖先标签或路径向量。

`training.jsonl` 仅包含运行时新闻与唯一对应已执行检验的对齐样本；初始化检验不自动成为样本。无检验或无唯一对应时不导出，并在 pairing_notes 说明原因。`python -m agt.train DATA.jsonl` 只验证；空配对返回 empty_pairing，不是假装训练成功。本次未执行训练、未下载权重，System1 返回 null。

模型输入保留完整树结构和未受影响上下文，遮蔽局部结果、全部祖先数值、重复数据/同数据族及其祖先的结果；移除预测、槽位、聚合载荷和执行日志。训练仅对一个已执行局部 log e 回归。正文须保持为结果产生前的真实文本，外部语料需独立进行数字泄漏审计及按来源划分。

`AggregationContract` 显式声明路径、顺序乘积规则和统计有效性依据；树边本身不授权聚合。对于已有合法顺序契约，临时 Enew=Eold×predicted_local_e；实测替换同一槽位后按相同规则重算。临时总量与正式实测总量分开。没有契约的路径保持结构连接、累计数值为空。当前真实代理检验 requires_review，**没有合法聚合契约，不报告根概率**。确定性测试可注入已知局部标量，标记为 fixture。

查看 [录制的真实 Qwen 投资演示](demo/index.html)（下载该 HTML 后可独立打开；System1 未训练）。[验证记录](docs/cloud-local-evalue-validation.md) 包含执行 SHA 和 HPC 产物路径。

## 代码位置

| 文件 | 责任 |
| --- | --- |
| `agt/tree.py` | 节点、关系、版本和时间 |
| `agt/engine.py` | System 2 编排、异步任务、版本比较、去重 |
| `agt/qwen.py` | 真实 API 客户端和结构化规划协议 |
| `agt/statistics.py` | 注册工具；CSV → SciPy → 执行记录 |
| `agt/system1.py` | 联合路径遮蔽、未训练预测接口 |
| `agt/train.py` | 数据验证及可选训练代码 |
| `agt/scenarios.py` | 投资历史回放和 DiscoveryBench 数据夹具 |
| `agt/web/index.html` | 交互式阶段回放页面 |

## 研究边界与下一步

目前实现了有限工具集和数据注册表，不执行 LLM 生成的任意 Python；API 规划结果须经树结构、工具和数据可用时间校验。后台任务使用 revision 比较，过期结果不会覆盖较新树；当前过期任务记录后退出，自动重规划/重试队列待实现。

POPPER 的固定 kappa=.5 校准形式 `e=.5/sqrt(p)` 已独立实现，并逐项保存 p、e、零假设和数据哈希。有效 e 的前提是有效 p；共享样本、数据依赖、假设关系和条件有效性必须进一步确立，程序没有将叶 e 自动连乘为根 E。实测 e、预测 log e 和命题概率是不同量。

下一步实验需要检验：完整树相对平铺文本的价值、异质监督可学性、概率校准、时间更新正确性，以及后台验证对即时判断的改善。本次软件演示不报告这些研究结论。

## HPC 离线 CPU 检查

在 HPC 检出固定提交后，使用已有环境执行：

    PYTHON=/path/to/existing/venv/bin/python bash scripts/check-cpu.sh /absolute/hpc/path/new-check-evidence

执行 compileall、单元测试、investment fixture 和配对数据验证；不调用 API、不训练。完整日志和结果留在 HPC。GitHub Actions workflow 已移除并保持禁用，不迁移到其他 CI。


## 可执行代理初始化（proxy-v1）

沿着代码阅读：scenarios.py 的注册目录/真实列类型 → prompts.py 的初始化计划
→ planning.py 的 JSON/schema 解析 → proxy.py 的方法、代理范围和真实数据核验
→ statistics.py 的 CPU 检验 → tree.py 的结构与逐论断叶代理追溯
→ engine.py 的候选提交。模型不能自行声称数据存在，也不能提交 p/e。

“可执行”表示代理规格已落到注册数据和实际工具执行记录；不表示父论断获支持。
规格包括目标 ID、测量量、实体、时期、单位、列映射、数据可用时间、方法、
H0/H1、单双侧、样本要求、统计假设、父子适配理由和局限。
Pearson 仅允许明确的双侧非零相关 H1；不能把双侧结果改名为单侧结果。
执行结果单独记录统计假设、共享数据、证据方向未定和语义审查状态；
自由文本适配理由不能自动证明逻辑蕴涵，仍需领域审查。

初始化先计划，再核验/有界修复、执行、结构/覆盖检查，最后提交一次成功快照。
中间 Claim 合法，但每条已提交分支必须递归到执行叶；空检验、悬空分支、无效列、
恒定序列、重复观测、未来数据会失败。失败候选只留在 HPC 运行审计中。
初始树无 TextualEvidence；真实新闻先经 S2 挂载，再调用未训练 S1（局部值 null），
最后异步检验并替换同一局部槽位。没有合法累计契约时路径数值保持 unset。

coverage 保留原始根假设并分别说明已操作化范围、未覆盖方面与是否完整覆盖。
投资样例只能执行历史收入代理，未来经营前景和回报没有被验证；
缺失方面不伪装成成功树中的 pending 分支。Discovery 只测注册历史计数表关联。
重复表/同数据族不是独立证据。时间序列依赖、因果性和父论断蕴涵不因软件检查通过而成立。

HPC 运行命令仍为前述 CLI。真实联调应共享一个新的 HPC AGT_QWEN_LEDGER 路径，
跨运行最多 36 次请求、每次至多 3000 输出 tokens（保守上限 108000），
首次请求起至多 40 分钟；每次请求前持久预留，传输失败也计数。
单次 CLI 最多 12 请求；schema 修复与执行/覆盖修复分别记录，不等同语义确认。
全日志和原始响应仅留 HPC；[本轮验证](docs/proxy-initialization-validation.md) 记录固定 SHA。
