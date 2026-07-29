# 具身智能研究雷达

> **版本**：v1.0 · **数据截点**：2026 年 7 月 29 日<br>
> **主分析期**：2025 年 7 月—2026 年 6 月 · **前瞻快照**：2026 年 7 月 1–29 日

---


## 执行摘要

> **版本**：v1.0 · **更新日期**：2026 年 7 月 29 日<br>
> **主分析期**：2025.07–2026.06 · **精读**：84 篇 · **官方评审锚点**：30 条

过去 12 个月最显眼的共识是 VLA / generalist policy 的论文数量急升；更有战略价值的变化却发生在“模型之外”：实时调度、动作验证与恢复、部署数据飞轮、可执行 world model、视触觉闭环和跨本体接口。**综合判断（推断）：**具身智能正在从“能输出动作”进入“能在物理世界持续运行、发现错误并学习”的阶段。

### 六个年度判断

1. **基础模型是最大共识，不再是最早信号。** 主分析期统一查询口径下，具身基础模型候选占比最高；方向已经拥挤，差异转向执行、数据与后训练。
2. **大小脑的真正拐点是实时系统。** fast–slow 名称本身价值有限，completion gating、continuous reasoning、verifier 和 3D trace 才是接口创新。
3. **world model 的淘汰赛开始。** 能否在同算力下提高闭环规划、RL 样本效率或失败恢复，将把控制模型与普通视频生成分开。
4. **触觉从“小众传感器”变成领先指标。** 它最可能先在接触失败恢复、材料/滑移预测和灵巧 world model 中兑现。
5. **跨本体更可能通过共享表示 + 小型 adapter 实现。** “一个权重直接覆盖所有机器人”的证据仍不足。
6. **数据护城河正在迁移到部署闭环。** 未来关键指标不是总小时，而是失败覆盖、修正效率和新任务上线速度。

### 数据概览

<div class="radar-kpis">
  <div class="radar-kpi"><strong>1841</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>633</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>59/84</strong><span>精读真机确认</span></div>
  <div class="radar-kpi"><strong>16/84</strong><span>精读明确开放披露</span></div>
</div>

| 深度指标 | 分子 / 分母 | 说明 |
|---|---:|---|
| 真实机器人 | 59/84 | 摘要或核验页明确披露 |
| 多任务 | 18/84 | 不把任务变体自动当作多任务 |
| 跨本体 | 20/84 | 至少两类机器人/硬件 |
| 长时序 | 21/84 | 明确长时、多阶段或连续任务 |
| 代码/数据/模型开放 | 16/84 | “will release” 不等于已开放 |

### 对研究布局与投资观察的含义

| 观察对象 | 应追问的证据 | 高风险信号 |
|---|---|---|
| VLA 团队 | 真机时延、失败恢复、部署数据回流 | 只报告仿真平均成功率 |
| 世界模型团队 | 同算力控制增益、model bias、闭环时长 | 只展示视频质量 |
| 灵巧/触觉团队 | 跨手型、跨传感器、长时接触 | 单次定制 demo |
| 数据团队 | 有效多样性、失败覆盖、下游边际增益 | 只强调总小时/总帧数 |
| 开源项目 | 第三方复现、外部采用、活跃维护 | 只放模型名或未来承诺 |

### 最重要的非共识机会

按当前证据排序：**实时 VLA 执行栈、verifier/自纠错、部署数据飞轮、控制导向 world model、触觉预测通道、跨本体动作接口、3D trace，以及高风险的 Embodied Agent OS。** 详见[未来判断](/analysis/weak-signals)。

<!-- 更新标记：执行摘要 最后更新 2026.07 -->

---


## 月度研究雷达

> 主分析期按 arXiv v1 月份归档；2026 年 7 月只覆盖 1–29 日。候选数量衡量统一查询下的研究密度，精读样本用于技术判断。

| 月份 | 候选数 | 同比增量 | 数量主导方向 | 精读 | 真机确认 |
|---|---:|---:|---|---:|---:|
| [2025 年 7 月](/monthly/2025-07) | 57 | +31 | 通用机器人学习（23） | 7 | 6/7 |
| [2025 年 8 月](/monthly/2025-08) | 75 | +55 | 具身基础模型（29） | 7 | 5/7 |
| [2025 年 9 月](/monthly/2025-09) | 138 | +97 | 具身基础模型（57） | 7 | 5/7 |
| [2025 年 10 月](/monthly/2025-10) | 140 | +79 | 具身基础模型（72） | 7 | 4/7 |
| [2025 年 11 月](/monthly/2025-11) | 119 | +84 | 具身基础模型（65） | 7 | 5/7 |
| [2025 年 12 月](/monthly/2025-12) | 124 | +84 | 具身基础模型（59） | 7 | 5/7 |
| [2026 年 1 月](/monthly/2026-01) | 85 | +55 | 具身基础模型（36） | 7 | 3/7 |
| [2026 年 2 月](/monthly/2026-02) | 174 | +130 | 具身基础模型（84） | 7 | 5/7 |
| [2026 年 3 月](/monthly/2026-03) | 234 | +155 | 具身基础模型（104） | 7 | 5/7 |
| [2026 年 4 月](/monthly/2026-04) | 134 | +92 | 具身基础模型（57） | 7 | 4/7 |
| [2026 年 5 月](/monthly/2026-05) | 203 | +95 | 具身基础模型（101） | 7 | 6/7 |
| [2026 年 6 月](/monthly/2026-06) | 358 | +251 | 具身基础模型（162） | 7 | 6/7 |
| [2026 年 7 月](/monthly/2026-07) | 166 | 快照 | 具身基础模型（85） | 6 | 3/6 |

### 怎么读月度页

1. 先看绝对数量和同比，判断是否只是小样本百分比。
2. 再看精读论文的真机、跨任务/本体、长时序和开放资产。
3. 用官方同行评审锚点区分“arXiv 密集”与“已有独立评审路线”。
4. 最后看弱信号与反证；前者寻找未来，后者防止把命名潮误判为能力跃迁。

<!-- 更新标记：月度总览 最后更新 2026.07 -->

---


## 2025 年 7 月研究雷达

> **统计口径。** 自动宽召回候选用于数量结构；7 篇精读样本用于实验与开放性指标。同比月为 2024-07。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>57</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>6/7</strong><span>摘要确认真机</span></div>
  <div class="radar-kpi"><strong>0</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

人类视频开始被拆成可迁移的动作先验；与此同时，空间增强很热，但尚未等于通用性。

### 主题结构

| 主方向 | 本月候选 | 占比 | 同比候选 | 同比增量 |
|---|---:|---:|---:|---:|
| [具身基础模型](/directions/foundation-models) | 17 | 29.8% | 4 | +13 |
| [大小脑与双系统](/directions/dual-system) | 1 | 1.8% | 0 | +1 |
| [灵巧操作](/directions/dexterous-manipulation) | 12 | 21.1% | 6 | +6 |
| [世界模型](/directions/world-models) | 4 | 7.0% | 3 | +1 |
| [通用机器人学习](/directions/general-robot-learning) | 23 | 40.4% | 13 | +10 |

> 自动宽召回对 VLA 命名敏感，不能单独解释为能力增长；大小脑类因常使用隐式架构命名，自动数量是保守下界。

### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 人类视频开始被拆成可迁移的动作先验

**变化。** EC-Flow、H-RDT 与 GR-3 分别从无动作标签视频、双臂人类操作和通用数据配方切入，信号尚未形成单一范式，但都在绕开机器人示教瓶颈。

**对比。** 同比基线中此类工作多停留在表征对齐；本月开始把人类数据直接接入动作生成或双臂策略。

**证据。** [EC-Flow: Enabling Versatile Robotic Manipulation from Action-Unlabeled Videos via Embodiment-Centric Flow](https://arxiv.org/abs/2507.06224)；[H-RDT: Human Manipulation Enhanced Bimanual Robotic Manipulation](https://arxiv.org/abs/2507.23523)；[GR-3 Technical Report](https://arxiv.org/abs/2507.15493)

**成熟度与瓶颈。** 多为预训练或受控任务验证，跨本体稳定性仍弱。 主要瓶颈是人—机动作空间对齐，以及视频中不可观测的力与接触。。

**战略含义。** 优先跟踪能同时拥有数据转换器、机器人数据闭环和跨本体评测的团队。

</div>

<div class="trend-card">

#### <span class="signal signal-c">C · 弱信号</span> “大脑—小脑”正在从二层变成三系统

**变化。** TriVLA 把高层语义、低层动作与 episodic world model 明确拆分；EmbodieDreamer 则让世界模型承担 real-to-sim-to-real 中介。

**对比。** 早期 planner–policy 通常只有两层；本月出现把记忆/预测独立成第三模块的尝试。

**证据。** [TriVLA: A Triple-System-Based Unified Vision-Language-Action Model with Episodic World Modeling for General Robot Control](https://arxiv.org/abs/2507.01424)；[EmbodieDreamer: Advancing Real2Sim2Real Transfer for Policy Training via Embodied World Modeling](https://arxiv.org/abs/2507.05198)

**成熟度与瓶颈。** 概念结构清晰，但独立团队和长时序真机证据不足。 主要瓶颈是模块间误差传递与实时调度。。

**战略含义。** 将“第三系统”作为观察项，不把新架构命名直接当作能力跃迁。

</div>

<div class="trend-card">

#### <span class="signal signal-d">D · 反证/降温</span> 空间增强很热，但尚未等于通用性

**变化。** Evo-0 用外部视觉几何模型补足 VLA 的 3D 表征，真实机器人结果积极；但没有同时证明跨本体、长时序和独立复现。

**对比。** 数量增量主要来自为 VLA 加适配器，而不是统一训练目标。

**证据。** [Evo-0: Vision-Language-Action Model with Implicit Spatial Understanding](https://arxiv.org/abs/2507.00416)

**成熟度与瓶颈。** 单点能力改善。 主要瓶颈是空间 benchmark 增益能否转化为开放环境成功率。。

**战略含义。** 投资研判应区分“VLA 组件供应商”与真正拥有数据和部署闭环的平台。

</div>

### 蛛丝马迹：小样本领先信号

| 弱信号 | 等级 | 下一道技术门槛 | 当前判断 |
|---|---|---|---|
| 人类视频开始被拆成可迁移的动作先验 | B | 人—机动作空间对齐，以及视频中不可观测的力与接触。 | 多为预训练或受控任务验证，跨本体稳定性仍弱。 |
| “大脑—小脑”正在从二层变成三系统 | C | 模块间误差传递与实时调度。 | 概念结构清晰，但独立团队和长时序真机证据不足。 |

识别逻辑不是“论文少就更前沿”，而是寻找多个弱证据是否指向同一个尚未被主流命名的瓶颈迁移。完整方法见[弱信号探测与未来判断](/analysis/weak-signals)。

### 本月精读论文

| 论文 | v1 日期 | 主方向 | 一句话贡献 | 证据标签 |
|---|---|---|---|---|
| [TriVLA: A Triple-System-Based Unified Vision-Language-Action Model with Episodic World Modeling for General Robot Control](https://arxiv.org/abs/2507.01424) | 2025-07-02 | 大小脑与双系统 | 用 VLM、视频扩散式情景世界模型和 flow-matching 低层策略组成三系统，在约 36 Hz 下兼顾记忆、未来预测与真实机器人长时序控制。 | 真机 · 长时序 · 开放资产 |
| [EmbodieDreamer: Advancing Real2Sim2Real Transfer for Policy Training via Embodied World Modeling](https://arxiv.org/abs/2507.05198) | 2025-07-07 | 世界模型 | 联合可微物理参数对齐与条件视频扩散外观对齐，缩小 Real2Sim2Real 差距，并报告真实任务平均成功率提升 29.17%。 | 真机 · 开放资产 |
| [GR-3 Technical Report](https://arxiv.org/abs/2507.15493) | 2025-07-21 | 具身基础模型 | GR-3 以网络视觉语言数据、VR 人类轨迹和机器人轨迹协同训练，展示新物体/环境/抽象指令、双臂移动与长时序真实任务泛化。 | 真机 · 多任务 · 长时序 |
| [H-RDT: Human Manipulation Enhanced Bimanual Robotic Manipulation](https://arxiv.org/abs/2507.23523) | 2025-07-31 | 通用机器人学习 | 以 2B diffusion transformer 先学大规模第一视角人类手部先验，再用模块化动作编解码器适配不同机器人，显著提升双臂真实操作。 | 真机 · 跨本体 |
| [Evo-0: Vision-Language-Action Model with Implicit Spatial Understanding](https://arxiv.org/abs/2507.00416) | 2025-07-01 | 具身基础模型 | 把现成视觉几何基础模型的深度感知特征以即插即用方式注入 VLA，在无需额外深度传感器的前提下提升仿真与真实场景的空间操作。 | 真机 |
| [EC-Flow: Enabling Versatile Robotic Manipulation from Action-Unlabeled Videos via Embodiment-Centric Flow](https://arxiv.org/abs/2507.06224) | 2025-07-08 | 通用机器人学习 | 从无动作标签视频预测 embodiment-centric flow，再借 URDF 约束转成可执行动作，覆盖遮挡、柔性物体及非位移操作。 | 真机 |
| [Towards Human-level Dexterity via Robot Learning](https://arxiv.org/abs/2507.09117) | 2025-07-12 | 灵巧操作 | 以结构化探索、采样式规划和视触觉人类示范为主线，总结可扩展多指灵巧操作强化学习的一套方法体系。 | 摘要未确认 |

精读样本明确开放披露 2/7；只在摘要、comment 或已核验项目页明确披露时记为“是”。

### 同行评审锚点

| 工作 | 官方证据 | 为什么可作为本月锚点 |
|---|---|---|
| — | — | 本月首次公开的精读样本尚无可安全归属到该月的官方录用证据；这不等于论文质量较低。 |

### 反证与信号质量检查

- 多篇论文共享相同数据、模型或作者团队时，不按独立证据重复加权。
- 单一 benchmark 提升若没有真实机器人迁移，不足以升级为 A 级趋势。
- “open-source / will release” 与实际可下载、可复现实验分开记录。
- 世界模型必须展示动作、规划、控制或数据生成价值；纯视频质量不计。

<!-- 更新标记：2025-07 月度雷达 最后更新 2026.07 -->

---


## 2025 年 8 月研究雷达

> **统计口径。** 自动宽召回候选用于数量结构；7 篇精读样本用于实验与开放性指标。同比月为 2024-08。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>75</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>5/7</strong><span>摘要确认真机</span></div>
  <div class="radar-kpi"><strong>1</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

视频生成器开始越过“数据增强”，直接扮演策略；与此同时，世界模型仍更像适配器，而非可靠规划器。

### 主题结构

| 主方向 | 本月候选 | 占比 | 同比候选 | 同比增量 |
|---|---:|---:|---:|---:|
| [具身基础模型](/directions/foundation-models) | 29 | 38.7% | 0 | +29 |
| [大小脑与双系统](/directions/dual-system) | 0 | 0.0% | 0 | 0 |
| [灵巧操作](/directions/dexterous-manipulation) | 11 | 14.7% | 8 | +3 |
| [世界模型](/directions/world-models) | 6 | 8.0% | 1 | +5 |
| [通用机器人学习](/directions/general-robot-learning) | 29 | 38.7% | 11 | +18 |

> 自动宽召回对 VLA 命名敏感，不能单独解释为能力增长；大小脑类因常使用隐式架构命名，自动数量是保守下界。

### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 视频生成器开始越过“数据增强”，直接扮演策略

**变化。** Video Generators are Robot Policies、Masquerade 与 DiWA 分别尝试直接控制、视频编辑迁移和用世界模型适配 diffusion policy。

**对比。** 相较 7 月主要把视频当作数据，本月首次集中出现“生成—预测—控制”连续化。

**证据。** [Video Generators are Robot Policies](https://arxiv.org/abs/2508.00795)；[Masquerade: Learning from In-the-wild Human Videos using Data-Editing](https://arxiv.org/abs/2508.09976)；[DiWA: Diffusion Policy Adaptation with World Models](https://arxiv.org/abs/2508.03645)

**成熟度与瓶颈。** 仿真与受控任务为主。 主要瓶颈是视频像素质量与可执行动作之间仍存在逆动力学鸿沟。。

**战略含义。** 关注能用执行成功而非视频指标训练生成模型的团队。

</div>

<div class="trend-card">

#### <span class="signal signal-c">C · 弱信号</span> 触觉开始进入 VLA 统一语义空间

**变化。** OmniVTLA 不再把触觉仅作为低层状态，而是与视觉、语言和动作对齐。

**对比。** 同比基线更多是触觉专用策略；本月出现 foundation-model 接口层的整合。

**证据。** [OmniVTLA: Vision-Tactile-Language-Action Models with Semantic-Aligned Tactile Sensing](https://arxiv.org/abs/2508.08706)

**成熟度与瓶颈。** 单团队早期信号。 主要瓶颈是传感器异构、跨硬件标定和公开数据规模。。

**战略含义。** 触觉价值可能先体现在接触失败恢复，而非通用语义理解。

</div>

<div class="trend-card">

#### <span class="signal signal-d">D · 反证/降温</span> 世界模型仍更像适配器，而非可靠规划器

**变化。** DiWA 与 GWM 展示适配和场景预测价值，但闭环规划收益、长时序误差和跨任务复现仍不充分。

**对比。** 论文数量上升快于控制证据升级。

**证据。** [DiWA: Diffusion Policy Adaptation with World Models](https://arxiv.org/abs/2508.03645)；[GWM: Towards Scalable Gaussian World Models for Robotic Manipulation](https://arxiv.org/abs/2508.17600)

**成熟度与瓶颈。** PoC 到早期验证。 主要瓶颈是预测误差在闭环中的累积。。

**战略含义。** 把是否改善规划成功率设为世界模型的硬门槛。

</div>

### 蛛丝马迹：小样本领先信号

| 弱信号 | 等级 | 下一道技术门槛 | 当前判断 |
|---|---|---|---|
| 视频生成器开始越过“数据增强”，直接扮演策略 | B | 视频像素质量与可执行动作之间仍存在逆动力学鸿沟。 | 仿真与受控任务为主。 |
| 触觉开始进入 VLA 统一语义空间 | C | 传感器异构、跨硬件标定和公开数据规模。 | 单团队早期信号。 |

识别逻辑不是“论文少就更前沿”，而是寻找多个弱证据是否指向同一个尚未被主流命名的瓶颈迁移。完整方法见[弱信号探测与未来判断](/analysis/weak-signals)。

### 本月精读论文

| 论文 | v1 日期 | 主方向 | 一句话贡献 | 证据标签 |
|---|---|---|---|---|
| [EO-1: An Open Unified Embodied Foundation Model for General Robot Control](https://arxiv.org/abs/2508.21112) | 2025-08-28 | 具身基础模型 | EO-1 在统一 decoder 中结合自回归与 flow matching，以 EO-Data1.5M 做交错 vision-text-action 预训练，覆盖多本体长时序灵巧控制。 | 真机 · 跨本体 · 长时序 · 开放资产 |
| [DiWA: Diffusion Policy Adaptation with World Models](https://arxiv.org/abs/2508.03645) | 2025-08-05 | 通用机器人学习 | 用一次训练的离线世界模型承载 diffusion policy 的强化学习适配，避开数百万次真实交互，并在 CALVIN 与真实技能上验证。 | 真机 · 多任务 · 开放资产 |
| [RICL: Adding In-Context Adaptability to Pre-Trained Vision-Language-Action Models](https://arxiv.org/abs/2508.02062) | 2025-08-04 | 具身基础模型 | 通过检索 10–20 条新任务示范，把 in-context adaptation 后置注入预训练 π0-FAST，无需参数更新即可快速教新任务。 | 多任务 · 开放资产 |
| [OmniVTLA: Vision-Tactile-Language-Action Models with Semantic-Aligned Tactile Sensing](https://arxiv.org/abs/2508.08706) | 2025-08-12 | 灵巧操作 | 以双路触觉编码器和 135K 样本 ObjTac 对齐视觉、语言与多类触觉传感器，在夹爪和灵巧手真实任务上显著增益。 | 真机 · 开放资产 |
| [Video Generators are Robot Policies](https://arxiv.org/abs/2508.00795) | 2025-08-01 | 通用机器人学习 | 把机器人视频生成与动作生成端到端联合，显示无动作视频可在少量机器人示范下提升新物体、背景和任务的真实泛化。 | 真机 |
| [Masquerade: Learning from In-the-wild Human Videos using Data-Editing](https://arxiv.org/abs/2508.09976) | 2025-08-13 | 通用机器人学习 | 把野外第一视角人类视频经 3D 手姿态、去人体和机器人叠加编辑为机器人化示范，675K 帧预训练后仅需每任务 50 条机器人示范。 | 长时序 |
| [GWM: Towards Scalable Gaussian World Models for Robotic Manipulation](https://arxiv.org/abs/2508.17600) | 2025-08-25 | 世界模型 | 以 3D VAE、latent DiT 与 Gaussian Splatting 预测动作后的三维高斯场，既作表征预训练也作模型式 RL 的神经模拟器。 | 真机 |

精读样本明确开放披露 4/7；只在摘要、comment 或已核验项目页明确披露时记为“是”。

### 同行评审锚点

| 工作 | 官方证据 | 为什么可作为本月锚点 |
|---|---|---|
| [Long-VLA: Unleashing Long-Horizon Capability of Vision Language Action Model for Robot Manipulation](https://arxiv.org/abs/2508.19958) | [CoRL 2025](https://proceedings.mlr.press/v305/fan25a.html) | PMLR official paper page lists the work in Proceedings of The 9th Conference on Robot Learning, held 27–30 Sep 2025. |

### 反证与信号质量检查

- 多篇论文共享相同数据、模型或作者团队时，不按独立证据重复加权。
- 单一 benchmark 提升若没有真实机器人迁移，不足以升级为 A 级趋势。
- “open-source / will release” 与实际可下载、可复现实验分开记录。
- 世界模型必须展示动作、规划、控制或数据生成价值；纯视频质量不计。

<!-- 更新标记：2025-08 月度雷达 最后更新 2026.07 -->

---


## 2025 年 9 月研究雷达

> **统计口径。** 自动宽召回候选用于数量结构；7 篇精读样本用于实验与开放性指标。同比月为 2024-09。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>138</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>5/7</strong><span>摘要确认真机</span></div>
  <div class="radar-kpi"><strong>0</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

flow matching 正在成为通用策略的新执行底座；与此同时，在线搜索被塞进 VLA 推理环。

### 主题结构

| 主方向 | 本月候选 | 占比 | 同比候选 | 同比增量 |
|---|---:|---:|---:|---:|
| [具身基础模型](/directions/foundation-models) | 57 | 41.3% | 5 | +52 |
| [大小脑与双系统](/directions/dual-system) | 2 | 1.4% | 0 | +2 |
| [灵巧操作](/directions/dexterous-manipulation) | 25 | 18.1% | 7 | +18 |
| [世界模型](/directions/world-models) | 12 | 8.7% | 4 | +8 |
| [通用机器人学习](/directions/general-robot-learning) | 42 | 30.4% | 25 | +17 |

> 自动宽召回对 VLA 命名敏感，不能单独解释为能力增长；大小脑类因常使用隐式架构命名，自动数量是保守下界。

### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> flow matching 正在成为通用策略的新执行底座

**变化。** ManiFlow、EC-Flow 与 FLOWER 在通用操控、无标签视频和轻量 generalist policy 三条线上同时采用 flow。

**对比。** 相比同比基线的 diffusion policy 主导，flow 的速度与连续控制优势开始跨团队扩散。

**证据。** [ManiFlow: A General Robot Manipulation Policy via Consistency Flow Training](https://arxiv.org/abs/2509.01819)；[EC-Flow: Enabling Versatile Robotic Manipulation from Action-Unlabeled Videos via Embodiment-Centric Flow](https://arxiv.org/abs/2507.06224)；[FLOWER: Democratizing Generalist Robot Policies with Efficient Vision-Language-Action Flow Policies](https://arxiv.org/abs/2509.04996)

**成熟度与瓶颈。** 多团队、跨月，但统一真机 benchmark 尚未形成。 主要瓶颈是训练稳定性和闭环重规划。。

**战略含义。** 基础设施层应支持 diffusion 与 flow 共存，而不是押注单一采样器。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 灵巧操作的数据表示从关节轨迹转向接触与第一视角

**变化。** OpenEgo、Text2Touch 与 CEDex 分别用 egocentric 数据、语言设计奖励和接触表示扩大灵巧操作监督。

**对比。** 本月信号不在更复杂的手，而在更可迁移的数据坐标系。

**证据。** [OpenEgo: A Large-Scale Multimodal Egocentric Dataset for Dexterous Manipulation](https://arxiv.org/abs/2509.05513)；[Text2Touch: Tactile In-Hand Manipulation with LLM-Designed Reward Functions](https://arxiv.org/abs/2509.07445)；[CEDex: Cross-Embodiment Dexterous Grasp Generation at Scale from Human-like Contact Representations](https://arxiv.org/abs/2509.24661)

**成熟度与瓶颈。** 数据与表示创新先于通用真机策略。 主要瓶颈是接触标注成本与不同手型的对应关系。。

**战略含义。** 长期价值更可能沉淀在接触数据协议与手型无关表示。

</div>

<div class="trend-card">

#### <span class="signal signal-c">C · 弱信号</span> 在线搜索被塞进 VLA 推理环

**变化。** VLA-Reasoner 用 online MCTS 把推理从一次性 chain-of-thought 变成动作候选搜索。

**对比。** 此前 reasoning 多是离线语义提示；这是面向执行验证的早期转向。

**证据。** [VLA-Reasoner: Empowering Vision-Language-Action Models with Reasoning via Online Monte Carlo Tree Search](https://arxiv.org/abs/2509.22643)

**成熟度与瓶颈。** 单项高新颖度工作。 主要瓶颈是搜索延迟、奖励可信度与真实机器人安全探索。。

**战略含义。** 观察后续是否出现轻量 verifier 或搜索蒸馏路线。

</div>

### 蛛丝马迹：小样本领先信号

| 弱信号 | 等级 | 下一道技术门槛 | 当前判断 |
|---|---|---|---|
| 灵巧操作的数据表示从关节轨迹转向接触与第一视角 | B | 接触标注成本与不同手型的对应关系。 | 数据与表示创新先于通用真机策略。 |
| 在线搜索被塞进 VLA 推理环 | C | 搜索延迟、奖励可信度与真实机器人安全探索。 | 单项高新颖度工作。 |

识别逻辑不是“论文少就更前沿”，而是寻找多个弱证据是否指向同一个尚未被主流命名的瓶颈迁移。完整方法见[弱信号探测与未来判断](/analysis/weak-signals)。

### 本月精读论文

| 论文 | v1 日期 | 主方向 | 一句话贡献 | 证据标签 |
|---|---|---|---|---|
| [OpenEgo: A Large-Scale Multimodal Egocentric Dataset for Dexterous Manipulation](https://arxiv.org/abs/2509.05513) | 2025-09-05 | 通用机器人学习 | OpenEgo 统一六个公开视频集为 1107 小时、290 任务、600+ 环境的手姿态与时间定位动作原语数据，服务灵巧 VLA 预训练。 | 开放资产 |
| [ManiFlow: A General Robot Manipulation Policy via Consistency Flow Training](https://arxiv.org/abs/2509.01819) | 2025-09-01 | 通用机器人学习 | ManiFlow 用 consistency flow 将高维动作生成压到 1–2 步，并在单臂、双臂与人形真实平台上验证多模态通用操作。 | 真机 · 多任务 |
| [Parse-Augment-Distill: Learning Generalizable Bimanual Visuomotor Policies from Single Human Video](https://arxiv.org/abs/2509.20286) | 2025-09-24 | 通用机器人学习 | PAD 将单条人类视频解析成机器人关键点动作，用双臂任务与运动规划无仿真扩增，再蒸馏成可泛化视觉运动策略。 | 真机 · 多任务 |
| [VLA-Reasoner: Empowering Vision-Language-Action Models with Reasoning via Online Monte Carlo Tree Search](https://arxiv.org/abs/2509.22643) | 2025-09-26 | 大小脑与双系统 | VLA-Reasoner 以世界模型 rollout、KDE 置信采样和 MCTS 为现成 VLA 增加测试时前瞻，在真实长时序任务上纠偏。 | 真机 · 长时序 |
| [Text2Touch: Tactile In-Hand Manipulation with LLM-Designed Reward Functions](https://arxiv.org/abs/2509.07445) | 2025-09-09 | 灵巧操作 | Text2Touch 让 LLM 为 70+ 环境变量设计短奖励，经 sim-to-real 蒸馏在四指触觉手上完成多轴 in-hand rotation。 | 真机 |
| [Latent Action Pretraining Through World Modeling](https://arxiv.org/abs/2509.18428) | 2025-09-22 | 世界模型 | LAWM 通过世界建模从无标签人/机器人视频学习 latent action，使较小模仿学习模型跨任务、环境与本体迁移。 | 真机 |
| [CEDex: Cross-Embodiment Dexterous Grasp Generation at Scale from Human-like Contact Representations](https://arxiv.org/abs/2509.24661) | 2025-09-29 | 灵巧操作 | CEDex 用人类式接触表征、拓扑合并与 SDF 物理约束，把同一抓取先验扩展到任意形态的灵巧手并规模化生成数据。 | 跨本体 |

精读样本明确开放披露 1/7；只在摘要、comment 或已核验项目页明确披露时记为“是”。

### 同行评审锚点

| 工作 | 官方证据 | 为什么可作为本月锚点 |
|---|---|---|
| — | — | 本月首次公开的精读样本尚无可安全归属到该月的官方录用证据；这不等于论文质量较低。 |

### 反证与信号质量检查

- 多篇论文共享相同数据、模型或作者团队时，不按独立证据重复加权。
- 单一 benchmark 提升若没有真实机器人迁移，不足以升级为 A 级趋势。
- “open-source / will release” 与实际可下载、可复现实验分开记录。
- 世界模型必须展示动作、规划、控制或数据生成价值；纯视频质量不计。

<!-- 更新标记：2025-09 月度雷达 最后更新 2026.07 -->

---


## 2025 年 10 月研究雷达

> **统计口径。** 自动宽召回候选用于数量结构；7 篇精读样本用于实验与开放性指标。同比月为 2024-10。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>140</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>4/7</strong><span>摘要确认真机</span></div>
  <div class="radar-kpi"><strong>0</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

fast–slow 从隐式分工变成显式训练目标；与此同时，视频驱动双臂学习成为数据规模化的第二战场。

### 主题结构

| 主方向 | 本月候选 | 占比 | 同比候选 | 同比增量 |
|---|---:|---:|---:|---:|
| [具身基础模型](/directions/foundation-models) | 72 | 51.4% | 8 | +64 |
| [大小脑与双系统](/directions/dual-system) | 2 | 1.4% | 0 | +2 |
| [灵巧操作](/directions/dexterous-manipulation) | 13 | 9.3% | 12 | +1 |
| [世界模型](/directions/world-models) | 16 | 11.4% | 14 | +2 |
| [通用机器人学习](/directions/general-robot-learning) | 37 | 26.4% | 27 | +10 |

> 自动宽召回对 VLA 命名敏感，不能单独解释为能力增长；大小脑类因常使用隐式架构命名，自动数量是保守下界。

### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> fast–slow 从隐式分工变成显式训练目标

**变化。** VLA-R1、MoTVLA 与上月 VLA-Reasoner 分别用推理增强、统一快慢推理和在线搜索建立高层思考—低层动作分工。

**对比。** 相较 7 月的架构试验，已有三个独立作者团队连续出现。

**证据。** [VLA-R1: Enhancing Reasoning in Vision-Language-Action Models](https://arxiv.org/abs/2510.01623)；[MoTVLA: A Vision-Language-Action Model with Unified Fast-Slow Reasoning](https://arxiv.org/abs/2510.18337)；[VLA-Reasoner: Empowering Vision-Language-Action Models with Reasoning via Online Monte Carlo Tree Search](https://arxiv.org/abs/2509.22643)

**成熟度与瓶颈。** 新兴架构簇，真实机器人延迟与失败恢复仍待验证。 主要瓶颈是推理 token 与控制频率的冲突。。

**战略含义。** 大小脑的竞争焦点将从模型大小转向调度、验证与恢复。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 世界模型开始进入 VLA 后训练

**变化。** VLA-RFT 用 world simulator 给可验证奖励，Ctrl-World 强调可控生成，Latent Action Pretraining 则把预测表征回流到动作学习。

**对比。** 8 月还以适配为主，本月开始直接改变策略训练目标。

**证据。** [VLA-RFT: Vision-Language-Action Reinforcement Fine-tuning with Verified Rewards in World Simulators](https://arxiv.org/abs/2510.00406)；[Ctrl-World: A Controllable Generative World Model for Robot Manipulation](https://arxiv.org/abs/2510.10125)；[Latent Action Pretraining Through World Modeling](https://arxiv.org/abs/2509.18428)

**成熟度与瓶颈。** 训练闭环已经出现，仿真偏差仍高。 主要瓶颈是奖励投机与 simulator bias。。

**战略含义。** 优先看同时报告模型预测质量和策略真实成功率的工作。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 视频驱动双臂学习成为数据规模化的第二战场

**变化。** DexMan、Parse-Augment-Distill 与真实人类活动视频预训练共同指向少机器人示教的双臂学习。

**对比。** 从 7 月单项数据转换扩散为生成视频、单视频蒸馏和大规模人类活动三类路线。

**证据。** [DexMan: Learning Bimanual Dexterous Manipulation from Human and Generated Videos](https://arxiv.org/abs/2510.08475)；[Parse-Augment-Distill: Learning Generalizable Bimanual Visuomotor Policies from Single Human Video](https://arxiv.org/abs/2509.20286)；[Scalable Vision-Language-Action Model Pretraining for Robotic Manipulation with Real-Life Human Activity Videos](https://arxiv.org/abs/2510.21571)

**成熟度与瓶颈。** 多团队验证，硬件与任务覆盖仍有限。 主要瓶颈是双臂同步、遮挡和接触力缺失。。

**战略含义。** 数据引擎应优先解决可执行性过滤，而不是只扩大视频总量。

</div>

### 蛛丝马迹：小样本领先信号

| 弱信号 | 等级 | 下一道技术门槛 | 当前判断 |
|---|---|---|---|
| 世界模型开始进入 VLA 后训练 | B | 奖励投机与 simulator bias。 | 训练闭环已经出现，仿真偏差仍高。 |
| 视频驱动双臂学习成为数据规模化的第二战场 | B | 双臂同步、遮挡和接触力缺失。 | 多团队验证，硬件与任务覆盖仍有限。 |

识别逻辑不是“论文少就更前沿”，而是寻找多个弱证据是否指向同一个尚未被主流命名的瓶颈迁移。完整方法见[弱信号探测与未来判断](/analysis/weak-signals)。

### 本月精读论文

| 论文 | v1 日期 | 主方向 | 一句话贡献 | 证据标签 |
|---|---|---|---|---|
| [X-VLA: Soft-Prompted Transformer as Scalable Cross-Embodiment Vision-Language-Action Model](https://arxiv.org/abs/2510.10274) | 2025-10-11 | 具身基础模型 | X-VLA 用每个数据源的软提示吸收跨本体异构数据，在 6 个仿真与 3 台真实机器人上兼顾灵巧性、适配速度和规模化。 | 真机 · 跨本体 |
| [Scalable Vision-Language-Action Model Pretraining for Robotic Manipulation with Real-Life Human Activity Videos](https://arxiv.org/abs/2510.21571) | 2025-10-24 | 通用机器人学习 | 将无脚本真实人类手部视频自动切分、描述并恢复 3D 动作，构成 100 万 episode/2600 万帧的 hand-VLA 预训练语料。 | 真机 · 多任务 |
| [VLA-R1: Enhancing Reasoning in Vision-Language-Action Models](https://arxiv.org/abs/2510.01623) | 2025-10-02 | 大小脑与双系统 | VLA-R1 用 RLVR/GRPO 与 13K 条 affordance-trajectory CoT 数据共同强化空间推理和动作执行，并覆盖仿真与真实机器人。 | 真机 |
| [Ctrl-World: A Controllable Generative World Model for Robot Manipulation](https://arxiv.org/abs/2510.10125) | 2025-10-11 | 世界模型 | Ctrl-World 以多视角预测、逐帧动作条件和姿态记忆支持通用策略的长时序 imagination rollout，用于低成本评估和改进。 | 长时序 |
| [MoTVLA: A Vision-Language-Action Model with Unified Fast-Slow Reasoning](https://arxiv.org/abs/2510.18337) | 2025-10-21 | 大小脑与双系统 | MoTVLA 让预训练 VLM 承担慢速语义规划、专用 transformer 生成快速运动分解，再驱动 action expert 实时执行。 | 真机 |
| [VLA-RFT: Vision-Language-Action Reinforcement Fine-tuning with Verified Rewards in World Simulators](https://arxiv.org/abs/2510.00406) | 2025-10-01 | 世界模型 | VLA-RFT 把真实交互训练的动作条件世界模型当可控模拟器，以可验证轨迹奖励在少于 400 步内完成 VLA 强化微调。 | 摘要未确认 |
| [DexMan: Learning Bimanual Dexterous Manipulation from Human and Generated Videos](https://arxiv.org/abs/2510.08475) | 2025-10-09 | 灵巧操作 | DexMan 从无标定第三视角人类或生成视频估计手物运动，以接触奖励在仿真人形机器人上学习双臂灵巧技能。 | 摘要未确认 |

精读样本明确开放披露 0/7；只在摘要、comment 或已核验项目页明确披露时记为“是”。

### 同行评审锚点

| 工作 | 官方证据 | 为什么可作为本月锚点 |
|---|---|---|
| — | — | 本月首次公开的精读样本尚无可安全归属到该月的官方录用证据；这不等于论文质量较低。 |

### 反证与信号质量检查

- 多篇论文共享相同数据、模型或作者团队时，不按独立证据重复加权。
- 单一 benchmark 提升若没有真实机器人迁移，不足以升级为 A 级趋势。
- “open-source / will release” 与实际可下载、可复现实验分开记录。
- 世界模型必须展示动作、规划、控制或数据生成价值；纯视频质量不计。

<!-- 更新标记：2025-10 月度雷达 最后更新 2026.07 -->

---


## 2025 年 11 月研究雷达

> **统计口径。** 自动宽召回候选用于数量结构；7 篇精读样本用于实验与开放性指标。同比月为 2024-11。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>119</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>5/7</strong><span>摘要确认真机</span></div>
  <div class="radar-kpi"><strong>1</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

世界模型终于开始用规划成功率证明自己；与此同时，VLA 开始从示范学习走向“从经验学习”。

### 主题结构

| 主方向 | 本月候选 | 占比 | 同比候选 | 同比增量 |
|---|---:|---:|---:|---:|
| [具身基础模型](/directions/foundation-models) | 65 | 54.6% | 7 | +58 |
| [大小脑与双系统](/directions/dual-system) | 1 | 0.8% | 0 | +1 |
| [灵巧操作](/directions/dexterous-manipulation) | 9 | 7.6% | 10 | -1 |
| [世界模型](/directions/world-models) | 13 | 10.9% | 3 | +10 |
| [通用机器人学习](/directions/general-robot-learning) | 31 | 26.1% | 15 | +16 |

> 自动宽召回对 VLA 命名敏感，不能单独解释为能力增长；大小脑类因常使用隐式架构命名，自动数量是保守下界。

### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> 世界模型终于开始用规划成功率证明自己

**变化。** WorldPlanner 把 action-conditioned visual world model 接入 MCTS/MPC；跨本体灵巧世界模型与 Ctrl-World 构成独立跟进。

**对比。** 比 8 月的生成/适配信号更接近闭环决策，但仍缺正式评审与规模化真机验证。

**证据。** [WorldPlanner: Monte Carlo Tree Search and MPC with Action-Conditioned Visual World Models](https://arxiv.org/abs/2511.03077)；[Scaling Cross-Embodiment World Models for Dexterous Manipulation](https://arxiv.org/abs/2511.01177)；[Ctrl-World: A Controllable Generative World Model for Robot Manipulation](https://arxiv.org/abs/2510.10125)

**成熟度与瓶颈。** 闭环 PoC。 主要瓶颈是长时预测误差和规划计算量。。

**战略含义。** 世界模型团队的关键里程碑应是同算力下的控制收益。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 跨本体迁移从模型适配转向数据分布设计

**变化。** X-Diffusion、InternData-A1 与 X-VLA 分别统一人类示范、合成数据和软提示式跨本体策略。

**对比。** 相比“为每台机器人做 adapter”，本月更多工作试图在数据和动作空间层消除本体差异。

**证据。** [X-Diffusion: Training Diffusion Policies on Cross-Embodiment Human Demonstrations](https://arxiv.org/abs/2511.04671)；[InternData-A1: Pioneering High-Fidelity Synthetic Data for Pre-training Generalist Policy](https://arxiv.org/abs/2511.16651)；[X-VLA: Soft-Prompted Transformer as Scalable Cross-Embodiment Vision-Language-Action Model](https://arxiv.org/abs/2510.10274)

**成熟度与瓶颈。** 多路线并行，尚无统一跨本体 benchmark。 主要瓶颈是动作坐标标准、硬件观测差异和负迁移。。

**战略含义。** 跨本体数据协议可能比单一 VLA 权重更具平台价值。

</div>

<div class="trend-card">

#### <span class="signal signal-c">C · 弱信号</span> VLA 开始从示范学习走向“从经验学习”

**变化。** π*0.6 明确强调 experience learning，与 VLA-RFT 的可验证奖励形成呼应。

**对比。** 共识仍是离线模仿；在线经验闭环尚属少数。

**证据。** [$π^{*}_{0.6}$: a VLA That Learns From Experience](https://arxiv.org/abs/2511.14759)；[VLA-RFT: Vision-Language-Action Reinforcement Fine-tuning with Verified Rewards in World Simulators](https://arxiv.org/abs/2510.00406)

**成熟度与瓶颈。** 两个高信号项目，独立复现弱。 主要瓶颈是真实机器人安全探索和奖励设计。。

**战略含义。** 跟踪拥有部署场景、可持续回收失败数据的团队。

</div>

### 蛛丝马迹：小样本领先信号

| 弱信号 | 等级 | 下一道技术门槛 | 当前判断 |
|---|---|---|---|
| 跨本体迁移从模型适配转向数据分布设计 | B | 动作坐标标准、硬件观测差异和负迁移。 | 多路线并行，尚无统一跨本体 benchmark。 |
| VLA 开始从示范学习走向“从经验学习” | C | 真实机器人安全探索和奖励设计。 | 两个高信号项目，独立复现弱。 |

识别逻辑不是“论文少就更前沿”，而是寻找多个弱证据是否指向同一个尚未被主流命名的瓶颈迁移。完整方法见[弱信号探测与未来判断](/analysis/weak-signals)。

### 本月精读论文

| 论文 | v1 日期 | 主方向 | 一句话贡献 | 证据标签 |
|---|---|---|---|---|
| [InternData-A1: Pioneering High-Fidelity Synthetic Data for Pre-training Generalist Policy](https://arxiv.org/abs/2511.16651) | 2025-11-20 | 通用机器人学习 | InternData-A1 以自动仿真流水线生成 63 万轨迹/7433 小时、4 本体/70 任务数据，报告纯合成预训练可匹配 π0 并零样本 sim-to-real。 | 真机 · 多任务 · 跨本体 · 长时序 · 开放资产 |
| [Scaling Cross-Embodiment World Models for Dexterous Manipulation](https://arxiv.org/abs/2511.01177) | 2025-11-03 | 世界模型 | 把不同人手/机器人手统一为 3D 粒子与末端位移场，以跨本体世界模型和 MPC 在新硬件上迁移刚体及柔性操作。 | 真机 · 跨本体 |
| [WorldPlanner: Monte Carlo Tree Search and MPC with Action-Conditioned Visual World Models](https://arxiv.org/abs/2511.03077) | 2025-11-04 | 世界模型 | WorldPlanner 用数小时无结构 play data 学动作条件视频世界模型、动作采样器和可选奖励，再以 MCTS+MPC 在真实机器人上规划。 | 真机 · 长时序 |
| [X-Diffusion: Training Diffusion Policies on Cross-Embodiment Human Demonstrations](https://arxiv.org/abs/2511.04671) | 2025-11-06 | 通用机器人学习 | X-Diffusion 将人类动作视为机器人动作的噪声对应物，只在高噪声层引入跨本体人类示范，五个真实任务平均提升 16%。 | 真机 · 跨本体 |
| [Dexterous Robotic Piano Playing at Scale](https://arxiv.org/abs/2511.02504) | 2025-11-04 | 灵巧操作 | OmniPianist 训练 2000+ 专项 RL 智能体并汇成百万轨迹 RP1M++，再以 flow transformer 蒸馏出覆盖近千曲目的双手策略。 | 多任务 |
| [$π^{*}_{0.6}$: a VLA That Learns From Experience](https://arxiv.org/abs/2511.14759) | 2025-11-18 | 具身基础模型 | RECAP 把示范、在线 rollout 与专家纠正统一为 advantage-conditioned VLA 强化学习，使 π*0.6 在家庭与商业设备任务中持续改进。 | 真机 |
| [DualVLA: Building a Generalizable Embodied Agent via Partial Decoupling of Reasoning and Action](https://arxiv.org/abs/2511.22134) | 2025-11-27 | 大小脑与双系统 | DualVLA 通过双层数据裁剪与双教师蒸馏缓解推理微调导致的动作退化，并提出按 reasoning/intention/action/alignment 分解的 VLA Score。 | 摘要未确认 |

精读样本明确开放披露 1/7；只在摘要、comment 或已核验项目页明确披露时记为“是”。

### 同行评审锚点

| 工作 | 官方证据 | 为什么可作为本月锚点 |
|---|---|---|
| [VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation](https://arxiv.org/abs/2511.15200) | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/He_VIRAL_Visual_Sim-to-Real_at_Scale_for_Humanoid_Loco-Manipulation_CVPR_2026_paper.html) | The CVF official open-access page lists the paper in the Proceedings of CVPR 2026, with authors, June 2026, and page numbers. |

### 反证与信号质量检查

- 多篇论文共享相同数据、模型或作者团队时，不按独立证据重复加权。
- 单一 benchmark 提升若没有真实机器人迁移，不足以升级为 A 级趋势。
- “open-source / will release” 与实际可下载、可复现实验分开记录。
- 世界模型必须展示动作、规划、控制或数据生成价值；纯视频质量不计。

<!-- 更新标记：2025-11 月度雷达 最后更新 2026.07 -->

---


## 2025 年 12 月研究雷达

> **统计口径。** 自动宽召回候选用于数量结构；7 篇精读样本用于实验与开放性指标。同比月为 2024-12。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>124</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>5/7</strong><span>摘要确认真机</span></div>
  <div class="radar-kpi"><strong>2</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

世界模型与搜索/规划形成方法簇；与此同时，低成本示范采集与合成开始合流。

### 主题结构

| 主方向 | 本月候选 | 占比 | 同比候选 | 同比增量 |
|---|---:|---:|---:|---:|
| [具身基础模型](/directions/foundation-models) | 59 | 47.6% | 13 | +46 |
| [大小脑与双系统](/directions/dual-system) | 3 | 2.4% | 0 | +3 |
| [灵巧操作](/directions/dexterous-manipulation) | 12 | 9.7% | 7 | +5 |
| [世界模型](/directions/world-models) | 16 | 12.9% | 4 | +12 |
| [通用机器人学习](/directions/general-robot-learning) | 34 | 27.4% | 16 | +18 |

> 自动宽召回对 VLA 命名敏感，不能单独解释为能力增长；大小脑类因常使用隐式架构命名，自动数量是保守下界。

### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> 世界模型与搜索/规划形成方法簇

**变化。** Motus、Large Video Planner、STORM 与 WorldPlanner 从统一 latent action、视频规划器和 search-guided generation 三路汇合。

**对比。** 这是全年首次在同月出现三项以上、不同作者团队的 planning-oriented world model。

**证据。** [Motus: A Unified Latent Action World Model](https://arxiv.org/abs/2512.13030)；[Large Video Planner Enables Generalizable Robot Control](https://arxiv.org/abs/2512.15840)；[STORM: Search-Guided Generative World Models for Robotic Manipulation](https://arxiv.org/abs/2512.18477)；[WorldPlanner: Monte Carlo Tree Search and MPC with Action-Conditioned Visual World Models](https://arxiv.org/abs/2511.03077)

**成熟度与瓶颈。** 研究密度高，同行评审滞后明显。 主要瓶颈是可执行性校验与长时 roll-out 漂移。。

**战略含义。** 2026 年应观察这批工作能否转化为真实机器人闭环收益。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 双系统跨出 manipulation，开始覆盖导航与视频策略

**变化。** Video2Act、Ground Slow Move Fast 与 DualVLA 显示快慢分工可跨视频策略、导航和通用代理。

**对比。** 10 月主要是 VLA 内部推理；本月开始形成跨任务架构语言。

**证据。** [Video2Act: A Dual-System Video Diffusion Policy with Robotic Spatio-Motional Modeling](https://arxiv.org/abs/2512.03044)；[Ground Slow, Move Fast: A Dual-System Foundation Model for Generalizable Vision-and-Language Navigation](https://arxiv.org/abs/2512.08186)；[DualVLA: Building a Generalizable Embodied Agent via Partial Decoupling of Reasoning and Action](https://arxiv.org/abs/2511.22134)

**成熟度与瓶颈。** 跨任务概念扩散，统一实验标准缺失。 主要瓶颈是不同任务的时钟频率和状态抽象不统一。。

**战略含义。** 双系统价值在于复用调度框架，而非统一一个超大模型。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 低成本示范采集与合成开始合流

**变化。** RoboWheel、One-Shot Demonstration Synthesis 和 InternData-A1 覆盖真实人类示范、单样本合成与高保真合成预训练。

**对比。** 数据规模化从单一 teleoperation 扩展为真实—合成混合流水线。

**证据。** [RoboWheel: A Data Engine from Real-World Human Demonstrations for Cross-Embodiment Robotic Learning](https://arxiv.org/abs/2512.02729)；[One-Shot Real-World Demonstration Synthesis for Scalable Bimanual Manipulation](https://arxiv.org/abs/2512.09297)；[InternData-A1: Pioneering High-Fidelity Synthetic Data for Pre-training Generalist Policy](https://arxiv.org/abs/2511.16651)

**成熟度与瓶颈。** 数据引擎成形，但跨团队采用尚未验证。 主要瓶颈是数据质量过滤与许可合规。。

**战略含义。** 评估数据公司时，应要求展示对下游多机器人成功率的边际贡献。

</div>

### 蛛丝马迹：小样本领先信号

| 弱信号 | 等级 | 下一道技术门槛 | 当前判断 |
|---|---|---|---|
| 双系统跨出 manipulation，开始覆盖导航与视频策略 | B | 不同任务的时钟频率和状态抽象不统一。 | 跨任务概念扩散，统一实验标准缺失。 |
| 低成本示范采集与合成开始合流 | B | 数据质量过滤与许可合规。 | 数据引擎成形，但跨团队采用尚未验证。 |

识别逻辑不是“论文少就更前沿”，而是寻找多个弱证据是否指向同一个尚未被主流命名的瓶颈迁移。完整方法见[弱信号探测与未来判断](/analysis/weak-signals)。

### 本月精读论文

| 论文 | v1 日期 | 主方向 | 一句话贡献 | 证据标签 |
|---|---|---|---|---|
| [Motus: A Unified Latent Action World Model](https://arxiv.org/abs/2512.13030) | 2025-12-15 | 世界模型 | Motus 用 MoT 统一理解、视频生成和动作专家，并以 optical-flow latent action 支持世界模型、VLA、逆动力学等多种模式。 | 真机 |
| [Large Video Planner Enables Generalizable Robot Control](https://arxiv.org/abs/2512.15840) | 2025-12-17 | 世界模型 | 以互联网规模人类活动视频预训练开放视频规划器，零样本生成新场景任务的视频计划并后处理为可执行真实机器人动作。 | 真机 · 多任务 · 开放资产 |
| [Ground Slow, Move Fast: A Dual-System Foundation Model for Generalizable Vision-and-Language Navigation](https://arxiv.org/abs/2512.08186) | 2025-12-09 | 大小脑与双系统 | DualVLN 让 VLM 全局规划器慢速生成中程像素目标，轻量 diffusion transformer 快速输出连续轨迹，在真实动态环境实现长时序导航。 | 真机 · 长时序 |
| [One-Shot Real-World Demonstration Synthesis for Scalable Bimanual Manipulation](https://arxiv.org/abs/2512.09297) | 2025-12-10 | 灵巧操作 | BiDemoSyn 从一条真实示范分解协调不变量与对象相关调整，数小时合成数千条双臂接触轨迹，并展示新平台零样本迁移。 | 真机 · 跨本体 |
| [RoboWheel: A Data Engine from Real-World Human Demonstrations for Cross-Embodiment Robotic Learning](https://arxiv.org/abs/2512.02729) | 2025-12-02 | 通用机器人学习 | RoboWheel 将单目/RGB-D 人类手物视频重建为物理可行接触轨迹，再重定向到夹爪、灵巧手和人形本体并做仿真扩增。 | 跨本体 |
| [Video2Act: A Dual-System Video Diffusion Policy with Robotic Spatio-Motional Modeling](https://arxiv.org/abs/2512.03044) | 2025-12-02 | 大小脑与双系统 | Video2Act 以视频扩散模型作低频慢系统、DiT 动作头作快速系统，通过空间边界与跨帧运动条件提升真实任务成功率。 | 真机 |
| [STORM: Search-Guided Generative World Models for Robotic Manipulation](https://arxiv.org/abs/2512.18477) | 2025-12-20 | 世界模型 | STORM 让 diffusion VLA 提议动作、视频世界模型预测结果、MCTS 搜索与重规划，在 SimplerEnv 达到 51.0% 平均成功率。 | 长时序 |

精读样本明确开放披露 1/7；只在摘要、comment 或已核验项目页明确披露时记为“是”。

### 同行评审锚点

| 工作 | 官方证据 | 为什么可作为本月锚点 |
|---|---|---|
| [Motus: A Unified Latent Action World Model](https://arxiv.org/abs/2512.13030) | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html) | The CVF official open-access page lists the paper in the Proceedings of CVPR 2026, with authors, June 2026, and page numbers. |
| [SIMPACT: Simulation-Enabled Action Planning using Vision-Language Models](https://arxiv.org/abs/2512.05955) | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_SIMPACT_Simulation-Enabled_Action_Planning_using_Vision-Language_Models_CVPR_2026_paper.html) | The CVF official open-access page lists the paper in the Proceedings of CVPR 2026, with authors, June 2026, and page numbers. |

### 反证与信号质量检查

- 多篇论文共享相同数据、模型或作者团队时，不按独立证据重复加权。
- 单一 benchmark 提升若没有真实机器人迁移，不足以升级为 A 级趋势。
- “open-source / will release” 与实际可下载、可复现实验分开记录。
- 世界模型必须展示动作、规划、控制或数据生成价值；纯视频质量不计。

<!-- 更新标记：2025-12 月度雷达 最后更新 2026.07 -->

---


## 2026 年 1 月研究雷达

> **统计口径。** 自动宽召回候选用于数量结构；7 篇精读样本用于实验与开放性指标。同比月为 2025-01。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>85</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>3/7</strong><span>摘要确认真机</span></div>
  <div class="radar-kpi"><strong>4</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

latent action world model 从实验室走向 in-the-wild；与此同时，人类中心数据被推到跨本体预训练主线。

### 主题结构

| 主方向 | 本月候选 | 占比 | 同比候选 | 同比增量 |
|---|---:|---:|---:|---:|
| [具身基础模型](/directions/foundation-models) | 36 | 42.4% | 9 | +27 |
| [大小脑与双系统](/directions/dual-system) | 3 | 3.5% | 0 | +3 |
| [灵巧操作](/directions/dexterous-manipulation) | 7 | 8.2% | 8 | -1 |
| [世界模型](/directions/world-models) | 13 | 15.3% | 3 | +10 |
| [通用机器人学习](/directions/general-robot-learning) | 26 | 30.6% | 10 | +16 |

> 自动宽召回对 VLA 命名敏感，不能单独解释为能力增长；大小脑类因常使用隐式架构命名，自动数量是保守下界。

### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> latent action world model 从实验室走向 in-the-wild

**变化。** Learning Latent Action World Models In The Wild、Cosmos Policy 与 Motus 分别覆盖野外视频、视频模型微调和统一 latent action。

**对比。** 12 月强调搜索，本月强调如何从开放视频获得可执行潜变量。

**证据。** [Learning Latent Action World Models In The Wild](https://arxiv.org/abs/2601.05230)；[Cosmos Policy: Fine-Tuning Video Models for Visuomotor Control and Planning](https://arxiv.org/abs/2601.16163)；[Motus: A Unified Latent Action World Model](https://arxiv.org/abs/2512.13030)

**成熟度与瓶颈。** 跨月多团队，真实环境可控性仍弱。 主要瓶颈是动作语义不可辨识和时序对齐。。

**战略含义。** 把 inverse dynamics 与可执行性奖励视为核心能力，而非附属模块。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> Action CoT 与非对称专家正在重写大小脑接口

**变化。** ACoT-VLA、TwinBrainVLA 与 DualVLA 从动作链推理、非对称混合专家和部分解耦三种方式定义高低层接口。

**对比。** 相比显式 planner 调 policy，这些工作更倾向于可联合训练的内部接口。

**证据。** [ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://arxiv.org/abs/2601.11404)；[TwinBrainVLA: Unleashing the Potential of Generalist VLMs for Embodied Tasks via Asymmetric Mixture-of-Transformers](https://arxiv.org/abs/2601.14133)；[DualVLA: Building a Generalizable Embodied Agent via Partial Decoupling of Reasoning and Action](https://arxiv.org/abs/2511.22134)

**成熟度与瓶颈。** 架构簇形成，实时性尚未标准化。 主要瓶颈是慢分支是否真的提升成功率而非只增加计算。。

**战略含义。** 需要按任务难度自适应启用慢推理。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> 人类中心数据被推到跨本体预训练主线

**变化。** Being-H0.5、RoboWheel 和 InternData-A1 都把人类数据转化为 generalist policy 的可扩展监督。

**对比。** 2025 年的零散数据编辑开始收敛为预训练数据栈。

**证据。** [Being-H0.5: Scaling Human-Centric Robot Learning for Cross-Embodiment Generalization](https://arxiv.org/abs/2601.12993)；[RoboWheel: A Data Engine from Real-World Human Demonstrations for Cross-Embodiment Robotic Learning](https://arxiv.org/abs/2512.02729)；[InternData-A1: Pioneering High-Fidelity Synthetic Data for Pre-training Generalist Policy](https://arxiv.org/abs/2511.16651)

**成熟度与瓶颈。** 模型规模化信号明确，独立机器人平台验证仍有限。 主要瓶颈是人类动作与机器人动力学不一致。。

**战略含义。** 关注能将人类视频、少量真机和在线修正闭环结合的团队。

</div>

### 蛛丝马迹：小样本领先信号

| 弱信号 | 等级 | 下一道技术门槛 | 当前判断 |
|---|---|---|---|
| Action CoT 与非对称专家正在重写大小脑接口 | B | 慢分支是否真的提升成功率而非只增加计算。 | 架构簇形成，实时性尚未标准化。 |

识别逻辑不是“论文少就更前沿”，而是寻找多个弱证据是否指向同一个尚未被主流命名的瓶颈迁移。完整方法见[弱信号探测与未来判断](/analysis/weak-signals)。

### 本月精读论文

| 论文 | v1 日期 | 主方向 | 一句话贡献 | 证据标签 |
|---|---|---|---|---|
| [ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://arxiv.org/abs/2601.11404) | 2026-01-16 | 大小脑与双系统 | 把 Chain-of-Thought 直接落在动作空间，以显式粗轨迹和隐式动作先验共同条件化下游动作头，缩短语义推理到连续控制的距离。 | 真机 · 开放资产 |
| [UniBiDex: A Unified Teleoperation Framework for Robotic Bimanual Dexterous Manipulation](https://arxiv.org/abs/2601.04629) | 2026-01-08 | 灵巧操作 | 统一 VR 与主从式输入，在共享控制栈中加入零空间避碰和奇异规避，为双臂灵巧操作提供可开源的数据采集底座。 | 多任务 · 长时序 · 开放资产 |
| [Cosmos Policy: Fine-Tuning Video Models for Visuomotor Control and Planning](https://arxiv.org/abs/2601.16163) | 2026-01-22 | 世界模型 | 用单阶段后训练把预训练视频模型直接改造成动作、未来状态和价值联合生成器，并以测试时规划提升双臂真实任务表现。 | 真机 · 开放资产 |
| [Green-VLA: Staged Vision-Language-Action Model for Generalist Robots](https://arxiv.org/abs/2602.00919) | 2026-01-31 | 具身基础模型 | 以五阶段课程、3,000 小时示范和统一的本体感知动作接口，把 VLM grounding、多本体预训练、单本体适配与 RL 对齐串成可部署的 generalist VLA。 | 真机 · 跨本体 · 长时序 |
| [Being-H0.5: Scaling Human-Centric Robot Learning for Cross-Embodiment Generalization](https://arxiv.org/abs/2601.12993) | 2026-01-19 | 具身基础模型 | 以 35,000 小时、30 种本体的 UniHand-2.0 和统一动作空间训练人类中心 VLA，并用 Mixture-of-Flow 分离共享运动原语与本体专家。 | 多任务 · 跨本体 |
| [Learning Latent Action World Models In The Wild](https://arxiv.org/abs/2601.05230) | 2026-01-08 | 世界模型 | 从无动作标注的 in-the-wild 视频学习受约束连续 latent actions，并用控制器映射已知动作以支持世界模型规划。 | 摘要未确认 |
| [TwinBrainVLA: Unleashing the Potential of Generalist VLMs for Embodied Tasks via Asymmetric Mixture-of-Transformers](https://arxiv.org/abs/2601.14133) | 2026-01-20 | 大小脑与双系统 | 以冻结 generalist VLM 与可训练 specialist VLM 构成双路径，通过 AsyMoT 查询未被破坏的语义能力并驱动 flow-matching 动作专家。 | 摘要未确认 |

精读样本明确开放披露 3/7；只在摘要、comment 或已核验项目页明确披露时记为“是”。

### 同行评审锚点

| 工作 | 官方证据 | 为什么可作为本月锚点 |
|---|---|---|
| [ActiveVLA: Injecting Active Perception into Vision-Language-Action Models for Precise 3D Robotic Manipulation](https://arxiv.org/abs/2601.08325) | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_ActiveVLA_Injecting_Active_Perception_into_Vision-Language-Action_Models_for_Precise_3D_CVPR_2026_paper.html) | The CVF official open-access page lists the paper in the Proceedings of CVPR 2026, with authors, June 2026, and page numbers. |
| [ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://arxiv.org/abs/2601.11404) | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhong_ACoT-VLA_Action_Chain-of-Thought_for_Vision-Language-Action_Models_CVPR_2026_paper.html) | The CVF official open-access page lists the paper in the Proceedings of CVPR 2026, with authors, June 2026, and page numbers. |
| [Action-Sketcher: From Reasoning to Action via Visual Sketches for Robotic Manipulation](https://arxiv.org/abs/2601.01618) | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Tan_Action-Sketcher_From_Reasoning_to_Action_via_Visual_Sketches_for_Robotic_CVPR_2026_paper.html) | The CVF official open-access page lists the standardized proceedings title in CVPR 2026; the merged arXiv version uses the slightly longer phrase 'Long-Horizon Robotic Manipulation'. |
| [PointWorld: Scaling 3D World Models for In-The-Wild Robotic Manipulation](https://arxiv.org/abs/2601.03782) | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Huang_PointWorld_Scaling_3D_World_Models_for_In-The-Wild_Robotic_Manipulation_CVPR_2026_paper.html) | The CVF official open-access page lists the paper in the Proceedings of CVPR 2026, with authors, June 2026, and page numbers. |

### 反证与信号质量检查

- 多篇论文共享相同数据、模型或作者团队时，不按独立证据重复加权。
- 单一 benchmark 提升若没有真实机器人迁移，不足以升级为 A 级趋势。
- “open-source / will release” 与实际可下载、可复现实验分开记录。
- 世界模型必须展示动作、规划、控制或数据生成价值；纯视频质量不计。

<!-- 更新标记：2026-01 月度雷达 最后更新 2026.07 -->

---


## 2026 年 2 月研究雷达

> **统计口径。** 自动宽召回候选用于数量结构；7 篇精读样本用于实验与开放性指标。同比月为 2025-02。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>174</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>5/7</strong><span>摘要确认真机</span></div>
  <div class="radar-kpi"><strong>0</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

世界模型开始承担 RL 模拟器与在线自纠错；与此同时，egocentric 数据开始真正服务灵巧规模化。

### 主题结构

| 主方向 | 本月候选 | 占比 | 同比候选 | 同比增量 |
|---|---:|---:|---:|---:|
| [具身基础模型](/directions/foundation-models) | 84 | 48.3% | 14 | +70 |
| [大小脑与双系统](/directions/dual-system) | 1 | 0.6% | 0 | +1 |
| [灵巧操作](/directions/dexterous-manipulation) | 22 | 12.6% | 7 | +15 |
| [世界模型](/directions/world-models) | 23 | 13.2% | 4 | +19 |
| [通用机器人学习](/directions/general-robot-learning) | 44 | 25.3% | 19 | +25 |

> 自动宽召回对 VLA 命名敏感，不能单独解释为能力增长；大小脑类因常使用隐式架构命名，自动数量是保守下界。

### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> 世界模型开始承担 RL 模拟器与在线自纠错

**变化。** WoVR、Self-Correcting VLA 与 World-Gymnast 分别用于后训练模拟、稀疏想象修正和世界模型内 RL。

**对比。** 相比 2025 年底的离线规划，这是一轮更靠近策略优化的迁移。

**证据。** [WoVR: World Models as Reliable Simulators for Post-Training VLA Policies with RL](https://arxiv.org/abs/2602.13977)；[Self-Correcting VLA: Online Action Refinement via Sparse World Imagination](https://arxiv.org/abs/2602.21633)；[World-Gymnast: Training Robots with Reinforcement Learning in a World Model](https://arxiv.org/abs/2602.02454)

**成熟度与瓶颈。** 多团队新兴趋势，真实机器人长期稳定性未确认。 主要瓶颈是模型偏差会被 RL 放大。。

**战略含义。** 验证时需报告 simulator exploitation 和真机回归测试。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 快慢系统开始感知力、接触与完成状态

**变化。** FAVLA 将力适应写入 fast–slow 架构，StreamVLA 用 completion-state gating 打破固定 reason–act 循环，自纠错框架补上终止判断。

**对比。** 双系统从“多想一步”转向“何时想、何时停、何时改动作”。

**证据。** [FAVLA: A Force-Adaptive Fast-Slow VLA model for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2602.23648)；[StreamVLA: Breaking the Reason-Act Cycle via Completion-State Gating](https://arxiv.org/abs/2602.01100)；[From Knowing to Doing Precisely: A General Self-Correction and Termination Framework for VLA models](https://arxiv.org/abs/2602.01811)

**成熟度与瓶颈。** 接口创新明显，跨平台复现不足。 主要瓶颈是事件触发器的误报与控制抖动。。

**战略含义。** 调度器、状态估计和 verifier 将成为独立技术层。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> egocentric 数据开始真正服务灵巧规模化

**变化。** EgoScale、Joint-Aligned Latent Action 与 Being-H0.5 把第一视角人类数据接入灵巧和跨本体预训练。

**对比。** 9 月 OpenEgo 还是数据集信号，本月已有训练管线和泛化目标。

**证据。** [EgoScale: Scaling Dexterous Manipulation with Diverse Egocentric Human Data](https://arxiv.org/abs/2602.16710)；[Joint-Aligned Latent Action: Towards Scalable VLA Pretraining in the Wild](https://arxiv.org/abs/2602.21736)；[Being-H0.5: Scaling Human-Centric Robot Learning for Cross-Embodiment Generalization](https://arxiv.org/abs/2601.12993)

**成熟度与瓶颈。** 数据规模化起步。 主要瓶颈是手—物接触状态和第三维动作不可观测。。

**战略含义。** 具备可穿戴采集与物理对齐工具链的团队可能形成数据壁垒。

</div>

### 蛛丝马迹：小样本领先信号

| 弱信号 | 等级 | 下一道技术门槛 | 当前判断 |
|---|---|---|---|
| 快慢系统开始感知力、接触与完成状态 | B | 事件触发器的误报与控制抖动。 | 接口创新明显，跨平台复现不足。 |
| egocentric 数据开始真正服务灵巧规模化 | B | 手—物接触状态和第三维动作不可观测。 | 数据规模化起步。 |

识别逻辑不是“论文少就更前沿”，而是寻找多个弱证据是否指向同一个尚未被主流命名的瓶颈迁移。完整方法见[弱信号探测与未来判断](/analysis/weak-signals)。

### 本月精读论文

| 论文 | v1 日期 | 主方向 | 一句话贡献 | 证据标签 |
|---|---|---|---|---|
| [Xiaomi-Robotics-0: An Open-Sourced Vision-Language-Action Model with Real-Time Execution](https://arxiv.org/abs/2602.12684) | 2026-02-13 | 具身基础模型 | 以跨本体预训练、异步执行训练和动作块时间对齐，让开放 VLA 在消费级 GPU 上实现平滑实时双臂控制。 | 真机 · 跨本体 · 开放资产 |
| [Self-Correcting VLA: Online Action Refinement via Sparse World Imagination](https://arxiv.org/abs/2602.21633) | 2026-02-25 | 世界模型 | 以任务进度和未来轨迹趋势构成稀疏世界想象，再把预测状态转成密集奖励在线修正动作。 | 真机 · 开放资产 |
| [WoVR: World Models as Reliable Simulators for Post-Training VLA Policies with RL](https://arxiv.org/abs/2602.13977) | 2026-02-15 | 世界模型 | 通过可控动作条件视频模型、关键帧初始化 rollout 和模型—策略共同演化，降低想象滚动的幻觉深度并用于 VLA 的 RL 后训练。 | 真机 · 跨本体 · 长时序 |
| [EgoScale: Scaling Dexterous Manipulation with Diverse Egocentric Human Data](https://arxiv.org/abs/2602.16710) | 2026-02-18 | 通用机器人学习 | 在 20,854 小时动作标注第一视角人类视频上建立 scaling law，并以轻量 human-robot mid-training 迁移到 22-DoF 灵巧手。 | 真机 · 跨本体 · 长时序 |
| [Joint-Aligned Latent Action: Towards Scalable VLA Pretraining in the Wild](https://arxiv.org/abs/2602.21736) | 2026-02-25 | 通用机器人学习 | 以逆动力学和真实动作联合对齐 latent action，在 7.5M 段、2,000 多小时人类视频上预训练可迁移的行为表征。 | 真机 |
| [StemVLA:An Open-Source Vision-Language-Action Model with Future 3D Spatial Geometry Knowledge and 4D Historical Representation](https://arxiv.org/abs/2602.23721) | 2026-02-27 | 世界模型 | 把未来 3D 几何预测与历史 4D 时空表征同时注入动作生成，使 VLA 显式建模场景动态与空间结构。 | 长时序 |
| [FAVLA: A Force-Adaptive Fast-Slow VLA model for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2602.23648) | 2026-02-27 | 大小脑与双系统 | 将低频 VLM 感知规划与高频力反馈动作专家解耦，并根据预测的力变化动态调度控制频率。 | 摘要未确认 |

精读样本明确开放披露 2/7；只在摘要、comment 或已核验项目页明确披露时记为“是”。

### 同行评审锚点

| 工作 | 官方证据 | 为什么可作为本月锚点 |
|---|---|---|
| — | — | 本月首次公开的精读样本尚无可安全归属到该月的官方录用证据；这不等于论文质量较低。 |

### 反证与信号质量检查

- 多篇论文共享相同数据、模型或作者团队时，不按独立证据重复加权。
- 单一 benchmark 提升若没有真实机器人迁移，不足以升级为 A 级趋势。
- “open-source / will release” 与实际可下载、可复现实验分开记录。
- 世界模型必须展示动作、规划、控制或数据生成价值；纯视频质量不计。

<!-- 更新标记：2026-02 月度雷达 最后更新 2026.07 -->

---


## 2026 年 3 月研究雷达

> **统计口径。** 自动宽召回候选用于数量结构；7 篇精读样本用于实验与开放性指标。同比月为 2025-03。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>234</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>5/7</strong><span>摘要确认真机</span></div>
  <div class="radar-kpi"><strong>3</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

world model 的新门槛是“动作可执行”；与此同时，论文量激增，但不能把提交周期当成技术爆发。

### 主题结构

| 主方向 | 本月候选 | 占比 | 同比候选 | 同比增量 |
|---|---:|---:|---:|---:|
| [具身基础模型](/directions/foundation-models) | 104 | 44.4% | 19 | +85 |
| [大小脑与双系统](/directions/dual-system) | 4 | 1.7% | 2 | +2 |
| [灵巧操作](/directions/dexterous-manipulation) | 40 | 17.1% | 18 | +22 |
| [世界模型](/directions/world-models) | 23 | 9.8% | 6 | +17 |
| [通用机器人学习](/directions/general-robot-learning) | 63 | 26.9% | 34 | +29 |

> 自动宽召回对 VLA 命名敏感，不能单独解释为能力增长；大小脑类因常使用隐式架构命名，自动数量是保守下界。

### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> world model 的新门槛是“动作可执行”

**变化。** EVA 用 inverse-dynamics rewards 对齐可执行动作，DreamPlan 用视频世界模型训练 planner，DIAL 用 latent world model 解耦 intent/action。

**对比。** 视频质量不再是主论据，策略可执行性成为共同评价轴。

**证据。** [EVA: Aligning Video World Models with Executable Robot Actions via Inverse Dynamics Rewards](https://arxiv.org/abs/2603.17808)；[DreamPlan: Efficient Reinforcement Fine-Tuning of Vision-Language Planners via Video World Models](https://arxiv.org/abs/2603.16860)；[DIAL: Decoupling Intent and Action via Latent World Modeling for End-to-End VLA](https://arxiv.org/abs/2603.29844)

**成熟度与瓶颈。** 三团队同时出现，评审与长期真机数据仍滞后。 主要瓶颈是逆动力学奖励的偏差和闭环漂移。。

**战略含义。** 这是比论文数量更重要的评价范式迁移。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 灵巧操作从单步抓取转向可观测的长时接触

**变化。** DexDrummer、UniDex 与 OmniVTA 分别覆盖长时演奏、通用手控制和视触觉世界模型。

**对比。** 相比早期 reward shaping，任务与感知都更接近连续接触闭环。

**证据。** [DexDrummer: In-Hand, Contact-Rich, and Long-Horizon Dexterous Robot Drumming](https://arxiv.org/abs/2603.22263)；[UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://arxiv.org/abs/2603.22264)；[OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2603.19201)

**成熟度与瓶颈。** 真实机器人证据增强，硬件可复制性仍有限。 主要瓶颈是高频触觉、动作空间维度和设备差异。。

**战略含义。** 优先跟踪“传感器—数据—策略”一体化团队。

</div>

<div class="trend-card">

#### <span class="signal signal-d">D · 反证/降温</span> 论文量激增，但不能把提交周期当成技术爆发

**变化。** 自动宽召回候选显著上升，基础模型命名占比最高；同期官方同行评审覆盖仍低。

**对比。** 增长既包含真实扩散，也受到会议周期与 VLA 命名泛化影响。

**证据。** [ManipArena: Comprehensive Real-world Evaluation of Reasoning-Oriented Generalist Robot Manipulation](https://arxiv.org/abs/2603.28545)；[DIAL: Decoupling Intent and Action via Latent World Modeling for End-to-End VLA](https://arxiv.org/abs/2603.29844)

**成熟度与瓶颈。** 数量强、质量分化。 主要瓶颈是统一真机评测和独立复现。。

**战略含义。** 本月趋势判断应降低数量权重，提高真实机器人和开放资产权重。

</div>

### 蛛丝马迹：小样本领先信号

| 弱信号 | 等级 | 下一道技术门槛 | 当前判断 |
|---|---|---|---|
| 灵巧操作从单步抓取转向可观测的长时接触 | B | 高频触觉、动作空间维度和设备差异。 | 真实机器人证据增强，硬件可复制性仍有限。 |

识别逻辑不是“论文少就更前沿”，而是寻找多个弱证据是否指向同一个尚未被主流命名的瓶颈迁移。完整方法见[弱信号探测与未来判断](/analysis/weak-signals)。

### 本月精读论文

| 论文 | v1 日期 | 主方向 | 一句话贡献 | 证据标签 |
|---|---|---|---|---|
| [UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://arxiv.org/abs/2603.22264) | 2026-03-23 | 灵巧操作 | 将 50K 轨迹、八种灵巧手、FAAS 统一动作空间、3D VLA 与便携采集装置组成 universal dexterous foundation suite。 | 摘要未确认 |
| [DexDrummer: In-Hand, Contact-Rich, and Long-Horizon Dexterous Robot Drumming](https://arxiv.org/abs/2603.22263) | 2026-03-23 | 灵巧操作 | 以架子鼓把手内控制、反复接触和长时序双手协调合并为统一测试床，并用规划加 residual RL 实现 sim-to-real。 | 真机 · 多任务 · 长时序 |
| [ManipArena: Comprehensive Real-world Evaluation of Reasoning-Oriented Generalist Robot Manipulation](https://arxiv.org/abs/2603.28545) | 2026-03-30 | 通用机器人学习 | 用 20 个实体任务、10,812 条专家轨迹和成对 real-to-sim 场景，为 VLA/WAM 提供可诊断的统一真实机器人评测。 | 真机 · 多任务 |
| [EVA: Aligning Video World Models with Executable Robot Actions via Inverse Dynamics Rewards](https://arxiv.org/abs/2603.17808) | 2026-03-18 | 世界模型 | 把 inverse dynamics model 反用作奖励模型，以速度、加速度、jerk 和本体约束对视频世界模型做可执行性对齐。 | 真机 |
| [OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2603.19201) | 2026-03-19 | 世界模型 | 以 21K+ 轨迹、86 任务的视觉—触觉—动作数据训练双流世界模型，并用 60Hz 触觉反射闭环纠偏。 | 真机 |
| [DIAL: Decoupling Intent and Action via Latent World Modeling for End-to-End VLA](https://arxiv.org/abs/2603.29844) | 2026-03-31 | 大小脑与双系统 | 用可微 latent intent bottleneck 连接 System-2 的未来表征与 System-1 的逆动力学控制，并以两阶段训练稳定端到端优化。 | 真机 |
| [DreamPlan: Efficient Reinforcement Fine-Tuning of Vision-Language Planners via Video World Models](https://arxiv.org/abs/2603.16860) | 2026-03-17 | 大小脑与双系统 | 先用零样本 VLM 收集次优交互训练动作条件视频世界模型，再在想象 rollout 中强化微调高层 planner。 | 摘要未确认 |

精读样本明确开放披露 0/7；只在摘要、comment 或已核验项目页明确披露时记为“是”。

### 同行评审锚点

| 工作 | 官方证据 | 为什么可作为本月锚点 |
|---|---|---|
| [AtomicVLA: Unlocking the Potential of Atomic Skill Learning in Robots](https://arxiv.org/abs/2603.07648) | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_AtomicVLA_Unlocking_the_Potential_of_Atomic_Skill_Learning_in_Robots_CVPR_2026_paper.html) | The CVF official open-access page lists the paper in the Proceedings of CVPR 2026, with authors, June 2026, and page numbers. |
| [UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://arxiv.org/abs/2603.22264) | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html) | The CVF official open-access page lists the paper in the Proceedings of CVPR 2026, with authors, June 2026, and page numbers. |
| [Cross-Hand Latent Representation for Vision-Language-Action Models](https://arxiv.org/abs/2603.10158) | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Jiang_Cross-Hand_Latent_Representation_for_Vision-Language-Action_Models_CVPR_2026_paper.html) | The CVF official open-access page lists the paper in the Proceedings of CVPR 2026, with authors, June 2026, and page numbers. |

### 反证与信号质量检查

- 多篇论文共享相同数据、模型或作者团队时，不按独立证据重复加权。
- 单一 benchmark 提升若没有真实机器人迁移，不足以升级为 A 级趋势。
- “open-source / will release” 与实际可下载、可复现实验分开记录。
- 世界模型必须展示动作、规划、控制或数据生成价值；纯视频质量不计。

<!-- 更新标记：2026-03 月度雷达 最后更新 2026.07 -->

---


## 2026 年 4 月研究雷达

> **统计口径。** 自动宽召回候选用于数量结构；7 篇精读样本用于实验与开放性指标。同比月为 2025-04。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>134</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>4/7</strong><span>摘要确认真机</span></div>
  <div class="radar-kpi"><strong>0</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

触觉与 world model 开始合流；与此同时，foundation model 开始接受垂直本体与可控行为约束。

### 主题结构

| 主方向 | 本月候选 | 占比 | 同比候选 | 同比增量 |
|---|---:|---:|---:|---:|
| [具身基础模型](/directions/foundation-models) | 57 | 42.5% | 4 | +53 |
| [大小脑与双系统](/directions/dual-system) | 2 | 1.5% | 0 | +2 |
| [灵巧操作](/directions/dexterous-manipulation) | 19 | 14.2% | 15 | +4 |
| [世界模型](/directions/world-models) | 20 | 14.9% | 5 | +15 |
| [通用机器人学习](/directions/general-robot-learning) | 36 | 26.9% | 18 | +18 |

> 自动宽召回对 VLA 命名敏感，不能单独解释为能力增长；大小脑类因常使用隐式架构命名，自动数量是保守下界。

### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 触觉与 world model 开始合流

**变化。** Touch Dreaming、FingerEye 与 OmniVTA 把触觉用于未来预测、连续感知和接触世界建模。

**对比。** 8 月只是多模态 VLA 接口；本月触觉开始改变训练目标和状态预测。

**证据。** [Learning Versatile Humanoid Manipulation with Touch Dreaming](https://arxiv.org/abs/2604.13015)；[FingerEye: Learning Dexterous Manipulation with Continuous Vision-Tactile Sensing](https://arxiv.org/abs/2604.20689)；[OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2603.19201)

**成熟度与瓶颈。** 跨团队、跨月信号明确。 主要瓶颈是低成本传感器一致性与大规模同步数据。。

**战略含义。** 触觉世界模型可能先在装配、工具使用和柔性物体中兑现。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> 双系统进入异步 coarse-to-fine 调度

**变化。** Libra-VLA、Trace-Conditioned Planning 与 DIAL 不再固定每步完整推理，而是在轨迹、意图和动作层分配不同计算。

**对比。** 比 2025 年的显式 fast–slow 更接近实时系统设计。

**证据。** [Libra-VLA: Achieving Learning Equilibrium via Asynchronous Coarse-to-Fine Dual-System](https://arxiv.org/abs/2604.24921)；[Long-Horizon Manipulation via Trace-Conditioned VLA Planning](https://arxiv.org/abs/2604.21924)；[DIAL: Decoupling Intent and Action via Latent World Modeling for End-to-End VLA](https://arxiv.org/abs/2603.29844)

**成熟度与瓶颈。** 架构成熟度上升，工程 benchmark 缺失。 主要瓶颈是异步状态陈旧与延迟抖动。。

**战略含义。** 控制频率、端到端延迟和恢复时间应进入标准评测。

</div>

<div class="trend-card">

#### <span class="signal signal-c">C · 弱信号</span> foundation model 开始接受垂直本体与可控行为约束

**变化。** π0.7 强调 steerable generalist policy，Open-H-Embodiment 把医疗机器人纳入大规模基础模型数据。

**对比。** 通用性从“同一权重做更多任务”转向“可控制地适应高约束域”。

**证据。** [$π_{0.7}$: a Steerable Generalist Robotic Foundation Model with Emergent Capabilities](https://arxiv.org/abs/2604.15483)；[Open-H-Embodiment: A Large-Scale Dataset for Enabling Foundation Models in Medical Robotics](https://arxiv.org/abs/2604.21017)

**成熟度与瓶颈。** 两个高信号工作，独立验证不足。 主要瓶颈是高风险域的安全验证与数据治理。。

**战略含义。** 通用底座与垂直合规层可能形成分层市场。

</div>

### 蛛丝马迹：小样本领先信号

| 弱信号 | 等级 | 下一道技术门槛 | 当前判断 |
|---|---|---|---|
| 触觉与 world model 开始合流 | B | 低成本传感器一致性与大规模同步数据。 | 跨团队、跨月信号明确。 |
| foundation model 开始接受垂直本体与可控行为约束 | C | 高风险域的安全验证与数据治理。 | 两个高信号工作，独立验证不足。 |

识别逻辑不是“论文少就更前沿”，而是寻找多个弱证据是否指向同一个尚未被主流命名的瓶颈迁移。完整方法见[弱信号探测与未来判断](/analysis/weak-signals)。

### 本月精读论文

| 论文 | v1 日期 | 主方向 | 一句话贡献 | 证据标签 |
|---|---|---|---|---|
| [Open-H-Embodiment: A Large-Scale Dataset for Enabling Foundation Models in Medical Robotics](https://arxiv.org/abs/2604.21017) | 2026-04-22 | 具身基础模型 | 汇集 50 多家机构、多种手术本体的同步视频—运动学开放数据，并展示 medical VLA 与多本体 action-conditioned simulator。 | 跨本体 · 长时序 · 开放资产 |
| [$π_{0.7}$: a Steerable Generalist Robotic Foundation Model with Emergent Capabilities](https://arxiv.org/abs/2604.15483) | 2026-04-16 | 具身基础模型 | 通过把策略、表现元数据和子目标图像等多模态上下文纳入训练，使单一 foundation policy 可被精细 steer 并出现跨本体、组合任务和灵巧能力。 | 多任务 · 跨本体 · 长时序 |
| [Long-Horizon Manipulation via Trace-Conditioned VLA Planning](https://arxiv.org/abs/2604.21924) | 2026-04-23 | 大小脑与双系统 | 以任务管理 VLM 反复输出剩余子任务与 2D visual trace，驱动短时 VLA 执行器并在失败后自动保留未完成步骤。 | 真机 · 长时序 |
| [STARRY: Spatial-Temporal Action-Centric World Modeling for Robotic Manipulation](https://arxiv.org/abs/2604.26848) | 2026-04-29 | 世界模型 | 在统一 diffusion 过程中联合去噪未来时空 latent 与动作，并以深度和末端几何调制动作注意力。 | 真机 · 多任务 |
| [Learning Versatile Humanoid Manipulation with Touch Dreaming](https://arxiv.org/abs/2604.13015) | 2026-04-14 | 灵巧操作 | 把低身稳定控制、全身 VR 数据采集和 touch dreaming 结合，使 humanoid policy 同时预测动作块、未来关节力与触觉 latent。 | 真机 |
| [FingerEye: Learning Dexterous Manipulation with Continuous Vision-Tactile Sensing](https://arxiv.org/abs/2604.20689) | 2026-04-22 | 灵巧操作 | 用指尖双目视觉与柔顺接触环实现从接近到接触后的连续感知，并以组结构融合策略减轻模态捷径。 | 真机 |
| [Libra-VLA: Achieving Learning Equilibrium via Asynchronous Coarse-to-Fine Dual-System](https://arxiv.org/abs/2604.24921) | 2026-04-27 | 大小脑与双系统 | 将宏观离散方向规划和微观连续位姿对齐分给异步双系统，并提出动作分解粒度存在学习均衡点。 | 摘要未确认 |

精读样本明确开放披露 1/7；只在摘要、comment 或已核验项目页明确披露时记为“是”。

### 同行评审锚点

| 工作 | 官方证据 | 为什么可作为本月锚点 |
|---|---|---|
| — | — | 本月首次公开的精读样本尚无可安全归属到该月的官方录用证据；这不等于论文质量较低。 |

### 反证与信号质量检查

- 多篇论文共享相同数据、模型或作者团队时，不按独立证据重复加权。
- 单一 benchmark 提升若没有真实机器人迁移，不足以升级为 A 级趋势。
- “open-source / will release” 与实际可下载、可复现实验分开记录。
- 世界模型必须展示动作、规划、控制或数据生成价值；纯视频质量不计。

<!-- 更新标记：2026-04 月度雷达 最后更新 2026.07 -->

---


## 2026 年 5 月研究雷达

> **统计口径。** 自动宽召回候选用于数量结构；7 篇精读样本用于实验与开放性指标。同比月为 2025-05。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>203</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>6/7</strong><span>摘要确认真机</span></div>
  <div class="radar-kpi"><strong>0</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

视频模型正在被改造成 generalist policy，而非外置 world model；与此同时，generalist 底座开始向软体与灵巧专用能力下沉。

### 主题结构

| 主方向 | 本月候选 | 占比 | 同比候选 | 同比增量 |
|---|---:|---:|---:|---:|
| [具身基础模型](/directions/foundation-models) | 101 | 49.8% | 36 | +65 |
| [大小脑与双系统](/directions/dual-system) | 3 | 1.5% | 3 | 0 |
| [灵巧操作](/directions/dexterous-manipulation) | 23 | 11.3% | 16 | +7 |
| [世界模型](/directions/world-models) | 28 | 13.8% | 9 | +19 |
| [通用机器人学习](/directions/general-robot-learning) | 48 | 23.6% | 44 | +4 |

> 自动宽召回对 VLA 命名敏感，不能单独解释为能力增长；大小脑类因常使用隐式架构命名，自动数量是保守下界。

### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> 视频模型正在被改造成 generalist policy，而非外置 world model

**变化。** Turning Video Models into Generalist Robot Policies、τ0-WM 与 Cosmos Policy 把视频预测和动作生成压进同一训练栈。

**对比。** 2025 年视频模型多是数据或模拟器；现在开始直接承担控制表示。

**证据。** [Turning Video Models into Generalist Robot Policies](https://arxiv.org/abs/2605.27817)；[$τ_0$-WM: A Unified Video-Action World Model for Robotic Manipulation](https://arxiv.org/abs/2606.01027)；[Cosmos Policy: Fine-Tuning Video Models for Visuomotor Control and Planning](https://arxiv.org/abs/2601.16163)

**成熟度与瓶颈。** 跨团队方向明确，实时控制成本仍高。 主要瓶颈是像素生成冗余与动作时延。。

**战略含义。** 未来胜出的可能是压缩 latent video-action model，而非最大视频生成器。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 连续推理开始取代离散 reason–act 循环

**变化。** Continuous Reasoning、Libra-VLA 与 StreamVLA 都试图让思考与控制异步或连续发生。

**对比。** 大小脑竞争由模块命名转向时钟与状态同步。

**证据。** [Continuous Reasoning for Vision-Language-Action](https://arxiv.org/abs/2606.00229)；[Libra-VLA: Achieving Learning Equilibrium via Asynchronous Coarse-to-Fine Dual-System](https://arxiv.org/abs/2604.24921)；[StreamVLA: Breaking the Reason-Act Cycle via Completion-State Gating](https://arxiv.org/abs/2602.01100)

**成熟度与瓶颈。** 三团队连续出现。 主要瓶颈是推理状态陈旧、测试时计算不可控。。

**战略含义。** 系统软件和推理调度会成为 VLA 部署的关键护城河。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> generalist 底座开始向软体与灵巧专用能力下沉

**变化。** DeMaVLA、BORA 与 Qwen-VLA 分别覆盖可变形物体、真实灵巧在线适配和跨任务/本体统一。

**对比。** 相较只做 kitchen benchmark，任务物理性明显增强。

**证据。** [DeMaVLA: A Vision-Language-Action Foundation Model for Generalizable Deformable Manipulation](https://arxiv.org/abs/2605.31286)；[BORA: Bridging Offline Reinforcement Learning and Online Residual Adaptation for Real-World Dexterous VLA Models](https://arxiv.org/abs/2605.30226)；[Qwen-VLA: Unifying Vision-Language-Action Modeling across Tasks, Environments, and Robot Embodiments](https://arxiv.org/abs/2605.30280)

**成熟度与瓶颈。** 真实任务信号增强，开放与独立复现待确认。 主要瓶颈是专用数据稀缺与在线适配安全。。

**战略含义。** 通用模型价值将通过高难度垂直任务兑现，而不是只看平均 benchmark。

</div>

### 蛛丝马迹：小样本领先信号

| 弱信号 | 等级 | 下一道技术门槛 | 当前判断 |
|---|---|---|---|
| 连续推理开始取代离散 reason–act 循环 | B | 推理状态陈旧、测试时计算不可控。 | 三团队连续出现。 |
| generalist 底座开始向软体与灵巧专用能力下沉 | B | 专用数据稀缺与在线适配安全。 | 真实任务信号增强，开放与独立复现待确认。 |

识别逻辑不是“论文少就更前沿”，而是寻找多个弱证据是否指向同一个尚未被主流命名的瓶颈迁移。完整方法见[弱信号探测与未来判断](/analysis/weak-signals)。

### 本月精读论文

| 论文 | v1 日期 | 主方向 | 一句话贡献 | 证据标签 |
|---|---|---|---|---|
| [Qwen-VLA: Unifying Vision-Language-Action Modeling across Tasks, Environments, and Robot Embodiments](https://arxiv.org/abs/2605.30280) | 2026-05-28 | 具身基础模型 | 以 embodiment-aware prompt 和统一动作—轨迹预测，把操作、导航、轨迹预测及多源数据纳入单一 Qwen-VLA。 | 真机 · 多任务 · 跨本体 |
| [Turning Video Models into Generalist Robot Policies](https://arxiv.org/abs/2605.27817) | 2026-05-27 | 世界模型 | 保持 video planner 本体无关，仅为各机器人训练基于 Jacobian 的 IDM，形成可替换视频模型的闭环 VERA 路线。 | 真机 · 跨本体 |
| [DeMaVLA: A Vision-Language-Action Foundation Model for Generalizable Deformable Manipulation](https://arxiv.org/abs/2605.31286) | 2026-05-29 | 具身基础模型 | 以约 5,000 小时双臂真实示范预训练，再用失败纠正轨迹和 HiL DAgger 学习跨服装类别的通用折叠策略。 | 真机 · 多任务 |
| [OneVLA: A Unified Framework for Embodied Tasks](https://arxiv.org/abs/2606.01241) | 2026-05-31 | 具身基础模型 | 用统一 action head 和渐进式多阶段训练把导航与操作纳入同一 VLA，探索跨任务正迁移。 | 真机 · 长时序 |
| [BORA: Bridging Offline Reinforcement Learning and Online Residual Adaptation for Real-World Dexterous VLA Models](https://arxiv.org/abs/2605.30226) | 2026-05-28 | 灵巧操作 | 用离线动作条件 critic 稳定价值学习，再冻结 VLA 基座，以人类介入的 chunk-wise residual 做低风险在线适配。 | 真机 |
| [Continuous Reasoning for Vision-Language-Action](https://arxiv.org/abs/2606.00229) | 2026-05-29 | 大小脑与双系统 | 把可共享、可验证的 Gaussian continuous thoughts 作为 VLA 推理介质，并以教师消费学生 latent 的动作改善来约束推理。 | 真机 |
| [$τ_0$-WM: A Unified Video-Action World Model for Robotic Manipulation](https://arxiv.org/abs/2606.01027) | 2026-05-31 | 世界模型 | 以共享视频 diffusion backbone 统一动作生成、未来视频模拟和进度评分，并在约 27,300 小时混合数据上训练。 | 长时序 |

精读样本明确开放披露 0/7；只在摘要、comment 或已核验项目页明确披露时记为“是”。

### 同行评审锚点

| 工作 | 官方证据 | 为什么可作为本月锚点 |
|---|---|---|
| — | — | 本月首次公开的精读样本尚无可安全归属到该月的官方录用证据；这不等于论文质量较低。 |

### 反证与信号质量检查

- 多篇论文共享相同数据、模型或作者团队时，不按独立证据重复加权。
- 单一 benchmark 提升若没有真实机器人迁移，不足以升级为 A 级趋势。
- “open-source / will release” 与实际可下载、可复现实验分开记录。
- 世界模型必须展示动作、规划、控制或数据生成价值；纯视频质量不计。

<!-- 更新标记：2026-05 月度雷达 最后更新 2026.07 -->

---


## 2026 年 6 月研究雷达

> **统计口径。** 自动宽召回候选用于数量结构；7 篇精读样本用于实验与开放性指标。同比月为 2025-06。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>358</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>6/7</strong><span>摘要确认真机</span></div>
  <div class="radar-kpi"><strong>0</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

大小脑接口正在变成可监督的 3D 轨迹语言；与此同时，开放训练栈与人类视频迁移同时加速。

### 主题结构

| 主方向 | 本月候选 | 占比 | 同比候选 | 同比增量 |
|---|---:|---:|---:|---:|
| [具身基础模型](/directions/foundation-models) | 162 | 45.3% | 38 | +124 |
| [大小脑与双系统](/directions/dual-system) | 3 | 0.8% | 2 | +1 |
| [灵巧操作](/directions/dexterous-manipulation) | 57 | 15.9% | 20 | +37 |
| [世界模型](/directions/world-models) | 54 | 15.1% | 14 | +40 |
| [通用机器人学习](/directions/general-robot-learning) | 82 | 22.9% | 33 | +49 |

> 自动宽召回对 VLA 命名敏感，不能单独解释为能力增长；大小脑类因常使用隐式架构命名，自动数量是保守下界。

### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> 大小脑接口正在变成可监督的 3D 轨迹语言

**变化。** Dense Embodied CoT、3D HAMSTER 与 Continuous Reasoning 分别提供密集思维监督、3D 轨迹桥接和连续推理。

**对比。** 从抽象语言计划进化到可落地的几何中间表示。

**证据。** [Training Vision-Language-Action Models with Dense Embodied Chain-of-Thought Supervision](https://arxiv.org/abs/2606.30552)；[3D HAMSTER: Bridging Planning and Control in Hierarchical Vision Language Action Models through 3D Trajectory Guidance](https://arxiv.org/abs/2606.31329)；[Continuous Reasoning for Vision-Language-Action](https://arxiv.org/abs/2606.00229)

**成熟度与瓶颈。** 跨团队新兴趋势，标准数据格式尚未形成。 主要瓶颈是中间监督获取成本和错误计划的可恢复性。。

**战略含义。** 3D trajectory token/trace 可能成为跨模型、跨控制器的接口标准。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 触觉从专用 policy 升级为 VLA 的预测通道

**变化。** UniTacVLA、CoDex 与 Touch Dreaming 分别统一触觉理解/预测、无示范组合灵巧任务和触觉想象。

**对比。** 相较 2025 年仅做感知融合，本月出现预测和组合泛化目标。

**证据。** [UniTacVLA: Unified Tactile Understanding and Prediction in Vision Language Action Models](https://arxiv.org/abs/2606.31723)；[CoDex: Learning Compositional Dexterous Functional Manipulation without Demonstrations](https://arxiv.org/abs/2606.31909)；[Learning Versatile Humanoid Manipulation with Touch Dreaming](https://arxiv.org/abs/2604.13015)

**成熟度与瓶颈。** 方法簇初成，硬件标准化不足。 主要瓶颈是传感器寿命、同步频率和跨手型迁移。。

**战略含义。** 触觉数据层可能成为新基础设施赛道。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> 开放训练栈与人类视频迁移同时加速

**变化。** Scalable Behavior Cloning、Human-as-Humanoid 与 Qwen-VLA 分别强调开放数据/训练/评测、人类对齐本体和跨本体统一。

**对比。** 开放不再只等于放权重，而是开始覆盖数据与评测。

**证据。** [Scalable Behavior Cloning with Open Data, Training, and Evaluation](https://arxiv.org/abs/2606.27375)；[Human-as-Humanoid: Enabling Zero-Shot Humanoid Learning from Ego-Exo Human Videos with Human-Aligned Embodiments](https://arxiv.org/abs/2606.32009)；[Qwen-VLA: Unifying Vision-Language-Action Modeling across Tasks, Environments, and Robot Embodiments](https://arxiv.org/abs/2605.30280)

**成熟度与瓶颈。** 资产开放信号强，独立采用尚需时间。 主要瓶颈是数据许可、硬件可复现与评测碎片化。。

**战略含义。** 跟踪外部团队是否在 3–6 个月内真正采用这些资产。

</div>

### 蛛丝马迹：小样本领先信号

| 弱信号 | 等级 | 下一道技术门槛 | 当前判断 |
|---|---|---|---|
| 触觉从专用 policy 升级为 VLA 的预测通道 | B | 传感器寿命、同步频率和跨手型迁移。 | 方法簇初成，硬件标准化不足。 |

识别逻辑不是“论文少就更前沿”，而是寻找多个弱证据是否指向同一个尚未被主流命名的瓶颈迁移。完整方法见[弱信号探测与未来判断](/analysis/weak-signals)。

### 本月精读论文

| 论文 | v1 日期 | 主方向 | 一句话贡献 | 证据标签 |
|---|---|---|---|---|
| [Scalable Behavior Cloning with Open Data, Training, and Evaluation](https://arxiv.org/abs/2606.27375) | 2026-06-25 | 通用机器人学习 | 发布 3,500 小时、130K episodes、195 任务的 ABC-130K，以及硬件、训练、仿真和真实评测全栈。 | 真机 · 多任务 · 开放资产 |
| [Training Vision-Language-Action Models with Dense Embodied Chain-of-Thought Supervision](https://arxiv.org/abs/2606.30552) | 2026-06-29 | 大小脑与双系统 | 以 60M 帧的 dense ECoT 对齐跨本体高层认知，同时由 flow action expert 输出连续动作且推理时可跳过 CoT。 | 真机 · 跨本体 |
| [Human-as-Humanoid: Enabling Zero-Shot Humanoid Learning from Ego-Exo Human Videos with Human-Aligned Embodiments](https://arxiv.org/abs/2606.32009) | 2026-06-30 | 通用机器人学习 | 通过 ego-exo 同步、60-DoF 动作重定向和 FK-aware supervision，把人类视频转成可直接训练 humanoid VLA 的动作标签。 | 真机 · 跨本体 |
| [3D HAMSTER: Bridging Planning and Control in Hierarchical Vision Language Action Models through 3D Trajectory Guidance](https://arxiv.org/abs/2606.31329) | 2026-06-30 | 大小脑与双系统 | 让高层 VLM 直接输出 metric 3D waypoint，并无缝接入点云低层策略，修正 2D guidance 的深度歧义。 | 真机 |
| [UniTacVLA: Unified Tactile Understanding and Prediction in Vision Language Action Models](https://arxiv.org/abs/2606.31723) | 2026-06-30 | 灵巧操作 | 以统一 tactile latent 同时建模当前接触语义和未来变化，再用 tactile-action mixed controller 高频修正低频动作块。 | 真机 |
| [DVG-WM: Disentangled Video Generation Enables Efficient Embodied World Model for Robotic Manipulation](https://arxiv.org/abs/2606.32028) | 2026-06-30 | 世界模型 | 把低层动力学演化与高分辨率视觉合成解耦，通过级联 latent 生成在保留接触细节的同时最高加速 3.97 倍。 | 真机 |
| [CoDex: Learning Compositional Dexterous Functional Manipulation without Demonstrations](https://arxiv.org/abs/2606.31909) | 2026-06-30 | 灵巧操作 | 让 VLM 提取功能和场景约束，经解析优化筛选功能抓取，再以 RL 形成可 sim-to-real 的抓—移—触发组合策略。 | 摘要未确认 |

精读样本明确开放披露 1/7；只在摘要、comment 或已核验项目页明确披露时记为“是”。

### 同行评审锚点

| 工作 | 官方证据 | 为什么可作为本月锚点 |
|---|---|---|
| — | — | 本月首次公开的精读样本尚无可安全归属到该月的官方录用证据；这不等于论文质量较低。 |

### 反证与信号质量检查

- 多篇论文共享相同数据、模型或作者团队时，不按独立证据重复加权。
- 单一 benchmark 提升若没有真实机器人迁移，不足以升级为 A 级趋势。
- “open-source / will release” 与实际可下载、可复现实验分开记录。
- 世界模型必须展示动作、规划、控制或数据生成价值；纯视频质量不计。

<!-- 更新标记：2026-06 月度雷达 最后更新 2026.07 -->

---


## 2026 年 7 月研究雷达（前瞻）

> **前瞻快照。** 本页只覆盖 2026 年 7 月 1–29 日，不计算环比、同比或与完整月份的热度排名。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>166</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>6</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>3/6</strong><span>摘要确认真机</span></div>
  <div class="radar-kpi"><strong>0</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

论文报告 100K 小时级真实轨迹，暂不是已确认趋势；与此同时，具身 Agent OS 可能成为模型之上的系统层。

### 主题结构

| 主方向 | 本月候选 | 占比 | 同比候选 | 同比增量 |
|---|---:|---:|---:|---:|
| [具身基础模型](/directions/foundation-models) | 85 | 51.2% | — | — |
| [大小脑与双系统](/directions/dual-system) | 2 | 1.2% | — | — |
| [灵巧操作](/directions/dexterous-manipulation) | 22 | 13.3% | — | — |
| [世界模型](/directions/world-models) | 30 | 18.1% | — | — |
| [通用机器人学习](/directions/general-robot-learning) | 27 | 16.3% | — | — |

> 自动宽召回对 VLA 命名敏感，不能单独解释为能力增长；大小脑类因常使用隐式架构命名，自动数量是保守下界。

### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-c">C · 弱信号</span> 论文报告 100K 小时级真实轨迹，暂不是已确认趋势

**变化。** Xiaomi-Robotics-1 论文报告超过 100K 小时真实轨迹，Data Pyramid 讨论数据层级；若数据口径能被下游能力和开放评测验证，数据工程门槛将显著抬高。

**对比。** 本月仅覆盖 1–29 日，不能与完整月数量比较。

**证据。** [Xiaomi-Robotics-1: Scaling Vision-Language-Action Models with over 100K Hours of Real-World Trajectories](https://arxiv.org/abs/2607.15330)；[Data Pyramid for Embodied Manipulation](https://arxiv.org/abs/2607.24744)

**成熟度与瓶颈。** 超大规模单团队信号。 主要瓶颈是数据质量、任务分布与外部可验证性。。

**战略含义。** 未来应问“有效多样性/小时”，而不只看总小时。

</div>

<div class="trend-card">

#### <span class="signal signal-c">C · 弱信号</span> 视触觉 world model 与 VLA 自纠错正在闭环

**变化。** ViTacWorld、τ 与 DC-WAM 分别从视触觉世界模型、未来视觉监督和 world-action model 推进接触闭环。

**对比。** 6 月的触觉预测在本月进一步接到世界—动作联合建模。

**证据。** [ViTacWorld: Scaling Visuo-Tactile World Models for Contact-Rich Robot Manipulation](https://arxiv.org/abs/2607.22530)；[τ: Learning Touch-Augmented Vision-Language-Action Models from Future Visual Supervision](https://arxiv.org/abs/2607.24485)；[DC-WAM: Dynamic-Centric Visual Supervision and Reasoning for World-Action Models](https://arxiv.org/abs/2607.25918)

**成熟度与瓶颈。** 三项同月信号，但都未经长期独立验证。 主要瓶颈是触觉数据规模与未来监督偏差。。

**战略含义。** 这是最值得跟踪的非共识信号之一，验证点是失败恢复率而非单次成功率。

</div>

<div class="trend-card">

#### <span class="signal signal-c">C · 弱信号</span> 具身 Agent OS 可能成为模型之上的系统层

**变化。** PhyAgentOS 把认知规划与物理执行解耦，并强调自演化操作系统；它呼应过去一年的双系统和调度趋势。

**对比。** 此前多是论文内架构，本月出现系统软件层叙事。

**证据。** [PhyAgentOS: A Self-Evolving Operating System for Embodied Agents with Decoupled Cognitive Planning and Physical Execution](https://arxiv.org/abs/2607.16636)

**成熟度与瓶颈。** 单项早期信号。 主要瓶颈是接口标准、实时性、安全隔离和跨硬件兼容。。

**战略含义。** 若未来出现跨模型/跨机器人的第三方采用，系统层可能形成独立平台价值。

</div>

### 蛛丝马迹：小样本领先信号

| 弱信号 | 等级 | 下一道技术门槛 | 当前判断 |
|---|---|---|---|
| 论文报告 100K 小时级真实轨迹，暂不是已确认趋势 | C | 数据质量、任务分布与外部可验证性。 | 超大规模单团队信号。 |
| 视触觉 world model 与 VLA 自纠错正在闭环 | C | 触觉数据规模与未来监督偏差。 | 三项同月信号，但都未经长期独立验证。 |
| 具身 Agent OS 可能成为模型之上的系统层 | C | 接口标准、实时性、安全隔离和跨硬件兼容。 | 单项早期信号。 |

识别逻辑不是“论文少就更前沿”，而是寻找多个弱证据是否指向同一个尚未被主流命名的瓶颈迁移。完整方法见[弱信号探测与未来判断](/analysis/weak-signals)。

### 本月精读论文

| 论文 | v1 日期 | 主方向 | 一句话贡献 | 证据标签 |
|---|---|---|---|---|
| [PhyAgentOS: A Self-Evolving Operating System for Embodied Agents with Decoupled Cognitive Planning and Physical Execution](https://arxiv.org/abs/2607.16636) | 2026-07-18 | 大小脑与双系统 | 以 session 运行时、文件化状态、语义验证、记忆和安全服务解耦认知规划与异构机器人执行，并覆盖 19+ 仿真/实体本体。 | 真机 · 跨本体 |
| [Xiaomi-Robotics-1: Scaling Vision-Language-Action Models with over 100K Hours of Real-World Trajectories](https://arxiv.org/abs/2607.15330) | 2026-07-16 | 具身基础模型 | 用超过 100K 小时 UMI 真实轨迹和自动语言标注预训练基础 VLA，展示数据与模型规模向真实机器人零样本和少样本能力传导。 | 真机 |
| [DC-WAM: Dynamic-Centric Visual Supervision and Reasoning for World-Action Models](https://arxiv.org/abs/2607.25918) | 2026-07-28 | 世界模型 | 用时间差 flow matching、轨迹加权和 DynaRoute 注意力偏置，把世界模型容量从外观重建转向控制相关动态。 | 真机 |
| [ViTacWorld: Scaling Visuo-Tactile World Models for Contact-Rich Robot Manipulation](https://arxiv.org/abs/2607.22530) | 2026-07-24 | 世界模型 | 联合公开真实触觉数据与仿真，训练可生成视觉—触觉—动作 rollout 的世界模型，用于策略数据增强和离线评估。 | 摘要未确认 |
| [τ: Learning Touch-Augmented Vision-Language-Action Models from Future Visual Supervision](https://arxiv.org/abs/2607.24485) | 2026-07-27 | 灵巧操作 | 以未来视觉 latent 监督学习 action-conditioned 时空触觉表征，在部署零额外开销下适配预训练 VLA。 | 摘要未确认 |
| [Data Pyramid for Embodied Manipulation](https://arxiv.org/abs/2607.24744) | 2026-07-27 | 通用机器人学习 | 以真实机器人、UMI、人类 ego/exo、仿真和通用视觉语言五层数据金字塔梳理具身数据配方与能力关系。 | 摘要未确认 |

精读样本明确开放披露 0/6；只在摘要、comment 或已核验项目页明确披露时记为“是”。

### 同行评审锚点

| 工作 | 官方证据 | 为什么可作为本月锚点 |
|---|---|---|
| — | — | 本月首次公开的精读样本尚无可安全归属到该月的官方录用证据；这不等于论文质量较低。 |

### 反证与信号质量检查

- 多篇论文共享相同数据、模型或作者团队时，不按独立证据重复加权。
- 单一 benchmark 提升若没有真实机器人迁移，不足以升级为 A 级趋势。
- “open-source / will release” 与实际可下载、可复现实验分开记录。
- 世界模型必须展示动作、规划、控制或数据生成价值；纯视频质量不计。

<!-- 更新标记：2026-07 月度雷达 最后更新 2026.07 -->

---


## 季度演进

> 季度页观察一个信号如何从出现、扩散走向验证，避免逐月噪声掩盖方法迁移。

### 2025 Q3 · 数据入口重构

人类视频、无标签动作和 egocentric/接触表示成为弱信号主线；flow policy 扩散，触觉首次进入 VLA 统一空间，但世界模型的闭环控制证据仍弱。

| 论文候选 | 基础模型 | 双系统 | 灵巧操作 | 世界模型 | 通用学习 |
|---:|---:|---:|---:|---:|---:|
| 270 | 103 | 3 | 48 | 22 | 94 |

**阶段证据链：**

- **人类视频开始被拆成可迁移的动作先验（B）**：EC-Flow、H-RDT 与 GR-3 分别从无动作标签视频、双臂人类操作和通用数据配方切入，信号尚未形成单一范式，但都在绕开机器人示教瓶颈。
- **“大脑—小脑”正在从二层变成三系统（C）**：TriVLA 把高层语义、低层动作与 episodic world model 明确拆分；EmbodieDreamer 则让世界模型承担 real-to-sim-to-real 中介。
- **视频生成器开始越过“数据增强”，直接扮演策略（B）**：Video Generators are Robot Policies、Masquerade 与 DiWA 分别尝试直接控制、视频编辑迁移和用世界模型适配 diffusion policy。
- **触觉开始进入 VLA 统一语义空间（C）**：OmniVTLA 不再把触觉仅作为低层状态，而是与视觉、语言和动作对齐。
- **flow matching 正在成为通用策略的新执行底座（B）**：ManiFlow、EC-Flow 与 FLOWER 在通用操控、无标签视频和轻量 generalist policy 三条线上同时采用 flow。
### 2025 Q4 · 规划与预测汇合

fast–slow 形成架构簇，world model 从生成与适配转向后训练、搜索和 MPC；跨本体问题从 adapter 转向数据和动作表示。

| 论文候选 | 基础模型 | 双系统 | 灵巧操作 | 世界模型 | 通用学习 |
|---:|---:|---:|---:|---:|---:|
| 383 | 196 | 6 | 34 | 45 | 102 |

**阶段证据链：**

- **fast–slow 从隐式分工变成显式训练目标（B）**：VLA-R1、MoTVLA 与上月 VLA-Reasoner 分别用推理增强、统一快慢推理和在线搜索建立高层思考—低层动作分工。
- **世界模型开始进入 VLA 后训练（B）**：VLA-RFT 用 world simulator 给可验证奖励，Ctrl-World 强调可控生成，Latent Action Pretraining 则把预测表征回流到动作学习。
- **视频驱动双臂学习成为数据规模化的第二战场（B）**：DexMan、Parse-Augment-Distill 与真实人类活动视频预训练共同指向少机器人示教的双臂学习。
- **世界模型终于开始用规划成功率证明自己（B）**：WorldPlanner 把 action-conditioned visual world model 接入 MCTS/MPC；跨本体灵巧世界模型与 Ctrl-World 构成独立跟进。
- **跨本体迁移从模型适配转向数据分布设计（B）**：X-Diffusion、InternData-A1 与 X-VLA 分别统一人类示范、合成数据和软提示式跨本体策略。
### 2026 Q1 · 可执行性成为新门槛

latent action world model 进入 in-the-wild 与 RL simulator，Action CoT/异步触发重写大小脑接口，3 月集中出现 executable alignment、长时接触和真实评测。

| 论文候选 | 基础模型 | 双系统 | 灵巧操作 | 世界模型 | 通用学习 |
|---:|---:|---:|---:|---:|---:|
| 493 | 224 | 8 | 69 | 59 | 133 |

**阶段证据链：**

- **latent action world model 从实验室走向 in-the-wild（B）**：Learning Latent Action World Models In The Wild、Cosmos Policy 与 Motus 分别覆盖野外视频、视频模型微调和统一 latent action。
- **Action CoT 与非对称专家正在重写大小脑接口（B）**：ACoT-VLA、TwinBrainVLA 与 DualVLA 从动作链推理、非对称混合专家和部分解耦三种方式定义高低层接口。
- **人类中心数据被推到跨本体预训练主线（B）**：Being-H0.5、RoboWheel 和 InternData-A1 都把人类数据转化为 generalist policy 的可扩展监督。
- **世界模型开始承担 RL 模拟器与在线自纠错（B）**：WoVR、Self-Correcting VLA 与 World-Gymnast 分别用于后训练模拟、稀疏想象修正和世界模型内 RL。
- **快慢系统开始感知力、接触与完成状态（B）**：FAVLA 将力适应写入 fast–slow 架构，StreamVLA 用 completion-state gating 打破固定 reason–act 循环，自纠错框架补上终止判断。
### 2026 Q2 · 系统工程与触觉闭环

连续推理、coarse-to-fine 调度、3D trace 与 real-time execution 使 VLA 竞争进入系统层；触觉从融合模态升级为预测与 world model 通道。

| 论文候选 | 基础模型 | 双系统 | 灵巧操作 | 世界模型 | 通用学习 |
|---:|---:|---:|---:|---:|---:|
| 695 | 320 | 8 | 99 | 102 | 166 |

**阶段证据链：**

- **触觉与 world model 开始合流（B）**：Touch Dreaming、FingerEye 与 OmniVTA 把触觉用于未来预测、连续感知和接触世界建模。
- **双系统进入异步 coarse-to-fine 调度（B）**：Libra-VLA、Trace-Conditioned Planning 与 DIAL 不再固定每步完整推理，而是在轨迹、意图和动作层分配不同计算。
- **foundation model 开始接受垂直本体与可控行为约束（C）**：π0.7 强调 steerable generalist policy，Open-H-Embodiment 把医疗机器人纳入大规模基础模型数据。
- **视频模型正在被改造成 generalist policy，而非外置 world model（B）**：Turning Video Models into Generalist Robot Policies、τ0-WM 与 Cosmos Policy 把视频预测和动作生成压进同一训练栈。
- **连续推理开始取代离散 reason–act 循环（B）**：Continuous Reasoning、Libra-VLA 与 StreamVLA 都试图让思考与控制异步或连续发生。

### 2026 年 7 月前瞻

100K 小时级轨迹、视触觉 world-action model 与 Embodied Agent OS 是三个早期信号；由于只覆盖 1–29 日，全部保持 C 级。

<!-- 更新标记：季度演进 最后更新 2026.07 -->

---


## 年度综合：从“更大 VLA”转向“可执行、可纠错、可持续学习”

> 主分析期为 2025 年 7 月—2026 年 6 月。同比增长只在同一宽召回查询口径内有效，不代表全部机器人论文的绝对市场份额。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>1841</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>633</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>84</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>30</strong><span>官方评审锚点</span></div>
</div>

### 五方向年度结构

| 方向 | 同比基线 | 主分析期 | 绝对增量 | 主分析期占比 |
|---|---:|---:|---:|---:|
| [具身基础模型](/directions/foundation-models) | 157 | 843 | +686 | 45.8% |
| [大小脑与双系统](/directions/dual-system) | 7 | 25 | +18 | 1.4% |
| [灵巧操作](/directions/dexterous-manipulation) | 134 | 250 | +116 | 13.6% |
| [世界模型](/directions/world-models) | 70 | 228 | +158 | 12.4% |
| [通用机器人学习](/directions/general-robot-learning) | 265 | 495 | +230 | 26.9% |

最显著的事实是具身基础模型候选增量远高于其他方向；但弱信号更多出现在双系统调度、触觉 world model、失败恢复和数据闭环，这些领域的论文数量反而不占主导。

### A 级：已确认路线

| 判断 | 为什么升级 | 官方证据 |
|---|---|---|
| <span class="signal signal-a">A</span> VLA / generalist policy 已从预印本热点变成正式研究主线 | π0、FAST、π0.5 等独立正式工作覆盖动作生成、效率和开放世界泛化。 | [π0: A Vision-Language-Action Flow Model for General Robot Control](https://www.roboticsproceedings.org/rss21/p010.html)；[FAST: Efficient Action Tokenization for Vision-Language-Action Models](https://www.roboticsproceedings.org/rss21/p012.html)；[π0.5: a Vision-Language-Action Model with Open-World Generalization](https://proceedings.mlr.press/v305/black25a.html) |
| <span class="signal signal-a">A</span> 快慢分工与中间推理已获得独立评审验证 | Embodied CoT、Reactive Diffusion Policy 与 ACoT-VLA 从语言推理、视觉触觉控制和动作链三侧验证。 | [Robotic Control via Embodied Chain-of-Thought Reasoning](https://proceedings.mlr.press/v270/zawalski25a.html)；[Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html)；[ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Zhong_ACoT-VLA_Action_Chain-of-Thought_for_Vision-Language-Action_Models_CVPR_2026_paper.html) |
| <span class="signal signal-a">A</span> 机器人世界模型从生成转向控制的路线已被多 venue 接纳 | 视频—动作联合、latent dynamics、3D 物理预测和统一 latent action 都有官方评审证据。 | [Unified World Models: Coupling Video and Action Diffusion for Pretraining on Large Robotic Datasets](https://www.roboticsproceedings.org/rss21/p015.html)；[LaDi-WM: A Latent Diffusion-based World Model for Predictive Manipulation](https://proceedings.mlr.press/v305/huang25a.html)；[ParticleFormer: A 3D Point Cloud World Model for Multi-Object, Multi-Material Robotic Manipulation](https://proceedings.mlr.press/v305/huang25c.html)；[Motus: A Unified Latent Action World Model](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html) |
| <span class="signal signal-a">A</span> 灵巧操作的数据与触觉路线已跨团队验证 | 视觉触觉、UMI 人类示范与 egocentric 通用手控制形成连续证据链。 | [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html)；[DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://proceedings.mlr.press/v305/xu25b.html)；[UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html) |

### 持续升温

- **VLA 后训练与经验学习。** 从 VLA-RFT、π*0.6 到 2026 年的在线自纠错，目标从复制示范转向用部署经验改进。
- **世界模型的可执行性。** 2026 年 3 月后，inverse dynamics reward、RL simulator 和 world-action unified model 密集出现。
- **视触觉闭环。** 触觉从感知输入升级为 future prediction、world model 和 recovery 信号。
- **跨本体数据与动作表示。** 共享人类视频、latent action、接触表示与 embodiment adapter 正在收敛。

### 出现拐点

- **大小脑。** 2025 年重在 planner–policy 结构，2026 年转向异步调度、continuous reasoning、completion gating 和 3D trace。
- **通用性。** 从“同一模型做更多 benchmark”转向“同一训练栈适应真实、灵巧、软体、医疗等高约束任务”。
- **开放。** 从只放权重扩展到数据、训练、评测和低成本采集工具。

### 降温与未兑现

- **只以视频生成质量证明的世界模型：D。** 若不报告规划或控制收益，不再视为强信号。
- **堆叠模块式 VLA：D。** 更换 backbone、adapter 或 action head 而没有新能力的工作增长很快，但战略价值有限。
- **“一个权重跨所有机器人”：C/D。** 现有证据更支持共享表征 + embodiment adapter。
- **开源承诺即生态：D。** 只有出现第三方复现和采用，开源热度才升级为趋势。

### 下一步

真正领先于共识的八项判断见[弱信号探测与未来判断](/analysis/weak-signals)。每项都包含 3–24 个月验证路标和反证条件。

<!-- 更新标记：年度综合 最后更新 2026.07 -->

---


## 弱信号探测与未来判断

> 热门 topic 说明共识已经形成；本页寻找的是尚未成为高频标签、却可能提前暴露下一轮瓶颈迁移的“蛛丝马迹”。预测截至 2026-07-29，不是事实陈述。

### 共识热度与弱信号有什么不同

| 维度 | 共识热点 | 有价值的弱信号 |
|---|---|---|
| 数量 | 同月大量论文 | 初期只有 1–3 项 |
| 命名 | 已有统一标签 | 多个团队用不同名字解决同一问题 |
| 证据 | benchmark 密集 | 出现新的真机指标、失败类型或系统约束 |
| 风险 | 容易追高与同质化 | 容易误判、需要明确反证 |
| 用途 | 判断资源拥挤度 | 提前布局能力、数据和基础设施 |

### 五步弱信号探测器

```mermaid
flowchart LR
  A["异常点<br/>新能力 / 新失败类型<br/> "] --> B["去项目簇<br/>同团队只算一次<br/> "]
  B --> C["跨名词对齐<br/>是否解决同一瓶颈<br/> "]
  C --> D["证据升级<br/>仿真→真机→独立采用<br/> "]
  D --> E["设置路标<br/>3–12 月可验证<br/> "]
  E --> F["设置反证<br/>失败即降级<br/> "]
```

每个候选弱信号按以下维度评分：

| 维度 | 分值 | 问题 |
|---|---:|---|
| 新颖性 | 0–2 | 是否引入新的能力、数据来源、接口或评价指标？ |
| 独立性 | 0–2 | 是否有至少两个不重叠作者/机构团队？ |
| 证据升级 | 0–2 | 是否从仿真走向真机、从成功率走向恢复/长时/跨本体？ |
| 使能性 | 0–1 | 是否可能成为其他路线的基础设施？ |
| 可证伪 | 0–1 | 未来 3–12 个月是否有明确验证路标？ |
| 同项目簇惩罚 | 0 至 −2 | 是否只是同一模型/数据集的多篇衍生论文？ |
| 命名潮惩罚 | 0 至 −2 | 是否只是换模型名而没有新能力？ |

总分 5 分以上进入月度弱信号卡；只有跨月扩散或获得独立评审后才升级为 B/A。数量再大，也不会自动升级。

### 未来趋势判断


### 1. VLA 的主战场将从“更大模型”转向实时执行栈

**置信度 / 时间窗：** 高 · 3–9 个月

**已经观察到的事实。** fast–slow、异步 coarse-to-fine、连续推理和 real-time VLA 在不同团队连续出现，解决的共同问题是推理频率与控制频率不匹配。

**我们的判断。** 下一轮有价值的基础设施将是 completion gating、异步缓存、动作 horizon 自适应、边缘部署和故障恢复，而不是单纯增加 VLM 参数。

**论文证据。** [FAVLA: A Force-Adaptive Fast-Slow VLA model for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2602.23648)；[Libra-VLA: Achieving Learning Equilibrium via Asynchronous Coarse-to-Fine Dual-System](https://arxiv.org/abs/2604.24921)；[Continuous Reasoning for Vision-Language-Action](https://arxiv.org/abs/2606.00229)；[Xiaomi-Robotics-0: An Open-Sourced Vision-Language-Action Model with Real-Time Execution](https://arxiv.org/abs/2602.12684)

| 验证路标 | 反证条件 |
|---|---|
| 公开评测开始同时报告端到端延迟、控制频率、状态陈旧度和恢复时间；同一模型通过调度改进获得显著真机收益。 | 更强的单体端到端模型在相同硬件上持续压过所有模块化/异步方案，且延迟不再是主要失败源。 |

**战略含义。** 优先关注能跨模型、跨硬件复用的 runtime 与控制中间层。

### 2. “小脑”会被 verifier、critic 与自纠错器重新定义

**置信度 / 时间窗：** 高 · 3–12 个月

**已经观察到的事实。** 在线搜索、稀疏世界想象、自逆动力学奖励和 Action CoT 都在引入动作候选验证，而不只是生成下一步。

**我们的判断。** 高低层分工将从 planner–policy 两块模型转向 policy + lightweight verifier + recovery loop；验证器可能比慢推理模型更快形成独立组件。

**论文证据。** [VLA-Reasoner: Empowering Vision-Language-Action Models with Reasoning via Online Monte Carlo Tree Search](https://arxiv.org/abs/2509.22643)；[Self-Correcting VLA: Online Action Refinement via Sparse World Imagination](https://arxiv.org/abs/2602.21633)；[EVA: Aligning Video World Models with Executable Robot Actions via Inverse Dynamics Rewards](https://arxiv.org/abs/2603.17808)；[ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://arxiv.org/abs/2601.11404)

| 验证路标 | 反证条件 |
|---|---|
| 第三方策略接入同一 verifier 后获得跨任务提升；评测从平均成功率扩展到失败检测召回率和恢复成功率。 | 验证器只在作者自有策略上有效，跨策略迁移失败，或计算开销抵消全部收益。 |

**战略含义。** 把失败数据、可验证奖励和恢复轨迹视为独立数据资产。

### 3. 数据飞轮将从示教采集转向“部署—失败—修正—再训练”

**置信度 / 时间窗：** 高 · 6–12 个月

**已经观察到的事实。** 从经验学习、低成本真实人类示范、开放训练栈，以及论文报告的 100K 小时级真实轨迹，把数据竞争从一次性 dataset 推向持续运营。

**我们的判断。** 数据量仍重要，但最具区分度的会是失败覆盖率、修正效率和任务分布更新速度；真正的 moat 在部署闭环而非公开抓取视频。

**论文证据。** [$π^{*}_{0.6}$: a VLA That Learns From Experience](https://arxiv.org/abs/2511.14759)；[RoboWheel: A Data Engine from Real-World Human Demonstrations for Cross-Embodiment Robotic Learning](https://arxiv.org/abs/2512.02729)；[Scalable Behavior Cloning with Open Data, Training, and Evaluation](https://arxiv.org/abs/2606.27375)；[Xiaomi-Robotics-1: Scaling Vision-Language-Action Models with over 100K Hours of Real-World Trajectories](https://arxiv.org/abs/2607.15330)

| 验证路标 | 反证条件 |
|---|---|
| 团队开始披露每周新增有效轨迹、失败类型覆盖、在线修正样本效率，以及新任务上线周期。 | 离线人类视频预训练在缺少部署回流时仍能稳定获得相同的长尾泛化。 |

**战略含义。** 评估团队时优先看可持续真机接触面和数据治理能力。

### 4. world model 将被迫用闭环控制收益而非视频质量生存

**置信度 / 时间窗：** 高 · 3–9 个月

**已经观察到的事实。** MCTS/MPC、RL simulator、executable alignment 和直接视频策略四条路线都把评估目标推向动作。

**我们的判断。** 世界模型会分化为两类：为策略提供紧凑 latent dynamics 的控制模型，以及为数据合成服务的高保真生成器；中间态的“漂亮视频模型”将降温。

**论文证据。** [WorldPlanner: Monte Carlo Tree Search and MPC with Action-Conditioned Visual World Models](https://arxiv.org/abs/2511.03077)；[WoVR: World Models as Reliable Simulators for Post-Training VLA Policies with RL](https://arxiv.org/abs/2602.13977)；[EVA: Aligning Video World Models with Executable Robot Actions via Inverse Dynamics Rewards](https://arxiv.org/abs/2603.17808)；[Turning Video Models into Generalist Robot Policies](https://arxiv.org/abs/2605.27817)

| 验证路标 | 反证条件 |
|---|---|
| 论文以同算力下的规划成功率、样本效率或失败恢复率作为主结果，并报告 model bias。 | 生成质量提升能稳定、无需动作对齐地转化为跨机器人控制提升。 |

**战略含义。** 避免把纯视频生成能力估值为机器人世界模型能力。

### 5. 触觉会先成为自纠错与 world model 通道，再成为通用语义模态

**置信度 / 时间窗：** 中高 · 6–18 个月

**已经观察到的事实。** 触觉从 VLA 融合扩展到视触觉世界建模、touch dreaming、统一理解/预测和 7 月的规模化世界模型。

**我们的判断。** 触觉最先兑现的指标会是接触失败检测、材料/滑移预测和动作恢复，不是开放词汇理解。

**论文证据。** [OmniVTLA: Vision-Tactile-Language-Action Models with Semantic-Aligned Tactile Sensing](https://arxiv.org/abs/2508.08706)；[OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2603.19201)；[Learning Versatile Humanoid Manipulation with Touch Dreaming](https://arxiv.org/abs/2604.13015)；[UniTacVLA: Unified Tactile Understanding and Prediction in Vision Language Action Models](https://arxiv.org/abs/2606.31723)；[ViTacWorld: Scaling Visuo-Tactile World Models for Contact-Rich Robot Manipulation](https://arxiv.org/abs/2607.22530)

| 验证路标 | 反证条件 |
|---|---|
| 跨传感器、跨手型 benchmark 出现；加入触觉后恢复率显著提升，并能在未知物体上保持。 | 触觉增益只在单一自研硬件和封闭任务存在，跨设备校准成本长期无法下降。 |

**战略含义。** 关注传感器标准、同步数据格式和自动标定，而不只看单个灵巧手 demo。

### 6. 跨本体迁移将收敛到“规范动作空间 + 小型本体适配器”

**置信度 / 时间窗：** 中高 · 6–18 个月

**已经观察到的事实。** 软提示、跨本体人类示范、人类中心预训练、通用灵巧手套件和 human-as-humanoid 共同尝试消除动作表示差异。

**我们的判断。** 一个权重直接覆盖所有机器人不太现实；更可能形成共享时空/接触表征，加少量 embodiment adapter 与安全约束。

**论文证据。** [X-VLA: Soft-Prompted Transformer as Scalable Cross-Embodiment Vision-Language-Action Model](https://arxiv.org/abs/2510.10274)；[X-Diffusion: Training Diffusion Policies on Cross-Embodiment Human Demonstrations](https://arxiv.org/abs/2511.04671)；[Being-H0.5: Scaling Human-Centric Robot Learning for Cross-Embodiment Generalization](https://arxiv.org/abs/2601.12993)；[UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://arxiv.org/abs/2603.22264)；[Human-as-Humanoid: Enabling Zero-Shot Humanoid Learning from Ego-Exo Human Videos with Human-Aligned Embodiments](https://arxiv.org/abs/2606.32009)

| 验证路标 | 反证条件 |
|---|---|
| 同一共享策略只用少量目标机器人数据即可适配，且负迁移可预测。 | 跨本体性能持续由大规模目标硬件数据决定，共享表征无法显著降低样本量。 |

**战略含义。** 可组合的动作接口与适配工具链比单一“通用权重”更值得长期跟踪。

### 7. 3D trajectory / trace 可能成为大脑与控制器之间的接口标准

**置信度 / 时间窗：** 中 · 6–15 个月

**已经观察到的事实。** 未来 3D/4D 表征、trace-conditioned planning、密集 embodied CoT 和 3D 轨迹引导连续出现。

**我们的判断。** 自然语言计划太抽象、关节动作太具体，3D trace 是可验证且相对跨本体的中间层候选。

**论文证据。** [StemVLA:An Open-Source Vision-Language-Action Model with Future 3D Spatial Geometry Knowledge and 4D Historical Representation](https://arxiv.org/abs/2602.23721)；[Long-Horizon Manipulation via Trace-Conditioned VLA Planning](https://arxiv.org/abs/2604.21924)；[Training Vision-Language-Action Models with Dense Embodied Chain-of-Thought Supervision](https://arxiv.org/abs/2606.30552)；[3D HAMSTER: Bridging Planning and Control in Hierarchical Vision Language Action Models through 3D Trajectory Guidance](https://arxiv.org/abs/2606.31329)

| 验证路标 | 反证条件 |
|---|---|
| 不同 VLM 与不同低层 policy 能通过同一 trace 协议互换，且在长时任务上降低数据量。 | 中间轨迹误差导致级联失败，端到端 latent interface 持续更优。 |

**战略含义。** 观察数据标注工具、轨迹 tokenization 和 trace verifier 是否出现开源生态。

### 8. 模型之上可能出现 Embodied Agent OS，但现在仍是高风险信号

**置信度 / 时间窗：** 低 · 12–24 个月

**已经观察到的事实。** 在本次语料中，PhyAgentOS 首次把自演化、认知规划与物理执行解耦包装为操作系统；背后已有一年多双系统与异步调度积累。

**我们的判断。** 如果机器人模型和硬件继续碎片化，统一任务、记忆、权限、调度与安全隔离的系统层可能独立出来。

**论文证据。** [PhyAgentOS: A Self-Evolving Operating System for Embodied Agents with Decoupled Cognitive Planning and Physical Execution](https://arxiv.org/abs/2607.16636)；[Libra-VLA: Achieving Learning Equilibrium via Asynchronous Coarse-to-Fine Dual-System](https://arxiv.org/abs/2604.24921)；[DualVLA: Building a Generalizable Embodied Agent via Partial Decoupling of Reasoning and Action](https://arxiv.org/abs/2511.22134)

| 验证路标 | 反证条件 |
|---|---|
| 至少两个外部机器人平台和两个模型家族接入同一 OS，形成插件/工具生态。 | 硬件厂商持续封闭全栈，接口无法标准化，所谓 OS 仅是单项目 orchestration code。 |

**战略含义。** 只作为长期期权跟踪；在出现第三方采用前不应按平台估值。

### 如何持续更新

每月新增论文后，先检查路标而不是重写预测：出现第三方采用、真实机器人恢复率、跨硬件 benchmark 或开放训练资产时升级；连续两个季度没有独立跟进、只剩同团队系列工作或真机增益消失时降级。

<!-- 更新标记：弱信号与未来判断 最后更新 2026.07 -->

---


## 具身基础模型

> 把视觉、语言、机器人状态与连续动作放入可跨任务复用的预训练—后训练框架，核心不只是模型规模，而是数据覆盖、动作表示、实时执行和经验学习。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>843</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>157</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>9</strong><span>官方评审锚点</span></div>
  <div class="radar-kpi"><strong>45.8%</strong><span>主分析期占比</span></div>
</div>

### 跨月演进

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

### 技术路线对比

| 路线 | 核心表示/机制 | 优势 | 当前局限 |
|---|---|---|---|
| 自回归 action token | 离散动作 token / chunk | 训练与语言模型兼容 | 量化误差、控制频率 |
| Diffusion / flow action | 连续轨迹分布 | 多峰动作、平滑控制 | 采样延迟、闭环修正 |
| 分层 / 双系统 VLA | 语义计划 + 低层执行 | 长时任务、可解释接口 | 模块误差与异步调度 |
| 视频—动作统一模型 | 预测未来 + 生成动作 | 人类视频扩展、world knowledge | 像素冗余、可执行性 |

### 代表工作

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

### 同行评审锚点

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

### 成熟度、瓶颈与战略判断

**成熟度。** 已从概念验证进入多团队真实机器人阶段；但“通用”仍高度依赖训练机器人、任务模板和评测环境。

**关键瓶颈。**

- 实时推理与控制频率
- 长尾失败恢复
- 跨本体负迁移
- 可持续部署数据闭环
- 安全与不确定性

**战略判断。** 短期不应只按模型参数或 benchmark 排名判断团队；应重点比较真实部署时延、数据飞轮、跨本体适配成本和失败恢复。

<!-- 更新标记：具身基础模型 最后更新 2026.07 -->

---


## 大小脑与双系统

> 由慢速语义推理/规划与快速反应控制协同完成任务；本报告也纳入未使用 System 1/2 命名、但实际具备高层意图与低层策略分工的工作。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>25</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>官方评审锚点</span></div>
  <div class="radar-kpi"><strong>1.4%</strong><span>主分析期占比</span></div>
</div>

### 跨月演进

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

### 技术路线对比

| 路线 | 核心表示/机制 | 优势 | 当前局限 |
|---|---|---|---|
| 显式 planner–policy | VLM/LLM 计划后调用 policy | 模块可替换、易解释 | 计划误差难恢复 |
| 统一 fast–slow 模型 | 共享表征、不同计算路径 | 端到端优化、延迟较低 | 分工是否真实存在难验证 |
| 搜索 / verifier | 生成候选并用模型或奖励验证 | 失败检测与自纠错 | 测试时计算高 |
| 3D trace / latent intent | 中间轨迹或潜意图连接动作 | 更接近几何执行、可跨本体 | 监督获取与接口标准 |

### 代表工作

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

### 同行评审锚点

| 工作 | Venue | arXiv |
|---|---|---|
| [Robotic Control via Embodied Chain-of-Thought Reasoning](https://proceedings.mlr.press/v270/zawalski25a.html) | CoRL 2024 | [2407.08693](https://arxiv.org/abs/2407.08693) |
| [ReKep: Spatio-Temporal Reasoning of Relational Keypoint Constraints for Robotic Manipulation](https://proceedings.mlr.press/v270/huang25g.html) | CoRL 2024 | [2409.01652](https://arxiv.org/abs/2409.01652) |
| [Reflective Planning: Vision-Language Models for Multi-Stage Long-Horizon Robotic Manipulation](https://proceedings.mlr.press/v305/feng25b.html) | CoRL 2025 | [2502.16707](https://arxiv.org/abs/2502.16707) |
| [ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Zhong_ACoT-VLA_Action_Chain-of-Thought_for_Vision-Language-Action_Models_CVPR_2026_paper.html) | CVPR 2026 | [2601.11404](https://arxiv.org/abs/2601.11404) |
| [Action-Sketcher: From Reasoning to Action via Visual Sketches for Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Tan_Action-Sketcher_From_Reasoning_to_Action_via_Visual_Sketches_for_Robotic_CVPR_2026_paper.html) | CVPR 2026 | [2601.01618](https://arxiv.org/abs/2601.01618) |
| [AtomicVLA: Unlocking the Potential of Atomic Skill Learning in Robots](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_AtomicVLA_Unlocking_the_Potential_of_Atomic_Skill_Learning_in_Robots_CVPR_2026_paper.html) | CVPR 2026 | [2603.07648](https://arxiv.org/abs/2603.07648) |
| [SIMPACT: Simulation-Enabled Action Planning using Vision-Language Models](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_SIMPACT_Simulation-Enabled_Action_Planning_using_Vision-Language_Models_CVPR_2026_paper.html) | CVPR 2026 | [2512.05955](https://arxiv.org/abs/2512.05955) |

### 成熟度、瓶颈与战略判断

**成熟度。** 架构概念已获得多项同行评审锚点，正在向实时系统和故障恢复迁移。

**关键瓶颈。**

- 何时触发慢推理
- 异步状态陈旧
- 验证器可靠性
- 接口误差传播
- 安全终止

**战略判断。** 真正的机会可能在推理调度、verifier、恢复和中间表示，而不是把两个模型简单串联。

<!-- 更新标记：大小脑与双系统 最后更新 2026.07 -->

---


## 灵巧操作

> 覆盖多指手、双臂、臂手协同、触觉与接触密集操作；判断成熟度时优先看长时连续接触、真实机器人和跨硬件可复现性。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>250</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>134</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>5</strong><span>官方评审锚点</span></div>
  <div class="radar-kpi"><strong>13.6%</strong><span>主分析期占比</span></div>
</div>

### 跨月演进

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

### 技术路线对比

| 路线 | 核心表示/机制 | 优势 | 当前局限 |
|---|---|---|---|
| 遥操作 / UMI | 直接采集人类或领导臂示范 | 高质量、真实接触 | 设备成本与动作映射 |
| 人类视频 / egocentric | 从第一视角或手部视频预训练 | 规模大、硬件无关 | 缺失力和动作标签 |
| 仿真 / 生成数据 | 合成接触、奖励或视频 | 覆盖长尾、成本低 | sim-to-real 与可行性过滤 |
| 视触觉策略 / world model | 预测接触与未来状态 | 失败恢复、精细控制 | 传感器标准化 |

### 代表工作

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

### 同行评审锚点

| 工作 | Venue | arXiv |
|---|---|---|
| [OmniH2O: Universal and Dexterous Human-to-Humanoid Whole-Body Teleoperation and Learning](https://proceedings.mlr.press/v270/he25b.html) | CoRL 2024 | [2406.08858](https://arxiv.org/abs/2406.08858) |
| [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html) | RSS 2025 | [2503.02881](https://arxiv.org/abs/2503.02881) |
| [DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://proceedings.mlr.press/v305/xu25b.html) | CoRL 2025 | [2505.21864](https://arxiv.org/abs/2505.21864) |
| [UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html) | CVPR 2026 | [2603.22264](https://arxiv.org/abs/2603.22264) |
| [Cross-Hand Latent Representation for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Jiang_Cross-Hand_Latent_Representation_for_Vision-Language-Action_Models_CVPR_2026_paper.html) | CVPR 2026 | [2603.10158](https://arxiv.org/abs/2603.10158) |

### 成熟度、瓶颈与战略判断

**成熟度。** 真实机器人证据显著增强，但硬件、传感器和 benchmark 仍碎片化。

**关键瓶颈。**

- 触觉硬件一致性
- 高频同步数据
- 跨手型动作空间
- 长时接触误差
- 安全与耐久

**战略判断。** 具备硬件、数据协议和策略闭环的一体化团队更可能积累壁垒；单次炫技 demo 的可复制性有限。

<!-- 更新标记：灵巧操作 最后更新 2026.07 -->

---


## 世界模型

> 只纳入与动作、交互、规划、控制或机器人数据生成直接相关的预测模型；普通视频生成不计入。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>228</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>70</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>5</strong><span>官方评审锚点</span></div>
  <div class="radar-kpi"><strong>12.4%</strong><span>主分析期占比</span></div>
</div>

### 跨月演进

- 2025 H1：Unified World Models、LaDi-WM、ParticleFormer 为视频—动作联合、latent dynamics 与物理 3D 预测提供同行评审锚点。
- 2025 Q3：world model 主要承担数据生成、适配和 real-to-sim-to-real。
- 2025 Q4：WorldPlanner、Motus、STORM 把搜索、MPC 与 latent action 接入闭环。
- 2026 H1：RL simulator、executable alignment、视触觉预测和视频—动作统一使评价标准转向控制收益。

| 月份 | 候选数 | 相对热度 |
|---|---:|---|
| 2025-07 | 4 | █ |
| 2025-08 | 6 | █ |
| 2025-09 | 12 | ███ |
| 2025-10 | 16 | ████ |
| 2025-11 | 13 | ███ |
| 2025-12 | 16 | ████ |
| 2026-01 | 13 | ███ |
| 2026-02 | 23 | █████ |
| 2026-03 | 23 | █████ |
| 2026-04 | 20 | ████ |
| 2026-05 | 28 | ██████ |
| 2026-06 | 54 | ████████████ |

### 技术路线对比

| 路线 | 核心表示/机制 | 优势 | 当前局限 |
|---|---|---|---|
| 像素 / 视频预测 | 生成未来观测 | 可利用网络视频、可解释 | 计算冗余、动作可执行性弱 |
| latent dynamics | 在紧凑状态空间预测 | 规划高效、易接 policy | 语义丢失、潜变量不可辨识 |
| 3D / 4D 物理模型 | 点云、几何或材质状态预测 | 空间与接触更明确 | 传感与建模成本高 |
| world-action unified | 联合预测视频和动作 | 训练目标统一、可直接控制 | 模型偏差与奖励投机 |

### 代表工作

| 论文 | v1 月份 | 状态 | 一句话贡献 |
|---|---|---|---|
| [Unified World Models: Coupling Video and Action Diffusion for Pretraining on Large Robotic Datasets](https://arxiv.org/abs/2504.02792) | 2025-04 | [RSS 2025](https://www.roboticsproceedings.org/rss21/p015.html) | Imitation learning has emerged as a promising approach towards building generalist robots |
| [LaDi-WM: A Latent Diffusion-based World Model for Predictive Manipulation](https://arxiv.org/abs/2505.11528) | 2025-05 | [CoRL 2025](https://proceedings.mlr.press/v305/huang25a.html) | Predictive manipulation has recently gained considerable attention in the Embodied AI community due to its potential to improve robot policy performance by leveraging predicted states |
| [ParticleFormer: A 3D Point Cloud World Model for Multi-Object, Multi-Material Robotic Manipulation](https://arxiv.org/abs/2506.23126) | 2025-06 | [CoRL 2025](https://proceedings.mlr.press/v305/huang25c.html) | 3D world models (i.e., learning-based 3D dynamics models) offer a promising approach to generalizable robotic manipulation by capturing the underlying physics of environment evolution conditioned on robot actions |
| [WorldPlanner: Monte Carlo Tree Search and MPC with Action-Conditioned Visual World Models](https://arxiv.org/abs/2511.03077) | 2025-11 | arXiv | WorldPlanner 用数小时无结构 play data 学动作条件视频世界模型、动作采样器和可选奖励，再以 MCTS+MPC 在真实机器人上规划。 |
| [Motus: A Unified Latent Action World Model](https://arxiv.org/abs/2512.13030) | 2025-12 | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html) | Motus 用 MoT 统一理解、视频生成和动作专家，并以 optical-flow latent action 支持世界模型、VLA、逆动力学等多种模式。 |
| [WoVR: World Models as Reliable Simulators for Post-Training VLA Policies with RL](https://arxiv.org/abs/2602.13977) | 2026-02 | arXiv | 通过可控动作条件视频模型、关键帧初始化 rollout 和模型—策略共同演化，降低想象滚动的幻觉深度并用于 VLA 的 RL 后训练。 |
| [EVA: Aligning Video World Models with Executable Robot Actions via Inverse Dynamics Rewards](https://arxiv.org/abs/2603.17808) | 2026-03 | arXiv | 把 inverse dynamics model 反用作奖励模型，以速度、加速度、jerk 和本体约束对视频世界模型做可执行性对齐。 |
| [OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2603.19201) | 2026-03 | arXiv | 以 21K+ 轨迹、86 任务的视觉—触觉—动作数据训练双流世界模型，并用 60Hz 触觉反射闭环纠偏。 |
| [Turning Video Models into Generalist Robot Policies](https://arxiv.org/abs/2605.27817) | 2026-05 | arXiv | 保持 video planner 本体无关，仅为各机器人训练基于 Jacobian 的 IDM，形成可替换视频模型的闭环 VERA 路线。 |
| [$τ_0$-WM: A Unified Video-Action World Model for Robotic Manipulation](https://arxiv.org/abs/2606.01027) | 2026-05 | arXiv | 以共享视频 diffusion backbone 统一动作生成、未来视频模拟和进度评分，并在约 27,300 小时混合数据上训练。 |

### 同行评审锚点

| 工作 | Venue | arXiv |
|---|---|---|
| [Unified World Models: Coupling Video and Action Diffusion for Pretraining on Large Robotic Datasets](https://www.roboticsproceedings.org/rss21/p015.html) | RSS 2025 | [2504.02792](https://arxiv.org/abs/2504.02792) |
| [LaDi-WM: A Latent Diffusion-Based World Model for Predictive Manipulation](https://proceedings.mlr.press/v305/huang25a.html) | CoRL 2025 | [2505.11528](https://arxiv.org/abs/2505.11528) |
| [ParticleFormer: A 3D Point Cloud World Model for Multi-Object, Multi-Material Robotic Manipulation](https://proceedings.mlr.press/v305/huang25c.html) | CoRL 2025 | [2506.23126](https://arxiv.org/abs/2506.23126) |
| [Motus: A Unified Latent Action World Model](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html) | CVPR 2026 | [2512.13030](https://arxiv.org/abs/2512.13030) |
| [PointWorld: Scaling 3D World Models for In-The-Wild Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Huang_PointWorld_Scaling_3D_World_Models_for_In-The-Wild_Robotic_Manipulation_CVPR_2026_paper.html) | CVPR 2026 | [2601.03782](https://arxiv.org/abs/2601.03782) |

### 成熟度、瓶颈与战略判断

**成熟度。** 同行评审证据较强，但真实机器人长时闭环仍是分水岭。

**关键瓶颈。**

- 长时 roll-out 漂移
- model bias
- 逆动力学可执行性
- 规划算力
- 真实接触建模

**战略判断。** 把‘是否在同算力下提高真实控制成功率’设为硬门槛，避免把生成质量误判为机器人能力。

<!-- 更新标记：世界模型 最后更新 2026.07 -->

---


## 通用机器人学习

> 覆盖跨任务/本体迁移、人类视频学习、模仿与强化学习、diffusion/flow policy 和数据规模化，是其他四类方法落地的共同训练底座。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>495</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>265</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>4</strong><span>官方评审锚点</span></div>
  <div class="radar-kpi"><strong>26.9%</strong><span>主分析期占比</span></div>
</div>

### 跨月演进

- 2024–2025 H1：diffusion/flow policy、latent action 和大规模机器人数据确立通用训练底座。
- 2025 H2：无标签视频、数据编辑、合成数据和跨本体 diffusion 扩大非机器人监督。
- 2026 Q1：egocentric 人类数据与在线/离线 RL 开始补足接触和经验学习。
- 2026 Q2：开放数据—训练—评测栈与 human-as-humanoid 指向共享表示 + 本体适配器。

| 月份 | 候选数 | 相对热度 |
|---|---:|---|
| 2025-07 | 23 | ███ |
| 2025-08 | 29 | ████ |
| 2025-09 | 42 | ██████ |
| 2025-10 | 37 | █████ |
| 2025-11 | 31 | █████ |
| 2025-12 | 34 | █████ |
| 2026-01 | 26 | ████ |
| 2026-02 | 44 | ██████ |
| 2026-03 | 63 | █████████ |
| 2026-04 | 36 | █████ |
| 2026-05 | 48 | ███████ |
| 2026-06 | 82 | ████████████ |

### 技术路线对比

| 路线 | 核心表示/机制 | 优势 | 当前局限 |
|---|---|---|---|
| Imitation / behavior cloning | 从示范直接学习 | 稳定、工程成熟 | 分布外恢复弱 |
| Diffusion / flow policy | 生成多峰动作分布 | 精细连续控制 | 推理时延与反馈修正 |
| Offline / online RL | 用奖励改进策略 | 能从失败和部署经验学习 | 奖励、安全与样本成本 |
| 人类视频 / 跨本体 | 共享视觉—动作或接触表征 | 数据规模大、迁移潜力高 | 动力学与动作空间不一致 |

### 代表工作

| 论文 | v1 月份 | 状态 | 一句话贡献 |
|---|---|---|---|
| [UniVLA: Learning to Act Anywhere with Task-centric Latent Actions](https://arxiv.org/abs/2505.06111) | 2025-05 | [RSS 2025](https://www.roboticsproceedings.org/rss21/p014.html) | A generalist robot should perform effectively across various environments |
| [EC-Flow: Enabling Versatile Robotic Manipulation from Action-Unlabeled Videos via Embodiment-Centric Flow](https://arxiv.org/abs/2507.06224) | 2025-07 | arXiv | 从无动作标签视频预测 embodiment-centric flow，再借 URDF 约束转成可执行动作，覆盖遮挡、柔性物体及非位移操作。 |
| [H-RDT: Human Manipulation Enhanced Bimanual Robotic Manipulation](https://arxiv.org/abs/2507.23523) | 2025-07 | arXiv | 以 2B diffusion transformer 先学大规模第一视角人类手部先验，再用模块化动作编解码器适配不同机器人，显著提升双臂真实操作。 |
| [X-Diffusion: Training Diffusion Policies on Cross-Embodiment Human Demonstrations](https://arxiv.org/abs/2511.04671) | 2025-11 | arXiv | X-Diffusion 将人类动作视为机器人动作的噪声对应物，只在高噪声层引入跨本体人类示范，五个真实任务平均提升 16%。 |
| [RoboWheel: A Data Engine from Real-World Human Demonstrations for Cross-Embodiment Robotic Learning](https://arxiv.org/abs/2512.02729) | 2025-12 | arXiv | RoboWheel 将单目/RGB-D 人类手物视频重建为物理可行接触轨迹，再重定向到夹爪、灵巧手和人形本体并做仿真扩增。 |
| [Being-H0.5: Scaling Human-Centric Robot Learning for Cross-Embodiment Generalization](https://arxiv.org/abs/2601.12993) | 2026-01 | arXiv | 以 35,000 小时、30 种本体的 UniHand-2.0 和统一动作空间训练人类中心 VLA，并用 Mixture-of-Flow 分离共享运动原语与本体专家。 |
| [EgoScale: Scaling Dexterous Manipulation with Diverse Egocentric Human Data](https://arxiv.org/abs/2602.16710) | 2026-02 | arXiv | 在 20,854 小时动作标注第一视角人类视频上建立 scaling law，并以轻量 human-robot mid-training 迁移到 22-DoF 灵巧手。 |
| [Scalable Behavior Cloning with Open Data, Training, and Evaluation](https://arxiv.org/abs/2606.27375) | 2026-06 | arXiv | 发布 3,500 小时、130K episodes、195 任务的 ABC-130K，以及硬件、训练、仿真和真实评测全栈。 |
| [Human-as-Humanoid: Enabling Zero-Shot Humanoid Learning from Ego-Exo Human Videos with Human-Aligned Embodiments](https://arxiv.org/abs/2606.32009) | 2026-06 | arXiv | 通过 ego-exo 同步、60-DoF 动作重定向和 FK-aware supervision，把人类视频转成可直接训练 humanoid VLA 的动作标签。 |

### 同行评审锚点

| 工作 | Venue | arXiv |
|---|---|---|
| [HumanPlus: Humanoid Shadowing and Imitation from Humans](https://proceedings.mlr.press/v270/fu25a.html) | CoRL 2024 | [2406.10454](https://arxiv.org/abs/2406.10454) |
| [ConRFT: A Reinforced Fine-tuning Method for VLA Models via Consistency Policy](https://www.roboticsproceedings.org/rss21/p019.html) | RSS 2025 | [2502.05450](https://arxiv.org/abs/2502.05450) |
| [Robot Learning with Super-Linear Scaling](https://www.roboticsproceedings.org/rss21/p025.html) | RSS 2025 | [2412.01770](https://arxiv.org/abs/2412.01770) |
| [VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/He_VIRAL_Visual_Sim-to-Real_at_Scale_for_Humanoid_Loco-Manipulation_CVPR_2026_paper.html) | CVPR 2026 | [2511.15200](https://arxiv.org/abs/2511.15200) |

### 成熟度、瓶颈与战略判断

**成熟度。** 方法工具链最成熟，但跨本体、长时序和开放世界的同时成立仍少见。

**关键瓶颈。**

- 数据有效多样性
- 失败与修正数据
- 动作空间标准
- 在线学习安全
- 统一评测

**战略判断。** 长期价值更可能来自可持续数据飞轮、跨本体接口和开放训练基础设施，而不是单一 policy 名称。

<!-- 更新标记：通用机器人学习 最后更新 2026.07 -->

---


## 同行评审锚点

> 只接受官方 proceedings、OpenReview 最终录用状态或期刊正式页面。30 条官方链接已在 2026-07-29 批量复检。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>30</strong><span>官方评审记录</span></div>
  <div class="radar-kpi"><strong>5</strong><span>Venue / 年份组合</span></div>
  <div class="radar-kpi"><strong>11</strong><span>可归入主分析月</span></div>
  <div class="radar-kpi"><strong>19</strong><span>历史路线锚点</span></div>
</div>

### 如何理解“锚点”

- 首次公开时间仍由 arXiv v1 决定，会议发表月不回写为技术出现月。
- 主分析期之前的正式工作用于证明路线基础，不进入过去 12 个月论文数量。
- 作者自述 accepted/to appear 不作为证据。
- 较新月份覆盖率低主要由评审滞后造成，不能直接解释为质量差。

### 官方证据表

| 工作 | arXiv | Venue | 主方向 | 机构（最多三家） |
|---|---|---|---|---|
| [OpenVLA: An Open-Source Vision-Language-Action Model](https://proceedings.mlr.press/v270/kim25c.html) | [2406.09246](https://arxiv.org/abs/2406.09246) | CoRL 2024 | 具身基础模型 | Stanford University、UC Berkeley、Toyota Research Institute |
| [Robotic Control via Embodied Chain-of-Thought Reasoning](https://proceedings.mlr.press/v270/zawalski25a.html) | [2407.08693](https://arxiv.org/abs/2407.08693) | CoRL 2024 | 大小脑与双系统 | UC Berkeley、Stanford University、University of Warsaw |
| [ReKep: Spatio-Temporal Reasoning of Relational Keypoint Constraints for Robotic Manipulation](https://proceedings.mlr.press/v270/huang25g.html) | [2409.01652](https://arxiv.org/abs/2409.01652) | CoRL 2024 | 大小脑与双系统 | Stanford University、Columbia University |
| [HumanPlus: Humanoid Shadowing and Imitation from Humans](https://proceedings.mlr.press/v270/fu25a.html) | [2406.10454](https://arxiv.org/abs/2406.10454) | CoRL 2024 | 通用机器人学习 | Stanford University |
| [OmniH2O: Universal and Dexterous Human-to-Humanoid Whole-Body Teleoperation and Learning](https://proceedings.mlr.press/v270/he25b.html) | [2406.08858](https://arxiv.org/abs/2406.08858) | CoRL 2024 | 灵巧操作 | Carnegie Mellon University、Shanghai Jiao Tong University |
| [Scaling Proprioceptive-Visual Learning with Heterogeneous Pre-trained Transformers](https://papers.nips.cc/paper_files/paper/2024/hash/e0f393e7980a24fd12fa6f15adfa25fb-Abstract-Conference.html) | [2409.20537](https://arxiv.org/abs/2409.20537) | NeurIPS 2024 | 具身基础模型 | MIT CSAIL、Meta FAIR |
| [π₀: A Vision-Language-Action Flow Model for General Robot Control](https://www.roboticsproceedings.org/rss21/p010.html) | [2410.24164](https://arxiv.org/abs/2410.24164) | RSS 2025 | 具身基础模型 | Physical Intelligence |
| [SpatialVLA: Exploring Spatial Representations for Visual-Language-Action Models](https://www.roboticsproceedings.org/rss21/p011.html) | [2501.15830](https://arxiv.org/abs/2501.15830) | RSS 2025 | 具身基础模型 | Shanghai AI Laboratory、Fudan University、Shanghai Jiao Tong University |
| [FAST: Efficient Action Tokenization for Vision-Language-Action Models](https://www.roboticsproceedings.org/rss21/p012.html) | [2501.09747](https://arxiv.org/abs/2501.09747) | RSS 2025 | 具身基础模型 | Physical Intelligence、UC Berkeley、Stanford University |
| [Learning to Act Anywhere with Task-centric Latent Actions](https://www.roboticsproceedings.org/rss21/p014.html) | [2505.06111](https://arxiv.org/abs/2505.06111) | RSS 2025 | 具身基础模型 | The University of Hong Kong、OpenDriveLab、AgiBot |
| [Unified World Models: Coupling Video and Action Diffusion for Pretraining on Large Robotic Datasets](https://www.roboticsproceedings.org/rss21/p015.html) | [2504.02792](https://arxiv.org/abs/2504.02792) | RSS 2025 | 世界模型 | University of Washington、Toyota Research Institute |
| [ConRFT: A Reinforced Fine-tuning Method for VLA Models via Consistency Policy](https://www.roboticsproceedings.org/rss21/p019.html) | [2502.05450](https://arxiv.org/abs/2502.05450) | RSS 2025 | 通用机器人学习 | Institute of Automation, Chinese Academy of Sciences、University of Chinese Academy of Sciences |
| [Robot Learning with Super-Linear Scaling](https://www.roboticsproceedings.org/rss21/p025.html) | [2412.01770](https://arxiv.org/abs/2412.01770) | RSS 2025 | 通用机器人学习 | MIT、University of Washington、Stanford University |
| [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html) | [2503.02881](https://arxiv.org/abs/2503.02881) | RSS 2025 | 灵巧操作 | Shanghai Jiao Tong University、Tsinghua University、Shanghai Qizhi Institute |
| [π₀.₅: A Vision-Language-Action Model with Open-World Generalization](https://proceedings.mlr.press/v305/black25a.html) | [2504.16054](https://arxiv.org/abs/2504.16054) | CoRL 2025 | 具身基础模型 | Physical Intelligence、UC Berkeley、Stanford University |
| [Reflective Planning: Vision-Language Models for Multi-Stage Long-Horizon Robotic Manipulation](https://proceedings.mlr.press/v305/feng25b.html) | [2502.16707](https://arxiv.org/abs/2502.16707) | CoRL 2025 | 大小脑与双系统 | Cornell University、The Chinese University of Hong Kong、Yale University |
| [LaDi-WM: A Latent Diffusion-Based World Model for Predictive Manipulation](https://proceedings.mlr.press/v305/huang25a.html) | [2505.11528](https://arxiv.org/abs/2505.11528) | CoRL 2025 | 世界模型 | National University of Defense Technology、Peking University、Shenzhen University |
| [DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://proceedings.mlr.press/v305/xu25b.html) | [2505.21864](https://arxiv.org/abs/2505.21864) | CoRL 2025 | 灵巧操作 | Stanford University、Columbia University、J.P. Morgan AI Research |
| [Long-VLA: Unleashing Long-Horizon Capability of Vision Language Action Model for Robot Manipulation](https://proceedings.mlr.press/v305/fan25a.html) | [2508.19958](https://arxiv.org/abs/2508.19958) | CoRL 2025 | 具身基础模型 | Westlake University、Zhejiang University、Xi'an Jiaotong University |
| [ParticleFormer: A 3D Point Cloud World Model for Multi-Object, Multi-Material Robotic Manipulation](https://proceedings.mlr.press/v305/huang25c.html) | [2506.23126](https://arxiv.org/abs/2506.23126) | CoRL 2025 | 世界模型 | Stanford University、The RAI Institute |
| [ActiveVLA: Injecting Active Perception into Vision-Language-Action Models for Precise 3D Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_ActiveVLA_Injecting_Active_Perception_into_Vision-Language-Action_Models_for_Precise_3D_CVPR_2026_paper.html) | [2601.08325](https://arxiv.org/abs/2601.08325) | CVPR 2026 | 具身基础模型 | Fudan University、Shanghai Innovation Institute、Nanyang Technological University |
| [ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Zhong_ACoT-VLA_Action_Chain-of-Thought_for_Vision-Language-Action_Models_CVPR_2026_paper.html) | [2601.11404](https://arxiv.org/abs/2601.11404) | CVPR 2026 | 大小脑与双系统 | Beihang University、AgiBot |
| [Action-Sketcher: From Reasoning to Action via Visual Sketches for Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Tan_Action-Sketcher_From_Reasoning_to_Action_via_Visual_Sketches_for_Robotic_CVPR_2026_paper.html) | [2601.01618](https://arxiv.org/abs/2601.01618) | CVPR 2026 | 大小脑与双系统 | Peking University、Beijing Academy of Artificial Intelligence、University of Sydney |
| [Motus: A Unified Latent Action World Model](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html) | [2512.13030](https://arxiv.org/abs/2512.13030) | CVPR 2026 | 世界模型 | Tsinghua University、ShengShu、Peking University |
| [AtomicVLA: Unlocking the Potential of Atomic Skill Learning in Robots](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_AtomicVLA_Unlocking_the_Potential_of_Atomic_Skill_Learning_in_Robots_CVPR_2026_paper.html) | [2603.07648](https://arxiv.org/abs/2603.07648) | CVPR 2026 | 大小脑与双系统 | Sun Yat-sen University、Peng Cheng Laboratory、Yinwang Intelligent Technology |
| [UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html) | [2603.22264](https://arxiv.org/abs/2603.22264) | CVPR 2026 | 灵巧操作 | Tsinghua University、Shanghai Qizhi Institute、Sun Yat-sen University |
| [Cross-Hand Latent Representation for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Jiang_Cross-Hand_Latent_Representation_for_Vision-Language-Action_Models_CVPR_2026_paper.html) | [2603.10158](https://arxiv.org/abs/2603.10158) | CVPR 2026 | 灵巧操作 | UC San Diego、Amazon FAR、UC Berkeley |
| [VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/He_VIRAL_Visual_Sim-to-Real_at_Scale_for_Humanoid_Loco-Manipulation_CVPR_2026_paper.html) | [2511.15200](https://arxiv.org/abs/2511.15200) | CVPR 2026 | 通用机器人学习 | NVIDIA、Carnegie Mellon University、UC Berkeley |
| [PointWorld: Scaling 3D World Models for In-The-Wild Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Huang_PointWorld_Scaling_3D_World_Models_for_In-The-Wild_Robotic_Manipulation_CVPR_2026_paper.html) | [2601.03782](https://arxiv.org/abs/2601.03782) | CVPR 2026 | 世界模型 | Stanford University、NVIDIA |
| [SIMPACT: Simulation-Enabled Action Planning using Vision-Language Models](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_SIMPACT_Simulation-Enabled_Action_Planning_using_Vision-Language_Models_CVPR_2026_paper.html) | [2512.05955](https://arxiv.org/abs/2512.05955) | CVPR 2026 | 大小脑与双系统 | University of Maryland、University of Illinois Urbana-Champaign、Harvard University |

<!-- 更新标记：同行评审锚点 最后更新 2026.07 -->

---


## 团队与机构雷达

> 全球统一口径。排名先看官方同行评审工作覆盖，再看经核验的精读论文数；多机构合著会同时计入各机构，因此本页不能与论文总数直接相加。

| 排名 | 机构 | 相关工作 | 官方评审工作 | 方向布局 | 代表工作 |
|---:|---|---:|---:|---|---|
| 1 | Stanford University | 10 | 4 | 具身基础模型、大小脑与双系统、通用机器人学习、灵巧操作、世界模型 | [OpenVLA: An Open-Source Vision-Language-Action Model](https://proceedings.mlr.press/v270/kim25c.html)；[Robotic Control via Embodied Chain-of-Thought Reasoning](https://proceedings.mlr.press/v270/zawalski25a.html)；[ReKep: Spatio-Temporal Reasoning of Relational Keypoint Constraints for Robotic Manipulation](https://proceedings.mlr.press/v270/huang25g.html) |
| 2 | UC Berkeley | 7 | 4 | 具身基础模型、大小脑与双系统、灵巧操作、通用机器人学习 | [OpenVLA: An Open-Source Vision-Language-Action Model](https://proceedings.mlr.press/v270/kim25c.html)；[Robotic Control via Embodied Chain-of-Thought Reasoning](https://proceedings.mlr.press/v270/zawalski25a.html)；[FAST: Efficient Action Tokenization for Vision-Language-Action Models](https://www.roboticsproceedings.org/rss21/p012.html) |
| 3 | Physical Intelligence | 5 | 3 | 具身基础模型 | [OpenVLA: An Open-Source Vision-Language-Action Model](https://proceedings.mlr.press/v270/kim25c.html)；[π₀: A Vision-Language-Action Flow Model for General Robot Control](https://www.roboticsproceedings.org/rss21/p010.html)；[FAST: Efficient Action Tokenization for Vision-Language-Action Models](https://www.roboticsproceedings.org/rss21/p012.html) |
| 4 | Carnegie Mellon University | 3 | 3 | 灵巧操作、通用机器人学习 | [OmniH2O: Universal and Dexterous Human-to-Humanoid Whole-Body Teleoperation and Learning](https://proceedings.mlr.press/v270/he25b.html)；[DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://proceedings.mlr.press/v305/xu25b.html)；[VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/He_VIRAL_Visual_Sim-to-Real_at_Scale_for_Humanoid_Loco-Manipulation_CVPR_2026_paper.html) |
| 5 | Shanghai Jiao Tong University | 4 | 2 | 灵巧操作、具身基础模型 | [OmniH2O: Universal and Dexterous Human-to-Humanoid Whole-Body Teleoperation and Learning](https://proceedings.mlr.press/v270/he25b.html)；[SpatialVLA: Exploring Spatial Representations for Visual-Language-Action Models](https://www.roboticsproceedings.org/rss21/p011.html)；[Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html) |
| 6 | Tsinghua University | 4 | 2 | 灵巧操作、世界模型、通用机器人学习 | [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html)；[Motus: A Unified Latent Action World Model](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html)；[UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html) |
| 7 | Fudan University | 3 | 2 | 具身基础模型、大小脑与双系统 | [SpatialVLA: Exploring Spatial Representations for Visual-Language-Action Models](https://www.roboticsproceedings.org/rss21/p011.html)；[ActiveVLA: Injecting Active Perception into Vision-Language-Action Models for Precise 3D Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_ActiveVLA_Injecting_Active_Perception_into_Vision-Language-Action_Models_for_Precise_3D_CVPR_2026_paper.html)；[TriVLA: A Triple-System-Based Unified Vision-Language-Action Model with Episodic World Modeling for General Robot Control](https://arxiv.org/abs/2507.01424) |
| 8 | NVIDIA | 3 | 2 | 灵巧操作、通用机器人学习、世界模型 | [DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://proceedings.mlr.press/v305/xu25b.html)；[VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/He_VIRAL_Visual_Sim-to-Real_at_Scale_for_Humanoid_Loco-Manipulation_CVPR_2026_paper.html)；[PointWorld: Scaling 3D World Models for In-The-Wild Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Huang_PointWorld_Scaling_3D_World_Models_for_In-The-Wild_Robotic_Manipulation_CVPR_2026_paper.html) |
| 9 | Peking University | 3 | 2 | 世界模型、大小脑与双系统 | [LaDi-WM: A Latent Diffusion-Based World Model for Predictive Manipulation](https://proceedings.mlr.press/v305/huang25a.html)；[Action-Sketcher: From Reasoning to Action via Visual Sketches for Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Tan_Action-Sketcher_From_Reasoning_to_Action_via_Visual_Sketches_for_Robotic_CVPR_2026_paper.html)；[Motus: A Unified Latent Action World Model](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html) |
| 10 | Shanghai Innovation Institute | 3 | 2 | 灵巧操作、具身基础模型、大小脑与双系统 | [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html)；[ActiveVLA: Injecting Active Perception into Vision-Language-Action Models for Precise 3D Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_ActiveVLA_Injecting_Active_Perception_into_Vision-Language-Action_Models_for_Precise_3D_CVPR_2026_paper.html)；[TriVLA: A Triple-System-Based Unified Vision-Language-Action Model with Episodic World Modeling for General Robot Control](https://arxiv.org/abs/2507.01424) |
| 11 | AgiBot | 2 | 2 | 具身基础模型、大小脑与双系统 | [Learning to Act Anywhere with Task-centric Latent Actions](https://www.roboticsproceedings.org/rss21/p014.html)；[ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Zhong_ACoT-VLA_Action_Chain-of-Thought_for_Vision-Language-Action_Models_CVPR_2026_paper.html)；[ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://arxiv.org/abs/2601.11404) |
| 12 | Beihang University | 2 | 2 | 具身基础模型、大小脑与双系统 | [Long-VLA: Unleashing Long-Horizon Capability of Vision Language Action Model for Robot Manipulation](https://proceedings.mlr.press/v305/fan25a.html)；[ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Zhong_ACoT-VLA_Action_Chain-of-Thought_for_Vision-Language-Action_Models_CVPR_2026_paper.html)；[ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://arxiv.org/abs/2601.11404) |
| 13 | Columbia University | 2 | 2 | 大小脑与双系统、灵巧操作 | [ReKep: Spatio-Temporal Reasoning of Relational Keypoint Constraints for Robotic Manipulation](https://proceedings.mlr.press/v270/huang25g.html)；[DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://proceedings.mlr.press/v305/xu25b.html) |
| 14 | Institute of Automation, Chinese Academy of Sciences | 2 | 2 | 通用机器人学习、大小脑与双系统 | [ConRFT: A Reinforced Fine-tuning Method for VLA Models via Consistency Policy](https://www.roboticsproceedings.org/rss21/p019.html)；[Action-Sketcher: From Reasoning to Action via Visual Sketches for Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Tan_Action-Sketcher_From_Reasoning_to_Action_via_Visual_Sketches_for_Robotic_CVPR_2026_paper.html) |
| 15 | MIT | 2 | 2 | 具身基础模型、通用机器人学习 | [OpenVLA: An Open-Source Vision-Language-Action Model](https://proceedings.mlr.press/v270/kim25c.html)；[Robot Learning with Super-Linear Scaling](https://www.roboticsproceedings.org/rss21/p025.html) |
| 16 | Shanghai Qizhi Institute | 2 | 2 | 灵巧操作 | [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html)；[UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html)；[UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://arxiv.org/abs/2603.22264) |
| 17 | The Chinese University of Hong Kong | 2 | 2 | 大小脑与双系统、通用机器人学习 | [Reflective Planning: Vision-Language Models for Multi-Stage Long-Horizon Robotic Manipulation](https://proceedings.mlr.press/v305/feng25b.html)；[VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/He_VIRAL_Visual_Sim-to-Real_at_Scale_for_Humanoid_Loco-Manipulation_CVPR_2026_paper.html) |
| 18 | Toyota Research Institute | 2 | 2 | 具身基础模型、世界模型 | [OpenVLA: An Open-Source Vision-Language-Action Model](https://proceedings.mlr.press/v270/kim25c.html)；[Unified World Models: Coupling Video and Action Diffusion for Pretraining on Large Robotic Datasets](https://www.roboticsproceedings.org/rss21/p015.html) |
| 19 | Zhejiang University | 2 | 2 | 具身基础模型 | [SpatialVLA: Exploring Spatial Representations for Visual-Language-Action Models](https://www.roboticsproceedings.org/rss21/p011.html)；[Long-VLA: Unleashing Long-Horizon Capability of Vision Language Action Model for Robot Manipulation](https://proceedings.mlr.press/v305/fan25a.html) |
| 20 | Amazon FAR | 2 | 1 | 灵巧操作、大小脑与双系统 | [Cross-Hand Latent Representation for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Jiang_Cross-Hand_Latent_Representation_for_Vision-Language-Action_Models_CVPR_2026_paper.html)；[SIMPACT: Simulation-Enabled Action Planning using Vision-Language Models](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_SIMPACT_Simulation-Enabled_Action_Planning_using_Vision-Language_Models_CVPR_2026_paper.html) |
| 21 | Cornell University | 2 | 1 | 大小脑与双系统、通用机器人学习 | [Reflective Planning: Vision-Language Models for Multi-Stage Long-Horizon Robotic Manipulation](https://proceedings.mlr.press/v305/feng25b.html)；[X-Diffusion: Training Diffusion Policies on Cross-Embodiment Human Demonstrations](https://arxiv.org/abs/2511.04671) |
| 22 | Horizon Robotics | 2 | 1 | 世界模型、通用机器人学习 | [Motus: A Unified Latent Action World Model](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html)；[H-RDT: Human Manipulation Enhanced Bimanual Robotic Manipulation](https://arxiv.org/abs/2507.23523)；[Motus: A Unified Latent Action World Model](https://arxiv.org/abs/2512.13030) |
| 23 | Shanghai AI Laboratory | 2 | 1 | 具身基础模型、灵巧操作 | [SpatialVLA: Exploring Spatial Representations for Visual-Language-Action Models](https://www.roboticsproceedings.org/rss21/p011.html)；[Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html) |
| 24 | Sun Yat-sen University | 2 | 1 | 大小脑与双系统、灵巧操作 | [AtomicVLA: Unlocking the Potential of Atomic Skill Learning in Robots](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_AtomicVLA_Unlocking_the_Potential_of_Atomic_Skill_Learning_in_Robots_CVPR_2026_paper.html)；[UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html)；[UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://arxiv.org/abs/2603.22264) |
| 25 | University of Washington | 2 | 1 | 世界模型、通用机器人学习 | [Unified World Models: Coupling Video and Action Diffusion for Pretraining on Large Robotic Datasets](https://www.roboticsproceedings.org/rss21/p015.html)；[Robot Learning with Super-Linear Scaling](https://www.roboticsproceedings.org/rss21/p025.html) |
| 26 | Beijing Academy of Artificial Intelligence | 1 | 1 | 大小脑与双系统 | [Action-Sketcher: From Reasoning to Action via Visual Sketches for Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Tan_Action-Sketcher_From_Reasoning_to_Action_via_Visual_Sketches_for_Robotic_CVPR_2026_paper.html) |
| 27 | Google DeepMind | 1 | 1 | 具身基础模型 | [OpenVLA: An Open-Source Vision-Language-Action Model](https://proceedings.mlr.press/v270/kim25c.html) |
| 28 | Harvard University | 1 | 1 | 大小脑与双系统 | [SIMPACT: Simulation-Enabled Action Planning using Vision-Language Models](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_SIMPACT_Simulation-Enabled_Action_Planning_using_Vision-Language_Models_CVPR_2026_paper.html) |
| 29 | J.P. Morgan AI Research | 1 | 1 | 灵巧操作 | [DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://proceedings.mlr.press/v305/xu25b.html) |
| 30 | Meta FAIR | 1 | 1 | 具身基础模型 | [Scaling Proprioceptive-Visual Learning with Heterogeneous Pre-trained Transformers](https://papers.nips.cc/paper_files/paper/2024/hash/e0f393e7980a24fd12fa6f15adfa25fb-Abstract-Conference.html) |
| 31 | MIT CSAIL | 1 | 1 | 具身基础模型 | [Scaling Proprioceptive-Visual Learning with Heterogeneous Pre-trained Transformers](https://papers.nips.cc/paper_files/paper/2024/hash/e0f393e7980a24fd12fa6f15adfa25fb-Abstract-Conference.html) |
| 32 | Nanyang Technological University | 1 | 1 | 具身基础模型 | [ActiveVLA: Injecting Active Perception into Vision-Language-Action Models for Precise 3D Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_ActiveVLA_Injecting_Active_Perception_into_Vision-Language-Action_Models_for_Precise_3D_CVPR_2026_paper.html) |
| 33 | National University of Defense Technology | 1 | 1 | 世界模型 | [LaDi-WM: A Latent Diffusion-Based World Model for Predictive Manipulation](https://proceedings.mlr.press/v305/huang25a.html) |
| 34 | Northwestern Polytechnical University | 1 | 1 | 具身基础模型 | [SpatialVLA: Exploring Spatial Representations for Visual-Language-Action Models](https://www.roboticsproceedings.org/rss21/p011.html) |
| 35 | OpenDriveLab | 1 | 1 | 具身基础模型 | [Learning to Act Anywhere with Task-centric Latent Actions](https://www.roboticsproceedings.org/rss21/p014.html) |
| 36 | Peng Cheng Laboratory | 1 | 1 | 大小脑与双系统 | [AtomicVLA: Unlocking the Potential of Atomic Skill Learning in Robots](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_AtomicVLA_Unlocking_the_Potential_of_Atomic_Skill_Learning_in_Robots_CVPR_2026_paper.html) |
| 37 | ShanghaiTech University | 1 | 1 | 具身基础模型 | [SpatialVLA: Exploring Spatial Representations for Visual-Language-Action Models](https://www.roboticsproceedings.org/rss21/p011.html) |
| 38 | ShengShu | 1 | 1 | 世界模型 | [Motus: A Unified Latent Action World Model](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html)；[Motus: A Unified Latent Action World Model](https://arxiv.org/abs/2512.13030) |
| 39 | Shenzhen University | 1 | 1 | 世界模型 | [LaDi-WM: A Latent Diffusion-Based World Model for Predictive Manipulation](https://proceedings.mlr.press/v305/huang25a.html) |
| 40 | The RAI Institute | 1 | 1 | 世界模型 | [ParticleFormer: A 3D Point Cloud World Model for Multi-Object, Multi-Material Robotic Manipulation](https://proceedings.mlr.press/v305/huang25c.html) |
| 41 | The University of Hong Kong | 1 | 1 | 具身基础模型 | [Learning to Act Anywhere with Task-centric Latent Actions](https://www.roboticsproceedings.org/rss21/p014.html) |
| 42 | UC San Diego | 1 | 1 | 灵巧操作 | [Cross-Hand Latent Representation for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Jiang_Cross-Hand_Latent_Representation_for_Vision-Language-Action_Models_CVPR_2026_paper.html) |
| 43 | University of Chinese Academy of Sciences | 1 | 1 | 通用机器人学习 | [ConRFT: A Reinforced Fine-tuning Method for VLA Models via Consistency Policy](https://www.roboticsproceedings.org/rss21/p019.html) |
| 44 | University of Electronic Science and Technology of China | 1 | 1 | 具身基础模型 | [Long-VLA: Unleashing Long-Horizon Capability of Vision Language Action Model for Robot Manipulation](https://proceedings.mlr.press/v305/fan25a.html) |
| 45 | University of Illinois Urbana-Champaign | 1 | 1 | 大小脑与双系统 | [SIMPACT: Simulation-Enabled Action Planning using Vision-Language Models](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_SIMPACT_Simulation-Enabled_Action_Planning_using_Vision-Language_Models_CVPR_2026_paper.html) |
| 46 | University of Maryland | 1 | 1 | 大小脑与双系统 | [SIMPACT: Simulation-Enabled Action Planning using Vision-Language Models](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_SIMPACT_Simulation-Enabled_Action_Planning_using_Vision-Language_Models_CVPR_2026_paper.html) |
| 47 | University of North Carolina at Chapel Hill | 1 | 1 | 灵巧操作 | [UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html)；[UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://arxiv.org/abs/2603.22264) |
| 48 | University of Pennsylvania | 1 | 1 | 大小脑与双系统 | [SIMPACT: Simulation-Enabled Action Planning using Vision-Language Models](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_SIMPACT_Simulation-Enabled_Action_Planning_using_Vision-Language_Models_CVPR_2026_paper.html) |
| 49 | University of Sydney | 1 | 1 | 大小脑与双系统 | [Action-Sketcher: From Reasoning to Action via Visual Sketches for Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Tan_Action-Sketcher_From_Reasoning_to_Action_via_Visual_Sketches_for_Robotic_CVPR_2026_paper.html) |
| 50 | University of Warsaw | 1 | 1 | 大小脑与双系统 | [Robotic Control via Embodied Chain-of-Thought Reasoning](https://proceedings.mlr.press/v270/zawalski25a.html) |
| 51 | Westlake University | 1 | 1 | 具身基础模型 | [Long-VLA: Unleashing Long-Horizon Capability of Vision Language Action Model for Robot Manipulation](https://proceedings.mlr.press/v305/fan25a.html) |
| 52 | Xi'an Jiaotong University | 1 | 1 | 具身基础模型 | [Long-VLA: Unleashing Long-Horizon Capability of Vision Language Action Model for Robot Manipulation](https://proceedings.mlr.press/v305/fan25a.html) |
| 53 | Yale University | 1 | 1 | 大小脑与双系统 | [Reflective Planning: Vision-Language Models for Multi-Stage Long-Horizon Robotic Manipulation](https://proceedings.mlr.press/v305/feng25b.html) |
| 54 | Yinwang Intelligent Technology | 1 | 1 | 大小脑与双系统 | [AtomicVLA: Unlocking the Potential of Atomic Skill Learning in Robots](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_AtomicVLA_Unlocking_the_Potential_of_Atomic_Skill_Learning_in_Robots_CVPR_2026_paper.html) |
| 55 | ByteDance Seed | 1 | 0 | 具身基础模型 | [GR-3 Technical Report](https://arxiv.org/abs/2507.15493) |
| 56 | EvoMind Tech | 1 | 0 | 具身基础模型 | [Evo-0: Vision-Language-Action Model with Implicit Spatial Understanding](https://arxiv.org/abs/2507.00416) |
| 57 | IAAR-Shanghai | 1 | 0 | 具身基础模型 | [Evo-0: Vision-Language-Action Model with Implicit Spatial Understanding](https://arxiv.org/abs/2507.00416) |
| 58 | Microsoft Research | 1 | 0 | 通用机器人学习 | [Scalable Vision-Language-Action Model Pretraining for Robotic Manipulation with Real-Life Human Activity Videos](https://arxiv.org/abs/2510.21571) |
| 59 | University of Cambridge | 1 | 0 | 具身基础模型 | [Evo-0: Vision-Language-Action Model with Implicit Spatial Understanding](https://arxiv.org/abs/2507.00416) |

### 读表原则

- 产量不是唯一质量指标；持续跨月、跨方向和独立评审证据更重要。
- arXiv 通常不含 affiliation，本页只使用官方 proceedings 和已核验作者/项目页。
- “团队”按论文作者组合与独立项目线判断，不将同一系列版本重复视为独立验证。

<!-- 更新标记：团队与机构雷达 最后更新 2026.07 -->

---


## 评估基准与证据门槛

> benchmark 的作用是让不同方法可比较，不是替代真实部署。本站尤其关注测试任务泄漏、控制频率、长时失败和跨本体可比性。

| Benchmark / 评测 | 主要覆盖 | 优点 | 不能证明什么 | 官方入口 |
|---|---|---|---|---|
| LIBERO | 语言条件、多任务、持续学习 | 任务组合清晰、VLA 使用广 | 真机动力学与开放世界 | [GitHub](https://github.com/Lifelong-Robot-Learning/LIBERO) |
| CALVIN | 长时语言条件桌面操作 | 支持多步序列 | 机器人/场景单一 | [GitHub](https://github.com/mees/calvin) |
| RLBench | 多任务仿真操作 | 任务数量大、接口成熟 | sim-to-real 与真实接触 | [GitHub](https://github.com/stepjam/RLBench) |
| ManiSkill | 高性能仿真与 manipulation | 并行仿真、可复现 | 人类环境长尾 | [官网](https://maniskill.ai/) |
| RoboCasa | 日常场景与大规模仿真 | 场景多样、数据生成 | 真实家庭鲁棒性 | [官网](https://robocasa.ai/) |
| LIBERO-PRO | VLA 记忆与公平性压力测试 | 检查训练泄漏与鲁棒性 | 真实硬件故障 | [arXiv](https://arxiv.org/abs/2510.03827) |
| ManipArena | 推理型 generalist manipulation 真机评测 | 更接近真实执行 | 仍受具体硬件和任务集限制 | [arXiv](https://arxiv.org/abs/2603.28545) |

### 建议的下一代评测矩阵

| 维度 | 最低报告项 | 为什么重要 |
|---|---|---|
| 执行 | 成功率、控制频率、端到端延迟 | 区分“能推理”与“能实时控制” |
| 长时 | 子任务完成曲线、失败位置、恢复率 | 避免平均成功率掩盖级联失败 |
| 泛化 | 新任务、新场景、新物体、新本体分别报告 | “泛化”不是一个单一维度 |
| 世界模型 | 同算力控制收益、roll-out 漂移、model bias | 生成质量不等于规划价值 |
| 触觉/灵巧 | 跨传感器和跨手型迁移、接触失败恢复 | 防止硬件专用结果被误读为通用能力 |
| 开放性 | 代码、数据、权重、硬件配置与评测脚本 | 支持独立复现和后续采用 |

<!-- 更新标记：评估基准 最后更新 2026.07 -->

---


## 论文证据库

> 本表由 `data/papers.json` 自动生成。候选层用于趋势数量；“精读”表示 ID、标题、v1 日期和摘要已逐条复核，并补充贡献、局限和实验信号。

[下载 JSON](https://raw.githubusercontent.com/JoenHune/embodied-ai-radar/main/data/papers.json) · [下载 CSV](https://raw.githubusercontent.com/JoenHune/embodied-ai-radar/main/data/papers.csv) · [下载完整 Markdown 报告](https://raw.githubusercontent.com/JoenHune/embodied-ai-radar/main/embodied-ai-radar-report.md)

### 全量候选分表

- [2024 年候选](/database/2024)
- [2025 年候选](/database/2025)
- [2026 年候选](/database/2026)

JSON/CSV 包含全部 2640 条纳入统计记录；网页按年份拆分，避免单页过大。

### 精读与核验记录

| arXiv ID | 论文 | v1 月份 | 主方向 | 置信度 | 层级 | 同行评审 |
|---|---|---|---|---|---|---|
| 2507.00416 | [Evo-0: Vision-Language-Action Model with Implicit Spatial Understanding](https://arxiv.org/abs/2507.00416) | 2025-07 | 具身基础模型 | high | 精读 | — |
| 2507.01424 | [TriVLA: A Triple-System-Based Unified Vision-Language-Action Model with Episodic World Modeling for General Robot Control](https://arxiv.org/abs/2507.01424) | 2025-07 | 大小脑与双系统 | high | 精读 | — |
| 2507.05198 | [EmbodieDreamer: Advancing Real2Sim2Real Transfer for Policy Training via Embodied World Modeling](https://arxiv.org/abs/2507.05198) | 2025-07 | 世界模型 | high | 精读 | — |
| 2507.06224 | [EC-Flow: Enabling Versatile Robotic Manipulation from Action-Unlabeled Videos via Embodiment-Centric Flow](https://arxiv.org/abs/2507.06224) | 2025-07 | 通用机器人学习 | high | 精读 | — |
| 2507.09117 | [Towards Human-level Dexterity via Robot Learning](https://arxiv.org/abs/2507.09117) | 2025-07 | 灵巧操作 | high | 精读 | — |
| 2507.15493 | [GR-3 Technical Report](https://arxiv.org/abs/2507.15493) | 2025-07 | 具身基础模型 | high | 精读 | — |
| 2507.23523 | [H-RDT: Human Manipulation Enhanced Bimanual Robotic Manipulation](https://arxiv.org/abs/2507.23523) | 2025-07 | 通用机器人学习 | high | 精读 | — |
| 2508.00795 | [Video Generators are Robot Policies](https://arxiv.org/abs/2508.00795) | 2025-08 | 通用机器人学习 | high | 精读 | — |
| 2508.02062 | [RICL: Adding In-Context Adaptability to Pre-Trained Vision-Language-Action Models](https://arxiv.org/abs/2508.02062) | 2025-08 | 具身基础模型 | high | 精读 | — |
| 2508.03645 | [DiWA: Diffusion Policy Adaptation with World Models](https://arxiv.org/abs/2508.03645) | 2025-08 | 通用机器人学习 | high | 精读 | — |
| 2508.08706 | [OmniVTLA: Vision-Tactile-Language-Action Models with Semantic-Aligned Tactile Sensing](https://arxiv.org/abs/2508.08706) | 2025-08 | 灵巧操作 | high | 精读 | — |
| 2508.09976 | [Masquerade: Learning from In-the-wild Human Videos using Data-Editing](https://arxiv.org/abs/2508.09976) | 2025-08 | 通用机器人学习 | high | 精读 | — |
| 2508.17600 | [GWM: Towards Scalable Gaussian World Models for Robotic Manipulation](https://arxiv.org/abs/2508.17600) | 2025-08 | 世界模型 | high | 精读 | — |
| 2508.21112 | [EO-1: An Open Unified Embodied Foundation Model for General Robot Control](https://arxiv.org/abs/2508.21112) | 2025-08 | 具身基础模型 | high | 精读 | — |
| 2509.01819 | [ManiFlow: A General Robot Manipulation Policy via Consistency Flow Training](https://arxiv.org/abs/2509.01819) | 2025-09 | 通用机器人学习 | high | 精读 | — |
| 2509.05513 | [OpenEgo: A Large-Scale Multimodal Egocentric Dataset for Dexterous Manipulation](https://arxiv.org/abs/2509.05513) | 2025-09 | 通用机器人学习 | high | 精读 | — |
| 2509.07445 | [Text2Touch: Tactile In-Hand Manipulation with LLM-Designed Reward Functions](https://arxiv.org/abs/2509.07445) | 2025-09 | 灵巧操作 | high | 精读 | — |
| 2509.18428 | [Latent Action Pretraining Through World Modeling](https://arxiv.org/abs/2509.18428) | 2025-09 | 世界模型 | high | 精读 | — |
| 2509.20286 | [Parse-Augment-Distill: Learning Generalizable Bimanual Visuomotor Policies from Single Human Video](https://arxiv.org/abs/2509.20286) | 2025-09 | 通用机器人学习 | high | 精读 | — |
| 2509.22643 | [VLA-Reasoner: Empowering Vision-Language-Action Models with Reasoning via Online Monte Carlo Tree Search](https://arxiv.org/abs/2509.22643) | 2025-09 | 大小脑与双系统 | high | 精读 | — |
| 2509.24661 | [CEDex: Cross-Embodiment Dexterous Grasp Generation at Scale from Human-like Contact Representations](https://arxiv.org/abs/2509.24661) | 2025-09 | 灵巧操作 | high | 精读 | — |
| 2510.00406 | [VLA-RFT: Vision-Language-Action Reinforcement Fine-tuning with Verified Rewards in World Simulators](https://arxiv.org/abs/2510.00406) | 2025-10 | 世界模型 | high | 精读 | — |
| 2510.01623 | [VLA-R1: Enhancing Reasoning in Vision-Language-Action Models](https://arxiv.org/abs/2510.01623) | 2025-10 | 大小脑与双系统 | high | 精读 | — |
| 2510.08475 | [DexMan: Learning Bimanual Dexterous Manipulation from Human and Generated Videos](https://arxiv.org/abs/2510.08475) | 2025-10 | 灵巧操作 | high | 精读 | — |
| 2510.10125 | [Ctrl-World: A Controllable Generative World Model for Robot Manipulation](https://arxiv.org/abs/2510.10125) | 2025-10 | 世界模型 | high | 精读 | — |
| 2510.10274 | [X-VLA: Soft-Prompted Transformer as Scalable Cross-Embodiment Vision-Language-Action Model](https://arxiv.org/abs/2510.10274) | 2025-10 | 具身基础模型 | high | 精读 | — |
| 2510.18337 | [MoTVLA: A Vision-Language-Action Model with Unified Fast-Slow Reasoning](https://arxiv.org/abs/2510.18337) | 2025-10 | 大小脑与双系统 | high | 精读 | — |
| 2510.21571 | [Scalable Vision-Language-Action Model Pretraining for Robotic Manipulation with Real-Life Human Activity Videos](https://arxiv.org/abs/2510.21571) | 2025-10 | 通用机器人学习 | high | 精读 | — |
| 2511.01177 | [Scaling Cross-Embodiment World Models for Dexterous Manipulation](https://arxiv.org/abs/2511.01177) | 2025-11 | 世界模型 | high | 精读 | — |
| 2511.02504 | [Dexterous Robotic Piano Playing at Scale](https://arxiv.org/abs/2511.02504) | 2025-11 | 灵巧操作 | high | 精读 | — |
| 2511.03077 | [WorldPlanner: Monte Carlo Tree Search and MPC with Action-Conditioned Visual World Models](https://arxiv.org/abs/2511.03077) | 2025-11 | 世界模型 | high | 精读 | — |
| 2511.04671 | [X-Diffusion: Training Diffusion Policies on Cross-Embodiment Human Demonstrations](https://arxiv.org/abs/2511.04671) | 2025-11 | 通用机器人学习 | high | 精读 | — |
| 2511.14759 | [$π^{*}_{0.6}$: a VLA That Learns From Experience](https://arxiv.org/abs/2511.14759) | 2025-11 | 具身基础模型 | high | 精读 | — |
| 2511.16651 | [InternData-A1: Pioneering High-Fidelity Synthetic Data for Pre-training Generalist Policy](https://arxiv.org/abs/2511.16651) | 2025-11 | 通用机器人学习 | high | 精读 | — |
| 2511.22134 | [DualVLA: Building a Generalizable Embodied Agent via Partial Decoupling of Reasoning and Action](https://arxiv.org/abs/2511.22134) | 2025-11 | 大小脑与双系统 | high | 精读 | — |
| 2512.02729 | [RoboWheel: A Data Engine from Real-World Human Demonstrations for Cross-Embodiment Robotic Learning](https://arxiv.org/abs/2512.02729) | 2025-12 | 通用机器人学习 | high | 精读 | — |
| 2512.03044 | [Video2Act: A Dual-System Video Diffusion Policy with Robotic Spatio-Motional Modeling](https://arxiv.org/abs/2512.03044) | 2025-12 | 大小脑与双系统 | high | 精读 | — |
| 2512.08186 | [Ground Slow, Move Fast: A Dual-System Foundation Model for Generalizable Vision-and-Language Navigation](https://arxiv.org/abs/2512.08186) | 2025-12 | 大小脑与双系统 | high | 精读 | — |
| 2512.09297 | [One-Shot Real-World Demonstration Synthesis for Scalable Bimanual Manipulation](https://arxiv.org/abs/2512.09297) | 2025-12 | 灵巧操作 | high | 精读 | — |
| 2512.13030 | [Motus: A Unified Latent Action World Model](https://arxiv.org/abs/2512.13030) | 2025-12 | 世界模型 | high | 精读 | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html) |
| 2512.15840 | [Large Video Planner Enables Generalizable Robot Control](https://arxiv.org/abs/2512.15840) | 2025-12 | 世界模型 | high | 精读 | — |
| 2512.18477 | [STORM: Search-Guided Generative World Models for Robotic Manipulation](https://arxiv.org/abs/2512.18477) | 2025-12 | 世界模型 | high | 精读 | — |
| 2601.04629 | [UniBiDex: A Unified Teleoperation Framework for Robotic Bimanual Dexterous Manipulation](https://arxiv.org/abs/2601.04629) | 2026-01 | 灵巧操作 | high | 精读 | — |
| 2601.05230 | [Learning Latent Action World Models In The Wild](https://arxiv.org/abs/2601.05230) | 2026-01 | 世界模型 | high | 精读 | — |
| 2601.11404 | [ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://arxiv.org/abs/2601.11404) | 2026-01 | 大小脑与双系统 | high | 精读 | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhong_ACoT-VLA_Action_Chain-of-Thought_for_Vision-Language-Action_Models_CVPR_2026_paper.html) |
| 2601.12993 | [Being-H0.5: Scaling Human-Centric Robot Learning for Cross-Embodiment Generalization](https://arxiv.org/abs/2601.12993) | 2026-01 | 具身基础模型 | high | 精读 | — |
| 2601.14133 | [TwinBrainVLA: Unleashing the Potential of Generalist VLMs for Embodied Tasks via Asymmetric Mixture-of-Transformers](https://arxiv.org/abs/2601.14133) | 2026-01 | 大小脑与双系统 | high | 精读 | — |
| 2601.16163 | [Cosmos Policy: Fine-Tuning Video Models for Visuomotor Control and Planning](https://arxiv.org/abs/2601.16163) | 2026-01 | 世界模型 | high | 精读 | — |
| 2602.00919 | [Green-VLA: Staged Vision-Language-Action Model for Generalist Robots](https://arxiv.org/abs/2602.00919) | 2026-01 | 具身基础模型 | high | 精读 | — |
| 2602.12684 | [Xiaomi-Robotics-0: An Open-Sourced Vision-Language-Action Model with Real-Time Execution](https://arxiv.org/abs/2602.12684) | 2026-02 | 具身基础模型 | high | 精读 | — |
| 2602.13977 | [WoVR: World Models as Reliable Simulators for Post-Training VLA Policies with RL](https://arxiv.org/abs/2602.13977) | 2026-02 | 世界模型 | high | 精读 | — |
| 2602.16710 | [EgoScale: Scaling Dexterous Manipulation with Diverse Egocentric Human Data](https://arxiv.org/abs/2602.16710) | 2026-02 | 通用机器人学习 | high | 精读 | — |
| 2602.21633 | [Self-Correcting VLA: Online Action Refinement via Sparse World Imagination](https://arxiv.org/abs/2602.21633) | 2026-02 | 世界模型 | high | 精读 | — |
| 2602.21736 | [Joint-Aligned Latent Action: Towards Scalable VLA Pretraining in the Wild](https://arxiv.org/abs/2602.21736) | 2026-02 | 通用机器人学习 | high | 精读 | — |
| 2602.23648 | [FAVLA: A Force-Adaptive Fast-Slow VLA model for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2602.23648) | 2026-02 | 大小脑与双系统 | high | 精读 | — |
| 2602.23721 | [StemVLA:An Open-Source Vision-Language-Action Model with Future 3D Spatial Geometry Knowledge and 4D Historical Representation](https://arxiv.org/abs/2602.23721) | 2026-02 | 世界模型 | high | 精读 | — |
| 2603.16860 | [DreamPlan: Efficient Reinforcement Fine-Tuning of Vision-Language Planners via Video World Models](https://arxiv.org/abs/2603.16860) | 2026-03 | 大小脑与双系统 | high | 精读 | — |
| 2603.17808 | [EVA: Aligning Video World Models with Executable Robot Actions via Inverse Dynamics Rewards](https://arxiv.org/abs/2603.17808) | 2026-03 | 世界模型 | high | 精读 | — |
| 2603.19201 | [OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2603.19201) | 2026-03 | 世界模型 | high | 精读 | — |
| 2603.22263 | [DexDrummer: In-Hand, Contact-Rich, and Long-Horizon Dexterous Robot Drumming](https://arxiv.org/abs/2603.22263) | 2026-03 | 灵巧操作 | high | 精读 | — |
| 2603.22264 | [UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://arxiv.org/abs/2603.22264) | 2026-03 | 灵巧操作 | high | 精读 | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html) |
| 2603.28545 | [ManipArena: Comprehensive Real-world Evaluation of Reasoning-Oriented Generalist Robot Manipulation](https://arxiv.org/abs/2603.28545) | 2026-03 | 通用机器人学习 | high | 精读 | — |
| 2603.29844 | [DIAL: Decoupling Intent and Action via Latent World Modeling for End-to-End VLA](https://arxiv.org/abs/2603.29844) | 2026-03 | 大小脑与双系统 | high | 精读 | — |
| 2604.13015 | [Learning Versatile Humanoid Manipulation with Touch Dreaming](https://arxiv.org/abs/2604.13015) | 2026-04 | 灵巧操作 | high | 精读 | — |
| 2604.15483 | [$π_{0.7}$: a Steerable Generalist Robotic Foundation Model with Emergent Capabilities](https://arxiv.org/abs/2604.15483) | 2026-04 | 具身基础模型 | high | 精读 | — |
| 2604.20689 | [FingerEye: Learning Dexterous Manipulation with Continuous Vision-Tactile Sensing](https://arxiv.org/abs/2604.20689) | 2026-04 | 灵巧操作 | high | 精读 | — |
| 2604.21017 | [Open-H-Embodiment: A Large-Scale Dataset for Enabling Foundation Models in Medical Robotics](https://arxiv.org/abs/2604.21017) | 2026-04 | 具身基础模型 | high | 精读 | — |
| 2604.21924 | [Long-Horizon Manipulation via Trace-Conditioned VLA Planning](https://arxiv.org/abs/2604.21924) | 2026-04 | 大小脑与双系统 | high | 精读 | — |
| 2604.24921 | [Libra-VLA: Achieving Learning Equilibrium via Asynchronous Coarse-to-Fine Dual-System](https://arxiv.org/abs/2604.24921) | 2026-04 | 大小脑与双系统 | high | 精读 | — |
| 2604.26848 | [STARRY: Spatial-Temporal Action-Centric World Modeling for Robotic Manipulation](https://arxiv.org/abs/2604.26848) | 2026-04 | 世界模型 | high | 精读 | — |
| 2605.27817 | [Turning Video Models into Generalist Robot Policies](https://arxiv.org/abs/2605.27817) | 2026-05 | 世界模型 | high | 精读 | — |
| 2605.30226 | [BORA: Bridging Offline Reinforcement Learning and Online Residual Adaptation for Real-World Dexterous VLA Models](https://arxiv.org/abs/2605.30226) | 2026-05 | 灵巧操作 | high | 精读 | — |
| 2605.30280 | [Qwen-VLA: Unifying Vision-Language-Action Modeling across Tasks, Environments, and Robot Embodiments](https://arxiv.org/abs/2605.30280) | 2026-05 | 具身基础模型 | high | 精读 | — |
| 2605.31286 | [DeMaVLA: A Vision-Language-Action Foundation Model for Generalizable Deformable Manipulation](https://arxiv.org/abs/2605.31286) | 2026-05 | 具身基础模型 | high | 精读 | — |
| 2606.00229 | [Continuous Reasoning for Vision-Language-Action](https://arxiv.org/abs/2606.00229) | 2026-05 | 大小脑与双系统 | high | 精读 | — |
| 2606.01027 | [$τ_0$-WM: A Unified Video-Action World Model for Robotic Manipulation](https://arxiv.org/abs/2606.01027) | 2026-05 | 世界模型 | high | 精读 | — |
| 2606.01241 | [OneVLA: A Unified Framework for Embodied Tasks](https://arxiv.org/abs/2606.01241) | 2026-05 | 具身基础模型 | high | 精读 | — |
| 2606.27375 | [Scalable Behavior Cloning with Open Data, Training, and Evaluation](https://arxiv.org/abs/2606.27375) | 2026-06 | 通用机器人学习 | high | 精读 | — |
| 2606.30552 | [Training Vision-Language-Action Models with Dense Embodied Chain-of-Thought Supervision](https://arxiv.org/abs/2606.30552) | 2026-06 | 大小脑与双系统 | high | 精读 | — |
| 2606.31329 | [3D HAMSTER: Bridging Planning and Control in Hierarchical Vision Language Action Models through 3D Trajectory Guidance](https://arxiv.org/abs/2606.31329) | 2026-06 | 大小脑与双系统 | high | 精读 | — |
| 2606.31723 | [UniTacVLA: Unified Tactile Understanding and Prediction in Vision Language Action Models](https://arxiv.org/abs/2606.31723) | 2026-06 | 灵巧操作 | high | 精读 | — |
| 2606.31909 | [CoDex: Learning Compositional Dexterous Functional Manipulation without Demonstrations](https://arxiv.org/abs/2606.31909) | 2026-06 | 灵巧操作 | high | 精读 | — |
| 2606.32009 | [Human-as-Humanoid: Enabling Zero-Shot Humanoid Learning from Ego-Exo Human Videos with Human-Aligned Embodiments](https://arxiv.org/abs/2606.32009) | 2026-06 | 通用机器人学习 | high | 精读 | — |
| 2606.32028 | [DVG-WM: Disentangled Video Generation Enables Efficient Embodied World Model for Robotic Manipulation](https://arxiv.org/abs/2606.32028) | 2026-06 | 世界模型 | high | 精读 | — |
| 2607.15330 | [Xiaomi-Robotics-1: Scaling Vision-Language-Action Models with over 100K Hours of Real-World Trajectories](https://arxiv.org/abs/2607.15330) | 2026-07 | 具身基础模型 | high | 精读 | — |
| 2607.16636 | [PhyAgentOS: A Self-Evolving Operating System for Embodied Agents with Decoupled Cognitive Planning and Physical Execution](https://arxiv.org/abs/2607.16636) | 2026-07 | 大小脑与双系统 | high | 精读 | — |
| 2607.22530 | [ViTacWorld: Scaling Visuo-Tactile World Models for Contact-Rich Robot Manipulation](https://arxiv.org/abs/2607.22530) | 2026-07 | 世界模型 | high | 精读 | — |
| 2607.24485 | [τ: Learning Touch-Augmented Vision-Language-Action Models from Future Visual Supervision](https://arxiv.org/abs/2607.24485) | 2026-07 | 灵巧操作 | high | 精读 | — |
| 2607.24744 | [Data Pyramid for Embodied Manipulation](https://arxiv.org/abs/2607.24744) | 2026-07 | 通用机器人学习 | high | 精读 | — |
| 2607.25918 | [DC-WAM: Dynamic-Centric Visual Supervision and Reasoning for World-Action Models](https://arxiv.org/abs/2607.25918) | 2026-07 | 世界模型 | high | 精读 | — |

<!-- 更新标记：论文证据库 最后更新 2026.07 -->

---


## 检索、分类与趋势判定方法

> **版本**：v1.0 · **数据截点**：2026 年 7 月 29 日（Asia/Shanghai）<br>
> 本页描述的是可复算流程；任何依赖人工判断的步骤都会明确标注。

### 时间口径

| 层级 | 时间范围 | 用途 | 深度 |
|---|---|---|---|
| 主分析期 | 2025-07-01—2026-06-30 | 逐月趋势、重点论文、实验与开放性指标 | 精读 + 完整分类 |
| 前瞻快照 | 2026-07-01—2026-07-29 | 识别早期信号 | 不与完整月直接比较 |
| 同比基线 | 2024-07-01—2025-06-30 | 数量、主题、机构结构 | 轻量分类 |
| 同行评审窗口 | 2024-07-01—2026-07-29 | 处理提出、投稿、录用与发表之间的滞后 | 官方证据核验 |

月份统一由 [arXiv](https://arxiv.org/) 首次提交版本 `v1` 的日期确定。修订版本更新摘要、DOI 与发表信息，但不重复计数。会议发表月只表示评审完成，并不替代研究首次公开时间。

### 三阶段检索

```mermaid
flowchart LR
  A["宽召回<br/>cs.RO 为核心<br/>补 cs.AI/CV/LG<br/> "] --> B["语义边界筛选<br/>标题 + 摘要 + 方法语境<br/> "]
  B --> C["人工复核<br/>低置信度 / 跨方向 / 高影响<br/> "]
  C --> D["版本合并<br/>arXiv + proceedings + journal<br/> "]
  D --> E["结构化证据库<br/>CSV / JSON 单一来源<br/> "]
```

宽召回优先保证“不漏掉使用新命名的工作”。当前轻量统计语料以 [Semantic Scholar Academic Graph](https://www.semanticscholar.org/product/api) 检索并只保留带官方 arXiv external ID 的记录；90 篇高信号样本再通过 arXiv API 逐条核对 ID、标题、`published`（v1）与摘要。若 arXiv Atom 批量接口可用，仓库也保留以 `cs.RO` 为核心的全量采集脚本。分类关键词只负责生成候选和初步分数；是否纳入高信号论文、是否构成趋势，以及跨方向归类均需结合摘要和方法描述复核。

### 五类主方向

| 代码 | 主方向 | 纳入重点 | 关键边界 |
|---|---|---|---|
| D1 | 具身基础模型 | VLA、generalist policy、多任务预训练、语言条件策略 | 必须输出或学习机器人动作 |
| D2 | 大小脑与双系统 | planner–policy、fast–slow、VLM 与低层控制器协同 | 不要求作者使用“大小脑”名称 |
| D3 | 灵巧操作 | 灵巧手、双臂、触觉、臂手协同、接触密集操作 | 单一简单抓取通常归 D5 |
| D4 | 世界模型 | 动作条件预测、latent action、动力学模型、生成式仿真 | 必须服务动作、规划、控制或机器人数据生成 |
| D5 | 通用机器人学习 | 跨任务/本体、模仿与强化学习、diffusion/flow policy、数据规模化 | 不能仅是特定任务传统控制 |

一篇论文可以拥有多个 `topics`，但只有一个 `primary_topic`。全站的方向数量统计只按主方向计数，防止重复加总；跨方向分析使用多标签。

### 同行评审证据

只接受三类证据：

1. 会议官方 proceedings；
2. [OpenReview](https://openreview.net/) 页面中的最终录用状态；
3. 期刊出版方正式页面。

作者主页、项目页、arXiv comment 中的 “accepted” 或 “to appear” 可作为检索线索，但不能单独升级状态。预印本与正式版本通过 arXiv ID、DOI、标准化标题和作者组合合并。

### 量化指标

所有比例同时显示分子和分母。同比基线仅计算可由元数据稳定推导的指标，不与主分析期的精读标签混用。

| 指标 | 计算方式 | 注意 |
|---|---|---|
| 主题占比 | 某主方向论文数 / 当月纳入论文数 | 多标签不重复计数 |
| 环比 / 同比 | 与上月 / 上年同月绝对数量相比 | 7 月快照不计算环比 |
| 机构集中度 | 头部 5 家机构去重论文数 / 有机构信息论文数 | 多机构合著按每家计一篇 |
| 真实机器人验证率 | 明确报告物理机器人实验的论文数 / 主分析期论文数 | 摘要未披露时不做正向推断 |
| 多任务 / 跨本体 / 长时序 | 满足对应证据标签的论文数 / 主分析期论文数 | 任务变体不自动等于多任务 |
| 开放率 | 明确提供代码、数据或模型任一资产 / 主分析期论文数 | “will release” 不计为已开放 |
| 同行评审覆盖率 | 已有官方录用/正式发表证据的工作数 / 主分析期论文数 | 时间滞后会系统性压低近期月份 |

### 趋势等级

| 等级 | 定义 | 最低证据门槛 |
|---|---|---|
| A 已确认 | 方向已跨团队、跨月扩散，且有正式评审锚点 | 明显跨月或同比增长 + 至少两项独立同行评审工作 |
| B 新兴 | 相邻月份连续出现独立工作，评审证据仍弱 | 至少三项工作 + 至少两个独立机构 |
| C 早期信号 | 高新颖度但样本过少 | 一至两项高信号工作 |
| D 降温/未兑现 | 数量、实验增量或独立跟进不足 | 明确反证或连续缺口 |

分级不是对单篇论文质量打分，而是判断一个研究命题的“趋势证据强度”。

### 可复算性

- `config/taxonomy.json` 固化主题词、排除词、标签和 venue 清单。
- `data/papers.json` 是论文记录的唯一结构化来源。
- `data/trends.json` 记录人工趋势判断及其论文 ID。
- `scripts/generate-site.mjs` 生成月度统计、论文表、机构表和参考索引。
- `scripts/audit-data.mjs` 检查重复 ID、日期范围、趋势证据、官方评审链接与数字一致性。

生成页面不是数据源，不应手工修改其中的数量。修正应先进入结构化文件，再重新生成。

<!-- 更新标记：检索与分类方法 最后更新 2026.07 -->

---


## 纳入、排除与研究局限

### 纳入规则

候选必须同时满足：

- 研究对象位于机器人或具身交互边界内；
- 方法直接学习、生成、规划或执行动作，或为这些能力提供数据与动力学模型；
- 标题、摘要或正式方法说明能支持至少一个主方向；
- 首次公开时间落入分析、基线或前瞻窗口。

### 典型边界样本

| 情形 | 处置 | 原因 |
|---|---|---|
| VLM 为机器人生成任务计划，低层策略执行 | 纳入 D2 | 实际形成高层推理—低层控制分工 |
| 机器人视频模型只展示生成质量 | 排除 D4 | 未证明对动作、规划或控制有用 |
| 动作条件视频预测用于 MPC 或策略训练 | 纳入 D4 | 与交互决策有直接因果链 |
| 通用 diffusion policy 在多个机器人上训练 | 纳入 D5，可加 D1 标签 | 主贡献是策略学习与迁移 |
| 单任务 PID / MPC 性能改进 | 排除 | 不属于计划关心的可迁移学习能力 |
| 自动驾驶 world model | 默认排除 | 本期不覆盖纯自动驾驶 |
| 纯 SLAM / visual odometry | 排除 | 不直接学习具身动作能力 |
| 新灵巧手机械结构，无学习方法 | 仅在硬件生态提及 | 不计入论文趋势总量 |

### 置信度

- `high`：标题与摘要存在多个一致信号，边界清晰。
- `medium`：属于具身学习，但主方向需要方法级判断。
- `low`：仅由单个关键词命中或摘要信息不足；不作为趋势数量证据，除非人工复核升级。

### 已知局限

1. **arXiv 召回不是学术全集。** 部分工作先出现在会议 proceedings、机构技术报告或项目页；本库以 arXiv 为趋势时间轴，同行评审页只用于状态核验。
2. **摘要标签偏保守。** “真实机器人”“开源”“跨本体”等证据若只写在正文或补充材料中，自动标签可能出现假阴性。
3. **机构信息不完整。** arXiv 元数据本身通常不含 affiliation；机构统计仅使用 OpenAlex 归一化结果和人工核验记录，并显示有效分母。
4. **近期同行评审覆盖率天然偏低。** 这反映发表滞后，不能直接解释为研究质量下降。
5. **会议周期会造成提交堆积。** 月度页面对显著集中提交做备注，不把截稿周期自动解释为技术爆发。
6. **百分比受小样本影响。** 所有图表保留绝对数量，2026 年 7 月快照不参与完整月比较。
7. **一句话贡献与局限是研究判断。** 它们不是作者原文，站点将其与可核验事实分开表述。
8. **轻量统计是统一查询的候选指数。** 当前批量 arXiv Atom 接口触发限流后，宽召回改用 Semantic Scholar 的 arXiv external ID 索引；因此候选数量适合做同口径环比/同比，不应解释为 cs.RO 的完整论文总量。

### 不在本期范围

市场规模、公司融资、商业订单、供应链和公司级尽调不在本期范围。本报告只提供研究证据，可作为后续商业模块的技术底座。

<!-- 更新标记：纳排与局限 最后更新 2026.07 -->

---


## 审校报告

> **审校对象**：执行摘要、年度综合、弱信号与未来判断<br>
> **审校依据**：`data/papers.json`、`data/peer-review.json`、arXiv 核验记录、官方 proceedings<br>
> **审校范围**：事实准确性、专有名词、数据一致性、事实/推断分层

### 一、已直接修改的问题

| 位置 | 修改前 | 修改后 | 说明 |
|---|---|---|---|
| 执行摘要总论 | “具身智能正从……” | 增加“综合判断（推断）” | 防止把年度归纳写成已证实事实 |
| 数据指标 | “开放资产确认” | “明确开放披露” | 本库确认的是摘要/comment/项目页披露，不等于本地复现 |
| 7 月前瞻 | “100K 小时级真实轨迹” | “论文报告 100K 小时级真实轨迹” | 规模为论文自报，尚无独立审计 |
| Agent OS 预测 | “首次” | “在本次语料中首次” | 避免无边界的全球首创断言 |

### 二、无需改动的正确项

| 项目 | 核查结果 |
|---|---|
| 主分析期精读数 | 84 篇，与 12 个月 × 每月 7 篇一致 |
| 7 月前瞻精读数 | 6 篇，与结构化记录一致 |
| 官方同行评审锚点 | 30 条，唯一性与官方域名检查通过 |
| 真实机器人 / 多任务 / 跨本体 / 长时序 | 均由精读记录重新计算，分母统一为 84 |
| 趋势论文链接 | 所有 `evidence_ids` 均存在于论文库 |
| B 级趋势 | 均至少 3 篇、2 个独立第一作者团队 |

### 三、待确认的专有名词

无。论文标题和模型名保留 arXiv/官方 proceedings 原文；中英文主题名称在全站统一。

### 四、事实与数据核查

#### 4.1 已验证一致

- `data/papers.json`：3,082 条记录、2,640 条纳入统计、90 条精读。
- 主分析期候选 1,841 条；同比基线候选 633 条。
- 五方向主分析期合计 1,841 条，未因多标签重复计数。
- 30 个官方评审链接在采集阶段均返回 HTTP 200；站点构建的内部链接检查通过。

#### 4.2 可接受的研究判断

- “实时执行栈”“verifier/自纠错”“触觉预测通道”等属于未来判断，均集中放在预测页，并提供验证路标与反证条件。
- A/B/C/D 是趋势证据强度，不是对单篇论文质量或团队优劣的评分。

#### 4.3 时效性备注

- 数据截点为 2026-07-29。
- 2026 年 7 月是 1–29 日快照，不参与完整月比较。
- CVPR 2026 等新近论文已使用官方页面，但近期月份的同行评审覆盖率仍受发表滞后影响。

### 五、技术名词一致性

- `VLA`、`world model`、`fast–slow`、`verifier`、`latent action` 和 `embodiment adapter` 保留英文。
- “大小脑与双系统”用于中文分类；未要求原论文必须采用 System 1/System 2 命名。
- “真实机器人”只表示明确的物理机器人实验，不等于部署级成熟。

### 六、审校结论

未发现未处理的确认错误。关键数字可从结构化数据复算；预测性表述已与事实记录分开，并附可证伪条件。

<!-- 更新标记：内容审校报告 最后更新 2026.07 -->

---


## 参考文献

> 收录月度精读、趋势卡、未来判断与同行评审页实际引用的唯一工作；官方发表版本优先链接正式页面。

### 具身基础模型

1. Michał Zawalski, William Chen, Karl Pertsch, Oier Mees, Chelsea Finn, Sergey Levine. (2024). [Robotic Control via Embodied Chain-of-Thought Reasoning](https://proceedings.mlr.press/v270/zawalski25a.html). *CoRL 2024*.
2. Kevin Black, Noah Brown, Danny Driess, A. Esmail, Michael Equi, Chelsea Finn, Niccolo Fusai, Lachy Groom, et al.. (2024). [π0: A Vision-Language-Action Flow Model for General Robot Control](https://www.roboticsproceedings.org/rss21/p010.html). *RSS 2025*.
3. Karl Pertsch, Kyle Stachowicz, Brian Ichter, Danny Driess, Suraj Nair, Quan Vuong, Oier Mees, Chelsea Finn, et al.. (2025). [FAST: Efficient Action Tokenization for Vision-Language-Action Models](https://www.roboticsproceedings.org/rss21/p012.html). *RSS 2025*.
4. Delin Qu, Haoming Song, Qizhi Chen, Yuanqi Yao, Xinyi Ye, Yani Ding, Zhigang Wang, Jiayuan Gu, et al.. (2025). [SpatialVLA: Exploring Spatial Representations for Visual-Language-Action Model](https://www.roboticsproceedings.org/rss21/p011.html). *RSS 2025*.
5. Yuhui Chen, Shuai Tian, Shugao Liu, Yingting Zhou, Haoran Li, Dongbin Zhao. (2025). [ConRFT: A Reinforced Fine-tuning Method for VLA Models via Consistency Policy](https://www.roboticsproceedings.org/rss21/p019.html). *RSS 2025*.
6. Chuning Zhu, Raymond Yu, Siyuan Feng, B. Burchfiel, Paarth Shah, Abhishek Gupta. (2025). [Unified World Models: Coupling Video and Action Diffusion for Pretraining on Large Robotic Datasets](https://www.roboticsproceedings.org/rss21/p015.html). *RSS 2025*.
7. Physical Intelligence, Kevin Black, Noah Brown, James Darpinian, Karan Dhabalia, Danny Driess, A. Esmail, Michael Equi, et al.. (2025). [π0.5: a Vision-Language-Action Model with Open-World Generalization](https://proceedings.mlr.press/v305/black25a.html). *CoRL 2025*.
8. Qingwen Bu, Yanting Yang, Jisong Cai, Shenyuan Gao, Guanghui Ren, Maoqing Yao, Ping Luo, Hongyang Li. (2025). [UniVLA: Learning to Act Anywhere with Task-centric Latent Actions](https://www.roboticsproceedings.org/rss21/p014.html). *RSS 2025*.
9. Tao Lin, Gen Li, Yilei Zhong, Yanwen Zou, Yuxin Du, Jiting Liu, Encheng Gu, Bo Zhao. (2025). [Evo-0: Vision-Language-Action Model with Implicit Spatial Understanding](https://arxiv.org/abs/2507.00416). arXiv:2507.00416.
10. Chilam Cheang, Sijin Chen, Zhongren Cui, Yingdong Hu, Liqun Huang, Tao Kong, Hang Li, Yifeng Li, et al.. (2025). [GR-3 Technical Report](https://arxiv.org/abs/2507.15493). arXiv:2507.15493.
11. Kaustubh Sridhar, Souradeep Dutta, Dinesh Jayaraman, Insup Lee. (2025). [RICL: Adding In-Context Adaptability to Pre-Trained Vision-Language-Action Models](https://arxiv.org/abs/2508.02062). arXiv:2508.02062.
12. Yiguo Fan, Pengxiang Ding, Shuanghao Bai, Xinyang Tong, Yuyang Zhu, Hongchao Lu, Fengqi Dai, Wei Zhao, et al.. (2025). [Long-VLA: Unleashing Long-Horizon Capability of Vision Language Action Model for Robot Manipulation](https://proceedings.mlr.press/v305/fan25a.html). *CoRL 2025*.
13. Delin Qu, Haoming Song, Qizhi Chen, Zhaoqing Chen, Xianqiang Gao, Dong Wang, Xinyi Ye, Qi Lv, et al.. (2025). [EO-1: An Open Unified Embodied Foundation Model for General Robot Control](https://arxiv.org/abs/2508.21112). arXiv:2508.21112.
14. Moritz Reuss, Hongyi Zhou, Marcel Rühle, Ömer Erdinç Yagmurlu, Fabian Otto, Rudolf Lioutikov. (2025). [FLOWER: Democratizing Generalist Robot Policies with Efficient Vision-Language-Action Flow Policies](https://arxiv.org/abs/2509.04996). arXiv:2509.04996.
15. Jinliang Zheng, Jianxiong Li, Zhihao Wang, Dongxiu Liu, Xirui Kang, Yuchun Feng, Yinan Zheng, Jiayin Zou, et al.. (2025). [X-VLA: Soft-Prompted Transformer as Scalable Cross-Embodiment Vision-Language-Action Model](https://arxiv.org/abs/2510.10274). arXiv:2510.10274.
16. Physical Intelligence, Ali Amin, Raichelle Aniceto, Ashwin Balakrishna, Kevin Black, Ken Conley, Grace Connors, James Darpinian, et al.. (2025). [$π^{*}_{0.6}$: a VLA That Learns From Experience](https://arxiv.org/abs/2511.14759). arXiv:2511.14759.
17. Zhenyang Liu, Yongchong Gu, Yikai Wang, Xiangyang Xue, Yanwei Fu. (2026). [ActiveVLA: Injecting Active Perception into Vision-Language-Action Models for Precise 3D Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_ActiveVLA_Injecting_Active_Perception_into_Vision-Language-Action_Models_for_Precise_3D_CVPR_2026_paper.html). *CVPR 2026*.
18. Hao Luo, Ye Wang, Wanpeng Zhang, Sipeng Zheng, Ziheng Xi, Chaoyi Xu, Haiweng Xu, Haoqi Yuan, et al.. (2026). [Being-H0.5: Scaling Human-Centric Robot Learning for Cross-Embodiment Generalization](https://arxiv.org/abs/2601.12993). arXiv:2601.12993.
19. I. Apanasevich, M. Artemyev, R. Babakyan, P. Fedotova, D. Grankin, E. Kupryashin, A. Misailidi, D. Nerus, et al.. (2026). [Green-VLA: Staged Vision-Language-Action Model for Generalist Robots](https://arxiv.org/abs/2602.00919). arXiv:2602.00919.
20. Tong Chen, Hang Wu, Jiasen Wang, Xiaotao Li, Lu Fang. (2026). [StreamVLA: Breaking the Reason-Act Cycle via Completion-State Gating](https://arxiv.org/abs/2602.01100). arXiv:2602.01100.
21. Wentao Zhang, Aolan Sun, Wentao Mo, Xiaoyang Qu, Yuxin Zheng, Jianzong Wang. (2026). [From Knowing to Doing Precisely: A General Self-Correction and Termination Framework for VLA models](https://arxiv.org/abs/2602.01811). arXiv:2602.01811.
22. Rui Cai, Jun Guo, Xinze He, Piaopiao Jin, Jie Li, Bingxuan Lin, Futeng Liu, Wei Liu, et al.. (2026). [Xiaomi-Robotics-0: An Open-Sourced Vision-Language-Action Model with Real-Time Execution](https://arxiv.org/abs/2602.12684). arXiv:2602.12684.
23. Guangqi Jiang, Yutong Liang, Jianglong Ye, Jiayin Huang, Changwei Jing, Rocky Duan, Pieter Abbeel, Xiaolong Wang, et al.. (2026). [Cross-Hand Latent Representation for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Jiang_Cross-Hand_Latent_Representation_for_Vision-Language-Action_Models_CVPR_2026_paper.html). *CVPR 2026*.
24. Physical Intelligence, Bo Ai, Ali Amin, Raichelle Aniceto, Ashwin Balakrishna, Greg Balke, Kevin Black, George Bokinsky, et al.. (2026). [$π_{0.7}$: a Steerable Generalist Robotic Foundation Model with Emergent Capabilities](https://arxiv.org/abs/2604.15483). arXiv:2604.15483.
25. Open-H-Embodiment Consortium, :, Nigel Nelson, Juo-Tung Chen, Jesse Haworth, Xinhao Chen, Lukas Zbinden, Dianye Huang, et al.. (2026). [Open-H-Embodiment: A Large-Scale Dataset for Enabling Foundation Models in Medical Robotics](https://arxiv.org/abs/2604.21017). arXiv:2604.21017.
26. Qiuyue Wang, Mingsheng Li, Jian Guan, Jinhui Ye, Sicheng Xie, Yitao Liu, Junhao Chen, Zhixuan Liang, et al.. (2026). [Qwen-VLA: Unifying Vision-Language-Action Modeling across Tasks, Environments, and Robot Embodiments](https://arxiv.org/abs/2605.30280). arXiv:2605.30280.
27. Taiyi Su, Jian Zhu, Tianjian Wang, Youzhang He, Zitai Huang, Jianjun Zhang, Chong Ma, Hanyang Wang, et al.. (2026). [DeMaVLA: A Vision-Language-Action Foundation Model for Generalizable Deformable Manipulation](https://arxiv.org/abs/2605.31286). arXiv:2605.31286.
28. Lingfeng Zhang, Xiaoshuai Hao, Yingbo Tang, Lei Zhou, Shuyi Zhang, Jinkun Liu, Hongsheng Li, Chenhao Zhang, et al.. (2026). [OneVLA: A Unified Framework for Embodied Tasks](https://arxiv.org/abs/2606.01241). arXiv:2606.01241.
29. Xiaomi Robotics Team, Jun Guo, Piaopiao Jin, Jason Li, Peiyan Li, Yingyan Li, Futeng Liu, Wanli Peng, et al.. (2026). [Xiaomi-Robotics-1: Scaling Vision-Language-Action Models with over 100K Hours of Real-World Trajectories](https://arxiv.org/abs/2607.15330). arXiv:2607.15330.
### 大小脑与双系统

1. Zhenyang Liu, Yongchong Gu, Sixiao Zheng, Yanwei Fu, Xiangyang Xue, Yu-Gang Jiang. (2025). [TriVLA: A Triple-System-Based Unified Vision-Language-Action Model with Episodic World Modeling for General Robot Control](https://arxiv.org/abs/2507.01424). arXiv:2507.01424.
2. Wenkai Guo, Guanxing Lu, Haoyuan Deng, Zhenyu Wu, Yansong Tang, Ziwei Wang. (2025). [VLA-Reasoner: Empowering Vision-Language-Action Models with Reasoning via Online Monte Carlo Tree Search](https://arxiv.org/abs/2509.22643). arXiv:2509.22643.
3. Angen Ye, Zeyu Zhang, Boyuan Wang, Xiaofeng Wang, Dapeng Zhang, Zheng Zhu. (2025). [VLA-R1: Enhancing Reasoning in Vision-Language-Action Models](https://arxiv.org/abs/2510.01623). arXiv:2510.01623.
4. Wenhui Huang, Changhe Chen, Han Qi, Chen Lv, Yilun Du, Heng Yang. (2025). [MoTVLA: A Vision-Language-Action Model with Unified Fast-Slow Reasoning](https://arxiv.org/abs/2510.18337). arXiv:2510.18337.
5. Zhen Fang, Zhuoyang Liu, Jiaming Liu, Hao Chen, Yu Zeng, Shiting Huang, Zehui Chen, Lin Chen, et al.. (2025). [DualVLA: Building a Generalizable Embodied Agent via Partial Decoupling of Reasoning and Action](https://arxiv.org/abs/2511.22134). arXiv:2511.22134.
6. Yueru Jia, Jiaming Liu, Shengbang Liu, Rui Zhou, Wanhe Yu, Yuyang Yan, Xiaowei Chi, Yandong Guo, et al.. (2025). [Video2Act: A Dual-System Video Diffusion Policy with Robotic Spatio-Motional Modeling](https://arxiv.org/abs/2512.03044). arXiv:2512.03044.
7. Meng Wei, Chenyang Wan, Jiaqi Peng, Xiqian Yu, Yuqiang Yang, Delin Feng, Wenzhe Cai, Chenming Zhu, et al.. (2025). [Ground Slow, Move Fast: A Dual-System Foundation Model for Generalizable Vision-and-Language Navigation](https://arxiv.org/abs/2512.08186). arXiv:2512.08186.
8. Linqing Zhong, Yi Liu, Yifei Wei, Ziyu Xiong, Maoqing Yao, Si Liu, Guanghui Ren. (2026). [ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Zhong_ACoT-VLA_Action_Chain-of-Thought_for_Vision-Language-Action_Models_CVPR_2026_paper.html). *CVPR 2026*.
9. Bin Yu, Shijie Lian, Xiaopeng Lin, Yuliang Wei, Zhaolong Shen, Changti Wu, Yuzhuo Miao, Xinming Wang, et al.. (2026). [TwinBrainVLA: Unleashing the Potential of Generalist VLMs for Embodied Tasks via Asymmetric Mixture-of-Transformers](https://arxiv.org/abs/2601.14133). arXiv:2601.14133.
10. Yao Li, Peiyuan Tang, Wuyang Zhang, Chengyang Zhu, Yifan Duan, Weikai Shi, Xiaodong Zhang, Zijiang Yang, et al.. (2026). [FAVLA: A Force-Adaptive Fast-Slow VLA model for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2602.23648). arXiv:2602.23648.
11. Emily Yue-Ting Jia, Weiduo Yuan, Tianheng Shi, Vitor Guizilini, Jiageng Mao, Yue Wang. (2026). [DreamPlan: Efficient Reinforcement Fine-Tuning of Vision-Language Planners via Video World Models](https://arxiv.org/abs/2603.16860). arXiv:2603.16860.
12. Yi Chen, Yuying Ge, Hui Zhou, Mingyu Ding, Yixiao Ge, Xihui Liu. (2026). [DIAL: Decoupling Intent and Action via Latent World Modeling for End-to-End VLA](https://arxiv.org/abs/2603.29844). arXiv:2603.29844.
13. Isabella Liu, An-Chieh Cheng, Rui Yan, Geng Chen, Ri-Zhao Qiu, Xueyan Zou, Sha Yi, Hongxu Yin, et al.. (2026). [Long-Horizon Manipulation via Trace-Conditioned VLA Planning](https://arxiv.org/abs/2604.21924). arXiv:2604.21924.
14. Yifei Wei, Linqing Zhong, Yi Liu, Yuxiang Lu, Xindong He, Maoqing Yao, Guanghui Ren. (2026). [Libra-VLA: Achieving Learning Equilibrium via Asynchronous Coarse-to-Fine Dual-System](https://arxiv.org/abs/2604.24921). arXiv:2604.24921.
15. Yueh-Hua Wu, Tatsuya Matsushima, Kei Ota. (2026). [Continuous Reasoning for Vision-Language-Action](https://arxiv.org/abs/2606.00229). arXiv:2606.00229.
16. Haoyang Li, Guanlin Li, Youhe Feng, Chen Zhao, Zhuoran Wang, Yang Li, Qizhe Wei, Shifeng Bao, et al.. (2026). [Training Vision-Language-Action Models with Dense Embodied Chain-of-Thought Supervision](https://arxiv.org/abs/2606.30552). arXiv:2606.30552.
17. Dongyoon Hwang, Byungkun Lee, Dongjin Kim, Hyojin Jang, Hoiyeong Jin, Jueun Mun, Minho Park, Hojoon Lee, et al.. (2026). [3D HAMSTER: Bridging Planning and Control in Hierarchical Vision Language Action Models through 3D Trajectory Guidance](https://arxiv.org/abs/2606.31329). arXiv:2606.31329.
18. Yang Liu, Weixing Chen, Xinshuai Song, Tao Pu, Siwen Mo, Yongjie Bai, Zihao Chen, Qianran Sun, et al.. (2026). [PhyAgentOS: A Self-Evolving Operating System for Embodied Agents with Decoupled Cognitive Planning and Physical Execution](https://arxiv.org/abs/2607.16636). arXiv:2607.16636.
### 灵巧操作

1. Han Xue, Jieji Ren, Wendi Chen, Gu Zhang, Yuan Fang, Guoying Gu, Huazhe Xu, Cewu Lu. (2025). [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html). *RSS 2025*.
2. Mengda Xu, H. Zhang, Yifan Hou, Zhenjia Xu, L. Fan, Manuela Veloso, Shuran Song. (2025). [DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://proceedings.mlr.press/v305/xu25b.html). *CoRL 2025*.
3. Gagan Khandate. (2025). [Towards Human-level Dexterity via Robot Learning](https://arxiv.org/abs/2507.09117). arXiv:2507.09117.
4. Zhengxue Cheng, Yiqian Zhang, Anni Tang, Keyu Wang, Wenkang Zhang, Haoyu Li, Hengdi Zhang, Li Song. (2025). [OmniVTLA: Vision-Tactile-Language-Action Models with Semantic-Aligned Tactile Sensing](https://arxiv.org/abs/2508.08706). arXiv:2508.08706.
5. Harrison Field, Max Yang, Yijiong Lin, Efi Psomopoulou, David Barton, Nathan F. Lepora. (2025). [Text2Touch: Tactile In-Hand Manipulation with LLM-Designed Reward Functions](https://arxiv.org/abs/2509.07445). arXiv:2509.07445.
6. Zhiyuan Wu, Rolandos Alexandros Potamias, Xuyang Zhang, Zhongqun Zhang, Jiankang Deng, Shan Luo. (2025). [CEDex: Cross-Embodiment Dexterous Grasp Generation at Scale from Human-like Contact Representations](https://arxiv.org/abs/2509.24661). arXiv:2509.24661.
7. Jhen Hsieh, Kuan-Hsun Tu, Kuo-Han Hung, Tsung-Wei Ke. (2025). [DexMan: Learning Bimanual Dexterous Manipulation from Human and Generated Videos](https://arxiv.org/abs/2510.08475). arXiv:2510.08475.
8. Le Chen, Yi Zhao, Jan Schneider, Quankai Gao, Simon Guist, Cheng Qian, Juho Kannala, Bernhard Schölkopf, et al.. (2025). [Dexterous Robotic Piano Playing at Scale](https://arxiv.org/abs/2511.02504). arXiv:2511.02504.
9. Huayi Zhou, Kui Jia. (2025). [One-Shot Real-World Demonstration Synthesis for Scalable Bimanual Manipulation](https://arxiv.org/abs/2512.09297). arXiv:2512.09297.
10. Zhongxuan Li, Zeliang Guo, Jun Hu, David Navarro-Alarcon, Jia Pan, Hongmin Wu, Peng Zhou. (2026). [UniBiDex: A Unified Teleoperation Framework for Robotic Bimanual Dexterous Manipulation](https://arxiv.org/abs/2601.04629). arXiv:2601.04629.
11. Hung-Chieh Fang, Amber Xie, Jennifer Grannen, Kenneth Llontop, Dorsa Sadigh. (2026). [DexDrummer: In-Hand, Contact-Rich, and Long-Horizon Dexterous Robot Drumming](https://arxiv.org/abs/2603.22263). arXiv:2603.22263.
12. Gu Zhang, Qicheng Xu, Haozhe Zhang, Jianhan Ma, Long He, Yiming Bao, Zeyu Ping, Zhecheng Yuan, et al.. (2026). [UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html). *CVPR 2026*.
13. Yaru Niu, Zhenlong Fang, Binghong Chen, Shuai Zhou, Revanth Krishna Senthilkumaran, Hao Zhang, Bingqing Chen, Chen Qiu, et al.. (2026). [Learning Versatile Humanoid Manipulation with Touch Dreaming](https://arxiv.org/abs/2604.13015). arXiv:2604.13015.
14. Zhixuan Xu, Yichen Li, Xuanye Wu, Tianyu Qiu, Lin Shao. (2026). [FingerEye: Learning Dexterous Manipulation with Continuous Vision-Tactile Sensing](https://arxiv.org/abs/2604.20689). arXiv:2604.20689.
15. Zhongxi Chen, Yifan Han, Yanming Shao, Huanming Liu, Congsheng Xu, Xiaoyu Chen, Yao Mu, Wenzhao Lian. (2026). [BORA: Bridging Offline Reinforcement Learning and Online Residual Adaptation for Real-World Dexterous VLA Models](https://arxiv.org/abs/2605.30226). arXiv:2605.30226.
16. Xidong Zhang, Yichi Zhang, Jiaxin Shi, Fucai Zhu, Siyu Zhu, Michael Yu Wang, Xiaojun Wu, Weihao Yuan. (2026). [UniTacVLA: Unified Tactile Understanding and Prediction in Vision Language Action Models](https://arxiv.org/abs/2606.31723). arXiv:2606.31723.
17. Bowen Jiang, William Painter Reger, Roberto Martin-Martin. (2026). [CoDex: Learning Compositional Dexterous Functional Manipulation without Demonstrations](https://arxiv.org/abs/2606.31909). arXiv:2606.31909.
18. Ning Cheng, Jinan Xu, Wanlin Li, Yangzhi Chen, Jing Gao, Yiqun Wang, Kelan Peng, Wenjuan Han. (2026). [τ: Learning Touch-Augmented Vision-Language-Action Models from Future Visual Supervision](https://arxiv.org/abs/2607.24485). arXiv:2607.24485.
### 世界模型

1. Yuhang Huang, Jiazhao Zhang, Shilong Zou, Xinwang Liu, Ruizhen Hu, Kai Xu. (2025). [LaDi-WM: A Latent Diffusion-based World Model for Predictive Manipulation](https://proceedings.mlr.press/v305/huang25a.html). *CoRL 2025*.
2. Suning Huang, Qianzhong Chen, Xiaohan Zhang, Jiankai Sun, Mac Schwager. (2025). [ParticleFormer: A 3D Point Cloud World Model for Multi-Object, Multi-Material Robotic Manipulation](https://proceedings.mlr.press/v305/huang25c.html). *CoRL 2025*.
3. Boyuan Wang, Xinpan Meng, Xiaofeng Wang, Zheng Zhu, Angen Ye, Yang Wang, Zhiqin Yang, Chaojun Ni, et al.. (2025). [EmbodieDreamer: Advancing Real2Sim2Real Transfer for Policy Training via Embodied World Modeling](https://arxiv.org/abs/2507.05198). arXiv:2507.05198.
4. Guanxing Lu, Baoxiong Jia, Puhao Li, Yixin Chen, Ziwei Wang, Yansong Tang, Siyuan Huang. (2025). [GWM: Towards Scalable Gaussian World Models for Robotic Manipulation](https://arxiv.org/abs/2508.17600). arXiv:2508.17600.
5. Bahey Tharwat, Yara Nasser, Ali Abouzeid, Ian Reid. (2025). [Latent Action Pretraining Through World Modeling](https://arxiv.org/abs/2509.18428). arXiv:2509.18428.
6. Hengtao Li, Pengxiang Ding, Runze Suo, Yihao Wang, Zirui Ge, Dongyuan Zang, Kexian Yu, Mingyang Sun, et al.. (2025). [VLA-RFT: Vision-Language-Action Reinforcement Fine-tuning with Verified Rewards in World Simulators](https://arxiv.org/abs/2510.00406). arXiv:2510.00406.
7. Yanjiang Guo, Lucy Xiaoyang Shi, Jianyu Chen, Chelsea Finn. (2025). [Ctrl-World: A Controllable Generative World Model for Robot Manipulation](https://arxiv.org/abs/2510.10125). arXiv:2510.10125.
8. Zihao He, Bo Ai, Tongzhou Mu, Yulin Liu, Weikang Wan, Jiawei Fu, Yilun Du, Henrik I. Christensen, et al.. (2025). [Scaling Cross-Embodiment World Models for Dexterous Manipulation](https://arxiv.org/abs/2511.01177). arXiv:2511.01177.
9. R. Khorrambakht, Joaquim Ortiz-Haro, Joseph Amigo, Omar Mostafa, Daniel Dugas, Franziska Meier, Ludovic Righetti. (2025). [WorldPlanner: Monte Carlo Tree Search and MPC with Action-Conditioned Visual World Models](https://arxiv.org/abs/2511.03077). arXiv:2511.03077.
10. Haowen Liu, Shaoxiong Yao, Haonan Chen, Jiawei Gao, Jiayuan Mao, Jia-Bin Huang, Yilun Du. (2025). [SIMPACT: Simulation-Enabled Action Planning using Vision-Language Models](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_SIMPACT_Simulation-Enabled_Action_Planning_using_Vision-Language_Models_CVPR_2026_paper.html). *CVPR 2026*.
11. Hongzhe Bi, Hengkai Tan, Shenghao Xie, Zeyuan Wang, Shuhe Huang, Haitian Liu, Ruowen Zhao, Yao Feng, et al.. (2025). [Motus: A Unified Latent Action World Model](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html). *CVPR 2026*.
12. Boyuan Chen, Tianyuan Zhang, Haoran Geng, Caiyi Zhang, Peihao Li, Kiwhan Song, William T. Freeman, Jitendra Malik, et al.. (2025). [Large Video Planner Enables Generalizable Robot Control](https://arxiv.org/abs/2512.15840). arXiv:2512.15840.
13. Wenjun Lin, Jensen Zhang, Kaitong Cai, Keze Wang. (2025). [STORM: Search-Guided Generative World Models for Robotic Manipulation](https://arxiv.org/abs/2512.18477). arXiv:2512.18477.
14. Quentin Garrido, Tushar Nagarajan, Basile Terver, Nicolas Ballas, Yann LeCun, Michael Rabbat. (2026). [Learning Latent Action World Models In The Wild](https://arxiv.org/abs/2601.05230). arXiv:2601.05230.
15. Moo Jin Kim, Yihuai Gao, Tsung-Yi Lin, Yen-Chen Lin, Yunhao Ge, Grace Lam, Percy Liang, Shuran Song, et al.. (2026). [Cosmos Policy: Fine-Tuning Video Models for Visuomotor Control and Planning](https://arxiv.org/abs/2601.16163). arXiv:2601.16163.
16. Zhennan Jiang, Shangqing Zhou, Yutong Jiang, Zefang Huang, Mingjie Wei, Yuhui Chen, Tianxing Zhou, Zhen Guo, et al.. (2026). [WoVR: World Models as Reliable Simulators for Post-Training VLA Policies with RL](https://arxiv.org/abs/2602.13977). arXiv:2602.13977.
17. Chenyv Liu, Wentao Tan, Lei Zhu, Fengling Li, Jingjing Li, Guoli Yang, Heng Tao Shen. (2026). [Self-Correcting VLA: Online Action Refinement via Sparse World Imagination](https://arxiv.org/abs/2602.21633). arXiv:2602.21633.
18. Jiasong Xiao, Yutao She, Kai Li, Yuyang Sha, Ziang Cheng. (2026). [StemVLA:An Open-Source Vision-Language-Action Model with Future 3D Spatial Geometry Knowledge and 4D Historical Representation](https://arxiv.org/abs/2602.23721). arXiv:2602.23721.
19. Ruixiang Wang, Qingming Liu, Yueci Deng, Guiliang Liu, Zhen Liu, Kui Jia. (2026). [EVA: Aligning Video World Models with Executable Robot Actions via Inverse Dynamics Rewards](https://arxiv.org/abs/2603.17808). arXiv:2603.17808.
20. Yuhang Zheng, Songen Gu, Weize Li, Yupeng Zheng, Yujie Zang, Shuai Tian, Xiang Li, Ce Hao, et al.. (2026). [OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2603.19201). arXiv:2603.19201.
21. Yuxuan Tian, Yurun Jin, Bin Yu, Yukun Shi, Hao Wu, Chi Harold Liu, Kai Chen, Cong Huang. (2026). [STARRY: Spatial-Temporal Action-Centric World Modeling for Robotic Manipulation](https://arxiv.org/abs/2604.26848). arXiv:2604.26848.
22. Sizhe Lester Li, Evan Kim, Xingjian Bai, Tong Zhao, Tao Pang, Max Simchowitz, Vincent Sitzmann. (2026). [Turning Video Models into Generalist Robot Policies](https://arxiv.org/abs/2605.27817). arXiv:2605.27817.
23. Pengfei Zhou, Shengcong Chen, Di Chen, Jiaxu Wang, Rongjun Jin, Bingwen Zhu, Yike Pan, Songen Gu, et al.. (2026). [$τ_0$-WM: A Unified Video-Action World Model for Robotic Manipulation](https://arxiv.org/abs/2606.01027). arXiv:2606.01027.
24. Ziyu Shan, Zhenyu Wu, Xiaofeng Wang, Zheng Zhu, Ziwei Wang. (2026). [DVG-WM: Disentangled Video Generation Enables Efficient Embodied World Model for Robotic Manipulation](https://arxiv.org/abs/2606.32028). arXiv:2606.32028.
25. Yunao Huang, Shiyu Sang, Haotao Lu, Suting Ni, Shijie Wu, Ziyang Guo, Ye Shi, Jingya Wang. (2026). [ViTacWorld: Scaling Visuo-Tactile World Models for Contact-Rich Robot Manipulation](https://arxiv.org/abs/2607.22530). arXiv:2607.22530.
26. Haoyuan Ji, Lingxiang Fan, Shang Su, Yinqiao Lu, Mengkai Shi, Jun Gao, Shuo Feng. (2026). [DC-WAM: Dynamic-Centric Visual Supervision and Reasoning for World-Action Models](https://arxiv.org/abs/2607.25918). arXiv:2607.25918.
### 通用机器人学习

1. Lirui Wang, Xinlei Chen, Jialiang Zhao, Kaiming He. (2024). [Scaling Proprioceptive-Visual Learning with Heterogeneous Pre-trained Transformers](https://papers.nips.cc/paper_files/paper/2024/hash/e0f393e7980a24fd12fa6f15adfa25fb-Abstract-Conference.html). *NeurIPS 2024*.
2. Yixiang Chen, Peiyan Li, Yan Huang, Jiabing Yang, Kehan Chen, Liang Wang. (2025). [EC-Flow: Enabling Versatile Robotic Manipulation from Action-Unlabeled Videos via Embodiment-Centric Flow](https://arxiv.org/abs/2507.06224). arXiv:2507.06224.
3. Hongzhe Bi, Lingxuan Wu, Tianwei Lin, Hengkai Tan, Zhizhong Su, Hang Su, Jun Zhu. (2025). [H-RDT: Human Manipulation Enhanced Bimanual Robotic Manipulation](https://arxiv.org/abs/2507.23523). arXiv:2507.23523.
4. Junbang Liang, Pavel Tokmakov, Ruoshi Liu, Sruthi Sudhakar, Paarth Shah, Rares Ambrus, Carl Vondrick. (2025). [Video Generators are Robot Policies](https://arxiv.org/abs/2508.00795). arXiv:2508.00795.
5. Akshay L Chandra, Iman Nematollahi, Chenguang Huang, Tim Welschehold, Wolfram Burgard, Abhinav Valada. (2025). [DiWA: Diffusion Policy Adaptation with World Models](https://arxiv.org/abs/2508.03645). arXiv:2508.03645.
6. Marion Lepert, Jiaying Fang, Jeannette Bohg. (2025). [Masquerade: Learning from In-the-wild Human Videos using Data-Editing](https://arxiv.org/abs/2508.09976). arXiv:2508.09976.
7. Ge Yan, Jiyue Zhu, Yuquan Deng, Shiqi Yang, Ri-Zhao Qiu, Xuxin Cheng, Marius Memmel, Ranjay Krishna, et al.. (2025). [ManiFlow: A General Robot Manipulation Policy via Consistency Flow Training](https://arxiv.org/abs/2509.01819). arXiv:2509.01819.
8. Ahad Jawaid, Yu Xiang. (2025). [OpenEgo: A Large-Scale Multimodal Egocentric Dataset for Dexterous Manipulation](https://arxiv.org/abs/2509.05513). arXiv:2509.05513.
9. Georgios Tziafas, Jiayun Zhang, Hamidreza Kasaei. (2025). [Parse-Augment-Distill: Learning Generalizable Bimanual Visuomotor Policies from Single Human Video](https://arxiv.org/abs/2509.20286). arXiv:2509.20286.
10. Qixiu Li, Yu Deng, Yaobo Liang, Lin Luo, Lei Zhou, Chengtang Yao, Lingqi Zeng, Zhiyuan Feng, et al.. (2025). [Scalable Vision-Language-Action Model Pretraining for Robotic Manipulation with Real-Life Human Activity Videos](https://arxiv.org/abs/2510.21571). arXiv:2510.21571.
11. Maximus A. Pace, Prithwish Dan, Chuanruo Ning, Atiksh Bhardwaj, Audrey Du, Edward W. Duan, Wei-Chiu Ma, Kushal Kedia. (2025). [X-Diffusion: Training Diffusion Policies on Cross-Embodiment Human Demonstrations](https://arxiv.org/abs/2511.04671). arXiv:2511.04671.
12. Yang Tian, Yuyin Yang, Yiman Xie, Zetao Cai, Xu Shi, Ning Gao, Hangxu Liu, Xuekun Jiang, et al.. (2025). [InternData-A1: Pioneering High-Fidelity Synthetic Data for Pre-training Generalist Policy](https://arxiv.org/abs/2511.16651). arXiv:2511.16651.
13. Yuhong Zhang, Zihan Gao, Shengpeng Li, Ling-Hao Chen, Kaisheng Liu, Runqing Cheng, Xiao Lin, Junjia Liu, et al.. (2025). [RoboWheel: A Data Engine from Real-World Human Demonstrations for Cross-Embodiment Robotic Learning](https://arxiv.org/abs/2512.02729). arXiv:2512.02729.
14. Huajie Tan, P. Co, Yijie Xu, Shanyu Rong, Yuheng Ji, Cheng Chi, Xiansheng Chen, Qiongyue Zhang, et al.. (2026). [Action-Sketcher: From Reasoning to Action via Visual Sketches for Long-Horizon Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Tan_Action-Sketcher_From_Reasoning_to_Action_via_Visual_Sketches_for_Robotic_CVPR_2026_paper.html). *CVPR 2026*.
15. Wenlong Huang, Yu-Wei Chao, A. Mousavian, Ming-Yu Liu, Dieter Fox, Kaichun Mo, Fei-Fei Li. (2026). [PointWorld: Scaling 3D World Models for In-The-Wild Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Huang_PointWorld_Scaling_3D_World_Models_for_In-The-Wild_Robotic_Manipulation_CVPR_2026_paper.html). *CVPR 2026*.
16. Ansh Kumar Sharma, Yixiang Sun, Ning Lu, Yunzhe Zhang, Jiarao Liu, Sherry Yang. (2026). [World-Gymnast: Training Robots with Reinforcement Learning in a World Model](https://arxiv.org/abs/2602.02454). arXiv:2602.02454.
17. Ruijie Zheng, Dantong Niu, Yuqi Xie, Jing Wang, Mengda Xu, Yunfan Jiang, Fernando Castañeda, Fengyuan Hu, et al.. (2026). [EgoScale: Scaling Dexterous Manipulation with Diverse Egocentric Human Data](https://arxiv.org/abs/2602.16710). arXiv:2602.16710.
18. Hao Luo, Ye Wang, Wanpeng Zhang, Haoqi Yuan, Yicheng Feng, Haiweng Xu, Sipeng Zheng, Zongqing Lu. (2026). [Joint-Aligned Latent Action: Towards Scalable VLA Pretraining in the Wild](https://arxiv.org/abs/2602.21736). arXiv:2602.21736.
19. Yu Sun, Meng Cao, Yang Ping, Kaidong Zhang, Qingxuan Chen, Rongtao Xu, Liangwang Ruan, Xuecheng Chen, et al.. (2026). [ManipArena: Comprehensive Real-world Evaluation of Reasoning-Oriented Generalist Robot Manipulation](https://arxiv.org/abs/2603.28545). arXiv:2603.28545.
20. Arthur Allshire, Himanshu Gaurav Singh, Ritvik Singh, Adam Rashid, Hongsuk Choi, David McAllister, Justin Yu, Yiyuan Chen, et al.. (2026). [Scalable Behavior Cloning with Open Data, Training, and Evaluation](https://arxiv.org/abs/2606.27375). arXiv:2606.27375.
21. Xiaopeng Lin, Ruoqi Yang, Shijie Lian, Zhaolong Shen, Bin Yu, Changti Wu, Haibao Liu, Yuxiang Zhang, et al.. (2026). [Human-as-Humanoid: Enabling Zero-Shot Humanoid Learning from Ego-Exo Human Videos with Human-Aligned Embodiments](https://arxiv.org/abs/2606.32009). arXiv:2606.32009.
22. Yifan Ye, Yankai Fu, Yaoxu Lv, Bohan Hou, Jun Cen, Lingdong Kong, Duo Zheng, Tianxing Chen, et al.. (2026). [Data Pyramid for Embodied Manipulation](https://arxiv.org/abs/2607.24744). arXiv:2607.24744.

<!-- 更新标记：参考文献 最后更新 2026.07 -->

---
