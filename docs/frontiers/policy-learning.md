---
outline: deep
---

# D8 · 策略学习与优化

> v2 层级：learning_and_infrastructure。当前 canonical works 3869 条；此页是扩展分类试运行，不直接改写旧五类历史序列。

## 纳入边界

核心表达：`robot learning`、`imitation learning`、`reinforcement learning`、`diffusion policy`、`flow policy`、`flow matching policy`、`behavior cloning`、`behaviour cloning`、`offline reinforcement`、`online reinforcement`、`visuomotor policy`、`manipulation policy`、`skill learning`、`policy distillation`、`policy optimization`、`cross-embodiment`、`cross embodiment`、`cross-robot`、`multi-robot learning`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`manipulation`、`embodied`、`policy`、`control`、`locomotion`。

## 月度结构与环比

| 月份 | 本月 | 对比月 | 上月 | 环比增量 | 环比 |
|---|---:|---|---:|---:|---:|
| 2024-07 | 64 | — | 0 | +64 | 新增 |
| 2024-08 | 51 | 2024-07 | 64 | -13 | -20.3% |
| 2024-09 | 80 | 2024-08 | 51 | +29 | +56.9% |
| 2024-10 | 87 | 2024-09 | 80 | +7 | +8.8% |
| 2024-11 | 58 | 2024-10 | 87 | -29 | -33.3% |
| 2024-12 | 55 | 2024-11 | 58 | -3 | -5.2% |
| 2025-01 | 41 | 2024-12 | 55 | -14 | -25.5% |
| 2025-02 | 81 | 2025-01 | 41 | +40 | +97.6% |
| 2025-03 | 121 | 2025-02 | 81 | +40 | +49.4% |
| 2025-04 | 63 | 2025-03 | 121 | -58 | -47.9% |
| 2025-05 | 130 | 2025-04 | 63 | +67 | +106.3% |
| 2025-06 | 82 | 2025-05 | 130 | -48 | -36.9% |
| 2025-07 | 72 | 2025-06 | 82 | -10 | -12.2% |
| 2025-08 | 66 | 2025-07 | 72 | -6 | -8.3% |
| 2025-09 | 124 | 2025-08 | 66 | +58 | +87.9% |
| 2025-10 | 105 | 2025-09 | 124 | -19 | -15.3% |
| 2025-11 | 87 | 2025-10 | 105 | -18 | -17.1% |
| 2025-12 | 75 | 2025-11 | 87 | -12 | -13.8% |
| 2026-01 | 72 | 2025-12 | 75 | -3 | -4.0% |
| 2026-02 | 91 | 2026-01 | 72 | +19 | +26.4% |
| 2026-03 | 157 | 2026-02 | 91 | +66 | +72.5% |
| 2026-04 | 89 | 2026-03 | 157 | -68 | -43.3% |
| 2026-05 | 138 | 2026-04 | 89 | +49 | +55.1% |
| 2026-06 | 141 | 2026-05 | 138 | +3 | +2.2% |
| 2026-07 | 102 | 2026-06 | 141 | -39 | -27.7% |

## 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [Don't Start From Scratch: Behavioral Refinement via Interpolant-based Policy Diffusion](https://arxiv.org/abs/2402.16075) | — | RSS 2024、RSS 2024 | 是 | — |
| [Safe & Accurate at Speed with Tendons: A Robot Arm for Exploring Dynamic Motion](https://arxiv.org/abs/2307.02654) | — | RSS 2024、RSS 2024 | 是 | — |
| [Developing Design Guidelines for Older Adults with Robot Learning from Demonstration](https://doi.org/10.15607/rss.2024.xx.030) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [3D Diffusion Policy: Generalizable Visuomotor Policy Learning via Simple 3D Representations](https://doi.org/10.15607/rss.2024.xx.067) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [A Dual Approach to Imitation Learning from Observations with Offline Datasets](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Action-Free Reasoning for Policy Generalization](https://arxiv.org/abs/2502.03729) | 2025-02-06 | CoRL 2025 | 是 | — |
| [Adapt3R: Adaptive 3D Scene Representation for Domain Transfer in Imitation Learning](https://arxiv.org/abs/2503.04877) | 2025-03-06 | CoRL 2025 | 是 | — |
| [Adapting by Analogy: OOD Generalization of Visuomotor Policies via Functional Correspondence](https://arxiv.org/abs/2506.12678) | 2025-06-15 | CoRL 2025 | 是 | — |
| [Adaptive Diffusion Terrain Generator for Autonomous Uneven Terrain Navigation](https://arxiv.org/abs/2410.10766) | 2024-10-14 | CoRL 2024、CoRL 2024 | 是 | — |
| [Adaptive Language-Guided Abstraction from Contrastive Explanations](https://arxiv.org/abs/2409.08212) | 2024-09-12 | CoRL 2024、CoRL 2024 | 是 | — |
| [Agreement Volatility: A Second-Order Metric for Uncertainty Quantification in Surgical Robot Learning](https://proceedings.mlr.press/v305/thompson25a.html) | 2025-10-07 | CoRL 2025 | 是 | — |
| [AirExo-2: Scaling up Generalizable Robotic Imitation Learning with Low-Cost Exoskeletons](https://arxiv.org/abs/2503.03081) | 2025-03-05 | CoRL 2025 | 是 | — |
| [ArticuBot: Learning Universal Articulated Object Manipulation Policy via Large Scale Simulation](https://arxiv.org/abs/2503.03045) | 2025-03-04 | RSS 2025 | 是 | — |
| [ATK: Automatic Task-driven Keypoint Selection for Robust Policy Learning](https://arxiv.org/abs/2506.13867) | 2025-06-16 | CoRL 2025 | 是 | — |
| [AtomicVLA: Unlocking the Potential of Atomic Skill Learning in Robots](https://arxiv.org/abs/2603.07648) | 2026-03-08 | CVPR 2026 | 是 | — |
| [Autonomous Improvement of Instruction Following Skills via Foundation Models](https://arxiv.org/abs/2407.20635) | 2024-07-30 | CoRL 2024、CoRL 2024 | 是 | — |
| [BiGym: A Demo-Driven Mobile Bi-Manual Manipulation Benchmark](https://arxiv.org/abs/2407.07788) | 2024-07-10 | CoRL 2024、CoRL 2024 | 是 | — |
| [Body Transformer: Leveraging Robot Embodiment for Policy Learning](https://arxiv.org/abs/2408.06316) | 2024-08-12 | CoRL 2024、CoRL 2024 | 是 | — |
| [Bootstrapping Reinforcement Learning with Imitation for Vision-Based Agile Flight](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Bridging the gap between Learning-to-plan, Motion Primitives and Safe Reinforcement Learning](https://arxiv.org/abs/2408.14063) | 2024-08-26 | CoRL 2024、CoRL 2024 | 是 | — |
| [CaRL: Learning Scalable Planning Policies with Simple Rewards](https://arxiv.org/abs/2504.17838) | 2025-04-24 | CoRL 2025 | 是 | — |
| [CDP: Towards Robust Autoregressive Visuomotor Policy Learning via Causal Diffusion](https://arxiv.org/abs/2506.14769) | 2025-06-17 | CoRL 2025 | 是 | — |
| [CLASS: Contrastive Learning via Action Sequence Supervision for Robot Manipulation](https://arxiv.org/abs/2508.01600) | 2025-08-03 | CoRL 2025 | 是 | — |
| [CLIP-RT: Learning Language-Conditioned Robotic Policies from Natural Language Supervision](https://arxiv.org/abs/2411.00508) | 2024-11-01 | RSS 2025 | 是 | — |
| [ClutterGen: A Cluttered Scene Generator for Robot Learning](https://arxiv.org/abs/2407.05425) | 2024-07-07 | CoRL 2024、CoRL 2024 | 是 | — |
| [CodeDiffuser: Attention-Enhanced Diffusion Policy via VLM-Generated Code for Instruction Ambiguity](https://arxiv.org/abs/2506.16652) | 2025-06-19 | RSS 2025 | 是 | — |
| [COLLAGE: Adaptive Fusion-based Retrieval for Augmented Policy Learning](https://arxiv.org/abs/2508.01131) | 2025-08-02 | CoRL 2025 | 是 | — |
| [ComposableNav: Instruction-Following Navigation in Dynamic Environments via Composable Diffusion](https://arxiv.org/abs/2509.17941) | 2025-09-22 | CoRL 2025 | 是 | — |
| [Constraint-Preserving Data Generation for One-Shot Visuomotor Policy Generalization](https://proceedings.mlr.press/v305/lin25b.html) | 2025-10-07 | CoRL 2025 | 是 | — |
| [Continuous Control with Coarse-to-fine Reinforcement Learning](https://arxiv.org/abs/2407.07787) | 2024-07-10 | CoRL 2024、CoRL 2024 | 是 | — |
| [Contrastive Imitation Learning for Language-guided Multi-Task Robotic Manipulation](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Crossing the Human-Robot Embodiment Gap with Sim-to-Real RL using One Human Demonstration](https://arxiv.org/abs/2504.12609) | 2025-04-17 | CoRL 2025 | 是 | — |
| [CtRL-Sim: Reactive and Controllable Driving Agents with Offline Reinforcement Learning](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Curating Demonstrations using Online Experience](https://arxiv.org/abs/2503.03707) | 2025-03-05 | RSS 2025 | 是 | — |
| [Data Retrieval with Importance Weights for Few-Shot Imitation Learning](https://arxiv.org/abs/2509.01657) | 2025-09-01 | CoRL 2025 | 是 | — |
| [Decentralized Aerial Manipulation of a Cable-Suspended Load using Multi-Agent Reinforcement Learning](https://arxiv.org/abs/2508.01522) | 2025-08-02 | CoRL 2025 | 是 | — |
| [DemoGen: Synthetic Demonstration Generation for Data-Efficient Visuomotor Policy Learning](https://arxiv.org/abs/2502.16932) | 2025-02-24 | RSS 2025 | 是 | — |
| [Demonstrating LEAP Hand v2: Low-Cost, Easy-to-Assemble, High-Performance Hand for Robot Learning](https://www.roboticsproceedings.org/rss21/p132.html) | 2025-06-21 | RSS 2025 | 是 | — |
| [DemoSpeedup: Accelerating Visuomotor Policies via Entropy-Guided Demonstration Acceleration](https://arxiv.org/abs/2506.05064) | 2025-06-05 | CoRL 2025 | 是 | — |
| [DexVLA: Vision-Language Model with Plug-In Diffusion Expert for General Robot Control](https://arxiv.org/abs/2502.05855) | 2025-02-09 | CoRL 2025 | 是 | — |
| [Divide, Discover, Deploy: Factorized Skill Learning with Symmetry and Style Priors](https://arxiv.org/abs/2508.19953) | 2025-08-27 | CoRL 2025 | 是 | — |
| [DiWA: Diffusion Policy Adaptation with World Models](https://arxiv.org/abs/2508.03645) | 2025-08-05 | CoRL 2025 | 是 | — |
| [Dreamitate: Real-World Visuomotor Policy Learning via Video Generation](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Dynamic Rank Adjustment in Diffusion Policies for Efficient and Flexible Training](https://arxiv.org/abs/2502.03822) | 2025-02-06 | RSS 2025 | 是 | — |
| [Enhancing Visual Domain Robustness in Behaviour Cloning via Saliency-Guided Augmentation](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [EquiBot: SIM(3)-Equivariant Diffusion Policy for Generalizable and Data Efficient Learning](https://arxiv.org/abs/2407.01479) | 2024-07-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Equivariant Diffusion Policy](https://arxiv.org/abs/2407.01812) | 2024-07-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [EXTRACT: Efficient Policy Learning by Extracting Transferable Robot Skills from Offline Data](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Fast Flow-based Visuomotor Policies via Conditional Optimal Transport Couplings](https://arxiv.org/abs/2505.01179) | 2025-05-02 | CoRL 2025 | 是 | — |
| [FastUMI: A Scalable and Hardware-Independent Universal Manipulation Interface with Dataset](https://arxiv.org/abs/2409.19499) | 2024-09-29 | CoRL 2025 | 是 | — |
| [Few-Shot Neuro-Symbolic Imitation Learning for Long-Horizon Planning and Acting](https://arxiv.org/abs/2508.21501) | 2025-08-29 | CoRL 2025 | 是 | — |
| [FLARE: Robot Learning with Implicit World Modeling](https://arxiv.org/abs/2505.15659) | 2025-05-21 | CoRL 2025 | 是 | — |
| [FlowRetrieval: Flow-Guided Data Retrieval for Few-Shot Imitation Learning](https://arxiv.org/abs/2408.16944) | 2024-08-29 | CoRL 2024、CoRL 2024 | 是 | — |
| [GenDP: 3D Semantic Fields for Category-Level Generalizable Diffusion Policy](https://arxiv.org/abs/2410.17488) | 2024-10-23 | CoRL 2024、CoRL 2024 | 是 | — |
| [General Flow as Foundation Affordance for Scalable Robot Learning](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Genetic Algorithm for Curriculum Design in Multi-Agent Reinforcement Learning](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Goal-Reaching Policy Learning from Non-Expert Observations via Effective Subgoal Guidance](https://arxiv.org/abs/2409.03996) | 2024-09-06 | CoRL 2024、CoRL 2024 | 是 | — |
| [HACMan++: Spatially-Grounded Motion Primitives for Manipulation](https://arxiv.org/abs/2407.08585) | 2024-07-11 | RSS 2024、RSS 2024 | 是 | — |
| [Handling Long-Term Safety and Uncertainty in Safe Reinforcement Learning](https://arxiv.org/abs/2409.12045) | 2024-09-18 | CoRL 2024、CoRL 2024 | 是 | — |
| [Imitation Bootstrapped Reinforcement Learning](https://doi.org/10.15607/rss.2024.xx.056) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
