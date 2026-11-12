# Boolean aggregation v1

基线 c2081db68b5bf6306aa6cd39b839d7d8e04b0ae9；HPC2 独立 worktree。
本页在真实验证后补录不可变执行 SHA、API 计数及产物路径。

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
