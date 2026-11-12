# Arguments as Growing Trees

**Can Models Learn to Assess Investment Hypotheses from Evolving Evidence?**

可运行的研究 Demo：System 2 将自然语言假设展开为可执行代理检验；新文本到达后，先挂载论断和来源，再调用 System 1 的路径预测接口，同时继续后台验证。

System 2 支持 OpenAI-compatible Qwen API。本次用户确认使用 **Qwen/Qwen3.8-27B**。System 1 提供联合遮蔽、数据导出和可选训练入口；**尚未训练，演示中的预测值为空**。

## 五分钟运行

Python 3.10+，不需要 GPU：

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

在本机或授权 HPC 的环境中设置 `.env.example` 列出的变量。程序读取环境变量，不会自动加载 `.env`，也不记录密钥或带凭据的 URL。

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
| 重新评分 | 保存实测结果和版本，再调用评分接口；保留之前快照 |
| 重复事件 | 以事件及来源链 ID 去重，同一来源不产生新独立证据因子 |

`investment` 是时间回放：2024-02-22 初始化仅使用 FY2024 四个季度；2024-05-23 才开放含 FY2025Q1 的数据。原始公告分别发布于 2 月 21 日、5 月 22 日，演示使用次日 UTC 作为保守可用时间，不声称分钟级历史还原。数据的每个数值来源见 [SOURCES.md](SOURCES.md)。

收入与季度序号的 Pearson 检验只是小样本观测代理。序列依赖未校正，模型选择和事后分析亦会影响推断，结果标记 `requires_review`。该演示展示执行与更新机制，根命题的概率、根 e 和投资回报推断尚未建立。初始树只展开本次注册的数据代理范围，完整投资论证分解是后续工作。

`discovery` 使用 DiscoveryBench 官方真实计数表，执行列联表检验，演示重复数据的显式引用：

```bash
python -m agt.cli demo --scenario discovery --output runs/discovery
```

这张表属于该项目的一项数据子集；本代码没有复现 POPPER 的完整 benchmark。Discovery 的运行时事件是“重新审阅同一来源”的软件夹具，页面及源记录明确标注，不作为历史新闻。

## System 1 的训练入口

`training.jsonl` 记录各时点完整树；标签来自已执行的统计记录。对预测叶节点到根的路径取并集，**同时隐藏路径上的全部 result（包括 p/e/log e/累积值/判定）**；去除预测和执行日志；保留未受影响分支。仅实际有观测的目标进入损失，当前数据没有中间论断与根的数值监督。

```bash
# 验证遮蔽和标签，无训练、无权重下载
python -m agt.train runs/investment/training.jsonl

# 未来单独授权训练后才使用；本轮未运行
python -m pip install -e '.[train]'
python -m agt.train DATA.jsonl --execute-training --base-model LOCAL_MODEL_DIR --output checkpoints/system1
```

训练代码使用共享文本编码器，对各目标节点查询 log e，并对一个路径上有实测标签的目标计算平均平方误差。完整上下文超长时显式报错，避免截断成局部树。训练输入/推理输入使用相同遮蔽函数。当前仅有少量演示样本，不能支持有效训练或校准评估；暂未实现已训练权重的线上加载和校准器。

初始化/实验设计文本在结果产生前生成；数据结构将结果单独保存。接入其他语料前，仍需检查正文或同源分支是否复述目标统计量，按来源分组划分训练/验证/测试集，并统一遮蔽共享实验结果，避免跨分支和跨样本泄漏。

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
