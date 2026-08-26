---
outline: deep
---

# CMU Learning and Control for Agile Robotics Lab

> 学术实验室/PI 组 · North America / United States · **来源状态：healthy** · 最后核验 2026-08-26

研究学习与控制交叉，重点关注具身智能的敏捷性、可靠性、自适应性与真实系统部署。

| 项目 | 内容 |
|---|---|
| 母机构/上级 | CMU Robotics Institute |
| 负责人 | [Guanya Shi](https://www.ri.cmu.edu/robotics-groups/lecar-lab/)（Lab Head） |
| 官方入口 | [home](https://www.ri.cmu.edu/robotics-groups/lecar-lab/) · [publications](https://lecar-lab.github.io/) |
| 官方自述方向 | [D5 · 人形、运动与全身控制](/frontiers/humanoid-whole-body)、[D8 · 策略学习与优化](/frontiers/policy-learning)、[D10 · 仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer)、[D12 · 评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) |
| 雷达问题映射 | [Q4 · 真实接触与仿真扩增的最优组合](/questions/#q4)、[Q5 · 站位、视角、支撑与操作的联合 loco-manipulation](/questions/#q5)、[Q6 · 可跨任务复用的 post-training recipe](/questions/#q6)、[Q7 · 失败边界数据与低人力纠正闭环](/questions/#q7) |
| 披露水平 | high |

## 本周新增（2026-W34）

| 日期 | 动态 | 类型 | 为什么重要 |
|---|---|---|---|
| — | 本周无可升级信号 | — | 官方来源未发现新的 G1/G2 更新。 |

## 最近 12 个月与前一窗口

| 当前 12 个月更新 | 前一 12 个月更新 | 已关联 work | 严格评审 work | 最新实质变化 |
|---:|---:|---:|---:|---|
| 3 | 1 | 4 | 2 | 2026-06-30 |

**观察到的方向：** [D5 · 人形、运动与全身控制](/frontiers/humanoid-whole-body)、[D8 · 策略学习与优化](/frontiers/policy-learning)、[D10 · 仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer)、[D12 · 评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation)、[D2 · 分层推理、规划与记忆](/frontiers/reasoning-planning)、[D13 · 持续学习、部署学习与自改进](/frontiers/continual-deployment-learning)、[D4 · 灵巧、双臂与接触操作](/frontiers/dexterous-manipulation)、[D9 · 数据引擎与人类视频学习](/frontiers/data-engines)

**观察到的问题轴：** [Q4 · 真实接触与仿真扩增的最优组合](/questions/#q4)、[Q5 · 站位、视角、支撑与操作的联合 loco-manipulation](/questions/#q5)、[Q6 · 可跨任务复用的 post-training recipe](/questions/#q6)、[Q7 · 失败边界数据与低人力纠正闭环](/questions/#q7)、[Q0 · 人类先验—交互表征—动作—失败回流能否形成闭环](/questions/#q0)

## 研究与发布动态

| 日期 | 类型 | 工作/项目 | 证据 | 方向 | 摘要 |
|---|---|---|---|---|---|
| 2026-06-30 | 预印本 | [ASPIRE: Agentic /Skills Discovery for Robotics](https://research.nvidia.com/labs/gear/aspire/) | G1 直接证据 | [D2 · 分层推理、规划与记忆](/frontiers/reasoning-planning)、[D8 · 策略学习与优化](/frontiers/policy-learning)、[D13 · 持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | ASPIRE 官方项目页明确感谢 GEAR、LeCAR 与 AUTOLAB 的支持，体现 agentic skill discovery 的跨组协作。 |
| 2026-06-18 | 预印本 | [ENPIRE: Agentic Robot Policy Self-Improvement in the Real World](https://research.nvidia.com/labs/gear/enpire/) | G1 直接证据 | [D4 · 灵巧、双臂与接触操作](/frontiers/dexterous-manipulation)、[D8 · 策略学习与优化](/frontiers/policy-learning)、[D13 · 持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | ENPIRE 由 NVIDIA GEAR、CMU LeCAR 与 UC Berkeley 团队共同完成，建立真机策略自改进闭环。 |
| 2025-11-19 | 同行评审论文 | [VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation](https://research.nvidia.com/labs/gear/publications/) | G1 直接证据 | [D5 · 人形、运动与全身控制](/frontiers/humanoid-whole-body)、[D10 · 仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | VIRAL 将 GEAR 的大规模仿真/人形平台与 LeCAR 的学习控制路线结合，用于真实人形 loco-manipulation。 |
| 2025-04-14 | 同行评审论文 | [Flying Hand: End-Effector-Centric Framework for Versatile Aerial Manipulation Teleoperation and Policy Learning](https://lecar-lab.github.io/flying_hand/) | G1 直接证据 | [D4 · 灵巧、双臂与接触操作](/frontiers/dexterous-manipulation)、[D8 · 策略学习与优化](/frontiers/policy-learning)、[D9 · 数据引擎与人类视频学习](/frontiers/data-engines) | 以末端执行器为中心统一空中操作的遥操作、全身控制与策略学习，并在 RSS 2025 通过同行评审。 |

## Canonical works 与归属证据

| 工作 | 首次公开 | 严格同行评审 | 归属等级 | 证据 |
|---|---|---|---|---|
| [ASPIRE: Agentic /Skills Discovery for Robotics](https://arxiv.org/abs/2607.00272) | 2026-06-30 | 否 | G1 直接证据 | [归属证据](https://research.nvidia.com/labs/gear/aspire/) |
| [ENPIRE: Agentic Robot Policy Self-Improvement in the Real World](https://arxiv.org/abs/2606.19980) | 2026-06-18 | 否 | G1 直接证据 | [归属证据](https://research.nvidia.com/labs/gear/enpire/) |
| [VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation](https://arxiv.org/abs/2511.15200) | 2025-11-19 | 是 | G1 直接证据 | [归属证据](https://research.nvidia.com/labs/gear/publications/) |
| [Flying Hand: End-Effector-Centric Framework for Versatile Aerial Manipulation Teleoperation and Policy Learning](https://arxiv.org/abs/2504.10334) | 2025-04-14 | 是 | G1 直接证据 | [归属证据](https://lecar-lab.github.io/flying_hand/) |

## 合作研究组

| 研究组 | 共同 work | 代表合作 |
|---|---:|---|
| [UC Berkeley AUTOLAB](/groups/berkeley-autolab) | 2 | ASPIRE: Agentic /Skills Discovery for Robotics；ENPIRE: Agentic Robot Policy Self-Improvement in the Real World |
| [NVIDIA GEAR](/groups/nvidia-gear) | 3 | ASPIRE: Agentic /Skills Discovery for Robotics；ENPIRE: Agentic Robot Policy Self-Improvement in the Real World；VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation |

## 来源健康与信息缺口

| 来源 | URL | 状态 | 最近成功 | 连续失败 |
|---|---|---|---|---:|
| home | [https://www.ri.cmu.edu/robotics-groups/lecar-lab/](https://www.ri.cmu.edu/robotics-groups/lecar-lab/) | healthy | 2026-08-26 | 0 |
| publications | [https://lecar-lab.github.io/](https://lecar-lab.github.io/) | healthy | 2026-08-26 | 0 |

- 当前没有影响档案解读的重大来源缺口。
