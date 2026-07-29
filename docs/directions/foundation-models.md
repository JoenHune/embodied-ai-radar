---
outline: deep
---

# 具身基础模型

> 把视觉、语言、机器人状态与连续动作放入可跨任务复用的预训练—后训练框架，核心不只是模型规模，而是数据覆盖、动作表示、实时执行和经验学习。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>843</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>157</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>9</strong><span>官方评审锚点</span></div>
  <div class="radar-kpi"><strong>45.8%</strong><span>主分析期占比</span></div>
</div>

## 跨月演进

- 2024 H2：OpenVLA、π0 等工作确立开放 VLA 与 flow action generation 的基线。
- 2025 H1：π0.5、FAST、SpatialVLA 把开放世界泛化、动作 tokenization 与空间表征带入同行评审。
- 2025 H2：研究从“是否可做 VLA”分化到效率、跨本体、经验学习和开放数据配方。
- 2026 H1：steerable、real-time、垂直物理任务和跨本体统一成为主线，执行系统开始与模型本体同等重要。

| 月份 | 候选数 | 相对热度 |
|---|---:|---|
| 2025-07 | 17 | █ |
| 2025-08 | 29 | ██ |
| 2025-09 | 57 | ████ |
| 2025-10 | 72 | █████ |
| 2025-11 | 65 | █████ |
| 2025-12 | 59 | ████ |
| 2026-01 | 36 | ███ |
| 2026-02 | 84 | ██████ |
| 2026-03 | 104 | ████████ |
| 2026-04 | 57 | ████ |
| 2026-05 | 101 | ███████ |
| 2026-06 | 162 | ████████████ |

## 技术路线对比

| 路线 | 核心表示/机制 | 优势 | 当前局限 |
|---|---|---|---|
| 自回归 action token | 离散动作 token / chunk | 训练与语言模型兼容 | 量化误差、控制频率 |
| Diffusion / flow action | 连续轨迹分布 | 多峰动作、平滑控制 | 采样延迟、闭环修正 |
| 分层 / 双系统 VLA | 语义计划 + 低层执行 | 长时任务、可解释接口 | 模块误差与异步调度 |
| 视频—动作统一模型 | 预测未来 + 生成动作 | 人类视频扩展、world knowledge | 像素冗余、可执行性 |

## 代表工作

| 论文 | v1 月份 | 状态 | 一句话贡献 |
|---|---|---|---|
| [π0: A Vision-Language-Action Flow Model for General Robot Control](https://arxiv.org/abs/2410.24164) | 2024-10 | [RSS 2025](https://www.roboticsproceedings.org/rss21/p010.html) | Robot learning holds tremendous promise to unlock the full potential of flexible, general, and dexterous robot systems, as well as to address some of the deepest questions in artificial intelligence |
| [FAST: Efficient Action Tokenization for Vision-Language-Action Models](https://arxiv.org/abs/2501.09747) | 2025-01 | [RSS 2025](https://www.roboticsproceedings.org/rss21/p012.html) | Autoregressive sequence models, such as Transformer-based vision-language action (VLA) policies, can be tremendously effective for capturing complex and generalizable robotic behaviors |
| [π0.5: a Vision-Language-Action Model with Open-World Generalization](https://arxiv.org/abs/2504.16054) | 2025-04 | [CoRL 2025](https://proceedings.mlr.press/v305/black25a.html) | In order for robots to be useful, they must perform practically relevant tasks in the real world, outside of the lab |
| [EO-1: An Open Unified Embodied Foundation Model for General Robot Control](https://arxiv.org/abs/2508.21112) | 2025-08 | arXiv | EO-1 在统一 decoder 中结合自回归与 flow matching，以 EO-Data1.5M 做交错 vision-text-action 预训练，覆盖多本体长时序灵巧控制。 |
| [$π^{*}_{0.6}$: a VLA That Learns From Experience](https://arxiv.org/abs/2511.14759) | 2025-11 | arXiv | RECAP 把示范、在线 rollout 与专家纠正统一为 advantage-conditioned VLA 强化学习，使 π*0.6 在家庭与商业设备任务中持续改进。 |
| [Xiaomi-Robotics-0: An Open-Sourced Vision-Language-Action Model with Real-Time Execution](https://arxiv.org/abs/2602.12684) | 2026-02 | arXiv | 以跨本体预训练、异步执行训练和动作块时间对齐，让开放 VLA 在消费级 GPU 上实现平滑实时双臂控制。 |
| [$π_{0.7}$: a Steerable Generalist Robotic Foundation Model with Emergent Capabilities](https://arxiv.org/abs/2604.15483) | 2026-04 | arXiv | 通过把策略、表现元数据和子目标图像等多模态上下文纳入训练，使单一 foundation policy 可被精细 steer 并出现跨本体、组合任务和灵巧能力。 |
| [Qwen-VLA: Unifying Vision-Language-Action Modeling across Tasks, Environments, and Robot Embodiments](https://arxiv.org/abs/2605.30280) | 2026-05 | arXiv | 以 embodiment-aware prompt 和统一动作—轨迹预测，把操作、导航、轨迹预测及多源数据纳入单一 Qwen-VLA。 |

## 同行评审锚点

| 工作 | Venue | arXiv |
|---|---|---|
| [OpenVLA: An Open-Source Vision-Language-Action Model](https://proceedings.mlr.press/v270/kim25c.html) | CoRL 2024 | [2406.09246](https://arxiv.org/abs/2406.09246) |
| [Scaling Proprioceptive-Visual Learning with Heterogeneous Pre-trained Transformers](https://papers.nips.cc/paper_files/paper/2024/hash/e0f393e7980a24fd12fa6f15adfa25fb-Abstract-Conference.html) | NeurIPS 2024 | [2409.20537](https://arxiv.org/abs/2409.20537) |
| [π₀: A Vision-Language-Action Flow Model for General Robot Control](https://www.roboticsproceedings.org/rss21/p010.html) | RSS 2025 | [2410.24164](https://arxiv.org/abs/2410.24164) |
| [SpatialVLA: Exploring Spatial Representations for Visual-Language-Action Models](https://www.roboticsproceedings.org/rss21/p011.html) | RSS 2025 | [2501.15830](https://arxiv.org/abs/2501.15830) |
| [FAST: Efficient Action Tokenization for Vision-Language-Action Models](https://www.roboticsproceedings.org/rss21/p012.html) | RSS 2025 | [2501.09747](https://arxiv.org/abs/2501.09747) |
| [Learning to Act Anywhere with Task-centric Latent Actions](https://www.roboticsproceedings.org/rss21/p014.html) | RSS 2025 | [2505.06111](https://arxiv.org/abs/2505.06111) |
| [π₀.₅: A Vision-Language-Action Model with Open-World Generalization](https://proceedings.mlr.press/v305/black25a.html) | CoRL 2025 | [2504.16054](https://arxiv.org/abs/2504.16054) |
| [Long-VLA: Unleashing Long-Horizon Capability of Vision Language Action Model for Robot Manipulation](https://proceedings.mlr.press/v305/fan25a.html) | CoRL 2025 | [2508.19958](https://arxiv.org/abs/2508.19958) |
| [ActiveVLA: Injecting Active Perception into Vision-Language-Action Models for Precise 3D Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_ActiveVLA_Injecting_Active_Perception_into_Vision-Language-Action_Models_for_Precise_3D_CVPR_2026_paper.html) | CVPR 2026 | [2601.08325](https://arxiv.org/abs/2601.08325) |

## 成熟度、瓶颈与战略判断

**成熟度。** 已从概念验证进入多团队真实机器人阶段；但“通用”仍高度依赖训练机器人、任务模板和评测环境。

**关键瓶颈。**

- 实时推理与控制频率
- 长尾失败恢复
- 跨本体负迁移
- 可持续部署数据闭环
- 安全与不确定性

**战略判断。** 短期不应只按模型参数或 benchmark 排名判断团队；应重点比较真实部署时延、数据飞轮、跨本体适配成本和失败恢复。

<!-- 更新标记：具身基础模型 最后更新 2026.07 -->
