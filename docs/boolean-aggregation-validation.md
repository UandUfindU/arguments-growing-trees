# Boolean aggregation v1

基线 c2081db68b5bf6306aa6cd39b839d7d8e04b0ae9；HPC2 独立 worktree。
最终真实执行 SHA：1cd88d80a854b7b2b862219e9d589575181b5741（先测试/推送，再 fetch、核对、干净 detached checkout）。
首个候选执行 SHA：790e72f6624b88390e01f82c766ea39a8f508567；两个无效初始化候选被拒，原始响应保留。
其后仅澄清 prompt 的原子 Claim/证据记录区别，没有调整统计规则或观察结果择优。交付提交另加入本页与录制页面，不改实测执行代码。

树默认只有 Boolean evaluator：AND=min；OR=预设非负归一权重平均；
NOT 递归传极性（De Morgan），查找独立局部测试，缺失 pending。
AND 的父 null 是并集，min 不大于任一真实 null 分支的 e。
OR 的父 null 是交集，预设加权平均在任意依赖下有效：
[Wang (2025), Biometrika 112(2), asaf020](https://doi.org/10.1093/biomet/asaf020)。
这些是固定 snapshot 规则，不授予跨时点 optional stopping 保证。

局部检验记录命题、极性、H0/H1、范围和语义/null/统计状态；
代理匹配字段与执行成功不代表语义等价或统计 valid。
预测、动态选择或待审条件使结果 provisional；拒绝 review 为 pending。
表达式改动须显式语义 review、新版本及原文/范围不变。
同一论断补充证据替换同一 slot，保留旧检验，不新增 AND 条件。
因果效应需要自己的操作化/检验，相关性不替代因果。
序贯乘积仅为隔离历史 POPPER 协议，不被树引擎使用。

页面中的 8/5/2、AND=2、混合 OR=3.2/替换后1.6 全为 illustrative 算术，
不是实测财务结果或 S1 训练结果。真实运行使用既有注册历史数据；
S1 仍未训练，不扩展 provider 或采集材料。

## HPC2 验证

- compileall 与 47 项核心离线 CPU 测试通过，加入录制页面审计后最终48项全部通过；investment fixture、训练资源仅格式校验通过，training_executed=false；Discovery fixture 亦执行。未训练、未使用 GPU、未下载权重、未采集网络材料。
- 真实 Qwen/Qwen3.8-27B 成功运行：初始化 → 挂载 → S1 untrained/null → 后台检验 → 同槽替换 → 重复来源跳过，共 3 请求。
- 包含先前两个被拒候选，总请求 5/16（5 个 HTTP200），预留输出15000/48000，实际输出3591，输入12554；首次请求到末响应约146.947秒，低于25分钟。同一持久账本，未重置。
- 被拒原因：未经审查的 supports 边、claim/test 重复 ID。修复只澄清结构提示；未将失败输出当执行成功，未选择最大 e。
- 初始化 nvda_fy24：Pearson 双侧，n=4，p=0.005768989389326018，e=6.582943599976901。
- 更新 nvda_fy25q1：同一 c_proxy 槽，n=5，p=0.0004792263782563918，e=22.840186552601637。旧检验、共享数据族、范围和条件均保留；不是两个因子相乘。
- 根原文固定“NVIDIA未来一个季度的经营前景将改善”；expr v1 ref(c_proxy) 仅为待审代理适配，根及局部结果 provisional / requires_review。S1 未训练期间即时结果 pending/null。未声称未来结论、因果识别、有效 p/e 或投资实验成立。
- 形式保证仍欠语义等价、null 对齐、时间序列/模型选择等统计条件审核；无相反极性测试时 NOT pending。真实回放只展示已有可检验代理，没有伪造因果分支。

## 全证据（仅 HPC2）

/hpc2hdd/home/yfeng044/agt-boolean-evidence-20261112/
包含 api-ledger.jsonl（所有原始响应与失败）、summary.json、执行 SHA、pinned-check/、
prompt-repair-check/、qwen-investment-final/{run.json,index.html,training.jsonl}；
最终交付检查位于 delivery-check/，旧实验未改动。
[录制页面](../demo/index.html) 与真实成功运行页面逐字节一致；
SHA256：4eef2decd0af4e01b23b2d962ddbc29772866fa954896c83cb191fa51b566d4c。
页面独立的 illustrative 段落与真实回放数据明确分开。
GitHub 仅托管代码，无 CI；VPS 仅保存仓库 URL、SHA 与任务元数据，无邮件/监控。
