---
outline: deep
---

# 问题地图：哪些瓶颈正在接近解决

> 本页把 Alphaist 内部研究材料转为雷达的正交“问题层”；公开站点不暴露私有飞书地址。D1–D15 回答论文主要研究什么；Q0–Q10 回答关键系统瓶颈是否正在被解决。两层不能相加，P0/P1/P2 也不等于 A/B/C 证据等级。

::: warning 证据边界
问题来自五份内部材料的综合；本站只把它作为研究假设来源，趋势等级仍由公开论文、同行评审与真机证据决定。 自动计数只是标题/摘要词表命中的相关工作密度，不自动升级趋势；每项判断仍需结合独立团队、真机、正式发表和反证。
:::

## 总判断

飞书文档抓住了一个真实变化：具身智能的领先差异正在从单一模型扩展到**接触表征—可执行动作—运行时验证—失败回流—软硬件迭代**。但其中既有当前主线，也有开放科学问题和工程门槛，不能全部写成“已确认趋势”。

| ID | 战略优先级 | 研究问题 | 证据 | 性质 | D 类映射 | 最近 12 个完整月词表命中 | 2026-08 完整月（已含在 12 月窗口） | 严格评审锚点 |
|---|---|---|---|---|---|---:|---:|---:|
| Q0 | P0 | [人类先验—交互表征—动作—失败回流能否形成闭环](#q0) | <span class="signal signal-b">B</span> | 跨方向系统主线 | [D2](/frontiers/reasoning-planning) / [D9](/frontiers/data-engines) / [D12](/frontiers/safety-evaluation) / [D13](/frontiers/continual-deployment-learning) | 451 | 58 | 2 |
| Q1 | P0 | [接触中心的最小充分交互表征](#q1) | <span class="signal signal-b">B</span> | 新兴研究方向 | [D4](/frontiers/dexterous-manipulation) / [D11](/frontiers/spatial-perception) / [D15](/frontiers/embodied-multisensory) / [D3](/frontiers/world-models) | 141 | 18 | 1 |
| Q2 | P0 | [Ego／人类视频到可执行机器人动作](#q2) | <span class="signal signal-a">A</span> | 当前主线 | [D9](/frontiers/data-engines) / [D8](/frontiers/policy-learning) / [D4](/frontiers/dexterous-manipulation) / [D1](/frontiers/foundation-models) | 551 | 45 | 2 |
| Q3 | P0 | [视觉、力觉与触觉的任务条件化消融](#q3) | <span class="signal signal-b">B</span> | 评测驱动方向 | [D15](/frontiers/embodied-multisensory) / [D4](/frontiers/dexterous-manipulation) / [D12](/frontiers/safety-evaluation) | 293 | 33 | 1 |
| Q4 | P1 | [真实接触与仿真扩增的最优组合](#q4) | <span class="signal signal-a">A</span> | 成熟路线中的未解问题 | [D10](/frontiers/simulation-transfer) / [D3](/frontiers/world-models) / [D4](/frontiers/dexterous-manipulation) | 513 | 32 | 2 |
| Q5 | P0 | [站位、视角、支撑与操作的联合 loco-manipulation](#q5) | <span class="signal signal-b">B</span> | 当前主线中的新兴统一问题 | [D5](/frontiers/humanoid-whole-body) / [D6](/frontiers/navigation-mobile-manipulation) / [D11](/frontiers/spatial-perception) / [D2](/frontiers/reasoning-planning) | 180 | 18 | 2 |
| Q6 | P0 | [可跨任务复用的 post-training recipe](#q6) | <span class="signal signal-b">B</span> | 快速升温方向 | [D8](/frontiers/policy-learning) / [D13](/frontiers/continual-deployment-learning) / [D1](/frontiers/foundation-models) / [D7](/frontiers/human-robot-interaction) | 268 | 29 | 1 |
| Q7 | P0 | [失败边界数据与低人力纠正闭环](#q7) | <span class="signal signal-b">B</span> | 新兴系统主线 | [D13](/frontiers/continual-deployment-learning) / [D12](/frontiers/safety-evaluation) / [D9](/frontiers/data-engines) / [D8](/frontiers/policy-learning) | 117 | 10 | 1 |
| Q8 | P1 | [模型、数采设备与机器人硬件共设计](#q8) | <span class="signal signal-c">C</span> | 早期 co-design 假设 | [D4](/frontiers/dexterous-manipulation) / [D9](/frontiers/data-engines) / [D15](/frontiers/embodied-multisensory) / [D12](/frontiers/safety-evaluation) | 83 | 5 | 1 |
| Q9 | P2 | [机器人模型、数据与交互的 scaling law](#q9) | <span class="signal signal-c">C</span> | 高价值早期假设 | [D1](/frontiers/foundation-models) / [D8](/frontiers/policy-learning) / [D9](/frontiers/data-engines) | 37 | 5 | 1 |
| Q10 | P2 | [决策相关世界模型与自动评测闭环（Physical RSI 观察项）](#q10) | <span class="signal signal-b">B</span> | 方向已成形、终局假设仍早期 | [D3](/frontiers/world-models) / [D12](/frontiers/safety-evaluation) / [D13](/frontiers/continual-deployment-learning) / [D2](/frontiers/reasoning-planning) | 116 | 33 | 1 |

## 最近 12 个完整月问题密度

> 时间窗：2025-09—2026-08。这是多标签高召回代理；同一论文可进入多个 Q，不能用行列合计替代主方向统计。

| 问题轴 | 2025-09 | 2025-10 | 2025-11 | 2025-12 | 2026-01 | 2026-02 | 2026-03 | 2026-04 | 2026-05 | 2026-06 | 2026-07 | 2026-08 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Q0 · 人类先验—交互表征—动作—失败回流能否形成闭环 | 28 | 24 | 16 | 13 | 20 | 31 | 45 | 34 | 58 | 71 | 53 | 58 |
| Q1 · 接触中心的最小充分交互表征 | 8 | 8 | 9 | 2 | 7 | 15 | 18 | 10 | 10 | 22 | 14 | 18 |
| Q2 · Ego／人类视频到可执行机器人动作 | 43 | 37 | 34 | 38 | 29 | 52 | 61 | 31 | 40 | 88 | 53 | 45 |
| Q3 · 视觉、力觉与触觉的任务条件化消融 | 22 | 17 | 11 | 12 | 14 | 30 | 37 | 22 | 22 | 40 | 33 | 33 |
| Q4 · 真实接触与仿真扩增的最优组合 | 50 | 39 | 31 | 23 | 30 | 49 | 55 | 36 | 44 | 77 | 47 | 32 |
| Q5 · 站位、视角、支撑与操作的联合 loco-manipulation | 16 | 10 | 9 | 6 | 6 | 18 | 16 | 13 | 17 | 40 | 11 | 18 |
| Q6 · 可跨任务复用的 post-training recipe | 16 | 18 | 12 | 14 | 13 | 30 | 34 | 13 | 28 | 28 | 33 | 29 |
| Q7 · 失败边界数据与低人力纠正闭环 | 8 | 11 | 3 | 5 | 11 | 6 | 6 | 7 | 11 | 24 | 15 | 10 |
| Q8 · 模型、数采设备与机器人硬件共设计 | 15 | 3 | 5 | 3 | 5 | 2 | 8 | 8 | 4 | 17 | 8 | 5 |
| Q9 · 机器人模型、数据与交互的 scaling law | 1 | 2 | 1 | 0 | 1 | 6 | 4 | 3 | 3 | 6 | 5 | 5 |
| Q10 · 决策相关世界模型与自动评测闭环（Physical RSI 观察项） | 0 | 1 | 1 | 2 | 1 | 1 | 5 | 4 | 10 | 31 | 27 | 33 |

## Q0 · 人类先验—交互表征—动作—失败回流能否形成闭环

**战略优先级：** P0 · **外部证据等级：** <span class="signal signal-b">B</span> · **性质：** 跨方向系统主线

**当前判断。** 领先差异正在从单一 backbone 扩展到感知、可执行动作、运行时验证、失败纠正与再训练的完整闭环；模型结构与系统闭环是共同瓶颈。

**对应主方向。** [D2](/frontiers/reasoning-planning)、[D9](/frontiers/data-engines)、[D12](/frontiers/safety-evaluation)、[D13](/frontiers/continual-deployment-learning)

**公开证据：**

- [Continuously Improving Mobile Manipulation with Autonomous Real-World RL](https://proceedings.mlr.press/v270/mendonca25a.html) — 同行评审 · CoRL 2024
- [Optimal Interactive Learning on the Job via Facility Location Planning](https://www.roboticsproceedings.org/rss21/p087.html) — 同行评审 · RSS 2025
- [Beyond Imitation: Self-Improving Robot Policies via Off-Policy Q-Planning](https://arxiv.org/abs/2608.21204) — 最新信号 · 2026-08

**决定性指标。** 从失败到修复的周期；单位真机小时能力增量；自动复位与无接管时长；跨任务复用和旧技能回归。

**反证条件。** 系统组件只在单一任务内有效，闭环成本高于离线重训，或迭代频繁造成能力回归。

## Q1 · 接触中心的最小充分交互表征

**战略优先级：** P0 · **外部证据等级：** <span class="signal signal-b">B</span> · **性质：** 新兴研究方向

**当前判断。** 对接触敏感任务而言，关节角和末端位姿通常不是充分交互状态；值得学习能够预测接触切换、力、滑移与物体状态转移的 interaction latent，但它尚未成为通用接口标准。

**对应主方向。** [D4](/frontiers/dexterous-manipulation)、[D11](/frontiers/spatial-perception)、[D15](/frontiers/embodied-multisensory)、[D3](/frontiers/world-models)

**公开证据：**

- [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html) — 同行评审 · RSS 2025
- [CEDex: Cross-Embodiment Dexterous Grasp Generation at Scale from Human-like Contact Representations](https://arxiv.org/abs/2509.24661) — 预印本 · 接触表征与跨本体
- [CoToGrasp: Contact-Topology-Conditioned Dexterous Grasp Synthesis via Canonical Workspace Learning](https://arxiv.org/abs/2608.19776) — 最新信号 · 2026-08

**决定性指标。** 跨材质与跨手型成功率；滑移/接触切换预测；峰值力与物体损伤；接触失败恢复率。

**反证条件。** 表征只在单一传感器或单一硬件上有效，或不能改善真实机器人控制与失败预测。

## Q2 · Ego／人类视频到可执行机器人动作

**战略优先级：** P0 · **外部证据等级：** <span class="signal signal-a">A</span> · **性质：** 当前主线

**当前判断。** 人类视频适合学习语义、affordance 与运动先验，但必须经过接触 grounding、动作重建、本体适配和少量真机校准才能形成可执行 action。

**对应主方向。** [D9](/frontiers/data-engines)、[D8](/frontiers/policy-learning)、[D4](/frontiers/dexterous-manipulation)、[D1](/frontiers/foundation-models)

**公开证据：**

- [DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://proceedings.mlr.press/v305/xu25b.html) — 同行评审 · CoRL 2025
- [UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html) — 同行评审 · CVPR 2026
- [LAWM-3D: Learning 3D-Aware Latent Actions from Human Videos for Generalizable Robot World Models](https://arxiv.org/abs/2608.05706) — 最新信号 · 2026-08

**决定性指标。** 目标本体动作可执行率；固定真机数据下的样本效率；跨手型/跨本体适配成本；负迁移与不可行动作率。

**反证条件。** 加入人类视频后只改善视觉表征，却不能在固定真机数据预算下提高最终策略。

## Q3 · 视觉、力觉与触觉的任务条件化消融

**战略优先级：** P0 · **外部证据等级：** <span class="signal signal-b">B</span> · **性质：** 评测驱动方向

**当前判断。** 问题不是触觉是否默认必要，而是不同任务的最小充分观测集合，以及额外模态能否稳定改善接触失败检测与恢复。

**对应主方向。** [D15](/frontiers/embodied-multisensory)、[D4](/frontiers/dexterous-manipulation)、[D12](/frontiers/safety-evaluation)

**公开证据：**

- [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html) — 同行评审 · RSS 2025
- [Demystifying When and Why VLAs Fail in Contact-Rich Tasks and How to Fix Them](https://arxiv.org/abs/2608.01402) — 最新信号 · 约 2,500 次真机 rollout
- [VT-MUSE: Multimodal Unified Sequential Visuotactile Representation Learning for Manipulation](https://arxiv.org/abs/2608.21290) — 最新信号 · 2026-08

**决定性指标。** 同硬件同数据预算的模态消融；跨传感器校准成本；未知材料滑移检测；恢复率与控制频率。

**反证条件。** 触觉增益可被腕部视觉或六维力稳定替代，且额外传感的维护成本高于收益。

## Q4 · 真实接触与仿真扩增的最优组合

**战略优先级：** P1 · **外部证据等级：** <span class="signal signal-a">A</span> · **性质：** 成熟路线中的未解问题

**当前判断。** Sim-to-Real 已是主线；在灵巧接触、柔性物体与多材质任务中，当前通常仍需要真实标定或失败数据，但 VIRAL 等工作也证明部分任务可由 sim-only 零样本落地。真正问题是固定总成本下的 sim／real 配方。

**对应主方向。** [D10](/frontiers/simulation-transfer)、[D3](/frontiers/world-models)、[D4](/frontiers/dexterous-manipulation)

**公开证据：**

- [VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/He_VIRAL_Visual_Sim-to-Real_at_Scale_for_Humanoid_Loco-Manipulation_CVPR_2026_paper.html) — 同行评审 · CVPR 2026
- [ParticleFormer: A 3D Point Cloud World Model for Multi-Object, Multi-Material Robotic Manipulation](https://proceedings.mlr.press/v305/huang25c.html) — 同行评审 · CoRL 2025
- [Tactile Sim2Real without Tactile Simulation via Bottlenecked Latent Reconstruction](https://arxiv.org/abs/2608.15897) — 最新信号 · 2026-08

**决定性指标。** 固定真实数据量的增益；未见材质/形变泛化；仿真资产制作成本；真机纠正小时与总迭代周期。

**反证条件。** 高保真仿真投入无法降低真实数据量或提升未见材质表现。

## Q5 · 站位、视角、支撑与操作的联合 loco-manipulation

**战略优先级：** P0 · **外部证据等级：** <span class="signal signal-b">B</span> · **性质：** 当前主线中的新兴统一问题

**当前判断。** 移动、相机视角与支撑接触应被视为任务动作，与手部操作共同受平衡、碰撞、可达性和信息增益约束。

**对应主方向。** [D5](/frontiers/humanoid-whole-body)、[D6](/frontiers/navigation-mobile-manipulation)、[D11](/frontiers/spatial-perception)、[D2](/frontiers/reasoning-planning)

**公开证据：**

- [VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/He_VIRAL_Visual_Sim-to-Real_at_Scale_for_Humanoid_Loco-Manipulation_CVPR_2026_paper.html) — 同行评审 · CVPR 2026
- [ActiveVLA: Injecting Active Perception into Vision-Language-Action Models for Precise 3D Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_ActiveVLA_Injecting_Active_Perception_into_Vision-Language-Action_Models_for_Precise_3D_CVPR_2026_paper.html) — 同行评审 · CVPR 2026
- [HAF: Adapting Generalist VLAs to Humanoid Whole-Body Loco-manipulation via Hierarchical Action Flow and Spectral Latent RL](https://arxiv.org/abs/2608.16837) — 最新信号 · 2026-08

**决定性指标。** 完整任务成功与连续时长；平衡违例和碰撞；不可行动作率；重站位/主动视角带来的控制收益。

**反证条件。** 联合策略并未优于模块化导航+操作，或无法保持可诊断、安全回滚。

## Q6 · 可跨任务复用的 post-training recipe

**战略优先级：** P0 · **外部证据等级：** <span class="signal signal-b">B</span> · **性质：** 快速升温方向

**当前判断。** BC—DAgger—offline/online RL 的组件并不新，真正问题是同一训练流程能否跨任务复用，并降低接管、奖励工程与旧技能回归成本。

**对应主方向。** [D8](/frontiers/policy-learning)、[D13](/frontiers/continual-deployment-learning)、[D1](/frontiers/foundation-models)、[D7](/frontiers/human-robot-interaction)

**公开证据：**

- [ConRFT: A Reinforced Fine-tuning Method for VLA Models via Consistency Policy](https://www.roboticsproceedings.org/rss21/p019.html) — 同行评审 · RSS 2025
- [AutoIntervene: Calibrated Intervention for Action-Chunking Imitation Learning Policies](https://arxiv.org/abs/2608.07065) — 最新信号 · 部署接管与再训练
- [Efficient Real-World Online Reinforcement Learning for Robot Manipulation via Centralized Training and Critic Decomposition](https://arxiv.org/abs/2608.09730) — 最新信号 · 2026-08

**决定性指标。** 单位接管分钟的成功率增量；奖励工程人时；跨任务 recipe 复用率；旧技能回归与 wall-clock 收敛。

**反证条件。** 每个任务仍需专用奖励、专人盯机和重新设计训练流程。

## Q7 · 失败边界数据与低人力纠正闭环

**战略优先级：** P0 · **外部证据等级：** <span class="signal signal-b">B</span> · **性质：** 新兴系统主线

**当前判断。** 总小时数不能单独反映部署价值；应把失败发现、接管、纠正、重训、回归和重新部署做成可归因的数据飞轮。

**对应主方向。** [D13](/frontiers/continual-deployment-learning)、[D12](/frontiers/safety-evaluation)、[D9](/frontiers/data-engines)、[D8](/frontiers/policy-learning)

**公开证据：**

- [Optimal Interactive Learning on the Job via Facility Location Planning](https://www.roboticsproceedings.org/rss21/p087.html) — 同行评审 · RSS 2025
- [RedFlow: Redirect Failure into Action-Level Corrections for Flow-matching VLA Policy](https://arxiv.org/abs/2607.27782) — 预印本 · 动作级失败纠正
- [FACT: Failure-Aware Causal Training for World-Action Models](https://arxiv.org/abs/2608.10232) — 最新信号 · 失败 rollout 进入因果预测

**决定性指标。** 单位真机小时的有效纠正轨迹；失败类型覆盖率；恢复成功率和接管时间；从失败到修复的可追溯率。

**反证条件。** 失败样本只改善见过的错误，跨任务迁移弱，或回训引发明显旧技能回归。

## Q8 · 模型、数采设备与机器人硬件共设计

**战略优先级：** P1 · **外部证据等级：** <span class="signal signal-c">C</span> · **性质：** 早期 co-design 假设

**当前判断。** 热、背隙、漂移、触觉布局、控制频率、维修周转与采集人因会改变数据分布和可执行动作空间，应进入模型实验的共同设计变量。

**对应主方向。** [D4](/frontiers/dexterous-manipulation)、[D9](/frontiers/data-engines)、[D15](/frontiers/embodied-multisensory)、[D12](/frontiers/safety-evaluation)

**公开证据：**

- [DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://proceedings.mlr.press/v305/xu25b.html) — 同行评审 · 软硬件适配
- [Koala Gripper: Co-designing Robotic Grippers and Data-Capture Devices for Scaling Dexterous Manipulation Learning](https://arxiv.org/abs/2608.20546) — 最新信号 · 机器人与数采设备共设计

**决定性指标。** 跨设备/硬件版本策略迁移；连续运行时间与维护小时；由训练失败驱动的硬件 A/B；同数据预算下的样本效率。

**反证条件。** 硬件修改无法在受控预算下改善学习结果，或历史数据因版本变化不可复用。

## Q9 · 机器人模型、数据与交互的 scaling law

**战略优先级：** P2 · **外部证据等级：** <span class="signal signal-c">C</span> · **性质：** 高价值早期假设

**当前判断。** 扩模收益必须与数据多样性、任务熵、真机交互量、推理延迟和控制频率共同扫描，不能把参数量增长直接解释为通用能力。

**对应主方向。** [D1](/frontiers/foundation-models)、[D8](/frontiers/policy-learning)、[D9](/frontiers/data-engines)

**公开证据：**

- [Robot Learning with Super-Linear Scaling](https://www.roboticsproceedings.org/rss21/p025.html) — 同行评审 · RSS 2025
- [Xiaomi-Robotics-1: Scaling Vision-Language-Action Models with over 100K Hours of Real-World Trajectories](https://arxiv.org/abs/2607.15330) — 预印本 · 大规模真实轨迹

**决定性指标。** 等数据/等算力/等交互量曲线；单位算力和真机小时收益；推理延迟与控制频率；扩模后的 post-training 增量。

**反证条件。** 收益主要由数据或任务覆盖解释，参数规模在受控条件下没有稳定边际收益。

## Q10 · 决策相关世界模型与自动评测闭环（Physical RSI 观察项）

**战略优先级：** P2 · **外部证据等级：** <span class="signal signal-b">B</span> · **性质：** 方向已成形、终局假设仍早期

**当前判断。** 用于闭环决策的世界模型应具备动作条件性、决策相关性和可测控制收益；在线使用还要满足时延预算。Physical RSI 尚不是定义稳定的研究类别，应拆成自动评测、数据回流、策略更新和安全部署四个可验证模块。

**对应主方向。** [D3](/frontiers/world-models)、[D12](/frontiers/safety-evaluation)、[D13](/frontiers/continual-deployment-learning)、[D2](/frontiers/reasoning-planning)

**公开证据：**

- [Unified World Models: Coupling Video and Action Diffusion for Pretraining on Large Robotic Datasets](https://www.roboticsproceedings.org/rss21/p015.html) — 同行评审 · RSS 2025
- [FACT: Failure-Aware Causal Training for World-Action Models](https://arxiv.org/abs/2608.10232) — 最新信号 · 因果、失败感知
- [GAUGE: A Measurement-Grounded Benchmark for Physical Fidelity in Simulation Engines and Video World Models](https://arxiv.org/abs/2608.05948) — 最新信号 · 物理真实性评测

**决定性指标。** 同算力闭环规划增益；失败/接触事件预测；model bias 与实时延迟；自动 evaluator 的准确率和抗 reward hacking。

**反证条件。** 生成质量与控制收益长期弱相关，或模型时延、偏差与评价器漏洞抵消样本效率收益。

## 如何进入月度雷达

1. 月度页继续先报告 D1–D15 的互斥主方向数量。
2. 问题层只报告工作密度、证据升级和反证，不制造第二套互斥 taxonomy。
3. A/B/C 由人工证据判断；自动词表只负责发现候选。
4. 每次更新优先检查决定性指标，而不是论文是否使用同一个热门名称。

[下载问题证据 sidecar](/embodied-ai-radar/research-question-evidence.json)
