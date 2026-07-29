---
outline: deep
---

# 灵巧操作

> 覆盖多指手、双臂、臂手协同、触觉与接触密集操作；判断成熟度时优先看长时连续接触、真实机器人和跨硬件可复现性。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>250</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>134</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>5</strong><span>官方评审锚点</span></div>
  <div class="radar-kpi"><strong>13.6%</strong><span>主分析期占比</span></div>
</div>

## 跨月演进

- 2024–2025 H1：DexUMI、Reactive Diffusion Policy 把可扩展人类示范与视觉—触觉快慢策略带入评审主线。
- 2025 H2：egocentric 数据、接触表示、生成视频和语言设计奖励扩大监督来源。
- 2026 Q1：长时演奏、通用手控制和视触觉世界模型让灵巧操作从抓取走向连续任务。
- 2026 Q2：touch dreaming、连续视触觉传感与统一触觉 VLA 形成“预测—控制—恢复”闭环。

| 月份 | 候选数 | 相对热度 |
|---|---:|---|
| 2025-07 | 12 | ███ |
| 2025-08 | 11 | ██ |
| 2025-09 | 25 | █████ |
| 2025-10 | 13 | ███ |
| 2025-11 | 9 | ██ |
| 2025-12 | 12 | ███ |
| 2026-01 | 7 | █ |
| 2026-02 | 22 | █████ |
| 2026-03 | 40 | ████████ |
| 2026-04 | 19 | ████ |
| 2026-05 | 23 | █████ |
| 2026-06 | 57 | ████████████ |

## 技术路线对比

| 路线 | 核心表示/机制 | 优势 | 当前局限 |
|---|---|---|---|
| 遥操作 / UMI | 直接采集人类或领导臂示范 | 高质量、真实接触 | 设备成本与动作映射 |
| 人类视频 / egocentric | 从第一视角或手部视频预训练 | 规模大、硬件无关 | 缺失力和动作标签 |
| 仿真 / 生成数据 | 合成接触、奖励或视频 | 覆盖长尾、成本低 | sim-to-real 与可行性过滤 |
| 视触觉策略 / world model | 预测接触与未来状态 | 失败恢复、精细控制 | 传感器标准化 |

## 代表工作

| 论文 | v1 月份 | 状态 | 一句话贡献 |
|---|---|---|---|
| [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://arxiv.org/abs/2503.02881) | 2025-03 | [RSS 2025](https://www.roboticsproceedings.org/rss21/p052.html) | Humans can accomplish complex contact-rich tasks using vision and touch, with highly reactive capabilities such as fast response to external changes and adaptive control of contact forces; however, this remains challenging for robots |
| [DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://arxiv.org/abs/2505.21864) | 2025-05 | [CoRL 2025](https://proceedings.mlr.press/v305/xu25b.html) | We present DexUMI - a data collection and policy learning framework that uses the human hand as the natural interface to transfer dexterous manipulation skills to various robot hands |
| [OmniVTLA: Vision-Tactile-Language-Action Models with Semantic-Aligned Tactile Sensing](https://arxiv.org/abs/2508.08706) | 2025-08 | arXiv | 以双路触觉编码器和 135K 样本 ObjTac 对齐视觉、语言与多类触觉传感器，在夹爪和灵巧手真实任务上显著增益。 |
| [CEDex: Cross-Embodiment Dexterous Grasp Generation at Scale from Human-like Contact Representations](https://arxiv.org/abs/2509.24661) | 2025-09 | arXiv | CEDex 用人类式接触表征、拓扑合并与 SDF 物理约束，把同一抓取先验扩展到任意形态的灵巧手并规模化生成数据。 |
| [DexMan: Learning Bimanual Dexterous Manipulation from Human and Generated Videos](https://arxiv.org/abs/2510.08475) | 2025-10 | arXiv | DexMan 从无标定第三视角人类或生成视频估计手物运动，以接触奖励在仿真人形机器人上学习双臂灵巧技能。 |
| [OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2603.19201) | 2026-03 | arXiv | 以 21K+ 轨迹、86 任务的视觉—触觉—动作数据训练双流世界模型，并用 60Hz 触觉反射闭环纠偏。 |
| [UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://arxiv.org/abs/2603.22264) | 2026-03 | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html) | 将 50K 轨迹、八种灵巧手、FAAS 统一动作空间、3D VLA 与便携采集装置组成 universal dexterous foundation suite。 |
| [Learning Versatile Humanoid Manipulation with Touch Dreaming](https://arxiv.org/abs/2604.13015) | 2026-04 | arXiv | 把低身稳定控制、全身 VR 数据采集和 touch dreaming 结合，使 humanoid policy 同时预测动作块、未来关节力与触觉 latent。 |
| [UniTacVLA: Unified Tactile Understanding and Prediction in Vision Language Action Models](https://arxiv.org/abs/2606.31723) | 2026-06 | arXiv | 以统一 tactile latent 同时建模当前接触语义和未来变化，再用 tactile-action mixed controller 高频修正低频动作块。 |

## 同行评审锚点

| 工作 | Venue | arXiv |
|---|---|---|
| [OmniH2O: Universal and Dexterous Human-to-Humanoid Whole-Body Teleoperation and Learning](https://proceedings.mlr.press/v270/he25b.html) | CoRL 2024 | [2406.08858](https://arxiv.org/abs/2406.08858) |
| [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html) | RSS 2025 | [2503.02881](https://arxiv.org/abs/2503.02881) |
| [DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://proceedings.mlr.press/v305/xu25b.html) | CoRL 2025 | [2505.21864](https://arxiv.org/abs/2505.21864) |
| [UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html) | CVPR 2026 | [2603.22264](https://arxiv.org/abs/2603.22264) |
| [Cross-Hand Latent Representation for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Jiang_Cross-Hand_Latent_Representation_for_Vision-Language-Action_Models_CVPR_2026_paper.html) | CVPR 2026 | [2603.10158](https://arxiv.org/abs/2603.10158) |

## 成熟度、瓶颈与战略判断

**成熟度。** 真实机器人证据显著增强，但硬件、传感器和 benchmark 仍碎片化。

**关键瓶颈。**

- 触觉硬件一致性
- 高频同步数据
- 跨手型动作空间
- 长时接触误差
- 安全与耐久

**战略判断。** 具备硬件、数据协议和策略闭环的一体化团队更可能积累壁垒；单次炫技 demo 的可复制性有限。

<!-- 更新标记：灵巧操作 最后更新 2026.07 -->
