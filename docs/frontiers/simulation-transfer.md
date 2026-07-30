---
outline: deep
---

# D10 · 仿真、合成数据与 Sim-to-Real

> v2 层级：learning_and_infrastructure。当前 canonical works 701 条；此页是扩展分类试运行，不直接改写旧五类历史序列。

## 纳入边界

核心表达：`sim-to-real`、`sim2real`、`simulation-to-reality`、`simulation to reality`、`synthetic robot data`、`robot simulation`、`robotics simulator`、`digital twin`、`domain randomization`、`procedural generation`、`synthetic demonstration`、`simulation data`、`physics simulator`、`neural simulator`、`generative simulator`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`manipulation`、`embodied`、`policy`、`control`、`simulation`。

## 月度结构与环比

| 月份 | 本月 | 对比月 | 上月 | 环比增量 | 环比 |
|---|---:|---|---:|---:|---:|
| 2024-07 | 5 | — | 0 | +5 | 新增 |
| 2024-08 | 2 | 2024-07 | 5 | -3 | -60.0% |
| 2024-09 | 10 | 2024-08 | 2 | +8 | +400.0% |
| 2024-10 | 17 | 2024-09 | 10 | +7 | +70.0% |
| 2024-11 | 16 | 2024-10 | 17 | -1 | -5.9% |
| 2024-12 | 5 | 2024-11 | 16 | -11 | -68.8% |
| 2025-01 | 5 | 2024-12 | 5 | 0 | 0.0% |
| 2025-02 | 14 | 2025-01 | 5 | +9 | +180.0% |
| 2025-03 | 14 | 2025-02 | 14 | 0 | 0.0% |
| 2025-04 | 11 | 2025-03 | 14 | -3 | -21.4% |
| 2025-05 | 16 | 2025-04 | 11 | +5 | +45.5% |
| 2025-06 | 12 | 2025-05 | 16 | -4 | -25.0% |
| 2025-07 | 9 | 2025-06 | 12 | -3 | -25.0% |
| 2025-08 | 12 | 2025-07 | 9 | +3 | +33.3% |
| 2025-09 | 17 | 2025-08 | 12 | +5 | +41.7% |
| 2025-10 | 13 | 2025-09 | 17 | -4 | -23.5% |
| 2025-11 | 13 | 2025-10 | 13 | 0 | 0.0% |
| 2025-12 | 7 | 2025-11 | 13 | -6 | -46.2% |
| 2026-01 | 14 | 2025-12 | 7 | +7 | +100.0% |
| 2026-02 | 13 | 2026-01 | 14 | -1 | -7.1% |
| 2026-03 | 23 | 2026-02 | 13 | +10 | +76.9% |
| 2026-04 | 10 | 2026-03 | 23 | -13 | -56.5% |
| 2026-05 | 15 | 2026-04 | 10 | +5 | +50.0% |
| 2026-06 | 27 | 2026-05 | 15 | +12 | +80.0% |
| 2026-07 | 14 | 2026-06 | 27 | -13 | -48.1% |

## 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [Automated Creation of Digital Cousins for Robust Policy Learning](https://arxiv.org/abs/2410.07408) | 2024-10-09 | CoRL 2024、CoRL 2024 | 是 | — |
| [Bridging the Sim-to-Real Gap for Athletic Loco-Manipulation](https://arxiv.org/abs/2502.10894) | 2025-02-15 | RSS 2025 | 是 | — |
| [Bridging the Sim-to-Real Gap from the Information Bottleneck Perspective](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Demonstrating CavePI: Autonomous Exploration of Underwater Caves by Semantic Guidance](https://arxiv.org/abs/2502.05384) | 2025-02-07 | RSS 2025 | 是 | — |
| [Demonstrating GPU Parallelized Robot Simulation and Rendering for Generalizable Embodied AI with ManiSkill3](https://www.roboticsproceedings.org/rss21/p021.html) | 2025-06-21 | RSS 2025 | 是 | — |
| [Demonstrating ViSafe: Vision-enabled Safety for High-speed Detect and Avoid](https://arxiv.org/abs/2505.03694) | 2025-05-06 | RSS 2025 | 是 | — |
| [DrEureka: Language Model Guided Sim-To-Real Transfer](https://doi.org/10.15607/rss.2024.xx.094) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [FetchBot: Learning Generalizable Object Fetching in Cluttered Scenes via Zero-Shot Sim2Real](https://arxiv.org/abs/2502.17894) | 2025-02-25 | CoRL 2025 | 是 | — |
| [Function Based Sim-to-Real Learning for Shape Control of Deformable Free-form Surfaces](https://doi.org/10.15607/rss.2024.xx.098) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Monocular Event-Based Vision for Obstacle Avoidance with a Quadrotor](https://arxiv.org/abs/2411.03303) | 2024-11-05 | CoRL 2024、CoRL 2024 | 是 | — |
| [Natural Language Can Help Bridge the Sim2Real Gap](https://doi.org/10.15607/rss.2024.xx.126) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Neural Robot Dynamics](https://arxiv.org/abs/2508.15755) | 2025-08-21 | CoRL 2025 | 是 | — |
| [Novel Demonstration Generation with Gaussian Splatting Enables Robust One-Shot Manipulation](https://arxiv.org/abs/2504.13175) | 2025-04-17 | RSS 2025 | 是 | — |
| [One View, Many Worlds: Single-Image to 3D Object Meets Generative Domain Randomization for One-Shot 6D Pose Estimation](https://arxiv.org/abs/2509.07978) | 2025-09-09 | CoRL 2025 | 是 | — |
| [Real-to-Sim Grasp: Rethinking the Gap between Simulation and Real World in Grasp Detection](https://arxiv.org/abs/2410.06521) | 2024-10-09 | CoRL 2024、CoRL 2024 | 是 | — |
| [Reconciling Reality through Simulation: A Real-To-Sim-to-Real Approach for Robust Manipulation](https://doi.org/10.15607/rss.2024.xx.015) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [ScissorBot: Learning Generalizable Scissor Skill for Paper Cutting via Simulation, Imitation, and Sim2Real](https://arxiv.org/abs/2409.13966) | 2024-09-21 | CoRL 2024、CoRL 2024 | 是 | — |
| [Sim-to-Real Transfer via 3D Feature Fields for Vision-and-Language Navigation](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [SimShear: Sim-to-Real Shear-based Tactile Servoing](https://arxiv.org/abs/2508.20561) | 2025-08-28 | CoRL 2025 | 是 | — |
| [The Sound of Simulation: Learning Multimodal Sim-to-Real Robot Policies with Generative Audio](https://arxiv.org/abs/2507.02864) | 2025-07-03 | CoRL 2025 | 是 | — |
| [TieBot: Learning to Knot a Tie from Visual Demonstration through a Real-to-Sim-to-Real Approach](https://arxiv.org/abs/2407.03245) | 2024-07-03 | CoRL 2024、CoRL 2024 | 是 | — |
| [V-HOP: Visuo-Haptic 6D Object Pose Tracking](https://arxiv.org/abs/2502.17434) | 2025-02-24 | RSS 2025 | 是 | — |
| [Wheeled Lab: Modern Sim2Real for Low-cost, Open-source Wheeled Robotics](https://arxiv.org/abs/2502.07380) | 2025-02-11 | CoRL 2025 | 是 | — |
| [ViPlanner: Visual Semantic Imperative Learning for Local Navigation](https://arxiv.org/abs/2310.00982) | — | ICRA 2024 | 否 | — |
| [SplatSim: Zero-Shot Sim2Real Transfer of RGB Manipulation Policies Using Gaussian Splatting](https://arxiv.org/abs/2409.10161) | 2024-09-16 | ICRA 2025 | 否 | — |
| [LIV-GaussMap: LiDAR-Inertial-Visual Fusion for Real-Time 3D Radiance Field Map Rendering](https://arxiv.org/abs/2401.14857) | — | RA-L 2024 | 否 | — |
| [Learning to Fly in Seconds](https://arxiv.org/abs/2311.13081) | — | RA-L 2024 | 否 | — |
| [Achieving Human Level Competitive Robot Table Tennis](https://arxiv.org/abs/2408.03906) | 2024-08-07 | ICRA 2025 | 否 | — |
| [Sim-to-Real of Soft Robots With Learned Residual Physics](https://arxiv.org/abs/2402.01086) | — | RA-L 2024 | 否 | — |
| [Local Policies Enable Zero-shot Long-horizon Manipulation](https://arxiv.org/abs/2410.22332) | 2024-10-29 | ICRA 2025 | 否 | — |
| [S2R-ViT for Multi-Agent Cooperative Perception: Bridging the Gap from Simulation to Reality](https://arxiv.org/abs/2307.07935) | — | ICRA 2024 | 否 | — |
| [DiffusionNOCS: Managing Symmetry and Uncertainty in Sim2Real Multi-Modal Category-level Pose Estimation](https://arxiv.org/abs/2402.12647) | — | IROS 2024 | 否 | — |
| [Domain Randomization for Sim2real Transfer of Automatically Generated Grasping Datasets](https://arxiv.org/abs/2310.04517) | — | ICRA 2024 | 否 | — |
| [Bridging the Sim-to-Real Gap with Dynamic Compliance Tuning for Industrial Insertion](https://arxiv.org/abs/2311.07499) | — | ICRA 2024 | 否 | — |
| [CoFRIDA: Self-Supervised Fine-Tuning for Human-Robot Co-Painting](https://arxiv.org/abs/2402.13442) | — | ICRA 2024 | 否 | — |
| [RflyMAD: A dataset for multicopter fault detection and health assessment](https://arxiv.org/abs/2311.11340) | — | IJRR 2025 | 否 | — |
| [ZISVFM: Zero-Shot Object Instance Segmentation in Indoor Robotic Environments with Vision Foundation Models](https://arxiv.org/abs/2502.03266) | 2025-02-05 | T-RO 2025 | 否 | — |
| [ASGrasp: Generalizable Transparent Object Reconstruction and 6-DoF Grasp Detection from RGB-D Active Stereo Camera](https://arxiv.org/abs/2405.05648) | — | ICRA 2024 | 否 | — |
| [OmniLRS: A Photorealistic Simulator for Lunar Robotics](https://arxiv.org/abs/2309.08997) | — | ICRA 2024 | 否 | — |
| [DISCOVERSE: Efficient Robot Simulation in Complex High-Fidelity Environments](https://arxiv.org/abs/2507.21981) | 2025-07-29 | IROS 2025 | 否 | — |
| [Dynamics as Prompts: In-Context Learning for Sim-to-Real System Identifications](https://arxiv.org/abs/2410.20357) | 2024-10-27 | RA-L 2025 | 否 | — |
| [Learning on the Fly: Rapid Policy Adaptation via Differentiable Simulation](https://arxiv.org/abs/2508.21065) | 2025-08-28 | RA-L 2026、ICRA 2026 | 否 | — |
| [Close the Sim2real Gap via Physically-based Structured Light Synthetic Data Simulation](https://arxiv.org/abs/2407.12449) | 2024-07-17 | ICRA 2024 | 否 | — |
| [Sim-to-real transfer of adaptive control parameters for AUV stabilisation under current disturbance](https://arxiv.org/abs/2310.11075) | — | IJRR 2024 | 否 | — |
| [What Matters in Learning A Zero-Shot Sim-to-Real RL Policy for Quadrotor Control? A Comprehensive Study](https://arxiv.org/abs/2412.11764) | 2024-12-16 | RA-L 2025、ICRA 2026 | 否 | — |
| [Soft Synergies: Model Order Reduction of Hybrid Soft-Rigid Robots via Optimal Strain Parameterization](https://arxiv.org/abs/2405.12959) | — | T-RO 2025 | 否 | — |
| [PINN-Ray: A Physics-Informed Neural Network to Model Soft Robotic Fin Ray Fingers](https://arxiv.org/abs/2407.08222) | 2024-07-11 | IROS 2024 | 否 | — |
| [Continual Domain Randomization](https://arxiv.org/abs/2403.12193) | — | IROS 2024 | 否 | — |
| [TactGen: Tactile Sensory Data Generation via Zero-Shot Sim-to-Real Transfer](https://ieeexplore.ieee.org/document/3521967) | 2025-01-01 | T-RO 2025 | 否 | — |
| [GS-SDF: LiDAR-Augmented Gaussian Splatting and Neural SDF for Geometrically Consistent Rendering and Reconstruction](https://arxiv.org/abs/2503.10170) | 2025-03-13 | IROS 2025 | 否 | — |
| [One Net to Rule Them All: Domain Randomization in Quadcopter Racing Across Different Platforms](https://arxiv.org/abs/2504.21586) | 2025-04-30 | ICRA 2025 | 否 | — |
| [Bridging the Sim-to-Real Gap with Bayesian Inference](https://arxiv.org/abs/2403.16644) | — | IROS 2024 | 否 | — |
| [CNS: Correspondence Encoded Neural Image Servo Policy](https://arxiv.org/abs/2309.09047) | — | ICRA 2024 | 否 | — |
| [High-Fidelity Simulated Data Generation for Real-World Zero-Shot Robotic Manipulation Learning with Gaussian Splatting](https://arxiv.org/abs/2510.10637) | 2025-10-12 | RA-L 2026 | 否 | — |
| [Learn to Navigate in Dynamic Environments with Normalized LiDAR Scans](https://ieeexplore.ieee.org/document/10611247) | 2024-05-13 | ICRA 2024 | 否 | — |
| [RPMArt: Towards Robust Perception and Manipulation for Articulated Objects](https://arxiv.org/abs/2403.16023) | — | IROS 2024 | 否 | — |
| [Aim My Robot: Precision Local Navigation to Any Object](https://arxiv.org/abs/2411.14770) | 2024-11-22 | RA-L 2025 | 否 | — |
| [Robotic Object Insertion with a Soft Wrist through Sim-to-Real Privileged Training](https://arxiv.org/abs/2408.17061) | 2024-08-30 | IROS 2024 | 否 | — |
| [Sim2Real Bilevel Adaptation for Object Surface Classification using Vision-Based Tactile Sensors](https://arxiv.org/abs/2311.01380) | — | ICRA 2024 | 否 | — |
| [PolyFit: A Peg-in-hole Assembly Framework for Unseen Polygon Shapes via Sim-to-real Adaptation](https://arxiv.org/abs/2312.02531) | — | IROS 2024 | 否 | — |
