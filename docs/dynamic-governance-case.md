# 动态治理案例 v1

这是拟开展研究的六阶段 **storyboard / planned / incomplete coverage**，不是已实测的 NVIDIA 治理结果。通用演示与已有真实可执行经营代理子树保持原样，见 demo/index.html；本场景不把其历史经营样本冒充未来两季或治理样本。

## 回放

在 HPC2 仓库根目录执行：

    python -m agt.governance --output /HPC/新目录
    python -m agt.cli serve --directory /HPC/新目录

也可直接打开 demo/governance/index.html。下拉选择六阶段及初始化、挂载、即时、后台快照，按钮逐步前后回放。来源可点击。生成器无网络客户端、不调用模型、不训练；API 实际使用 0/8 次，输出 0/24000 tokens。

版本化数据位于 agt/data/dynamic-governance-v1.json，小 provider 与回放在 agt/governance.py。GovernanceProvider 遵循 EvidenceProvider 的 query 边界；未知 first_available_at 的材料不能通过严格 as-of 查询。storyboard 方法是显式人工选段，不宣称已验证当时可用性。

## 六阶段与时间

1. 2026-10-28 一句自然语言假设，H=A AND B，A=D AND M AND R，B=L AND O。L/O 都有具体代理方案，但没有注册样本与检验，故不成功初始化全树。
2. 10/29 早期报道仅保留待核对事件。缺原始归档、正文与首次可用时间；11/11 Reuters 不能回填。t0 更早风险仍保留待核对项，不能解释为没有风险。
3. 11/08 董事会调查与管理团队信心是同一文档两个语义片段，共用 document_id/lineage。用户批准的职责连续性语义 review 将 L v1 细化为 L v2=C OR S，预设权重各 0.5；不是仅 CEO 在任的命题。表达式仍 requires_review，不认证正式统计有效性。
4. 11/10 外部律师说明调查程序，新增 IC 诊断问题。IC 不自动加入 B 聚合表达式。
5. 11/11 Reuters 转述 NYT 保留 reported/alleged 与原始报道 lineage；不是已裁定事实。
6. 同树并置历史支持表态与后续风险报道，先定位目标、时间与来源状态；经营证据本场景仍缺，不能虚构冲突结论或 11/12 官方澄清。

日期来自用户任务，链接与摘要尚未独立核验。保存美国日期标签及 America/New_York、北京时间 Asia/Shanghai 字段，但由于缺原始发布时间，首次时间与北京时间日期为 null，不造分钟、不把 day-only 日期转成精确出版时刻。root_time 的午夜只是 storyboard 参考边界。

## 数值和结构约束

复用现有 Boolean AST/evaluate、Tree 表达式版本与 UntrainedSystem1 的祖先联合遮罩；S2 挂载后才调用 S1，随后异步后台阶段带 revision 检查。S1 untrained/log_e=null，局部目标依片段为 L 或 IC。后台只记录缺样本，不生成 p/e 或训练对。公告、在任状态等事实核查与实际统计检验分别处理；文本反馈和新闻情绪不是统计样本，股价异动不构成经营因果证据。

distinctEvidenceIDs 按来源 lineage 去重，片段 ID 分开；重复派送不增加样本。全树 formal_root_E=null。require_initialized 明确拒绝不完整覆盖。原通用 Engine 的同 slot 实测替换、Boolean 重算、版本并发与监督边界保持不变。新测试使用标注 synthetic test fixture 的值检查替换与正反极性；这些值从不进入 NVIDIA 回放或训练监督。低正向 e 不转换为反向 e。

## 尚待验证

D：需求样本；M：订单到收入/交付匹配样本；R：未来两季财报与预注册基准；L/C/S：职责履行、授权和有效接续记录；O：经营交付与里程碑样本；IC：独立内控有效性核查。每项还缺预注册操作化定义、H0/H1、极性与统计有效性审核。新增内控问题只扩展诊断结构；改变参与聚合表达式需逻辑等价或明确 scope revision 审核。本轮未采集所有证据，未完成上述检验。

## 验证

HPC2 运行 compileall 与全部 CPU unittest；完整 stdout/stderr 在仓库之外的 HPC2 evidence 目录。无 CI、GPU、权重下载、新闻采集、邮件或监控。
