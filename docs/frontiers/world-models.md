---
outline: deep
---

# D3 · 世界模型与预测控制

> v2 层级：model_and_system。当前 canonical works 987 条；此页是扩展分类试运行，不直接改写旧五类历史序列。

## 纳入边界

核心表达：`world model`、`action-conditioned video`、`action conditioned video`、`robot video prediction`、`latent action`、`predictive dynamics`、`dynamics model`、`model-based planning`、`model based planning`、`generative simulation`、`video prediction for robot`、`future prediction`、`action-conditioned generation`、`action conditioned generation`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`manipulation`、`action`、`control`、`policy`、`planning`、`interaction`、`embodied`、`dynamics`。

## 月度结构与环比

| 月份 | 本月 | 对比月 | 上月 | 环比增量 | 环比 |
|---|---:|---|---:|---:|---:|
| 2024-07 | 6 | — | 0 | +6 | 新增 |
| 2024-08 | 3 | 2024-07 | 6 | -3 | -50.0% |
| 2024-09 | 12 | 2024-08 | 3 | +9 | +300.0% |
| 2024-10 | 17 | 2024-09 | 12 | +5 | +41.7% |
| 2024-11 | 8 | 2024-10 | 17 | -9 | -52.9% |
| 2024-12 | 7 | 2024-11 | 8 | -1 | -12.5% |
| 2025-01 | 4 | 2024-12 | 7 | -3 | -42.9% |
| 2025-02 | 8 | 2025-01 | 4 | +4 | +100.0% |
| 2025-03 | 19 | 2025-02 | 8 | +11 | +137.5% |
| 2025-04 | 11 | 2025-03 | 19 | -8 | -42.1% |
| 2025-05 | 18 | 2025-04 | 11 | +7 | +63.6% |
| 2025-06 | 22 | 2025-05 | 18 | +4 | +22.2% |
| 2025-07 | 11 | 2025-06 | 22 | -11 | -50.0% |
| 2025-08 | 10 | 2025-07 | 11 | -1 | -9.1% |
| 2025-09 | 13 | 2025-08 | 10 | +3 | +30.0% |
| 2025-10 | 25 | 2025-09 | 13 | +12 | +92.3% |
| 2025-11 | 19 | 2025-10 | 25 | -6 | -24.0% |
| 2025-12 | 29 | 2025-11 | 19 | +10 | +52.6% |
| 2026-01 | 21 | 2025-12 | 29 | -8 | -27.6% |
| 2026-02 | 41 | 2026-01 | 21 | +20 | +95.2% |
| 2026-03 | 49 | 2026-02 | 41 | +8 | +19.5% |
| 2026-04 | 32 | 2026-03 | 49 | -17 | -34.7% |
| 2026-05 | 53 | 2026-04 | 32 | +21 | +65.6% |
| 2026-06 | 83 | 2026-05 | 53 | +30 | +56.6% |
| 2026-07 | 47 | 2026-06 | 83 | -36 | -43.4% |

## 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [AdaptiGraph: Material-Adaptive Graph-Based Neural Dynamics for Robotic Manipulation](https://arxiv.org/abs/2407.07889) | 2024-07-10 | RSS 2024、RSS 2024 | 是 | — |
| [Beyond Constant Parameters: Hyper Prediction Models and HyperMPC](https://arxiv.org/abs/2508.06181) | 2025-08-08 | CoRL 2025 | 是 | — |
| [Cloth-Splatting: 3D Cloth State Estimation from RGB Supervision](https://arxiv.org/abs/2501.01715) | 2025-01-03 | CoRL 2024、CoRL 2024 | 是 | — |
| [Diffusion Dynamics Models with Generative State Estimation for Cloth Manipulation](https://arxiv.org/abs/2503.11999) | 2025-03-15 | CoRL 2025 | 是 | — |
| [DreamGen: Unlocking Generalization in Robot Learning through Video World Models](https://arxiv.org/abs/2505.12705) | 2025-05-19 | CoRL 2025 | 是 | [NVIDIA/GR00T-Dreams](https://github.com/NVIDIA/GR00T-Dreams) |
| [Dreaming to Assist: Learning to Align with Human Objectives for Shared Control in High-Speed Racing](https://arxiv.org/abs/2410.10062) | 2024-10-14 | CoRL 2024、CoRL 2024 | 是 | — |
| [Dynamic 3D Gaussian Tracking for Graph-Based Neural Dynamics Modeling](https://arxiv.org/abs/2410.18912) | 2024-10-24 | CoRL 2024、CoRL 2024 | 是 | — |
| [From Foresight to Forethought: VLM-In-the-Loop Policy Steering via Latent Alignment](https://arxiv.org/abs/2502.01828) | 2025-02-03 | RSS 2025 | 是 | — |
| [Generalizing Safety Beyond Collision-Avoidance via Latent-Space Reachability Analysis](https://arxiv.org/abs/2502.00935) | 2025-02-02 | RSS 2025 | 是 | — |
| [LaDi-WM: A Latent Diffusion-based World Model for Predictive Manipulation](https://arxiv.org/abs/2505.11528) | 2025-05-13 | CoRL 2025 | 是 | — |
| [Learned Perceptive Forward Dynamics Model for Safe and Platform-aware Robotic Navigation](https://arxiv.org/abs/2504.19322) | 2025-04-27 | RSS 2025 | 是 | — |
| [Learning Compositional Behaviors from Demonstration and Language](https://arxiv.org/abs/2505.21981) | 2025-05-28 | CoRL 2024、CoRL 2024 | 是 | — |
| [Learning to Act Anywhere with Task-centric Latent Actions](https://www.roboticsproceedings.org/rss21/p014.html) | 2025-06-21 | RSS 2025 | 是 | — |
| [Learning to Walk from Three Minutes of Real-World Data with Semi-structured Dynamics Models](https://arxiv.org/abs/2410.09163) | 2024-10-11 | CoRL 2024、CoRL 2024 | 是 | — |
| [Meta-Learning Online Dynamics Model Adaptation in Off-Road Autonomous Driving](https://arxiv.org/abs/2504.16923) | 2025-04-23 | RSS 2025 | 是 | — |
| [Motus: A Unified Latent Action World Model](https://arxiv.org/abs/2512.13030) | 2025-12-15 | CVPR 2026 | 是 | — |
| [Multi-Task Interactive Robot Fleet Learning with Visual World Models](https://arxiv.org/abs/2410.22689) | 2024-10-30 | CoRL 2024、CoRL 2024 | 是 | — |
| [Particle-Grid Neural Dynamics for Learning Deformable Object Models from RGB-D Videos](https://arxiv.org/abs/2506.15680) | 2025-06-18 | RSS 2025 | 是 | — |
| [ParticleFormer: A 3D Point Cloud World Model for Multi-Object, Multi-Material Robotic Manipulation](https://arxiv.org/abs/2506.23126) | 2025-06-29 | CoRL 2025 | 是 | — |
| [PIN-WM: Learning Physics-INformed World Models for Non-Prehensile Manipulation](https://arxiv.org/abs/2504.16693) | 2025-04-23 | RSS 2025 | 是 | — |
| [PointWorld: Scaling 3D World Models for In-The-Wild Robotic Manipulation](https://arxiv.org/abs/2601.03782) | 2026-01-07 | CVPR 2026 | 是 | — |
| [Prompting with the Future: Open-World Model Predictive Control with Interactive Digital Twins](https://arxiv.org/abs/2506.13761) | 2025-06-16 | RSS 2025 | 是 | — |
| [Rapid Mismatch Estimation via Neural Network Informed Variational Inference](https://arxiv.org/abs/2508.21007) | 2025-08-28 | CoRL 2025 | 是 | — |
| [RoboPack: Learning Tactile-Informed Dynamics Models for Dense Packing](https://arxiv.org/abs/2407.01418) | 2024-07-01 | RSS 2024、RSS 2024 | 是 | — |
| [SLAC: Simulation-Pretrained Latent Action Space for Whole-Body Real-World RL](https://proceedings.mlr.press/v305/hu25b.html) | 2025-10-07 | CoRL 2025 | 是 | — |
| [Unified Video Action Model](https://arxiv.org/abs/2503.00200) | 2025-02-28 | RSS 2025 | 是 | — |
| [Unified World Models: Coupling Video and Action Diffusion for Pretraining on Large Robotic Datasets](https://arxiv.org/abs/2504.02792) | 2025-04-03 | RSS 2025 | 是 | — |
| [VLMPC: Vision-Language Model Predictive Control for Robotic Manipulation](https://arxiv.org/abs/2407.09829) | 2024-07-13 | RSS 2024、RSS 2024 | 是 | — |
| [WoMAP: World Models For Embodied Open-Vocabulary Object Localization](https://arxiv.org/abs/2506.01600) | 2025-06-02 | CoRL 2025 | 是 | — |
| [World Models for General Surgical Grasping](https://doi.org/10.15607/rss.2024.xx.041) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [A review of learning-based dynamics models for robotic manipulation](https://www.science.org/doi/10.1126/scirobotics.adt1497) | 2025-09-17 | Science Robotics 2025 | 否 | — |
| [LidarDM: Generative LiDAR Simulation in a Generated World](https://arxiv.org/abs/2404.02903) | — | ICRA 2025 | 否 | — |
| [WMNav: Integrating Vision-Language Models into World Models for Object Goal Navigation](https://arxiv.org/abs/2503.02247) | 2025-03-04 | IROS 2025 | 否 | — |
| [Renderworld: World Model with Self-Supervised 3D Label](https://arxiv.org/abs/2409.11356) | — | ICRA 2025 | 否 | — |
| [World Model-based Perception for Visual Legged Locomotion](https://arxiv.org/abs/2409.16784) | 2024-09-25 | ICRA 2025 | 否 | — |
| [AnyCar to Anywhere: Learning Universal Dynamics Model for Agile and Adaptive Mobility](https://arxiv.org/abs/2409.15783) | 2024-09-24 | ICRA 2025 | 否 | — |
| [Learning Quadrotor Control From Visual Features Using Differentiable Simulation](https://arxiv.org/abs/2410.15979) | 2024-10-21 | ICRA 2025 | 否 | — |
| [MoDem-V2: Visuo-Motor World Models for Real-World Robot Manipulation](https://arxiv.org/abs/2309.14236) | — | ICRA 2024 | 否 | — |
| [SOUS VIDE: Cooking Visual Drone Navigation Policies in a Gaussian Splatting Vacuum](https://arxiv.org/abs/2412.16346) | 2024-12-20 | RA-L 2025 | 否 | — |
| [Probing Multimodal LLMs as World Models for Driving](https://arxiv.org/abs/2405.05956) | — | RA-L 2025、ICRA 2026 | 否 | — |
| [FlowDreamer: A RGB-D World Model with Flow-based Motion Representations for Robot Manipulation](https://arxiv.org/abs/2505.10075) | 2025-05-15 | RA-L 2026、ICRA 2026 | 否 | — |
| [TWIST: Teacher-Student World Model Distillation for Efficient Sim-to-Real Transfer](https://arxiv.org/abs/2311.03622) | — | ICRA 2024 | 否 | — |
| [X-MOBILITY: End-To-End Generalizable Navigation via World Modeling](https://arxiv.org/abs/2410.17491) | 2024-10-23 | ICRA 2025 | 否 | — |
| [LUMOS: Language-Conditioned Imitation Learning with World Models](https://arxiv.org/abs/2503.10370) | 2025-03-13 | ICRA 2025 | 否 | — |
| [Point Cloud Models Improve Visual Robustness in Robotic Learners](https://arxiv.org/abs/2404.18926) | — | ICRA 2024 | 否 | — |
| [NEUSIS: A Compositional Neuro-Symbolic Framework for Autonomous Perception, Reasoning, and Planning in Complex UAV Search Missions](https://arxiv.org/abs/2409.10196) | 2024-09-16 | RA-L 2025、ICRA 2026 | 否 | — |
| [Inference-Time Enhancement of Generative Robot Policies via Predictive World Modeling](https://arxiv.org/abs/2502.00622) | 2025-02-02 | RA-L 2026 | 否 | — |
| [Safe Deep Policy Adaptation](https://arxiv.org/abs/2310.08602) | — | ICRA 2024 | 否 | — |
| [Planning with Adaptive World Models for Autonomous Driving](https://arxiv.org/abs/2406.10714) | — | ICRA 2025 | 否 | — |
| [Geometric Tracking Control of Omnidirectional Multirotors for Aggressive Maneuvers](https://arxiv.org/abs/2209.10024) | — | RA-L 2025 | 否 | — |
| [HortiBot: An Adaptive Multi-Arm System for Robotic Horticulture of Sweet Peppers](https://arxiv.org/abs/2403.15306) | — | IROS 2024 | 否 | — |
| [ManiGaussian++: General Robotic Bimanual Manipulation with Hierarchical Gaussian World Model](https://arxiv.org/abs/2506.19842) | 2025-06-24 | IROS 2025 | 否 | — |
| [R-AIF: Solving Sparse-Reward Robotic Tasks from Pixels with Active Inference and World Models](https://arxiv.org/abs/2409.14216) | 2024-09-21 | ICRA 2025 | 否 | — |
| [Residual Learning towards High-fidelity Vehicle Dynamics Modeling with Transformer](https://arxiv.org/abs/2502.11800) | 2025-02-17 | RA-L 2025 | 否 | — |
| [QT-TDM: Planning With Transformer Dynamics Model and Autoregressive Q-Learning](https://arxiv.org/abs/2407.18841) | — | RA-L 2025 | 否 | — |
| [Risk-Averse Model Predictive Control for Racing in Adverse Conditions](https://arxiv.org/abs/2410.17183) | 2024-10-22 | ICRA 2025 | 否 | — |
| [Learning Coordinated Bimanual Manipulation Policies using State Diffusion and Inverse Dynamics Models](https://arxiv.org/abs/2503.23271) | 2025-03-30 | ICRA 2025 | 否 | — |
| [Learning Multiple Probabilistic Decisions from Latent World Model in Autonomous Driving](https://arxiv.org/abs/2409.15730) | 2024-09-24 | ICRA 2025 | 否 | — |
| [Online Adaptation of Learned Vehicle Dynamics Model with Meta-Learning Approach](https://arxiv.org/abs/2409.14950) | 2024-09-23 | IROS 2024 | 否 | — |
| [Points2Plans: From Point Clouds to Long-Horizon Plans with Composable Relational Dynamics](https://arxiv.org/abs/2408.14769) | 2024-08-27 | ICRA 2025 | 否 | — |
