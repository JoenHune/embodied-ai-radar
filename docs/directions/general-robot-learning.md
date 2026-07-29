---
outline: deep
---

# 通用机器人学习

> 覆盖跨任务/本体迁移、人类视频学习、模仿与强化学习、diffusion/flow policy 和数据规模化，是其他四类方法落地的共同训练底座。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>495</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>265</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>4</strong><span>官方评审锚点</span></div>
  <div class="radar-kpi"><strong>26.9%</strong><span>主分析期占比</span></div>
</div>

## 跨月演进

- 2024–2025 H1：diffusion/flow policy、latent action 和大规模机器人数据确立通用训练底座。
- 2025 H2：无标签视频、数据编辑、合成数据和跨本体 diffusion 扩大非机器人监督。
- 2026 Q1：egocentric 人类数据与在线/离线 RL 开始补足接触和经验学习。
- 2026 Q2：开放数据—训练—评测栈与 human-as-humanoid 指向共享表示 + 本体适配器。

| 月份 | 候选数 | 相对热度 |
|---|---:|---|
| 2025-07 | 23 | ███ |
| 2025-08 | 29 | ████ |
| 2025-09 | 42 | ██████ |
| 2025-10 | 37 | █████ |
| 2025-11 | 31 | █████ |
| 2025-12 | 34 | █████ |
| 2026-01 | 26 | ████ |
| 2026-02 | 44 | ██████ |
| 2026-03 | 63 | █████████ |
| 2026-04 | 36 | █████ |
| 2026-05 | 48 | ███████ |
| 2026-06 | 82 | ████████████ |

## 技术路线对比

| 路线 | 核心表示/机制 | 优势 | 当前局限 |
|---|---|---|---|
| Imitation / behavior cloning | 从示范直接学习 | 稳定、工程成熟 | 分布外恢复弱 |
| Diffusion / flow policy | 生成多峰动作分布 | 精细连续控制 | 推理时延与反馈修正 |
| Offline / online RL | 用奖励改进策略 | 能从失败和部署经验学习 | 奖励、安全与样本成本 |
| 人类视频 / 跨本体 | 共享视觉—动作或接触表征 | 数据规模大、迁移潜力高 | 动力学与动作空间不一致 |

## 代表工作

| 论文 | v1 月份 | 状态 | 一句话贡献 |
|---|---|---|---|
| [UniVLA: Learning to Act Anywhere with Task-centric Latent Actions](https://arxiv.org/abs/2505.06111) | 2025-05 | [RSS 2025](https://www.roboticsproceedings.org/rss21/p014.html) | A generalist robot should perform effectively across various environments |
| [EC-Flow: Enabling Versatile Robotic Manipulation from Action-Unlabeled Videos via Embodiment-Centric Flow](https://arxiv.org/abs/2507.06224) | 2025-07 | arXiv | 从无动作标签视频预测 embodiment-centric flow，再借 URDF 约束转成可执行动作，覆盖遮挡、柔性物体及非位移操作。 |
| [H-RDT: Human Manipulation Enhanced Bimanual Robotic Manipulation](https://arxiv.org/abs/2507.23523) | 2025-07 | arXiv | 以 2B diffusion transformer 先学大规模第一视角人类手部先验，再用模块化动作编解码器适配不同机器人，显著提升双臂真实操作。 |
| [X-Diffusion: Training Diffusion Policies on Cross-Embodiment Human Demonstrations](https://arxiv.org/abs/2511.04671) | 2025-11 | arXiv | X-Diffusion 将人类动作视为机器人动作的噪声对应物，只在高噪声层引入跨本体人类示范，五个真实任务平均提升 16%。 |
| [RoboWheel: A Data Engine from Real-World Human Demonstrations for Cross-Embodiment Robotic Learning](https://arxiv.org/abs/2512.02729) | 2025-12 | arXiv | RoboWheel 将单目/RGB-D 人类手物视频重建为物理可行接触轨迹，再重定向到夹爪、灵巧手和人形本体并做仿真扩增。 |
| [Being-H0.5: Scaling Human-Centric Robot Learning for Cross-Embodiment Generalization](https://arxiv.org/abs/2601.12993) | 2026-01 | arXiv | 以 35,000 小时、30 种本体的 UniHand-2.0 和统一动作空间训练人类中心 VLA，并用 Mixture-of-Flow 分离共享运动原语与本体专家。 |
| [EgoScale: Scaling Dexterous Manipulation with Diverse Egocentric Human Data](https://arxiv.org/abs/2602.16710) | 2026-02 | arXiv | 在 20,854 小时动作标注第一视角人类视频上建立 scaling law，并以轻量 human-robot mid-training 迁移到 22-DoF 灵巧手。 |
| [Scalable Behavior Cloning with Open Data, Training, and Evaluation](https://arxiv.org/abs/2606.27375) | 2026-06 | arXiv | 发布 3,500 小时、130K episodes、195 任务的 ABC-130K，以及硬件、训练、仿真和真实评测全栈。 |
| [Human-as-Humanoid: Enabling Zero-Shot Humanoid Learning from Ego-Exo Human Videos with Human-Aligned Embodiments](https://arxiv.org/abs/2606.32009) | 2026-06 | arXiv | 通过 ego-exo 同步、60-DoF 动作重定向和 FK-aware supervision，把人类视频转成可直接训练 humanoid VLA 的动作标签。 |

## 同行评审锚点

| 工作 | Venue | arXiv |
|---|---|---|
| [HumanPlus: Humanoid Shadowing and Imitation from Humans](https://proceedings.mlr.press/v270/fu25a.html) | CoRL 2024 | [2406.10454](https://arxiv.org/abs/2406.10454) |
| [ConRFT: A Reinforced Fine-tuning Method for VLA Models via Consistency Policy](https://www.roboticsproceedings.org/rss21/p019.html) | RSS 2025 | [2502.05450](https://arxiv.org/abs/2502.05450) |
| [Robot Learning with Super-Linear Scaling](https://www.roboticsproceedings.org/rss21/p025.html) | RSS 2025 | [2412.01770](https://arxiv.org/abs/2412.01770) |
| [VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/He_VIRAL_Visual_Sim-to-Real_at_Scale_for_Humanoid_Loco-Manipulation_CVPR_2026_paper.html) | CVPR 2026 | [2511.15200](https://arxiv.org/abs/2511.15200) |

## 成熟度、瓶颈与战略判断

**成熟度。** 方法工具链最成熟，但跨本体、长时序和开放世界的同时成立仍少见。

**关键瓶颈。**

- 数据有效多样性
- 失败与修正数据
- 动作空间标准
- 在线学习安全
- 统一评测

**战略判断。** 长期价值更可能来自可持续数据飞轮、跨本体接口和开放训练基础设施，而不是单一 policy 名称。

<!-- 更新标记：通用机器人学习 最后更新 2026.07 -->
