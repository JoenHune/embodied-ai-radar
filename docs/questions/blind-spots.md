---
outline: deep
---

# 文档之外：具身研究雷达还必须看什么

> 原文是一份很强的“单机器人灵巧操作迭代纲领”，但不是完整的具身智能地图。以下缺口大多已经由 D1–D15 覆盖，因此重点是补充研究叙事与横向证据，而不是继续增加互斥主方向。

| ID | 文档遗漏/弱覆盖方向 | 类型 | 已有 D 类 | 为什么重要 | 公开锚点 | 雷达处理 |
|---|---|---|---|---|---|---|
| G1 | 通才基础模型、推理与长期记忆 | 独立主方向 | [D1](/frontiers/foundation-models) / [D2](/frontiers/reasoning-planning) | 内部文档有意降低 backbone 的优先级，但模型如何形成可组合技能、任务进度记忆与可验证中间表示仍是当前主线，不能从雷达移除。 | [π0: A Vision-Language-Action Flow Model for General Robot Control](https://www.roboticsproceedings.org/rss21/p010.html)；[Robotic Control via Embodied Chain-of-Thought Reasoning](https://proceedings.mlr.press/v270/zawalski25a.html) | 保留 D1/D2；问题层只负责检验模型是否真正改善执行闭环。 |
| G2 | 开放世界导航、空间记忆与主动探索 | 独立主方向 | [D6](/frontiers/navigation-mobile-manipulation) / [D11](/frontiers/spatial-perception) / [D2](/frontiers/reasoning-planning) | loco-manipulation 只覆盖其中一部分；建筑级移动操作、开放词汇导航、动态地图和长期空间记忆具有独立问题结构与评测。 | [MoTo: A Zero-shot Plug-in Interaction-aware Navigation for Generalized Mobile Manipulation](https://proceedings.mlr.press/v305/wu25c.html)；[ActLoc: Learning to Localize through Active Viewpoint Selection](https://proceedings.mlr.press/v305/li25b.html) | 继续由 D6/D11 跟踪，并把主动感知作为横向问题与 Q5 连接。 |
| G3 | 人机协作、共享自治与偏好学习 | 独立主方向 | [D7](/frontiers/human-robot-interaction) | 内部文档主要把人当作数据采集者和接管者，遗漏了协作、信任、意图沟通、辅助机器人与社会导航。 | [FlashBack: Consistency Model-Accelerated Shared Autonomy](https://proceedings.mlr.press/v305/sun25a.html)；[Safety with Agency: Human-Centered Safety Filter with Application to AI-Assisted Motorsports](https://www.roboticsproceedings.org/rss21/p093.html) | 保留 D7；把人因、操作者建模与 Q6/Q7 的接管效率相连。 |
| G4 | 安全、形式验证、不确定性与物理攻击面 | 独立主方向 | [D12](/frontiers/safety-evaluation) / [D2](/frontiers/reasoning-planning) | 失败回流不等于安全保证；开放世界机器人还需要风险校准、运行时保障、指令/视觉攻击评测和人身安全边界。 | [Geometric Red-Teaming for Robotic Manipulation](https://proceedings.mlr.press/v305/goel25a.html)；[Uncertainty-aware Latent Safety Filters for Avoiding Out-of-Distribution Failures](https://proceedings.mlr.press/v305/seo25a.html) | 强化 D12，并将安全成本、风险暴露时间和干预触发纳入所有问题轴的共同指标。 |
| G5 | 长期记忆、持续学习与灾难性遗忘 | 横向能力轴 | [D13](/frontiers/continual-deployment-learning) / [D2](/frontiers/reasoning-planning) | 一次 post-training 不能代表长期运行；策略需要在任务、环境和硬件变化后持续吸收经验且不破坏旧技能。 | [Continuously Improving Mobile Manipulation with Autonomous Real-World RL](https://proceedings.mlr.press/v270/mendonca25a.html)；[Beyond Imitation: Self-Improving Robot Policies via Off-Policy Q-Planning](https://arxiv.org/abs/2608.21204) | 保留 D13；把回归测试、记忆更新和技能保留加入 Q6/Q7。 |
| G6 | 多机器人协同、异构编队与 fleet learning | 独立但低密度方向 | [D14](/frontiers/multi-robot-coordination) / [D13](/frontiers/continual-deployment-learning) | 内部材料集中在单机操作，未覆盖多机通信、协作操作、异构团队与跨设备经验共享。 | [Capability-Aware Shared Hypernetworks for Multi-Agent Coordination](https://proceedings.mlr.press/v305/fu25a.html)；[Latent Theory of Mind for Cooperative Multi-Agent Reinforcement Learning](https://proceedings.mlr.press/v305/he25a.html) | 保留 D14，但在出现跨月独立团队与真实系统证据前不扩为核心问题轴。 |
| G7 | 实时、边缘部署、能耗与系统资源调度 | 横向系统轴 | [D1](/frontiers/foundation-models) / [D2](/frontiers/reasoning-planning) / [D12](/frontiers/safety-evaluation) | 控制频率、云边时延、功耗和状态陈旧会直接决定大模型、verifier 与世界模型能否进入闭环。 | [Deltoris: Enabling Real-time VLA Inference in Embodied AI via Bit-level Sparsity and Speculative Inference](https://arxiv.org/abs/2608.04428)；[EcoVLA: Energy-Efficient Device-Edge Co-Inference for Vision-Language-Action Models under Real-Time Constraints](https://arxiv.org/abs/2608.15502) | 不新增 D16；作为所有模型/系统方向的强制证据字段和月度弱信号。 |
| G8 | 柔性物体、医疗、工业与极端环境等压力测试域 | 应用压力测试 | [D4](/frontiers/dexterous-manipulation) / [D1](/frontiers/foundation-models) / [D10](/frontiers/simulation-transfer) / [D12](/frontiers/safety-evaluation) | 这些场景不是简单行业标签，而是检验精确接触、合规、安全、数据稀缺和跨域泛化的高约束测试床。 | [DeMaVLA: A Vision-Language-Action Foundation Model for Generalizable Deformable Manipulation](https://arxiv.org/abs/2605.31286)；[Open-H-Embodiment: A Large-Scale Dataset for Enabling Foundation Models in Medical Robotics](https://arxiv.org/abs/2604.21017) | 作为 domain tags 和专题页维护，不拆成互斥主方向。 |
| G9 | 本体、软体机器人与学习驱动的形态设计 | 候选一级方向 | [D4](/frontiers/dexterous-manipulation) / [D10](/frontiers/simulation-transfer) / [D15](/frontiers/embodied-multisensory) | 内部文档已提出软硬件共设计，但仍主要把硬件视为训练约束；新研究开始把刚度、形态、传感布局和控制器放入同一优化问题。 | [KineSoft: A Kinematically Inspired Soft Gripper with Proprioceptive Sensing](https://proceedings.mlr.press/v305/yoo25a.html)；[Co-Design of Soft Gripper with Neural Physics](https://proceedings.mlr.press/v305/yi25a.html) | 先设 D16 观察池；只有达到至少 3 个独立团队、2 个正式 venue 且主贡献确为本体设计与学习联合优化时再升级。 |

## 是否需要新增 D16

当前不正式新增。**本体、软体机器人与学习驱动形态设计**值得建立观察池，但升级前应同时满足：至少 3 个独立团队、2 个正式 venue，并且论文主贡献确实是“本体设计与学习联合优化”，而不是纯机械、材料或没有自主学习闭环的硬件论文。

## 最重要的补充判断

- 失败恢复不等于安全保证；风险校准、运行时保障、形式约束和物理攻防需要独立观察。
- Loco-manipulation 不等于开放世界导航；建筑级移动操作、动态语义地图和长期空间记忆仍有独立问题结构。
- 人不只是示范者或接管者，也是协作者、被服务者和共同决策者。
- 单机数据飞轮不等于 fleet learning；异构多机器人协作、策略分发与集体回归测试仍被低估。
- 端侧算力、能耗、网络依赖、标定、维护和数据权利属于战略看板变量，不应伪装成论文主方向。
