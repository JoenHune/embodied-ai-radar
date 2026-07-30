---
outline: deep
---

# GitHub 与开源生态证据

> 快照：2026-07-29。所有 42 个仓库 URL 均通过 GitHub API 解析；stars 仅作传播规模旁证，不进入独立采用分。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>42</strong><span>已核验仓库</span></div>
  <div class="radar-kpi"><strong>34</strong><span>关联论文证据</span></div>
  <div class="radar-kpi"><strong>17</strong><span>高独立参与代理</span></div>
  <div class="radar-kpi"><strong>12</strong><span>许可证缺失/未识别</span></div>
</div>

## 如何读这个表

IAS-GH（0–100）由近 12 个月外部 issue/PR 作者、贡献者广度、合并 PR、forks 与 release 新鲜度构成。它衡量公开 GitHub 协作与独立参与，不等于论文质量、商业采用或安全成熟度。GitHub 通用 API 没有稳定的反向依赖总数，缺失值保持 null，绝不用 forks 冒充 dependents。

| 仓库 | 类别 | 论文 | IAS-GH | forks / watchers | License | 最近推送 |
|---|---|---|---:|---:|---|---|
| [huggingface/lerobot](https://github.com/huggingface/lerobot) ![GitHub stars](https://img.shields.io/github/stars/huggingface/lerobot?style=flat-square&label=stars) | 训练/数据平台 | [2602.22818](https://arxiv.org/abs/2602.22818) | 99（高） | 5235 / 165 | Apache-2.0 | 2026-07-29 |
| [ros2/ros2](https://github.com/ros2/ros2) ![GitHub stars](https://img.shields.io/github/stars/ros2/ros2?style=flat-square&label=stars) | 机器人运行时 | 待映射 | 98（高） | 930 / 242 | NOASSERTION | 2026-06-23 |
| [isaac-sim/IsaacLab](https://github.com/isaac-sim/IsaacLab) ![GitHub stars](https://img.shields.io/github/stars/isaac-sim/IsaacLab?style=flat-square&label=stars) | 仿真/训练运行时 | [2511.04831](https://arxiv.org/abs/2511.04831) | 97（高） | 3800 / 64 | BSD-3-Clause | 2026-07-29 |
| [google-deepmind/mujoco](https://github.com/google-deepmind/mujoco) ![GitHub stars](https://img.shields.io/github/stars/google-deepmind/mujoco?style=flat-square&label=stars) | 仿真/物理引擎 | [2012.63861](https://arxiv.org/abs/2012.63861)、[DOI](https://doi.org/10.1109/iros.2012.6386109) | 96（高） | 1656 / 129 | Apache-2.0 | 2026-07-29 |
| [NVIDIA/Isaac-GR00T](https://github.com/NVIDIA/Isaac-GR00T) ![GitHub stars](https://img.shields.io/github/stars/NVIDIA/Isaac-GR00T?style=flat-square&label=stars) | VLA/人形基础模型 | [2503.14734](https://arxiv.org/abs/2503.14734) | 96（高） | 1373 / 75 | Apache-2.0 | 2026-07-22 |
| [mani-skill/ManiSkill](https://github.com/mani-skill/ManiSkill) ![GitHub stars](https://img.shields.io/github/stars/mani-skill/ManiSkill?style=flat-square&label=stars) | Benchmark/仿真 | [2107.14483](https://arxiv.org/abs/2107.14483)、[2410.00425](https://arxiv.org/abs/2410.00425) | 95（高） | 519 / 20 | Apache-2.0 | 2026-07-29 |
| [Genesis-Embodied-AI/genesis-world](https://github.com/Genesis-Embodied-AI/genesis-world) ![GitHub stars](https://img.shields.io/github/stars/Genesis-Embodied-AI/genesis-world?style=flat-square&label=stars) | 仿真/生成式物理 | 待映射 | 93（高） | 2822 / 224 | Apache-2.0 | 2026-07-29 |
| [moveit/moveit2](https://github.com/moveit/moveit2) ![GitHub stars](https://img.shields.io/github/stars/moveit/moveit2?style=flat-square&label=stars) | 规划/执行运行时 | 待映射 | 93（高） | 770 / 47 | BSD-3-Clause | 2026-07-20 |
| [RobotLocomotion/drake](https://github.com/RobotLocomotion/drake) ![GitHub stars](https://img.shields.io/github/stars/RobotLocomotion/drake?style=flat-square&label=stars) | 规划/控制运行时 | 待映射 | 91（高） | 1382 / 168 | NOASSERTION | 2026-07-29 |
| [RoboTwin-Platform/RoboTwin](https://github.com/RoboTwin-Platform/RoboTwin) ![GitHub stars](https://img.shields.io/github/stars/RoboTwin-Platform/RoboTwin?style=flat-square&label=stars) | Benchmark/双臂 | [2506.18088](https://arxiv.org/abs/2506.18088)、[2506.23351](https://arxiv.org/abs/2506.23351)、[2504.13059](https://arxiv.org/abs/2504.13059)、[2409.02920](https://arxiv.org/abs/2409.02920) | 91（高） | 441 / 38 | MIT | 2026-07-25 |
| [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) ![GitHub stars](https://img.shields.io/github/stars/Physical-Intelligence/openpi?style=flat-square&label=stars) | VLA/基础模型 | [2410.24164](https://arxiv.org/abs/2410.24164) | 89（高） | 2268 / 91 | Apache-2.0 | 2026-06-16 |
| [nvidia-cosmos/cosmos-predict2](https://github.com/nvidia-cosmos/cosmos-predict2) ![GitHub stars](https://img.shields.io/github/stars/nvidia-cosmos/cosmos-predict2?style=flat-square&label=stars) | 世界模型 | 待映射 | 84（高） | 104 / 1 | Apache-2.0 | 2025-10-29 |
| [OpenDriveLab/AgiBot-World](https://github.com/OpenDriveLab/AgiBot-World) ![GitHub stars](https://img.shields.io/github/stars/OpenDriveLab/AgiBot-World?style=flat-square&label=stars) | 机器人数据/Benchmark | [2503.06669](https://arxiv.org/abs/2503.06669) | 72（高） | 212 / 37 | NOASSERTION | 2026-05-29 |
| [robocasa/robocasa](https://github.com/robocasa/robocasa) ![GitHub stars](https://img.shields.io/github/stars/robocasa/robocasa?style=flat-square&label=stars) | Benchmark/家庭操作 | [2406.02523](https://arxiv.org/abs/2406.02523) | 67（中高） | 229 / 13 | NOASSERTION | 2026-07-08 |
| [ARISE-Initiative/robomimic](https://github.com/ARISE-Initiative/robomimic) ![GitHub stars](https://img.shields.io/github/stars/ARISE-Initiative/robomimic?style=flat-square&label=stars) | 机器人学习框架 | [2108.03298](https://arxiv.org/abs/2108.03298) | 66（中高） | 410 / 15 | MIT | 2026-02-05 |
| [Lifelong-Robot-Learning/LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO) ![GitHub stars](https://img.shields.io/github/stars/Lifelong-Robot-Learning/LIBERO?style=flat-square&label=stars) | Benchmark/终身学习 | [2306.03310](https://arxiv.org/abs/2306.03310) | 62（中高） | 446 / 7 | MIT | 2025-03-15 |
| [openvla/openvla](https://github.com/openvla/openvla) ![GitHub stars](https://img.shields.io/github/stars/openvla/openvla?style=flat-square&label=stars) | VLA/基础模型 | [2406.09246](https://arxiv.org/abs/2406.09246) | 62（中高） | 807 / 33 | MIT | 2025-03-23 |
| [simpler-env/SimplerEnv](https://github.com/simpler-env/SimplerEnv) ![GitHub stars](https://img.shields.io/github/stars/simpler-env/SimplerEnv?style=flat-square&label=stars) | Benchmark/真实到仿真 | [2405.05941](https://arxiv.org/abs/2405.05941) | 50（中高） | 194 / 9 | MIT | 2025-12-20 |
| [real-stanford/universal_manipulation_interface](https://github.com/real-stanford/universal_manipulation_interface) ![GitHub stars](https://img.shields.io/github/stars/real-stanford/universal_manipulation_interface?style=flat-square&label=stars) | 遥操作/数据引擎 | [2402.10329](https://arxiv.org/abs/2402.10329) | 46（中） | 278 / 20 | MIT | 2026-05-26 |
| [thu-ml/RoboticsDiffusionTransformer](https://github.com/thu-ml/RoboticsDiffusionTransformer) ![GitHub stars](https://img.shields.io/github/stars/thu-ml/RoboticsDiffusionTransformer?style=flat-square&label=stars) | VLA/扩散策略 | [2410.07864](https://arxiv.org/abs/2410.07864) | 46（中） | 164 / 12 | MIT | 2026-01-21 |
| [octo-models/octo](https://github.com/octo-models/octo) ![GitHub stars](https://img.shields.io/github/stars/octo-models/octo?style=flat-square&label=stars) | VLA/基础模型 | [2405.12213](https://arxiv.org/abs/2405.12213) | 44（中） | 275 / 19 | MIT | 2024-07-31 |
| [NVIDIA/GR00T-Dreams](https://github.com/NVIDIA/GR00T-Dreams) ![GitHub stars](https://img.shields.io/github/stars/NVIDIA/GR00T-Dreams?style=flat-square&label=stars) | 世界模型/合成数据 | [2505.12705](https://arxiv.org/abs/2505.12705) | 43（中） | 61 / 7 | Apache-2.0 | 2025-10-24 |
| [real-stanford/diffusion_policy](https://github.com/real-stanford/diffusion_policy) ![GitHub stars](https://img.shields.io/github/stars/real-stanford/diffusion_policy?style=flat-square&label=stars) | 机器人学习/扩散策略 | [2303.04137](https://arxiv.org/abs/2303.04137) | 43（中） | 814 / 20 | MIT | 2024-12-24 |
| [droid-dataset/droid](https://github.com/droid-dataset/droid) ![GitHub stars](https://img.shields.io/github/stars/droid-dataset/droid?style=flat-square&label=stars) | 机器人数据 | [2403.12945](https://arxiv.org/abs/2403.12945) | 35（中） | 82 / 8 | NOASSERTION | 2025-09-15 |
| [google-deepmind/open_x_embodiment](https://github.com/google-deepmind/open_x_embodiment) ![GitHub stars](https://img.shields.io/github/stars/google-deepmind/open_x_embodiment?style=flat-square&label=stars) | 机器人数据/多本体 | [2310.08864](https://arxiv.org/abs/2310.08864) | 26（早期/低证据） | 119 / 28 | Apache-2.0 | 2025-11-05 |
| [tonyzhaozh/aloha](https://github.com/tonyzhaozh/aloha) ![GitHub stars](https://img.shields.io/github/stars/tonyzhaozh/aloha?style=flat-square&label=stars) | 遥操作/双臂硬件 | [2304.13705](https://arxiv.org/abs/2304.13705) | 26（早期/低证据） | 337 / 34 | MIT | 2024-04-19 |
| [StanfordVL/BEHAVIOR-1K](https://github.com/StanfordVL/BEHAVIOR-1K) ![GitHub stars](https://img.shields.io/github/stars/StanfordVL/BEHAVIOR-1K?style=flat-square&label=stars) | 数据/Benchmark | 待映射 | 89（高） | 223 / 30 | NOASSERTION | 2026-07-28 |
| [facebookresearch/habitat-lab](https://github.com/facebookresearch/habitat-lab) ![GitHub stars](https://img.shields.io/github/stars/facebookresearch/habitat-lab?style=flat-square&label=stars) | 仿真/具身平台 | [1904.01201](https://arxiv.org/abs/1904.01201)、[2106.14405](https://arxiv.org/abs/2106.14405)、[2310.13724](https://arxiv.org/abs/2310.13724)、[2109.07703](https://arxiv.org/abs/2109.07703) | 87（高） | 684 / 43 | MIT | 2026-05-07 |
| [RoboVerseOrg/RoboVerse](https://github.com/RoboVerseOrg/RoboVerse) ![GitHub stars](https://img.shields.io/github/stars/RoboVerseOrg/RoboVerse?style=flat-square&label=stars) | Benchmark/数据平台 | [2504.18904](https://arxiv.org/abs/2504.18904)、[2411.18276](https://arxiv.org/abs/2411.18276) | 81（高） | 160 / 16 | Apache-2.0 | 2026-07-27 |
| [Farama-Foundation/Gymnasium-Robotics](https://github.com/Farama-Foundation/Gymnasium-Robotics) ![GitHub stars](https://img.shields.io/github/stars/Farama-Foundation/Gymnasium-Robotics?style=flat-square&label=stars) | 仿真/标准接口 | 待映射 | 70（高） | 136 / 15 | MIT | 2026-07-25 |
| [facebookresearch/hot3d](https://github.com/facebookresearch/hot3d) ![GitHub stars](https://img.shields.io/github/stars/facebookresearch/hot3d?style=flat-square&label=stars) | 人类数据/手物交互 | 待映射 | 43（中） | 34 / 38 | Apache-2.0 | 2026-06-16 |
| [stepjam/RLBench](https://github.com/stepjam/RLBench) ![GitHub stars](https://img.shields.io/github/stars/stepjam/RLBench?style=flat-square&label=stars) | Benchmark/任务学习 | [1909.12271](https://arxiv.org/abs/1909.12271) | 41（中） | 318 / 17 | NOASSERTION | 2025-01-25 |
| [AgibotTech/ACoT-VLA](https://github.com/AgibotTech/ACoT-VLA) ![GitHub stars](https://img.shields.io/github/stars/AgibotTech/ACoT-VLA?style=flat-square&label=stars) | VLA/动作推理 | [2601.11404](https://arxiv.org/abs/2601.11404) | 35（中） | 41 / 5 | Apache-2.0 | 2026-05-21 |
| [mees/calvin](https://github.com/mees/calvin) ![GitHub stars](https://img.shields.io/github/stars/mees/calvin?style=flat-square&label=stars) | Benchmark/长时序 | [2112.03227](https://arxiv.org/abs/2112.03227) | 35（中） | 124 / 7 | MIT | 2025-09-08 |
| [1x-technologies/1xgpt](https://github.com/1x-technologies/1xgpt) ![GitHub stars](https://img.shields.io/github/stars/1x-technologies/1xgpt?style=flat-square&label=stars) | 世界模型/数据 | [2402.15391](https://arxiv.org/abs/2402.15391) | 32（中） | 48 / 24 | Apache-2.0 | 2024-11-08 |
| [rail-berkeley/bridge_data_v2](https://github.com/rail-berkeley/bridge_data_v2) ![GitHub stars](https://img.shields.io/github/stars/rail-berkeley/bridge_data_v2?style=flat-square&label=stars) | 机器人数据 | [2308.12952](https://arxiv.org/abs/2308.12952)、[2110.06169](https://arxiv.org/abs/2110.06169)、[2306.03346](https://arxiv.org/abs/2306.03346)、[2206.07568](https://arxiv.org/abs/2206.07568)、[2212.06817](https://arxiv.org/abs/2212.06817)、[2304.13705](https://arxiv.org/abs/2304.13705) | 30（中） | 36 / 11 | MIT | 2024-03-17 |
| [OpenTeleVision/TeleVision](https://github.com/OpenTeleVision/TeleVision) ![GitHub stars](https://img.shields.io/github/stars/OpenTeleVision/TeleVision?style=flat-square&label=stars) | 遥操作 | [2407.01512](https://arxiv.org/abs/2407.01512) | 27（早期/低证据） | 136 / 15 | NOASSERTION | 2024-09-27 |
| [PKU-EPIC/DexGraspNet](https://github.com/PKU-EPIC/DexGraspNet) ![GitHub stars](https://img.shields.io/github/stars/PKU-EPIC/DexGraspNet?style=flat-square&label=stars) | 灵巧操作/数据 | [2210.02697](https://arxiv.org/abs/2210.02697) | 16（早期/低证据） | 50 / 4 | NOASSERTION | 2025-01-06 |
| [leap-hand/LEAP_Hand_Sim](https://github.com/leap-hand/LEAP_Hand_Sim) ![GitHub stars](https://img.shields.io/github/stars/leap-hand/LEAP_Hand_Sim?style=flat-square&label=stars) | 灵巧手/仿真 | [2309.06440](https://arxiv.org/abs/2309.06440) | 14（早期/低证据） | 35 / 2 | MIT | 2024-05-18 |
| [Kisaragi0/SC-VLA](https://github.com/Kisaragi0/SC-VLA) ![GitHub stars](https://img.shields.io/github/stars/Kisaragi0/SC-VLA?style=flat-square&label=stars) | VLA/世界模型 | [2602.21633](https://arxiv.org/abs/2602.21633) | 13（早期/低证据） | 2 / 1 | NOASSERTION | 2026-04-14 |
| [Meowuu7/DexTrack](https://github.com/Meowuu7/DexTrack) ![GitHub stars](https://img.shields.io/github/stars/Meowuu7/DexTrack?style=flat-square&label=stars) | 灵巧操作/追踪控制 | [2502.09614](https://arxiv.org/abs/2502.09614) | 13（早期/低证据） | 7 / 1 | NOASSERTION | 2026-04-14 |
| [ZGC-EmbodyAI/TwinBrainVLA](https://github.com/ZGC-EmbodyAI/TwinBrainVLA) ![GitHub stars](https://img.shields.io/github/stars/ZGC-EmbodyAI/TwinBrainVLA?style=flat-square&label=stars) | VLA/双系统 | [2601.14133](https://arxiv.org/abs/2601.14133) | 9（早期/低证据） | 0 / 1 | NOASSERTION | 2026-05-22 |

## 下一层采用证据

仓库进入“独立研究采用”还需要至少一种更强证据：第三方仓库真实 import/配置使用、包注册表依赖、无作者重叠的独立复现，或后续论文把它作为 benchmark/训练基础设施而非 related work 引用。

[下载完整仓库证据 JSON](/embodied-ai-radar/repositories.json)

<!-- 更新标记：GitHub 与开源生态证据 最后更新 2026.07 -->
