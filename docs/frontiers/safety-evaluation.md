---
outline: deep
---

# D12 · 评测、安全、可靠性与故障恢复

> v2 层级：learning_and_infrastructure。当前 canonical works 409 条；此页是扩展分类试运行，不直接改写旧五类历史序列。

## 纳入边界

核心表达：`robot benchmark`、`robotics benchmark`、`benchmark suite`、`embodied benchmark`、`policy evaluation`、`robot safety`、`safe robot`、`safe reinforcement learning`、`failure detection`、`failure recovery`、`uncertainty estimation`、`out-of-distribution`、`out of distribution`、`robustness evaluation`、`risk-sensitive`、`risk sensitive`、`runtime assurance`、`verification of robot`、`robot reliability`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`manipulation`、`embodied`、`policy`、`control`、`safety`。

## 月度结构与环比

| 月份 | 本月 | 对比月 | 上月 | 环比增量 | 环比 |
|---|---:|---|---:|---:|---:|
| 2024-07 | 2 | — | 0 | +2 | 新增 |
| 2024-08 | 2 | 2024-07 | 2 | 0 | 0.0% |
| 2024-09 | 4 | 2024-08 | 2 | +2 | +100.0% |
| 2024-10 | 4 | 2024-09 | 4 | 0 | 0.0% |
| 2024-11 | 4 | 2024-10 | 4 | 0 | 0.0% |
| 2024-12 | 6 | 2024-11 | 4 | +2 | +50.0% |
| 2025-01 | 3 | 2024-12 | 6 | -3 | -50.0% |
| 2025-02 | 3 | 2025-01 | 3 | 0 | 0.0% |
| 2025-03 | 4 | 2025-02 | 3 | +1 | +33.3% |
| 2025-04 | 3 | 2025-03 | 4 | -1 | -25.0% |
| 2025-05 | 9 | 2025-04 | 3 | +6 | +200.0% |
| 2025-06 | 6 | 2025-05 | 9 | -3 | -33.3% |
| 2025-07 | 2 | 2025-06 | 6 | -4 | -66.7% |
| 2025-08 | 4 | 2025-07 | 2 | +2 | +100.0% |
| 2025-09 | 8 | 2025-08 | 4 | +4 | +100.0% |
| 2025-10 | 11 | 2025-09 | 8 | +3 | +37.5% |
| 2025-11 | 4 | 2025-10 | 11 | -7 | -63.6% |
| 2025-12 | 4 | 2025-11 | 4 | 0 | 0.0% |
| 2026-01 | 1 | 2025-12 | 4 | -3 | -75.0% |
| 2026-02 | 4 | 2026-01 | 1 | +3 | +300.0% |
| 2026-03 | 5 | 2026-02 | 4 | +1 | +25.0% |
| 2026-04 | 4 | 2026-03 | 5 | -1 | -20.0% |
| 2026-05 | 9 | 2026-04 | 4 | +5 | +125.0% |
| 2026-06 | 10 | 2026-05 | 9 | +1 | +11.1% |
| 2026-07 | 5 | 2026-06 | 10 | -5 | -50.0% |

## 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [Can We Detect Failures Without Failure Data? Uncertainty-Aware Runtime Failure Detection for Imitation Learning Policies](https://arxiv.org/abs/2503.08558) | 2025-03-11 | RSS 2025 | 是 | — |
| [Certifiably-Correct Mapping for Safe Navigation Despite Odometry Drift](https://arxiv.org/abs/2504.18713) | 2025-04-25 | RSS 2025 | 是 | — |
| [RACER: Epistemic Risk-Sensitive RL Enables Fast Driving with Fewer Crashes](https://doi.org/10.15607/rss.2024.xx.080) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Real-Time Out-of-Distribution Failure Prevention via Multi-Modal Reasoning](https://arxiv.org/abs/2505.10547) | 2025-05-15 | CoRL 2025 | 是 | — |
| [Uncertainty-aware Accurate Elevation Modeling for Off-road Navigation via Neural Processes](https://arxiv.org/abs/2508.03890) | 2025-08-05 | CoRL 2025 | 是 | — |
| [Uncertainty-aware Latent Safety Filters for Avoiding Out-of-Distribution Failures](https://arxiv.org/abs/2505.00779) | 2025-05-01 | CoRL 2025 | 是 | — |
| [Uncertainty-Aware Trajectory Prediction via Rule-Regularized Heteroscedastic Deep Classification](https://arxiv.org/abs/2504.13111) | 2025-04-17 | RSS 2025 | 是 | — |
| [Drive Anywhere: Generalizable End-to-end Autonomous Driving with Multi-modal Foundation Models](https://arxiv.org/abs/2310.17642) | — | ICRA 2024 | 否 | — |
| [V-STRONG: Visual Self-Supervised Traversability Learning for Off-road Navigation](https://arxiv.org/abs/2312.16016) | — | ICRA 2024 | 否 | — |
| [Topology-Driven Parallel Trajectory Optimization in Dynamic Environments](https://arxiv.org/abs/2401.06021) | — | T-RO 2025 | 否 | — |
| [CoBL-Diffusion: Diffusion-Based Conditional Robot Planning in Dynamic Environments Using Control Barrier and Lyapunov Functions](https://arxiv.org/abs/2406.05309) | — | IROS 2024 | 否 | — |
| [Toward Efficient MPPI Trajectory Generation With Unscented Guidance: U-MPPI Control Strategy](https://arxiv.org/abs/2306.12369) | — | T-RO 2025 | 否 | — |
| [Semantically Safe Robot Manipulation: From Semantic Scene Understanding to Motion Safeguards](https://arxiv.org/abs/2410.15185) | 2024-10-19 | RA-L 2025 | 否 | — |
| [MotionScript: Natural Language Descriptions for Expressive 3D Human Motions](https://arxiv.org/abs/2312.12634) | — | IROS 2025 | 否 | — |
| [PIETRA: Physics-Informed Evidential Learning for Traversing Out-of-Distribution Terrain](https://arxiv.org/abs/2409.03005) | 2024-09-04 | RA-L 2025 | 否 | — |
| [VINGS-Mono: Visual-Inertial Gaussian Splatting Monocular SLAM in Large Scenes](https://arxiv.org/abs/2501.08286) | 2025-01-14 | T-RO 2025、ICRA 2026 | 否 | — |
| [Deep Evidential Uncertainty Estimation for Semantic Segmentation under Out-Of-Distribution Obstacles](https://ieeexplore.ieee.org/document/10611342) | 2024-05-13 | ICRA 2024 | 否 | — |
| [RobotPerf: An Open-Source, Vendor-Agnostic, Benchmarking Suite for Evaluating Robotics Computing System Performance](https://arxiv.org/abs/2309.09212) | — | ICRA 2024 | 否 | — |
| [Integrating Predictive Motion Uncertainties with Distributionally Robust Risk-Aware Control for Safe Robot Navigation in Crowds](https://arxiv.org/abs/2403.05081) | — | ICRA 2024 | 否 | — |
| [Sensor-based distributionally robust control for safe robot navigation in dynamic environments](https://arxiv.org/abs/2405.18251) | — | IJRR 2025 | 否 | — |
| [TrustNavGPT: Modeling Uncertainty to Improve Trustworthiness of Audio-Guided LLM-Based Robot Navigation](https://arxiv.org/abs/2408.01867) | 2024-08-03 | IROS 2024 | 否 | — |
| [Online tree-based planning for active spacecraft fault estimation and collision avoidance](https://www.science.org/doi/10.1126/scirobotics.adn4722) | 2024-08-28 | Science Robotics 2024 | 否 | — |
| [Recover: A Neuro-Symbolic Framework for Failure Detection and Recovery](https://arxiv.org/abs/2404.00756) | — | IROS 2024 | 否 | — |
| [Mutual Information-calibrated Conformal Feature Fusion for Uncertainty-Aware Multimodal 3D Object Detection at the Edge](https://arxiv.org/abs/2309.09593) | — | ICRA 2024 | 否 | — |
| [HR-APR: APR-agnostic Framework with Uncertainty Estimation and Hierarchical Refinement for Camera Relocalisation](https://arxiv.org/abs/2402.14371) | — | ICRA 2024 | 否 | — |
| [Generative Modeling of Residuals for Real-Time Risk-Sensitive Safety with Discrete-Time Control Barrier Functions](https://arxiv.org/abs/2311.05802) | — | ICRA 2024 | 否 | — |
| [LRAE: Large-Region-Aware Safe and Fast Autonomous Exploration of Ground Robots for Uneven Terrains](https://ieeexplore.ieee.org/document/3486229) | 2024-12-01 | RA-L 2024 | 否 | — |
| [Chance-Constrained Sampling-Based MPC for Collision Avoidance in Uncertain Dynamic Environments](https://arxiv.org/abs/2501.08520) | 2025-01-15 | RA-L 2025 | 否 | — |
| [STLCG++: A Masking Approach for Differentiable Signal Temporal Logic Specification](https://arxiv.org/abs/2501.04194) | 2025-01-08 | RA-L 2025、ICRA 2026 | 否 | — |
| [Updating Robot Safety Representations Online from Natural Language Feedback](https://arxiv.org/abs/2409.14580) | 2024-09-22 | ICRA 2025 | 否 | — |
| [Wait, That Feels Familiar: Learning to Extrapolate Human Preferences for Preference-Aligned Path Planning](https://arxiv.org/abs/2309.09912) | — | ICRA 2024 | 否 | — |
| [SEAL: Towards Safe Autonomous Driving via Skill-Enabled Adversary Learning for Closed-Loop Scenario Generation](https://arxiv.org/abs/2409.10320) | 2024-09-16 | RA-L 2025、ICRA 2026 | 否 | — |
| [CoBRA: A Composable Benchmark for Robotics Applications](https://arxiv.org/abs/2203.09337) | — | ICRA 2024 | 否 | — |
| [A Morphing Quadrotor-Blimp With Balloon Failure Resilience for Mobile Ecological Sensing](https://ieeexplore.ieee.org/document/3406061) | 2024-07-01 | RA-L 2024 | 否 | — |
| [Adaptive Prediction Ensemble: Improving Out-of-Distribution Generalization of Motion Forecasting](https://arxiv.org/abs/2407.09475) | 2024-07-12 | RA-L 2025 | 否 | — |
| [RoadRunner M&M -- Learning Multi-range Multi-resolution Traversability Maps for Autonomous Off-road Navigation](https://arxiv.org/abs/2409.10940) | 2024-09-17 | RA-L 2024 | 否 | — |
| [Safe Robot Reflexes: A Taxonomy-Based Decision and Modulation Framework](https://ieeexplore.ieee.org/document/3519421) | 2025-01-01 | T-RO 2025 | 否 | — |
| [TrajFlow: Multi-modal Motion Prediction via Flow Matching](https://arxiv.org/abs/2506.08541) | — | IROS 2025 | 否 | — |
| [vMF-Contact: Uncertainty-aware Evidential Learning for Probabilistic Contact-grasp in Noisy Clutter](https://arxiv.org/abs/2411.03591) | 2024-11-06 | ICRA 2025 | 否 | — |
| [Detecting and Mitigating System-Level Anomalies of Vision-Based Controllers](https://arxiv.org/abs/2309.13475) | — | ICRA 2024 | 否 | — |
| [Improving Out-of-Distribution Generalization of Trajectory Prediction for Autonomous Driving via Polynomial Representations](https://arxiv.org/abs/2407.13431) | — | IROS 2024 | 否 | — |
| [Multi-LIO: A Lightweight Multiple LiDAR-Inertial Odometry System](https://ieeexplore.ieee.org/document/10611257) | 2024-05-13 | ICRA 2024 | 否 | — |
| [A Hierarchical Framework for Robot Safety using Whole-body Tactile Sensors](https://ieeexplore.ieee.org/document/10610834) | 2024-05-13 | ICRA 2024 | 否 | — |
| [Towards Safe Robot Use with Edged or Pointed Objects: A Surrogate Study Assembling a Human Hand Injury Protection Database](https://arxiv.org/abs/2404.04004) | — | ICRA 2024 | 否 | — |
| [A Multimodal Handover Failure Detection Dataset and Baselines](https://arxiv.org/abs/2402.18319) | — | ICRA 2024 | 否 | — |
| [Designing Control Barrier Function via Probabilistic Enumeration for Safe Reinforcement Learning Navigation](https://arxiv.org/abs/2504.21643) | 2025-04-30 | RA-L 2025 | 否 | — |
| [UASTHN: Uncertainty-Aware Deep Homography Estimation for UAV Satellite-Thermal Geo-localization](https://arxiv.org/abs/2502.01035) | 2025-02-03 | ICRA 2025 | 否 | — |
| [Uncertainty-driven Exploration Strategies for Online Grasp Learning](https://arxiv.org/abs/2309.12038) | — | ICRA 2024 | 否 | — |
| [A Unified Interaction Control Framework for Safe Robotic Ultrasound Scanning with Human-Intention-Aware Compliance](https://arxiv.org/abs/2411.19545) | 2024-11-29 | IROS 2024 | 否 | — |
| [Evidential Uncertainty Estimation for Multi-Modal Trajectory Prediction](https://arxiv.org/abs/2503.05274) | 2025-03-07 | IROS 2025 | 否 | — |
| [Large-scale Indoor Mapping with Failure Detection and Recovery in SLAM](https://ieeexplore.ieee.org/document/10802593) | 2024-01-01 | IROS 2024 | 否 | — |
| [OCCUQ: Exploring Efficient Uncertainty Quantification for 3D Occupancy Prediction](https://arxiv.org/abs/2503.10605) | — | ICRA 2025 | 否 | — |
| [OoDIS: Anomaly Instance Segmentation and Detection Benchmark](https://arxiv.org/abs/2406.11835) | — | ICRA 2025 | 否 | — |
| [UMAD: University of Macau Anomaly Detection Benchmark Dataset](https://arxiv.org/abs/2408.12527) | 2024-08-22 | IROS 2024 | 否 | — |
| [Estimating Control Barriers from Offline Data](https://arxiv.org/abs/2503.10641) | 2025-02-21 | ICRA 2025 | 否 | — |
| [VLM Can Be a Good Assistant: Enhancing Embodied Visual Tracking with Self-Improving Vision-Language Models](https://arxiv.org/abs/2505.20718) | 2025-05-27 | IROS 2025 | 否 | — |
| [Autonomous 3D Exploration in Large-Scale Environments with Dynamic Obstacles](https://arxiv.org/abs/2310.17977) | — | ICRA 2024 | 否 | — |
| [BAM: Box Abstraction Monitors for Real-time OoD Detection in Object Detection](https://arxiv.org/abs/2403.18373) | — | IROS 2024 | 否 | — |
| [Efficient Hybrid Neuromorphic-Bayesian Model for Olfaction Sensing: Detection and Classification](https://arxiv.org/abs/2407.04714) | — | ICRA 2024 | 否 | — |
| [Learning Through Retrospection: Improving Trajectory Prediction for Automated Driving with Error Feedback](https://arxiv.org/abs/2504.13785) | 2025-04-18 | IROS 2025 | 否 | — |
