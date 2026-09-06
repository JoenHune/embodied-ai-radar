---
outline: deep
---

# NVIDIA GEAR

> 企业/独立研究组织 · North America / United States · **来源状态：healthy** · 最后核验 2026-09-06

NVIDIA 面向通用具身智能的核心研究组，覆盖多模态基础模型、通用机器人、foundation agents、仿真与合成数据，并以 GR00T、EgoScale 等项目连接人类视频、世界模型与真实机器人策略。

| 项目 | 内容 |
|---|---|
| 母机构/上级 | [NVIDIA](https://www.nvidia.com/) |
| 负责人 | [Linxi "Jim" Fan](https://research.nvidia.com/labs/gear/)（Group lead）、[Yuke Zhu](https://research.nvidia.com/labs/gear/)（Group lead） |
| 官方入口 | [home](https://research.nvidia.com/labs/gear/) · [publications](https://research.nvidia.com/labs/gear/publications/) · [projects](https://research.nvidia.com/labs/gear/projects/) |
| 官方自述方向 | [D1 · 具身基础模型与通才策略](/frontiers/foundation-models)、[D2 · 分层推理、规划与记忆](/frontiers/reasoning-planning)、[D3 · 世界模型与预测控制](/frontiers/world-models)、[D4 · 灵巧、双臂与接触操作](/frontiers/dexterous-manipulation)、[D5 · 人形、运动与全身控制](/frontiers/humanoid-whole-body)、[D8 · 策略学习与优化](/frontiers/policy-learning)、[D9 · 数据引擎与人类视频学习](/frontiers/data-engines)、[D10 · 仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer)、[D13 · 持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) |
| 雷达问题映射 | [Q0 · 人类先验—交互表征—动作—失败回流能否形成闭环](/questions/#q0)、[Q2 · Ego／人类视频到可执行机器人动作](/questions/#q2)、[Q4 · 真实接触与仿真扩增的最优组合](/questions/#q4)、[Q5 · 站位、视角、支撑与操作的联合 loco-manipulation](/questions/#q5)、[Q6 · 可跨任务复用的 post-training recipe](/questions/#q6)、[Q7 · 失败边界数据与低人力纠正闭环](/questions/#q7)、[Q8 · 模型、数采设备与机器人硬件共设计](/questions/#q8)、[Q9 · 机器人模型、数据与交互的 scaling law](/questions/#q9)、[Q10 · 决策相关世界模型与自动评测闭环（Physical RSI 观察项）](/questions/#q10) |
| 披露水平 | high |

## 本周新增（2026-W36）

| 日期 | 动态 | 类型 | 为什么重要 |
|---|---|---|---|
| — | 本周无可升级信号 | — | 官方来源未发现新的 G1/G2 更新。 |

## 最近 12 个月与前一窗口

| 当前 12 个月更新 | 前一 12 个月更新 | 已关联 work | 严格评审 work | 最新实质变化 |
|---:|---:|---:|---:|---|
| 5 | 0 | 5 | 1 | 2026-06-30 |

**观察到的方向：** [D1 · 具身基础模型与通才策略](/frontiers/foundation-models)、[D2 · 分层推理、规划与记忆](/frontiers/reasoning-planning)、[D3 · 世界模型与预测控制](/frontiers/world-models)、[D4 · 灵巧、双臂与接触操作](/frontiers/dexterous-manipulation)、[D5 · 人形、运动与全身控制](/frontiers/humanoid-whole-body)、[D8 · 策略学习与优化](/frontiers/policy-learning)、[D9 · 数据引擎与人类视频学习](/frontiers/data-engines)、[D10 · 仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer)、[D13 · 持续学习、部署学习与自改进](/frontiers/continual-deployment-learning)

**观察到的问题轴：** [Q0 · 人类先验—交互表征—动作—失败回流能否形成闭环](/questions/#q0)、[Q2 · Ego／人类视频到可执行机器人动作](/questions/#q2)、[Q4 · 真实接触与仿真扩增的最优组合](/questions/#q4)、[Q5 · 站位、视角、支撑与操作的联合 loco-manipulation](/questions/#q5)、[Q6 · 可跨任务复用的 post-training recipe](/questions/#q6)、[Q7 · 失败边界数据与低人力纠正闭环](/questions/#q7)、[Q8 · 模型、数采设备与机器人硬件共设计](/questions/#q8)、[Q9 · 机器人模型、数据与交互的 scaling law](/questions/#q9)、[Q10 · 决策相关世界模型与自动评测闭环（Physical RSI 观察项）](/questions/#q10)

## 研究与发布动态

| 日期 | 类型 | 工作/项目 | 评审状态 | 归属证据 | 方向 | 摘要 |
|---|---|---|---|---|---|---|
| 2026-06-30 | 预印本 | [ASPIRE: Agentic /Skills Discovery for Robotics](https://research.nvidia.com/labs/gear/aspire/) | 未严格同行评审 | G1 直接证据 | [D2 · 分层推理、规划与记忆](/frontiers/reasoning-planning)、[D8 · 策略学习与优化](/frontiers/policy-learning)、[D13 · 持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | ASPIRE 官方项目页明确感谢 GEAR、LeCAR 与 AUTOLAB 的支持，体现 agentic skill discovery 的跨组协作。 |
| 2026-06-18 | 预印本 | [ENPIRE: Agentic Robot Policy Self-Improvement in the Real World](https://research.nvidia.com/labs/gear/enpire/) | 未严格同行评审 | G1 直接证据 | [D4 · 灵巧、双臂与接触操作](/frontiers/dexterous-manipulation)、[D8 · 策略学习与优化](/frontiers/policy-learning)、[D13 · 持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | ENPIRE 由 NVIDIA GEAR、CMU LeCAR 与 UC Berkeley 团队共同完成，建立真机策略自改进闭环。 |
| 2026-02-19 | 预印本 | [EgoScale: Scaling Human Video to Unlock Dexterous Robot Intelligence](https://research.nvidia.com/labs/gear/egoscale/) | 未严格同行评审 | G1 直接证据 | [D1 · 具身基础模型与通才策略](/frontiers/foundation-models)、[D4 · 灵巧、双臂与接触操作](/frontiers/dexterous-manipulation)、[D9 · 数据引擎与人类视频学习](/frontiers/data-engines) | 以超过 2 万小时第一视角人类视频预训练灵巧 VLA，并报告人类视频规模与验证损失之间的近似对数线性关系。 |
| 2026-02-06 | 预印本 | [DreamDojo: A Generalist Robot World Model from Large-Scale Human Videos](https://research.nvidia.com/labs/gear/publications/) | 未严格同行评审 | G2 时间对齐重建 | [D3 · 世界模型与预测控制](/frontiers/world-models)、[D9 · 数据引擎与人类视频学习](/frontiers/data-engines)、[D10 · 仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | DreamDojo 的官方 GEAR 页面与作者/PI 关系共同支持 GEAR—Berkeley Robot Learning 的时间对齐合作归属。 |
| 2025-11-19 | 同行评审论文 | [VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation](https://research.nvidia.com/labs/gear/publications/) | 已同行评审 | G1 直接证据 | [D5 · 人形、运动与全身控制](/frontiers/humanoid-whole-body)、[D10 · 仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | VIRAL 将 GEAR 的大规模仿真/人形平台与 LeCAR 的学习控制路线结合，用于真实人形 loco-manipulation。 |

## Canonical works 与归属证据

| 工作 | 首次公开 | 严格同行评审 | 归属等级 | 证据 |
|---|---|---|---|---|
| [ASPIRE: Agentic /Skills Discovery for Robotics](https://arxiv.org/abs/2607.00272) | 2026-06-30 | 否 | G1 直接证据 | [归属证据](https://research.nvidia.com/labs/gear/aspire/) |
| [ENPIRE: Agentic Robot Policy Self-Improvement in the Real World](https://arxiv.org/abs/2606.19980) | 2026-06-18 | 否 | G1 直接证据 | [归属证据](https://research.nvidia.com/labs/gear/enpire/) |
| [EgoScale: Scaling Dexterous Manipulation with Diverse Egocentric Human Data](https://arxiv.org/abs/2602.16710) | 2026-02-18 | 否 | G1 直接证据 | [归属证据](https://research.nvidia.com/labs/gear/egoscale/) |
| [DreamDojo: A Generalist Robot World Model from Large-Scale Human Videos](https://arxiv.org/abs/2602.06949) | 2026-02-06 | 否 | G2 时间对齐重建 | [归属证据](https://research.nvidia.com/labs/gear/publications/) |
| [VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation](https://arxiv.org/abs/2511.15200) | 2025-11-19 | 是 | G1 直接证据 | [归属证据](https://research.nvidia.com/labs/gear/publications/) |

## 合作研究组

| 研究组 | 共同 work | 代表合作 |
|---|---:|---|
| [UC Berkeley AUTOLAB](/groups/berkeley-autolab) | 2 | ASPIRE: Agentic /Skills Discovery for Robotics；ENPIRE: Agentic Robot Policy Self-Improvement in the Real World |
| [CMU Learning and Control for Agile Robotics Lab](/groups/cmu-lecar) | 3 | ASPIRE: Agentic /Skills Discovery for Robotics；ENPIRE: Agentic Robot Policy Self-Improvement in the Real World；VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation |
| [UC Berkeley Robot Learning Lab](/groups/berkeley-robot-learning-lab) | 1 | DreamDojo: A Generalist Robot World Model from Large-Scale Human Videos |

## 来源健康与信息缺口

| 来源 | URL | 状态 | 最近成功 | 连续失败 |
|---|---|---|---|---:|
| home | [https://research.nvidia.com/labs/gear/](https://research.nvidia.com/labs/gear/) | healthy | 2026-09-06 | 0 |
| publications | [https://research.nvidia.com/labs/gear/publications/](https://research.nvidia.com/labs/gear/publications/) | healthy | 2026-09-06 | 0 |
| projects | [https://research.nvidia.com/labs/gear/projects/](https://research.nvidia.com/labs/gear/projects/) | healthy | 2026-09-06 | 0 |

- 当前没有影响档案解读的重大来源缺口。
