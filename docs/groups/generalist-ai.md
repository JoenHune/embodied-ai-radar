---
outline: deep
---

# Generalist AI

> 初创前沿观察 · Europe / United Kingdom · **来源状态：healthy** · 最后核验 2026-08-26

以大规模跨任务机器人数据训练通才策略的初创公司，研究重点从 GEN-0/GEN-1 的规模化预训练推进到 GEN-1.5 的少样本快速适配。

| 项目 | 内容 |
|---|---|
| 母机构/上级 | 独立研究组织 |
| 负责人 | 官方未指定单一负责人 |
| 官方入口 | [home](https://generalistai.com/) · [research](https://generalistai.com/blog/research) · [people](https://generalistai.com/about) |
| 官方自述方向 | [D1 · 具身基础模型与通才策略](/frontiers/foundation-models)、[D2 · 分层推理、规划与记忆](/frontiers/reasoning-planning)、[D4 · 灵巧、双臂与接触操作](/frontiers/dexterous-manipulation)、[D8 · 策略学习与优化](/frontiers/policy-learning)、[D9 · 数据引擎与人类视频学习](/frontiers/data-engines)、[D13 · 持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) |
| 雷达问题映射 | [Q0 · 人类先验—交互表征—动作—失败回流能否形成闭环](/questions/#q0)、[Q2 · Ego／人类视频到可执行机器人动作](/questions/#q2)、[Q6 · 可跨任务复用的 post-training recipe](/questions/#q6)、[Q7 · 失败边界数据与低人力纠正闭环](/questions/#q7)、[Q9 · 机器人模型、数据与交互的 scaling law](/questions/#q9) |
| 披露水平 | medium |

## 本周新增（2026-W34）

| 日期 | 动态 | 类型 | 为什么重要 |
|---|---|---|---|
| 2026-08-19 | [GEN-1.5](https://generalistai.com/blog/gen-1.5) | 技术报告 | 公司报告展示 3–12 秒单次示教与少量梯度更新的快速适配；59%/83% 为内部短任务平均成功率，并非独立 benchmark。 |

## 最近 12 个月与前一窗口

| 当前 12 个月更新 | 前一 12 个月更新 | 已关联 work | 严格评审 work | 最新实质变化 |
|---:|---:|---:|---:|---|
| 4 | 0 | 0 | 0 | 2026-08-19 |

**观察到的方向：** [D1 · 具身基础模型与通才策略](/frontiers/foundation-models)、[D2 · 分层推理、规划与记忆](/frontiers/reasoning-planning)、[D4 · 灵巧、双臂与接触操作](/frontiers/dexterous-manipulation)、[D8 · 策略学习与优化](/frontiers/policy-learning)、[D9 · 数据引擎与人类视频学习](/frontiers/data-engines)、[D13 · 持续学习、部署学习与自改进](/frontiers/continual-deployment-learning)、[D10 · 仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer)

**观察到的问题轴：** [Q0 · 人类先验—交互表征—动作—失败回流能否形成闭环](/questions/#q0)、[Q2 · Ego／人类视频到可执行机器人动作](/questions/#q2)、[Q6 · 可跨任务复用的 post-training recipe](/questions/#q6)、[Q7 · 失败边界数据与低人力纠正闭环](/questions/#q7)、[Q9 · 机器人模型、数据与交互的 scaling law](/questions/#q9)、[Q8 · 模型、数采设备与机器人硬件共设计](/questions/#q8)

## 研究与发布动态

| 日期 | 类型 | 工作/项目 | 评审状态 | 归属证据 | 方向 | 摘要 |
|---|---|---|---|---|---|---|
| 2026-08-19 | 技术报告 | [GEN-1.5](https://generalistai.com/blog/gen-1.5) | 未同行评审·公司自报 | G1 直接证据 | [D1 · 具身基础模型与通才策略](/frontiers/foundation-models)、[D2 · 分层推理、规划与记忆](/frontiers/reasoning-planning)、[D8 · 策略学习与优化](/frontiers/policy-learning)、[D13 · 持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 公司报告展示 3–12 秒单次示教与少量梯度更新的快速适配；59%/83% 为内部短任务平均成功率，并非独立 benchmark。 |
| 2026-07-23 | 技术报告 | [Towards Machines with a Thousand Hands](https://generalistai.com/blog/towards-machines-with-a-thousand-hands) | 未同行评审·公司自报 | G1 直接证据 | [D1 · 具身基础模型与通才策略](/frontiers/foundation-models)、[D9 · 数据引擎与人类视频学习](/frontiers/data-engines)、[D10 · 仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 公司报告研究约 9,000 种生成式末端执行器变化下的跨形态学习；该数字不是 9,000 款实体商业机械手。 |
| 2026-04-02 | 技术报告 | [GEN-1](https://generalistai.com/blog/gen-1) | 未同行评审·公司自报 | G1 直接证据 | [D1 · 具身基础模型与通才策略](/frontiers/foundation-models)、[D8 · 策略学习与优化](/frontiers/policy-learning)、[D9 · 数据引擎与人类视频学习](/frontiers/data-engines)、[D13 · 持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 公司报告将数据规模扩展到超过 50 万小时，并报告约一小时任务数据的内部适配实验；性能比例只适用于其自定义任务集。 |
| 2025-11-04 | 技术报告 | [GEN-0](https://generalistai.com/blog/gen-0) | 未同行评审·公司自报 | G1 直接证据 | [D1 · 具身基础模型与通才策略](/frontiers/foundation-models)、[D8 · 策略学习与优化](/frontiers/policy-learning)、[D9 · 数据引擎与人类视频学习](/frontiers/data-engines) | 公司报告披露 10B+ 参数通才机器人策略和超过 27 万小时数据的内部扩展结果；未提供同行评审或独立复现。 |
| 日期待核 | 项目 | [Towards Machines with a Thousand Hands Robots aren't locked into the hands they're born with. GEN-1 now supports a broad range of end effectors, showing how a single model can transfer across radically different ways of interacting with the physical world. 5 min read July 23, 2026](https://generalistai.com/blog/towards-machines-with-a-thousand-hands) | 未严格同行评审 | G1 直接证据 | — | 官方来源页面新发现的链接，等待结构化归类。 |
| 日期待核 | 项目 | [The Robots Build Now, Too One-shot assembly is one of our new internal evaluation tasks: you build a small Lego structure, place it in front of the robot, and the robot builds copies of it. 3 min read September 24, 2025](https://generalistai.com/blog/the-robots-build-now-too) | 未严格同行评审 | G1 直接证据 | — | 官方来源页面新发现的链接，等待结构化归类。 |
| 日期待核 | 项目 | [Research Preview A glimpse of what we're building at Generalist — end-to-end neural networks for dexterous sensorimotor policies across different embodiments, environments, and physical interactions. 3 min read June 17, 2025](https://generalistai.com/blog/research-preview) | 未严格同行评审 | G1 直接证据 | — | 官方来源页面新发现的链接，等待结构化归类。 |
| 日期待核 | 项目 | [Research](https://generalistai.com/blog/research) | 未严格同行评审 | G1 直接证据 | — | 官方来源页面新发现的链接，等待结构化归类。 |
| 日期待核 | 项目 | [GEN-1.5 / Embodied Foundation Models are One-Shot Learners GEN-1.5 can in-context learn a new task from as little as 12 seconds of demonstration data — or adapt with 1 to 10 gradient steps on minutes of data. These capabilities emerge from pretraining on large-scale physical experience. 17 min read August 19, 2026 GEN- 1.5](https://generalistai.com/blog/gen-1.5) | 未严格同行评审 | G1 直接证据 | — | 官方来源页面新发现的链接，等待结构化归类。 |
| 日期待核 | 项目 | [GEN-1 / Scaling Embodied Foundation Models to Mastery We've created GEN-1 , our latest milestone in scaling robot learning — the first general-purpose AI model that crosses a new performance threshold: mastery of simple physical tasks. 14 min read April 2, 2026](https://generalistai.com/blog/gen-1) | 未严格同行评审 | G1 直接证据 | — | 官方来源页面新发现的链接，等待结构化归类。 |
| 日期待核 | 项目 | [GEN-0 / Embodied Foundation Models That Scale with Physical Interaction We're introducing GEN-0 , a new class of embodied foundation models built for multimodal training directly on high-fidelity raw physical interaction. 12 min read November 4, 2025](https://generalistai.com/blog/gen-0) | 未严格同行评审 | G1 直接证据 | — | 官方来源页面新发现的链接，等待结构化归类。 |

## Canonical works 与归属证据

| 工作 | 首次公开 | 严格同行评审 | 归属等级 | 证据 |
|---|---|---|---|---|
| — | — | — | — | — |

## 合作研究组

| 研究组 | 共同 work | 代表合作 |
|---|---:|---|
| — | — | 暂无多组 G1/G2 共同 work |

## 来源健康与信息缺口

| 来源 | URL | 状态 | 最近成功 | 连续失败 |
|---|---|---|---|---:|
| home | [https://generalistai.com/](https://generalistai.com/) | healthy | 2026-08-26 | 0 |
| people | [https://generalistai.com/about](https://generalistai.com/about) | healthy | 2026-08-26 | 0 |
| research | [https://generalistai.com/blog/research](https://generalistai.com/blog/research) | healthy | 2026-08-26 | 0 |

- 尚无 canonical work 归属边；当前档案主要依赖官方项目更新。
