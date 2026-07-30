---
outline: deep
---

# D2 · 分层推理、规划与记忆

> v2 层级：model_and_system。当前 canonical works 1684 条；此页是扩展分类试运行，不直接改写旧五类历史序列。

## 纳入边界

核心表达：`system 1`、`system 2`、`system-1`、`system-2`、`fast-slow`、`fast slow`、`planner-policy`、`planner policy`、`hierarchical reasoning`、`hierarchical policy`、`high-level planner`、`low-level policy`、`task planning`、`motion planning`、`vlm planner`、`embodied reasoning`、`chain-of-thought`、`chain of thought`、`long-horizon planning`、`long horizon planning`、`robot memory`、`failure recovery`、`test-time adaptation`、`test time adaptation`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`manipulation`、`embodied`、`action`、`policy`、`control`。

## 月度结构与环比

| 月份 | 本月 | 对比月 | 上月 | 环比增量 | 环比 |
|---|---:|---|---:|---:|---:|
| 2024-07 | 11 | — | 0 | +11 | 新增 |
| 2024-08 | 10 | 2024-07 | 11 | -1 | -9.1% |
| 2024-09 | 25 | 2024-08 | 10 | +15 | +150.0% |
| 2024-10 | 31 | 2024-09 | 25 | +6 | +24.0% |
| 2024-11 | 17 | 2024-10 | 31 | -14 | -45.2% |
| 2024-12 | 17 | 2024-11 | 17 | 0 | 0.0% |
| 2025-01 | 9 | 2024-12 | 17 | -8 | -47.1% |
| 2025-02 | 16 | 2025-01 | 9 | +7 | +77.8% |
| 2025-03 | 34 | 2025-02 | 16 | +18 | +112.5% |
| 2025-04 | 25 | 2025-03 | 34 | -9 | -26.5% |
| 2025-05 | 32 | 2025-04 | 25 | +7 | +28.0% |
| 2025-06 | 23 | 2025-05 | 32 | -9 | -28.1% |
| 2025-07 | 21 | 2025-06 | 23 | -2 | -8.7% |
| 2025-08 | 25 | 2025-07 | 21 | +4 | +19.0% |
| 2025-09 | 34 | 2025-08 | 25 | +9 | +36.0% |
| 2025-10 | 29 | 2025-09 | 34 | -5 | -14.7% |
| 2025-11 | 24 | 2025-10 | 29 | -5 | -17.2% |
| 2025-12 | 22 | 2025-11 | 24 | -2 | -8.3% |
| 2026-01 | 15 | 2025-12 | 22 | -7 | -31.8% |
| 2026-02 | 24 | 2026-01 | 15 | +9 | +60.0% |
| 2026-03 | 29 | 2026-02 | 24 | +5 | +20.8% |
| 2026-04 | 20 | 2026-03 | 29 | -9 | -31.0% |
| 2026-05 | 35 | 2026-04 | 20 | +15 | +75.0% |
| 2026-06 | 36 | 2026-05 | 35 | +1 | +2.9% |
| 2026-07 | 31 | 2026-06 | 36 | -5 | -13.9% |

## 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [AutoGPT+P: Affordance-based Task Planning using Large Language Models](https://arxiv.org/abs/2402.10778) | — | RSS 2024、RSS 2024 | 是 | — |
| [Implicit Graph Search for Planning on Graphs of Convex Sets](https://arxiv.org/abs/2410.08909) | 2024-10-11 | RSS 2024、RSS 2024 | 是 | — |
| [Collision-Affording Point Trees: SIMD-Amenable Nearest Neighbors for Fast Motion Planning with Pointclouds](https://doi.org/10.15607/rss.2024.xx.038) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Motion Planning in Foliated Manifolds using Repetition Roadmap](https://doi.org/10.15607/rss.2024.xx.036) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [A biconvex method for minimum-time motion planning through sequences of convex sets](https://arxiv.org/abs/2504.18978) | 2025-04-26 | RSS 2025 | 是 | — |
| [APRICOT: Active Preference Learning and Constraint-Aware Task Planning with LLMs](https://arxiv.org/abs/2410.19656) | 2024-10-25 | CoRL 2024、CoRL 2024 | 是 | — |
| [Articulated Object Estimation in the Wild](https://arxiv.org/abs/2509.01708) | 2025-09-01 | CoRL 2025 | 是 | — |
| [Deep Reactive Policy: Learning Reactive Manipulator Motion Planning for Dynamic Environments](https://arxiv.org/abs/2509.06953) | 2025-09-08 | CoRL 2025 | 是 | — |
| [Differentiable GPU-Parallelized Task and Motion Planning](https://arxiv.org/abs/2411.11833) | 2024-11-18 | RSS 2025 | 是 | — |
| [DiffusionSeeder: Seeding Motion Optimization with Diffusion for Rapid Motion Planning](https://arxiv.org/abs/2410.16727) | 2024-10-22 | CoRL 2024、CoRL 2024 | 是 | — |
| [Distilling Contact Planning for Fast Trajectory Optimization in Robot Air Hockey](https://arxiv.org/abs/2407.03705) | 2024-07-04 | RSS 2025 | 是 | — |
| [Dynamics-Compliant Trajectory Diffusion for Super-Nominal Payload Manipulation](https://arxiv.org/abs/2508.21375) | 2025-08-29 | CoRL 2025 | 是 | — |
| [Effective Sampling for Robot Motion Planning Through the Lens of Lattices](https://arxiv.org/abs/2502.04908) | 2025-02-07 | RSS 2025 | 是 | — |
| [Extracting Visual Plans from Unlabeled Videos via Symbolic Guidance](https://arxiv.org/abs/2505.08444) | 2025-05-13 | CoRL 2025 | 是 | — |
| [Geometric Gait Optimization for Kinodynamic Systems Using a Lie Group Integrator](https://arxiv.org/abs/2504.19072) | 2025-04-27 | RSS 2025 | 是 | — |
| [Hierarchical Temporal Logic Task and Motion Planning for Multi-Robot Systems](https://arxiv.org/abs/2504.18899) | 2025-04-26 | RSS 2025 | 是 | — |
| [I Can Tell What I am Doing: Toward Real-World Natural Language Grounding of Robot Experiences](https://arxiv.org/abs/2411.12960) | 2024-11-20 | CoRL 2024、CoRL 2024 | 是 | — |
| [INTERPRET: Interactive Predicate Learning from Language Feedback for Generalizable Task Planning](https://doi.org/10.15607/rss.2024.xx.034) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Joint Model-based Model-free Diffusion for Planning with Constraints](https://arxiv.org/abs/2509.08775) | 2025-09-10 | CoRL 2025 | 是 | — |
| [KoopMotion: Learning Almost Divergence Free Koopman Flow Fields for Motion Planning](https://arxiv.org/abs/2509.09074) | 2025-09-11 | CoRL 2025 | 是 | — |
| [Language-Augmented Symbolic Planner for Open-World Task Planning](https://arxiv.org/abs/2407.09792) | 2024-07-13 | RSS 2024、RSS 2024 | 是 | — |
| [Language-guided Manipulator Motion Planning with Bounded Task Space](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [ManipBench: Benchmarking Vision-Language Models for Low-Level Robot Manipulation](https://arxiv.org/abs/2505.09698) | 2025-05-14 | CoRL 2025 | 是 | — |
| [Manual2Skill: Learning to Read Manuals and Acquire Robotic Skills for Furniture Assembly Using Vision-Language Models](https://arxiv.org/abs/2502.10090) | 2025-02-14 | RSS 2025 | 是 | — |
| [Meta-Optimization and Program Search using Language Models for Task and Motion Planning](https://arxiv.org/abs/2505.03725) | 2025-05-06 | CoRL 2025 | 是 | — |
| [Multi-agent Reinforcement Learning with Hybrid Action Space for Free Gait Motion Planning of Hexapod Robots](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Multimodal Fused Learning for Solving the Generalized Traveling Salesman Problem in Robotic Task Planning](https://arxiv.org/abs/2506.16931) | 2025-06-20 | CoRL 2025 | 是 | — |
| [NeuralSVCD for Efficient Swept Volume Collision Detection](https://arxiv.org/abs/2509.00499) | 2025-08-30 | CoRL 2025 | 是 | — |
| [NOD-TAMP: Generalizable Long-Horizon Planning with Neural Object Descriptors](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Partially Observable Task and Motion Planning with Uncertainty and Risk Awareness](https://doi.org/10.15607/rss.2024.xx.118) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Planning from Point Clouds over Continuous Actions for Multi-object Rearrangement](https://arxiv.org/abs/2509.04645) | 2025-09-04 | CoRL 2025 | 是 | — |
| [ReasonPlan: Unified Scene Prediction and Decision Reasoning for Closed-loop Autonomous Driving](https://arxiv.org/abs/2505.20024) | 2025-05-26 | CoRL 2025 | 是 | — |
| [Robotic Control via Embodied Chain-of-Thought Reasoning](https://arxiv.org/abs/2407.08693) | 2024-07-11 | CoRL 2024、CoRL 2024 | 是 | — |
| [Search-TTA: A Multimodal Test-Time Adaptation Framework for Visual Search in the Wild](https://arxiv.org/abs/2505.11350) | 2025-05-16 | CoRL 2025 | 是 | — |
| [Subteaming and Adaptive Formation Control for Coordinated Multi-Robot Navigation](https://arxiv.org/abs/2509.16412) | 2025-09-19 | CoRL 2025 | 是 | — |
| [Superfast Configuration-Space Convex Set Computation on GPUs for Online Motion Planning](https://arxiv.org/abs/2504.10783) | 2025-04-15 | RSS 2025 | 是 | — |
| [Train-Once Plan-Anywhere Kinodynamic Motion Planning via Diffusion Trees](https://arxiv.org/abs/2508.21001) | 2025-08-28 | CoRL 2025 | 是 | — |
| [Training Strategies for Efficient Embodied Reasoning](https://arxiv.org/abs/2505.08243) | 2025-05-13 | CoRL 2025 | 是 | — |
| [SMART-LLM: Smart Multi-Agent Robot Task Planning using Large Language Models](https://arxiv.org/abs/2309.10062) | — | IROS 2024 | 否 | — |
| [AutoTAMP: Autoregressive Task and Motion Planning with LLMs as Translators and Checkers](https://arxiv.org/abs/2306.06531) | — | ICRA 2024 | 否 | — |
| [CoPa: General Robotic Manipulation through Spatial Constraints of Parts with Foundation Models](https://arxiv.org/abs/2403.08248) | — | IROS 2024 | 否 | — |
| [ISR-LLM: Iterative Self-Refined Large Language Model for Long-Horizon Sequential Task Planning](https://arxiv.org/abs/2308.13724) | — | ICRA 2024 | 否 | — |
| [GPT-4V(ision) for Robotics: Multimodal Task Planning From Human Demonstration](https://arxiv.org/abs/2311.12015) | — | RA-L 2024 | 否 | — |
| [LLM3: Large Language Model-based Task and Motion Planning with Motion Failure Reasoning](https://arxiv.org/abs/2403.11552) | — | IROS 2024 | 否 | — |
| [Language Models as Zero-Shot Trajectory Generators](https://arxiv.org/abs/2310.11604) | — | RA-L 2024 | 否 | — |
| [Guiding Long-Horizon Task and Motion Planning with Vision Language Models](https://arxiv.org/abs/2410.02193) | 2024-10-03 | ICRA 2025 | 否 | — |
| [CoPAL: Corrective Planning of Robot Actions with Large Language Models](https://arxiv.org/abs/2310.07263) | — | ICRA 2024 | 否 | — |
| [Motions in Microseconds via Vectorized Sampling-Based Planning](https://arxiv.org/abs/2309.14545) | — | ICRA 2024 | 否 | — |
| [Open-Nav: Exploring Zero-Shot Vision-and-Language Navigation in Continuous Environment with Open-Source LLMs](https://arxiv.org/abs/2409.18794) | 2024-09-27 | ICRA 2025 | 否 | — |
| [EDMP: Ensemble-of-costs-guided Diffusion for Motion Planning](https://arxiv.org/abs/2309.11414) | — | ICRA 2024 | 否 | — |
| [Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions](https://arxiv.org/abs/2310.05921) | — | ICRA 2024 | 否 | — |
| [Statler: State-Maintaining Language Models for Embodied Reasoning](https://arxiv.org/abs/2306.17840) | — | ICRA 2024 | 否 | — |
| [Vision-Language Interpreter for Robot Task Planning](https://arxiv.org/abs/2311.00967) | — | ICRA 2024 | 否 | — |
| [Interactive Planning Using Large Language Models for Partially Observable Robotic Tasks](https://arxiv.org/abs/2312.06876) | — | ICRA 2024 | 否 | — |
| [ReplanVLM: Replanning Robotic Tasks with Visual Language Models](https://arxiv.org/abs/2407.21762) | 2024-07-31 | RA-L 2024 | 否 | — |
| [DELTA: Decomposed Efficient Long-Term Robot Task Planning Using Large Language Models](https://arxiv.org/abs/2404.03275) | — | ICRA 2025 | 否 | — |
| [How to Prompt Your Robot: A PromptBook for Manipulation Skills with Code as Policies](https://ieeexplore.ieee.org/document/10610784) | 2024-05-13 | ICRA 2024 | 否 | — |
| [COHERENT: Collaboration of Heterogeneous Multi-Robot System with Large Language Models](https://arxiv.org/abs/2409.15146) | 2024-09-23 | ICRA 2025 | 否 | — |
| [VLM See, Robot Do: Human Demo Video to Robot Action Plan via Vision Language Model](https://arxiv.org/abs/2410.08792) | 2024-10-11 | IROS 2025 | 否 | — |
| [GRID: Scene-Graph-based Instruction-driven Robotic Task Planning](https://arxiv.org/abs/2309.07726) | — | IROS 2024 | 否 | — |
