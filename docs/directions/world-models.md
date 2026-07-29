---
outline: deep
---

# 世界模型

> 只纳入与动作、交互、规划、控制或机器人数据生成直接相关的预测模型；普通视频生成不计入。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>228</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>70</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>5</strong><span>官方评审锚点</span></div>
  <div class="radar-kpi"><strong>12.4%</strong><span>主分析期占比</span></div>
</div>

## 跨月演进

- 2025 H1：Unified World Models、LaDi-WM、ParticleFormer 为视频—动作联合、latent dynamics 与物理 3D 预测提供同行评审锚点。
- 2025 Q3：world model 主要承担数据生成、适配和 real-to-sim-to-real。
- 2025 Q4：WorldPlanner、Motus、STORM 把搜索、MPC 与 latent action 接入闭环。
- 2026 H1：RL simulator、executable alignment、视触觉预测和视频—动作统一使评价标准转向控制收益。

| 月份 | 候选数 | 相对热度 |
|---|---:|---|
| 2025-07 | 4 | █ |
| 2025-08 | 6 | █ |
| 2025-09 | 12 | ███ |
| 2025-10 | 16 | ████ |
| 2025-11 | 13 | ███ |
| 2025-12 | 16 | ████ |
| 2026-01 | 13 | ███ |
| 2026-02 | 23 | █████ |
| 2026-03 | 23 | █████ |
| 2026-04 | 20 | ████ |
| 2026-05 | 28 | ██████ |
| 2026-06 | 54 | ████████████ |

## 技术路线对比

| 路线 | 核心表示/机制 | 优势 | 当前局限 |
|---|---|---|---|
| 像素 / 视频预测 | 生成未来观测 | 可利用网络视频、可解释 | 计算冗余、动作可执行性弱 |
| latent dynamics | 在紧凑状态空间预测 | 规划高效、易接 policy | 语义丢失、潜变量不可辨识 |
| 3D / 4D 物理模型 | 点云、几何或材质状态预测 | 空间与接触更明确 | 传感与建模成本高 |
| world-action unified | 联合预测视频和动作 | 训练目标统一、可直接控制 | 模型偏差与奖励投机 |

## 代表工作

| 论文 | v1 月份 | 状态 | 一句话贡献 |
|---|---|---|---|
| [Unified World Models: Coupling Video and Action Diffusion for Pretraining on Large Robotic Datasets](https://arxiv.org/abs/2504.02792) | 2025-04 | [RSS 2025](https://www.roboticsproceedings.org/rss21/p015.html) | Imitation learning has emerged as a promising approach towards building generalist robots |
| [LaDi-WM: A Latent Diffusion-based World Model for Predictive Manipulation](https://arxiv.org/abs/2505.11528) | 2025-05 | [CoRL 2025](https://proceedings.mlr.press/v305/huang25a.html) | Predictive manipulation has recently gained considerable attention in the Embodied AI community due to its potential to improve robot policy performance by leveraging predicted states |
| [ParticleFormer: A 3D Point Cloud World Model for Multi-Object, Multi-Material Robotic Manipulation](https://arxiv.org/abs/2506.23126) | 2025-06 | [CoRL 2025](https://proceedings.mlr.press/v305/huang25c.html) | 3D world models (i.e., learning-based 3D dynamics models) offer a promising approach to generalizable robotic manipulation by capturing the underlying physics of environment evolution conditioned on robot actions |
| [WorldPlanner: Monte Carlo Tree Search and MPC with Action-Conditioned Visual World Models](https://arxiv.org/abs/2511.03077) | 2025-11 | arXiv | WorldPlanner 用数小时无结构 play data 学动作条件视频世界模型、动作采样器和可选奖励，再以 MCTS+MPC 在真实机器人上规划。 |
| [Motus: A Unified Latent Action World Model](https://arxiv.org/abs/2512.13030) | 2025-12 | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html) | Motus 用 MoT 统一理解、视频生成和动作专家，并以 optical-flow latent action 支持世界模型、VLA、逆动力学等多种模式。 |
| [WoVR: World Models as Reliable Simulators for Post-Training VLA Policies with RL](https://arxiv.org/abs/2602.13977) | 2026-02 | arXiv | 通过可控动作条件视频模型、关键帧初始化 rollout 和模型—策略共同演化，降低想象滚动的幻觉深度并用于 VLA 的 RL 后训练。 |
| [EVA: Aligning Video World Models with Executable Robot Actions via Inverse Dynamics Rewards](https://arxiv.org/abs/2603.17808) | 2026-03 | arXiv | 把 inverse dynamics model 反用作奖励模型，以速度、加速度、jerk 和本体约束对视频世界模型做可执行性对齐。 |
| [OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2603.19201) | 2026-03 | arXiv | 以 21K+ 轨迹、86 任务的视觉—触觉—动作数据训练双流世界模型，并用 60Hz 触觉反射闭环纠偏。 |
| [Turning Video Models into Generalist Robot Policies](https://arxiv.org/abs/2605.27817) | 2026-05 | arXiv | 保持 video planner 本体无关，仅为各机器人训练基于 Jacobian 的 IDM，形成可替换视频模型的闭环 VERA 路线。 |
| [$τ_0$-WM: A Unified Video-Action World Model for Robotic Manipulation](https://arxiv.org/abs/2606.01027) | 2026-05 | arXiv | 以共享视频 diffusion backbone 统一动作生成、未来视频模拟和进度评分，并在约 27,300 小时混合数据上训练。 |

## 同行评审锚点

| 工作 | Venue | arXiv |
|---|---|---|
| [Unified World Models: Coupling Video and Action Diffusion for Pretraining on Large Robotic Datasets](https://www.roboticsproceedings.org/rss21/p015.html) | RSS 2025 | [2504.02792](https://arxiv.org/abs/2504.02792) |
| [LaDi-WM: A Latent Diffusion-Based World Model for Predictive Manipulation](https://proceedings.mlr.press/v305/huang25a.html) | CoRL 2025 | [2505.11528](https://arxiv.org/abs/2505.11528) |
| [ParticleFormer: A 3D Point Cloud World Model for Multi-Object, Multi-Material Robotic Manipulation](https://proceedings.mlr.press/v305/huang25c.html) | CoRL 2025 | [2506.23126](https://arxiv.org/abs/2506.23126) |
| [Motus: A Unified Latent Action World Model](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html) | CVPR 2026 | [2512.13030](https://arxiv.org/abs/2512.13030) |
| [PointWorld: Scaling 3D World Models for In-The-Wild Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Huang_PointWorld_Scaling_3D_World_Models_for_In-The-Wild_Robotic_Manipulation_CVPR_2026_paper.html) | CVPR 2026 | [2601.03782](https://arxiv.org/abs/2601.03782) |

## 成熟度、瓶颈与战略判断

**成熟度。** 同行评审证据较强，但真实机器人长时闭环仍是分水岭。

**关键瓶颈。**

- 长时 roll-out 漂移
- model bias
- 逆动力学可执行性
- 规划算力
- 真实接触建模

**战略判断。** 把‘是否在同算力下提高真实控制成功率’设为硬门槛，避免把生成质量误判为机器人能力。

<!-- 更新标记：世界模型 最后更新 2026.07 -->
