---
outline: deep
---

# 执行摘要

> **版本**：v2.1 · **更新日期**：2026 年 7 月 30 日<br>
> **主分析期**：2025.07–2026.06 · **精读**：84 篇 · **官方评审锚点**：30 条

过去 12 个月最显眼的共识是 VLA / generalist policy 的论文数量急升；更有战略价值的变化却发生在“模型之外”：实时调度、动作验证与恢复、部署数据飞轮、可执行 world model、视触觉闭环和跨本体接口。**综合判断（推断）：**具身智能正在从“能输出动作”进入“能在物理世界持续运行、发现错误并学习”的阶段。

::: tip v2.1 扩容说明
旧五类月度序列继续作为可比的精选分析层；它不再代表全部数据量。新版同时维护两年宽召回母库、正式发表母库、严格官方 proceedings 和 GitHub 证据，并将方向体系扩展为 15 类。详见[语料扩充与覆盖审计](/analysis/corpus-expansion)。
:::

<div class="radar-kpis">
  <div class="radar-kpi"><strong>30,604</strong><span>arXiv 宽召回母集</span></div>
  <div class="radar-kpi"><strong>10,254</strong><span>窗口内正式发表记录</span></div>
  <div class="radar-kpi"><strong>824</strong><span>严格官方 proceedings</span></div>
  <div class="radar-kpi"><strong>40,345</strong><span>去重 canonical works</span></div>
  <div class="radar-kpi"><strong>42</strong><span>GitHub 核验仓库</span></div>
</div>

## 六个年度判断

1. **基础模型是最大共识，不再是最早信号。** 主分析期统一查询口径下，具身基础模型候选占比最高；方向已经拥挤，差异转向执行、数据与后训练。
2. **大小脑的真正拐点是实时系统。** fast–slow 名称本身价值有限，completion gating、continuous reasoning、verifier 和 3D trace 才是接口创新。
3. **world model 的淘汰赛开始。** 能否在同算力下提高闭环规划、RL 样本效率或失败恢复，将把控制模型与普通视频生成分开。
4. **触觉从“小众传感器”变成领先指标。** 它最可能先在接触失败恢复、材料/滑移预测和灵巧 world model 中兑现。
5. **跨本体更可能通过共享表示 + 小型 adapter 实现。** “一个权重直接覆盖所有机器人”的证据仍不足。
6. **数据护城河正在迁移到部署闭环。** 未来关键指标不是总小时，而是失败覆盖、修正效率和新任务上线速度。

## 精选月度分析层

<div class="radar-kpis">
  <div class="radar-kpi"><strong>1841</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>633</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>59/84</strong><span>精读真机确认</span></div>
  <div class="radar-kpi"><strong>16/84</strong><span>精读明确开放披露</span></div>
</div>

| 深度指标 | 分子 / 分母 | 说明 |
|---|---:|---|
| 真实机器人 | 59/84 | 摘要或核验页明确披露 |
| 多任务 | 18/84 | 不把任务变体自动当作多任务 |
| 跨本体 | 20/84 | 至少两类机器人/硬件 |
| 长时序 | 21/84 | 明确长时、多阶段或连续任务 |
| 代码/数据/模型开放 | 16/84 | “will release” 不等于已开放 |

## 对研究布局与投资观察的含义

| 观察对象 | 应追问的证据 | 高风险信号 |
|---|---|---|
| VLA 团队 | 真机时延、失败恢复、部署数据回流 | 只报告仿真平均成功率 |
| 世界模型团队 | 同算力控制增益、model bias、闭环时长 | 只展示视频质量 |
| 灵巧/触觉团队 | 跨手型、跨传感器、长时接触 | 单次定制 demo |
| 数据团队 | 有效多样性、失败覆盖、下游边际增益 | 只强调总小时/总帧数 |
| 开源项目 | 第三方复现、外部采用、活跃维护 | 只放模型名或未来承诺 |

## 最重要的非共识机会

按当前证据排序：**实时 VLA 执行栈、verifier/自纠错、部署数据飞轮、控制导向 world model、触觉预测通道、跨本体动作接口、3D trace，以及高风险的 Embodied Agent OS。** 详见[未来判断](/analysis/weak-signals)。

<!-- 更新标记：执行摘要 最后更新 2026.07 -->
