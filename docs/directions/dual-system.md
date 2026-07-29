---
outline: deep
---

# 大小脑与双系统

> 由慢速语义推理/规划与快速反应控制协同完成任务；本报告也纳入未使用 System 1/2 命名、但实际具备高层意图与低层策略分工的工作。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>25</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>官方评审锚点</span></div>
  <div class="radar-kpi"><strong>1.4%</strong><span>主分析期占比</span></div>
</div>

## 跨月演进

- 2024 H2：Embodied CoT 证明显式中间推理可改善机器人控制。
- 2025 H1：Reactive Diffusion Policy 等工作把 slow–fast 分工落到视觉—触觉控制。
- 2025 H2：VLA-Reasoner、MoTVLA、DualVLA 形成搜索、快慢统一和部分解耦三条路线。
- 2026 H1：Action CoT、异步 coarse-to-fine、连续推理和 3D trace 使接口从语言计划走向可执行中间表示。

| 月份 | 候选数 | 相对热度 |
|---|---:|---|
| 2025-07 | 1 | ███ |
| 2025-08 | 0 | █ |
| 2025-09 | 2 | ██████ |
| 2025-10 | 2 | ██████ |
| 2025-11 | 1 | ███ |
| 2025-12 | 3 | █████████ |
| 2026-01 | 3 | █████████ |
| 2026-02 | 1 | ███ |
| 2026-03 | 4 | ████████████ |
| 2026-04 | 2 | ██████ |
| 2026-05 | 3 | █████████ |
| 2026-06 | 3 | █████████ |

## 技术路线对比

| 路线 | 核心表示/机制 | 优势 | 当前局限 |
|---|---|---|---|
| 显式 planner–policy | VLM/LLM 计划后调用 policy | 模块可替换、易解释 | 计划误差难恢复 |
| 统一 fast–slow 模型 | 共享表征、不同计算路径 | 端到端优化、延迟较低 | 分工是否真实存在难验证 |
| 搜索 / verifier | 生成候选并用模型或奖励验证 | 失败检测与自纠错 | 测试时计算高 |
| 3D trace / latent intent | 中间轨迹或潜意图连接动作 | 更接近几何执行、可跨本体 | 监督获取与接口标准 |

## 代表工作

| 论文 | v1 月份 | 状态 | 一句话贡献 |
|---|---|---|---|
| [Robotic Control via Embodied Chain-of-Thought Reasoning](https://arxiv.org/abs/2407.08693) | 2024-07 | [CoRL 2024](https://proceedings.mlr.press/v270/zawalski25a.html) | A key limitation of learned robot control policies is their inability to generalize outside their training data |
| [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://arxiv.org/abs/2503.02881) | 2025-03 | [RSS 2025](https://www.roboticsproceedings.org/rss21/p052.html) | Humans can accomplish complex contact-rich tasks using vision and touch, with highly reactive capabilities such as fast response to external changes and adaptive control of contact forces; however, this remains challenging for robots |
| [VLA-Reasoner: Empowering Vision-Language-Action Models with Reasoning via Online Monte Carlo Tree Search](https://arxiv.org/abs/2509.22643) | 2025-09 | arXiv | VLA-Reasoner 以世界模型 rollout、KDE 置信采样和 MCTS 为现成 VLA 增加测试时前瞻，在真实长时序任务上纠偏。 |
| [MoTVLA: A Vision-Language-Action Model with Unified Fast-Slow Reasoning](https://arxiv.org/abs/2510.18337) | 2025-10 | arXiv | MoTVLA 让预训练 VLM 承担慢速语义规划、专用 transformer 生成快速运动分解，再驱动 action expert 实时执行。 |
| [DualVLA: Building a Generalizable Embodied Agent via Partial Decoupling of Reasoning and Action](https://arxiv.org/abs/2511.22134) | 2025-11 | arXiv | DualVLA 通过双层数据裁剪与双教师蒸馏缓解推理微调导致的动作退化，并提出按 reasoning/intention/action/alignment 分解的 VLA Score。 |
| [ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://arxiv.org/abs/2601.11404) | 2026-01 | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhong_ACoT-VLA_Action_Chain-of-Thought_for_Vision-Language-Action_Models_CVPR_2026_paper.html) | 把 Chain-of-Thought 直接落在动作空间，以显式粗轨迹和隐式动作先验共同条件化下游动作头，缩短语义推理到连续控制的距离。 |
| [Libra-VLA: Achieving Learning Equilibrium via Asynchronous Coarse-to-Fine Dual-System](https://arxiv.org/abs/2604.24921) | 2026-04 | arXiv | 将宏观离散方向规划和微观连续位姿对齐分给异步双系统，并提出动作分解粒度存在学习均衡点。 |
| [Continuous Reasoning for Vision-Language-Action](https://arxiv.org/abs/2606.00229) | 2026-05 | arXiv | 把可共享、可验证的 Gaussian continuous thoughts 作为 VLA 推理介质，并以教师消费学生 latent 的动作改善来约束推理。 |
| [3D HAMSTER: Bridging Planning and Control in Hierarchical Vision Language Action Models through 3D Trajectory Guidance](https://arxiv.org/abs/2606.31329) | 2026-06 | arXiv | 让高层 VLM 直接输出 metric 3D waypoint，并无缝接入点云低层策略，修正 2D guidance 的深度歧义。 |

## 同行评审锚点

| 工作 | Venue | arXiv |
|---|---|---|
| [Robotic Control via Embodied Chain-of-Thought Reasoning](https://proceedings.mlr.press/v270/zawalski25a.html) | CoRL 2024 | [2407.08693](https://arxiv.org/abs/2407.08693) |
| [ReKep: Spatio-Temporal Reasoning of Relational Keypoint Constraints for Robotic Manipulation](https://proceedings.mlr.press/v270/huang25g.html) | CoRL 2024 | [2409.01652](https://arxiv.org/abs/2409.01652) |
| [Reflective Planning: Vision-Language Models for Multi-Stage Long-Horizon Robotic Manipulation](https://proceedings.mlr.press/v305/feng25b.html) | CoRL 2025 | [2502.16707](https://arxiv.org/abs/2502.16707) |
| [ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Zhong_ACoT-VLA_Action_Chain-of-Thought_for_Vision-Language-Action_Models_CVPR_2026_paper.html) | CVPR 2026 | [2601.11404](https://arxiv.org/abs/2601.11404) |
| [Action-Sketcher: From Reasoning to Action via Visual Sketches for Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Tan_Action-Sketcher_From_Reasoning_to_Action_via_Visual_Sketches_for_Robotic_CVPR_2026_paper.html) | CVPR 2026 | [2601.01618](https://arxiv.org/abs/2601.01618) |
| [AtomicVLA: Unlocking the Potential of Atomic Skill Learning in Robots](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_AtomicVLA_Unlocking_the_Potential_of_Atomic_Skill_Learning_in_Robots_CVPR_2026_paper.html) | CVPR 2026 | [2603.07648](https://arxiv.org/abs/2603.07648) |
| [SIMPACT: Simulation-Enabled Action Planning using Vision-Language Models](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_SIMPACT_Simulation-Enabled_Action_Planning_using_Vision-Language_Models_CVPR_2026_paper.html) | CVPR 2026 | [2512.05955](https://arxiv.org/abs/2512.05955) |

## 成熟度、瓶颈与战略判断

**成熟度。** 架构概念已获得多项同行评审锚点，正在向实时系统和故障恢复迁移。

**关键瓶颈。**

- 何时触发慢推理
- 异步状态陈旧
- 验证器可靠性
- 接口误差传播
- 安全终止

**战略判断。** 真正的机会可能在推理调度、verifier、恢复和中间表示，而不是把两个模型简单串联。

<!-- 更新标记：大小脑与双系统 最后更新 2026.07 -->
