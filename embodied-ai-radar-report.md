# 具身智能研究雷达

> **数据截点**：2026 年 8 月 24 日<br>
> **主分析期**：2025 年 7 月—2026 年 6 月 · **7 月完整月** · **8 月前瞻快照**：1–24 日

---


## 执行摘要

> **数据截至**：2026-08-24 · **主分析期**：2025.07–2026.06<br>
> **精读**：84 篇 · **官方评审锚点**：30 条

过去 12 个月最显眼的共识是 VLA / generalist policy 的论文数量急升；更有战略价值的变化却发生在“模型之外”：实时调度、动作验证与恢复、部署数据飞轮、可执行 world model、视触觉闭环和跨本体接口。**综合判断（推断）：**具身智能正在从“能输出动作”进入“能在物理世界持续运行、发现错误并学习”的阶段。

::: tip 统一分析口径
全站主题结构统一使用当前 15 个研究方向，并同时维护 arXiv 母库、正式发表母库、严格官方 proceedings 与 GitHub 证据。详见[语料扩充与覆盖审计](/analysis/corpus-expansion)。
:::

::: info 8 月更新
7 月已收完整月；8 月截至 24 日已纳入 328 条直接候选。由于月份尚未关闭，不与完整月计算环比；本轮重点新增[问题地图](/questions/)，把接触表征、Ego-to-Action、失败回流和软硬件 co-design 与公开证据逐项对应。
:::

<div class="radar-kpis">
  <div class="radar-kpi"><strong>31,773</strong><span>arXiv 宽召回母集</span></div>
  <div class="radar-kpi"><strong>10,404</strong><span>窗口内正式发表记录</span></div>
  <div class="radar-kpi"><strong>824</strong><span>严格官方 proceedings</span></div>
  <div class="radar-kpi"><strong>41,592</strong><span>去重 canonical works</span></div>
  <div class="radar-kpi"><strong>42</strong><span>GitHub 核验仓库</span></div>
</div>

### 六个年度判断

1. **策略学习构成数量底座，VLA 是最显眼的命名共识。** 真正拉开差异的部分已转向执行、数据、后训练和真实机器人闭环。
2. **大小脑的真正拐点是实时系统。** fast–slow 名称本身价值有限，completion gating、continuous reasoning、verifier 和 3D trace 才是接口创新。
3. **world model 的淘汰赛开始。** 能否在同算力下提高闭环规划、RL 样本效率或失败恢复，将把控制模型与普通视频生成分开。
4. **触觉从“小众传感器”变成领先指标。** 它最可能先在接触失败恢复、材料/滑移预测和灵巧 world model 中兑现。
5. **跨本体更可能通过共享表示 + 小型 adapter 实现。** “一个权重直接覆盖所有机器人”的证据仍不足。
6. **数据护城河正在迁移到部署闭环。** 未来关键指标不是总小时，而是失败覆盖、修正效率和新任务上线速度。

### 精选月度分析层

<div class="radar-kpis">
  <div class="radar-kpi"><strong>5221</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>3214</strong><span>同比基线候选</span></div>
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

飞书材料提出的系统问题及文档之外的研究缺口，见[Q0–Q10 研究问题地图](/questions/)和[遗漏方向](/questions/blind-spots)。

---


## 月度研究雷达

> 月份按 arXiv 首次提交日期归档；主题数量统一使用当前 15 个研究方向。2026 年 8 月是不完整快照，因此保留 7 月参照数但不计算误导性的百分比。

| 月份 | 候选数 | 环比增量 | 环比 | 同比增量 | 同比 | 数量主导方向 | 精读 | 真机确认 |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| [2025 年 7 月](/monthly/2025-07) | 265 | -82 | -23.6% | +67 | +33.8% | D8 · 策略学习（72） | 7 | 6/7 |
| [2025 年 8 月](/monthly/2025-08) | 288 | +23 | +8.7% | +143 | +98.6% | D5 · 人形与全身控制（66） | 7 | 5/7 |
| [2025 年 9 月](/monthly/2025-09) | 469 | +181 | +62.8% | +151 | +47.5% | D8 · 策略学习（124） | 7 | 5/7 |
| [2025 年 10 月](/monthly/2025-10) | 427 | -42 | -9.0% | +125 | +41.4% | D8 · 策略学习（105） | 7 | 4/7 |
| [2025 年 11 月](/monthly/2025-11) | 347 | -80 | -18.7% | +124 | +55.6% | D8 · 策略学习（87） | 7 | 5/7 |
| [2025 年 12 月](/monthly/2025-12) | 299 | -48 | -13.8% | +91 | +43.8% | D8 · 策略学习（75） | 7 | 5/7 |
| [2026 年 1 月](/monthly/2026-01) | 280 | -19 | -6.4% | +149 | +113.7% | D8 · 策略学习（72） | 7 | 3/7 |
| [2026 年 2 月](/monthly/2026-02) | 466 | +186 | +66.4% | +203 | +77.2% | D8 · 策略学习（91） | 7 | 5/7 |
| [2026 年 3 月](/monthly/2026-03) | 694 | +228 | +48.9% | +281 | +68.0% | D8 · 策略学习（157） | 7 | 5/7 |
| [2026 年 4 月](/monthly/2026-04) | 392 | -302 | -43.5% | +145 | +58.7% | D8 · 策略学习（89） | 7 | 4/7 |
| [2026 年 5 月](/monthly/2026-05) | 559 | +167 | +42.6% | +140 | +33.4% | D8 · 策略学习（138） | 7 | 6/7 |
| [2026 年 6 月](/monthly/2026-06) | 735 | +176 | +31.5% | +388 | +111.8% | D8 · 策略学习（141） | 7 | 6/7 |
| [2026 年 7 月（完整月）](/monthly/2026-07) | 506 | -229 | -31.2% | +241 | +90.9% | D8 · 策略学习（102） | 20 | 13/20 |
| [2026 年 8 月（截至 24 日）](/monthly/2026-08) | 328 | — | 不可比 | — | 不可比 | D1 · 具身基础模型（57） | 0 | 0/0 |

### 怎么读月度页

1. 先看绝对数量、环比和同比，判断变化是短期波动还是跨年结构增长。
2. 再看精读论文的真机、跨任务/本体、长时序和开放资产。
3. 用官方同行评审锚点区分“arXiv 密集”与“已有独立评审路线”。
4. 最后看弱信号与反证；前者寻找未来，后者防止把命名潮误判为能力跃迁。

---


## 2025 年 7 月研究雷达

> **统计口径。** 当前 15 个研究方向用于数量结构；7 篇精读样本用于实验与开放性指标。上月为 2025-06，同比月为 2024-07。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>265</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>6/7</strong><span>核验确认真机</span></div>
  <div class="radar-kpi"><strong>0</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

人类视频开始被拆成可迁移的动作先验；与此同时，空间增强很热，但尚未等于通用性。

### 主题结构与环比

> 本表使用当前 15 个研究方向，只统计自动判为“直接候选”的记录。每篇论文只计一个主方向，环比同时展示绝对量和百分比。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>1,060</strong><span>当月 arXiv 母集</span></div>
  <div class="radar-kpi"><strong>265</strong><span>直接候选</span></div>
  <div class="radar-kpi"><strong>187</strong><span>边界候选</span></div>
  <div class="radar-kpi"><strong>347</strong><span>上月直接候选</span></div>
</div>

| 主方向 | 本月 | 占比 | 上月 | 环比增量 | 环比 |
|---|---:|---:|---:|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 20 | 7.5% | 29 | -9 | -31.0% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 21 | 7.9% | 23 | -2 | -8.7% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 11 | 4.2% | 22 | -11 | -50.0% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 23 | 8.7% | 45 | -22 | -48.9% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 44 | 16.6% | 55 | -11 | -20.0% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 13 | 4.9% | 17 | -4 | -23.5% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 30 | 11.3% | 23 | +7 | +30.4% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 72 | 27.2% | 82 | -10 | -12.2% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 7 | 2.6% | 8 | -1 | -12.5% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 9 | 3.4% | 12 | -3 | -25.0% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 12 | 4.5% | 24 | -12 | -50.0% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 2 | 0.8% | 6 | -4 | -66.7% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 0 | 0.0% | 0 | 0 | — |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 1 | 0.4% | 0 | +1 | 新增 |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 0 | 0.0% | 1 | -1 | -100.0% |
| **总计** | **265** | **100.0%** | **347** | **-82** | **-23.6%** |

跨月比较时，应先看绝对数量与独立论文簇，再用正式发表和 GitHub 采用证据判断是否从 arXiv 热点走向兑现。
### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 人类视频开始被拆成可迁移的动作先验

**变化。** EC-Flow、H-RDT 与 GR-3 分别从无动作标签视频、双臂人类操作和通用数据配方切入，信号尚未形成单一范式，但都在绕开机器人示教瓶颈。

**对比。** 同比基线中此类工作多停留在表征对齐；本月开始把人类数据直接接入动作生成或双臂策略。

**证据。** [EC-Flow: Enabling Versatile Robotic Manipulation from Action-Unlabeled Videos via Embodiment-Centric Flow](https://arxiv.org/abs/2507.06224)；[H-RDT: Human Manipulation Enhanced Bimanual Robotic Manipulation](https://arxiv.org/abs/2507.23523)；[GR-3 Technical Report](https://arxiv.org/abs/2507.15493)

**成熟度与瓶颈。** 多为预训练或受控任务验证，跨本体稳定性仍弱。主要瓶颈是人—机动作空间对齐，以及视频中不可观测的力与接触。

**战略含义。** 优先跟踪能同时拥有数据转换器、机器人数据闭环和跨本体评测的团队。

</div>

<div class="trend-card">

#### <span class="signal signal-c">C · 弱信号</span> “大脑—小脑”正在从二层变成三系统

**变化。** TriVLA 把高层语义、低层动作与 episodic world model 明确拆分；EmbodieDreamer 则让世界模型承担 real-to-sim-to-real 中介。

**对比。** 早期 planner–policy 通常只有两层；本月出现把记忆/预测独立成第三模块的尝试。

**证据。** [TriVLA: A Triple-System-Based Unified Vision-Language-Action Model with Episodic World Modeling for General Robot Control](https://arxiv.org/abs/2507.01424)；[EmbodieDreamer: Advancing Real2Sim2Real Transfer for Policy Training via Embodied World Modeling](https://arxiv.org/abs/2507.05198)

**成熟度与瓶颈。** 概念结构清晰，但独立团队和长时序真机证据不足。主要瓶颈是模块间误差传递与实时调度。

**战略含义。** 将“第三系统”作为观察项，不把新架构命名直接当作能力跃迁。

</div>

<div class="trend-card">

#### <span class="signal signal-d">D · 反证/降温</span> 空间增强很热，但尚未等于通用性

**变化。** Evo-0 用外部视觉几何模型补足 VLA 的 3D 表征，真实机器人结果积极；但没有同时证明跨本体、长时序和独立复现。

**对比。** 数量增量主要来自为 VLA 加适配器，而不是统一训练目标。

**证据。** [Evo-0: Vision-Language-Action Model with Implicit Spatial Understanding](https://arxiv.org/abs/2507.00416)

**成熟度与瓶颈。** 单点能力改善。主要瓶颈是空间 benchmark 增益能否转化为开放环境成功率。

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
| [TriVLA: A Triple-System-Based Unified Vision-Language-Action Model with Episodic World Modeling for General Robot Control](https://arxiv.org/abs/2507.01424) | 2025-07-02 | 具身基础模型与通才策略 | 用 VLM、视频扩散式情景世界模型和 flow-matching 低层策略组成三系统，在约 36 Hz 下兼顾记忆、未来预测与真实机器人长时序控制。 | 真机 · 长时序 · 开放资产 |
| [EmbodieDreamer: Advancing Real2Sim2Real Transfer for Policy Training via Embodied World Modeling](https://arxiv.org/abs/2507.05198) | 2025-07-07 | 世界模型与预测控制 | 联合可微物理参数对齐与条件视频扩散外观对齐，缩小 Real2Sim2Real 差距，并报告真实任务平均成功率提升 29.17%。 | 真机 · 开放资产 |
| [GR-3 Technical Report](https://arxiv.org/abs/2507.15493) | 2025-07-21 | 具身基础模型与通才策略 | GR-3 以网络视觉语言数据、VR 人类轨迹和机器人轨迹协同训练，展示新物体/环境/抽象指令、双臂移动与长时序真实任务泛化。 | 真机 · 多任务 · 长时序 |
| [H-RDT: Human Manipulation Enhanced Bimanual Robotic Manipulation](https://arxiv.org/abs/2507.23523) | 2025-07-31 | 灵巧、双臂与接触操作 | 以 2B diffusion transformer 先学大规模第一视角人类手部先验，再用模块化动作编解码器适配不同机器人，显著提升双臂真实操作。 | 真机 · 跨本体 |
| [Evo-0: Vision-Language-Action Model with Implicit Spatial Understanding](https://arxiv.org/abs/2507.00416) | 2025-07-01 | 具身基础模型与通才策略 | 把现成视觉几何基础模型的深度感知特征以即插即用方式注入 VLA，在无需额外深度传感器的前提下提升仿真与真实场景的空间操作。 | 真机 |
| [EC-Flow: Enabling Versatile Robotic Manipulation from Action-Unlabeled Videos via Embodiment-Centric Flow](https://arxiv.org/abs/2507.06224) | 2025-07-08 | 灵巧、双臂与接触操作 | 从无动作标签视频预测 embodiment-centric flow，再借 URDF 约束转成可执行动作，覆盖遮挡、柔性物体及非位移操作。 | 真机 |
| [Towards Human-level Dexterity via Robot Learning](https://arxiv.org/abs/2507.09117) | 2025-07-12 | 策略学习与优化 | 以结构化探索、采样式规划和视触觉人类示范为主线，总结可扩展多指灵巧操作强化学习的一套方法体系。 | 摘要未确认 |

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

---


## 2025 年 8 月研究雷达

> **统计口径。** 当前 15 个研究方向用于数量结构；7 篇精读样本用于实验与开放性指标。上月为 2025-07，同比月为 2024-08。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>288</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>5/7</strong><span>核验确认真机</span></div>
  <div class="radar-kpi"><strong>1</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

视频生成器开始越过“数据增强”，直接扮演策略；与此同时，世界模型仍更像适配器，而非可靠规划器。

### 主题结构与环比

> 本表使用当前 15 个研究方向，只统计自动判为“直接候选”的记录。每篇论文只计一个主方向，环比同时展示绝对量和百分比。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>1,066</strong><span>当月 arXiv 母集</span></div>
  <div class="radar-kpi"><strong>288</strong><span>直接候选</span></div>
  <div class="radar-kpi"><strong>213</strong><span>边界候选</span></div>
  <div class="radar-kpi"><strong>265</strong><span>上月直接候选</span></div>
</div>

| 主方向 | 本月 | 占比 | 上月 | 环比增量 | 环比 |
|---|---:|---:|---:|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 26 | 9.0% | 20 | +6 | +30.0% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 25 | 8.7% | 21 | +4 | +19.0% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 10 | 3.5% | 11 | -1 | -9.1% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 22 | 7.6% | 23 | -1 | -4.3% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 66 | 22.9% | 44 | +22 | +50.0% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 12 | 4.2% | 13 | -1 | -7.7% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 21 | 7.3% | 30 | -9 | -30.0% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 66 | 22.9% | 72 | -6 | -8.3% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 9 | 3.1% | 7 | +2 | +28.6% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 12 | 4.2% | 9 | +3 | +33.3% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 12 | 4.2% | 12 | 0 | 0.0% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 4 | 1.4% | 2 | +2 | +100.0% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 0 | 0.0% | 0 | 0 | — |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 2 | 0.7% | 1 | +1 | +100.0% |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 1 | 0.3% | 0 | +1 | 新增 |
| **总计** | **288** | **100.0%** | **265** | **+23** | **+8.7%** |

跨月比较时，应先看绝对数量与独立论文簇，再用正式发表和 GitHub 采用证据判断是否从 arXiv 热点走向兑现。
### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 视频生成器开始越过“数据增强”，直接扮演策略

**变化。** Video Generators are Robot Policies、Masquerade 与 DiWA 分别尝试直接控制、视频编辑迁移和用世界模型适配 diffusion policy。

**对比。** 相较 7 月主要把视频当作数据，本月首次集中出现“生成—预测—控制”连续化。

**证据。** [Video Generators are Robot Policies](https://arxiv.org/abs/2508.00795)；[Masquerade: Learning from In-the-wild Human Videos using Data-Editing](https://arxiv.org/abs/2508.09976)；[DiWA: Diffusion Policy Adaptation with World Models](https://arxiv.org/abs/2508.03645)

**成熟度与瓶颈。** 仿真与受控任务为主。主要瓶颈是视频像素质量与可执行动作之间仍存在逆动力学鸿沟。

**战略含义。** 关注能用执行成功而非视频指标训练生成模型的团队。

</div>

<div class="trend-card">

#### <span class="signal signal-c">C · 弱信号</span> 触觉开始进入 VLA 统一语义空间

**变化。** OmniVTLA 不再把触觉仅作为低层状态，而是与视觉、语言和动作对齐。

**对比。** 同比基线更多是触觉专用策略；本月出现 foundation-model 接口层的整合。

**证据。** [OmniVTLA: Vision-Tactile-Language-Action Models with Semantic-Aligned Tactile Sensing](https://arxiv.org/abs/2508.08706)

**成熟度与瓶颈。** 单团队早期信号。主要瓶颈是传感器异构、跨硬件标定和公开数据规模。

**战略含义。** 触觉价值可能先体现在接触失败恢复，而非通用语义理解。

</div>

<div class="trend-card">

#### <span class="signal signal-d">D · 反证/降温</span> 世界模型仍更像适配器，而非可靠规划器

**变化。** DiWA 与 GWM 展示适配和场景预测价值，但闭环规划收益、长时序误差和跨任务复现仍不充分。

**对比。** 论文数量上升快于控制证据升级。

**证据。** [DiWA: Diffusion Policy Adaptation with World Models](https://arxiv.org/abs/2508.03645)；[GWM: Towards Scalable Gaussian World Models for Robotic Manipulation](https://arxiv.org/abs/2508.17600)

**成熟度与瓶颈。** PoC 到早期验证。主要瓶颈是预测误差在闭环中的累积。

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
| [EO-1: An Open Unified Embodied Foundation Model for General Robot Control](https://arxiv.org/abs/2508.21112) | 2025-08-28 | 具身基础模型与通才策略 | EO-1 在统一 decoder 中结合自回归与 flow matching，以 EO-Data1.5M 做交错 vision-text-action 预训练，覆盖多本体长时序灵巧控制。 | 真机 · 跨本体 · 长时序 · 开放资产 |
| [DiWA: Diffusion Policy Adaptation with World Models](https://arxiv.org/abs/2508.03645) | 2025-08-05 | 策略学习与优化 | 用一次训练的离线世界模型承载 diffusion policy 的强化学习适配，避开数百万次真实交互，并在 CALVIN 与真实技能上验证。 | 真机 · 多任务 · 开放资产 |
| [RICL: Adding In-Context Adaptability to Pre-Trained Vision-Language-Action Models](https://arxiv.org/abs/2508.02062) | 2025-08-04 | 具身基础模型与通才策略 | 通过检索 10–20 条新任务示范，把 in-context adaptation 后置注入预训练 π0-FAST，无需参数更新即可快速教新任务。 | 多任务 · 开放资产 |
| [OmniVTLA: Vision-Tactile-Language-Action Models with Semantic-Aligned Tactile Sensing](https://arxiv.org/abs/2508.08706) | 2025-08-12 | 触觉、力觉与多模态身体感知 | 以双路触觉编码器和 135K 样本 ObjTac 对齐视觉、语言与多类触觉传感器，在夹爪和灵巧手真实任务上显著增益。 | 真机 · 开放资产 |
| [Video Generators are Robot Policies](https://arxiv.org/abs/2508.00795) | 2025-08-01 | 灵巧、双臂与接触操作 | 把机器人视频生成与动作生成端到端联合，显示无动作视频可在少量机器人示范下提升新物体、背景和任务的真实泛化。 | 真机 |
| [Masquerade: Learning from In-the-wild Human Videos using Data-Editing](https://arxiv.org/abs/2508.09976) | 2025-08-13 | 数据引擎与人类视频学习 | 把野外第一视角人类视频经 3D 手姿态、去人体和机器人叠加编辑为机器人化示范，675K 帧预训练后仅需每任务 50 条机器人示范。 | 长时序 |
| [GWM: Towards Scalable Gaussian World Models for Robotic Manipulation](https://arxiv.org/abs/2508.17600) | 2025-08-25 | 世界模型与预测控制 | 以 3D VAE、latent DiT 与 Gaussian Splatting 预测动作后的三维高斯场，既作表征预训练也作模型式 RL 的神经模拟器。 | 真机 |

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

---


## 2025 年 9 月研究雷达

> **统计口径。** 当前 15 个研究方向用于数量结构；7 篇精读样本用于实验与开放性指标。上月为 2025-08，同比月为 2024-09。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>469</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>5/7</strong><span>核验确认真机</span></div>
  <div class="radar-kpi"><strong>0</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

flow matching 正在成为通用策略的新执行底座；与此同时，在线搜索被塞进 VLA 推理环。

### 主题结构与环比

> 本表使用当前 15 个研究方向，只统计自动判为“直接候选”的记录。每篇论文只计一个主方向，环比同时展示绝对量和百分比。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>1,512</strong><span>当月 arXiv 母集</span></div>
  <div class="radar-kpi"><strong>469</strong><span>直接候选</span></div>
  <div class="radar-kpi"><strong>284</strong><span>边界候选</span></div>
  <div class="radar-kpi"><strong>288</strong><span>上月直接候选</span></div>
</div>

| 主方向 | 本月 | 占比 | 上月 | 环比增量 | 环比 |
|---|---:|---:|---:|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 47 | 10.0% | 26 | +21 | +80.8% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 34 | 7.2% | 25 | +9 | +36.0% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 13 | 2.8% | 10 | +3 | +30.0% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 46 | 9.8% | 22 | +24 | +109.1% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 70 | 14.9% | 66 | +4 | +6.1% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 32 | 6.8% | 12 | +20 | +166.7% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 32 | 6.8% | 21 | +11 | +52.4% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 124 | 26.4% | 66 | +58 | +87.9% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 16 | 3.4% | 9 | +7 | +77.8% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 17 | 3.6% | 12 | +5 | +41.7% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 25 | 5.3% | 12 | +13 | +108.3% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 8 | 1.7% | 4 | +4 | +100.0% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 1 | 0.2% | 0 | +1 | 新增 |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 3 | 0.6% | 2 | +1 | +50.0% |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 1 | 0.2% | 1 | 0 | 0.0% |
| **总计** | **469** | **100.0%** | **288** | **+181** | **+62.8%** |

跨月比较时，应先看绝对数量与独立论文簇，再用正式发表和 GitHub 采用证据判断是否从 arXiv 热点走向兑现。
### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> flow matching 正在成为通用策略的新执行底座

**变化。** ManiFlow、EC-Flow 与 FLOWER 在通用操控、无标签视频和轻量 generalist policy 三条线上同时采用 flow。

**对比。** 相比同比基线的 diffusion policy 主导，flow 的速度与连续控制优势开始跨团队扩散。

**证据。** [ManiFlow: A General Robot Manipulation Policy via Consistency Flow Training](https://arxiv.org/abs/2509.01819)；[EC-Flow: Enabling Versatile Robotic Manipulation from Action-Unlabeled Videos via Embodiment-Centric Flow](https://arxiv.org/abs/2507.06224)；[FLOWER: Democratizing Generalist Robot Policies with Efficient Vision-Language-Action Flow Policies](https://arxiv.org/abs/2509.04996)

**成熟度与瓶颈。** 多团队、跨月，但统一真机 benchmark 尚未形成。主要瓶颈是训练稳定性和闭环重规划。

**战略含义。** 基础设施层应支持 diffusion 与 flow 共存，而不是押注单一采样器。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 灵巧操作的数据表示从关节轨迹转向接触与第一视角

**变化。** OpenEgo、Text2Touch 与 CEDex 分别用 egocentric 数据、语言设计奖励和接触表示扩大灵巧操作监督。

**对比。** 本月信号不在更复杂的手，而在更可迁移的数据坐标系。

**证据。** [OpenEgo: A Large-Scale Multimodal Egocentric Dataset for Dexterous Manipulation](https://arxiv.org/abs/2509.05513)；[Text2Touch: Tactile In-Hand Manipulation with LLM-Designed Reward Functions](https://arxiv.org/abs/2509.07445)；[CEDex: Cross-Embodiment Dexterous Grasp Generation at Scale from Human-like Contact Representations](https://arxiv.org/abs/2509.24661)

**成熟度与瓶颈。** 数据与表示创新先于通用真机策略。主要瓶颈是接触标注成本与不同手型的对应关系。

**战略含义。** 长期价值更可能沉淀在接触数据协议与手型无关表示。

</div>

<div class="trend-card">

#### <span class="signal signal-c">C · 弱信号</span> 在线搜索被塞进 VLA 推理环

**变化。** VLA-Reasoner 用 online MCTS 把推理从一次性 chain-of-thought 变成动作候选搜索。

**对比。** 此前 reasoning 多是离线语义提示；这是面向执行验证的早期转向。

**证据。** [VLA-Reasoner: Empowering Vision-Language-Action Models with Reasoning via Online Monte Carlo Tree Search](https://arxiv.org/abs/2509.22643)

**成熟度与瓶颈。** 单项高新颖度工作。主要瓶颈是搜索延迟、奖励可信度与真实机器人安全探索。

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
| [OpenEgo: A Large-Scale Multimodal Egocentric Dataset for Dexterous Manipulation](https://arxiv.org/abs/2509.05513) | 2025-09-05 | 灵巧、双臂与接触操作 | OpenEgo 统一六个公开视频集为 1107 小时、290 任务、600+ 环境的手姿态与时间定位动作原语数据，服务灵巧 VLA 预训练。 | 开放资产 |
| [ManiFlow: A General Robot Manipulation Policy via Consistency Flow Training](https://arxiv.org/abs/2509.01819) | 2025-09-01 | 策略学习与优化 | ManiFlow 用 consistency flow 将高维动作生成压到 1–2 步，并在单臂、双臂与人形真实平台上验证多模态通用操作。 | 真机 · 多任务 |
| [Parse-Augment-Distill: Learning Generalizable Bimanual Visuomotor Policies from Single Human Video](https://arxiv.org/abs/2509.20286) | 2025-09-24 | 数据引擎与人类视频学习 | PAD 将单条人类视频解析成机器人关键点动作，用双臂任务与运动规划无仿真扩增，再蒸馏成可泛化视觉运动策略。 | 真机 · 多任务 |
| [VLA-Reasoner: Empowering Vision-Language-Action Models with Reasoning via Online Monte Carlo Tree Search](https://arxiv.org/abs/2509.22643) | 2025-09-26 | 具身基础模型与通才策略 | VLA-Reasoner 以世界模型 rollout、KDE 置信采样和 MCTS 为现成 VLA 增加测试时前瞻，在真实长时序任务上纠偏。 | 真机 · 长时序 |
| [Text2Touch: Tactile In-Hand Manipulation with LLM-Designed Reward Functions](https://arxiv.org/abs/2509.07445) | 2025-09-09 | 灵巧、双臂与接触操作 | Text2Touch 让 LLM 为 70+ 环境变量设计短奖励，经 sim-to-real 蒸馏在四指触觉手上完成多轴 in-hand rotation。 | 真机 |
| [Latent Action Pretraining Through World Modeling](https://arxiv.org/abs/2509.18428) | 2025-09-22 | 世界模型与预测控制 | LAWM 通过世界建模从无标签人/机器人视频学习 latent action，使较小模仿学习模型跨任务、环境与本体迁移。 | 真机 |
| [CEDex: Cross-Embodiment Dexterous Grasp Generation at Scale from Human-like Contact Representations](https://arxiv.org/abs/2509.24661) | 2025-09-29 | 灵巧、双臂与接触操作 | CEDex 用人类式接触表征、拓扑合并与 SDF 物理约束，把同一抓取先验扩展到任意形态的灵巧手并规模化生成数据。 | 跨本体 |

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

---


## 2025 年 10 月研究雷达

> **统计口径。** 当前 15 个研究方向用于数量结构；7 篇精读样本用于实验与开放性指标。上月为 2025-09，同比月为 2024-10。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>427</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>4/7</strong><span>核验确认真机</span></div>
  <div class="radar-kpi"><strong>0</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

fast–slow 从隐式分工变成显式训练目标；与此同时，视频驱动双臂学习成为数据规模化的第二战场。

### 主题结构与环比

> 本表使用当前 15 个研究方向，只统计自动判为“直接候选”的记录。每篇论文只计一个主方向，环比同时展示绝对量和百分比。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>1,348</strong><span>当月 arXiv 母集</span></div>
  <div class="radar-kpi"><strong>427</strong><span>直接候选</span></div>
  <div class="radar-kpi"><strong>241</strong><span>边界候选</span></div>
  <div class="radar-kpi"><strong>469</strong><span>上月直接候选</span></div>
</div>

| 主方向 | 本月 | 占比 | 上月 | 环比增量 | 环比 |
|---|---:|---:|---:|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 59 | 13.8% | 47 | +12 | +25.5% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 29 | 6.8% | 34 | -5 | -14.7% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 25 | 5.9% | 13 | +12 | +92.3% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 38 | 8.9% | 46 | -8 | -17.4% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 81 | 19.0% | 70 | +11 | +15.7% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 19 | 4.4% | 32 | -13 | -40.6% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 19 | 4.4% | 32 | -13 | -40.6% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 105 | 24.6% | 124 | -19 | -15.3% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 3 | 0.7% | 16 | -13 | -81.3% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 13 | 3.0% | 17 | -4 | -23.5% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 22 | 5.2% | 25 | -3 | -12.0% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 11 | 2.6% | 8 | +3 | +37.5% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 0 | 0.0% | 1 | -1 | -100.0% |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 3 | 0.7% | 3 | 0 | 0.0% |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 0 | 0.0% | 1 | -1 | -100.0% |
| **总计** | **427** | **100.0%** | **469** | **-42** | **-9.0%** |

跨月比较时，应先看绝对数量与独立论文簇，再用正式发表和 GitHub 采用证据判断是否从 arXiv 热点走向兑现。
### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> fast–slow 从隐式分工变成显式训练目标

**变化。** VLA-R1、MoTVLA 与上月 VLA-Reasoner 分别用推理增强、统一快慢推理和在线搜索建立高层思考—低层动作分工。

**对比。** 相较 7 月的架构试验，已有三个独立作者团队连续出现。

**证据。** [VLA-R1: Enhancing Reasoning in Vision-Language-Action Models](https://arxiv.org/abs/2510.01623)；[MoTVLA: A Vision-Language-Action Model with Unified Fast-Slow Reasoning](https://arxiv.org/abs/2510.18337)；[VLA-Reasoner: Empowering Vision-Language-Action Models with Reasoning via Online Monte Carlo Tree Search](https://arxiv.org/abs/2509.22643)

**成熟度与瓶颈。** 新兴架构簇，真实机器人延迟与失败恢复仍待验证。主要瓶颈是推理 token 与控制频率的冲突。

**战略含义。** 大小脑的竞争焦点将从模型大小转向调度、验证与恢复。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 世界模型开始进入 VLA 后训练

**变化。** VLA-RFT 用 world simulator 给可验证奖励，Ctrl-World 强调可控生成，Latent Action Pretraining 则把预测表征回流到动作学习。

**对比。** 8 月还以适配为主，本月开始直接改变策略训练目标。

**证据。** [VLA-RFT: Vision-Language-Action Reinforcement Fine-tuning with Verified Rewards in World Simulators](https://arxiv.org/abs/2510.00406)；[Ctrl-World: A Controllable Generative World Model for Robot Manipulation](https://arxiv.org/abs/2510.10125)；[Latent Action Pretraining Through World Modeling](https://arxiv.org/abs/2509.18428)

**成熟度与瓶颈。** 训练闭环已经出现，仿真偏差仍高。主要瓶颈是奖励投机与 simulator bias。

**战略含义。** 优先看同时报告模型预测质量和策略真实成功率的工作。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 视频驱动双臂学习成为数据规模化的第二战场

**变化。** DexMan、Parse-Augment-Distill 与真实人类活动视频预训练共同指向少机器人示教的双臂学习。

**对比。** 从 7 月单项数据转换扩散为生成视频、单视频蒸馏和大规模人类活动三类路线。

**证据。** [DexMan: Learning Bimanual Dexterous Manipulation from Human and Generated Videos](https://arxiv.org/abs/2510.08475)；[Parse-Augment-Distill: Learning Generalizable Bimanual Visuomotor Policies from Single Human Video](https://arxiv.org/abs/2509.20286)；[Scalable Vision-Language-Action Model Pretraining for Robotic Manipulation with Real-Life Human Activity Videos](https://arxiv.org/abs/2510.21571)

**成熟度与瓶颈。** 多团队验证，硬件与任务覆盖仍有限。主要瓶颈是双臂同步、遮挡和接触力缺失。

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
| [X-VLA: Soft-Prompted Transformer as Scalable Cross-Embodiment Vision-Language-Action Model](https://arxiv.org/abs/2510.10274) | 2025-10-11 | 策略学习与优化 | X-VLA 用每个数据源的软提示吸收跨本体异构数据，在 6 个仿真与 3 台真实机器人上兼顾灵巧性、适配速度和规模化。 | 真机 · 跨本体 |
| [Scalable Vision-Language-Action Model Pretraining for Robotic Manipulation with Real-Life Human Activity Videos](https://arxiv.org/abs/2510.21571) | 2025-10-24 | 具身基础模型与通才策略 | 将无脚本真实人类手部视频自动切分、描述并恢复 3D 动作，构成 100 万 episode/2600 万帧的 hand-VLA 预训练语料。 | 真机 · 多任务 |
| [VLA-R1: Enhancing Reasoning in Vision-Language-Action Models](https://arxiv.org/abs/2510.01623) | 2025-10-02 | 具身基础模型与通才策略 | VLA-R1 用 RLVR/GRPO 与 13K 条 affordance-trajectory CoT 数据共同强化空间推理和动作执行，并覆盖仿真与真实机器人。 | 真机 |
| [Ctrl-World: A Controllable Generative World Model for Robot Manipulation](https://arxiv.org/abs/2510.10125) | 2025-10-11 | 世界模型与预测控制 | Ctrl-World 以多视角预测、逐帧动作条件和姿态记忆支持通用策略的长时序 imagination rollout，用于低成本评估和改进。 | 长时序 |
| [MoTVLA: A Vision-Language-Action Model with Unified Fast-Slow Reasoning](https://arxiv.org/abs/2510.18337) | 2025-10-21 | 具身基础模型与通才策略 | MoTVLA 让预训练 VLM 承担慢速语义规划、专用 transformer 生成快速运动分解，再驱动 action expert 实时执行。 | 真机 |
| [VLA-RFT: Vision-Language-Action Reinforcement Fine-tuning with Verified Rewards in World Simulators](https://arxiv.org/abs/2510.00406) | 2025-10-01 | 具身基础模型与通才策略 | VLA-RFT 把真实交互训练的动作条件世界模型当可控模拟器，以可验证轨迹奖励在少于 400 步内完成 VLA 强化微调。 | 摘要未确认 |
| [DexMan: Learning Bimanual Dexterous Manipulation from Human and Generated Videos](https://arxiv.org/abs/2510.08475) | 2025-10-09 | 灵巧、双臂与接触操作 | DexMan 从无标定第三视角人类或生成视频估计手物运动，以接触奖励在仿真人形机器人上学习双臂灵巧技能。 | 摘要未确认 |

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

---


## 2025 年 11 月研究雷达

> **统计口径。** 当前 15 个研究方向用于数量结构；7 篇精读样本用于实验与开放性指标。上月为 2025-10，同比月为 2024-11。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>347</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>5/7</strong><span>核验确认真机</span></div>
  <div class="radar-kpi"><strong>1</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

世界模型终于开始用规划成功率证明自己；与此同时，VLA 开始从示范学习走向“从经验学习”。

### 主题结构与环比

> 本表使用当前 15 个研究方向，只统计自动判为“直接候选”的记录。每篇论文只计一个主方向，环比同时展示绝对量和百分比。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>1,162</strong><span>当月 arXiv 母集</span></div>
  <div class="radar-kpi"><strong>347</strong><span>直接候选</span></div>
  <div class="radar-kpi"><strong>203</strong><span>边界候选</span></div>
  <div class="radar-kpi"><strong>427</strong><span>上月直接候选</span></div>
</div>

| 主方向 | 本月 | 占比 | 上月 | 环比增量 | 环比 |
|---|---:|---:|---:|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 48 | 13.8% | 59 | -11 | -18.6% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 24 | 6.9% | 29 | -5 | -17.2% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 19 | 5.5% | 25 | -6 | -24.0% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 32 | 9.2% | 38 | -6 | -15.8% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 58 | 16.7% | 81 | -23 | -28.4% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 16 | 4.6% | 19 | -3 | -15.8% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 19 | 5.5% | 19 | 0 | 0.0% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 87 | 25.1% | 105 | -18 | -17.1% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 8 | 2.3% | 3 | +5 | +166.7% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 13 | 3.7% | 13 | 0 | 0.0% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 16 | 4.6% | 22 | -6 | -27.3% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 4 | 1.2% | 11 | -7 | -63.6% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 1 | 0.3% | 0 | +1 | 新增 |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 1 | 0.3% | 3 | -2 | -66.7% |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 1 | 0.3% | 0 | +1 | 新增 |
| **总计** | **347** | **100.0%** | **427** | **-80** | **-18.7%** |

跨月比较时，应先看绝对数量与独立论文簇，再用正式发表和 GitHub 采用证据判断是否从 arXiv 热点走向兑现。
### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> 世界模型终于开始用规划成功率证明自己

**变化。** WorldPlanner 把 action-conditioned visual world model 接入 MCTS/MPC；跨本体灵巧世界模型与 Ctrl-World 构成独立跟进。

**对比。** 比 8 月的生成/适配信号更接近闭环决策，但仍缺正式评审与规模化真机验证。

**证据。** [WorldPlanner: Monte Carlo Tree Search and MPC with Action-Conditioned Visual World Models](https://arxiv.org/abs/2511.03077)；[Scaling Cross-Embodiment World Models for Dexterous Manipulation](https://arxiv.org/abs/2511.01177)；[Ctrl-World: A Controllable Generative World Model for Robot Manipulation](https://arxiv.org/abs/2510.10125)

**成熟度与瓶颈。** 闭环 PoC。主要瓶颈是长时预测误差和规划计算量。

**战略含义。** 世界模型团队的关键里程碑应是同算力下的控制收益。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 跨本体迁移从模型适配转向数据分布设计

**变化。** X-Diffusion、InternData-A1 与 X-VLA 分别统一人类示范、合成数据和软提示式跨本体策略。

**对比。** 相比“为每台机器人做 adapter”，本月更多工作试图在数据和动作空间层消除本体差异。

**证据。** [X-Diffusion: Training Diffusion Policies on Cross-Embodiment Human Demonstrations](https://arxiv.org/abs/2511.04671)；[InternData-A1: Pioneering High-Fidelity Synthetic Data for Pre-training Generalist Policy](https://arxiv.org/abs/2511.16651)；[X-VLA: Soft-Prompted Transformer as Scalable Cross-Embodiment Vision-Language-Action Model](https://arxiv.org/abs/2510.10274)

**成熟度与瓶颈。** 多路线并行，尚无统一跨本体 benchmark。主要瓶颈是动作坐标标准、硬件观测差异和负迁移。

**战略含义。** 跨本体数据协议可能比单一 VLA 权重更具平台价值。

</div>

<div class="trend-card">

#### <span class="signal signal-c">C · 弱信号</span> VLA 开始从示范学习走向“从经验学习”

**变化。** π*0.6 明确强调 experience learning，与 VLA-RFT 的可验证奖励形成呼应。

**对比。** 共识仍是离线模仿；在线经验闭环尚属少数。

**证据。** [$π^{*}_{0.6}$: a VLA That Learns From Experience](https://arxiv.org/abs/2511.14759)；[VLA-RFT: Vision-Language-Action Reinforcement Fine-tuning with Verified Rewards in World Simulators](https://arxiv.org/abs/2510.00406)

**成熟度与瓶颈。** 两个高信号项目，独立复现弱。主要瓶颈是真实机器人安全探索和奖励设计。

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
| [InternData-A1: Pioneering High-Fidelity Synthetic Data for Pre-training Generalist Policy](https://arxiv.org/abs/2511.16651) | 2025-11-20 | 具身基础模型与通才策略 | InternData-A1 以自动仿真流水线生成 63 万轨迹/7433 小时、4 本体/70 任务数据，报告纯合成预训练可匹配 π0 并零样本 sim-to-real。 | 真机 · 多任务 · 跨本体 · 长时序 · 开放资产 |
| [Scaling Cross-Embodiment World Models for Dexterous Manipulation](https://arxiv.org/abs/2511.01177) | 2025-11-03 | 灵巧、双臂与接触操作 | 把不同人手/机器人手统一为 3D 粒子与末端位移场，以跨本体世界模型和 MPC 在新硬件上迁移刚体及柔性操作。 | 真机 · 跨本体 |
| [WorldPlanner: Monte Carlo Tree Search and MPC with Action-Conditioned Visual World Models](https://arxiv.org/abs/2511.03077) | 2025-11-04 | 世界模型与预测控制 | WorldPlanner 用数小时无结构 play data 学动作条件视频世界模型、动作采样器和可选奖励，再以 MCTS+MPC 在真实机器人上规划。 | 真机 · 长时序 |
| [X-Diffusion: Training Diffusion Policies on Cross-Embodiment Human Demonstrations](https://arxiv.org/abs/2511.04671) | 2025-11-06 | 策略学习与优化 | X-Diffusion 将人类动作视为机器人动作的噪声对应物，只在高噪声层引入跨本体人类示范，五个真实任务平均提升 16%。 | 真机 · 跨本体 |
| [Dexterous Robotic Piano Playing at Scale](https://arxiv.org/abs/2511.02504) | 2025-11-04 | 灵巧、双臂与接触操作 | OmniPianist 训练 2000+ 专项 RL 智能体并汇成百万轨迹 RP1M++，再以 flow transformer 蒸馏出覆盖近千曲目的双手策略。 | 多任务 |
| [$π^{*}_{0.6}$: a VLA That Learns From Experience](https://arxiv.org/abs/2511.14759) | 2025-11-18 | 具身基础模型与通才策略 | RECAP 把示范、在线 rollout 与专家纠正统一为 advantage-conditioned VLA 强化学习，使 π*0.6 在家庭与商业设备任务中持续改进。 | 真机 |
| [DualVLA: Building a Generalizable Embodied Agent via Partial Decoupling of Reasoning and Action](https://arxiv.org/abs/2511.22134) | 2025-11-27 | 具身基础模型与通才策略 | DualVLA 通过双层数据裁剪与双教师蒸馏缓解推理微调导致的动作退化，并提出按 reasoning/intention/action/alignment 分解的 VLA Score。 | 摘要未确认 |

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

---


## 2025 年 12 月研究雷达

> **统计口径。** 当前 15 个研究方向用于数量结构；7 篇精读样本用于实验与开放性指标。上月为 2025-11，同比月为 2024-12。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>299</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>5/7</strong><span>核验确认真机</span></div>
  <div class="radar-kpi"><strong>2</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

世界模型与搜索/规划形成方法簇；与此同时，低成本示范采集与合成开始合流。

### 主题结构与环比

> 本表使用当前 15 个研究方向，只统计自动判为“直接候选”的记录。每篇论文只计一个主方向，环比同时展示绝对量和百分比。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>1,122</strong><span>当月 arXiv 母集</span></div>
  <div class="radar-kpi"><strong>299</strong><span>直接候选</span></div>
  <div class="radar-kpi"><strong>230</strong><span>边界候选</span></div>
  <div class="radar-kpi"><strong>347</strong><span>上月直接候选</span></div>
</div>

| 主方向 | 本月 | 占比 | 上月 | 环比增量 | 环比 |
|---|---:|---:|---:|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 46 | 15.4% | 48 | -2 | -4.2% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 22 | 7.4% | 24 | -2 | -8.3% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 29 | 9.7% | 19 | +10 | +52.6% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 18 | 6.0% | 32 | -14 | -43.8% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 38 | 12.7% | 58 | -20 | -34.5% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 19 | 6.4% | 16 | +3 | +18.8% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 20 | 6.7% | 19 | +1 | +5.3% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 75 | 25.1% | 87 | -12 | -13.8% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 10 | 3.3% | 8 | +2 | +25.0% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 7 | 2.3% | 13 | -6 | -46.2% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 10 | 3.3% | 16 | -6 | -37.5% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 4 | 1.3% | 4 | 0 | 0.0% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 0 | 0.0% | 1 | -1 | -100.0% |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 0 | 0.0% | 1 | -1 | -100.0% |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 1 | 0.3% | 1 | 0 | 0.0% |
| **总计** | **299** | **100.0%** | **347** | **-48** | **-13.8%** |

跨月比较时，应先看绝对数量与独立论文簇，再用正式发表和 GitHub 采用证据判断是否从 arXiv 热点走向兑现。
### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> 世界模型与搜索/规划形成方法簇

**变化。** Motus、Large Video Planner、STORM 与 WorldPlanner 从统一 latent action、视频规划器和 search-guided generation 三路汇合。

**对比。** 这是全年首次在同月出现三项以上、不同作者团队的 planning-oriented world model。

**证据。** [Motus: A Unified Latent Action World Model](https://arxiv.org/abs/2512.13030)；[Large Video Planner Enables Generalizable Robot Control](https://arxiv.org/abs/2512.15840)；[STORM: Search-Guided Generative World Models for Robotic Manipulation](https://arxiv.org/abs/2512.18477)；[WorldPlanner: Monte Carlo Tree Search and MPC with Action-Conditioned Visual World Models](https://arxiv.org/abs/2511.03077)

**成熟度与瓶颈。** 研究密度高，同行评审滞后明显。主要瓶颈是可执行性校验与长时 roll-out 漂移。

**战略含义。** 2026 年应观察这批工作能否转化为真实机器人闭环收益。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 双系统跨出 manipulation，开始覆盖导航与视频策略

**变化。** Video2Act、Ground Slow Move Fast 与 DualVLA 显示快慢分工可跨视频策略、导航和通用代理。

**对比。** 10 月主要是 VLA 内部推理；本月开始形成跨任务架构语言。

**证据。** [Video2Act: A Dual-System Video Diffusion Policy with Robotic Spatio-Motional Modeling](https://arxiv.org/abs/2512.03044)；[Ground Slow, Move Fast: A Dual-System Foundation Model for Generalizable Vision-and-Language Navigation](https://arxiv.org/abs/2512.08186)；[DualVLA: Building a Generalizable Embodied Agent via Partial Decoupling of Reasoning and Action](https://arxiv.org/abs/2511.22134)

**成熟度与瓶颈。** 跨任务概念扩散，统一实验标准缺失。主要瓶颈是不同任务的时钟频率和状态抽象不统一。

**战略含义。** 双系统价值在于复用调度框架，而非统一一个超大模型。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 低成本示范采集与合成开始合流

**变化。** RoboWheel、One-Shot Demonstration Synthesis 和 InternData-A1 覆盖真实人类示范、单样本合成与高保真合成预训练。

**对比。** 数据规模化从单一 teleoperation 扩展为真实—合成混合流水线。

**证据。** [RoboWheel: A Data Engine from Real-World Human Demonstrations for Cross-Embodiment Robotic Learning](https://arxiv.org/abs/2512.02729)；[One-Shot Real-World Demonstration Synthesis for Scalable Bimanual Manipulation](https://arxiv.org/abs/2512.09297)；[InternData-A1: Pioneering High-Fidelity Synthetic Data for Pre-training Generalist Policy](https://arxiv.org/abs/2511.16651)

**成熟度与瓶颈。** 数据引擎成形，但跨团队采用尚未验证。主要瓶颈是数据质量过滤与许可合规。

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
| [Motus: A Unified Latent Action World Model](https://arxiv.org/abs/2512.13030) | 2025-12-15 | 世界模型与预测控制 | Motus 用 MoT 统一理解、视频生成和动作专家，并以 optical-flow latent action 支持世界模型、VLA、逆动力学等多种模式。 | 真机 |
| [Large Video Planner Enables Generalizable Robot Control](https://arxiv.org/abs/2512.15840) | 2025-12-17 | 具身基础模型与通才策略 | 以互联网规模人类活动视频预训练开放视频规划器，零样本生成新场景任务的视频计划并后处理为可执行真实机器人动作。 | 真机 · 多任务 · 开放资产 |
| [Ground Slow, Move Fast: A Dual-System Foundation Model for Generalizable Vision-and-Language Navigation](https://arxiv.org/abs/2512.08186) | 2025-12-09 | 分层推理、规划与记忆 | DualVLN 让 VLM 全局规划器慢速生成中程像素目标，轻量 diffusion transformer 快速输出连续轨迹，在真实动态环境实现长时序导航。 | 真机 · 长时序 |
| [One-Shot Real-World Demonstration Synthesis for Scalable Bimanual Manipulation](https://arxiv.org/abs/2512.09297) | 2025-12-10 | 灵巧、双臂与接触操作 | BiDemoSyn 从一条真实示范分解协调不变量与对象相关调整，数小时合成数千条双臂接触轨迹，并展示新平台零样本迁移。 | 真机 · 跨本体 |
| [RoboWheel: A Data Engine from Real-World Human Demonstrations for Cross-Embodiment Robotic Learning](https://arxiv.org/abs/2512.02729) | 2025-12-02 | 策略学习与优化 | RoboWheel 将单目/RGB-D 人类手物视频重建为物理可行接触轨迹，再重定向到夹爪、灵巧手和人形本体并做仿真扩增。 | 跨本体 |
| [Video2Act: A Dual-System Video Diffusion Policy with Robotic Spatio-Motional Modeling](https://arxiv.org/abs/2512.03044) | 2025-12-02 | 策略学习与优化 | Video2Act 以视频扩散模型作低频慢系统、DiT 动作头作快速系统，通过空间边界与跨帧运动条件提升真实任务成功率。 | 真机 |
| [STORM: Search-Guided Generative World Models for Robotic Manipulation](https://arxiv.org/abs/2512.18477) | 2025-12-20 | 世界模型与预测控制 | STORM 让 diffusion VLA 提议动作、视频世界模型预测结果、MCTS 搜索与重规划，在 SimplerEnv 达到 51.0% 平均成功率。 | 长时序 |

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

---


## 2026 年 1 月研究雷达

> **统计口径。** 当前 15 个研究方向用于数量结构；7 篇精读样本用于实验与开放性指标。上月为 2025-12，同比月为 2025-01。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>280</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>3/7</strong><span>核验确认真机</span></div>
  <div class="radar-kpi"><strong>4</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

latent action world model 从实验室走向 in-the-wild；与此同时，人类中心数据被推到跨本体预训练主线。

### 主题结构与环比

> 本表使用当前 15 个研究方向，只统计自动判为“直接候选”的记录。每篇论文只计一个主方向，环比同时展示绝对量和百分比。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>979</strong><span>当月 arXiv 母集</span></div>
  <div class="radar-kpi"><strong>280</strong><span>直接候选</span></div>
  <div class="radar-kpi"><strong>160</strong><span>边界候选</span></div>
  <div class="radar-kpi"><strong>299</strong><span>上月直接候选</span></div>
</div>

| 主方向 | 本月 | 占比 | 上月 | 环比增量 | 环比 |
|---|---:|---:|---:|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 30 | 10.7% | 46 | -16 | -34.8% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 15 | 5.4% | 22 | -7 | -31.8% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 21 | 7.5% | 29 | -8 | -27.6% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 27 | 9.6% | 18 | +9 | +50.0% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 37 | 13.2% | 38 | -1 | -2.6% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 16 | 5.7% | 19 | -3 | -15.8% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 25 | 8.9% | 20 | +5 | +25.0% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 72 | 25.7% | 75 | -3 | -4.0% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 7 | 2.5% | 10 | -3 | -30.0% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 14 | 5.0% | 7 | +7 | +100.0% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 14 | 5.0% | 10 | +4 | +40.0% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 1 | 0.4% | 4 | -3 | -75.0% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 0 | 0.0% | 0 | 0 | — |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 1 | 0.4% | 0 | +1 | 新增 |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 0 | 0.0% | 1 | -1 | -100.0% |
| **总计** | **280** | **100.0%** | **299** | **-19** | **-6.4%** |

跨月比较时，应先看绝对数量与独立论文簇，再用正式发表和 GitHub 采用证据判断是否从 arXiv 热点走向兑现。
### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> latent action world model 从实验室走向 in-the-wild

**变化。** Learning Latent Action World Models In The Wild、Cosmos Policy 与 Motus 分别覆盖野外视频、视频模型微调和统一 latent action。

**对比。** 12 月强调搜索，本月强调如何从开放视频获得可执行潜变量。

**证据。** [Learning Latent Action World Models In The Wild](https://arxiv.org/abs/2601.05230)；[Cosmos Policy: Fine-Tuning Video Models for Visuomotor Control and Planning](https://arxiv.org/abs/2601.16163)；[Motus: A Unified Latent Action World Model](https://arxiv.org/abs/2512.13030)

**成熟度与瓶颈。** 跨月多团队，真实环境可控性仍弱。主要瓶颈是动作语义不可辨识和时序对齐。

**战略含义。** 把 inverse dynamics 与可执行性奖励视为核心能力，而非附属模块。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> Action CoT 与非对称专家正在重写大小脑接口

**变化。** ACoT-VLA、TwinBrainVLA 与 DualVLA 从动作链推理、非对称混合专家和部分解耦三种方式定义高低层接口。

**对比。** 相比显式 planner 调 policy，这些工作更倾向于可联合训练的内部接口。

**证据。** [ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://arxiv.org/abs/2601.11404)；[TwinBrainVLA: Unleashing the Potential of Generalist VLMs for Embodied Tasks via Asymmetric Mixture-of-Transformers](https://arxiv.org/abs/2601.14133)；[DualVLA: Building a Generalizable Embodied Agent via Partial Decoupling of Reasoning and Action](https://arxiv.org/abs/2511.22134)

**成熟度与瓶颈。** 架构簇形成，实时性尚未标准化。主要瓶颈是慢分支是否真的提升成功率而非只增加计算。

**战略含义。** 需要按任务难度自适应启用慢推理。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> 人类中心数据被推到跨本体预训练主线

**变化。** Being-H0.5、RoboWheel 和 InternData-A1 都把人类数据转化为 generalist policy 的可扩展监督。

**对比。** 2025 年的零散数据编辑开始收敛为预训练数据栈。

**证据。** [Being-H0.5: Scaling Human-Centric Robot Learning for Cross-Embodiment Generalization](https://arxiv.org/abs/2601.12993)；[RoboWheel: A Data Engine from Real-World Human Demonstrations for Cross-Embodiment Robotic Learning](https://arxiv.org/abs/2512.02729)；[InternData-A1: Pioneering High-Fidelity Synthetic Data for Pre-training Generalist Policy](https://arxiv.org/abs/2511.16651)

**成熟度与瓶颈。** 模型规模化信号明确，独立机器人平台验证仍有限。主要瓶颈是人类动作与机器人动力学不一致。

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
| [ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://arxiv.org/abs/2601.11404) | 2026-01-16 | 具身基础模型与通才策略 | 把 Chain-of-Thought 直接落在动作空间，以显式粗轨迹和隐式动作先验共同条件化下游动作头，缩短语义推理到连续控制的距离。 | 真机 · 开放资产 |
| [UniBiDex: A Unified Teleoperation Framework for Robotic Bimanual Dexterous Manipulation](https://arxiv.org/abs/2601.04629) | 2026-01-08 | 灵巧、双臂与接触操作 | 统一 VR 与主从式输入，在共享控制栈中加入零空间避碰和奇异规避，为双臂灵巧操作提供可开源的数据采集底座。 | 多任务 · 长时序 · 开放资产 |
| [Cosmos Policy: Fine-Tuning Video Models for Visuomotor Control and Planning](https://arxiv.org/abs/2601.16163) | 2026-01-22 | 世界模型与预测控制 | 用单阶段后训练把预训练视频模型直接改造成动作、未来状态和价值联合生成器，并以测试时规划提升双臂真实任务表现。 | 真机 · 开放资产 |
| [Green-VLA: Staged Vision-Language-Action Model for Generalist Robots](https://arxiv.org/abs/2602.00919) | 2026-01-31 | 具身基础模型与通才策略 | 以五阶段课程、3,000 小时示范和统一的本体感知动作接口，把 VLM grounding、多本体预训练、单本体适配与 RL 对齐串成可部署的 generalist VLA。 | 真机 · 跨本体 · 长时序 |
| [Being-H0.5: Scaling Human-Centric Robot Learning for Cross-Embodiment Generalization](https://arxiv.org/abs/2601.12993) | 2026-01-19 | 策略学习与优化 | 以 35,000 小时、30 种本体的 UniHand-2.0 和统一动作空间训练人类中心 VLA，并用 Mixture-of-Flow 分离共享运动原语与本体专家。 | 多任务 · 跨本体 |
| [Learning Latent Action World Models In The Wild](https://arxiv.org/abs/2601.05230) | 2026-01-08 | 世界模型与预测控制 | 从无动作标注的 in-the-wild 视频学习受约束连续 latent actions，并用控制器映射已知动作以支持世界模型规划。 | 摘要未确认 |
| [TwinBrainVLA: Unleashing the Potential of Generalist VLMs for Embodied Tasks via Asymmetric Mixture-of-Transformers](https://arxiv.org/abs/2601.14133) | 2026-01-20 | 具身基础模型与通才策略 | 以冻结 generalist VLM 与可训练 specialist VLM 构成双路径，通过 AsyMoT 查询未被破坏的语义能力并驱动 flow-matching 动作专家。 | 摘要未确认 |

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

---


## 2026 年 2 月研究雷达

> **统计口径。** 当前 15 个研究方向用于数量结构；7 篇精读样本用于实验与开放性指标。上月为 2026-01，同比月为 2025-02。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>466</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>5/7</strong><span>核验确认真机</span></div>
  <div class="radar-kpi"><strong>0</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

世界模型开始承担 RL 模拟器与在线自纠错；与此同时，egocentric 数据开始真正服务灵巧规模化。

### 主题结构与环比

> 本表使用当前 15 个研究方向，只统计自动判为“直接候选”的记录。每篇论文只计一个主方向，环比同时展示绝对量和百分比。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>1,392</strong><span>当月 arXiv 母集</span></div>
  <div class="radar-kpi"><strong>466</strong><span>直接候选</span></div>
  <div class="radar-kpi"><strong>263</strong><span>边界候选</span></div>
  <div class="radar-kpi"><strong>280</strong><span>上月直接候选</span></div>
</div>

| 主方向 | 本月 | 占比 | 上月 | 环比增量 | 环比 |
|---|---:|---:|---:|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 74 | 15.9% | 30 | +44 | +146.7% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 24 | 5.2% | 15 | +9 | +60.0% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 41 | 8.8% | 21 | +20 | +95.2% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 49 | 10.5% | 27 | +22 | +81.5% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 87 | 18.7% | 37 | +50 | +135.1% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 22 | 4.7% | 16 | +6 | +37.5% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 25 | 5.4% | 25 | 0 | 0.0% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 91 | 19.5% | 72 | +19 | +26.4% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 12 | 2.6% | 7 | +5 | +71.4% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 13 | 2.8% | 14 | -1 | -7.1% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 23 | 4.9% | 14 | +9 | +64.3% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 4 | 0.9% | 1 | +3 | +300.0% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 0 | 0.0% | 0 | 0 | — |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 0 | 0.0% | 1 | -1 | -100.0% |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 1 | 0.2% | 0 | +1 | 新增 |
| **总计** | **466** | **100.0%** | **280** | **+186** | **+66.4%** |

跨月比较时，应先看绝对数量与独立论文簇，再用正式发表和 GitHub 采用证据判断是否从 arXiv 热点走向兑现。
### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> 世界模型开始承担 RL 模拟器与在线自纠错

**变化。** WoVR、Self-Correcting VLA 与 World-Gymnast 分别用于后训练模拟、稀疏想象修正和世界模型内 RL。

**对比。** 相比 2025 年底的离线规划，这是一轮更靠近策略优化的迁移。

**证据。** [WoVR: World Models as Reliable Simulators for Post-Training VLA Policies with RL](https://arxiv.org/abs/2602.13977)；[Self-Correcting VLA: Online Action Refinement via Sparse World Imagination](https://arxiv.org/abs/2602.21633)；[World-Gymnast: Training Robots with Reinforcement Learning in a World Model](https://arxiv.org/abs/2602.02454)

**成熟度与瓶颈。** 多团队新兴趋势，真实机器人长期稳定性未确认。主要瓶颈是模型偏差会被 RL 放大。

**战略含义。** 验证时需报告 simulator exploitation 和真机回归测试。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 快慢系统开始感知力、接触与完成状态

**变化。** FAVLA 将力适应写入 fast–slow 架构，StreamVLA 用 completion-state gating 打破固定 reason–act 循环，自纠错框架补上终止判断。

**对比。** 双系统从“多想一步”转向“何时想、何时停、何时改动作”。

**证据。** [FAVLA: A Force-Adaptive Fast-Slow VLA model for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2602.23648)；[StreamVLA: Breaking the Reason-Act Cycle via Completion-State Gating](https://arxiv.org/abs/2602.01100)；[From Knowing to Doing Precisely: A General Self-Correction and Termination Framework for VLA models](https://arxiv.org/abs/2602.01811)

**成熟度与瓶颈。** 接口创新明显，跨平台复现不足。主要瓶颈是事件触发器的误报与控制抖动。

**战略含义。** 调度器、状态估计和 verifier 将成为独立技术层。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> egocentric 数据开始真正服务灵巧规模化

**变化。** EgoScale、Joint-Aligned Latent Action 与 Being-H0.5 把第一视角人类数据接入灵巧和跨本体预训练。

**对比。** 9 月 OpenEgo 还是数据集信号，本月已有训练管线和泛化目标。

**证据。** [EgoScale: Scaling Dexterous Manipulation with Diverse Egocentric Human Data](https://arxiv.org/abs/2602.16710)；[Joint-Aligned Latent Action: Towards Scalable VLA Pretraining in the Wild](https://arxiv.org/abs/2602.21736)；[Being-H0.5: Scaling Human-Centric Robot Learning for Cross-Embodiment Generalization](https://arxiv.org/abs/2601.12993)

**成熟度与瓶颈。** 数据规模化起步。主要瓶颈是手—物接触状态和第三维动作不可观测。

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
| [Xiaomi-Robotics-0: An Open-Sourced Vision-Language-Action Model with Real-Time Execution](https://arxiv.org/abs/2602.12684) | 2026-02-13 | 具身基础模型与通才策略 | 以跨本体预训练、异步执行训练和动作块时间对齐，让开放 VLA 在消费级 GPU 上实现平滑实时双臂控制。 | 真机 · 跨本体 · 开放资产 |
| [Self-Correcting VLA: Online Action Refinement via Sparse World Imagination](https://arxiv.org/abs/2602.21633) | 2026-02-25 | 具身基础模型与通才策略 | 以任务进度和未来轨迹趋势构成稀疏世界想象，再把预测状态转成密集奖励在线修正动作。 | 真机 · 开放资产 |
| [WoVR: World Models as Reliable Simulators for Post-Training VLA Policies with RL](https://arxiv.org/abs/2602.13977) | 2026-02-15 | 世界模型与预测控制 | 通过可控动作条件视频模型、关键帧初始化 rollout 和模型—策略共同演化，降低想象滚动的幻觉深度并用于 VLA 的 RL 后训练。 | 真机 · 跨本体 · 长时序 |
| [EgoScale: Scaling Dexterous Manipulation with Diverse Egocentric Human Data](https://arxiv.org/abs/2602.16710) | 2026-02-18 | 灵巧、双臂与接触操作 | 在 20,854 小时动作标注第一视角人类视频上建立 scaling law，并以轻量 human-robot mid-training 迁移到 22-DoF 灵巧手。 | 真机 · 跨本体 · 长时序 |
| [Joint-Aligned Latent Action: Towards Scalable VLA Pretraining in the Wild](https://arxiv.org/abs/2602.21736) | 2026-02-25 | 世界模型与预测控制 | 以逆动力学和真实动作联合对齐 latent action，在 7.5M 段、2,000 多小时人类视频上预训练可迁移的行为表征。 | 真机 |
| [StemVLA:An Open-Source Vision-Language-Action Model with Future 3D Spatial Geometry Knowledge and 4D Historical Representation](https://arxiv.org/abs/2602.23721) | 2026-02-27 | 具身基础模型与通才策略 | 把未来 3D 几何预测与历史 4D 时空表征同时注入动作生成，使 VLA 显式建模场景动态与空间结构。 | 长时序 |
| [FAVLA: A Force-Adaptive Fast-Slow VLA model for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2602.23648) | 2026-02-27 | 具身基础模型与通才策略 | 将低频 VLM 感知规划与高频力反馈动作专家解耦，并根据预测的力变化动态调度控制频率。 | 摘要未确认 |

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

---


## 2026 年 3 月研究雷达

> **统计口径。** 当前 15 个研究方向用于数量结构；7 篇精读样本用于实验与开放性指标。上月为 2026-02，同比月为 2025-03。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>694</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>5/7</strong><span>核验确认真机</span></div>
  <div class="radar-kpi"><strong>3</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

world model 的新门槛是“动作可执行”；与此同时，论文量激增，但不能把提交周期当成技术爆发。

### 主题结构与环比

> 本表使用当前 15 个研究方向，只统计自动判为“直接候选”的记录。每篇论文只计一个主方向，环比同时展示绝对量和百分比。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>1,949</strong><span>当月 arXiv 母集</span></div>
  <div class="radar-kpi"><strong>694</strong><span>直接候选</span></div>
  <div class="radar-kpi"><strong>386</strong><span>边界候选</span></div>
  <div class="radar-kpi"><strong>466</strong><span>上月直接候选</span></div>
</div>

| 主方向 | 本月 | 占比 | 上月 | 环比增量 | 环比 |
|---|---:|---:|---:|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 95 | 13.7% | 74 | +21 | +28.4% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 29 | 4.2% | 24 | +5 | +20.8% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 49 | 7.1% | 41 | +8 | +19.5% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 74 | 10.7% | 49 | +25 | +51.0% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 121 | 17.4% | 87 | +34 | +39.1% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 49 | 7.1% | 22 | +27 | +122.7% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 29 | 4.2% | 25 | +4 | +16.0% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 157 | 22.6% | 91 | +66 | +72.5% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 19 | 2.7% | 12 | +7 | +58.3% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 23 | 3.3% | 13 | +10 | +76.9% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 39 | 5.6% | 23 | +16 | +69.6% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 5 | 0.7% | 4 | +1 | +25.0% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 0 | 0.0% | 0 | 0 | — |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 3 | 0.4% | 0 | +3 | 新增 |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 2 | 0.3% | 1 | +1 | +100.0% |
| **总计** | **694** | **100.0%** | **466** | **+228** | **+48.9%** |

跨月比较时，应先看绝对数量与独立论文簇，再用正式发表和 GitHub 采用证据判断是否从 arXiv 热点走向兑现。
### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> world model 的新门槛是“动作可执行”

**变化。** EVA 用 inverse-dynamics rewards 对齐可执行动作，DreamPlan 用视频世界模型训练 planner，DIAL 用 latent world model 解耦 intent/action。

**对比。** 视频质量不再是主论据，策略可执行性成为共同评价轴。

**证据。** [EVA: Aligning Video World Models with Executable Robot Actions via Inverse Dynamics Rewards](https://arxiv.org/abs/2603.17808)；[DreamPlan: Efficient Reinforcement Fine-Tuning of Vision-Language Planners via Video World Models](https://arxiv.org/abs/2603.16860)；[DIAL: Decoupling Intent and Action via Latent World Modeling for End-to-End VLA](https://arxiv.org/abs/2603.29844)

**成熟度与瓶颈。** 三团队同时出现，评审与长期真机数据仍滞后。主要瓶颈是逆动力学奖励的偏差和闭环漂移。

**战略含义。** 这是比论文数量更重要的评价范式迁移。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 灵巧操作从单步抓取转向可观测的长时接触

**变化。** DexDrummer、UniDex 与 OmniVTA 分别覆盖长时演奏、通用手控制和视触觉世界模型。

**对比。** 相比早期 reward shaping，任务与感知都更接近连续接触闭环。

**证据。** [DexDrummer: In-Hand, Contact-Rich, and Long-Horizon Dexterous Robot Drumming](https://arxiv.org/abs/2603.22263)；[UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://arxiv.org/abs/2603.22264)；[OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2603.19201)

**成熟度与瓶颈。** 真实机器人证据增强，硬件可复制性仍有限。主要瓶颈是高频触觉、动作空间维度和设备差异。

**战略含义。** 优先跟踪“传感器—数据—策略”一体化团队。

</div>

<div class="trend-card">

#### <span class="signal signal-d">D · 反证/降温</span> 论文量激增，但不能把提交周期当成技术爆发

**变化。** 自动宽召回候选显著上升，基础模型命名占比最高；同期官方同行评审覆盖仍低。

**对比。** 增长既包含真实扩散，也受到会议周期与 VLA 命名泛化影响。

**证据。** [ManipArena: Comprehensive Real-world Evaluation of Reasoning-Oriented Generalist Robot Manipulation](https://arxiv.org/abs/2603.28545)；[DIAL: Decoupling Intent and Action via Latent World Modeling for End-to-End VLA](https://arxiv.org/abs/2603.29844)

**成熟度与瓶颈。** 数量强、质量分化。主要瓶颈是统一真机评测和独立复现。

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
| [UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://arxiv.org/abs/2603.22264) | 2026-03-23 | 数据引擎与人类视频学习 | 将 50K 轨迹、八种灵巧手、FAAS 统一动作空间、3D VLA 与便携采集装置组成 universal dexterous foundation suite。 | 摘要未确认 |
| [DexDrummer: In-Hand, Contact-Rich, and Long-Horizon Dexterous Robot Drumming](https://arxiv.org/abs/2603.22263) | 2026-03-23 | 灵巧、双臂与接触操作 | 以架子鼓把手内控制、反复接触和长时序双手协调合并为统一测试床，并用规划加 residual RL 实现 sim-to-real。 | 真机 · 多任务 · 长时序 |
| [ManipArena: Comprehensive Real-world Evaluation of Reasoning-Oriented Generalist Robot Manipulation](https://arxiv.org/abs/2603.28545) | 2026-03-30 | 具身基础模型与通才策略 | 用 20 个实体任务、10,812 条专家轨迹和成对 real-to-sim 场景，为 VLA/WAM 提供可诊断的统一真实机器人评测。 | 真机 · 多任务 |
| [EVA: Aligning Video World Models with Executable Robot Actions via Inverse Dynamics Rewards](https://arxiv.org/abs/2603.17808) | 2026-03-18 | 世界模型与预测控制 | 把 inverse dynamics model 反用作奖励模型，以速度、加速度、jerk 和本体约束对视频世界模型做可执行性对齐。 | 真机 |
| [OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2603.19201) | 2026-03-19 | 灵巧、双臂与接触操作 | 以 21K+ 轨迹、86 任务的视觉—触觉—动作数据训练双流世界模型，并用 60Hz 触觉反射闭环纠偏。 | 真机 |
| [DIAL: Decoupling Intent and Action via Latent World Modeling for End-to-End VLA](https://arxiv.org/abs/2603.29844) | 2026-03-31 | 世界模型与预测控制 | 用可微 latent intent bottleneck 连接 System-2 的未来表征与 System-1 的逆动力学控制，并以两阶段训练稳定端到端优化。 | 真机 |
| [DreamPlan: Efficient Reinforcement Fine-Tuning of Vision-Language Planners via Video World Models](https://arxiv.org/abs/2603.16860) | 2026-03-17 | 世界模型与预测控制 | 先用零样本 VLM 收集次优交互训练动作条件视频世界模型，再在想象 rollout 中强化微调高层 planner。 | 摘要未确认 |

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

---


## 2026 年 4 月研究雷达

> **统计口径。** 当前 15 个研究方向用于数量结构；7 篇精读样本用于实验与开放性指标。上月为 2026-03，同比月为 2025-04。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>392</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>4/7</strong><span>核验确认真机</span></div>
  <div class="radar-kpi"><strong>0</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

触觉与 world model 开始合流；与此同时，foundation model 开始接受垂直本体与可控行为约束。

### 主题结构与环比

> 本表使用当前 15 个研究方向，只统计自动判为“直接候选”的记录。每篇论文只计一个主方向，环比同时展示绝对量和百分比。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>1,319</strong><span>当月 arXiv 母集</span></div>
  <div class="radar-kpi"><strong>392</strong><span>直接候选</span></div>
  <div class="radar-kpi"><strong>254</strong><span>边界候选</span></div>
  <div class="radar-kpi"><strong>694</strong><span>上月直接候选</span></div>
</div>

| 主方向 | 本月 | 占比 | 上月 | 环比增量 | 环比 |
|---|---:|---:|---:|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 49 | 12.5% | 95 | -46 | -48.4% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 20 | 5.1% | 29 | -9 | -31.0% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 32 | 8.2% | 49 | -17 | -34.7% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 42 | 10.7% | 74 | -32 | -43.2% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 67 | 17.1% | 121 | -54 | -44.6% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 26 | 6.6% | 49 | -23 | -46.9% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 25 | 6.4% | 29 | -4 | -13.8% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 89 | 22.7% | 157 | -68 | -43.3% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 7 | 1.8% | 19 | -12 | -63.2% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 10 | 2.6% | 23 | -13 | -56.5% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 20 | 5.1% | 39 | -19 | -48.7% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 4 | 1.0% | 5 | -1 | -20.0% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 0 | 0.0% | 0 | 0 | — |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 1 | 0.3% | 3 | -2 | -66.7% |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 0 | 0.0% | 2 | -2 | -100.0% |
| **总计** | **392** | **100.0%** | **694** | **-302** | **-43.5%** |

跨月比较时，应先看绝对数量与独立论文簇，再用正式发表和 GitHub 采用证据判断是否从 arXiv 热点走向兑现。
### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 触觉与 world model 开始合流

**变化。** Touch Dreaming、FingerEye 与 OmniVTA 把触觉用于未来预测、连续感知和接触世界建模。

**对比。** 8 月只是多模态 VLA 接口；本月触觉开始改变训练目标和状态预测。

**证据。** [Learning Versatile Humanoid Manipulation with Touch Dreaming](https://arxiv.org/abs/2604.13015)；[FingerEye: Learning Dexterous Manipulation with Continuous Vision-Tactile Sensing](https://arxiv.org/abs/2604.20689)；[OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2603.19201)

**成熟度与瓶颈。** 跨团队、跨月信号明确。主要瓶颈是低成本传感器一致性与大规模同步数据。

**战略含义。** 触觉世界模型可能先在装配、工具使用和柔性物体中兑现。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> 双系统进入异步 coarse-to-fine 调度

**变化。** Libra-VLA、Trace-Conditioned Planning 与 DIAL 不再固定每步完整推理，而是在轨迹、意图和动作层分配不同计算。

**对比。** 比 2025 年的显式 fast–slow 更接近实时系统设计。

**证据。** [Libra-VLA: Achieving Learning Equilibrium via Asynchronous Coarse-to-Fine Dual-System](https://arxiv.org/abs/2604.24921)；[Long-Horizon Manipulation via Trace-Conditioned VLA Planning](https://arxiv.org/abs/2604.21924)；[DIAL: Decoupling Intent and Action via Latent World Modeling for End-to-End VLA](https://arxiv.org/abs/2603.29844)

**成熟度与瓶颈。** 架构成熟度上升，工程 benchmark 缺失。主要瓶颈是异步状态陈旧与延迟抖动。

**战略含义。** 控制频率、端到端延迟和恢复时间应进入标准评测。

</div>

<div class="trend-card">

#### <span class="signal signal-c">C · 弱信号</span> foundation model 开始接受垂直本体与可控行为约束

**变化。** π0.7 强调 steerable generalist policy，Open-H-Embodiment 把医疗机器人纳入大规模基础模型数据。

**对比。** 通用性从“同一权重做更多任务”转向“可控制地适应高约束域”。

**证据。** [$π_{0.7}$: a Steerable Generalist Robotic Foundation Model with Emergent Capabilities](https://arxiv.org/abs/2604.15483)；[Open-H-Embodiment: A Large-Scale Dataset for Enabling Foundation Models in Medical Robotics](https://arxiv.org/abs/2604.21017)

**成熟度与瓶颈。** 两个高信号工作，独立验证不足。主要瓶颈是高风险域的安全验证与数据治理。

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
| [Open-H-Embodiment: A Large-Scale Dataset for Enabling Foundation Models in Medical Robotics](https://arxiv.org/abs/2604.21017) | 2026-04-22 | 具身基础模型与通才策略 | 汇集 50 多家机构、多种手术本体的同步视频—运动学开放数据，并展示 medical VLA 与多本体 action-conditioned simulator。 | 跨本体 · 长时序 · 开放资产 |
| [$π_{0.7}$: a Steerable Generalist Robotic Foundation Model with Emergent Capabilities](https://arxiv.org/abs/2604.15483) | 2026-04-16 | 具身基础模型与通才策略 | 通过把策略、表现元数据和子目标图像等多模态上下文纳入训练，使单一 foundation policy 可被精细 steer 并出现跨本体、组合任务和灵巧能力。 | 多任务 · 跨本体 · 长时序 |
| [Long-Horizon Manipulation via Trace-Conditioned VLA Planning](https://arxiv.org/abs/2604.21924) | 2026-04-23 | 具身基础模型与通才策略 | 以任务管理 VLM 反复输出剩余子任务与 2D visual trace，驱动短时 VLA 执行器并在失败后自动保留未完成步骤。 | 真机 · 长时序 |
| [STARRY: Spatial-Temporal Action-Centric World Modeling for Robotic Manipulation](https://arxiv.org/abs/2604.26848) | 2026-04-29 | 世界模型与预测控制 | 在统一 diffusion 过程中联合去噪未来时空 latent 与动作，并以深度和末端几何调制动作注意力。 | 真机 · 多任务 |
| [Learning Versatile Humanoid Manipulation with Touch Dreaming](https://arxiv.org/abs/2604.13015) | 2026-04-14 | 人形、运动与全身控制 | 把低身稳定控制、全身 VR 数据采集和 touch dreaming 结合，使 humanoid policy 同时预测动作块、未来关节力与触觉 latent。 | 真机 |
| [FingerEye: Learning Dexterous Manipulation with Continuous Vision-Tactile Sensing](https://arxiv.org/abs/2604.20689) | 2026-04-22 | 灵巧、双臂与接触操作 | 用指尖双目视觉与柔顺接触环实现从接近到接触后的连续感知，并以组结构融合策略减轻模态捷径。 | 真机 |
| [Libra-VLA: Achieving Learning Equilibrium via Asynchronous Coarse-to-Fine Dual-System](https://arxiv.org/abs/2604.24921) | 2026-04-27 | 具身基础模型与通才策略 | 将宏观离散方向规划和微观连续位姿对齐分给异步双系统，并提出动作分解粒度存在学习均衡点。 | 摘要未确认 |

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

---


## 2026 年 5 月研究雷达

> **统计口径。** 当前 15 个研究方向用于数量结构；7 篇精读样本用于实验与开放性指标。上月为 2026-04，同比月为 2025-05。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>559</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>6/7</strong><span>核验确认真机</span></div>
  <div class="radar-kpi"><strong>0</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

视频模型正在被改造成 generalist policy，而非外置 world model；与此同时，generalist 底座开始向软体与灵巧专用能力下沉。

### 主题结构与环比

> 本表使用当前 15 个研究方向，只统计自动判为“直接候选”的记录。每篇论文只计一个主方向，环比同时展示绝对量和百分比。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>1,737</strong><span>当月 arXiv 母集</span></div>
  <div class="radar-kpi"><strong>559</strong><span>直接候选</span></div>
  <div class="radar-kpi"><strong>360</strong><span>边界候选</span></div>
  <div class="radar-kpi"><strong>392</strong><span>上月直接候选</span></div>
</div>

| 主方向 | 本月 | 占比 | 上月 | 环比增量 | 环比 |
|---|---:|---:|---:|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 94 | 16.8% | 49 | +45 | +91.8% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 35 | 6.3% | 20 | +15 | +75.0% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 53 | 9.5% | 32 | +21 | +65.6% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 47 | 8.4% | 42 | +5 | +11.9% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 66 | 11.8% | 67 | -1 | -1.5% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 19 | 3.4% | 26 | -7 | -26.9% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 24 | 4.3% | 25 | -1 | -4.0% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 138 | 24.7% | 89 | +49 | +55.1% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 21 | 3.8% | 7 | +14 | +200.0% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 15 | 2.7% | 10 | +5 | +50.0% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 33 | 5.9% | 20 | +13 | +65.0% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 9 | 1.6% | 4 | +5 | +125.0% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 0 | 0.0% | 0 | 0 | — |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 4 | 0.7% | 1 | +3 | +300.0% |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 1 | 0.2% | 0 | +1 | 新增 |
| **总计** | **559** | **100.0%** | **392** | **+167** | **+42.6%** |

跨月比较时，应先看绝对数量与独立论文簇，再用正式发表和 GitHub 采用证据判断是否从 arXiv 热点走向兑现。
### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> 视频模型正在被改造成 generalist policy，而非外置 world model

**变化。** Turning Video Models into Generalist Robot Policies、τ0-WM 与 Cosmos Policy 把视频预测和动作生成压进同一训练栈。

**对比。** 2025 年视频模型多是数据或模拟器；现在开始直接承担控制表示。

**证据。** [Turning Video Models into Generalist Robot Policies](https://arxiv.org/abs/2605.27817)；[$τ_0$-WM: A Unified Video-Action World Model for Robotic Manipulation](https://arxiv.org/abs/2606.01027)；[Cosmos Policy: Fine-Tuning Video Models for Visuomotor Control and Planning](https://arxiv.org/abs/2601.16163)

**成熟度与瓶颈。** 跨团队方向明确，实时控制成本仍高。主要瓶颈是像素生成冗余与动作时延。

**战略含义。** 未来胜出的可能是压缩 latent video-action model，而非最大视频生成器。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 连续推理开始取代离散 reason–act 循环

**变化。** Continuous Reasoning、Libra-VLA 与 StreamVLA 都试图让思考与控制异步或连续发生。

**对比。** 大小脑竞争由模块命名转向时钟与状态同步。

**证据。** [Continuous Reasoning for Vision-Language-Action](https://arxiv.org/abs/2606.00229)；[Libra-VLA: Achieving Learning Equilibrium via Asynchronous Coarse-to-Fine Dual-System](https://arxiv.org/abs/2604.24921)；[StreamVLA: Breaking the Reason-Act Cycle via Completion-State Gating](https://arxiv.org/abs/2602.01100)

**成熟度与瓶颈。** 三团队连续出现。主要瓶颈是推理状态陈旧、测试时计算不可控。

**战略含义。** 系统软件和推理调度会成为 VLA 部署的关键护城河。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> generalist 底座开始向软体与灵巧专用能力下沉

**变化。** DeMaVLA、BORA 与 Qwen-VLA 分别覆盖可变形物体、真实灵巧在线适配和跨任务/本体统一。

**对比。** 相较只做 kitchen benchmark，任务物理性明显增强。

**证据。** [DeMaVLA: A Vision-Language-Action Foundation Model for Generalizable Deformable Manipulation](https://arxiv.org/abs/2605.31286)；[BORA: Bridging Offline Reinforcement Learning and Online Residual Adaptation for Real-World Dexterous VLA Models](https://arxiv.org/abs/2605.30226)；[Qwen-VLA: Unifying Vision-Language-Action Modeling across Tasks, Environments, and Robot Embodiments](https://arxiv.org/abs/2605.30280)

**成熟度与瓶颈。** 真实任务信号增强，开放与独立复现待确认。主要瓶颈是专用数据稀缺与在线适配安全。

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
| [Qwen-VLA: Unifying Vision-Language-Action Modeling across Tasks, Environments, and Robot Embodiments](https://arxiv.org/abs/2605.30280) | 2026-05-28 | 具身基础模型与通才策略 | 以 embodiment-aware prompt 和统一动作—轨迹预测，把操作、导航、轨迹预测及多源数据纳入单一 Qwen-VLA。 | 真机 · 多任务 · 跨本体 |
| [Turning Video Models into Generalist Robot Policies](https://arxiv.org/abs/2605.27817) | 2026-05-27 | 具身基础模型与通才策略 | 保持 video planner 本体无关，仅为各机器人训练基于 Jacobian 的 IDM，形成可替换视频模型的闭环 VERA 路线。 | 真机 · 跨本体 |
| [DeMaVLA: A Vision-Language-Action Foundation Model for Generalizable Deformable Manipulation](https://arxiv.org/abs/2605.31286) | 2026-05-29 | 具身基础模型与通才策略 | 以约 5,000 小时双臂真实示范预训练，再用失败纠正轨迹和 HiL DAgger 学习跨服装类别的通用折叠策略。 | 真机 · 多任务 |
| [OneVLA: A Unified Framework for Embodied Tasks](https://arxiv.org/abs/2606.01241) | 2026-05-31 | 具身基础模型与通才策略 | 用统一 action head 和渐进式多阶段训练把导航与操作纳入同一 VLA，探索跨任务正迁移。 | 真机 · 长时序 |
| [BORA: Bridging Offline Reinforcement Learning and Online Residual Adaptation for Real-World Dexterous VLA Models](https://arxiv.org/abs/2605.30226) | 2026-05-28 | 策略学习与优化 | 用离线动作条件 critic 稳定价值学习，再冻结 VLA 基座，以人类介入的 chunk-wise residual 做低风险在线适配。 | 真机 |
| [Continuous Reasoning for Vision-Language-Action](https://arxiv.org/abs/2606.00229) | 2026-05-29 | 具身基础模型与通才策略 | 把可共享、可验证的 Gaussian continuous thoughts 作为 VLA 推理介质，并以教师消费学生 latent 的动作改善来约束推理。 | 真机 |
| [$τ_0$-WM: A Unified Video-Action World Model for Robotic Manipulation](https://arxiv.org/abs/2606.01027) | 2026-05-31 | 世界模型与预测控制 | 以共享视频 diffusion backbone 统一动作生成、未来视频模拟和进度评分，并在约 27,300 小时混合数据上训练。 | 长时序 |

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

---


## 2026 年 6 月研究雷达

> **统计口径。** 当前 15 个研究方向用于数量结构；7 篇精读样本用于实验与开放性指标。上月为 2026-05，同比月为 2025-06。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>735</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>7</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>6/7</strong><span>核验确认真机</span></div>
  <div class="radar-kpi"><strong>0</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

大小脑接口正在变成可监督的 3D 轨迹语言；与此同时，开放训练栈与人类视频迁移同时加速。

### 主题结构与环比

> 本表使用当前 15 个研究方向，只统计自动判为“直接候选”的记录。每篇论文只计一个主方向，环比同时展示绝对量和百分比。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>1,918</strong><span>当月 arXiv 母集</span></div>
  <div class="radar-kpi"><strong>735</strong><span>直接候选</span></div>
  <div class="radar-kpi"><strong>411</strong><span>边界候选</span></div>
  <div class="radar-kpi"><strong>559</strong><span>上月直接候选</span></div>
</div>

| 主方向 | 本月 | 占比 | 上月 | 环比增量 | 环比 |
|---|---:|---:|---:|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 112 | 15.2% | 94 | +18 | +19.1% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 36 | 4.9% | 35 | +1 | +2.9% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 83 | 11.3% | 53 | +30 | +56.6% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 85 | 11.6% | 47 | +38 | +80.9% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 121 | 16.5% | 66 | +55 | +83.3% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 29 | 3.9% | 19 | +10 | +52.6% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 29 | 3.9% | 24 | +5 | +20.8% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 141 | 19.2% | 138 | +3 | +2.2% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 26 | 3.5% | 21 | +5 | +23.8% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 27 | 3.7% | 15 | +12 | +80.0% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 30 | 4.1% | 33 | -3 | -9.1% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 10 | 1.4% | 9 | +1 | +11.1% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 2 | 0.3% | 0 | +2 | 新增 |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 1 | 0.1% | 4 | -3 | -75.0% |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 3 | 0.4% | 1 | +2 | +200.0% |
| **总计** | **735** | **100.0%** | **559** | **+176** | **+31.5%** |

跨月比较时，应先看绝对数量与独立论文簇，再用正式发表和 GitHub 采用证据判断是否从 arXiv 热点走向兑现。
### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> 大小脑接口正在变成可监督的 3D 轨迹语言

**变化。** Dense Embodied CoT、3D HAMSTER 与 Continuous Reasoning 分别提供密集思维监督、3D 轨迹桥接和连续推理。

**对比。** 从抽象语言计划进化到可落地的几何中间表示。

**证据。** [Training Vision-Language-Action Models with Dense Embodied Chain-of-Thought Supervision](https://arxiv.org/abs/2606.30552)；[3D HAMSTER: Bridging Planning and Control in Hierarchical Vision Language Action Models through 3D Trajectory Guidance](https://arxiv.org/abs/2606.31329)；[Continuous Reasoning for Vision-Language-Action](https://arxiv.org/abs/2606.00229)

**成熟度与瓶颈。** 跨团队新兴趋势，标准数据格式尚未形成。主要瓶颈是中间监督获取成本和错误计划的可恢复性。

**战略含义。** 3D trajectory token/trace 可能成为跨模型、跨控制器的接口标准。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 触觉从专用 policy 升级为 VLA 的预测通道

**变化。** UniTacVLA、CoDex 与 Touch Dreaming 分别统一触觉理解/预测、无示范组合灵巧任务和触觉想象。

**对比。** 相较 2025 年仅做感知融合，本月出现预测和组合泛化目标。

**证据。** [UniTacVLA: Unified Tactile Understanding and Prediction in Vision Language Action Models](https://arxiv.org/abs/2606.31723)；[CoDex: Learning Compositional Dexterous Functional Manipulation without Demonstrations](https://arxiv.org/abs/2606.31909)；[Learning Versatile Humanoid Manipulation with Touch Dreaming](https://arxiv.org/abs/2604.13015)

**成熟度与瓶颈。** 方法簇初成，硬件标准化不足。主要瓶颈是传感器寿命、同步频率和跨手型迁移。

**战略含义。** 触觉数据层可能成为新基础设施赛道。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 共识演进</span> 开放训练栈与人类视频迁移同时加速

**变化。** Scalable Behavior Cloning、Human-as-Humanoid 与 Qwen-VLA 分别强调开放数据/训练/评测、人类对齐本体和跨本体统一。

**对比。** 开放不再只等于放权重，而是开始覆盖数据与评测。

**证据。** [Scalable Behavior Cloning with Open Data, Training, and Evaluation](https://arxiv.org/abs/2606.27375)；[Human-as-Humanoid: Enabling Zero-Shot Humanoid Learning from Ego-Exo Human Videos with Human-Aligned Embodiments](https://arxiv.org/abs/2606.32009)；[Qwen-VLA: Unifying Vision-Language-Action Modeling across Tasks, Environments, and Robot Embodiments](https://arxiv.org/abs/2605.30280)

**成熟度与瓶颈。** 资产开放信号强，独立采用尚需时间。主要瓶颈是数据许可、硬件可复现与评测碎片化。

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
| [Scalable Behavior Cloning with Open Data, Training, and Evaluation](https://arxiv.org/abs/2606.27375) | 2026-06-25 | 策略学习与优化 | 发布 3,500 小时、130K episodes、195 任务的 ABC-130K，以及硬件、训练、仿真和真实评测全栈。 | 真机 · 多任务 · 开放资产 |
| [Training Vision-Language-Action Models with Dense Embodied Chain-of-Thought Supervision](https://arxiv.org/abs/2606.30552) | 2026-06-29 | 分层推理、规划与记忆 | 以 60M 帧的 dense ECoT 对齐跨本体高层认知，同时由 flow action expert 输出连续动作且推理时可跳过 CoT。 | 真机 · 跨本体 |
| [Human-as-Humanoid: Enabling Zero-Shot Humanoid Learning from Ego-Exo Human Videos with Human-Aligned Embodiments](https://arxiv.org/abs/2606.32009) | 2026-06-30 | 数据引擎与人类视频学习 | 通过 ego-exo 同步、60-DoF 动作重定向和 FK-aware supervision，把人类视频转成可直接训练 humanoid VLA 的动作标签。 | 真机 · 跨本体 |
| [3D HAMSTER: Bridging Planning and Control in Hierarchical Vision Language Action Models through 3D Trajectory Guidance](https://arxiv.org/abs/2606.31329) | 2026-06-30 | 具身基础模型与通才策略 | 让高层 VLM 直接输出 metric 3D waypoint，并无缝接入点云低层策略，修正 2D guidance 的深度歧义。 | 真机 |
| [UniTacVLA: Unified Tactile Understanding and Prediction in Vision Language Action Models](https://arxiv.org/abs/2606.31723) | 2026-06-30 | 具身基础模型与通才策略 | 以统一 tactile latent 同时建模当前接触语义和未来变化，再用 tactile-action mixed controller 高频修正低频动作块。 | 真机 |
| [DVG-WM: Disentangled Video Generation Enables Efficient Embodied World Model for Robotic Manipulation](https://arxiv.org/abs/2606.32028) | 2026-06-30 | 世界模型与预测控制 | 把低层动力学演化与高分辨率视觉合成解耦，通过级联 latent 生成在保留接触细节的同时最高加速 3.97 倍。 | 真机 |
| [CoDex: Learning Compositional Dexterous Functional Manipulation without Demonstrations](https://arxiv.org/abs/2606.31909) | 2026-06-30 | 灵巧、双臂与接触操作 | 让 VLM 提取功能和场景约束，经解析优化筛选功能抓取，再以 RL 形成可 sim-to-real 的抓—移—触发组合策略。 | 摘要未确认 |

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

---


## 2026 年 7 月研究雷达（完整月）

> **7 月完整月。** arXiv 母集覆盖至 31 日，并补入 30–31 日 10 篇高信号精读；主题结构统一采用当前 15 个研究方向。


<div class="radar-kpis">
  <div class="radar-kpi"><strong>506</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>20</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>13/20</strong><span>核验确认真机</span></div>
  <div class="radar-kpi"><strong>0</strong><span>官方评审锚点</span></div>
</div>

### 一句话结论

7 月完整月总量较 6 月回落，但月末的世界模型决策化、失败纠错、触觉未来监督和行为对齐跨本体迁移组成了比总量更值得跟踪的弱信号。

### 主题结构与环比

> 本表使用当前 15 个研究方向，只统计自动判为“直接候选”的记录。每篇论文只计一个主方向，环比同时展示绝对量和百分比。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>1,444</strong><span>当月 arXiv 母集</span></div>
  <div class="radar-kpi"><strong>506</strong><span>直接候选</span></div>
  <div class="radar-kpi"><strong>307</strong><span>边界候选</span></div>
  <div class="radar-kpi"><strong>735</strong><span>上月直接候选</span></div>
</div>

| 主方向 | 本月 | 占比 | 上月 | 环比增量 | 环比 |
|---|---:|---:|---:|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 74 | 14.6% | 112 | -38 | -33.9% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 32 | 6.3% | 36 | -4 | -11.1% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 57 | 11.3% | 83 | -26 | -31.3% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 50 | 9.9% | 85 | -35 | -41.2% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 70 | 13.8% | 121 | -51 | -42.1% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 26 | 5.1% | 29 | -3 | -10.3% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 37 | 7.3% | 29 | +8 | +27.6% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 102 | 20.2% | 141 | -39 | -27.7% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 16 | 3.2% | 26 | -10 | -38.5% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 14 | 2.8% | 27 | -13 | -48.1% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 18 | 3.6% | 30 | -12 | -40.0% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 6 | 1.2% | 10 | -4 | -40.0% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 0 | 0.0% | 2 | -2 | -100.0% |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 1 | 0.2% | 1 | 0 | 0.0% |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 3 | 0.6% | 3 | 0 | 0.0% |
| **总计** | **506** | **100.0%** | **735** | **-229** | **-31.2%** |

跨月比较时，应先看绝对数量与独立论文簇，再用正式发表和 GitHub 采用证据判断是否从 arXiv 热点走向兑现。
### 7 月完整月研判

#### 数量层：完整月环比回落，但不等于技术降温

**事实。** 7 月宽召回收录 1444 条母集、506 条直接候选；6 月分别为 1918 和 735，直接候选环比 -31.2%。

**解释。** 现在的环比已是完整月对完整月，可以确认 7 月总量低于 6 月。但会议周期与集中提交仍可放大单月波动；而 7 月 30–31 日反而集中出现多项高信号工作。所以“数量回落”是事实，“技术降温”仍需跨月和独立实验证据。

#### 共识主线：规模化 VLA 仍最热，但信息增量正在下降

[Xiaomi-Robotics-1](https://arxiv.org/abs/2607.15330) 把论文自报训练规模推到 100K 小时级，[Data Pyramid](https://arxiv.org/abs/2607.24744) 试图解释不同数据层级的作用。“更大、更杂的数据”仍是最强共识，但单纯拥有大数字已不足以构成差异；更关键的是有效多样性、失败覆盖、新任务上线时间与每小时的真机边际收益。

#### 月末弱信号：不同名词开始指向同一瓶颈

| 潜在瓶颈迁移 | 月末证据 | 当前判断 |
|---|---|---|
| world model 从“预测画面”走向“搜索/评价动作” | [World Action Planner: Generalizable Decision-Making with Action-Conditioned World Models](https://arxiv.org/abs/2607.27599)；[BWM: A Low-Cost High-Fidelity World Simulator for Robot Learning](https://arxiv.org/abs/2607.29302)；[WCM: A World Critic Model for Vision-Language-Action Reinforcement Learning](https://arxiv.org/abs/2607.29613) | 三个独立项目分别用于规划搜索、策略排序与 critic 学习，为 B 级新兴簇；仍缺正式评审和第三方对照。 |
| 失败从事后统计变成训练信号 | [RedFlow: Redirect Failure into Action-Level Corrections for Flow-matching VLA Policy](https://arxiv.org/abs/2607.27782)；[CLIFT: Turning Gemini Robotics On-Device into Humanoid Specialists via Non-Invasive Closed-Loop Iterative Fine-Tuning](https://arxiv.org/abs/2607.29172)；[WCM: A World Critic Model for Vision-Language-Action Reinforcement Learning](https://arxiv.org/abs/2607.29613) | 动作级纠错、托管 API 反复微调与世界 critic 用不同名词指向同一数据飞轮；应优先跟踪失败覆盖率和单次修正成本。 |
| 接触操作需要“未来触觉 + 变频控制” | [TacWAM: Anchor-Guided World Action Model with Mechanics-Aware Tactile Prediction](https://arxiv.org/abs/2607.28391)；[FA-RDP: A Frequency-Adaptive Reactive Diffusion Policy for Contact-Rich Manipulation](https://arxiv.org/abs/2607.28596) | 一项用力/形变/滑移未来监督动作，一项在接触前后切换推理频率；仍需跨传感器和跨材料验证。 |
| 跨本体接口从关节动作转向行为对齐表征 | [Cross-Embodiment Transfer via Behavior-Aligned Representations](https://arxiv.org/abs/2607.27549) | 真机 sim-to-real 进度增益使其成为 C 级高新颖信号，但尚不是跨团队趋势。 |
| 安全约束开始进入生成式策略内部 | [Safe Vision Language Action Models via Barrier Enhanced Flow Matching](https://arxiv.org/abs/2607.29569) | CBF 不再只做末端滤波，而是影响整个 flow-matching denoising；感知错误与未建模风险仍是反证。 |
| 人类数据引擎开始追求全链路同步 | [ACE-Data-0: Human-Centric Ambient Capture as Embodied Data Engine](https://arxiv.org/abs/2607.28625) | 150 小时、17M 帧、75,000 episodes 与多视角/全身/手/物体/音频/触觉对齐是稀缺数据设计；但尚未证明下游真机收益。 |

#### 证据成熟度：为什么这些信号仍不是 A 级

| 命题 | 当前等级 | 已有证据 | 升级到 A 级需要什么 |
|---|---|---|---|
| 在线评价与纠错侧车 | B | 多个独立团队；跨 backbone、真机、失败纠错与未来 latent critic 均已出现 | 至少两项正式同行评审；第三方复现能同时提高恢复率并控制时延 |
| 进度—记忆—运行时状态 | B | 全尺寸双臂装配、真实长时记忆任务、19+ 本体系统验证等互补证据 | 开放接口被独立团队采用；跨机器人统一记录 completion、replan 和 failure provenance |
| 视触觉 world model | B | 6–7 月连续出现多个独立团队，已连接数据生成、评估、纠错和接触变频控制 | 跨传感器 benchmark；同等真实数据量下稳定改善闭环恢复 |
| Embodied Agent OS | C | 单项目提出 session、verification、memory 和 safety 服务 | 至少两个外部模型/机器人团队采用同一运行时 |

#### 对未来 6–12 个月的判断

1. **高置信：verifier/critic/corrector 会成为 VLA 的标准侧车。** 主模型负责 proposal，轻量 dynamics/value/safety 模块负责打断、排序和恢复。WCM 与 RedFlow 提高了置信度，但仍须跨策略第三方复现。
2. **中高置信：大小脑会演化成 Executor–Monitor/Sentry–Planner 的三层系统。** “第三层”未必是更大的模型，更可能是持续维护任务进度、记忆和完成条件的状态层。
3. **中高置信：触觉 world model 会先在失败恢复和后训练兑现。** TacWAM 的未来力/形变监督与 FA-RDP 的接触阶段变频是两条互补路线；短期不会成为所有 VLA 的必选输入。
4. **中等置信：数据竞争将从总小时迁移到有效多样性和失败覆盖。** 能公开数据组成、去重、纠正效率与下游边际收益的团队，会比只披露总小时的团队更快建立可信度。
5. **中置信：world model 会分化成“控制迭代”和“数据/评估基础设施”。** WCM/World Action Planner 代表前者，BWM 代表后者；只报告视频质量的中间路线会被边缘化。
6. **中低置信：Embodied Agent OS 可能形成独立平台层。** 只有当第三方模型和不同硬件愿意复用其 session、verification 和 safety 接口时，才会从论文系统升级为生态。

#### 研究与团队跟踪清单

- VLA：要求披露失败检测时机、恢复成功率、每次恢复时延和误报代价。
- 数据团队：跟踪独立场景/技能/失败的有效覆盖，以及新增 1,000 小时的真机边际收益。
- world model：坚持同算力、同真实数据量下比较控制收益；只有视频更清晰不算升级。
- 开源项目：stars 只作传播旁证；优先找无作者重叠的下游采用、真实 import 和复现结果。


### 趋势证据卡


<div class="trend-card">

#### <span class="signal signal-c">C · 弱信号</span> 论文报告 100K 小时级真实轨迹，暂不是已确认趋势

**变化。** Xiaomi-Robotics-1 论文报告超过 100K 小时真实轨迹，Data Pyramid 讨论数据层级；若数据口径能被下游能力和开放评测验证，数据工程门槛将显著抬高。

**对比。** 7 月完整月候选量低于 6 月、但显著高于 2025 年 7 月；高召回语料为 506 对 735，环比 −31.2%，仍需结合 6 月集中提交效应解读。

**证据。** [Xiaomi-Robotics-1: Scaling Vision-Language-Action Models with over 100K Hours of Real-World Trajectories](https://arxiv.org/abs/2607.15330)；[Data Pyramid for Embodied Manipulation](https://arxiv.org/abs/2607.24744)

**成熟度与瓶颈。** 超大规模单团队信号。主要瓶颈是数据质量、任务分布与外部可验证性。

**战略含义。** 未来应问“有效多样性/小时”，而不只看总小时。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 视触觉 world model 正从感知融合转向失败恢复

**变化。** ViTacWorld、τ、TACO 与 DC-WAM 分别把触觉接到 rollout 生成、未来视觉监督、失败纠正和 world-action 联合建模；共同目标不再只是提升融合表征。

**对比。** 6 月 TacForeSight 等工作把触觉推进到预测通道，7 月又出现多个独立团队把预测结果用于数据增强、策略评估和纠错。

**证据。** [ViTacWorld: Scaling Visuo-Tactile World Models for Contact-Rich Robot Manipulation](https://arxiv.org/abs/2607.22530)；[τ: Learning Touch-Augmented Vision-Language-Action Models from Future Visual Supervision](https://arxiv.org/abs/2607.24485)；[TACO: TActile World Model as a Self-COrrector forScalable VLA Post-Training](https://arxiv.org/abs/2607.02840)；[DC-WAM: Dynamic-Centric Visual Supervision and Reasoning for World-Action Models](https://arxiv.org/abs/2607.25918)

**成熟度与瓶颈。** 跨月、跨团队的新兴方法簇，但传感器和任务仍高度异构。主要瓶颈是跨触觉硬件迁移、未来监督偏差，以及恢复率的统一 benchmark。

**战略含义。** 这是 7 月最强的非共识信号；未来应以接触失败恢复率、跨传感器迁移和数据边际收益验证。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> VLA 的下一层竞争从动作生成转向在线评价与纠错

**变化。** VLA-Corrector 监视执行偏差并触发重规划，TACO 用触觉世界模型生成纠正片段，SVA 则把树搜索蒸馏为候选动作价值评估；三者都保留或冻结主策略，把增量能力放到测试时侧车。

**对比。** 此前自纠错更多依赖重新训练主策略或人工失败数据；7 月集中出现轻量 monitor、verifier/value model 和事件触发机制。

**证据。** [VLA-Corrector: Lightweight Detect-and-Correct Inference for Adaptive Action Horizon](https://arxiv.org/abs/2607.01804)；[TACO: TActile World Model as a Self-COrrector forScalable VLA Post-Training](https://arxiv.org/abs/2607.02840)；[Look Before You Leap: Distilling Tree Search into Action Evaluation for Frozen VLA Models](https://arxiv.org/abs/2607.03751)

**成熟度与瓶颈。** 三个独立团队形成同月簇，且至少两项报告真实机器人或跨 backbone 结果。主要瓶颈是异常检测误报、纠错延迟、价值模型分布外可靠性与统一恢复评测。

**战略含义。** 短期优先跟踪能量化 success-per-call、失败恢复率和安全边界的 verifier/corrector 基础设施。

</div>

<div class="trend-card">

#### <span class="signal signal-b">B · 弱信号</span> 长时序瓶颈正在从“任务分解”迁移到进度、记忆与运行时状态

**变化。** FurnitureVLA 用连续进度触发子任务切换，HiMe 用 Executor–Sentry–Planner 管理不同时间尺度的记忆，PhyAgentOS 则把 session、验证和经验固化为系统服务。

**对比。** 此前长时 VLA 多依赖语言 planner 生成步骤；本月三个独立团队开始显式表示任务完成度、非马尔可夫记忆和跨层执行状态。

**证据。** [FurnitureVLA: Learning Long-Horizon Bimanual Furniture Assembly with Vision-Language-Action Model](https://arxiv.org/abs/2607.01212)；[HiMe: Hierarchical Embodied Memory for Long-Horizon Vision-Language-Action Control](https://arxiv.org/abs/2607.03449)；[PhyAgentOS: A Self-Evolving Operating System for Embodied Agents with Decoupled Cognitive Planning and Physical Execution](https://arxiv.org/abs/2607.16636)

**成熟度与瓶颈。** 已出现全尺寸双臂和真实机器人验证，但任务范围与接口标准仍有限。主要瓶颈是完成度校准、记忆污染、模块错误归因和跨机器人可复用性。

**战略含义。** 长期价值可能沉淀在 progress/verifier/memory runtime，而非更长的语言 chain-of-thought。

</div>

<div class="trend-card">

#### <span class="signal signal-c">C · 弱信号</span> 具身 Agent OS 可能成为模型之上的系统层

**变化。** PhyAgentOS 把认知规划与物理执行解耦，并强调自演化操作系统；它呼应过去一年的双系统和调度趋势。

**对比。** 此前多是论文内架构，本月出现系统软件层叙事，但当前仍主要由单一项目定义接口和评测。

**证据。** [PhyAgentOS: A Self-Evolving Operating System for Embodied Agents with Decoupled Cognitive Planning and Physical Execution](https://arxiv.org/abs/2607.16636)

**成熟度与瓶颈。** 单项早期信号。主要瓶颈是接口标准、实时性、安全隔离和跨硬件兼容。

**战略含义。** 若未来出现跨模型/跨机器人的第三方采用，系统层可能形成独立平台价值。

</div>

### 蛛丝马迹：小样本领先信号

| 弱信号 | 等级 | 下一道技术门槛 | 当前判断 |
|---|---|---|---|
| 论文报告 100K 小时级真实轨迹，暂不是已确认趋势 | C | 数据质量、任务分布与外部可验证性。 | 超大规模单团队信号。 |
| 视触觉 world model 正从感知融合转向失败恢复 | B | 跨触觉硬件迁移、未来监督偏差，以及恢复率的统一 benchmark。 | 跨月、跨团队的新兴方法簇，但传感器和任务仍高度异构。 |
| VLA 的下一层竞争从动作生成转向在线评价与纠错 | B | 异常检测误报、纠错延迟、价值模型分布外可靠性与统一恢复评测。 | 三个独立团队形成同月簇，且至少两项报告真实机器人或跨 backbone 结果。 |
| 长时序瓶颈正在从“任务分解”迁移到进度、记忆与运行时状态 | B | 完成度校准、记忆污染、模块错误归因和跨机器人可复用性。 | 已出现全尺寸双臂和真实机器人验证，但任务范围与接口标准仍有限。 |
| 具身 Agent OS 可能成为模型之上的系统层 | C | 接口标准、实时性、安全隔离和跨硬件兼容。 | 单项早期信号。 |

识别逻辑不是“论文少就更前沿”，而是寻找多个弱证据是否指向同一个尚未被主流命名的瓶颈迁移。完整方法见[弱信号探测与未来判断](/analysis/weak-signals)。

### 本月精读论文

| 论文 | v1 日期 | 主方向 | 一句话贡献 | 证据标签 |
|---|---|---|---|---|
| [VLA-Corrector: Lightweight Detect-and-Correct Inference for Adaptive Action Horizon](https://arxiv.org/abs/2607.01804) | 2026-07-02 | 具身基础模型与通才策略 | 在冻结 VLA 之外加入 latent dynamics 监视、事件触发截断与梯度引导重规划，让固定 action chunk 变成按执行偏差自适应的闭环控制。 | 真机 · 多任务 · 长时序 · 开放资产 |
| [HiMe: Hierarchical Embodied Memory for Long-Horizon Vision-Language-Action Control](https://arxiv.org/abs/2607.03449) | 2026-07-03 | 具身基础模型与通才策略 | 将长时 VLA 拆成高频 Executor、工作记忆 Sentry 和慢速 Planner，并用可增删改的跨模态记忆在真实机器人上处理非马尔可夫任务。 | 真机 · 多任务 · 长时序 · 开放资产 |
| [Cross-Embodiment Transfer via Behavior-Aligned Representations](https://arxiv.org/abs/2607.27549) | 2026-07-30 | 策略学习与优化 | 证明末端执行器轨迹等行为对齐表征可以绕开关节空间差异，将多本体数据真正转化为新本体增益。 | 真机 · 多任务 · 跨本体 · 开放资产 |
| [World Action Planner: Generalizable Decision-Making with Action-Conditioned World Models](https://arxiv.org/abs/2607.27599) | 2026-07-30 | 世界模型与预测控制 | 让 VLM 提案、动作条件世界模型预演，再用优化与搜索修改计划，把 world model 从表象生成推向决策空间。 | 多任务 · 长时序 · 开放资产 |
| [BWM: A Low-Cost High-Fidelity World Simulator for Robot Learning](https://arxiv.org/abs/2607.29302) | 2026-07-31 | 策略学习与优化 | 把动作条件视频模型同时做成仿真器、数据引擎和策略评估器，直接对齐预测质量与机器人决策用途。 | 真机 · 多任务 · 开放资产 |
| [FA-RDP: A Frequency-Adaptive Reactive Diffusion Policy for Contact-Rich Manipulation](https://arxiv.org/abs/2607.28596) | 2026-07-30 | 灵巧、双臂与接触操作 | 用变频策略匹配接触前的多模态路径与接触后的快速力反馈，把控制频率本身变成可学习结构。 | 多任务 · 开放资产 |
| [FurnitureVLA: Learning Long-Horizon Bimanual Furniture Assembly with Vision-Language-Action Model](https://arxiv.org/abs/2607.01212) | 2026-07-01 | 具身基础模型与通才策略 | 把 VLA 推进到全尺寸双臂家具装配，以连续进度预测衔接最多 7 个子任务和 1,550 个控制步，并在真实 Kinova Gen3 上验证。 | 真机 · 多任务 · 长时序 |
| [CLIFT: Turning Gemini Robotics On-Device into Humanoid Specialists via Non-Invasive Closed-Loop Iterative Fine-Tuning](https://arxiv.org/abs/2607.29172) | 2026-07-31 | 人形、运动与全身控制 | 将真机部署奖励转换为托管 SFT API 可接受的监督数据，在不访问权重、梯度或损失的情况下形成两轮部署飞轮。 | 真机 · 多任务 · 跨本体 |
| [Safe Vision Language Action Models via Barrier Enhanced Flow Matching](https://arxiv.org/abs/2607.29569) | 2026-07-31 | 具身基础模型与通才策略 | 不在 VLA 输出后外挂安全滤波器，而把 CBF 约束写入 flow-matching 去噪过程，直接约束整个 action chunk。 | 真机 · 多任务 · 跨本体 |
| [PhyAgentOS: A Self-Evolving Operating System for Embodied Agents with Decoupled Cognitive Planning and Physical Execution](https://arxiv.org/abs/2607.16636) | 2026-07-18 | 具身基础模型与通才策略 | 以 session 运行时、文件化状态、语义验证、记忆和安全服务解耦认知规划与异构机器人执行，并覆盖 19+ 仿真/实体本体。 | 真机 · 跨本体 |
| [RedFlow: Redirect Failure into Action-Level Corrections for Flow-matching VLA Policy](https://arxiv.org/abs/2607.27782) | 2026-07-30 | 策略学习与优化 | 把失败轨迹拆成动作级负例和可替换的成功动作，以约十分之一的样本量学到部署后纠错。 | 真机 · 多任务 |
| [TacWAM: Anchor-Guided World Action Model with Mechanics-Aware Tactile Prediction](https://arxiv.org/abs/2607.28391) | 2026-07-30 | 灵巧、双臂与接触操作 | 将未来触觉中的力、形变和滑移变成 world-action model 的训练监督，但隔离部署时不可见的未来信息。 | 真机 · 多任务 |
| [ACE-Data-0: Human-Centric Ambient Capture as Embodied Data Engine](https://arxiv.org/abs/2607.28625) | 2026-07-30 | 数据引擎与人类视频学习 | 把真实家庭改造为同步采集工厂，将第一/第三人称视频、全身与手部运动、物体轨迹、音频和触觉对齐到同一交互流。 | 多任务 · 长时序 |
| [WCM: A World Critic Model for Vision-Language-Action Reinforcement Learning](https://arxiv.org/abs/2607.29613) | 2026-07-31 | 具身基础模型与通才策略 | 让 critic 在估值之外同时预测未来 latent，用世界建模目标补足单帧价值估计对部分可观测控制的状态缺口。 | 真机 · 多任务 |
| [DynaWM: A Base-VLA-Guided World Foundation Model for Moving-Object Manipulation](https://arxiv.org/abs/2607.02604) | 2026-07-01 | 具身基础模型与通才策略 | 用动作条件、多视角动态表征和 flow-matching DiT 重生成移动物体操作轨迹，并在四类基础 VLA 上测试可插拔增益。 | 多任务 |
| [Xiaomi-Robotics-1: Scaling Vision-Language-Action Models with over 100K Hours of Real-World Trajectories](https://arxiv.org/abs/2607.15330) | 2026-07-16 | 具身基础模型与通才策略 | 用超过 100K 小时 UMI 真实轨迹和自动语言标注预训练基础 VLA，展示数据与模型规模向真实机器人零样本和少样本能力传导。 | 真机 |
| [DC-WAM: Dynamic-Centric Visual Supervision and Reasoning for World-Action Models](https://arxiv.org/abs/2607.25918) | 2026-07-28 | 世界模型与预测控制 | 用时间差 flow matching、轨迹加权和 DynaRoute 注意力偏置，把世界模型容量从外观重建转向控制相关动态。 | 真机 |
| [ViTacWorld: Scaling Visuo-Tactile World Models for Contact-Rich Robot Manipulation](https://arxiv.org/abs/2607.22530) | 2026-07-24 | 世界模型与预测控制 | 联合公开真实触觉数据与仿真，训练可生成视觉—触觉—动作 rollout 的世界模型，用于策略数据增强和离线评估。 | 摘要未确认 |
| [τ: Learning Touch-Augmented Vision-Language-Action Models from Future Visual Supervision](https://arxiv.org/abs/2607.24485) | 2026-07-27 | 具身基础模型与通才策略 | 以未来视觉 latent 监督学习 action-conditioned 时空触觉表征，在部署零额外开销下适配预训练 VLA。 | 摘要未确认 |
| [Data Pyramid for Embodied Manipulation](https://arxiv.org/abs/2607.24744) | 2026-07-27 | 策略学习与优化 | 以真实机器人、UMI、人类 ego/exo、仿真和通用视觉语言五层数据金字塔梳理具身数据配方与能力关系。 | 摘要未确认 |

精读样本明确开放披露 6/20；只在摘要、comment 或已核验项目页明确披露时记为“是”。

### 同行评审锚点

| 工作 | 官方证据 | 为什么可作为本月锚点 |
|---|---|---|
| — | — | 本月首次公开的精读样本尚无可安全归属到该月的官方录用证据；这不等于论文质量较低。 |

### 反证与信号质量检查

- 多篇论文共享相同数据、模型或作者团队时，不按独立证据重复加权。
- 单一 benchmark 提升若没有真实机器人迁移，不足以升级为 A 级趋势。
- “open-source / will release” 与实际可下载、可复现实验分开记录。
- 世界模型必须展示动作、规划、控制或数据生成价值；纯视频质量不计。

---


## 2026 年 8 月研究雷达（前瞻快照，截至 24 日）

> **这是前瞻快照，不是完整月。** 本站按 arXiv 首次提交 v1 日期归档。截至 2026-08-24，8 月已形成可观察样本，但不与 7 月完整月直接计算环比或外推整月趋势。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>1,007</strong><span>8 月 arXiv 母集</span></div>
  <div class="radar-kpi"><strong>328</strong><span>直接候选</span></div>
  <div class="radar-kpi"><strong>10,404</strong><span>窗口内发表版本</span></div>
  <div class="radar-kpi"><strong>42 + 4</strong><span>已审计 + 新仓观察</span></div>
</div>

### 一句话结论

8 月截至 24 日已有 328 条直接候选；数量领先的是具身基础模型与通才策略（57）、策略学习与优化（55）、人形、运动与全身控制（45）、世界模型与预测控制（41）、灵巧、双臂与接触操作（38）。不完整月的数量不用于判断升降，更有价值的变化是：接触失败诊断、自动干预、失败感知 world-action model 和学习驱动硬件 co-design 正开始直接回应[问题地图](/questions/)中的 P0/P1 命题。

### 主题结构与环比

| 主方向 | 8 月截至 24 日 | 7 月完整月 | 环比 | 判读 |
|---|---:|---:|---:|---|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 57 | 74 | — | 截至 24 日，不完整月，不做环比 |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 20 | 32 | — | 截至 24 日，不完整月，不做环比 |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 41 | 57 | — | 截至 24 日，不完整月，不做环比 |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 38 | 50 | — | 截至 24 日，不完整月，不做环比 |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 45 | 70 | — | 截至 24 日，不完整月，不做环比 |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 18 | 26 | — | 截至 24 日，不完整月，不做环比 |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 12 | 37 | — | 截至 24 日，不完整月，不做环比 |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 55 | 102 | — | 截至 24 日，不完整月，不做环比 |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 14 | 16 | — | 截至 24 日，不完整月，不做环比 |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 7 | 14 | — | 截至 24 日，不完整月，不做环比 |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 11 | 18 | — | 截至 24 日，不完整月，不做环比 |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 7 | 6 | — | 截至 24 日，不完整月，不做环比 |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 1 | 0 | — | 截至 24 日，不完整月，不做环比 |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 1 | 1 | — | 截至 24 日，不完整月，不做环比 |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 1 | 3 | — | 截至 24 日，不完整月，不做环比 |
| **总计** | **328** | **506** | **—** | **不完整月，不计算环比** |

这里仍然展示 7 月绝对数，满足追踪的可追溯性；但由于 8 月只覆盖到 24 日，任何环比百分比都会把截点差异误写成研究变化，因此显式标记为不可比。

### 8 月要验证的六条早期命题

| 命题 | 7 月末触发点 | 升级路标 | 反证/降级条件 |
|---|---|---|---|
| verifier/critic/corrector 成为 VLA 标准侧车 | [RedFlow](https://arxiv.org/abs/2607.27782)、[WCM](https://arxiv.org/abs/2607.29613) | 第三方策略接入同一评价/纠错器，同时报告检测召回、恢复成功率和时延 | 只在自有策略有效，或计算开销抵消成功率收益 |
| world model 用决策效用而非画质生存 | [World Action Planner](https://arxiv.org/abs/2607.27599)、[BWM](https://arxiv.org/abs/2607.29302)、[WCM](https://arxiv.org/abs/2607.29613) | 同算力/同数据下稳定改善规划、策略排序或 RL 样本效率 | 只剩视频指标，与真机成功率相关性低 |
| 触觉优先成为未来预测与接触控制信号 | [TacWAM](https://arxiv.org/abs/2607.28391)、[FA-RDP](https://arxiv.org/abs/2607.28596) | 跨传感器/手型复现，对未知物体保持失败恢复收益 | 增益仅存在于单一硬件、单一材料或封闭任务 |
| 失败覆盖比总数据小时更关键 | [RedFlow](https://arxiv.org/abs/2607.27782)、[CLIFT](https://arxiv.org/abs/2607.29172) | 团队披露失败类型分布、每轮回收成本和新任务上线周期 | 大规模离线预训练在没有部署回流时仍能稳定处理长尾失败 |
| 行为对齐表征成为跨本体中间层 | [Cross-Embodiment Transfer](https://arxiv.org/abs/2607.27549) | 多个独立团队用少量目标本体数据复现增益，并报告负迁移 | 性能仍主要由目标硬件数据量决定 |
| 安全从外挂滤波进入 generative policy 内部 | [Barrier Enhanced Flow Matching](https://arxiv.org/abs/2607.29569) | 在感知不确定、接触动力学偏差下仍保持安全，且不破坏任务语义 | 形式保证只在理想 CBF 假设下成立，真实开放世界误报/漏报过高 |

### 给研究布局的当前判断

1. **不追 8 月月初的“最热 topic”，先看观测性指标。** 恢复成功率、价值误差、接触滑移、进度校准和负迁移比新模型名更能预示瓶颈迁移。
2. **高置信主线是“可评价、可打断、可恢复”的 VLA 执行栈。** 它会同时拉动 critic/verifier、runtime、失败数据与安全边界，比单一算法标签更像一个长期平台机会。
3. **中高置信主线是 world model 的功能分化。** 控制型模型追求短 horizon 决策收益，基础设施型模型追求风险预演、数据生成和策略排序；两者的评估不应混为一个视频质量榜单。
4. **中置信主线是人类中心数据引擎。** ACE-Data-0 表明视角、运动、物体、声音和接触的时空同步可能比纯小时规模更稀缺；但在出现真机下游收益前，仍只是高质量数据信号。

### 月末新增精读锚点

| 论文 | v1 日期 | 一句话贡献 | 证据标签 |
|---|---|---|---|
| [Cross-Embodiment Transfer via Behavior-Aligned Representations](https://arxiv.org/abs/2607.27549) | 2026-07-30 | 证明末端执行器轨迹等行为对齐表征可以绕开关节空间差异，将多本体数据真正转化为新本体增益。 | 真机 · 多任务 · 跨本体 · 开放资产 |
| [World Action Planner: Generalizable Decision-Making with Action-Conditioned World Models](https://arxiv.org/abs/2607.27599) | 2026-07-30 | 让 VLM 提案、动作条件世界模型预演，再用优化与搜索修改计划，把 world model 从表象生成推向决策空间。 | 多任务 · 长时序 · 开放资产 |
| [RedFlow: Redirect Failure into Action-Level Corrections for Flow-matching VLA Policy](https://arxiv.org/abs/2607.27782) | 2026-07-30 | 把失败轨迹拆成动作级负例和可替换的成功动作，以约十分之一的样本量学到部署后纠错。 | 真机 · 多任务 |
| [TacWAM: Anchor-Guided World Action Model with Mechanics-Aware Tactile Prediction](https://arxiv.org/abs/2607.28391) | 2026-07-30 | 将未来触觉中的力、形变和滑移变成 world-action model 的训练监督，但隔离部署时不可见的未来信息。 | 真机 · 多任务 |
| [FA-RDP: A Frequency-Adaptive Reactive Diffusion Policy for Contact-Rich Manipulation](https://arxiv.org/abs/2607.28596) | 2026-07-30 | 用变频策略匹配接触前的多模态路径与接触后的快速力反馈，把控制频率本身变成可学习结构。 | 多任务 · 开放资产 |
| [ACE-Data-0: Human-Centric Ambient Capture as Embodied Data Engine](https://arxiv.org/abs/2607.28625) | 2026-07-30 | 把真实家庭改造为同步采集工厂，将第一/第三人称视频、全身与手部运动、物体轨迹、音频和触觉对齐到同一交互流。 | 多任务 · 长时序 |
| [CLIFT: Turning Gemini Robotics On-Device into Humanoid Specialists via Non-Invasive Closed-Loop Iterative Fine-Tuning](https://arxiv.org/abs/2607.29172) | 2026-07-31 | 将真机部署奖励转换为托管 SFT API 可接受的监督数据，在不访问权重、梯度或损失的情况下形成两轮部署飞轮。 | 真机 · 多任务 · 跨本体 |
| [BWM: A Low-Cost High-Fidelity World Simulator for Robot Learning](https://arxiv.org/abs/2607.29302) | 2026-07-31 | 把动作条件视频模型同时做成仿真器、数据引擎和策略评估器，直接对齐预测质量与机器人决策用途。 | 真机 · 多任务 · 开放资产 |
| [Safe Vision Language Action Models via Barrier Enhanced Flow Matching](https://arxiv.org/abs/2607.29569) | 2026-07-31 | 不在 VLA 输出后外挂安全滤波器，而把 CBF 约束写入 flow-matching 去噪过程，直接约束整个 action chunk。 | 真机 · 多任务 · 跨本体 |
| [WCM: A World Critic Model for Vision-Language-Action Reinforcement Learning](https://arxiv.org/abs/2607.29613) | 2026-07-31 | 让 critic 在估值之外同时预测未来 latent，用世界建模目标补足单帧价值估计对部分可观测控制的状态缺口。 | 真机 · 多任务 |

### 正式发表与 GitHub 更新

- 正式发表母库现为 12,165 条版本，其中窗口内 10,404 条、自动直接相关 2,670 条；新增主要来自期刊 Crossref 记录，不自动等于严格官方同行评审锚点。
- 完整官方 proceedings 仍为 824 条；ICRA 2026 官方 program 与 RSS 2026 官方录用清单共 3,161 条，但后者尚无 RSS 22 proceedings，不进严格分子。
- GitHub 已刷新 42 个已审计仓库的 stars、forks、license 和推送时间，并将 4 个 7 月末新论文仓库单列为待独立采用审计的观察清单。

### 下次更新触发条件

月末关闭 8 月窗口后再计算完整环比；只有当至少 3 项工作、来自 2 个以上独立团队指向同一瓶颈时，才升级为 B 级新兴趋势。

---


## 季度演进

> 季度页观察一个信号如何从出现、扩散走向验证，避免逐月噪声掩盖方法迁移。

### 2025 Q3 · 数据入口重构

人类视频、无标签动作和 egocentric/接触表示成为弱信号主线；flow policy 扩散，触觉首次进入 VLA 统一空间，但世界模型的闭环控制证据仍弱。

本季度共纳入 1022 条直接候选。

| 研究方向 | 候选数 | 季度占比 |
|---|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 93 | 9.1% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 80 | 7.8% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 34 | 3.3% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 91 | 8.9% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 180 | 17.6% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 57 | 5.6% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 83 | 8.1% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 262 | 25.6% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 32 | 3.1% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 38 | 3.7% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 49 | 4.8% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 14 | 1.4% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 1 | 0.1% |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 6 | 0.6% |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 2 | 0.2% |

**阶段证据链：**

- **人类视频开始被拆成可迁移的动作先验（B）**：EC-Flow、H-RDT 与 GR-3 分别从无动作标签视频、双臂人类操作和通用数据配方切入，信号尚未形成单一范式，但都在绕开机器人示教瓶颈。
- **“大脑—小脑”正在从二层变成三系统（C）**：TriVLA 把高层语义、低层动作与 episodic world model 明确拆分；EmbodieDreamer 则让世界模型承担 real-to-sim-to-real 中介。
- **视频生成器开始越过“数据增强”，直接扮演策略（B）**：Video Generators are Robot Policies、Masquerade 与 DiWA 分别尝试直接控制、视频编辑迁移和用世界模型适配 diffusion policy。
- **触觉开始进入 VLA 统一语义空间（C）**：OmniVTLA 不再把触觉仅作为低层状态，而是与视觉、语言和动作对齐。
- **flow matching 正在成为通用策略的新执行底座（B）**：ManiFlow、EC-Flow 与 FLOWER 在通用操控、无标签视频和轻量 generalist policy 三条线上同时采用 flow。
### 2025 Q4 · 规划与预测汇合

fast–slow 形成架构簇，world model 从生成与适配转向后训练、搜索和 MPC；跨本体问题从 adapter 转向数据和动作表示。

本季度共纳入 1073 条直接候选。

| 研究方向 | 候选数 | 季度占比 |
|---|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 153 | 14.3% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 75 | 7.0% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 73 | 6.8% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 88 | 8.2% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 177 | 16.5% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 54 | 5.0% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 58 | 5.4% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 267 | 24.9% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 21 | 2.0% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 33 | 3.1% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 48 | 4.5% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 19 | 1.8% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 1 | 0.1% |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 4 | 0.4% |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 2 | 0.2% |

**阶段证据链：**

- **fast–slow 从隐式分工变成显式训练目标（B）**：VLA-R1、MoTVLA 与上月 VLA-Reasoner 分别用推理增强、统一快慢推理和在线搜索建立高层思考—低层动作分工。
- **世界模型开始进入 VLA 后训练（B）**：VLA-RFT 用 world simulator 给可验证奖励，Ctrl-World 强调可控生成，Latent Action Pretraining 则把预测表征回流到动作学习。
- **视频驱动双臂学习成为数据规模化的第二战场（B）**：DexMan、Parse-Augment-Distill 与真实人类活动视频预训练共同指向少机器人示教的双臂学习。
- **世界模型终于开始用规划成功率证明自己（B）**：WorldPlanner 把 action-conditioned visual world model 接入 MCTS/MPC；跨本体灵巧世界模型与 Ctrl-World 构成独立跟进。
- **跨本体迁移从模型适配转向数据分布设计（B）**：X-Diffusion、InternData-A1 与 X-VLA 分别统一人类示范、合成数据和软提示式跨本体策略。
### 2026 Q1 · 可执行性成为新门槛

latent action world model 进入 in-the-wild 与 RL simulator，Action CoT/异步触发重写大小脑接口，3 月集中出现 executable alignment、长时接触和真实评测。

本季度共纳入 1440 条直接候选。

| 研究方向 | 候选数 | 季度占比 |
|---|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 199 | 13.8% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 68 | 4.7% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 111 | 7.7% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 150 | 10.4% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 245 | 17.0% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 87 | 6.0% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 79 | 5.5% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 320 | 22.2% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 38 | 2.6% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 50 | 3.5% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 76 | 5.3% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 10 | 0.7% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 0 | 0.0% |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 4 | 0.3% |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 3 | 0.2% |

**阶段证据链：**

- **latent action world model 从实验室走向 in-the-wild（B）**：Learning Latent Action World Models In The Wild、Cosmos Policy 与 Motus 分别覆盖野外视频、视频模型微调和统一 latent action。
- **Action CoT 与非对称专家正在重写大小脑接口（B）**：ACoT-VLA、TwinBrainVLA 与 DualVLA 从动作链推理、非对称混合专家和部分解耦三种方式定义高低层接口。
- **人类中心数据被推到跨本体预训练主线（B）**：Being-H0.5、RoboWheel 和 InternData-A1 都把人类数据转化为 generalist policy 的可扩展监督。
- **世界模型开始承担 RL 模拟器与在线自纠错（B）**：WoVR、Self-Correcting VLA 与 World-Gymnast 分别用于后训练模拟、稀疏想象修正和世界模型内 RL。
- **快慢系统开始感知力、接触与完成状态（B）**：FAVLA 将力适应写入 fast–slow 架构，StreamVLA 用 completion-state gating 打破固定 reason–act 循环，自纠错框架补上终止判断。
### 2026 Q2 · 系统工程与触觉闭环

连续推理、coarse-to-fine 调度、3D trace 与 real-time execution 使 VLA 竞争进入系统层；触觉从融合模态升级为预测与 world model 通道。

本季度共纳入 1686 条直接候选。

| 研究方向 | 候选数 | 季度占比 |
|---|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 255 | 15.1% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 91 | 5.4% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 168 | 10.0% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 174 | 10.3% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 254 | 15.1% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 74 | 4.4% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 78 | 4.6% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 368 | 21.8% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 54 | 3.2% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 52 | 3.1% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 83 | 4.9% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 23 | 1.4% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 2 | 0.1% |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 6 | 0.4% |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 4 | 0.2% |

**阶段证据链：**

- **触觉与 world model 开始合流（B）**：Touch Dreaming、FingerEye 与 OmniVTA 把触觉用于未来预测、连续感知和接触世界建模。
- **双系统进入异步 coarse-to-fine 调度（B）**：Libra-VLA、Trace-Conditioned Planning 与 DIAL 不再固定每步完整推理，而是在轨迹、意图和动作层分配不同计算。
- **foundation model 开始接受垂直本体与可控行为约束（C）**：π0.7 强调 steerable generalist policy，Open-H-Embodiment 把医疗机器人纳入大规模基础模型数据。
- **视频模型正在被改造成 generalist policy，而非外置 world model（B）**：Turning Video Models into Generalist Robot Policies、τ0-WM 与 Cosmos Policy 把视频预测和动作生成压进同一训练栈。
- **连续推理开始取代离散 reason–act 循环（B）**：Continuous Reasoning、Libra-VLA 与 StreamVLA 都试图让思考与控制异步或连续发生。

### 2026 年 7 月完整月与 8 月早期快照

7 月完整月中，100K 小时级轨迹仍是数量共识；更领先的 B 级信号集中在 verifier/critic/corrector、进度—记忆—运行时状态、触觉 world model 以及世界模型的规划/评价用途。8 月截至 24 日已有 328 条直接候选，但不完整月不与 7 月直接计算环比；新增证据优先进入[研究问题地图](/questions/)验证既有命题。

---


## 年度综合：从“更大 VLA”转向“可执行、可纠错、可持续学习”

> 主分析期为 2025 年 7 月—2026 年 6 月。同比增长只在同一宽召回查询口径内有效，不代表全部机器人论文的绝对市场份额。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>5221</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>3214</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>84</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>30</strong><span>官方评审锚点</span></div>
</div>

### 15 个方向年度结构

| 方向 | 同比基线 | 主分析期 | 绝对增量 | 主分析期占比 |
|---|---:|---:|---:|---:|
| D1 · [具身基础模型与通才策略](/frontiers/foundation-models) | 124 | 700 | +576 | 13.4% |
| D2 · [分层推理、规划与记忆](/frontiers/reasoning-planning) | 250 | 314 | +64 | 6.0% |
| D3 · [世界模型与预测控制](/frontiers/world-models) | 135 | 386 | +251 | 7.4% |
| D4 · [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 369 | 503 | +134 | 9.6% |
| D5 · [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 582 | 856 | +274 | 16.4% |
| D6 · [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 137 | 272 | +135 | 5.2% |
| D7 · [人机协作与交互学习](/frontiers/human-robot-interaction) | 250 | 298 | +48 | 5.7% |
| D8 · [策略学习与优化](/frontiers/policy-learning) | 913 | 1217 | +304 | 23.3% |
| D9 · [数据引擎与人类视频学习](/frontiers/data-engines) | 96 | 145 | +49 | 2.8% |
| D10 · [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 127 | 173 | +46 | 3.3% |
| D11 · [动作关联的空间感知与表征](/frontiers/spatial-perception) | 154 | 256 | +102 | 4.9% |
| D12 · [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 50 | 66 | +16 | 1.3% |
| D13 · [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 2 | 4 | +2 | 0.1% |
| D14 · [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 16 | 20 | +4 | 0.4% |
| D15 · [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 9 | 11 | +2 | 0.2% |

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

---


## 弱信号探测与未来判断

> 热门 topic 说明共识已经形成；本页寻找的是尚未成为高频标签、却可能提前暴露下一轮瓶颈迁移的“蛛丝马迹”。预测截至 2026-08-04，不是事实陈述。

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

**已经观察到的事实。** fast–slow、异步 coarse-to-fine、连续推理和 real-time VLA 在不同团队连续出现；7 月末又出现接触前后自适应控制频率和直接修改 action-chunk 去噪过程的安全约束。

**我们的判断。** 下一轮有价值的基础设施将是 completion gating、异步缓存、动作 horizon 自适应、边缘部署和故障恢复，而不是单纯增加 VLM 参数。

**论文证据。** [FAVLA: A Force-Adaptive Fast-Slow VLA model for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2602.23648)；[Libra-VLA: Achieving Learning Equilibrium via Asynchronous Coarse-to-Fine Dual-System](https://arxiv.org/abs/2604.24921)；[Continuous Reasoning for Vision-Language-Action](https://arxiv.org/abs/2606.00229)；[Xiaomi-Robotics-0: An Open-Sourced Vision-Language-Action Model with Real-Time Execution](https://arxiv.org/abs/2602.12684)；[FA-RDP: A Frequency-Adaptive Reactive Diffusion Policy for Contact-Rich Manipulation](https://arxiv.org/abs/2607.28596)；[Safe Vision Language Action Models via Barrier Enhanced Flow Matching](https://arxiv.org/abs/2607.29569)

| 验证路标 | 反证条件 |
|---|---|
| 公开评测开始同时报告端到端延迟、控制频率、状态陈旧度和恢复时间；同一模型通过调度改进获得显著真机收益。 | 更强的单体端到端模型在相同硬件上持续压过所有模块化/异步方案，且延迟不再是主要失败源。 |

**战略含义。** 优先关注能跨模型、跨硬件复用的 runtime 与控制中间层。

### 2. “小脑”会被 verifier、critic 与自纠错器重新定义

**置信度 / 时间窗：** 高 · 3–12 个月

**已经观察到的事实。** 在线搜索、稀疏世界想象、自逆动力学奖励和 Action CoT 都在引入动作候选验证；RedFlow 把失败转成动作级纠错，WCM 则用未来 latent 预测重做 critic 的状态估计。

**我们的判断。** 高低层分工将从 planner–policy 两块模型转向 policy + lightweight verifier + recovery loop；验证器可能比慢推理模型更快形成独立组件。

**论文证据。** [VLA-Reasoner: Empowering Vision-Language-Action Models with Reasoning via Online Monte Carlo Tree Search](https://arxiv.org/abs/2509.22643)；[Self-Correcting VLA: Online Action Refinement via Sparse World Imagination](https://arxiv.org/abs/2602.21633)；[EVA: Aligning Video World Models with Executable Robot Actions via Inverse Dynamics Rewards](https://arxiv.org/abs/2603.17808)；[ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://arxiv.org/abs/2601.11404)；[RedFlow: Redirect Failure into Action-Level Corrections for Flow-matching VLA Policy](https://arxiv.org/abs/2607.27782)；[WCM: A World Critic Model for Vision-Language-Action Reinforcement Learning](https://arxiv.org/abs/2607.29613)

| 验证路标 | 反证条件 |
|---|---|
| 第三方策略接入同一 verifier 后获得跨任务提升；评测从平均成功率扩展到失败检测召回率和恢复成功率。 | 验证器只在作者自有策略上有效，跨策略迁移失败，或计算开销抵消全部收益。 |

**战略含义。** 把失败数据、可验证奖励和恢复轨迹视为独立数据资产。

### 3. 数据飞轮将从示教采集转向“部署—失败—修正—再训练”

**置信度 / 时间窗：** 高 · 6–12 个月

**已经观察到的事实。** 从经验学习、100K 小时级轨迹到 ACE 的 75,000 个同步多模态交互 episode，数据竞争正从一次性 dataset 走向持续运营；CLIFT 进一步证明即使只有托管 SFT API，部署失败也能被改写成下一轮训练数据。

**我们的判断。** 数据量仍重要，但最具区分度的会是失败覆盖率、修正效率和任务分布更新速度；真正的 moat 在部署闭环而非公开抓取视频。

**论文证据。** [$π^{*}_{0.6}$: a VLA That Learns From Experience](https://arxiv.org/abs/2511.14759)；[RoboWheel: A Data Engine from Real-World Human Demonstrations for Cross-Embodiment Robotic Learning](https://arxiv.org/abs/2512.02729)；[Scalable Behavior Cloning with Open Data, Training, and Evaluation](https://arxiv.org/abs/2606.27375)；[Xiaomi-Robotics-1: Scaling Vision-Language-Action Models with over 100K Hours of Real-World Trajectories](https://arxiv.org/abs/2607.15330)；[ACE-Data-0: Human-Centric Ambient Capture as Embodied Data Engine](https://arxiv.org/abs/2607.28625)；[CLIFT: Turning Gemini Robotics On-Device into Humanoid Specialists via Non-Invasive Closed-Loop Iterative Fine-Tuning](https://arxiv.org/abs/2607.29172)

| 验证路标 | 反证条件 |
|---|---|
| 团队开始披露每周新增有效轨迹、失败类型覆盖、在线修正样本效率，以及新任务上线周期。 | 离线人类视频预训练在缺少部署回流时仍能稳定获得相同的长尾泛化。 |

**战略含义。** 评估团队时优先看可持续真机接触面和数据治理能力。

### 4. world model 将被迫用闭环控制收益而非视频质量生存

**置信度 / 时间窗：** 高 · 3–9 个月

**已经观察到的事实。** MCTS/MPC、RL simulator、executable alignment 和直接视频策略都把评估目标推向动作；7 月末的 World Action Planner、BWM 和 WCM 分别把世界模型用于计划搜索、策略排序/数据生成和价值估计。

**我们的判断。** 世界模型会分化为两类：为策略提供紧凑 latent dynamics 的控制模型，以及为数据合成服务的高保真生成器；中间态的“漂亮视频模型”将降温。

**论文证据。** [WorldPlanner: Monte Carlo Tree Search and MPC with Action-Conditioned Visual World Models](https://arxiv.org/abs/2511.03077)；[WoVR: World Models as Reliable Simulators for Post-Training VLA Policies with RL](https://arxiv.org/abs/2602.13977)；[EVA: Aligning Video World Models with Executable Robot Actions via Inverse Dynamics Rewards](https://arxiv.org/abs/2603.17808)；[Turning Video Models into Generalist Robot Policies](https://arxiv.org/abs/2605.27817)；[World Action Planner: Generalizable Decision-Making with Action-Conditioned World Models](https://arxiv.org/abs/2607.27599)；[BWM: A Low-Cost High-Fidelity World Simulator for Robot Learning](https://arxiv.org/abs/2607.29302)；[WCM: A World Critic Model for Vision-Language-Action Reinforcement Learning](https://arxiv.org/abs/2607.29613)

| 验证路标 | 反证条件 |
|---|---|
| 论文以同算力下的规划成功率、样本效率或失败恢复率作为主结果，并报告 model bias。 | 生成质量提升能稳定、无需动作对齐地转化为跨机器人控制提升。 |

**战略含义。** 避免把纯视频生成能力估值为机器人世界模型能力。

### 5. 触觉会先成为自纠错与 world model 通道，再成为通用语义模态

**置信度 / 时间窗：** 中高 · 6–18 个月

**已经观察到的事实。** 触觉从 VLA 融合扩展到视触觉世界建模、touch dreaming 和统一理解/预测；TacWAM 开始显式预测力、形变与滑移，FA-RDP 则用力反馈改变接触前后的策略频率。

**我们的判断。** 触觉最先兑现的指标会是接触失败检测、材料/滑移预测和动作恢复，不是开放词汇理解。

**论文证据。** [OmniVTLA: Vision-Tactile-Language-Action Models with Semantic-Aligned Tactile Sensing](https://arxiv.org/abs/2508.08706)；[OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2603.19201)；[Learning Versatile Humanoid Manipulation with Touch Dreaming](https://arxiv.org/abs/2604.13015)；[UniTacVLA: Unified Tactile Understanding and Prediction in Vision Language Action Models](https://arxiv.org/abs/2606.31723)；[ViTacWorld: Scaling Visuo-Tactile World Models for Contact-Rich Robot Manipulation](https://arxiv.org/abs/2607.22530)；[TacWAM: Anchor-Guided World Action Model with Mechanics-Aware Tactile Prediction](https://arxiv.org/abs/2607.28391)；[FA-RDP: A Frequency-Adaptive Reactive Diffusion Policy for Contact-Rich Manipulation](https://arxiv.org/abs/2607.28596)

| 验证路标 | 反证条件 |
|---|---|
| 跨传感器、跨手型 benchmark 出现；加入触觉后恢复率显著提升，并能在未知物体上保持。 | 触觉增益只在单一自研硬件和封闭任务存在，跨设备校准成本长期无法下降。 |

**战略含义。** 关注传感器标准、同步数据格式和自动标定，而不只看单个灵巧手 demo。

### 6. 跨本体迁移将收敛到“规范动作空间 + 小型本体适配器”

**置信度 / 时间窗：** 中高 · 6–18 个月

**已经观察到的事实。** 软提示、跨本体人类示范、通用灵巧手套件和 human-as-humanoid 共同尝试消除动作表示差异；新的行为对齐实验表明，末端执行器轨迹比直接共享关节动作更有机会跨本体迁移。

**我们的判断。** 一个权重直接覆盖所有机器人不太现实；更可能形成共享时空/接触表征，加少量 embodiment adapter 与安全约束。

**论文证据。** [X-VLA: Soft-Prompted Transformer as Scalable Cross-Embodiment Vision-Language-Action Model](https://arxiv.org/abs/2510.10274)；[X-Diffusion: Training Diffusion Policies on Cross-Embodiment Human Demonstrations](https://arxiv.org/abs/2511.04671)；[Being-H0.5: Scaling Human-Centric Robot Learning for Cross-Embodiment Generalization](https://arxiv.org/abs/2601.12993)；[UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://arxiv.org/abs/2603.22264)；[Human-as-Humanoid: Enabling Zero-Shot Humanoid Learning from Ego-Exo Human Videos with Human-Aligned Embodiments](https://arxiv.org/abs/2606.32009)；[Cross-Embodiment Transfer via Behavior-Aligned Representations](https://arxiv.org/abs/2607.27549)

| 验证路标 | 反证条件 |
|---|---|
| 同一共享策略只用少量目标机器人数据即可适配，且负迁移可预测。 | 跨本体性能持续由大规模目标硬件数据决定，共享表征无法显著降低样本量。 |

**战略含义。** 可组合的动作接口与适配工具链比单一“通用权重”更值得长期跟踪。

### 7. 3D trajectory / trace 可能成为大脑与控制器之间的接口标准

**置信度 / 时间窗：** 中 · 6–15 个月

**已经观察到的事实。** 未来 3D/4D 表征、trace-conditioned planning、密集 embodied CoT 和 3D 轨迹引导连续出现。

**我们的判断。** 自然语言计划太抽象、关节动作太具体，3D trace 是可验证且相对跨本体的中间层候选。

**论文证据。** [StemVLA:An Open-Source Vision-Language-Action Model with Future 3D Spatial Geometry Knowledge and 4D Historical Representation](https://arxiv.org/abs/2602.23721)；[Long-Horizon Manipulation via Trace-Conditioned VLA Planning](https://arxiv.org/abs/2604.21924)；[Training Vision-Language-Action Models with Dense Embodied Chain-of-Thought Supervision](https://arxiv.org/abs/2606.30552)；[3D HAMSTER: Bridging Planning and Control in Hierarchical Vision Language Action Models through 3D Trajectory Guidance](https://arxiv.org/abs/2606.31329)；[Cross-Embodiment Transfer via Behavior-Aligned Representations](https://arxiv.org/abs/2607.27549)

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

---


## 问题地图：哪些瓶颈正在接近解决

> 本页把 Alphaist 内部研究材料转为雷达的正交“问题层”；公开站点不暴露私有飞书地址。D1–D15 回答论文主要研究什么；Q0–Q10 回答关键系统瓶颈是否正在被解决。两层不能相加，P0/P1/P2 也不等于 A/B/C 证据等级。

::: warning 证据边界
问题来自五份内部材料的综合；本站只把它作为研究假设来源，趋势等级仍由公开论文、同行评审与真机证据决定。 自动计数只是标题/摘要词表命中的相关工作密度，不自动升级趋势；每项判断仍需结合独立团队、真机、正式发表和反证。
:::

### 总判断

飞书文档抓住了一个真实变化：具身智能的领先差异正在从单一模型扩展到**接触表征—可执行动作—运行时验证—失败回流—软硬件迭代**。但其中既有当前主线，也有开放科学问题和工程门槛，不能全部写成“已确认趋势”。

| ID | 战略优先级 | 研究问题 | 证据 | 性质 | D 类映射 | 最近 12 个完整月词表命中 | 2026-08 截至 24 日 | 严格评审锚点 |
|---|---|---|---|---|---|---:|---:|---:|
| Q0 | P0 | [人类先验—交互表征—动作—失败回流能否形成闭环](#q0) | <span class="signal signal-b">B</span> | 跨方向系统主线 | [D2](/frontiers/reasoning-planning) / [D9](/frontiers/data-engines) / [D12](/frontiers/safety-evaluation) / [D13](/frontiers/continual-deployment-learning) | 403 | 47 | 2 |
| Q1 | P0 | [接触中心的最小充分交互表征](#q1) | <span class="signal signal-b">B</span> | 新兴研究方向 | [D4](/frontiers/dexterous-manipulation) / [D11](/frontiers/spatial-perception) / [D15](/frontiers/embodied-multisensory) / [D3](/frontiers/world-models) | 127 | 13 | 1 |
| Q2 | P0 | [Ego／人类视频到可执行机器人动作](#q2) | <span class="signal signal-a">A</span> | 当前主线 | [D9](/frontiers/data-engines) / [D8](/frontiers/policy-learning) / [D4](/frontiers/dexterous-manipulation) / [D1](/frontiers/foundation-models) | 523 | 36 | 2 |
| Q3 | P0 | [视觉、力觉与触觉的任务条件化消融](#q3) | <span class="signal signal-b">B</span> | 评测驱动方向 | [D15](/frontiers/embodied-multisensory) / [D4](/frontiers/dexterous-manipulation) / [D12](/frontiers/safety-evaluation) | 269 | 25 | 1 |
| Q4 | P1 | [真实接触与仿真扩增的最优组合](#q4) | <span class="signal signal-a">A</span> | 成熟路线中的未解问题 | [D10](/frontiers/simulation-transfer) / [D3](/frontiers/world-models) / [D4](/frontiers/dexterous-manipulation) | 504 | 21 | 2 |
| Q5 | P0 | [站位、视角、支撑与操作的联合 loco-manipulation](#q5) | <span class="signal signal-b">B</span> | 当前主线中的新兴统一问题 | [D5](/frontiers/humanoid-whole-body) / [D6](/frontiers/navigation-mobile-manipulation) / [D11](/frontiers/spatial-perception) / [D2](/frontiers/reasoning-planning) | 172 | 10 | 2 |
| Q6 | P0 | [可跨任务复用的 post-training recipe](#q6) | <span class="signal signal-b">B</span> | 快速升温方向 | [D8](/frontiers/policy-learning) / [D13](/frontiers/continual-deployment-learning) / [D1](/frontiers/foundation-models) / [D7](/frontiers/human-robot-interaction) | 251 | 21 | 1 |
| Q7 | P0 | [失败边界数据与低人力纠正闭环](#q7) | <span class="signal signal-b">B</span> | 新兴系统主线 | [D13](/frontiers/continual-deployment-learning) / [D12](/frontiers/safety-evaluation) / [D9](/frontiers/data-engines) / [D8](/frontiers/policy-learning) | 113 | 10 | 1 |
| Q8 | P1 | [模型、数采设备与机器人硬件共设计](#q8) | <span class="signal signal-c">C</span> | 早期 co-design 假设 | [D4](/frontiers/dexterous-manipulation) / [D9](/frontiers/data-engines) / [D15](/frontiers/embodied-multisensory) / [D12](/frontiers/safety-evaluation) | 80 | 3 | 1 |
| Q9 | P2 | [机器人模型、数据与交互的 scaling law](#q9) | <span class="signal signal-c">C</span> | 高价值早期假设 | [D1](/frontiers/foundation-models) / [D8](/frontiers/policy-learning) / [D9](/frontiers/data-engines) | 33 | 2 | 1 |
| Q10 | P2 | [决策相关世界模型与自动评测闭环（Physical RSI 观察项）](#q10) | <span class="signal signal-b">B</span> | 方向已成形、终局假设仍早期 | [D3](/frontiers/world-models) / [D12](/frontiers/safety-evaluation) / [D13](/frontiers/continual-deployment-learning) / [D2](/frontiers/reasoning-planning) | 84 | 24 | 1 |

### 最近 12 个完整月问题密度

> 时间窗：2025-08—2026-07。这是多标签高召回代理；同一论文可进入多个 Q，不能用行列合计替代主方向统计。

| 问题轴 | 2025-08 | 2025-09 | 2025-10 | 2025-11 | 2025-12 | 2026-01 | 2026-02 | 2026-03 | 2026-04 | 2026-05 | 2026-06 | 2026-07 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Q0 · 人类先验—交互表征—动作—失败回流能否形成闭环 | 10 | 28 | 24 | 16 | 13 | 20 | 31 | 45 | 34 | 58 | 71 | 53 |
| Q1 · 接触中心的最小充分交互表征 | 4 | 8 | 8 | 9 | 2 | 7 | 15 | 18 | 10 | 10 | 22 | 14 |
| Q2 · Ego／人类视频到可执行机器人动作 | 17 | 43 | 37 | 34 | 38 | 29 | 52 | 61 | 31 | 40 | 88 | 53 |
| Q3 · 视觉、力觉与触觉的任务条件化消融 | 9 | 22 | 17 | 11 | 12 | 14 | 30 | 37 | 22 | 22 | 40 | 33 |
| Q4 · 真实接触与仿真扩增的最优组合 | 23 | 50 | 39 | 31 | 23 | 30 | 49 | 55 | 36 | 44 | 77 | 47 |
| Q5 · 站位、视角、支撑与操作的联合 loco-manipulation | 10 | 16 | 10 | 9 | 6 | 6 | 18 | 16 | 13 | 17 | 40 | 11 |
| Q6 · 可跨任务复用的 post-training recipe | 12 | 16 | 18 | 12 | 14 | 13 | 30 | 34 | 13 | 28 | 28 | 33 |
| Q7 · 失败边界数据与低人力纠正闭环 | 6 | 8 | 11 | 3 | 5 | 11 | 6 | 6 | 7 | 11 | 24 | 15 |
| Q8 · 模型、数采设备与机器人硬件共设计 | 2 | 15 | 3 | 5 | 3 | 5 | 2 | 8 | 8 | 4 | 17 | 8 |
| Q9 · 机器人模型、数据与交互的 scaling law | 1 | 1 | 2 | 1 | 0 | 1 | 6 | 4 | 3 | 3 | 6 | 5 |
| Q10 · 决策相关世界模型与自动评测闭环（Physical RSI 观察项） | 1 | 0 | 1 | 1 | 2 | 1 | 1 | 5 | 4 | 10 | 31 | 27 |

### Q0 · 人类先验—交互表征—动作—失败回流能否形成闭环

**战略优先级：** P0 · **外部证据等级：** <span class="signal signal-b">B</span> · **性质：** 跨方向系统主线

**当前判断。** 领先差异正在从单一 backbone 扩展到感知、可执行动作、运行时验证、失败纠正与再训练的完整闭环；模型结构与系统闭环是共同瓶颈。

**对应主方向。** [D2](/frontiers/reasoning-planning)、[D9](/frontiers/data-engines)、[D12](/frontiers/safety-evaluation)、[D13](/frontiers/continual-deployment-learning)

**公开证据：**

- [Continuously Improving Mobile Manipulation with Autonomous Real-World RL](https://proceedings.mlr.press/v270/mendonca25a.html) — 同行评审 · CoRL 2024
- [Optimal Interactive Learning on the Job via Facility Location Planning](https://www.roboticsproceedings.org/rss21/p087.html) — 同行评审 · RSS 2025
- [Beyond Imitation: Self-Improving Robot Policies via Off-Policy Q-Planning](https://arxiv.org/abs/2608.21204) — 最新信号 · 2026-08

**决定性指标。** 从失败到修复的周期；单位真机小时能力增量；自动复位与无接管时长；跨任务复用和旧技能回归。

**反证条件。** 系统组件只在单一任务内有效，闭环成本高于离线重训，或迭代频繁造成能力回归。

### Q1 · 接触中心的最小充分交互表征

**战略优先级：** P0 · **外部证据等级：** <span class="signal signal-b">B</span> · **性质：** 新兴研究方向

**当前判断。** 对接触敏感任务而言，关节角和末端位姿通常不是充分交互状态；值得学习能够预测接触切换、力、滑移与物体状态转移的 interaction latent，但它尚未成为通用接口标准。

**对应主方向。** [D4](/frontiers/dexterous-manipulation)、[D11](/frontiers/spatial-perception)、[D15](/frontiers/embodied-multisensory)、[D3](/frontiers/world-models)

**公开证据：**

- [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html) — 同行评审 · RSS 2025
- [CEDex: Cross-Embodiment Dexterous Grasp Generation at Scale from Human-like Contact Representations](https://arxiv.org/abs/2509.24661) — 预印本 · 接触表征与跨本体
- [CoToGrasp: Contact-Topology-Conditioned Dexterous Grasp Synthesis via Canonical Workspace Learning](https://arxiv.org/abs/2608.19776) — 最新信号 · 2026-08

**决定性指标。** 跨材质与跨手型成功率；滑移/接触切换预测；峰值力与物体损伤；接触失败恢复率。

**反证条件。** 表征只在单一传感器或单一硬件上有效，或不能改善真实机器人控制与失败预测。

### Q2 · Ego／人类视频到可执行机器人动作

**战略优先级：** P0 · **外部证据等级：** <span class="signal signal-a">A</span> · **性质：** 当前主线

**当前判断。** 人类视频适合学习语义、affordance 与运动先验，但必须经过接触 grounding、动作重建、本体适配和少量真机校准才能形成可执行 action。

**对应主方向。** [D9](/frontiers/data-engines)、[D8](/frontiers/policy-learning)、[D4](/frontiers/dexterous-manipulation)、[D1](/frontiers/foundation-models)

**公开证据：**

- [DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://proceedings.mlr.press/v305/xu25b.html) — 同行评审 · CoRL 2025
- [UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html) — 同行评审 · CVPR 2026
- [LAWM-3D: Learning 3D-Aware Latent Actions from Human Videos for Generalizable Robot World Models](https://arxiv.org/abs/2608.05706) — 最新信号 · 2026-08

**决定性指标。** 目标本体动作可执行率；固定真机数据下的样本效率；跨手型/跨本体适配成本；负迁移与不可行动作率。

**反证条件。** 加入人类视频后只改善视觉表征，却不能在固定真机数据预算下提高最终策略。

### Q3 · 视觉、力觉与触觉的任务条件化消融

**战略优先级：** P0 · **外部证据等级：** <span class="signal signal-b">B</span> · **性质：** 评测驱动方向

**当前判断。** 问题不是触觉是否默认必要，而是不同任务的最小充分观测集合，以及额外模态能否稳定改善接触失败检测与恢复。

**对应主方向。** [D15](/frontiers/embodied-multisensory)、[D4](/frontiers/dexterous-manipulation)、[D12](/frontiers/safety-evaluation)

**公开证据：**

- [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html) — 同行评审 · RSS 2025
- [Demystifying When and Why VLAs Fail in Contact-Rich Tasks and How to Fix Them](https://arxiv.org/abs/2608.01402) — 最新信号 · 约 2,500 次真机 rollout
- [VT-MUSE: Multimodal Unified Sequential Visuotactile Representation Learning for Manipulation](https://arxiv.org/abs/2608.21290) — 最新信号 · 2026-08

**决定性指标。** 同硬件同数据预算的模态消融；跨传感器校准成本；未知材料滑移检测；恢复率与控制频率。

**反证条件。** 触觉增益可被腕部视觉或六维力稳定替代，且额外传感的维护成本高于收益。

### Q4 · 真实接触与仿真扩增的最优组合

**战略优先级：** P1 · **外部证据等级：** <span class="signal signal-a">A</span> · **性质：** 成熟路线中的未解问题

**当前判断。** Sim-to-Real 已是主线；在灵巧接触、柔性物体与多材质任务中，当前通常仍需要真实标定或失败数据，但 VIRAL 等工作也证明部分任务可由 sim-only 零样本落地。真正问题是固定总成本下的 sim／real 配方。

**对应主方向。** [D10](/frontiers/simulation-transfer)、[D3](/frontiers/world-models)、[D4](/frontiers/dexterous-manipulation)

**公开证据：**

- [VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/He_VIRAL_Visual_Sim-to-Real_at_Scale_for_Humanoid_Loco-Manipulation_CVPR_2026_paper.html) — 同行评审 · CVPR 2026
- [ParticleFormer: A 3D Point Cloud World Model for Multi-Object, Multi-Material Robotic Manipulation](https://proceedings.mlr.press/v305/huang25c.html) — 同行评审 · CoRL 2025
- [Tactile Sim2Real without Tactile Simulation via Bottlenecked Latent Reconstruction](https://arxiv.org/abs/2608.15897) — 最新信号 · 2026-08

**决定性指标。** 固定真实数据量的增益；未见材质/形变泛化；仿真资产制作成本；真机纠正小时与总迭代周期。

**反证条件。** 高保真仿真投入无法降低真实数据量或提升未见材质表现。

### Q5 · 站位、视角、支撑与操作的联合 loco-manipulation

**战略优先级：** P0 · **外部证据等级：** <span class="signal signal-b">B</span> · **性质：** 当前主线中的新兴统一问题

**当前判断。** 移动、相机视角与支撑接触应被视为任务动作，与手部操作共同受平衡、碰撞、可达性和信息增益约束。

**对应主方向。** [D5](/frontiers/humanoid-whole-body)、[D6](/frontiers/navigation-mobile-manipulation)、[D11](/frontiers/spatial-perception)、[D2](/frontiers/reasoning-planning)

**公开证据：**

- [VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/He_VIRAL_Visual_Sim-to-Real_at_Scale_for_Humanoid_Loco-Manipulation_CVPR_2026_paper.html) — 同行评审 · CVPR 2026
- [ActiveVLA: Injecting Active Perception into Vision-Language-Action Models for Precise 3D Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_ActiveVLA_Injecting_Active_Perception_into_Vision-Language-Action_Models_for_Precise_3D_CVPR_2026_paper.html) — 同行评审 · CVPR 2026
- [HAF: Adapting Generalist VLAs to Humanoid Whole-Body Loco-manipulation via Hierarchical Action Flow and Spectral Latent RL](https://arxiv.org/abs/2608.16837) — 最新信号 · 2026-08

**决定性指标。** 完整任务成功与连续时长；平衡违例和碰撞；不可行动作率；重站位/主动视角带来的控制收益。

**反证条件。** 联合策略并未优于模块化导航+操作，或无法保持可诊断、安全回滚。

### Q6 · 可跨任务复用的 post-training recipe

**战略优先级：** P0 · **外部证据等级：** <span class="signal signal-b">B</span> · **性质：** 快速升温方向

**当前判断。** BC—DAgger—offline/online RL 的组件并不新，真正问题是同一训练流程能否跨任务复用，并降低接管、奖励工程与旧技能回归成本。

**对应主方向。** [D8](/frontiers/policy-learning)、[D13](/frontiers/continual-deployment-learning)、[D1](/frontiers/foundation-models)、[D7](/frontiers/human-robot-interaction)

**公开证据：**

- [ConRFT: A Reinforced Fine-tuning Method for VLA Models via Consistency Policy](https://www.roboticsproceedings.org/rss21/p019.html) — 同行评审 · RSS 2025
- [AutoIntervene: Calibrated Intervention for Action-Chunking Imitation Learning Policies](https://arxiv.org/abs/2608.07065) — 最新信号 · 部署接管与再训练
- [Efficient Real-World Online Reinforcement Learning for Robot Manipulation via Centralized Training and Critic Decomposition](https://arxiv.org/abs/2608.09730) — 最新信号 · 2026-08

**决定性指标。** 单位接管分钟的成功率增量；奖励工程人时；跨任务 recipe 复用率；旧技能回归与 wall-clock 收敛。

**反证条件。** 每个任务仍需专用奖励、专人盯机和重新设计训练流程。

### Q7 · 失败边界数据与低人力纠正闭环

**战略优先级：** P0 · **外部证据等级：** <span class="signal signal-b">B</span> · **性质：** 新兴系统主线

**当前判断。** 总小时数不能单独反映部署价值；应把失败发现、接管、纠正、重训、回归和重新部署做成可归因的数据飞轮。

**对应主方向。** [D13](/frontiers/continual-deployment-learning)、[D12](/frontiers/safety-evaluation)、[D9](/frontiers/data-engines)、[D8](/frontiers/policy-learning)

**公开证据：**

- [Optimal Interactive Learning on the Job via Facility Location Planning](https://www.roboticsproceedings.org/rss21/p087.html) — 同行评审 · RSS 2025
- [RedFlow: Redirect Failure into Action-Level Corrections for Flow-matching VLA Policy](https://arxiv.org/abs/2607.27782) — 预印本 · 动作级失败纠正
- [FACT: Failure-Aware Causal Training for World-Action Models](https://arxiv.org/abs/2608.10232) — 最新信号 · 失败 rollout 进入因果预测

**决定性指标。** 单位真机小时的有效纠正轨迹；失败类型覆盖率；恢复成功率和接管时间；从失败到修复的可追溯率。

**反证条件。** 失败样本只改善见过的错误，跨任务迁移弱，或回训引发明显旧技能回归。

### Q8 · 模型、数采设备与机器人硬件共设计

**战略优先级：** P1 · **外部证据等级：** <span class="signal signal-c">C</span> · **性质：** 早期 co-design 假设

**当前判断。** 热、背隙、漂移、触觉布局、控制频率、维修周转与采集人因会改变数据分布和可执行动作空间，应进入模型实验的共同设计变量。

**对应主方向。** [D4](/frontiers/dexterous-manipulation)、[D9](/frontiers/data-engines)、[D15](/frontiers/embodied-multisensory)、[D12](/frontiers/safety-evaluation)

**公开证据：**

- [DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://proceedings.mlr.press/v305/xu25b.html) — 同行评审 · 软硬件适配
- [Koala Gripper: Co-designing Robotic Grippers and Data-Capture Devices for Scaling Dexterous Manipulation Learning](https://arxiv.org/abs/2608.20546) — 最新信号 · 机器人与数采设备共设计

**决定性指标。** 跨设备/硬件版本策略迁移；连续运行时间与维护小时；由训练失败驱动的硬件 A/B；同数据预算下的样本效率。

**反证条件。** 硬件修改无法在受控预算下改善学习结果，或历史数据因版本变化不可复用。

### Q9 · 机器人模型、数据与交互的 scaling law

**战略优先级：** P2 · **外部证据等级：** <span class="signal signal-c">C</span> · **性质：** 高价值早期假设

**当前判断。** 扩模收益必须与数据多样性、任务熵、真机交互量、推理延迟和控制频率共同扫描，不能把参数量增长直接解释为通用能力。

**对应主方向。** [D1](/frontiers/foundation-models)、[D8](/frontiers/policy-learning)、[D9](/frontiers/data-engines)

**公开证据：**

- [Robot Learning with Super-Linear Scaling](https://www.roboticsproceedings.org/rss21/p025.html) — 同行评审 · RSS 2025
- [Xiaomi-Robotics-1: Scaling Vision-Language-Action Models with over 100K Hours of Real-World Trajectories](https://arxiv.org/abs/2607.15330) — 预印本 · 大规模真实轨迹

**决定性指标。** 等数据/等算力/等交互量曲线；单位算力和真机小时收益；推理延迟与控制频率；扩模后的 post-training 增量。

**反证条件。** 收益主要由数据或任务覆盖解释，参数规模在受控条件下没有稳定边际收益。

### Q10 · 决策相关世界模型与自动评测闭环（Physical RSI 观察项）

**战略优先级：** P2 · **外部证据等级：** <span class="signal signal-b">B</span> · **性质：** 方向已成形、终局假设仍早期

**当前判断。** 用于闭环决策的世界模型应具备动作条件性、决策相关性和可测控制收益；在线使用还要满足时延预算。Physical RSI 尚不是定义稳定的研究类别，应拆成自动评测、数据回流、策略更新和安全部署四个可验证模块。

**对应主方向。** [D3](/frontiers/world-models)、[D12](/frontiers/safety-evaluation)、[D13](/frontiers/continual-deployment-learning)、[D2](/frontiers/reasoning-planning)

**公开证据：**

- [Unified World Models: Coupling Video and Action Diffusion for Pretraining on Large Robotic Datasets](https://www.roboticsproceedings.org/rss21/p015.html) — 同行评审 · RSS 2025
- [FACT: Failure-Aware Causal Training for World-Action Models](https://arxiv.org/abs/2608.10232) — 最新信号 · 因果、失败感知
- [GAUGE: A Measurement-Grounded Benchmark for Physical Fidelity in Simulation Engines and Video World Models](https://arxiv.org/abs/2608.05948) — 最新信号 · 物理真实性评测

**决定性指标。** 同算力闭环规划增益；失败/接触事件预测；model bias 与实时延迟；自动 evaluator 的准确率和抗 reward hacking。

**反证条件。** 生成质量与控制收益长期弱相关，或模型时延、偏差与评价器漏洞抵消样本效率收益。

### 如何进入月度雷达

1. 月度页继续先报告 D1–D15 的互斥主方向数量。
2. 问题层只报告工作密度、证据升级和反证，不制造第二套互斥 taxonomy。
3. A/B/C 由人工证据判断；自动词表只负责发现候选。
4. 每次更新优先检查决定性指标，而不是论文是否使用同一个热门名称。

[下载问题证据 sidecar](/embodied-ai-radar/research-question-evidence.json)

---


## 文档之外：具身研究雷达还必须看什么

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

### 是否需要新增 D16

当前不正式新增。**本体、软体机器人与学习驱动形态设计**值得建立观察池，但升级前应同时满足：至少 3 个独立团队、2 个正式 venue，并且论文主贡献确实是“本体设计与学习联合优化”，而不是纯机械、材料或没有自主学习闭环的硬件论文。

### 最重要的补充判断

- 失败恢复不等于安全保证；风险校准、运行时保障、形式约束和物理攻防需要独立观察。
- Loco-manipulation 不等于开放世界导航；建筑级移动操作、动态语义地图和长期空间记忆仍有独立问题结构。
- 人不只是示范者或接管者，也是协作者、被服务者和共同决策者。
- 单机数据飞轮不等于 fleet learning；异构多机器人协作、策略分发与集体回归测试仍被低估。
- 端侧算力、能耗、网络依赖、标定、维护和数据权利属于战略看板变量，不应伪装成论文主方向。

---


## 全球关键研究组雷达

> 这里追踪 60 个研究执行单元，不做跨组排行榜。母机构、研究院、实验室、独立研究公司和部署观察团队分层保存；默认按最近发生实质变化排序。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>60</strong><span>持续跟踪研究组</span></div>
  <div class="radar-kpi"><strong>18</strong><span>企业/独立组织</span></div>
  <div class="radar-kpi"><strong>30</strong><span>学术实验室</span></div>
  <div class="radar-kpi"><strong>12</strong><span>平台 + 部署观察</span></div>
</div>

::: warning 归属边界
Affiliation 只能证明母机构，不能自动证明具体研究组：NVIDIA 不等于 GEAR，CMU 不等于 RI 或某个实验室，当前员工也不能反向改写历史论文归属。正式动态只使用 G1/G2，G3/G0 保留在复核队列。
:::

<ResearchGroupExplorer />

### 周报与方法

- [2026-W34 周报](/groups/weekly/2026-w34)
- [组织层级图](/groups/organizations)
- [研究组合作网络](/groups/collaboration)
- [组织归属与每周更新方法](/methods/research-groups)
- [旧机构页兼容入口](/analysis/institutions)

---


## 关键研究组周报

| 周次 | 覆盖窗口 | G1/G2 更新 | 变化研究组 | 链接 |
|---|---|---:|---:|---|
| 2026-W34 | 2026-08-17—2026-08-23 | 3 | 3 | [阅读](/groups/weekly/2026-w34) |

---


## 研究组织层级图

> 母机构节点不占 60 个跟踪名额。子研究组的 work 可以向母机构汇总，但母机构不会额外获得第二份 work credit。

### 母机构与直接子组

| 母机构 | 跟踪子组 | 子研究组 |
|---|---:|---|
| [1X Technologies](https://www.1x.tech/about) | 1 | [1X AI](/groups/1x-ai) |
| [Agibot Innovation Shanghai Technology Co Ltd](https://www.agibot.com/research/) | 1 | [AgiBot Research](/groups/agibot-research) |
| [Allen Institute for AI](https://allenai.org/) | 1 | [Ai2 Embodied AI](/groups/ai2-embodied-ai) |
| [Amazon](https://www.amazon.science/) | 2 | [Amazon Frontier AI & Robotics](/groups/amazon-far)、[Amazon Robotics](/groups/amazon-robotics) |
| [Bytedance Seed](https://seed.bytedance.com/en/direction/robotics) | 1 | [ByteDance Seed Robotics](/groups/bytedance-seed-robotics) |
| [Carnegie Mellon University](https://www.cmu.edu/) | 1 | [CMU Robotics Institute](/groups/cmu-robotics-institute) |
| [ETH Zurich](https://ethz.ch/en.html) | 1 | [ETH Zurich Robotic Systems Lab](/groups/eth-rsl) |
| [Ecole Polytechnique Federale De Lausanne](https://www.epfl.ch/labs/lasa/) | 1 | [EPFL Learning Algorithms and Systems Laboratory](/groups/epfl-lasa) |
| [Google](https://www.intrinsic.ai/mission) | 1 | [Intrinsic](/groups/intrinsic) |
| [Google DeepMind](https://deepmind.google/) | 1 | [Google DeepMind Robotics](/groups/google-deepmind-robotics) |
| [Hyundai Motor Group](https://bostondynamics.com/about/) | 1 | [Boston Dynamics](/groups/boston-dynamics) |
| [Massachusetts Institute of Technology](https://www.mit.edu/) | 1 | [MIT CSAIL](/groups/mit-csail) |
| [Meta Fair](https://ai.meta.com/results/?content_types%5B0%5D=publication&research_areas%5B0%5D=robotics) | 1 | [Meta FAIR Embodied AI](/groups/meta-fair-embodied-ai) |
| [NVIDIA](https://www.nvidia.com/) | 3 | [NVIDIA Cosmos Lab](/groups/nvidia-cosmos-lab)、[NVIDIA GEAR](/groups/nvidia-gear)、[NVIDIA Seattle Robotics Lab](/groups/nvidia-seattle-robotics-lab) |
| [Stanford University](https://www.stanford.edu/) | 6 | [Stanford Intelligence through Robotic Interaction at Scale Lab](/groups/stanford-iris)、[Stanford Intelligent and Interactive Autonomous Systems Group](/groups/stanford-iliad)、[Stanford Interactive Perception and Robot Learning Lab](/groups/stanford-iprl)、[Stanford Movement Lab](/groups/stanford-movement-lab)、[Stanford Robotics and Embodied Artificial Intelligence Lab](/groups/stanford-real)、[Stanford Robotics Center](/groups/stanford-robotics-center) |
| [Tesla](https://www.tesla.com/AI) | 1 | [Tesla Optimus](/groups/tesla-optimus) |
| [The University of Hong Kong](https://www.hku.hk/) | 1 | [OpenDriveLab](/groups/opendrivelab) |
| [Toyota Research Institute](https://www.tri.global/) | 1 | [Toyota Research Institute Robotics](/groups/tri-robotics) |
| [Tsinghua University College Of Ai](https://collegeai.tsinghua.edu.cn/en/Research/Research_Groups/E__Interactive_Embodied_Intelligence__Lab.htm) | 1 | [Tsinghua Interactive Embodied Intelligence Lab](/groups/tsinghua-interactive-embodied-intelligence) |
| [Tsinghua University Institute For Ai Industry Research](https://air-dream.netlify.app/) | 2 | [Tsinghua AIR DISCOVER Lab](/groups/tsinghua-discover-lab)、[Tsinghua AIR-DREAM Lab](/groups/tsinghua-air-dream) |
| [Tsinghua University Institute For Interdisciplinary Information Sciences](https://iiis.tsinghua.edu.cn/en/Research/Research_Groups/Tsinghua_Embodied_AI_Lab.htm) | 3 | [Tsinghua Embodied AI Lab](/groups/tsinghua-tea-lab)、[Tsinghua Laboratory of 3D Vision Computing and Machine Intelligence](/groups/tsinghua-li-yi-3d-vision)、[Tsinghua Vision and Robotics Lab](/groups/tsinghua-vision-robotics) |
| [University Of Washington Paul G Allen School](https://weirdlab.cs.washington.edu/) | 3 | [University of Washington Personal Robotics Lab](/groups/uw-personal-robotics)、[University of Washington Robot Learning Laboratory](/groups/uw-robot-learning-lab)、[University of Washington WEIRD Lab](/groups/uw-weird) |
| [University of California, Berkeley](https://www.berkeley.edu/) | 6 | [UC Berkeley AUTOLAB](/groups/berkeley-autolab)、[UC Berkeley Interactive Agents and Collaborative Technologies Lab](/groups/berkeley-interact)、[UC Berkeley Kanazawa AI Research Lab](/groups/berkeley-kair)、[UC Berkeley Robot Learning Lab](/groups/berkeley-robot-learning-lab)、[UC Berkeley Robotic AI and Learning Lab](/groups/berkeley-rail)、[Berkeley AI Research (BAIR)](/groups/berkeley-bair) |

### 独立研究执行单元

| 研究组 | 类型 | 定位 |
|---|---|---|
| [Figure AI](/groups/figure-ai) | 企业/独立研究组织 | 围绕 Figure 人形本体与 Helix 分层 VLA 联合开发的闭源研究和产品团队，重点追踪全身像素到动作控制、触觉灵巧操作、人类视频迁移、长时家庭任务与工业部署。 |
| [Physical Intelligence](/groups/physical-intelligence) | 企业/独立研究组织 | 专注通用机器人基础模型的独立研究公司，以 π 系列 VLA 连接多机器人多任务预训练、开放世界泛化、记忆、实时控制与基于经验的强化学习。官方站未设置可核验的领导岗位页面，因此不从论文作者反推负责人。 |
| [RAI Institute](/groups/rai-institute) | 企业/独立研究组织 | 独立机器人研究院，研究灵巧操作、先进学习控制、机器人交互基础模型、挑战环境导航与机器人社会伦理；与 Boston Dynamics 是合作关系而非同一组织。 |
| [Skild AI](/groups/skild-ai) | 企业/独立研究组织 | 以 omni-bodied intelligence 为核心的机器人基础模型公司，利用大规模仿真、互联网人类视频、遥操作与真实部署形成数据飞轮，目标是一套模型控制多种机器人和任务。 |
| [Agility Robotics](/groups/agility-robotics) | 部署与早期观察 | Deployment watch centered on Digit's commercial workflows, cooperative safety, uptime, fleet orchestration, and learning from operational data. |
| [Apptronik](/groups/apptronik) | 部署与早期观察 | Deployment watch for Apollo hardware, Robot Park data infrastructure, customer pilots, manufacturing readiness, and Google DeepMind model integration. |
| [DYNA Robotics](/groups/dyna-robotics) | 部署与早期观察 | Early strategic deployment watch connecting world-action models, human-video scaling, dexterous dual-arm workflows, real-time recovery, and production data flywheels. |
| [Dexterity AI](/groups/dexterity-ai) | 部署与早期观察 | Deployment watch for production-scale dexterous manipulation, interpretable world models, tactile/force-guided recovery, and multi-arm logistics workflows. |
| [Sanctuary AI](/groups/sanctuary-ai) | 部署与早期观察 | Closed-source and deployment watch for tactile dexterity, multi-embodiment policies, industrial task reliability, and Phoenix data collection. |
| [Unitree Robotics](/groups/unitree-robotics) | 部署与早期观察 | Hardware-and-deployment watch for accessible humanoid and quadruped platforms, whole-body control, dexterous end effectors, datasets, and ecosystem adoption. |

---


## 研究组合作网络

> 合作边只来自同一 canonical work 上的多个 G1/G2 研究组归属。母机构共同出现、作者相识或当前人员关系都不会自动创建合作边。

| 研究组 A | 研究组 B | 共同 work | 代表合作 |
|---|---|---:|---|
| [CMU Learning and Control for Agile Robotics Lab](/groups/cmu-lecar) | [NVIDIA GEAR](/groups/nvidia-gear) | 3 | ASPIRE: Agentic /Skills Discovery for Robotics；ENPIRE: Agentic Robot Policy Self-Improvement in the Real World；VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation |
| [UC Berkeley AUTOLAB](/groups/berkeley-autolab) | [CMU Learning and Control for Agile Robotics Lab](/groups/cmu-lecar) | 2 | ASPIRE: Agentic /Skills Discovery for Robotics；ENPIRE: Agentic Robot Policy Self-Improvement in the Real World |
| [UC Berkeley AUTOLAB](/groups/berkeley-autolab) | [NVIDIA GEAR](/groups/nvidia-gear) | 2 | ASPIRE: Agentic /Skills Discovery for Robotics；ENPIRE: Agentic Robot Policy Self-Improvement in the Real World |
| [UC Berkeley Robot Learning Lab](/groups/berkeley-robot-learning-lab) | [NVIDIA GEAR](/groups/nvidia-gear) | 1 | DreamDojo: A Generalist Robot World Model from Large-Scale Human Videos |
| [UC Berkeley Kanazawa AI Research Lab](/groups/berkeley-kair) | [UC Berkeley Robot Learning Lab](/groups/berkeley-robot-learning-lab) | 1 | Visual Imitation Enables Contextual Humanoid Control |

---


## 15 个研究方向

> 本站当前统一使用以下 15 个主方向。每项工作只计一个主方向，可同时拥有多个关联方向与证据标签。

主方向回答“论文主要研究什么”；[Q0–Q10 问题地图](/questions/)进一步回答接触表征、可执行动作、失败回流和软硬件共设计等跨方向瓶颈是否正在接近解决。

| 编号 | 方向 | 层级 | 纳入工作 |
|---|---|---|---:|
| D1 | [具身基础模型与通才策略](/frontiers/foundation-models) | 模型与系统 | 981 |
| D2 | [分层推理、规划与记忆](/frontiers/reasoning-planning) | 模型与系统 | 839 |
| D3 | [世界模型与预测控制](/frontiers/world-models) | 模型与系统 | 657 |
| D4 | [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | 物理能力 | 1271 |
| D5 | [人形、运动与全身控制](/frontiers/humanoid-whole-body) | 物理能力 | 2031 |
| D6 | [导航与移动操作](/frontiers/navigation-mobile-manipulation) | 物理能力 | 548 |
| D7 | [人机协作与交互学习](/frontiers/human-robot-interaction) | 物理能力 | 801 |
| D8 | [策略学习与优化](/frontiers/policy-learning) | 学习与基础设施 | 2820 |
| D9 | [数据引擎与人类视频学习](/frontiers/data-engines) | 学习与基础设施 | 357 |
| D10 | [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | 学习与基础设施 | 408 |
| D11 | [动作关联的空间感知与表征](/frontiers/spatial-perception) | 学习与基础设施 | 529 |
| D12 | [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | 学习与基础设施 | 168 |
| D13 | [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | 学习与基础设施 | 9 |
| D14 | [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | 物理能力 | 52 |
| D15 | [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | 学习与基础设施 | 29 |

---


## D1 · 具身基础模型与通才策略

> 归属层级：模型与系统。当前纳入 981 个 canonical works；数量、环比和代表工作均按本站当前分类规则生成。

### 纳入边界

核心表达：`vision-language-action`、`vision language action`、`vla model`、`robot foundation model`、`robotic foundation model`、`generalist robot`、`generalist policy`、`general-purpose robot`、`language-conditioned policy`、`language conditioned policy`、`multitask robot policy`、`robot pretraining`、`robot pre-training`、`large-scale robot model`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`manipulation`、`embodied`、`action`、`policy`。

### 月度结构与环比

| 月份 | 本月 | 对比月 | 上月 | 环比增量 | 环比 |
|---|---:|---|---:|---:|---:|
| 2024-07 | 1 | — | 0 | +1 | 新增 |
| 2024-08 | 0 | 2024-07 | 1 | -1 | -100.0% |
| 2024-09 | 6 | 2024-08 | 0 | +6 | 新增 |
| 2024-10 | 6 | 2024-09 | 6 | 0 | 0.0% |
| 2024-11 | 6 | 2024-10 | 6 | 0 | 0.0% |
| 2024-12 | 7 | 2024-11 | 6 | +1 | +16.7% |
| 2025-01 | 6 | 2024-12 | 7 | -1 | -14.3% |
| 2025-02 | 11 | 2025-01 | 6 | +5 | +83.3% |
| 2025-03 | 20 | 2025-02 | 11 | +9 | +81.8% |
| 2025-04 | 3 | 2025-03 | 20 | -17 | -85.0% |
| 2025-05 | 29 | 2025-04 | 3 | +26 | +866.7% |
| 2025-06 | 29 | 2025-05 | 29 | 0 | 0.0% |
| 2025-07 | 20 | 2025-06 | 29 | -9 | -31.0% |
| 2025-08 | 26 | 2025-07 | 20 | +6 | +30.0% |
| 2025-09 | 47 | 2025-08 | 26 | +21 | +80.8% |
| 2025-10 | 59 | 2025-09 | 47 | +12 | +25.5% |
| 2025-11 | 48 | 2025-10 | 59 | -11 | -18.6% |
| 2025-12 | 46 | 2025-11 | 48 | -2 | -4.2% |
| 2026-01 | 30 | 2025-12 | 46 | -16 | -34.8% |
| 2026-02 | 74 | 2026-01 | 30 | +44 | +146.7% |
| 2026-03 | 95 | 2026-02 | 74 | +21 | +28.4% |
| 2026-04 | 49 | 2026-03 | 95 | -46 | -48.4% |
| 2026-05 | 94 | 2026-04 | 49 | +45 | +91.8% |
| 2026-06 | 112 | 2026-05 | 94 | +18 | +19.1% |
| 2026-07 | 74 | 2026-06 | 112 | -38 | -33.9% |

### 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [RoboCasa: Large-Scale Simulation of Household Tasks for Generalist Robots](https://doi.org/10.15607/rss.2024.xx.050) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [$\pi_0.5$: a Vision-Language-Action Model with Open-World Generalization](https://proceedings.mlr.press/v305/black25a.html) | 2025-10-07 | CoRL 2025 | 是 | — |
| [$π_{0.5}$: a Vision-Language-Action Model with Open-World Generalization](https://arxiv.org/abs/2504.16054) | 2025-04-22 | CoRL 2025 | 是 | — |
| [$π_0$: A Vision-Language-Action Flow Model for General Robot Control](https://arxiv.org/abs/2410.24164) | 2024-10-31 | RSS 2025 | 是 | [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) |
| [3DS-VLA: A 3D Spatial-Aware Vision Language Action Model for Robust Multi-Task Manipulation](https://proceedings.mlr.press/v305/li25g.html) | 2025-10-07 | CoRL 2025 | 是 | — |
| [ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://arxiv.org/abs/2601.11404) | 2026-01-16 | CVPR 2026 | 是 | [AgibotTech/ACoT-VLA](https://github.com/AgibotTech/ACoT-VLA) |
| [ActiveVLA: Injecting Active Perception into Vision-Language-Action Models for Precise 3D Robotic Manipulation](https://arxiv.org/abs/2601.08325) | 2026-01-13 | CVPR 2026 | 是 | — |
| [AutoEval: Autonomous Evaluation of Generalist Robot Manipulation Policies in the Real World](https://arxiv.org/abs/2503.24278) | 2025-03-31 | CoRL 2025 | 是 | — |
| [ConRFT: A Reinforced Fine-tuning Method for VLA Models via Consistency Policy](https://arxiv.org/abs/2502.05450) | 2025-02-08 | RSS 2025 | 是 | — |
| [ControlVLA: Few-shot Object-centric Adaptation for Pre-trained Vision-Language-Action Models](https://arxiv.org/abs/2506.16211) | 2025-06-19 | CoRL 2025 | 是 | — |
| [Cross-Hand Latent Representation for Vision-Language-Action Models](https://arxiv.org/abs/2603.10158) | 2026-03-10 | CVPR 2026 | 是 | — |
| [Elucidating the Design Space of Torque-aware Vision-Language-Action Models](https://proceedings.mlr.press/v305/zhang25k.html) | 2025-10-07 | CoRL 2025 | 是 | — |
| [EndoVLA: Dual-Phase Vision-Language-Action for Precise Autonomous Tracking in Endoscopy](https://proceedings.mlr.press/v305/kit25a.html) | 2025-10-07 | CoRL 2025 | 是 | — |
| [FAST: Efficient Action Tokenization for Vision-Language-Action Models](https://arxiv.org/abs/2501.09747) | 2025-01-16 | RSS 2025 | 是 | — |
| [Fine-Tuning Vision-Language-Action Models: Optimizing Speed and Success](https://arxiv.org/abs/2502.19645) | 2025-02-27 | RSS 2025 | 是 | — |
| [FLOWER: Democratizing Generalist Robot Policies with Efficient Vision-Language-Flow Models](https://proceedings.mlr.press/v305/reuss25a.html) | 2025-10-07 | CoRL 2025 | 是 | — |
| [Focusing on What Matters: Object-Agent-centric Tokenization for Vision Language Action models](https://arxiv.org/abs/2509.23655) | 2025-09-28 | CoRL 2025 | 是 | — |
| [Generalist Robot Manipulation beyond Action Labeled Data](https://arxiv.org/abs/2509.19958) | 2025-09-24 | CoRL 2025 | 是 | — |
| [GraspVLA: a Grasping Foundation Model Pre-trained on Billion-scale Synthetic Action Data](https://arxiv.org/abs/2505.03233) | 2025-05-06 | CoRL 2025 | 是 | — |
| [HiRT: Enhancing Robotic Control with Hierarchical Robot Transformers](https://arxiv.org/abs/2410.05273) | 2024-09-12 | CoRL 2024、CoRL 2024 | 是 | — |
| [Long-VLA: Unleashing Long-Horizon Capability of Vision Language Action Model for Robot Manipulation](https://arxiv.org/abs/2508.19958) | 2025-08-27 | CoRL 2025 | 是 | — |
| [Mechanistic interpretability for steering vision-language-action models](https://arxiv.org/abs/2509.00328) | 2025-08-30 | CoRL 2025 | 是 | — |
| [Octo: An Open-Source Generalist Robot Policy](https://doi.org/10.15607/rss.2024.xx.090) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [OpenVLA: An Open-Source Vision-Language-Action Model](https://arxiv.org/abs/2406.09246) | 2024-06-13 | CoRL 2024、CoRL 2024 | 是 | [openvla/openvla](https://github.com/openvla/openvla) |
| [RICL: Adding In-Context Adaptability to Pre-Trained Vision-Language-Action Models](https://arxiv.org/abs/2508.02062) | 2025-08-04 | CoRL 2025 | 是 | — |
| [RoboArena: Distributed Real-World Evaluation of Generalist Robot Policies](https://arxiv.org/abs/2506.18123) | 2025-06-22 | CoRL 2025 | 是 | — |
| [RoboChemist: Long-Horizon and Safety-Compliant Robotic Chemical Experimentation](https://arxiv.org/abs/2509.08820) | 2025-09-10 | CoRL 2025 | 是 | — |
| [RoboMIND: Benchmark on Multi-embodiment Intelligence Normative Data for Robot Manipulation](https://arxiv.org/abs/2412.13877) | 2024-12-18 | RSS 2025 | 是 | — |
| [RoboMonkey: Scaling Test-Time Sampling and Verification for Vision-Language-Action Models](https://arxiv.org/abs/2506.17811) | 2025-06-21 | CoRL 2025 | 是 | — |
| [Shortcut Learning in Generalist Robot Policies: The Role of Dataset Diversity and Fragmentation](https://arxiv.org/abs/2508.06426) | 2025-08-08 | CoRL 2025 | 是 | — |
| [SpatialVLA: Exploring Spatial Representations for Visual-Language-Action Model](https://arxiv.org/abs/2501.15830) | 2025-01-27 | RSS 2025 | 是 | — |
| [Steering Your Generalists: Improving Robotic Foundation Models via Value Guidance](https://arxiv.org/abs/2410.13816) | 2024-10-17 | CoRL 2024、CoRL 2024 | 是 | — |
| [Uni-NaVid: A Video-based Vision-Language-Action Model for Unifying Embodied Navigation Tasks](https://arxiv.org/abs/2412.06224) | 2024-12-09 | RSS 2025 | 是 | — |
| [UniVLA: Learning to Act Anywhere with Task-centric Latent Actions](https://arxiv.org/abs/2505.06111) | 2025-05-09 | RSS 2025 | 是 | — |
| [TinyVLA: Towards Fast, Data-Efficient Vision-Language-Action Models for Robotic Manipulation](https://arxiv.org/abs/2409.12514) | 2024-09-19 | RA-L 2025 | 否 | — |
| [PD-VLA: Accelerating Vision-Language-Action Model Integrated with Action Chunking via Parallel Decoding](https://arxiv.org/abs/2503.02310) | 2025-03-04 | IROS 2025 | 否 | — |
| [Beyond Sight: Finetuning Generalist Robot Policies with Heterogeneous Sensors via Language Grounding](https://arxiv.org/abs/2501.04693) | 2025-01-08 | ICRA 2025 | 否 | — |
| [GeRM: A Generalist Robotic Model with Mixture-of-experts for Quadruped Robot](https://arxiv.org/abs/2403.13358) | — | IROS 2024 | 否 | — |
| [RoboNurse-VLA: Robotic Scrub Nurse System based on Vision-Language-Action Model](https://arxiv.org/abs/2409.19590) | 2024-09-29 | IROS 2025 | 否 | — |
| [ReVLA: Reverting Visual Domain Limitation of Robotic Foundation Models](https://arxiv.org/abs/2409.15250) | 2024-09-23 | ICRA 2025 | 否 | — |
| [Run-time Observation Interventions Make Vision-Language-Action Models More Visually Robust](https://arxiv.org/abs/2410.01971) | 2024-10-02 | ICRA 2025 | 否 | — |
| [MoRE: Unlocking Scalability in Reinforcement Learning for Quadruped Vision-Language-Action Models](https://arxiv.org/abs/2503.08007) | 2025-03-11 | ICRA 2025 | 否 | — |
| [ManiFoundation Model for General-Purpose Robotic Manipulation of Contact Synthesis with Arbitrary Objects and Robots](https://arxiv.org/abs/2405.06964) | — | IROS 2024 | 否 | — |
| [RLRC: Reinforcement Learning-based Recovery for Compressed Vision-Language-Action Models](https://arxiv.org/abs/2506.17639) | 2025-06-21 | RA-L 2026 | 否 | — |
| [A Taxonomy for Evaluating Generalist Robot Manipulation Policies](https://arxiv.org/abs/2503.01238) | 2025-03-03 | RA-L 2026、ICRA 2026 | 否 | — |
| [VLA-Touch: Enhancing Vision-Language-Action Model With Dual-Level Tactile Feedback](https://ieeexplore.ieee.org/document/3692345) | 2026-07-01 | RA-L 2026 | 否 | — |
| [Effective Tuning Strategies for Generalist Robot Manipulation Policies](https://arxiv.org/abs/2410.01220) | 2024-10-02 | ICRA 2025 | 否 | — |
| [CLARE: Continual Learning for Vision-Language-Action Models via Autonomous Adapter Routing and Expansion](https://arxiv.org/abs/2601.09512) | 2026-01-14 | RA-L 2026 | 否 | — |
| [REALM: A Real-to-Sim Validated Benchmark for Generalization in Robotic Manipulation](https://arxiv.org/abs/2512.19562) | 2025-12-22 | RA-L 2026 | 否 | — |
| [PointVLA: Injecting the 3D World into Vision-Language-Action Models](https://arxiv.org/abs/2503.07511) | 2025-03-10 | RA-L 2026 | 否 | — |
| [Beyond alignment: Why robotic foundation models need context-aware safety](https://www.science.org/doi/10.1126/scirobotics.aef2191) | 2026-04-29 | Science Robotics 2026 | 否 | — |
| [BFA++: Hierarchical Best-Feature-Aware Token Prune for Multi-View Vision Language Action Model](https://arxiv.org/abs/2602.20566) | 2026-02-24 | RA-L 2026 | 否 | — |
| [CapsDT: Diffusion-Transformer for Capsule Robot Manipulation](https://arxiv.org/abs/2506.16263) | 2025-06-19 | IROS 2025 | 否 | — |
| [CLAP: A Closed-Loop Diffusion Transformer Action Foundation Model for Robotic Manipulation](https://ieeexplore.ieee.org/document/11246478) | 2025-01-01 | IROS 2025 | 否 | — |
| [ThermoAct:Thermal-Aware Vision-Language-Action Models for Robotic Perception and Decision-Making](https://arxiv.org/abs/2603.25044) | 2026-03-26 | RA-L 2026 | 否 | — |
| [Dynamic Maclaurin-Series-Based Vision-Language-Action Model](https://ieeexplore.ieee.org/document/3683324) | 2026-07-01 | RA-L 2026 | 否 | — |
| [From autonomy to alliance: Robotic foundation models must learn with us, not just for us](https://www.science.org/doi/10.1126/scirobotics.aea1822) | 2026-04-22 | Science Robotics 2026 | 否 | — |
| [$Δ$VLA: Prior-Guided Vision-Language-Action Models via World Knowledge Variation](https://arxiv.org/abs/2603.08361) | 2026-03-09 | 预印本 | 否 | — |
| [$μ$VLA: On Recurrent Memory for Partially Observable Manipulation in VLA Models](https://arxiv.org/abs/2606.12497) | 2026-06-10 | 预印本 | 否 | — |
| [$π_{0.7}$: a Steerable Generalist Robotic Foundation Model with Emergent Capabilities](https://arxiv.org/abs/2604.15483) | 2026-04-16 | 预印本 | 否 | — |

---


## D2 · 分层推理、规划与记忆

> 归属层级：模型与系统。当前纳入 839 个 canonical works；数量、环比和代表工作均按本站当前分类规则生成。

### 纳入边界

核心表达：`system 1`、`system 2`、`system-1`、`system-2`、`fast-slow`、`fast slow`、`planner-policy`、`planner policy`、`hierarchical reasoning`、`hierarchical policy`、`high-level planner`、`low-level policy`、`task planning`、`motion planning`、`vlm planner`、`embodied reasoning`、`chain-of-thought`、`chain of thought`、`long-horizon planning`、`long horizon planning`、`robot memory`、`failure recovery`、`test-time adaptation`、`test time adaptation`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`manipulation`、`embodied`、`action`、`policy`、`control`。

### 月度结构与环比

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
| 2026-07 | 32 | 2026-06 | 36 | -4 | -11.1% |

### 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [AutoGPT+P: Affordance-based Task Planning using Large Language Models](https://arxiv.org/abs/2402.10778) | — | RSS 2024、RSS 2024 | 是 | — |
| [Collision-Affording Point Trees: SIMD-Amenable Nearest Neighbors for Fast Motion Planning with Pointclouds](https://doi.org/10.15607/rss.2024.xx.038) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Motion Planning in Foliated Manifolds using Repetition Roadmap](https://doi.org/10.15607/rss.2024.xx.036) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [A biconvex method for minimum-time motion planning through sequences of convex sets](https://arxiv.org/abs/2504.18978) | 2025-04-26 | RSS 2025 | 是 | — |
| [APRICOT: Active Preference Learning and Constraint-Aware Task Planning with LLMs](https://arxiv.org/abs/2410.19656) | 2024-10-25 | CoRL 2024、CoRL 2024 | 是 | — |
| [Deep Reactive Policy: Learning Reactive Manipulator Motion Planning for Dynamic Environments](https://arxiv.org/abs/2509.06953) | 2025-09-08 | CoRL 2025 | 是 | — |
| [Differentiable GPU-Parallelized Task and Motion Planning](https://arxiv.org/abs/2411.11833) | 2024-11-18 | RSS 2025 | 是 | — |
| [DiffusionSeeder: Seeding Motion Optimization with Diffusion for Rapid Motion Planning](https://arxiv.org/abs/2410.16727) | 2024-10-22 | CoRL 2024、CoRL 2024 | 是 | — |
| [Effective Sampling for Robot Motion Planning Through the Lens of Lattices](https://arxiv.org/abs/2502.04908) | 2025-02-07 | RSS 2025 | 是 | — |
| [Hierarchical Temporal Logic Task and Motion Planning for Multi-Robot Systems](https://arxiv.org/abs/2504.18899) | 2025-04-26 | RSS 2025 | 是 | — |
| [INTERPRET: Interactive Predicate Learning from Language Feedback for Generalizable Task Planning](https://doi.org/10.15607/rss.2024.xx.034) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [KoopMotion: Learning Almost Divergence Free Koopman Flow Fields for Motion Planning](https://arxiv.org/abs/2509.09074) | 2025-09-11 | CoRL 2025 | 是 | — |
| [Language-Augmented Symbolic Planner for Open-World Task Planning](https://arxiv.org/abs/2407.09792) | 2024-07-13 | RSS 2024、RSS 2024 | 是 | — |
| [Language-guided Manipulator Motion Planning with Bounded Task Space](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Meta-Optimization and Program Search using Language Models for Task and Motion Planning](https://arxiv.org/abs/2505.03725) | 2025-05-06 | CoRL 2025 | 是 | — |
| [Multi-agent Reinforcement Learning with Hybrid Action Space for Free Gait Motion Planning of Hexapod Robots](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Multimodal Fused Learning for Solving the Generalized Traveling Salesman Problem in Robotic Task Planning](https://arxiv.org/abs/2506.16931) | 2025-06-20 | CoRL 2025 | 是 | — |
| [NOD-TAMP: Generalizable Long-Horizon Planning with Neural Object Descriptors](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Partially Observable Task and Motion Planning with Uncertainty and Risk Awareness](https://doi.org/10.15607/rss.2024.xx.118) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Planning from Point Clouds over Continuous Actions for Multi-object Rearrangement](https://arxiv.org/abs/2509.04645) | 2025-09-04 | CoRL 2025 | 是 | — |
| [Robotic Control via Embodied Chain-of-Thought Reasoning](https://arxiv.org/abs/2407.08693) | 2024-07-11 | CoRL 2024、CoRL 2024 | 是 | — |
| [Search-TTA: A Multimodal Test-Time Adaptation Framework for Visual Search in the Wild](https://arxiv.org/abs/2505.11350) | 2025-05-16 | CoRL 2025 | 是 | — |
| [Superfast Configuration-Space Convex Set Computation on GPUs for Online Motion Planning](https://arxiv.org/abs/2504.10783) | 2025-04-15 | RSS 2025 | 是 | — |
| [Train-Once Plan-Anywhere Kinodynamic Motion Planning via Diffusion Trees](https://arxiv.org/abs/2508.21001) | 2025-08-28 | CoRL 2025 | 是 | — |
| [Training Strategies for Efficient Embodied Reasoning](https://arxiv.org/abs/2505.08243) | 2025-05-13 | CoRL 2025 | 是 | — |
| [SMART-LLM: Smart Multi-Agent Robot Task Planning using Large Language Models](https://arxiv.org/abs/2309.10062) | — | IROS 2024 | 否 | — |
| [AutoTAMP: Autoregressive Task and Motion Planning with LLMs as Translators and Checkers](https://arxiv.org/abs/2306.06531) | — | ICRA 2024 | 否 | — |
| [CoPa: General Robotic Manipulation through Spatial Constraints of Parts with Foundation Models](https://arxiv.org/abs/2403.08248) | — | IROS 2024 | 否 | — |
| [ISR-LLM: Iterative Self-Refined Large Language Model for Long-Horizon Sequential Task Planning](https://arxiv.org/abs/2308.13724) | — | ICRA 2024 | 否 | — |
| [GPT-4V(ision) for Robotics: Multimodal Task Planning From Human Demonstration](https://arxiv.org/abs/2311.12015) | — | RA-L 2024 | 否 | — |
| [LLM3: Large Language Model-based Task and Motion Planning with Motion Failure Reasoning](https://arxiv.org/abs/2403.11552) | — | IROS 2024 | 否 | — |
| [Guiding Long-Horizon Task and Motion Planning with Vision Language Models](https://arxiv.org/abs/2410.02193) | 2024-10-03 | ICRA 2025 | 否 | — |
| [EDMP: Ensemble-of-costs-guided Diffusion for Motion Planning](https://arxiv.org/abs/2309.11414) | — | ICRA 2024 | 否 | — |
| [Statler: State-Maintaining Language Models for Embodied Reasoning](https://arxiv.org/abs/2306.17840) | — | ICRA 2024 | 否 | — |
| [Vision-Language Interpreter for Robot Task Planning](https://arxiv.org/abs/2311.00967) | — | ICRA 2024 | 否 | — |
| [DELTA: Decomposed Efficient Long-Term Robot Task Planning Using Large Language Models](https://arxiv.org/abs/2404.03275) | — | ICRA 2025 | 否 | — |
| [VLM See, Robot Do: Human Demo Video to Robot Action Plan via Vision Language Model](https://arxiv.org/abs/2410.08792) | 2024-10-11 | IROS 2025 | 否 | — |
| [GRID: Scene-Graph-based Instruction-driven Robotic Task Planning](https://arxiv.org/abs/2309.07726) | — | IROS 2024 | 否 | — |
| [Towards Generalizable Vision-Language Robotic Manipulation: A Benchmark and LLM-guided 3D Policy](https://arxiv.org/abs/2410.01345) | 2024-10-02 | ICRA 2025 | 否 | — |
| [Can Vehicle Motion Planning Generalize to Realistic Long-tail Scenarios?](https://arxiv.org/abs/2404.07569) | — | IROS 2024 | 否 | — |
| [Motion Planning Diffusion: Learning and Adapting Robot Motion Planning with Diffusion Models](https://arxiv.org/abs/2412.19948) | 2024-12-27 | T-RO 2025 | 否 | — |
| [LiP-LLM: Integrating Linear Programming and dependency graph with Large Language Models for multi-robot task planning](https://arxiv.org/abs/2410.21040) | 2024-10-28 | RA-L 2025 | 否 | — |
| [LLM-as-BT-Planner: Leveraging LLMs for Behavior Tree Generation in Robot Task Planning](https://arxiv.org/abs/2409.10444) | 2024-09-16 | ICRA 2025 | 否 | — |
| [ROG-Map: An Efficient Robocentric Occupancy Grid Map for Large-scene and High-resolution LiDAR-based Motion Planning](https://arxiv.org/abs/2302.14819) | — | IROS 2024 | 否 | — |
| [Non-Euclidean motion planning with graphs of geodesically convex sets](https://arxiv.org/abs/2305.06341) | — | IJRR 2024 | 否 | — |
| [DiMSam: Diffusion Models as Samplers for Task and Motion Planning under Partial Observability](https://arxiv.org/abs/2306.13196) | — | IROS 2024 | 否 | — |
| [Kinematic-aware Prompting for Generalizable Articulated Object Manipulation with LLMs](https://arxiv.org/abs/2311.02847) | — | ICRA 2024 | 否 | — |
| [Safety Aware Task Planning via Large Language Models in Robotics](https://arxiv.org/abs/2503.15707) | 2025-03-19 | IROS 2025 | 否 | — |
| [Sce2DriveX: A Generalized MLLM Framework for Scene-to-Drive Learning](https://arxiv.org/abs/2502.14917) | — | RA-L 2025、ICRA 2026 | 否 | — |
| [Extended Tree Search for Robot Task and Motion Planning](https://arxiv.org/abs/2103.05456) | — | IROS 2024 | 否 | — |
| [FLTRNN: Faithful Long-Horizon Task Planning for Robotics with Large Language Models](https://ieeexplore.ieee.org/document/10611663) | 2024-05-13 | ICRA 2024 | 否 | — |
| [db-CBS: Discontinuity-Bounded Conflict-Based Search for Multi-Robot Kinodynamic Motion Planning](https://arxiv.org/abs/2309.16445) | — | ICRA 2024 | 否 | — |
| [iDb-A*: Iterative Search and Optimization for Optimal Kinodynamic Motion Planning](https://arxiv.org/abs/2311.03553) | — | T-RO 2025 | 否 | — |
| [Conflict-Based Model Predictive Control for Scalable Multi-Robot Motion Planning](https://arxiv.org/abs/2303.01619) | — | ICRA 2024 | 否 | — |
| [RoboDexVLM: Visual Language Model-Enabled Task Planning and Motion Control for Dexterous Robot Manipulation](https://arxiv.org/abs/2503.01616) | 2025-03-03 | IROS 2025 | 否 | — |
| [GG-LLM: Geometrically Grounding Large Language Models for Zero-shot Human Activity Forecasting in Human-Aware Task Planning](https://arxiv.org/abs/2310.20034) | — | ICRA 2024 | 否 | — |
| [Multi-Modal MPPI and Active Inference for Reactive Task and Motion Planning](https://arxiv.org/abs/2312.02328) | — | RA-L 2024 | 否 | — |
| [Real-time Whole-body Motion Planning for Mobile Manipulators Using Environment-adaptive Search and Spatial-temporal Optimization](https://ieeexplore.ieee.org/document/10610192) | 2024-05-13 | ICRA 2024 | 否 | — |
| [Fast and Accurate Task Planning using Neuro-Symbolic Language Models and Multi-level Goal Decomposition](https://arxiv.org/abs/2409.19250) | 2024-09-28 | ICRA 2025 | 否 | — |
| [iDb-RRT: Sampling-based Kinodynamic Motion Planning with Motion Primitives and Trajectory Optimization](https://arxiv.org/abs/2403.10745) | — | IROS 2024 | 否 | — |

---


## D3 · 世界模型与预测控制

> 归属层级：模型与系统。当前纳入 657 个 canonical works；数量、环比和代表工作均按本站当前分类规则生成。

### 纳入边界

核心表达：`world model`、`action-conditioned video`、`action conditioned video`、`robot video prediction`、`latent action`、`predictive dynamics`、`dynamics model`、`model-based planning`、`model based planning`、`generative simulation`、`video prediction for robot`、`future prediction`、`action-conditioned generation`、`action conditioned generation`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`manipulation`、`action`、`control`、`policy`、`planning`、`interaction`、`embodied`、`dynamics`。

### 月度结构与环比

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
| 2026-07 | 57 | 2026-06 | 83 | -26 | -31.3% |

### 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [Diffusion Dynamics Models with Generative State Estimation for Cloth Manipulation](https://arxiv.org/abs/2503.11999) | 2025-03-15 | CoRL 2025 | 是 | — |
| [DreamGen: Unlocking Generalization in Robot Learning through Video World Models](https://arxiv.org/abs/2505.12705) | 2025-05-19 | CoRL 2025 | 是 | [NVIDIA/GR00T-Dreams](https://github.com/NVIDIA/GR00T-Dreams) |
| [Dynamic 3D Gaussian Tracking for Graph-Based Neural Dynamics Modeling](https://arxiv.org/abs/2410.18912) | 2024-10-24 | CoRL 2024、CoRL 2024 | 是 | — |
| [LaDi-WM: A Latent Diffusion-based World Model for Predictive Manipulation](https://arxiv.org/abs/2505.11528) | 2025-05-13 | CoRL 2025 | 是 | — |
| [Learned Perceptive Forward Dynamics Model for Safe and Platform-aware Robotic Navigation](https://arxiv.org/abs/2504.19322) | 2025-04-27 | RSS 2025 | 是 | — |
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
| [RoboPack: Learning Tactile-Informed Dynamics Models for Dense Packing](https://arxiv.org/abs/2407.01418) | 2024-07-01 | RSS 2024、RSS 2024 | 是 | — |
| [SLAC: Simulation-Pretrained Latent Action Space for Whole-Body Real-World RL](https://proceedings.mlr.press/v305/hu25b.html) | 2025-10-07 | CoRL 2025 | 是 | — |
| [Unified World Models: Coupling Video and Action Diffusion for Pretraining on Large Robotic Datasets](https://arxiv.org/abs/2504.02792) | 2025-04-03 | RSS 2025 | 是 | — |
| [WoMAP: World Models For Embodied Open-Vocabulary Object Localization](https://arxiv.org/abs/2506.01600) | 2025-06-02 | CoRL 2025 | 是 | — |
| [World Models for General Surgical Grasping](https://doi.org/10.15607/rss.2024.xx.041) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [A review of learning-based dynamics models for robotic manipulation](https://www.science.org/doi/10.1126/scirobotics.adt1497) | 2025-09-17 | Science Robotics 2025 | 否 | — |
| [WMNav: Integrating Vision-Language Models into World Models for Object Goal Navigation](https://arxiv.org/abs/2503.02247) | 2025-03-04 | IROS 2025 | 否 | — |
| [Renderworld: World Model with Self-Supervised 3D Label](https://arxiv.org/abs/2409.11356) | — | ICRA 2025 | 否 | — |
| [World Model-based Perception for Visual Legged Locomotion](https://arxiv.org/abs/2409.16784) | 2024-09-25 | ICRA 2025 | 否 | — |
| [AnyCar to Anywhere: Learning Universal Dynamics Model for Agile and Adaptive Mobility](https://arxiv.org/abs/2409.15783) | 2024-09-24 | ICRA 2025 | 否 | — |
| [MoDem-V2: Visuo-Motor World Models for Real-World Robot Manipulation](https://arxiv.org/abs/2309.14236) | — | ICRA 2024 | 否 | — |
| [Probing Multimodal LLMs as World Models for Driving](https://arxiv.org/abs/2405.05956) | — | RA-L 2025、ICRA 2026 | 否 | — |
| [FlowDreamer: A RGB-D World Model with Flow-based Motion Representations for Robot Manipulation](https://arxiv.org/abs/2505.10075) | 2025-05-15 | RA-L 2026、ICRA 2026 | 否 | — |
| [TWIST: Teacher-Student World Model Distillation for Efficient Sim-to-Real Transfer](https://arxiv.org/abs/2311.03622) | — | ICRA 2024 | 否 | — |
| [X-MOBILITY: End-To-End Generalizable Navigation via World Modeling](https://arxiv.org/abs/2410.17491) | 2024-10-23 | ICRA 2025 | 否 | — |
| [LUMOS: Language-Conditioned Imitation Learning with World Models](https://arxiv.org/abs/2503.10370) | 2025-03-13 | ICRA 2025 | 否 | — |
| [Inference-Time Enhancement of Generative Robot Policies via Predictive World Modeling](https://arxiv.org/abs/2502.00622) | 2025-02-02 | RA-L 2026 | 否 | — |
| [Planning with Adaptive World Models for Autonomous Driving](https://arxiv.org/abs/2406.10714) | — | ICRA 2025 | 否 | — |
| [ManiGaussian++: General Robotic Bimanual Manipulation with Hierarchical Gaussian World Model](https://arxiv.org/abs/2506.19842) | 2025-06-24 | IROS 2025 | 否 | — |
| [R-AIF: Solving Sparse-Reward Robotic Tasks from Pixels with Active Inference and World Models](https://arxiv.org/abs/2409.14216) | 2024-09-21 | ICRA 2025 | 否 | — |
| [Residual Learning towards High-fidelity Vehicle Dynamics Modeling with Transformer](https://arxiv.org/abs/2502.11800) | 2025-02-17 | RA-L 2025 | 否 | — |
| [QT-TDM: Planning With Transformer Dynamics Model and Autoregressive Q-Learning](https://arxiv.org/abs/2407.18841) | — | RA-L 2025 | 否 | — |
| [Learning Coordinated Bimanual Manipulation Policies using State Diffusion and Inverse Dynamics Models](https://arxiv.org/abs/2503.23271) | 2025-03-30 | ICRA 2025 | 否 | — |
| [Learning Multiple Probabilistic Decisions from Latent World Model in Autonomous Driving](https://arxiv.org/abs/2409.15730) | 2024-09-24 | ICRA 2025 | 否 | — |
| [Online Adaptation of Learned Vehicle Dynamics Model with Meta-Learning Approach](https://arxiv.org/abs/2409.14950) | 2024-09-23 | IROS 2024 | 否 | — |
| [A Deep Reinforcement Learning Framework and Methodology for Reducing the Sim-to-Real Gap in ASV Navigation](https://arxiv.org/abs/2407.08263) | 2024-07-11 | IROS 2024 | 否 | — |
| [OccTENS: 3D Occ upancy World Model via Te mporal N ext- S cale Prediction](https://arxiv.org/abs/2509.03887) | — | RA-L 2026、ICRA 2026 | 否 | — |
| [Data-Driven Dynamics Modeling of Miniature Robotic Blimps Using Neural ODEs With Parameter Auto-Tuning](https://arxiv.org/abs/2404.18580) | — | RA-L 2024 | 否 | — |
| [From Pixels to Predicates: Learning Symbolic World Models via Pretrained VLMs](https://ieeexplore.ieee.org/document/3662533) | 2026-04-01 | RA-L 2026 | 否 | — |
| [Learning dynamics models for velocity estimation in autonomous racing](https://arxiv.org/abs/2408.15610) | 2024-08-28 | IROS 2024 | 否 | — |
| [Online Calibration of a Single-Track Ground Vehicle Dynamics Model by Tight Fusion with Visual-Inertial Odometry](https://arxiv.org/abs/2309.11148) | — | ICRA 2024 | 否 | — |
| [STAGE: A Stream-Centric Generative World Model for Long-Horizon Driving-Scene Simulation](https://arxiv.org/abs/2506.13138) | — | IROS 2025 | 否 | — |
| [Dynamics Modeling using Visual Terrain Features for High-Speed Autonomous Off-Road Driving](https://arxiv.org/abs/2412.00581) | 2024-11-30 | ICRA 2025 | 否 | — |
| [Imagine-2-Drive: Leveraging High-Fidelity World Models via Multi-Modal Diffusion Policies](https://arxiv.org/abs/2411.10171) | 2024-11-15 | IROS 2025 | 否 | — |
| [KUDA: Keypoints to Unify Dynamics Learning and Visual Prompting for Open-Vocabulary Robotic Manipulation](https://arxiv.org/abs/2503.10546) | 2025-03-13 | ICRA 2025 | 否 | — |
| [Task-Oriented Active Learning of Model Preconditions for Inaccurate Dynamics Models](https://arxiv.org/abs/2401.04007) | — | ICRA 2024 | 否 | — |
| [Automatic Configuration of Multi-Agent Model Predictive Controllers based on Semantic Graph World Models](https://arxiv.org/abs/2311.01180) | — | ICRA 2024 | 否 | — |
| [LIMT: Language-Informed Multi-Task Visual World Models](https://arxiv.org/abs/2407.13466) | 2024-07-18 | ICRA 2025 | 否 | — |
| [Model-based Policy Optimization using Symbolic World Model](https://arxiv.org/abs/2407.13518) | 2024-07-18 | IROS 2024 | 否 | — |
| [PerlAD: Towards Enhanced Closed-loop End-to-end Autonomous Driving with Pseudo-simulation-based Reinforcement Learning](https://arxiv.org/abs/2603.14908) | 2026-03-16 | RA-L 2026 | 否 | — |
| [PosePilot: Steering Camera Pose for Generative World Models with Self-supervised Depth](https://arxiv.org/abs/2505.01729) | — | IROS 2025 | 否 | — |
| [SimWorld: A Unified Benchmark for Simulator-Conditioned Scene Generation via World Model](https://arxiv.org/abs/2503.13952) | — | IROS 2025 | 否 | — |
| [Behavior-Controllable Stable Dynamics Models on Riemannian Configuration Manifolds](https://ieeexplore.ieee.org/document/3647763) | 2026-01-01 | T-RO 2026、ICRA 2026 | 否 | — |
| [Beyond Simulation: Benchmarking World Models for Planning and Causality in Autonomous Driving](https://arxiv.org/abs/2508.01922) | 2025-08-03 | ICRA 2025 | 否 | — |
| [Real-World Robot Control by Deep Active Inference With a Temporally Hierarchical World Model](https://arxiv.org/abs/2512.01924) | 2025-12-01 | RA-L 2026、ICRA 2026 | 否 | — |

---


## D4 · 灵巧、双臂与接触操作

> 归属层级：物理能力。当前纳入 1271 个 canonical works；数量、环比和代表工作均按本站当前分类规则生成。

### 纳入边界

核心表达：`dexterous`、`in-hand`、`in hand manipulation`、`bimanual`、`dual-arm`、`dual arm`、`tactile manipulation`、`contact-rich`、`contact rich`、`hand-arm`、`hand arm`、`multifinger`、`multi-finger`、`robotic hand`、`grasp synthesis`、`grasping policy`、`non-prehensile`、`nonprehensile`、`tool use`、`deformable object manipulation`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`manipulation`、`hand`、`grasp`、`tactile`、`contact`。

### 月度结构与环比

| 月份 | 本月 | 对比月 | 上月 | 环比增量 | 环比 |
|---|---:|---|---:|---:|---:|
| 2024-07 | 21 | — | 0 | +21 | 新增 |
| 2024-08 | 21 | 2024-07 | 21 | 0 | 0.0% |
| 2024-09 | 30 | 2024-08 | 21 | +9 | +42.9% |
| 2024-10 | 33 | 2024-09 | 30 | +3 | +10.0% |
| 2024-11 | 31 | 2024-10 | 33 | -2 | -6.1% |
| 2024-12 | 24 | 2024-11 | 31 | -7 | -22.6% |
| 2025-01 | 15 | 2024-12 | 24 | -9 | -37.5% |
| 2025-02 | 31 | 2025-01 | 15 | +16 | +106.7% |
| 2025-03 | 46 | 2025-02 | 31 | +15 | +48.4% |
| 2025-04 | 33 | 2025-03 | 46 | -13 | -28.3% |
| 2025-05 | 39 | 2025-04 | 33 | +6 | +18.2% |
| 2025-06 | 45 | 2025-05 | 39 | +6 | +15.4% |
| 2025-07 | 23 | 2025-06 | 45 | -22 | -48.9% |
| 2025-08 | 22 | 2025-07 | 23 | -1 | -4.3% |
| 2025-09 | 46 | 2025-08 | 22 | +24 | +109.1% |
| 2025-10 | 38 | 2025-09 | 46 | -8 | -17.4% |
| 2025-11 | 32 | 2025-10 | 38 | -6 | -15.8% |
| 2025-12 | 18 | 2025-11 | 32 | -14 | -43.8% |
| 2026-01 | 27 | 2025-12 | 18 | +9 | +50.0% |
| 2026-02 | 49 | 2026-01 | 27 | +22 | +81.5% |
| 2026-03 | 74 | 2026-02 | 49 | +25 | +51.0% |
| 2026-04 | 42 | 2026-03 | 74 | -32 | -43.2% |
| 2026-05 | 47 | 2026-04 | 42 | +5 | +11.9% |
| 2026-06 | 85 | 2026-05 | 47 | +38 | +80.9% |
| 2026-07 | 50 | 2026-06 | 85 | -35 | -41.2% |

### 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [Collaborative Planar Pushing of Polytopic Objects with Multiple Robots in Complex Scenes](https://arxiv.org/abs/2405.07908) | — | RSS 2024、RSS 2024 | 是 | — |
| [Demonstrating Learning from Humans on Open-Source Dexterous Robot Hands](https://doi.org/10.15607/rss.2024.xx.014) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [$\texttt{SPIN}$: distilling $\texttt{Skill-RRT}$ for long-horizon prehensile and non-prehensile manipulation](https://arxiv.org/abs/2502.18015) | 2025-02-25 | CoRL 2025 | 是 | — |
| [3D-ViTac: Learning Fine-Grained Manipulation with Visuo-Tactile Sensing](https://arxiv.org/abs/2410.24091) | 2024-10-31 | CoRL 2024、CoRL 2024 | 是 | — |
| [A low-cost and lightweight 6 DoF bimanual arm for dynamic and contact-rich manipulation](https://arxiv.org/abs/2502.16908) | 2025-02-24 | RSS 2025 | 是 | — |
| [ACE: A Cross-platform and visual-Exoskeletons System for Low-Cost Dexterous Teleoperation](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [ALOHA Unleashed: A Simple Recipe for Robot Dexterity](https://arxiv.org/abs/2410.13126) | 2024-10-17 | CoRL 2024、CoRL 2024 | 是 | — |
| [AnyRotate: Gravity-Invariant In-Hand Object Rotation with Sim-to-Real Touch](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [APEX-MR: Multi-Robot Asynchronous Planning and Execution for Cooperative Assembly](https://arxiv.org/abs/2503.15836) | 2025-03-20 | RSS 2025 | 是 | — |
| [ARCH: Hierarchical Hybrid Learning for Long-Horizon Contact-Rich Robotic Assembly](https://arxiv.org/abs/2409.16451) | 2024-09-24 | CoRL 2025 | 是 | — |
| [Bimanual Dexterity for Complex Tasks](https://arxiv.org/abs/2411.13677) | 2024-11-20 | CoRL 2024、CoRL 2024 | 是 | — |
| [Bridging Perception and Action: Spatially-Grounded Mid-Level Representations for Robot Generalization](https://arxiv.org/abs/2506.06196) | 2025-06-06 | RSS 2025 | 是 | — |
| [ClutterDexGrasp: A Sim-to-Real System for General Dexterous Grasping in Cluttered Scenes](https://arxiv.org/abs/2506.14317) | 2025-06-17 | CoRL 2025 | 是 | — |
| [COMBO-Grasp: Learning Constraint-Based Manipulation for Bimanual Occluded Grasping](https://arxiv.org/abs/2502.08054) | 2025-02-12 | CoRL 2025 | 是 | — |
| [Complementarity-Free Multi-Contact Modeling and Optimization for Dexterous Manipulation](https://arxiv.org/abs/2408.07855) | 2024-08-14 | RSS 2025 | 是 | — |
| [CordViP: Correspondence-based Visuomotor Policy for Dexterous Manipulation in Real-World](https://arxiv.org/abs/2502.08449) | 2025-02-12 | RSS 2025 | 是 | — |
| [D-CODA: Diffusion for Coordinated Dual-Arm Data Augmentation](https://arxiv.org/abs/2505.04860) | 2025-05-08 | CoRL 2025 | 是 | — |
| [D-Cubed: Latent Diffusion Trajectory Optimisation for Dexterous Deformable Manipulation](https://proceedings.mlr.press/v305/yamada25b.html) | 2025-10-07 | CoRL 2025 | 是 | — |
| [Demonstrating REASSEMBLE: A Multimodal Dataset for Contact-rich Robotic Assembly and Disassembly](https://www.roboticsproceedings.org/rss21/p059.html) | 2025-06-21 | RSS 2025 | 是 | — |
| [Dex1B: Learning with 1B Demonstrations for Dexterous Manipulation](https://arxiv.org/abs/2506.17198) | 2025-06-20 | RSS 2025 | 是 | — |
| [DexCap: Scalable and Portable Mocap Data Collection System for Dexterous Manipulation](https://doi.org/10.15607/rss.2024.xx.043) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [DexCatch: Learning to Catch Arbitrary Objects with Dexterous Hands](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [DexGraspNet 2.0: Learning Generative Dexterous Grasping in Large-scale Synthetic Cluttered Scenes](https://arxiv.org/abs/2410.23004) | 2024-10-30 | CoRL 2024、CoRL 2024 | 是 | — |
| [Dexonomy: Synthesizing All Dexterous Grasp Types in a Grasp Taxonomy](https://arxiv.org/abs/2504.18829) | 2025-04-26 | RSS 2025 | 是 | — |
| [Dexplore: Scalable Neural Control for Dexterous Manipulation from Reference-Scoped Exploration](https://arxiv.org/abs/2509.09671) | 2025-09-11 | CoRL 2025 | 是 | — |
| [DexSkin: High-Coverage Conformable Robotic Skin for Learning Contact-Rich Manipulation](https://arxiv.org/abs/2509.18830) | 2025-09-23 | CoRL 2025 | 是 | — |
| [DexterityGen: Foundation Controller for Unprecedented Dexterity](https://arxiv.org/abs/2502.04307) | 2025-02-06 | RSS 2025 | 是 | — |
| [DextrAH-G: Pixels-to-Action Dexterous Arm-Hand Grasping with Geometric Fabrics](https://arxiv.org/abs/2407.02274) | 2024-07-02 | CoRL 2024、CoRL 2024 | 是 | — |
| [DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://arxiv.org/abs/2505.21864) | 2025-05-28 | CoRL 2025 | 是 | — |
| [DexWild: Dexterous Human Interactions for In-the-Wild Robot Policies](https://arxiv.org/abs/2505.07813) | 2025-05-12 | RSS 2025 | 是 | — |
| [Diffusion Meets DAgger: Supercharging Eye-in-hand Imitation Learning](https://doi.org/10.15607/rss.2024.xx.048) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [DOGlove: Dexterous Manipulation with a Low-Cost Open-Source Haptic Force Feedback Glove](https://arxiv.org/abs/2502.07730) | 2025-02-11 | RSS 2025 | 是 | — |
| [emg2tendon: From sEMG Signals to Tendon Control in Musculoskeletal Hands](https://arxiv.org/abs/2508.08269) | 2025-07-29 | RSS 2025 | 是 | — |
| [Fabrica: Dual-Arm Assembly of General Multi-Part Objects via Integrated Planning and Learning](https://arxiv.org/abs/2506.05168) | 2025-06-05 | CoRL 2025 | 是 | — |
| [FACTR: Force-Attending Curriculum Training for Contact-Rich Policy Learning](https://arxiv.org/abs/2502.17432) | 2025-02-24 | RSS 2025 | 是 | — |
| [FFHFlow: Diverse and Uncertainty-Aware Dexterous Grasp Generation via Flow Variational Inference](https://arxiv.org/abs/2407.15161) | 2024-07-21 | CoRL 2025 | 是 | — |
| [GeoDEx: A Unified Geometric Framework for Tactile Dexterous and Extrinsic Manipulation under Force Uncertainty](https://arxiv.org/abs/2505.00647) | 2025-05-01 | RSS 2025 | 是 | — |
| [Get a Grip: Multi-Finger Grasp Evaluation at Scale Enables Robust Sim-to-Real Transfer](https://arxiv.org/abs/2410.23701) | 2024-10-31 | CoRL 2024、CoRL 2024 | 是 | — |
| [Global Contact-Rich Planning with Sparsity-Rich Semidefinite Relaxations](https://arxiv.org/abs/2502.02829) | 2025-02-05 | RSS 2025 | 是 | — |
| [GraspQP: Differentiable Optimization of Force Closure for Diverse and Robust Dexterous Grasping](https://arxiv.org/abs/2508.15002) | 2025-08-20 | CoRL 2025 | 是 | — |
| [Gripper Pose and Object Pointflow as Interfaces for Robotic Bimanual Manipulation](https://www.roboticsproceedings.org/rss21/p160.html) | 2025-06-21 | RSS 2025 | 是 | — |
| [Hierarchical and Modular Network on Non-prehensile Manipulation in General Environments](https://arxiv.org/abs/2502.20843) | 2025-02-28 | RSS 2025 | 是 | — |
| [InterACT: Inter-dependency Aware Action Chunking with Hierarchical Attention Transformers for Bimanual Manipulation](https://arxiv.org/abs/2409.07914) | 2024-09-12 | CoRL 2024、CoRL 2024 | 是 | — |
| [Jacta: A Versatile Planner for Learning Dexterous and Whole-body Manipulation](https://arxiv.org/abs/2408.01258) | 2024-08-02 | CoRL 2024、CoRL 2024 | 是 | — |
| [KineDex: Learning Tactile-Informed Visuomotor Policies via Kinesthetic Teaching for Dexterous Manipulation](https://arxiv.org/abs/2505.01974) | 2025-05-04 | CoRL 2025 | 是 | — |
| [KineSoft: Learning Proprioceptive Manipulation Policies with Soft Robot Hands](https://arxiv.org/abs/2503.01078) | 2025-03-03 | CoRL 2025 | 是 | — |
| [Learning Long-Horizon Robot Manipulation Skills via Privileged Action](https://arxiv.org/abs/2502.15442) | 2025-02-21 | CoRL 2025 | 是 | — |
| [Learning Visuotactile Estimation and Control for Non-prehensile Manipulation under Occlusions](https://arxiv.org/abs/2412.13157) | 2024-12-17 | CoRL 2024、CoRL 2024 | 是 | — |
| [MimicTouch: Leveraging Multi-modal Human Tactile Demonstrations for Contact-rich Manipulation](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Mobile ALOHA: Learning Bimanual Mobile Manipulation using Low-Cost Whole-Body Teleoperation](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Morphologically Symmetric Reinforcement Learning for Ambidextrous Bimanual Manipulation](https://arxiv.org/abs/2505.05287) | 2025-05-08 | CoRL 2025 | 是 | — |
| [Neural Attention Field: Emerging Point Relevance in 3D Scenes for One-Shot Dexterous Grasping](https://arxiv.org/abs/2410.23039) | 2024-10-30 | CoRL 2024、CoRL 2024 | 是 | — |
| [Object-Centric Dexterous Manipulation from Human Motion Data](https://arxiv.org/abs/2411.04005) | 2024-11-06 | CoRL 2024、CoRL 2024 | 是 | — |
| [OmniH2O: Universal and Dexterous Human-to-Humanoid Whole-Body Teleoperation and Learning](https://arxiv.org/abs/2406.08858) | 2024-06-13 | CoRL 2024、CoRL 2024 | 是 | — |
| [Physics-Driven Data Generation for Contact-Rich Manipulation via Trajectory Optimization](https://arxiv.org/abs/2502.20382) | 2025-02-27 | RSS 2025 | 是 | — |
| [PianoMime: Learning a Generalist, Dexterous Piano Player from Internet Demonstrations](https://arxiv.org/abs/2407.18178) | 2024-07-25 | CoRL 2024、CoRL 2024 | 是 | — |
| [PP-Tac: Paper Picking Using Omnidirectional Tactile Feedback in Dexterous Robotic Hands](https://www.roboticsproceedings.org/rss21/p056.html) | 2025-06-21 | RSS 2025 | 是 | — |
| [ReKep: Spatio-Temporal Reasoning of Relational Keypoint Constraints for Robotic Manipulation](https://arxiv.org/abs/2409.01652) | 2024-09-03 | CoRL 2024、CoRL 2024 | 是 | — |
| [ResPilot: Teleoperated Finger Gaiting via Gaussian Process Residual Learning](https://arxiv.org/abs/2409.09140) | 2024-09-13 | CoRL 2024、CoRL 2024 | 是 | — |
| [Robust Dexterous Grasping of General Objects](https://proceedings.mlr.press/v305/zhang25h.html) | 2025-10-07 | CoRL 2025 | 是 | — |

---


## D5 · 人形、运动与全身控制

> 归属层级：物理能力。当前纳入 2031 个 canonical works；数量、环比和代表工作均按本站当前分类规则生成。

### 纳入边界

核心表达：`humanoid`、`whole-body control`、`whole body control`、`whole-body manipulation`、`whole body manipulation`、`legged robot`、`quadruped`、`biped`、`locomotion`、`loco-manipulation`、`loco manipulation`、`parkour`、`motor skill`、`motion imitation`、`human motion retargeting`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`humanoid`、`legged`、`quadruped`、`biped`、`control`。

### 月度结构与环比

| 月份 | 本月 | 对比月 | 上月 | 环比增量 | 环比 |
|---|---:|---|---:|---:|---:|
| 2024-07 | 42 | — | 0 | +42 | 新增 |
| 2024-08 | 25 | 2024-07 | 42 | -17 | -40.5% |
| 2024-09 | 73 | 2024-08 | 25 | +48 | +192.0% |
| 2024-10 | 49 | 2024-09 | 73 | -24 | -32.9% |
| 2024-11 | 41 | 2024-10 | 49 | -8 | -16.3% |
| 2024-12 | 37 | 2024-11 | 41 | -4 | -9.8% |
| 2025-01 | 16 | 2024-12 | 37 | -21 | -56.8% |
| 2025-02 | 47 | 2025-01 | 16 | +31 | +193.8% |
| 2025-03 | 73 | 2025-02 | 47 | +26 | +55.3% |
| 2025-04 | 44 | 2025-03 | 73 | -29 | -39.7% |
| 2025-05 | 80 | 2025-04 | 44 | +36 | +81.8% |
| 2025-06 | 55 | 2025-05 | 80 | -25 | -31.3% |
| 2025-07 | 44 | 2025-06 | 55 | -11 | -20.0% |
| 2025-08 | 66 | 2025-07 | 44 | +22 | +50.0% |
| 2025-09 | 70 | 2025-08 | 66 | +4 | +6.1% |
| 2025-10 | 81 | 2025-09 | 70 | +11 | +15.7% |
| 2025-11 | 58 | 2025-10 | 81 | -23 | -28.4% |
| 2025-12 | 38 | 2025-11 | 58 | -20 | -34.5% |
| 2026-01 | 37 | 2025-12 | 38 | -1 | -2.6% |
| 2026-02 | 87 | 2026-01 | 37 | +50 | +135.1% |
| 2026-03 | 121 | 2026-02 | 87 | +34 | +39.1% |
| 2026-04 | 67 | 2026-03 | 121 | -54 | -44.6% |
| 2026-05 | 66 | 2026-04 | 67 | -1 | -1.5% |
| 2026-06 | 121 | 2026-05 | 66 | +55 | +83.3% |
| 2026-07 | 70 | 2026-06 | 121 | -51 | -42.1% |

### 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [Advancing Humanoid Locomotion: Mastering Challenging Terrains with Denoising World Model Learning](https://arxiv.org/abs/2408.14472) | 2024-08-26 | RSS 2024、RSS 2024 | 是 | — |
| [Design and Control of a Bipedal Robotic Character](https://arxiv.org/abs/2501.05204) | 2025-01-09 | RSS 2024、RSS 2024 | 是 | — |
| [RL2AC: Reinforcement Learning-based Rapid Online Adaptive Control for Legged Robot Robust Locomotion](https://doi.org/10.15607/rss.2024.xx.060) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Linear-time Differential Inverse Kinematics: an Augmented Lagrangian Perspective](https://doi.org/10.15607/rss.2024.xx.110) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [A Unified and General Humanoid Whole-Body Controller for Fine-Grained Locomotion](https://www.roboticsproceedings.org/rss21/p067.html) | 2025-06-21 | RSS 2025 | 是 | — |
| [Action Space Design in Reinforcement Learning for Robot Motor Skills](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Adapting Humanoid Locomotion over Challenging Terrain via Two-Phase Training](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Adaptive Locomotion on Mud through Proprioceptive Sensing of Substrate Properties](https://arxiv.org/abs/2504.19607) | 2025-04-28 | RSS 2025 | 是 | — |
| [AgentWorld: An Interactive Simulation Platform for Scene Construction and Mobile Robotic Manipulation](https://arxiv.org/abs/2508.07770) | 2025-08-11 | CoRL 2025 | 是 | — |
| [Agile But Safe: Learning Collision-Free High-Speed Legged Locomotion](https://doi.org/10.15607/rss.2024.xx.059) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [AMO: Adaptive Motion Optimization for Hyper-Dexterous Humanoid Whole-Body Control](https://arxiv.org/abs/2505.03738) | 2025-05-06 | RSS 2025 | 是 | — |
| [ASAP: Aligning Simulation and Real-World Physics for Learning Agile Humanoid Whole-Body Skills](https://arxiv.org/abs/2502.01143) | 2025-02-03 | RSS 2025 | 是 | — |
| [BeamDojo: Learning Agile Humanoid Locomotion on Sparse Footholds](https://arxiv.org/abs/2502.10363) | 2025-02-14 | RSS 2025 | 是 | — |
| [BEHAVIOR Robot Suite: Streamlining Real-World Whole-Body Manipulation for Everyday Household Activities](https://arxiv.org/abs/2503.05652) | 2025-03-07 | CoRL 2025 | 是 | — |
| [Bi-Level Motion Imitation for Humanoid Robots](https://arxiv.org/abs/2410.01968) | 2024-10-02 | CoRL 2024、CoRL 2024 | 是 | — |
| [Bipedal Balance Control with Whole-body Musculoskeletal Standing and Falling Simulations](https://arxiv.org/abs/2506.09383) | 2025-06-11 | CoRL 2025 | 是 | — |
| [CLONE: Closed-Loop Whole-Body Humanoid Teleoperation for Long-Horizon Tasks](https://arxiv.org/abs/2506.08931) | 2025-06-10 | CoRL 2025 | 是 | — |
| [Contrastive Forward Prediction Reinforcement Learning for Adaptive Fault-Tolerant Legged Robots](https://proceedings.mlr.press/v305/fu25b.html) | 2025-10-07 | CoRL 2025 | 是 | — |
| [Demonstrating Berkeley Humanoid Lite: An Open-source, Accessible, and Customizable 3D-printed Humanoid Robot](https://arxiv.org/abs/2504.17249) | 2025-04-24 | RSS 2025 | 是 | — |
| [DiffuseLoco: Real-Time Legged Locomotion Control with Diffusion from Offline Datasets](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Discrete-Time Hybrid Automata Learning: Legged Locomotion Meets Skateboarding](https://arxiv.org/abs/2503.01842) | 2025-03-03 | RSS 2025 | 是 | — |
| [Disentangled Multi-Context Meta-Learning: Unlocking robust and Generalized Task Learning](https://arxiv.org/abs/2509.01297) | 2025-09-01 | CoRL 2025 | 是 | — |
| [Dynamic Safety in Complex Environments: Synthesizing Safety Filters with Poisson's Equation](https://arxiv.org/abs/2505.06794) | 2025-05-11 | RSS 2025 | 是 | — |
| [Embrace Contacts: humanoid shadowing with full body ground contacts](https://proceedings.mlr.press/v305/zhuang25b.html) | 2025-10-07 | CoRL 2025 | 是 | — |
| [Expressive Whole-Body Control for Humanoid Robots](https://doi.org/10.15607/rss.2024.xx.107) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [FACET: Force-Adaptive Control via Impedance Reference Tracking for Legged Robots](https://arxiv.org/abs/2505.06883) | 2025-05-11 | CoRL 2025 | 是 | — |
| [First Order Model-Based RL through Decoupled Backpropagation](https://arxiv.org/abs/2509.00215) | 2025-08-29 | CoRL 2025 | 是 | — |
| [From Tabula Rasa to Emergent Abilities: Discovering Robot Skills via Real-World Unsupervised Quality-Diversity](https://arxiv.org/abs/2508.19172) | 2025-08-26 | CoRL 2025 | 是 | — |
| [Gain Tuning Is Not What You Need: Reward Gain Adaptation for Constrained Locomotion Learning](https://arxiv.org/abs/2510.10759) | 2025-10-12 | RSS 2025 | 是 | — |
| [Gait-Net-augmented Implicit Kino-dynamic MPC for Dynamic Variable-frequency Humanoid Locomotion over Discrete Terrains](https://arxiv.org/abs/2502.02934) | 2025-02-05 | RSS 2025 | 是 | — |
| [Gaitor: Learning a Unified Representation Across Gaits for Real-World Quadruped Locomotion](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Generalized Animal Imitator: Agile Locomotion with Versatile Motion Prior](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Granular Loco-Manipulation: Repositioning Rocks Through Strategic Sand Avalanche](https://arxiv.org/abs/2505.12934) | 2025-05-19 | CoRL 2025 | 是 | — |
| [Guided Reinforcement Learning for Robust Multi-Contact Loco-Manipulation](https://arxiv.org/abs/2410.13817) | 2024-10-17 | CoRL 2024、CoRL 2024 | 是 | — |
| [Hand-Eye Autonomous Delivery: Learning Humanoid Navigation, Locomotion and Reaching](https://arxiv.org/abs/2508.03068) | 2025-08-05 | CoRL 2025 | 是 | — |
| [Harmon: Whole-Body Motion Generation of Humanoid Robots from Language Descriptions](https://arxiv.org/abs/2410.12773) | 2024-10-16 | CoRL 2024、CoRL 2024 | 是 | — |
| [Hold My Beer: Learning Gentle Humanoid Locomotion and End-Effector Stabilization Control](https://arxiv.org/abs/2505.24198) | 2025-05-30 | CoRL 2025 | 是 | — |
| [HOMIE: Humanoid Loco-Manipulation with Isomorphic Exoskeleton Cockpit](https://arxiv.org/abs/2502.13013) | 2025-02-18 | RSS 2025 | 是 | — |
| [HuB: Learning Extreme Humanoid Balance](https://arxiv.org/abs/2505.07294) | 2025-05-12 | CoRL 2025 | 是 | — |
| [Human2LocoMan: Learning Versatile Quadrupedal Manipulation with Human Pretraining](https://arxiv.org/abs/2506.16475) | 2025-06-19 | RSS 2025 | 是 | — |
| [Humanoid Parkour Learning](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Humanoid Policy ~ Human Policy](https://arxiv.org/abs/2503.13441) | 2025-03-17 | CoRL 2025 | 是 | — |
| [HumanoidBench: Simulated Humanoid Benchmark for Whole-Body Locomotion and Manipulation](https://doi.org/10.15607/rss.2024.xx.061) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [HumanPlus: Humanoid Shadowing and Imitation from Humans](https://arxiv.org/abs/2406.10454) | 2024-06-15 | CoRL 2024、CoRL 2024 | 是 | — |
| [HYPERmotion: Learning Hybrid Behavior Planning for Autonomous Loco-manipulation](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [In-Flight Attitude Control of a Quadruped using Deep Reinforcement Learning](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [LangWBC: Language-directed Humanoid Whole-Body Control via End-to-end Learning](https://arxiv.org/abs/2504.21738) | 2025-04-30 | RSS 2025 | 是 | — |
| [Learning a Distributed Hierarchical Locomotion Controller for Embodied Cooperation](https://arxiv.org/abs/2407.06499) | 2024-07-09 | CoRL 2024、CoRL 2024 | 是 | — |
| [Learning a Unified Policy for Position and Force Control in Legged Loco-Manipulation](https://arxiv.org/abs/2505.20829) | 2025-05-27 | CoRL 2025 | 是 | — |
| [Learning Decentralized Multi-Biped Control for Payload Transport](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Learning Deployable Locomotion Control via Differentiable Simulation](https://proceedings.mlr.press/v305/schwarke25a.html) | 2025-10-07 | CoRL 2025 | 是 | — |
| [Learning Getting-Up Policies for Real-World Humanoid Robots](https://arxiv.org/abs/2502.12152) | 2025-02-17 | RSS 2025 | 是 | — |
| [Learning Granular Media Avalanche Behavior for Indirectly Manipulating Obstacles on a Granular Slope](https://arxiv.org/abs/2407.01898) | 2024-07-02 | CoRL 2024、CoRL 2024 | 是 | — |
| [Learning H-Infinity Locomotion Control](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Learning Humanoid Standing-up Control across Diverse Postures](https://arxiv.org/abs/2502.08378) | 2025-02-12 | RSS 2025 | 是 | — |
| [Learning Quadruped Locomotion Using Differentiable Simulation](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Learning Robotic Locomotion Affordances and Photorealistic Simulators from Human-Captured Data](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Learning Visual Parkour from Generated Images](https://arxiv.org/abs/2411.00083) | 2024-10-31 | CoRL 2024、CoRL 2024 | 是 | — |
| [LocoFormer: Generalist Locomotion via Long-context Adaptation](https://arxiv.org/abs/2509.23745) | 2025-09-28 | CoRL 2025 | 是 | — |
| [LocoTouch: Learning Dynamic Quadrupedal Transport with Tactile Sensing](https://arxiv.org/abs/2505.23175) | 2025-05-29 | CoRL 2025 | 是 | — |

---


## D6 · 导航与移动操作

> 归属层级：物理能力。当前纳入 548 个 canonical works；数量、环比和代表工作均按本站当前分类规则生成。

### 纳入边界

核心表达：`mobile manipulation`、`mobile manipulator`、`visual navigation`、`vision-language navigation`、`vision language navigation`、`object navigation`、`semantic navigation`、`social navigation`、`active exploration`、`navigation policy`、`nav-manipulation`、`nav manipulation`、`embodied navigation`、`goal-conditioned navigation`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`embodied`、`navigation`、`mobile`、`manipulation`。

### 月度结构与环比

| 月份 | 本月 | 对比月 | 上月 | 环比增量 | 环比 |
|---|---:|---|---:|---:|---:|
| 2024-07 | 10 | — | 0 | +10 | 新增 |
| 2024-08 | 4 | 2024-07 | 10 | -6 | -60.0% |
| 2024-09 | 19 | 2024-08 | 4 | +15 | +375.0% |
| 2024-10 | 19 | 2024-09 | 19 | 0 | 0.0% |
| 2024-11 | 6 | 2024-10 | 19 | -13 | -68.4% |
| 2024-12 | 13 | 2024-11 | 6 | +7 | +116.7% |
| 2025-01 | 4 | 2024-12 | 13 | -9 | -69.2% |
| 2025-02 | 12 | 2025-01 | 4 | +8 | +200.0% |
| 2025-03 | 14 | 2025-02 | 12 | +2 | +16.7% |
| 2025-04 | 6 | 2025-03 | 14 | -8 | -57.1% |
| 2025-05 | 13 | 2025-04 | 6 | +7 | +116.7% |
| 2025-06 | 17 | 2025-05 | 13 | +4 | +30.8% |
| 2025-07 | 13 | 2025-06 | 17 | -4 | -23.5% |
| 2025-08 | 12 | 2025-07 | 13 | -1 | -7.7% |
| 2025-09 | 32 | 2025-08 | 12 | +20 | +166.7% |
| 2025-10 | 19 | 2025-09 | 32 | -13 | -40.6% |
| 2025-11 | 16 | 2025-10 | 19 | -3 | -15.8% |
| 2025-12 | 19 | 2025-11 | 16 | +3 | +18.8% |
| 2026-01 | 16 | 2025-12 | 19 | -3 | -15.8% |
| 2026-02 | 22 | 2026-01 | 16 | +6 | +37.5% |
| 2026-03 | 49 | 2026-02 | 22 | +27 | +122.7% |
| 2026-04 | 26 | 2026-03 | 49 | -23 | -46.9% |
| 2026-05 | 19 | 2026-04 | 26 | -7 | -26.9% |
| 2026-06 | 29 | 2026-05 | 19 | +10 | +52.6% |
| 2026-07 | 26 | 2026-06 | 29 | -3 | -10.3% |

### 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [Demonstrating Adaptive Mobile Manipulation in Retail Environments](https://doi.org/10.15607/rss.2024.xx.047) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Demonstrating Arena 3.0: Advancing Social Navigation in Collaborative and Highly Dynamic Environments](https://doi.org/10.15607/rss.2024.xx.074) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Bilevel Learning for Bilevel Planning](https://arxiv.org/abs/2502.08697) | 2025-02-12 | RSS 2025 | 是 | — |
| [CARE: Enhancing Safety of Visual Navigation through Collision Avoidance via Repulsive Estimation](https://arxiv.org/abs/2506.03834) | 2025-06-04 | CoRL 2025 | 是 | — |
| [Context-Aware Replanning with Pre-explored Semantic Map for Object Navigation](https://arxiv.org/abs/2409.04837) | 2024-09-07 | CoRL 2024、CoRL 2024 | 是 | — |
| [Continuously Improving Mobile Manipulation with Autonomous Real-World RL](https://arxiv.org/abs/2409.20568) | 2024-09-30 | CoRL 2024、CoRL 2024 | 是 | — |
| [Demonstrating Arena 5.0: A Photorealistic ROS2 Simulation Framework for Developing and Benchmarking Social Navigation](https://www.roboticsproceedings.org/rss21/p092.html) | 2025-06-21 | RSS 2025 | 是 | — |
| [LeLaN: Learning A Language-Conditioned Navigation Policy from In-the-Wild Video](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [MoTo: A Zero-shot Plug-in Interaction-aware Navigation for General Mobile Manipulation](https://arxiv.org/abs/2509.01658) | 2025-09-01 | CoRL 2025 | 是 | — |
| [ObjectReact: Learning Object-Relative Control for Visual Navigation](https://arxiv.org/abs/2509.09594) | 2025-09-11 | CoRL 2025 | 是 | — |
| [RoboEXP: Action-Conditioned Scene Graph via Interactive Exploration for Robotic Manipulation](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [SafeMimic: Towards Safe and Autonomous Human-to-Robot Imitation for Mobile Manipulation](https://arxiv.org/abs/2506.15847) | 2025-06-18 | RSS 2025 | 是 | — |
| [TaMMa: Target-driven Multi-subscene Mobile Manipulation](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [TidyBot++: An Open-Source Holonomic Mobile Manipulator for Robot Learning](https://arxiv.org/abs/2412.10447) | 2024-12-11 | CoRL 2024、CoRL 2024 | 是 | — |
| [VLFM: Vision-Language Frontier Maps for Zero-Shot Semantic Navigation](https://arxiv.org/abs/2312.03275) | — | ICRA 2024 | 否 | — |
| [Bridging Zero-shot Object Navigation and Foundation Models through Pixel-Guided Navigation Skill](https://arxiv.org/abs/2309.10309) | — | ICRA 2024 | 否 | — |
| [Language-Grounded Dynamic Scene Graphs for Interactive Object Search With Mobile Manipulation](https://arxiv.org/abs/2403.08605) | — | RA-L 2024 | 否 | — |
| [HM3D-OVON: A Dataset and Benchmark for Open-Vocabulary Object Goal Navigation](https://arxiv.org/abs/2409.14296) | 2024-09-22 | IROS 2024 | 否 | — |
| [Closed-Loop Open-Vocabulary Mobile Manipulation with GPT-4V](https://arxiv.org/abs/2404.10220) | — | ICRA 2025 | 否 | — |
| [RoboHop: Segment-based Topological Map Representation for Open-World Visual Navigation](https://arxiv.org/abs/2405.05792) | — | ICRA 2024 | 否 | — |
| [DynaMem: Online Dynamic Spatio-Semantic Memory for Open World Mobile Manipulation](https://arxiv.org/abs/2411.04999) | 2024-11-07 | ICRA 2025 | 否 | — |
| [Dynamic Open-Vocabulary 3D Scene Graphs for Long-term Language-Guided Mobile Manipulation](https://arxiv.org/abs/2410.11989) | 2024-10-15 | RA-L 2025 | 否 | — |
| [TriHelper: Zero-Shot Object Navigation with Dynamic Assistance](https://arxiv.org/abs/2403.15223) | — | IROS 2024 | 否 | — |
| [Learning Generalizable Feature Fields for Mobile Manipulation](https://arxiv.org/abs/2403.07563) | — | IROS 2025 | 否 | — |
| [ApexNav: An Adaptive Exploration Strategy for Zero-Shot Object Navigation with Target-centric Semantic Fusion](https://arxiv.org/abs/2504.14478) | 2025-04-20 | RA-L 2025、ICRA 2026 | 否 | — |
| [BUMBLE: Unifying Reasoning and Acting with Vision-Language Models for Building-wide Mobile Manipulation](https://arxiv.org/abs/2410.06237) | 2024-10-08 | ICRA 2025 | 否 | — |
| [NaviDiffusor: Cost-Guided Diffusion Model for Visual Navigation](https://arxiv.org/abs/2504.10003) | 2025-04-14 | ICRA 2025 | 否 | — |
| [EMMA: Scaling Mobile Manipulation via Egocentric Human Data](https://arxiv.org/abs/2509.04443) | 2025-09-04 | RA-L 2026、ICRA 2026 | 否 | — |
| [Harmonic Mobile Manipulation](https://arxiv.org/abs/2312.06639) | — | IROS 2024 | 否 | — |
| [DR-MPC: Deep Residual Model Predictive Control for Real-world Social Navigation](https://arxiv.org/abs/2410.10646) | 2024-10-14 | RA-L 2025 | 否 | — |
| [Multi-Floor Zero-Shot Object Navigation Policy](https://arxiv.org/abs/2409.10906) | 2024-09-17 | ICRA 2025 | 否 | — |
| [OLiVia-Nav: An Online Lifelong Vision Language Approach for Mobile Robot Social Navigation](https://arxiv.org/abs/2409.13675) | 2024-09-20 | ICRA 2025 | 否 | — |
| [Dynamic object goal pushing with mobile manipulators through model-free constrained reinforcement learning](https://arxiv.org/abs/2502.01546) | 2025-02-03 | ICRA 2025 | 否 | — |
| [From Cognition to Precognition: A Future-Aware Framework for Social Navigation](https://arxiv.org/abs/2409.13244) | 2024-09-20 | ICRA 2025 | 否 | — |
| [One Map to Find Them All: Real-time Open-Vocabulary Mapping for Zero-shot Multi-Object Navigation](https://arxiv.org/abs/2409.11764) | 2024-09-18 | ICRA 2025 | 否 | — |
| [TDANet: Target-Directed Attention Network for Object-Goal Visual Navigation With Zero-Shot Ability](https://arxiv.org/abs/2404.08353) | — | RA-L 2024 | 否 | — |
| [HabiCrowd: A High Performance Simulator for Crowd-Aware Visual Navigation](https://arxiv.org/abs/2306.11377) | — | IROS 2024 | 否 | — |
| [Learning to Drive Anywhere with Model-Based Reannotation](https://arxiv.org/abs/2505.05592) | 2025-05-08 | RA-L 2026、ICRA 2026 | 否 | — |
| [Malicious Path Manipulations via Exploitation of Representation Vulnerabilities of Vision-Language Navigation Systems](https://arxiv.org/abs/2407.07392) | 2024-07-10 | IROS 2024 | 否 | — |
| [VLN-Game: Vision-Language Equilibrium Search for Zero-Shot Semantic Navigation](https://arxiv.org/abs/2411.11609) | 2024-11-18 | T-RO 2026 | 否 | — |
| [Active-Perceptive Motion Generation for Mobile Manipulation](https://arxiv.org/abs/2310.00433) | — | ICRA 2024 | 否 | — |
| [Revolutionizing Battery Disassembly: The Design and Implementation of a Battery Disassembly Autonomous Mobile Manipulator Robot(BEAM-1)](https://arxiv.org/abs/2407.06590) | 2024-07-09 | IROS 2024 | 否 | — |
| [Exploitation-Guided Exploration for Semantic Embodied Navigation](https://arxiv.org/abs/2311.03357) | — | ICRA 2024 | 否 | — |
| [Social Navigation in Crowded Environments with Model Predictive Control and Deep Learning-Based Human Trajectory Prediction](https://arxiv.org/abs/2309.16838) | — | IROS 2024 | 否 | — |
| [ForceSight: Text-Guided Mobile Manipulation with Visual-Force Goals](https://arxiv.org/abs/2309.12312) | — | ICRA 2024 | 否 | — |
| [ORLA*: Mobile Manipulator-Based Object Rearrangement with Lazy A](https://arxiv.org/abs/2309.13707) | — | ICRA 2025 | 否 | — |
| [Sim2Real Transfer for Audio-Visual Navigation with Frequency-Adaptive Acoustic Field Prediction](https://arxiv.org/abs/2405.02821) | — | IROS 2024 | 否 | — |
| [Whole-Body Teleoperation for Mobile Manipulation at Zero Added Cost](https://arxiv.org/abs/2409.15095) | 2024-09-23 | RA-L 2025 | 否 | — |
| [MAkEable: Memory-centered and Affordance-based Task Execution Framework for Transferable Mobile Manipulation Skills](https://arxiv.org/abs/2401.16899) | — | IROS 2024 | 否 | — |
| [BaSeNet: A Learning-based Mobile Manipulator Base Pose Sequence Planning for Pickup Tasks](https://arxiv.org/abs/2406.08653) | — | IROS 2024 | 否 | — |
| [MORE: Mobile Manipulation Rearrangement Through Grounded Language Reasoning](https://arxiv.org/abs/2505.03035) | 2025-05-05 | IROS 2025 | 否 | — |
| [OpenBench: A New Benchmark and Baseline for Semantic Navigation in Smart Logistics](https://arxiv.org/abs/2502.09238) | 2025-02-13 | ICRA 2025 | 否 | — |
| [Planning Optimal Trajectories for Mobile Manipulators under End-effector Trajectory Continuity Constraint](https://arxiv.org/abs/2309.12251) | — | ICRA 2024 | 否 | — |
| [HSPNav: Hierarchical Scene Prior Learning for Visual Semantic Navigation Towards Real Settings](https://ieeexplore.ieee.org/document/10610061) | 2024-05-13 | ICRA 2024 | 否 | — |
| [osmAG-LLM: Zero-Shot Open-Vocabulary Object Navigation via Semantic Maps and Large Language Models Reasoning](https://arxiv.org/abs/2507.12753) | 2025-07-17 | RA-L 2026、ICRA 2026 | 否 | — |
| [A CBF-Adaptive Control Architecture for Visual Navigation for UAV in the Presence of Uncertainties](https://arxiv.org/abs/2402.10729) | — | ICRA 2024 | 否 | — |
| [A Map-free Deep Learning-based Framework for Gate-to-Gate Monocular Visual Navigation aboard Miniaturized Aerial Vehicles](https://arxiv.org/abs/2503.05251) | 2025-03-07 | ICRA 2025 | 否 | — |
| [Coupled Active Perception and Manipulation Planning for a Mobile Manipulator in Precision Agriculture Applications](https://arxiv.org/abs/2309.16778) | — | ICRA 2024 | 否 | — |
| [DOZE: A Dataset for Open-Vocabulary Zero-Shot Object Navigation in Dynamic Environments](https://arxiv.org/abs/2402.19007) | — | RA-L 2024 | 否 | — |
| [Learning Implicit Social Navigation Behavior using Deep Inverse Reinforcement Learning](https://arxiv.org/abs/2501.06946) | 2025-01-12 | RA-L 2025 | 否 | — |

---


## D7 · 人机协作与交互学习

> 归属层级：物理能力。当前纳入 801 个 canonical works；数量、环比和代表工作均按本站当前分类规则生成。

### 纳入边界

核心表达：`human-robot interaction`、`human robot interaction`、`human-robot collaboration`、`human robot collaboration`、`shared autonomy`、`interactive learning`、`learning from human feedback`、`preference learning`、`assistive robot`、`collaborative robot`、`social robot`、`language-guided correction`、`online correction`、`human-in-the-loop`、`human in the loop`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`embodied`、`interaction`、`collaboration`、`assistive`。

### 月度结构与环比

| 月份 | 本月 | 对比月 | 上月 | 环比增量 | 环比 |
|---|---:|---|---:|---:|---:|
| 2024-07 | 17 | — | 0 | +17 | 新增 |
| 2024-08 | 13 | 2024-07 | 17 | -4 | -23.5% |
| 2024-09 | 26 | 2024-08 | 13 | +13 | +100.0% |
| 2024-10 | 20 | 2024-09 | 26 | -6 | -23.1% |
| 2024-11 | 15 | 2024-10 | 20 | -5 | -25.0% |
| 2024-12 | 21 | 2024-11 | 15 | +6 | +40.0% |
| 2025-01 | 20 | 2024-12 | 21 | -1 | -4.8% |
| 2025-02 | 24 | 2025-01 | 20 | +4 | +20.0% |
| 2025-03 | 30 | 2025-02 | 24 | +6 | +25.0% |
| 2025-04 | 17 | 2025-03 | 30 | -13 | -43.3% |
| 2025-05 | 24 | 2025-04 | 17 | +7 | +41.2% |
| 2025-06 | 23 | 2025-05 | 24 | -1 | -4.2% |
| 2025-07 | 30 | 2025-06 | 23 | +7 | +30.4% |
| 2025-08 | 21 | 2025-07 | 30 | -9 | -30.0% |
| 2025-09 | 32 | 2025-08 | 21 | +11 | +52.4% |
| 2025-10 | 19 | 2025-09 | 32 | -13 | -40.6% |
| 2025-11 | 19 | 2025-10 | 19 | 0 | 0.0% |
| 2025-12 | 20 | 2025-11 | 19 | +1 | +5.3% |
| 2026-01 | 25 | 2025-12 | 20 | +5 | +25.0% |
| 2026-02 | 25 | 2026-01 | 25 | 0 | 0.0% |
| 2026-03 | 29 | 2026-02 | 25 | +4 | +16.0% |
| 2026-04 | 25 | 2026-03 | 29 | -4 | -13.8% |
| 2026-05 | 24 | 2026-04 | 25 | -1 | -4.0% |
| 2026-06 | 29 | 2026-05 | 24 | +5 | +20.8% |
| 2026-07 | 37 | 2026-06 | 29 | +8 | +27.6% |

### 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [CoRI: Communication of Robot Intent for Physical Human-Robot Interaction](https://arxiv.org/abs/2505.20537) | 2025-05-26 | CoRL 2025 | 是 | — |
| [Demonstrating a Control Framework for Physical Human-Robot Interaction Toward Industrial Applications](https://arxiv.org/abs/2502.02967) | 2025-02-05 | RSS 2025 | 是 | — |
| [Demonstrating HumanTHOR: A Simulation Platform and Benchmark for Human-Robot Collaboration in a Shared Workspace](https://doi.org/10.15607/rss.2024.xx.029) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [FlashBack: Consistency Model-Accelerated Shared Autonomy](https://arxiv.org/abs/2505.16892) | 2025-05-22 | CoRL 2025 | 是 | — |
| [Optimal Interactive Learning on the Job via Facility Location Planning](https://arxiv.org/abs/2505.00490) | 2025-05-01 | RSS 2025 | 是 | — |
| [PrioriTouch: Adapting to User Contact Preferences for Whole-Arm Physical Human-Robot Interaction](https://arxiv.org/abs/2509.18447) | 2025-09-22 | CoRL 2025 | 是 | — |
| [Risk-Calibrated Human-Robot Interaction via Set-Valued Intent Prediction](https://doi.org/10.15607/rss.2024.xx.027) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Sense and Sensibility: What makes an social robot convincing to high-school students?](https://www.roboticsproceedings.org/rss21/p082.html) | 2025-06-21 | RSS 2025 | 是 | — |
| [SocialNav-SUB: Benchmarking VLMs for Scene Understanding in Social Robot Navigation](https://arxiv.org/abs/2509.08757) | 2025-09-10 | CoRL 2025 | 是 | — |
| [Task Adaptation in Industrial Human-Robot Interaction: Leveraging Riemannian Motion Policies](https://doi.org/10.15607/rss.2024.xx.026) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Text2Interaction: Establishing Safe and Preferable Human-Robot Interaction](https://arxiv.org/abs/2408.06105) | 2024-08-12 | CoRL 2024、CoRL 2024 | 是 | — |
| [Towards Uncertainty Unification: A Case Study for Preference Learning](https://arxiv.org/abs/2503.19317) | 2025-03-25 | RSS 2025 | 是 | — |
| [TRANSIC: Sim-to-Real Policy Transfer by Learning from Online Correction](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Users and Wizards in Conversations: How WoZ Interface Choices Define Human-Robot Interactions](https://arxiv.org/abs/2603.28338) | 2026-03-30 | RSS 2025 | 是 | — |
| [Vocal Sandbox: Continual Learning and Adaptation for Situated Human-Robot Collaboration](https://arxiv.org/abs/2411.02599) | 2024-11-04 | CoRL 2024、CoRL 2024 | 是 | — |
| [Robot learning on the job: Human-in-the-loop autonomy and learning during deployment](https://arxiv.org/abs/2211.08416) | — | IJRR 2024 | 否 | — |
| [Enhancing the LLM-Based Robot Manipulation Through Human-Robot Collaboration](https://arxiv.org/abs/2406.14097) | — | RA-L 2024 | 否 | — |
| [Intrinsic sense of touch for intuitive physical human-robot interaction](https://www.science.org/doi/10.1126/scirobotics.adn4008) | 2024-08-21 | Science Robotics 2024 | 否 | — |
| [Rethinking Social Robot Navigation: Leveraging the Best of Two Worlds](https://arxiv.org/abs/2309.13466) | — | ICRA 2024 | 否 | — |
| [Social robots as conversational catalysts: Enhancing long-term human-human interaction at home](https://www.science.org/doi/10.1126/scirobotics.adk3307) | 2025-03-12 | Science Robotics 2025 | 否 | — |
| [Promoting Trust in Industrial Human-Robot Collaboration Through Preference-Based Optimization](https://ieeexplore.ieee.org/document/3455792) | 2024-11-01 | RA-L 2024 | 否 | — |
| [Decision Making for Human-in-the-loop Robotic Agents via Uncertainty-Aware Reinforcement Learning](https://arxiv.org/abs/2303.06710) | — | ICRA 2024 | 否 | — |
| [Development of compositionality through interactive learning of language and action of robots](https://www.science.org/doi/10.1126/scirobotics.adp0751) | 2025-01-22 | Science Robotics 2025 | 否 | — |
| [Cellular-enabled Collaborative Robots Planning and Operations for Search-and-Rescue Scenarios](https://arxiv.org/abs/2403.09177) | — | ICRA 2024 | 否 | — |
| [Characterizing the Complexity of Social Robot Navigation Scenarios](https://arxiv.org/abs/2405.11410) | — | RA-L 2025 | 否 | — |
| [A survey of communicating robot learning during human-robot interaction](https://journals.sagepub.com/doi/10.1177/02783649241281369) | 2024-10-07 | IJRR 2024 | 否 | — |
| [PlanCollabNL: Leveraging Large Language Models for Adaptive Plan Generation in Human-Robot Collaboration](https://ieeexplore.ieee.org/document/10610055) | 2024-05-13 | ICRA 2024 | 否 | — |
| [GPT-Driven Gestures: Leveraging Large Language Models to Generate Expressive Robot Motion for Enhanced Human-Robot Interaction](https://ieeexplore.ieee.org/document/3547631) | 2025-05-01 | RA-L 2025 | 否 | — |
| [Human-Robot Gym: Benchmarking Reinforcement Learning in Human-Robot Collaboration](https://arxiv.org/abs/2310.06208) | — | ICRA 2024 | 否 | — |
| [SocialGAIL: Faithful Crowd Simulation for Social Robot Navigation](https://ieeexplore.ieee.org/document/10610371) | 2024-05-13 | ICRA 2024 | 否 | — |
| [CushSense: Soft, Stretchable, and Comfortable Tactile-Sensing Skin for Physical Human-Robot Interaction](https://arxiv.org/abs/2405.03155) | — | ICRA 2024 | 否 | — |
| [PRO-MIND: Proximity and Reactivity Optimisation of robot Motion to tune safety limits, human stress, and productivity in INDustrial settings](https://arxiv.org/abs/2409.06864) | 2024-09-10 | T-RO 2025 | 否 | — |
| [AutoSpatial: Visual-Language Reasoning for Social Robot Navigation through Efficient Spatial Reasoning Learning](https://arxiv.org/abs/2503.07557) | 2025-03-10 | IROS 2025 | 否 | — |
| [Jacquard V2: Refining Datasets using the Human In the Loop Data Correction Method](https://arxiv.org/abs/2402.05747) | — | ICRA 2024 | 否 | — |
| [MoVEInt: Mixture of Variational Experts for Learning Human-Robot Interactions from Demonstrations](https://arxiv.org/abs/2407.07636) | 2024-07-10 | RA-L 2024 | 否 | — |
| [Trust-Preserved Human-Robot Shared Autonomy Enabled by Bayesian Relational Event Modeling](https://arxiv.org/abs/2311.02009) | — | RA-L 2024 | 否 | — |
| [A Learning-Based Framework for Safe Human-Robot Collaboration with Multiple Backup Control Barrier Functions](https://arxiv.org/abs/2310.05865) | — | ICRA 2024 | 否 | — |
| [Interactive Distance Field Mapping and Planning to Enable Human-Robot Collaboration](https://arxiv.org/abs/2403.09988) | — | RA-L 2024 | 否 | — |
| [Planning Human-Robot Co-manipulation with Human Motor Control Objectives and Multi-component Reaching Strategies](https://arxiv.org/abs/2412.13474) | 2024-12-18 | RA-L 2025 | 否 | — |
| [Social-LLaVA: Enhancing Social Robot Navigation through Human-Language Reasoning](https://ieeexplore.ieee.org/document/11247618) | 2025-01-01 | IROS 2025 | 否 | — |
| [Dynamic Collaborative Workspace Based on Human Interference Estimation for Safe and Productive Human-Robot Collaboration](https://ieeexplore.ieee.org/document/3405352) | 2024-07-01 | RA-L 2024 | 否 | — |
| [Hierarchical Human Motion Intention Prediction for Increasing Efficacy of Human-Robot Collaboration](https://ieeexplore.ieee.org/document/3430131) | 2024-09-01 | RA-L 2024 | 否 | — |
| [Legible and Proactive Robot Planning for Prosocial Human-Robot Interactions](https://arxiv.org/abs/2404.03734) | — | ICRA 2024 | 否 | — |
| [To Ask or not to Ask: Human-in-the-loop Contextual Bandits with Applications in Robot-Assisted Feeding](https://arxiv.org/abs/2405.06908) | — | ICRA 2025 | 否 | — |
| [Towards Proactive Safe Human-Robot Collaborations via Data-Efficient Conditional Behavior Prediction](https://arxiv.org/abs/2311.11893) | — | ICRA 2024 | 否 | — |
| [EgoPAT3Dv2: Predicting 3D Action Target from 2D Egocentric Vision for Human-Robot Interaction](https://arxiv.org/abs/2403.05046) | — | ICRA 2024 | 否 | — |
| [AutoMisty: A Multi-Agent LLM Framework for Automated Code Generation in the Misty Social Robot](https://arxiv.org/abs/2503.06791) | 2025-03-09 | IROS 2025 | 否 | — |
| [Robot Interaction Behavior Generation based on Social Motion Forecasting for Human-Robot Interaction](https://arxiv.org/abs/2402.04768) | — | ICRA 2024 | 否 | — |
| [Shared Autonomy via Variable Impedance Control and Virtual Potential Fields for Encoding Human Demonstrations](https://arxiv.org/abs/2403.12720) | — | ICRA 2024 | 否 | — |
| [A probabilistic approach for learning and adapting shared control skills with the human in the loop](https://ieeexplore.ieee.org/document/10610956) | 2024-05-13 | ICRA 2024 | 否 | — |
| [Enhanced Human-Robot Collaboration with Intent Prediction using Deep Inverse Reinforcement Learning](https://ieeexplore.ieee.org/document/10610595) | 2024-05-13 | ICRA 2024 | 否 | — |
| [Interactive Learning of Physical Object Properties Through Robot Manipulation and Database of Object Measurements](https://arxiv.org/abs/2404.07344) | — | IROS 2024 | 否 | — |
| [Multi-Agent Strategy Explanations for Human-Robot Collaboration](https://arxiv.org/abs/2311.11955) | — | ICRA 2024 | 否 | — |
| [Multi-Camera Hand-Eye Calibration for Human-Robot Collaboration in Industrial Robotic Workcells](https://arxiv.org/abs/2406.11392) | — | RA-L 2024 | 否 | — |
| [UGotMe: An Embodied System for Affective Human-Robot Interaction](https://arxiv.org/abs/2410.18373) | 2024-10-24 | ICRA 2025 | 否 | — |
| [A Multi-Task Energy-Aware Impedance Controller for Enhanced Safety in Physical Human-Robot Interaction](https://ieeexplore.ieee.org/document/3519871) | 2025-02-01 | RA-L 2025 | 否 | — |
| [Dual-modal Tactile E-skin: Enabling Bidirectional Human-Robot Interaction via Integrated Tactile Perception and Feedback](https://arxiv.org/abs/2402.05725) | — | ICRA 2024 | 否 | — |
| [Haptic-Assisted Collaborative Robot Framework for Improved Situational Awareness in Skull Base Surgery](https://arxiv.org/abs/2401.11709) | — | ICRA 2024 | 否 | — |
| [Human-in-the-Loop Gaussian Splatting for Robotic Teleoperation](https://ieeexplore.ieee.org/document/3632755) | 2026-01-01 | RA-L 2026、ICRA 2026 | 否 | — |
| [IDAGC: Adaptive Generalized Human-Robot Collaboration via Human Intent Estimation and Multimodal Policy Learning](https://arxiv.org/abs/2507.04620) | 2025-07-07 | IROS 2025 | 否 | — |

---


## D8 · 策略学习与优化

> 归属层级：学习与基础设施。当前纳入 2820 个 canonical works；数量、环比和代表工作均按本站当前分类规则生成。

### 纳入边界

核心表达：`robot learning`、`imitation learning`、`reinforcement learning`、`diffusion policy`、`flow policy`、`flow matching policy`、`behavior cloning`、`behaviour cloning`、`offline reinforcement`、`online reinforcement`、`visuomotor policy`、`manipulation policy`、`skill learning`、`policy distillation`、`policy optimization`、`cross-embodiment`、`cross embodiment`、`cross-robot`、`multi-robot learning`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`manipulation`、`embodied`、`policy`、`control`、`locomotion`。

### 月度结构与环比

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

### 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [Developing Design Guidelines for Older Adults with Robot Learning from Demonstration](https://doi.org/10.15607/rss.2024.xx.030) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [3D Diffusion Policy: Generalizable Visuomotor Policy Learning via Simple 3D Representations](https://doi.org/10.15607/rss.2024.xx.067) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [A Dual Approach to Imitation Learning from Observations with Offline Datasets](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Action-Free Reasoning for Policy Generalization](https://arxiv.org/abs/2502.03729) | 2025-02-06 | CoRL 2025 | 是 | — |
| [Adapt3R: Adaptive 3D Scene Representation for Domain Transfer in Imitation Learning](https://arxiv.org/abs/2503.04877) | 2025-03-06 | CoRL 2025 | 是 | — |
| [Adapting by Analogy: OOD Generalization of Visuomotor Policies via Functional Correspondence](https://arxiv.org/abs/2506.12678) | 2025-06-15 | CoRL 2025 | 是 | — |
| [Adaptive Language-Guided Abstraction from Contrastive Explanations](https://arxiv.org/abs/2409.08212) | 2024-09-12 | CoRL 2024、CoRL 2024 | 是 | — |
| [Agreement Volatility: A Second-Order Metric for Uncertainty Quantification in Surgical Robot Learning](https://proceedings.mlr.press/v305/thompson25a.html) | 2025-10-07 | CoRL 2025 | 是 | — |
| [AirExo-2: Scaling up Generalizable Robotic Imitation Learning with Low-Cost Exoskeletons](https://arxiv.org/abs/2503.03081) | 2025-03-05 | CoRL 2025 | 是 | — |
| [ArticuBot: Learning Universal Articulated Object Manipulation Policy via Large Scale Simulation](https://arxiv.org/abs/2503.03045) | 2025-03-04 | RSS 2025 | 是 | — |
| [AtomicVLA: Unlocking the Potential of Atomic Skill Learning in Robots](https://arxiv.org/abs/2603.07648) | 2026-03-08 | CVPR 2026 | 是 | — |
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
| [Constraint-Preserving Data Generation for One-Shot Visuomotor Policy Generalization](https://proceedings.mlr.press/v305/lin25b.html) | 2025-10-07 | CoRL 2025 | 是 | — |
| [Continuous Control with Coarse-to-fine Reinforcement Learning](https://arxiv.org/abs/2407.07787) | 2024-07-10 | CoRL 2024、CoRL 2024 | 是 | — |
| [Contrastive Imitation Learning for Language-guided Multi-Task Robotic Manipulation](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Crossing the Human-Robot Embodiment Gap with Sim-to-Real RL using One Human Demonstration](https://arxiv.org/abs/2504.12609) | 2025-04-17 | CoRL 2025 | 是 | — |
| [CtRL-Sim: Reactive and Controllable Driving Agents with Offline Reinforcement Learning](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
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
| [Enhancing Visual Domain Robustness in Behaviour Cloning via Saliency-Guided Augmentation](https://arxiv.org/abs/2608.11870) | 2026-08-12 | CoRL 2024、CoRL 2024 | 是 | — |
| [EquiBot: SIM(3)-Equivariant Diffusion Policy for Generalizable and Data Efficient Learning](https://arxiv.org/abs/2407.01479) | 2024-07-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Equivariant Diffusion Policy](https://arxiv.org/abs/2407.01812) | 2024-07-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Few-Shot Neuro-Symbolic Imitation Learning for Long-Horizon Planning and Acting](https://arxiv.org/abs/2508.21501) | 2025-08-29 | CoRL 2025 | 是 | — |
| [FLARE: Robot Learning with Implicit World Modeling](https://arxiv.org/abs/2505.15659) | 2025-05-21 | CoRL 2025 | 是 | — |
| [FlowRetrieval: Flow-Guided Data Retrieval for Few-Shot Imitation Learning](https://arxiv.org/abs/2408.16944) | 2024-08-29 | CoRL 2024、CoRL 2024 | 是 | — |
| [GenDP: 3D Semantic Fields for Category-Level Generalizable Diffusion Policy](https://arxiv.org/abs/2410.17488) | 2024-10-23 | CoRL 2024、CoRL 2024 | 是 | — |
| [General Flow as Foundation Affordance for Scalable Robot Learning](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Genetic Algorithm for Curriculum Design in Multi-Agent Reinforcement Learning](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [HACMan++: Spatially-Grounded Motion Primitives for Manipulation](https://arxiv.org/abs/2407.08585) | 2024-07-11 | RSS 2024、RSS 2024 | 是 | — |
| [Handling Long-Term Safety and Uncertainty in Safe Reinforcement Learning](https://arxiv.org/abs/2409.12045) | 2024-09-18 | CoRL 2024、CoRL 2024 | 是 | — |
| [Imitation Bootstrapped Reinforcement Learning](https://doi.org/10.15607/rss.2024.xx.056) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Imitation Learning Based on Disentangled Representation Learning of Behavioral Characteristics](https://arxiv.org/abs/2509.04737) | 2025-09-05 | CoRL 2025 | 是 | — |
| [IMLE Policy: Fast and Sample Efficient Visuomotor Policy Learning via Implicit Maximum Likelihood Estimation](https://arxiv.org/abs/2502.12371) | 2025-02-17 | RSS 2025 | 是 | — |
| [Is Your Imitation Learning Policy Better than Mine? Policy Comparison with Near-Optimal Stopping](https://arxiv.org/abs/2503.10966) | 2025-03-14 | RSS 2025 | 是 | — |
| [JaxRobotarium: Training and Deploying Multi-Robot Policies in 10 Minutes](https://arxiv.org/abs/2505.06771) | 2025-05-10 | CoRL 2025 | 是 | — |
| [KDPE: A Kernel Density Estimation Strategy for Diffusion Policy Trajectory Selection](https://arxiv.org/abs/2508.10511) | 2025-08-14 | CoRL 2025 | 是 | — |
| [Keypoint Action Tokens Enable In-Context Imitation Learning in Robotics](https://doi.org/10.15607/rss.2024.xx.096) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [KOI: Accelerating Online Imitation Learning via Hybrid Key-state Guidance](https://arxiv.org/abs/2408.02912) | 2024-08-06 | CoRL 2024、CoRL 2024 | 是 | — |
| [Learning Robot Soccer from Egocentric Vision with Deep Reinforcement Learning](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Learning to Manipulate Anywhere: A Visual Generalizable Framework For Reinforcement Learning](https://arxiv.org/abs/2407.15815) | 2024-07-22 | CoRL 2024、CoRL 2024 | 是 | — |
| [LLARVA: Vision-Action Instruction Tuning Enhances Robot Learning](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [LodeStar: Long-horizon Dexterity via Synthetic Data Augmentation from Human Demonstrations](https://arxiv.org/abs/2508.17547) | 2025-08-24 | CoRL 2025 | 是 | — |
| [MaIL: Improving Imitation Learning with Selective State Space Models](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |

---


## D9 · 数据引擎与人类视频学习

> 归属层级：学习与基础设施。当前纳入 357 个 canonical works；数量、环比和代表工作均按本站当前分类规则生成。

### 纳入边界

核心表达：`robot dataset`、`robotics dataset`、`data engine`、`data scaling`、`large-scale robot data`、`large scale robot data`、`robot demonstration`、`teleoperation`、`tele-operation`、`human video`、`internet video`、`egocentric video`、`play data`、`autonomous data collection`、`data curation`、`data mixture`、`trajectory dataset`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`manipulation`、`embodied`、`action`、`trajectory`。

### 月度结构与环比

| 月份 | 本月 | 对比月 | 上月 | 环比增量 | 环比 |
|---|---:|---|---:|---:|---:|
| 2024-07 | 11 | — | 0 | +11 | 新增 |
| 2024-08 | 5 | 2024-07 | 11 | -6 | -54.5% |
| 2024-09 | 12 | 2024-08 | 5 | +7 | +140.0% |
| 2024-10 | 9 | 2024-09 | 12 | -3 | -25.0% |
| 2024-11 | 3 | 2024-10 | 9 | -6 | -66.7% |
| 2024-12 | 7 | 2024-11 | 3 | +4 | +133.3% |
| 2025-01 | 4 | 2024-12 | 7 | -3 | -42.9% |
| 2025-02 | 7 | 2025-01 | 4 | +3 | +75.0% |
| 2025-03 | 10 | 2025-02 | 7 | +3 | +42.9% |
| 2025-04 | 12 | 2025-03 | 10 | +2 | +20.0% |
| 2025-05 | 8 | 2025-04 | 12 | -4 | -33.3% |
| 2025-06 | 8 | 2025-05 | 8 | 0 | 0.0% |
| 2025-07 | 7 | 2025-06 | 8 | -1 | -12.5% |
| 2025-08 | 9 | 2025-07 | 7 | +2 | +28.6% |
| 2025-09 | 16 | 2025-08 | 9 | +7 | +77.8% |
| 2025-10 | 3 | 2025-09 | 16 | -13 | -81.3% |
| 2025-11 | 8 | 2025-10 | 3 | +5 | +166.7% |
| 2025-12 | 10 | 2025-11 | 8 | +2 | +25.0% |
| 2026-01 | 7 | 2025-12 | 10 | -3 | -30.0% |
| 2026-02 | 12 | 2026-01 | 7 | +5 | +71.4% |
| 2026-03 | 19 | 2026-02 | 12 | +7 | +58.3% |
| 2026-04 | 7 | 2026-03 | 19 | -12 | -63.2% |
| 2026-05 | 21 | 2026-04 | 7 | +14 | +200.0% |
| 2026-06 | 26 | 2026-05 | 21 | +5 | +23.8% |
| 2026-07 | 16 | 2026-06 | 26 | -10 | -38.5% |

### 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [Casper: Inferring Diverse Intents for Assistive Teleoperation with Vision Language Models](https://arxiv.org/abs/2506.14727) | 2025-06-17 | CoRL 2025 | 是 | — |
| [Conformalized Teleoperation: Confidently Mapping Human Inputs to High-Dimensional Robot Actions](https://doi.org/10.15607/rss.2024.xx.008) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [FERMI: Flexible Radio Mapping with a Hybrid Propagation Model and Scalable Autonomous Data Collection](https://arxiv.org/abs/2504.14862) | 2025-04-21 | RSS 2025 | 是 | — |
| [Flow as the Cross-Domain Manipulation Interface](https://arxiv.org/abs/2407.15208) | 2024-07-21 | CoRL 2024、CoRL 2024 | 是 | — |
| [Flying Hand: End-Effector-Centric Framework for Versatile Aerial Manipulation Teleoperation and Policy Learning](https://arxiv.org/abs/2504.10334) | 2025-04-14 | RSS 2025 | 是 | — |
| [Gen2Act: Human Video Generation in Novel Scenarios enables Generalizable Robot Manipulation](https://arxiv.org/abs/2409.16283) | 2024-09-24 | CoRL 2025 | 是 | — |
| [ImMimic: Cross-Domain Imitation from Human Videos via Mapping and Interpolation](https://arxiv.org/abs/2509.10952) | 2025-09-13 | CoRL 2025 | 是 | — |
| [Interface-level Intent Inference for Environment-agnostic Robot Teleoperation Assistance](https://www.roboticsproceedings.org/rss21/p081.html) | 2025-06-21 | RSS 2025 | 是 | — |
| [Lucid-XR: An Extended-Reality Data Engine for Robotic Manipulation](https://arxiv.org/abs/2605.00244) | 2026-04-30 | CoRL 2025 | 是 | — |
| [MimicFunc: Imitating Tool Manipulation from a Single Human Video via Functional Correspondence](https://arxiv.org/abs/2508.13534) | 2025-08-19 | CoRL 2025 | 是 | — |
| [Online Transfer and Adaptation of Tactile Skill: A Teleoperation Framework](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [OPEN TEACH: A Versatile Teleoperation System for Robotic Manipulation](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Open-TeleVision: Teleoperation with Immersive Active Visual Feedback](https://arxiv.org/abs/2407.01512) | 2024-07-01 | CoRL 2024、CoRL 2024 | 是 | [OpenTeleVision/TeleVision](https://github.com/OpenTeleVision/TeleVision) |
| [Phantom: Training Robots Without Robots Using Only Human Videos](https://arxiv.org/abs/2503.00779) | 2025-03-02 | CoRL 2025 | 是 | — |
| [Re-Mix: Optimizing Data Mixtures for Large Scale Imitation Learning](https://arxiv.org/abs/2408.14037) | 2024-08-26 | CoRL 2024、CoRL 2024 | 是 | — |
| [Robot Data Curation with Mutual Information Estimators](https://arxiv.org/abs/2502.08623) | 2025-02-12 | RSS 2025 | 是 | — |
| [Scaling Robot Policy Learning via Zero-Shot Labeling with Foundation Models](https://arxiv.org/abs/2410.17772) | 2024-10-23 | CoRL 2024、CoRL 2024 | 是 | — |
| [UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://arxiv.org/abs/2603.22264) | 2026-03-23 | CVPR 2026 | 是 | — |
| [GELLO: A General, Low-Cost, and Intuitive Teleoperation Framework for Robot Manipulators](https://arxiv.org/abs/2309.13037) | — | IROS 2024 | 否 | — |
| [EgoMimic: Scaling Imitation Learning via Egocentric Video](https://arxiv.org/abs/2410.24221) | 2024-10-31 | ICRA 2025 | 否 | — |
| [R+X: Retrieval and Execution from Everyday Human Videos](https://arxiv.org/abs/2407.12957) | 2024-07-17 | ICRA 2025 | 否 | — |
| [Radiance Fields for Robotic Teleoperation](https://arxiv.org/abs/2407.20194) | 2024-07-29 | IROS 2024 | 否 | — |
| [Diff-IP2D: Diffusion-Based Hand-Object Interaction Prediction on Egocentric Videos](https://arxiv.org/abs/2405.04370) | — | IROS 2025 | 否 | — |
| [Learning Fabric Manipulation in the Real World with Human Videos](https://arxiv.org/abs/2211.02832) | — | ICRA 2024 | 否 | — |
| [AeroHaptix: A Wearable Vibrotactile Feedback System for Enhancing Collision Avoidance in UAV Teleoperation](https://arxiv.org/abs/2407.12105) | 2024-07-16 | RA-L 2025 | 否 | — |
| [TreeScope: An Agricultural Robotics Dataset for LiDAR-Based Mapping of Trees in Forests and Orchards](https://arxiv.org/abs/2310.02162) | — | ICRA 2024 | 否 | — |
| [Learning Semantic Traversability With Egocentric Video and Automated Annotation Strategy](https://arxiv.org/abs/2406.02989) | — | RA-L 2024 | 否 | — |
| [Passive Bilateral Surgical Teleoperation With RCM and Spatial Constraints in the Presence of Time Delays](https://ieeexplore.ieee.org/document/3502221) | 2025-01-01 | T-RO 2025 | 否 | — |
| [RTAGrasp: Learning Task-Oriented Grasping from Human Videos via Retrieval, Transfer, and Alignment](https://arxiv.org/abs/2409.16033) | 2024-09-24 | ICRA 2025 | 否 | — |
| [Cybernetic avatars: Teleoperation technologies from in-body monitoring to social interaction](https://www.science.org/doi/10.1126/scirobotics.adg1842) | 2024-11-20 | Science Robotics 2024 | 否 | — |
| [E-BTS: Event-Based Tactile Sensor for Haptic Teleoperation in Augmented Reality](https://ieeexplore.ieee.org/document/3502215) | 2025-01-01 | T-RO 2025 | 否 | — |
| [One-Shot Imitation under Mismatched Execution](https://arxiv.org/abs/2409.06615) | 2024-09-10 | ICRA 2025 | 否 | — |
| [Cooperative vs. Teleoperation Control of the Steady Hand Eye Robot with Adaptive Sclera Force Control: A Comparative Study](https://arxiv.org/abs/2312.01631) | — | ICRA 2024 | 否 | — |
| [Passivity-Based Control of Distributed Teleoperation With Velocity/Force Manipulability Optimization](https://ieeexplore.ieee.org/document/3508192) | 2025-01-01 | T-RO 2025 | 否 | — |
| [Hierarchical Deep Learning for Intention Estimation of Teleoperation Manipulation in Assembly Tasks](https://arxiv.org/abs/2403.19770) | — | ICRA 2024 | 否 | — |
| [Reality Fusion: Robust Real-time Immersive Mobile Robot Teleoperation with Volumetric Visual Data Fusion](https://arxiv.org/abs/2408.01225) | 2024-08-02 | IROS 2024 | 否 | — |
| [Robotic Offline RL from Internet Videos via Value-Function Learning](https://ieeexplore.ieee.org/document/10611575) | 2024-05-13 | ICRA 2024 | 否 | — |
| [TELESIM: A Modular and Plug-and-Play Framework for Robotic Arm Teleoperation using a Digital Twin](https://arxiv.org/abs/2309.10579) | — | ICRA 2024 | 否 | — |
| [Chain-of-Modality: Learning Manipulation Programs from Multimodal Human Videos with Vision-Language-Models](https://arxiv.org/abs/2504.13351) | 2025-04-17 | ICRA 2025 | 否 | — |
| [Control-Barrier-Aided Teleoperation with Visual-Inertial SLAM for Safe MAV Navigation in Complex Environments](https://arxiv.org/abs/2403.04331) | — | ICRA 2024 | 否 | — |
| [Linearized Virtual Energy Tank for Passivity-Based Bilateral Teleoperation Using Linear MPC](https://ieeexplore.ieee.org/document/3554447) | 2025-01-01 | T-RO 2025 | 否 | — |
| [User-customizable Shared Control for Robot Teleoperation via Virtual Reality](https://arxiv.org/abs/2403.13177) | — | IROS 2024 | 否 | — |
| [Adaptive Neural Network Synchronous Tracking Control for Teleoperation Robots Under Event-Triggered Mechanism](https://ieeexplore.ieee.org/document/3455894) | 2024-11-01 | RA-L 2024 | 否 | — |
| [A Digital Twin-Driven Immersive Teleoperation Framework for Robot-Assisted Microsurgery](https://ieeexplore.ieee.org/document/10801954) | 2024-01-01 | IROS 2024 | 否 | — |
| [Exploring Cognitive Load Dynamics in Human-Machine Interaction for Teleoperation: A User-Centric Perspective on Remote Operation System Design](https://ieeexplore.ieee.org/document/10802226) | 2024-01-01 | IROS 2024 | 否 | — |
| [Passivity-Based Teleoperation With Variable Rotational Impedance Control](https://ieeexplore.ieee.org/document/3490260) | 2024-12-01 | RA-L 2024 | 否 | — |
| [Self-supervised 6-DoF Robot Grasping by Demonstration via Augmented Reality Teleoperation System](https://arxiv.org/abs/2404.03067) | — | ICRA 2024 | 否 | — |
| [A Tetherless Soft Robotic Wearable Haptic Human Machine Interface for Robot Teleoperation](https://ieeexplore.ieee.org/document/10802410) | 2024-01-01 | IROS 2024 | 否 | — |
| [Position Prediction for Space Teleoperation With SAO-CNN-BiGRU-Attention Algorithm](https://ieeexplore.ieee.org/document/3498700) | 2024-12-01 | RA-L 2024 | 否 | — |
| [Stability and Transparency in Mixed Reality Bilateral Human Teleoperation](https://arxiv.org/abs/2410.09679) | 2024-10-13 | T-RO 2025、ICRA 2026 | 否 | — |
| [A Tactile Lightweight Exoskeleton for Teleoperation: Design and Control Performance](https://ieeexplore.ieee.org/document/10802732) | 2024-01-01 | IROS 2024 | 否 | — |
| [DART: Dexterous Augmented Reality Teleoperation Platform for Large-Scale Robot Data Collection in Simulation](https://ieeexplore.ieee.org/document/11128299) | 2025-01-01 | ICRA 2025 | 否 | — |
| [Lie Group-Based User Motion Refinement Control for Teleoperation of a Constrained Robot Arm](https://ieeexplore.ieee.org/document/3401135) | 2024-07-01 | RA-L 2024 | 否 | — |
| [Sampling-Based Grasp and Collision Prediction for Assisted Teleoperation](https://arxiv.org/abs/2504.18186) | 2025-04-25 | ICRA 2025 | 否 | — |
| [SPOTS: Stable Placement of Objects with Reasoning in Semi-Autonomous Teleoperation Systems](https://arxiv.org/abs/2309.13937) | — | ICRA 2024 | 否 | — |
| [Adaptive User Interface With Parallel Neural Networks for Robot Teleoperation](https://ieeexplore.ieee.org/document/3518085) | 2025-02-01 | RA-L 2025 | 否 | — |
| [DiffGen: Robot Demonstration Generation via Differentiable Physics Simulation, Differentiable Rendering, and Vision-Language Model](https://arxiv.org/abs/2405.07309) | — | IROS 2025 | 否 | — |
| [Intelligent Mode-switching Framework for Teleoperation](https://arxiv.org/abs/2402.06047) | — | ICRA 2024 | 否 | — |
| [Perfectly Undetectable False Data Injection Attacks on Encrypted Bilateral Teleoperation System based on Dynamic Symmetry and Malleability](https://arxiv.org/abs/2409.13061) | 2024-09-19 | ICRA 2025 | 否 | — |
| [Towards Real-Time Generation of Delay-Compensated Video Feeds for Outdoor Mobile Robot Teleoperation](https://arxiv.org/abs/2409.09921) | 2024-09-16 | ICRA 2025 | 否 | — |

---


## D10 · 仿真、合成数据与 Sim-to-Real

> 归属层级：学习与基础设施。当前纳入 408 个 canonical works；数量、环比和代表工作均按本站当前分类规则生成。

### 纳入边界

核心表达：`sim-to-real`、`sim2real`、`simulation-to-reality`、`simulation to reality`、`synthetic robot data`、`robot simulation`、`robotics simulator`、`digital twin`、`domain randomization`、`procedural generation`、`synthetic demonstration`、`simulation data`、`physics simulator`、`neural simulator`、`generative simulator`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`manipulation`、`embodied`、`policy`、`control`、`simulation`。

### 月度结构与环比

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

### 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [Automated Creation of Digital Cousins for Robust Policy Learning](https://arxiv.org/abs/2410.07408) | 2024-10-09 | CoRL 2024、CoRL 2024 | 是 | — |
| [Bridging the Sim-to-Real Gap for Athletic Loco-Manipulation](https://arxiv.org/abs/2502.10894) | 2025-02-15 | RSS 2025 | 是 | — |
| [Bridging the Sim-to-Real Gap from the Information Bottleneck Perspective](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [Demonstrating GPU Parallelized Robot Simulation and Rendering for Generalizable Embodied AI with ManiSkill3](https://www.roboticsproceedings.org/rss21/p021.html) | 2025-06-21 | RSS 2025 | 是 | — |
| [DrEureka: Language Model Guided Sim-To-Real Transfer](https://doi.org/10.15607/rss.2024.xx.094) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [FetchBot: Learning Generalizable Object Fetching in Cluttered Scenes via Zero-Shot Sim2Real](https://arxiv.org/abs/2502.17894) | 2025-02-25 | CoRL 2025 | 是 | — |
| [Function Based Sim-to-Real Learning for Shape Control of Deformable Free-form Surfaces](https://doi.org/10.15607/rss.2024.xx.098) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Natural Language Can Help Bridge the Sim2Real Gap](https://doi.org/10.15607/rss.2024.xx.126) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Neural Robot Dynamics](https://arxiv.org/abs/2508.15755) | 2025-08-21 | CoRL 2025 | 是 | — |
| [One View, Many Worlds: Single-Image to 3D Object Meets Generative Domain Randomization for One-Shot 6D Pose Estimation](https://arxiv.org/abs/2509.07978) | 2025-09-09 | CoRL 2025 | 是 | — |
| [Reconciling Reality through Simulation: A Real-To-Sim-to-Real Approach for Robust Manipulation](https://doi.org/10.15607/rss.2024.xx.015) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [ScissorBot: Learning Generalizable Scissor Skill for Paper Cutting via Simulation, Imitation, and Sim2Real](https://arxiv.org/abs/2409.13966) | 2024-09-21 | CoRL 2024、CoRL 2024 | 是 | — |
| [Sim-to-Real Transfer via 3D Feature Fields for Vision-and-Language Navigation](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [SimShear: Sim-to-Real Shear-based Tactile Servoing](https://arxiv.org/abs/2508.20561) | 2025-08-28 | CoRL 2025 | 是 | — |
| [The Sound of Simulation: Learning Multimodal Sim-to-Real Robot Policies with Generative Audio](https://arxiv.org/abs/2507.02864) | 2025-07-03 | CoRL 2025 | 是 | — |
| [TieBot: Learning to Knot a Tie from Visual Demonstration through a Real-to-Sim-to-Real Approach](https://arxiv.org/abs/2407.03245) | 2024-07-03 | CoRL 2024、CoRL 2024 | 是 | — |
| [Wheeled Lab: Modern Sim2Real for Low-cost, Open-source Wheeled Robotics](https://arxiv.org/abs/2502.07380) | 2025-02-11 | CoRL 2025 | 是 | — |
| [SplatSim: Zero-Shot Sim2Real Transfer of RGB Manipulation Policies Using Gaussian Splatting](https://arxiv.org/abs/2409.10161) | 2024-09-16 | ICRA 2025 | 否 | — |
| [Learning to Fly in Seconds](https://arxiv.org/abs/2311.13081) | — | RA-L 2024 | 否 | — |
| [Sim-to-Real of Soft Robots With Learned Residual Physics](https://arxiv.org/abs/2402.01086) | — | RA-L 2024 | 否 | — |
| [Local Policies Enable Zero-shot Long-horizon Manipulation](https://arxiv.org/abs/2410.22332) | 2024-10-29 | ICRA 2025 | 否 | — |
| [S2R-ViT for Multi-Agent Cooperative Perception: Bridging the Gap from Simulation to Reality](https://arxiv.org/abs/2307.07935) | — | ICRA 2024 | 否 | — |
| [DiffusionNOCS: Managing Symmetry and Uncertainty in Sim2Real Multi-Modal Category-level Pose Estimation](https://arxiv.org/abs/2402.12647) | — | IROS 2024 | 否 | — |
| [Domain Randomization for Sim2real Transfer of Automatically Generated Grasping Datasets](https://arxiv.org/abs/2310.04517) | — | ICRA 2024 | 否 | — |
| [Bridging the Sim-to-Real Gap with Dynamic Compliance Tuning for Industrial Insertion](https://arxiv.org/abs/2311.07499) | — | ICRA 2024 | 否 | — |
| [ASGrasp: Generalizable Transparent Object Reconstruction and 6-DoF Grasp Detection from RGB-D Active Stereo Camera](https://arxiv.org/abs/2405.05648) | — | ICRA 2024 | 否 | — |
| [DISCOVERSE: Efficient Robot Simulation in Complex High-Fidelity Environments](https://arxiv.org/abs/2507.21981) | 2025-07-29 | IROS 2025 | 否 | — |
| [Dynamics as Prompts: In-Context Learning for Sim-to-Real System Identifications](https://arxiv.org/abs/2410.20357) | 2024-10-27 | RA-L 2025 | 否 | — |
| [Learning on the Fly: Rapid Policy Adaptation via Differentiable Simulation](https://arxiv.org/abs/2508.21065) | 2025-08-28 | RA-L 2026、ICRA 2026 | 否 | — |
| [Close the Sim2real Gap via Physically-based Structured Light Synthetic Data Simulation](https://arxiv.org/abs/2407.12449) | 2024-07-17 | ICRA 2024 | 否 | — |
| [Sim-to-real transfer of adaptive control parameters for AUV stabilisation under current disturbance](https://arxiv.org/abs/2310.11075) | — | IJRR 2024 | 否 | — |
| [What Matters in Learning A Zero-Shot Sim-to-Real RL Policy for Quadrotor Control? A Comprehensive Study](https://arxiv.org/abs/2412.11764) | 2024-12-16 | RA-L 2025、ICRA 2026 | 否 | — |
| [Continual Domain Randomization](https://arxiv.org/abs/2403.12193) | — | IROS 2024 | 否 | — |
| [TactGen: Tactile Sensory Data Generation via Zero-Shot Sim-to-Real Transfer](https://ieeexplore.ieee.org/document/3521967) | 2025-01-01 | T-RO 2025 | 否 | — |
| [One Net to Rule Them All: Domain Randomization in Quadcopter Racing Across Different Platforms](https://arxiv.org/abs/2504.21586) | 2025-04-30 | ICRA 2025 | 否 | — |
| [Bridging the Sim-to-Real Gap with Bayesian Inference](https://arxiv.org/abs/2403.16644) | — | IROS 2024 | 否 | — |
| [High-Fidelity Simulated Data Generation for Real-World Zero-Shot Robotic Manipulation Learning with Gaussian Splatting](https://arxiv.org/abs/2510.10637) | 2025-10-12 | RA-L 2026 | 否 | — |
| [Robotic Object Insertion with a Soft Wrist through Sim-to-Real Privileged Training](https://arxiv.org/abs/2408.17061) | 2024-08-30 | IROS 2024 | 否 | — |
| [Sim2Real Bilevel Adaptation for Object Surface Classification using Vision-Based Tactile Sensors](https://arxiv.org/abs/2311.01380) | — | ICRA 2024 | 否 | — |
| [PolyFit: A Peg-in-hole Assembly Framework for Unseen Polygon Shapes via Sim-to-real Adaptation](https://arxiv.org/abs/2312.02531) | — | IROS 2024 | 否 | — |
| [REPeat: A Real2Sim2Real Approach for Pre-acquisition of Soft Food Items in Robot-assisted Feeding](https://arxiv.org/abs/2410.10017) | 2024-10-13 | IROS 2024 | 否 | — |
| [Sim-to-Real Grasp Detection with Global-to-Local RGB-D Adaptation](https://arxiv.org/abs/2403.11511) | — | ICRA 2024 | 否 | — |
| [DexSim2Real$^{2}$: Building Explicit World Model for Precise Articulated Object Dexterous Manipulation](https://arxiv.org/abs/2409.08750) | 2024-09-13 | T-RO 2025 | 否 | — |
| [Domain Randomization for Object Detection in Manufacturing Applications using Synthetic Data: A Comprehensive Study](https://arxiv.org/abs/2506.07539) | 2025-06-09 | ICRA 2025 | 否 | — |
| [Impact of Static Friction on Sim2Real in Robotic Reinforcement Learning](https://arxiv.org/abs/2503.01255) | 2025-03-03 | IROS 2025 | 否 | — |
| [Learning Multi-Scale Context Mask-RCNN Network for Slant Angled Aerial Imagery in Instance Segmentation in a Sim2Real setup](https://ieeexplore.ieee.org/document/10610358) | 2024-05-13 | ICRA 2024 | 否 | — |
| [FalconGym: A Photorealistic Simulation Framework for Zero-Shot Sim-to-Real Vision-Based Quadrotor Navigation](https://arxiv.org/abs/2503.02198) | 2025-03-04 | IROS 2025 | 否 | — |
| [Integrating Model-based Control and RL for Sim2Real Transfer of Tight Insertion Policies](https://arxiv.org/abs/2505.11858) | 2025-05-17 | ICRA 2025 | 否 | — |
| [MetaMVUC: Active Learning for Sample-Efficient Sim-to-Real Domain Adaptation in Robotic Grasping](https://ieeexplore.ieee.org/document/3544083) | 2025-04-01 | RA-L 2025 | 否 | — |
| [Quantifying the Sim2Real Gap: Model-Based Verification and Validation in Autonomous Ground Systems](https://ieeexplore.ieee.org/document/3546126) | 2025-04-01 | RA-L 2025 | 否 | — |
| [Skill Transfer and Discovery for Sim-to-Real Learning: A Representation-Based Viewpoint](https://arxiv.org/abs/2404.05051) | — | IROS 2024 | 否 | — |
| [SurgEM: A Vision-Based Surgery Environment Modeling Framework for Constructing a Digital Twin Toward Autonomous Soft Tissue Manipulation](https://ieeexplore.ieee.org/document/3466074) | 2024-11-01 | RA-L 2024 | 否 | — |
| [Tracking cloth deformation: A novel dataset for closing the sim-to-real gap for robotic cloth manipulation learning](https://journals.sagepub.com/doi/10.1177/02783649251317617) | 2025-02-08 | IJRR 2025 | 否 | — |
| [BayRnTune: Adaptive Bayesian Domain Randomization via Strategic Fine-tuning](https://arxiv.org/abs/2310.10606) | — | IROS 2024 | 否 | — |
| [Domain Randomization for Learning to Navigate in Human Environments](https://ieeexplore.ieee.org/document/3521178) | 2025-02-01 | RA-L 2025 | 否 | — |
| [Test-Time Certifiable Self-Supervision to Bridge the Sim2Real Gap in Event-Based Satellite Pose Estimation](https://arxiv.org/abs/2409.06240) | 2024-09-10 | IROS 2024 | 否 | — |
| [Closing the Visual Sim-to-Real Gap with Object-Composable NeRFs](https://arxiv.org/abs/2403.04114) | — | ICRA 2024 | 否 | — |
| [Fine Manipulation Using a Tactile Skin: Learning in Simulation and Sim-to-Real Transfer](https://arxiv.org/abs/2409.12735) | 2024-09-19 | IROS 2024 | 否 | — |
| [RLPP: A Residual Method for Zero-Shot Real-World Autonomous Racing on Scaled Platforms](https://arxiv.org/abs/2501.17311) | 2025-01-28 | ICRA 2025 | 否 | — |
| [SuPerPM: A Surgical Perception Framework Based on Deep Point Matching Learned from Physical Constrained Simulation Data](https://arxiv.org/abs/2309.13863) | — | IROS 2024 | 否 | — |

---


## D11 · 动作关联的空间感知与表征

> 归属层级：学习与基础设施。当前纳入 529 个 canonical works；数量、环比和代表工作均按本站当前分类规则生成。

### 纳入边界

核心表达：`affordance`、`actionable 3d`、`actionable representation`、`spatial reasoning`、`robot perception`、`3d representation`、`4d representation`、`point cloud policy`、`scene graph`、`semantic scene representation`、`object-centric representation`、`object centric representation`、`visual representation for robot`、`active perception`、`tactile perception`、`visuotactile`、`vision-tactile`、`vision tactile`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`manipulation`、`embodied`、`action`、`affordance`、`tactile`。

### 月度结构与环比

| 月份 | 本月 | 对比月 | 上月 | 环比增量 | 环比 |
|---|---:|---|---:|---:|---:|
| 2024-07 | 8 | — | 0 | +8 | 新增 |
| 2024-08 | 8 | 2024-07 | 8 | 0 | 0.0% |
| 2024-09 | 19 | 2024-08 | 8 | +11 | +137.5% |
| 2024-10 | 8 | 2024-09 | 19 | -11 | -57.9% |
| 2024-11 | 16 | 2024-10 | 8 | +8 | +100.0% |
| 2024-12 | 8 | 2024-11 | 16 | -8 | -50.0% |
| 2025-01 | 3 | 2024-12 | 8 | -5 | -62.5% |
| 2025-02 | 8 | 2025-01 | 3 | +5 | +166.7% |
| 2025-03 | 20 | 2025-02 | 8 | +12 | +150.0% |
| 2025-04 | 16 | 2025-03 | 20 | -4 | -20.0% |
| 2025-05 | 16 | 2025-04 | 16 | 0 | 0.0% |
| 2025-06 | 24 | 2025-05 | 16 | +8 | +50.0% |
| 2025-07 | 12 | 2025-06 | 24 | -12 | -50.0% |
| 2025-08 | 12 | 2025-07 | 12 | 0 | 0.0% |
| 2025-09 | 25 | 2025-08 | 12 | +13 | +108.3% |
| 2025-10 | 22 | 2025-09 | 25 | -3 | -12.0% |
| 2025-11 | 16 | 2025-10 | 22 | -6 | -27.3% |
| 2025-12 | 10 | 2025-11 | 16 | -6 | -37.5% |
| 2026-01 | 14 | 2025-12 | 10 | +4 | +40.0% |
| 2026-02 | 23 | 2026-01 | 14 | +9 | +64.3% |
| 2026-03 | 39 | 2026-02 | 23 | +16 | +69.6% |
| 2026-04 | 20 | 2026-03 | 39 | -19 | -48.7% |
| 2026-05 | 33 | 2026-04 | 20 | +13 | +65.0% |
| 2026-06 | 30 | 2026-05 | 33 | -3 | -9.1% |
| 2026-07 | 18 | 2026-06 | 30 | -12 | -40.0% |

### 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation](https://arxiv.org/abs/2403.17846) | — | RSS 2024、RSS 2024 | 是 | — |
| [CLAMP: Crowdsourcing a LArge-scale in-the-wild haptic dataset with an open-source device for Multimodal robot Perception](https://arxiv.org/abs/2505.21495) | 2025-05-27 | CoRL 2025 | 是 | — |
| [GLOVER++: Unleashing the Potential of Affordance Learning from Human Behaviors for Robotic Manipulation](https://arxiv.org/abs/2505.11865) | 2025-05-17 | CoRL 2025 | 是 | — |
| [GraphEQA: Using 3D Semantic Scene Graphs for Real-time Embodied Question Answering](https://arxiv.org/abs/2412.14480) | 2024-12-19 | CoRL 2025 | 是 | — |
| [HRP: Human Affordances for Robotic Pre-Training](https://arxiv.org/abs/2407.18911) | 2024-07-26 | RSS 2024、RSS 2024 | 是 | — |
| [Learning from 10 Demos: Generalisable and Sample-Efficient Policy Learning with Oriented Affordance Frames](https://arxiv.org/abs/2410.12124) | 2024-10-15 | CoRL 2025 | 是 | — |
| [O$^3$Afford: One-Shot 3D Object-to-Object Affordance Grounding for Generalizable Robotic Manipulation](https://arxiv.org/abs/2509.06233) | 2025-09-07 | CoRL 2025 | 是 | — |
| [Physically Embodied Gaussian Splatting: A Visually Learnt and Physically Grounded 3D Representation for Robotics](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [RAM: Retrieval-Based Affordance Transfer for Generalizable Zero-Shot Robotic Manipulation](https://arxiv.org/abs/2407.04689) | 2024-07-05 | CoRL 2024、CoRL 2024 | 是 | — |
| [Reactive In-Air Clothing Manipulation with Confidence-Aware Dense Correspondence and Visuotactile Affordance](https://arxiv.org/abs/2509.03889) | 2025-09-04 | CoRL 2025 | 是 | — |
| [RoboPoint: A Vision-Language Model for Spatial Affordance Prediction in Robotics](https://proceedings.mlr.press/) | 2024-01-01 | CoRL 2024、CoRL 2024 | 是 | — |
| [SAVOR: Skill Affordance Learning from Visuo-Haptic Perception for Robot-Assisted Bite Acquisition](https://arxiv.org/abs/2506.02353) | 2025-06-03 | CoRL 2025 | 是 | — |
| [Tag Map: A Text-Based Map for Spatial Reasoning and Navigation with Large Language Models](https://arxiv.org/abs/2409.15451) | 2024-09-23 | CoRL 2024、CoRL 2024 | 是 | — |
| [Vision in Action: Learning Active Perception from Human Demonstrations](https://arxiv.org/abs/2506.15666) | 2025-06-18 | CoRL 2025 | 是 | — |
| [ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning](https://arxiv.org/abs/2309.16650) | — | ICRA 2024 | 否 | — |
| [Clio: Real-Time Task-Driven Open-Set 3D Scene Graphs](https://arxiv.org/abs/2404.13696) | — | RA-L 2024 | 否 | — |
| [NeuralFeels with neural fields: Visuotactile perception for in-hand manipulation](https://www.science.org/doi/10.1126/scirobotics.adl0628) | 2024-11-13 | Science Robotics 2024 | 否 | — |
| [Collaborative Dynamic 3D Scene Graphs for Automated Driving](https://arxiv.org/abs/2309.06635) | — | ICRA 2024 | 否 | — |
| [TacSL: A Library for Visuotactile Sensor Simulation and Learning](https://arxiv.org/abs/2408.06506) | 2024-08-12 | T-RO 2025 | 否 | — |
| [RT-Affordance: Affordances are Versatile Intermediate Representations for Robot Manipulation](https://arxiv.org/abs/2411.02704) | 2024-11-05 | ICRA 2025 | 否 | — |
| [ManipVQA: Injecting Robotic Affordance and Physically Grounded Information into Multi-Modal Large Language Models](https://arxiv.org/abs/2403.11289) | — | IROS 2024 | 否 | — |
| [Optimal Scene Graph Planning with Large Language Model Guidance](https://arxiv.org/abs/2309.09182) | — | ICRA 2024 | 否 | — |
| [SG-Bot: Object Rearrangement via Coarse-to-Fine Robotic Imagination on Scene Graphs](https://arxiv.org/abs/2309.12188) | — | ICRA 2024 | 否 | — |
| [ViTacTip: Design and Verification of a Novel Biomimetic Physical Vision-Tactile Fusion Sensor](https://arxiv.org/abs/2402.00199) | — | ICRA 2024 | 否 | — |
| [AffordGrasp: In-Context Affordance Reasoning for Open-Vocabulary Task-Oriented Grasping in Clutter](https://arxiv.org/abs/2503.00778) | 2025-03-02 | IROS 2025 | 否 | — |
| [Beyond Bare Queries: Open-Vocabulary Object Grounding with 3D Scene Graph](https://arxiv.org/abs/2406.07113) | — | ICRA 2025 | 否 | — |
| [UAD: Unsupervised Affordance Distillation for Generalization in Robotic Manipulation](https://arxiv.org/abs/2506.09284) | 2025-06-10 | ICRA 2025 | 否 | — |
| [Open Scene Graphs for Open-World Object-Goal Navigation](https://arxiv.org/abs/2508.04678) | 2025-08-06 | IJRR 2025 | 否 | — |
| [TartanGround: A Large-Scale Dataset for Ground Robot Perception and Navigation](https://arxiv.org/abs/2505.10696) | 2025-05-15 | IROS 2025 | 否 | — |
| [Language-Conditioned Affordance-Pose Detection in 3D Point Clouds](https://arxiv.org/abs/2309.10911) | — | ICRA 2024 | 否 | — |
| [Outram: One-shot Global Localization via Triangulated Scene Graph and Global Outlier Pruning](https://arxiv.org/abs/2309.08914) | — | ICRA 2024 | 否 | — |
| [Articulated Object Manipulation with Coarse-to-fine Affordance for Mitigating the Effect of Point Cloud Noise](https://arxiv.org/abs/2402.18699) | — | ICRA 2024 | 否 | — |
| [Long-Term Human Trajectory Prediction Using 3D Dynamic Scene Graphs](https://arxiv.org/abs/2405.00552) | — | RA-L 2024 | 否 | — |
| [Composing Pre-Trained Object-Centric Representations for Robotics From "What" and "Where" Foundation Models](https://arxiv.org/abs/2404.13474) | — | ICRA 2024 | 否 | — |
| [Open-Vocabulary Affordance Detection using Knowledge Distillation and Text-Point Correlation](https://arxiv.org/abs/2309.10932) | — | ICRA 2024 | 否 | — |
| [PreAfford: Universal Affordance-Based Pre-Grasping for Diverse Objects and Environments](https://arxiv.org/abs/2404.03634) | — | IROS 2024 | 否 | — |
| [MR-COGraphs: Communication-efficient Multi-Robot Open-vocabulary Mapping System via 3D Scene Graphs](https://arxiv.org/abs/2412.18381) | 2024-12-24 | RA-L 2025 | 否 | — |
| [NaturalVLM: Leveraging Fine-Grained Natural Language for Affordance-Guided Visual Manipulation](https://arxiv.org/abs/2403.08355) | — | RA-L 2024、ICRA 2026 | 否 | — |
| [FunGraph: Functionality Aware 3D Scene Graphs for Language-Prompted Scene Interaction](https://arxiv.org/abs/2503.07909) | 2025-03-10 | IROS 2025 | 否 | — |
| [OceanSim: A GPU-Accelerated Underwater Robot Perception Simulation Framework](https://arxiv.org/abs/2503.01074) | 2025-03-03 | IROS 2025 | 否 | — |
| [Commonsense Scene Graph-based Target Localization for Object Search](https://arxiv.org/abs/2404.00343) | — | IROS 2024 | 否 | — |
| [3D Force and Contact Estimation for a Soft-Bubble Visuotactile Sensor Using FEM](https://arxiv.org/abs/2310.11372) | — | ICRA 2024 | 否 | — |
| [UniAff: A Unified Representation of Affordances for Tool Usage and Articulation with Vision-Language Models](https://arxiv.org/abs/2409.20551) | 2024-09-30 | ICRA 2025 | 否 | — |
| [Snake Robot with Tactile Perception Navigates on Large-scale Challenging Terrain](https://arxiv.org/abs/2312.03225) | — | ICRA 2024 | 否 | — |
| [TacFlex: Multimode Tactile Imprints Simulation for Visuotactile Sensors With Coating Patterns](https://ieeexplore.ieee.org/document/3576970) | 2025-01-01 | T-RO 2025、ICRA 2026 | 否 | — |
| [Shared visuo-tactile interactive perception for robust object pose estimation](https://journals.sagepub.com/doi/10.1177/02783649241301443) | 2024-12-18 | IJRR 2024 | 否 | — |
| [ViTa-Zero: Zero-shot Visuotactile Object 6D Pose Estimation](https://arxiv.org/abs/2504.13179) | 2025-04-17 | ICRA 2025 | 否 | — |
| [A Parameter-Efficient Tuning Framework for Language-guided Object Grounding and Robot Grasping](https://arxiv.org/abs/2409.19457) | 2024-09-28 | ICRA 2025 | 否 | — |
| [DynamicGSG: Dynamic 3D Gaussian Scene Graphs for Environment Adaptation](https://arxiv.org/abs/2502.15309) | 2025-02-21 | IROS 2025 | 否 | — |
| [GaussianGraph: 3D Gaussian-Based Scene Graph Generation for Open-World Scene Understanding](https://arxiv.org/abs/2503.04034) | — | IROS 2025 | 否 | — |
| [Lost & Found: Tracking Changes from Egocentric Observations in 3D Dynamic Scene Graphs](https://arxiv.org/abs/2411.19162) | 2024-11-28 | RA-L 2025 | 否 | — |
| [Perceptual Factors for Environmental Modeling in Robotic Active Perception](https://arxiv.org/abs/2309.10620) | — | ICRA 2024 | 否 | — |
| [Point2Graph: An End-to-end Point Cloud-based 3D Open-Vocabulary Scene Graph for Robot Navigation](https://arxiv.org/abs/2409.10350) | 2024-09-16 | ICRA 2025 | 否 | — |
| [Visual-Tactile Perception Based Control Strategy for Complex Robot Peg-in-Hole Process via Topological and Geometric Reasoning](https://ieeexplore.ieee.org/document/3436334) | 2024-10-01 | RA-L 2024 | 否 | — |
| [ToolEENet: Tool Affordance 6D Pose Estimation](https://arxiv.org/abs/2404.04193) | — | IROS 2024 | 否 | — |
| [Belief Scene Graphs: Expanding Partial Scenes with Objects through Computation of Expectation](https://arxiv.org/abs/2402.03840) | — | ICRA 2024 | 否 | — |
| [Caging in Time: A Framework for Robust Object Manipulation under Uncertainties and Limited Robot Perception](https://arxiv.org/abs/2410.16481) | 2024-10-21 | IJRR 2025 | 否 | — |
| [Collaborative Dynamic 3D Scene Graphs for Open-Vocabulary Urban Scene Understanding](https://arxiv.org/abs/2503.08474) | 2025-03-11 | IROS 2025 | 否 | — |
| [CuriousBot: Interactive Mobile Exploration via Actionable 3D Relational Object Graph](https://arxiv.org/abs/2501.13338) | 2025-01-23 | RA-L 2026 | 否 | — |
| [EMBOSR: Embodied Spatial Reasoning for Enhanced Situated Question Answering in 3D Scenes](https://ieeexplore.ieee.org/document/10801720) | 2024-01-01 | IROS 2024 | 否 | — |

---


## D12 · 评测、安全、可靠性与故障恢复

> 归属层级：学习与基础设施。当前纳入 168 个 canonical works；数量、环比和代表工作均按本站当前分类规则生成。

### 纳入边界

核心表达：`robot benchmark`、`robotics benchmark`、`benchmark suite`、`embodied benchmark`、`policy evaluation`、`robot safety`、`safe robot`、`safe reinforcement learning`、`failure detection`、`failure recovery`、`uncertainty estimation`、`out-of-distribution`、`out of distribution`、`robustness evaluation`、`risk-sensitive`、`risk sensitive`、`runtime assurance`、`verification of robot`、`robot reliability`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`manipulation`、`embodied`、`policy`、`control`、`safety`。

### 月度结构与环比

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
| 2026-07 | 6 | 2026-06 | 10 | -4 | -40.0% |

### 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [Can We Detect Failures Without Failure Data? Uncertainty-Aware Runtime Failure Detection for Imitation Learning Policies](https://arxiv.org/abs/2503.08558) | 2025-03-11 | RSS 2025 | 是 | — |
| [RACER: Epistemic Risk-Sensitive RL Enables Fast Driving with Fewer Crashes](https://doi.org/10.15607/rss.2024.xx.080) | 2024-01-01 | RSS 2024、RSS 2024 | 是 | — |
| [Real-Time Out-of-Distribution Failure Prevention via Multi-Modal Reasoning](https://arxiv.org/abs/2505.10547) | 2025-05-15 | CoRL 2025 | 是 | — |
| [Uncertainty-aware Latent Safety Filters for Avoiding Out-of-Distribution Failures](https://arxiv.org/abs/2505.00779) | 2025-05-01 | CoRL 2025 | 是 | — |
| [Semantically Safe Robot Manipulation: From Semantic Scene Understanding to Motion Safeguards](https://arxiv.org/abs/2410.15185) | 2024-10-19 | RA-L 2025 | 否 | — |
| [PIETRA: Physics-Informed Evidential Learning for Traversing Out-of-Distribution Terrain](https://arxiv.org/abs/2409.03005) | 2024-09-04 | RA-L 2025 | 否 | — |
| [Deep Evidential Uncertainty Estimation for Semantic Segmentation under Out-Of-Distribution Obstacles](https://ieeexplore.ieee.org/document/10611342) | 2024-05-13 | ICRA 2024 | 否 | — |
| [Integrating Predictive Motion Uncertainties with Distributionally Robust Risk-Aware Control for Safe Robot Navigation in Crowds](https://arxiv.org/abs/2403.05081) | — | ICRA 2024 | 否 | — |
| [Sensor-based distributionally robust control for safe robot navigation in dynamic environments](https://arxiv.org/abs/2405.18251) | — | IJRR 2025 | 否 | — |
| [Recover: A Neuro-Symbolic Framework for Failure Detection and Recovery](https://arxiv.org/abs/2404.00756) | — | IROS 2024 | 否 | — |
| [HR-APR: APR-agnostic Framework with Uncertainty Estimation and Hierarchical Refinement for Camera Relocalisation](https://arxiv.org/abs/2402.14371) | — | ICRA 2024 | 否 | — |
| [Generative Modeling of Residuals for Real-Time Risk-Sensitive Safety with Discrete-Time Control Barrier Functions](https://arxiv.org/abs/2311.05802) | — | ICRA 2024 | 否 | — |
| [Updating Robot Safety Representations Online from Natural Language Feedback](https://arxiv.org/abs/2409.14580) | 2024-09-22 | ICRA 2025 | 否 | — |
| [Wait, That Feels Familiar: Learning to Extrapolate Human Preferences for Preference-Aligned Path Planning](https://arxiv.org/abs/2309.09912) | — | ICRA 2024 | 否 | — |
| [Adaptive Prediction Ensemble: Improving Out-of-Distribution Generalization of Motion Forecasting](https://arxiv.org/abs/2407.09475) | 2024-07-12 | RA-L 2025 | 否 | — |
| [Safe Robot Reflexes: A Taxonomy-Based Decision and Modulation Framework](https://ieeexplore.ieee.org/document/3519421) | 2025-01-01 | T-RO 2025 | 否 | — |
| [Improving Out-of-Distribution Generalization of Trajectory Prediction for Autonomous Driving via Polynomial Representations](https://arxiv.org/abs/2407.13431) | — | IROS 2024 | 否 | — |
| [A Hierarchical Framework for Robot Safety using Whole-body Tactile Sensors](https://ieeexplore.ieee.org/document/10610834) | 2024-05-13 | ICRA 2024 | 否 | — |
| [Towards Safe Robot Use with Edged or Pointed Objects: A Surrogate Study Assembling a Human Hand Injury Protection Database](https://arxiv.org/abs/2404.04004) | — | ICRA 2024 | 否 | — |
| [A Multimodal Handover Failure Detection Dataset and Baselines](https://arxiv.org/abs/2402.18319) | — | ICRA 2024 | 否 | — |
| [Designing Control Barrier Function via Probabilistic Enumeration for Safe Reinforcement Learning Navigation](https://arxiv.org/abs/2504.21643) | 2025-04-30 | RA-L 2025 | 否 | — |
| [A Unified Interaction Control Framework for Safe Robotic Ultrasound Scanning with Human-Intention-Aware Compliance](https://arxiv.org/abs/2411.19545) | 2024-11-29 | IROS 2024 | 否 | — |
| [Evidential Uncertainty Estimation for Multi-Modal Trajectory Prediction](https://arxiv.org/abs/2503.05274) | 2025-03-07 | IROS 2025 | 否 | — |
| [Large-scale Indoor Mapping with Failure Detection and Recovery in SLAM](https://ieeexplore.ieee.org/document/10802593) | 2024-01-01 | IROS 2024 | 否 | — |
| [OCCUQ: Exploring Efficient Uncertainty Quantification for 3D Occupancy Prediction](https://arxiv.org/abs/2503.10605) | — | ICRA 2025 | 否 | — |
| [Estimating Control Barriers from Offline Data](https://arxiv.org/abs/2503.10641) | 2025-02-21 | ICRA 2025 | 否 | — |
| [VLM Can Be a Good Assistant: Enhancing Embodied Visual Tracking with Self-Improving Vision-Language Models](https://arxiv.org/abs/2505.20718) | 2025-05-27 | IROS 2025 | 否 | — |
| [Risk-Sensitive Extended Kalman Filter](https://arxiv.org/abs/2305.11573) | — | ICRA 2024 | 否 | — |
| [Bio-Inspired Plastic Neural Networks for Zero-Shot Out-of-Distribution Generalization in Complex Animal-Inspired Robots](https://arxiv.org/abs/2503.12406) | 2025-03-16 | IROS 2025 | 否 | — |
| [Learning When to Ask for Help: Efficient Interactive Navigation via Implicit Uncertainty Estimation](https://arxiv.org/abs/2305.16502) | — | ICRA 2024 | 否 | — |
| [ToMPC: Task-oriented Model Predictive Control via ADMM for Safe Robotic Manipulation](https://arxiv.org/abs/2603.13944) | 2026-03-14 | RA-L 2025 | 否 | — |
| [Mitigating Hallucinations in YOLO-based Object Detection Models: A Revisit to Out-of-Distribution Detection](https://ieeexplore.ieee.org/document/11245852) | 2025-01-01 | IROS 2025 | 否 | — |
| [Road Obstacle Detection based on Unknown Objectness Scores](https://arxiv.org/abs/2403.18207) | — | ICRA 2024 | 否 | — |
| [A Metacognitive Approach to Out-of-Distribution Detection for Segmentation](https://arxiv.org/abs/2311.07578) | — | ICRA 2024 | 否 | — |
| [DOSE3: Diffusion-Based Unified Out-of-Distribution Detection on $\mathbb{SE}(3)$ Trajectories](https://ieeexplore.ieee.org/document/3640358) | 2026-02-01 | RA-L 2026 | 否 | — |
| [Dynamic Residual Safe Reinforcement Learning for Multi-Agent Safety-Critical Scenarios Decision-Making](https://arxiv.org/abs/2504.06670) | 2025-04-09 | IROS 2025 | 否 | — |
| [HD-OOD3D: Supervised and Unsupervised Out-of-Distribution object detection in LiDAR data](https://arxiv.org/abs/2410.23767) | — | IROS 2025 | 否 | — |
| [SVN-ICP: Uncertainty Estimation of ICP-based LiDAR Odometry using Stein Variational Newton](https://arxiv.org/abs/2509.08069) | 2025-09-09 | RA-L 2025、ICRA 2026 | 否 | — |
| [Uncertainty-Aware Shape Estimation of a Surgical Continuum Manipulator in Constrained Environments using Fiber Bragg Grating Sensors](https://arxiv.org/abs/2405.07104) | — | ICRA 2024 | 否 | — |
| [AugInsert: Learning Robust Visual-Force Policies via Data Augmentation for Object Assembly Tasks](https://arxiv.org/abs/2410.14968) | 2024-10-19 | IROS 2025 | 否 | — |
| [Differentiable Obstacle Avoidance Framework for Robot Safety](https://ieeexplore.ieee.org/document/3664595) | 2026-04-01 | RA-L 2026 | 否 | — |
| [Improving Out-of-Distribution Generalization of Learned Dynamics by Learning Pseudometrics and Constraint Manifolds](https://arxiv.org/abs/2403.12245) | — | ICRA 2024 | 否 | — |
| [Learning Robot Safety from Sparse Human Feedback using Conformal Prediction](https://arxiv.org/abs/2501.04823) | 2025-01-08 | T-RO 2026 | 否 | — |
| [Masked γ-SSL: Learning Uncertainty Estimation via Masked Image Modeling](https://ieeexplore.ieee.org/document/10610398) | 2024-05-13 | ICRA 2024 | 否 | — |
| [Trajectory Tracking Runtime Assurance for Systems with Partially Unknown Dynamics](https://ieeexplore.ieee.org/document/10611237) | 2024-05-13 | ICRA 2024 | 否 | — |
| [A Single Hydraulic Bellows-Based MRI-Safe Robotic Needle Driver Capable of Independent and Coupled Needle Translation and Rotation](https://ieeexplore.ieee.org/document/3661718) | 2026-01-01 | T-RO 2026、ICRA 2026 | 否 | — |
| [Anomaly detection for generic failure monitoring in robotic assembly, screwing and manipulation](https://arxiv.org/abs/2509.26308) | 2025-09-30 | RA-L 2026 | 否 | — |
| [CUEMP: Correspondence Uncertainty Estimation With Motion Priors for Dense Visual Odometry](https://ieeexplore.ieee.org/document/3666386) | 2026-04-01 | RA-L 2026 | 否 | — |
| [Distributional Decision Transformer: Risk-Sensitive Offline RL via Quantile-Based Critics and Stochastic Return](https://ieeexplore.ieee.org/document/11247007) | 2025-01-01 | IROS 2025 | 否 | — |
| [Failure Detection and Recovery for Quadrotors in the Presence of Severe Rotor Failures With Multiple Model $\mathcal {L}_{1}$ Adaptive Controller](https://ieeexplore.ieee.org/document/3630964) | 2026-01-01 | RA-L 2026 | 否 | — |
| [Failure Detection With Zero-Shot Error Correction in Robotic Manipulation](https://ieeexplore.ieee.org/document/3678124) | 2026-05-01 | RA-L 2026 | 否 | — |
| [Sequential Probabilistic Descriptor via Uncertainty-Aware Multi-Modal Fusion for Safety-Critical Place Recognition](https://ieeexplore.ieee.org/document/3669806) | 2026-04-01 | RA-L 2026 | 否 | — |
| [A Framework for the Systematic Evaluation of Obstacle Avoidance and Object-Aware Controllers](https://arxiv.org/abs/2510.24683) | 2025-10-28 | 预印本 | 否 | — |
| [A Sensor-Aware Phenomenological Framework for Lidar Degradation Simulation and SLAM Robustness Evaluation](https://arxiv.org/abs/2512.08653) | 2025-12-09 | 预印本 | 否 | — |
| [AC-VLA: Robust Out-of-Distribution Action Execution via Compositional Learning](https://arxiv.org/abs/2607.15714) | 2026-07-17 | 预印本 | 否 | — |
| [ActProbe: Action-Space Probe for Early Failure Detection of Generative Robot Policies](https://arxiv.org/abs/2606.08508) | 2026-06-07 | 预印本 | 否 | — |
| [An Open-Source Software Toolkit & Benchmark Suite for the Evaluation and Adaptation of Multimodal Action Models](https://arxiv.org/abs/2506.09172) | 2025-06-10 | 预印本 | 否 | — |
| [Analysis of Deep-Learning Methods in an ISO/TS 15066-Compliant Human-Robot Safety Framework](https://arxiv.org/abs/2511.19094) | 2025-11-24 | 预印本 | 否 | — |
| [ARMADA: Autonomous Online Failure Detection and Human Shared Control Empower Scalable Real-world Deployment and Adaptation](https://arxiv.org/abs/2510.02298) | 2025-10-02 | RA-L 2026 | 否 | — |
| [ATOM-CBF: Adaptive Safe Perception-Based Control under Out-of-Distribution Measurements](https://arxiv.org/abs/2511.08741) | 2025-11-11 | 预印本 | 否 | — |

---


## D13 · 持续学习、部署学习与自改进

> 归属层级：学习与基础设施。当前纳入 9 个 canonical works；数量、环比和代表工作均按本站当前分类规则生成。

### 纳入边界

核心表达：`continual robot learning`、`continual learning for robot`、`self-improving robot`、`self improving robot`、`learning from experience`、`learning while deploying`、`fleet learning`、`deployment data flywheel`、`offline-to-online`、`offline to online`、`online robot learning`、`online reinforcement learning`、`autonomous recovery`、`experience replay for robot`、`lifelong robot learning`、`test-time adaptation`、`test time adaptation`、`policy self-improvement`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`manipulation`、`embodied`、`policy`、`deployment`。

### 月度结构与环比

| 月份 | 本月 | 对比月 | 上月 | 环比增量 | 环比 |
|---|---:|---|---:|---:|---:|
| 2024-07 | 0 | — | 0 | 0 | — |
| 2024-08 | 0 | 2024-07 | 0 | 0 | — |
| 2024-09 | 0 | 2024-08 | 0 | 0 | — |
| 2024-10 | 0 | 2024-09 | 0 | 0 | — |
| 2024-11 | 0 | 2024-10 | 0 | 0 | — |
| 2024-12 | 0 | 2024-11 | 0 | 0 | — |
| 2025-01 | 0 | 2024-12 | 0 | 0 | — |
| 2025-02 | 0 | 2025-01 | 0 | 0 | — |
| 2025-03 | 1 | 2025-02 | 0 | +1 | 新增 |
| 2025-04 | 0 | 2025-03 | 1 | -1 | -100.0% |
| 2025-05 | 1 | 2025-04 | 0 | +1 | 新增 |
| 2025-06 | 0 | 2025-05 | 1 | -1 | -100.0% |
| 2025-07 | 0 | 2025-06 | 0 | 0 | — |
| 2025-08 | 0 | 2025-07 | 0 | 0 | — |
| 2025-09 | 1 | 2025-08 | 0 | +1 | 新增 |
| 2025-10 | 0 | 2025-09 | 1 | -1 | -100.0% |
| 2025-11 | 1 | 2025-10 | 0 | +1 | 新增 |
| 2025-12 | 0 | 2025-11 | 1 | -1 | -100.0% |
| 2026-01 | 0 | 2025-12 | 0 | 0 | — |
| 2026-02 | 0 | 2026-01 | 0 | 0 | — |
| 2026-03 | 0 | 2026-02 | 0 | 0 | — |
| 2026-04 | 0 | 2026-03 | 0 | 0 | — |
| 2026-05 | 0 | 2026-04 | 0 | 0 | — |
| 2026-06 | 2 | 2026-05 | 0 | +2 | 新增 |
| 2026-07 | 0 | 2026-06 | 2 | -2 | -100.0% |

### 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [SIME: Enhancing Policy Self-Improvement with Modal-level Exploration](https://arxiv.org/abs/2505.01396) | 2025-05-02 | IROS 2025 | 否 | — |
| [MAER-Nav: Bidirectional Motion Learning Through Mirror-Augmented Experience Replay for Robot Navigation](https://arxiv.org/abs/2503.23908) | 2025-03-31 | IROS 2025 | 否 | — |
| [Overparametrization helps offline-to-online generalization of closed-loop control from pixels](https://ieeexplore.ieee.org/document/10610284) | 2024-05-13 | ICRA 2024 | 否 | — |
| [Safe Offline-to-Online Multi-Agent Decision Transformer: A Safety Conscious Sequence Modeling Approach](https://ieeexplore.ieee.org/document/10801292) | 2024-01-01 | IROS 2024 | 否 | — |
| [Beyond Imitation: Self-Improving Robot Policies via Off-Policy Q-Planning](https://arxiv.org/abs/2608.21204) | 2026-08-21 | 预印本 | 否 | — |
| [ENPIRE: Agentic Robot Policy Self-Improvement in the Real World](https://arxiv.org/abs/2606.19980) | 2026-06-18 | 预印本 | 否 | — |
| [LACY: A Vision-Language Model-based Language-Action Cycle for Self-Improving Robotic Manipulation](https://arxiv.org/abs/2511.02239) | 2025-11-04 | ICRA 2026 | 否 | — |
| [SARM2: Multi-Task Stage Aware Reward Modeling for Self Improving Robotic Manipulation](https://arxiv.org/abs/2606.10305) | 2026-06-09 | 预印本 | 否 | — |
| [SOE: Sample-Efficient Robot Policy Self-Improvement via On-Manifold Exploration](https://arxiv.org/abs/2509.19292) | 2025-09-23 | ICRA 2026 | 否 | — |

---


## D14 · 多机器人协同与群体智能

> 归属层级：物理能力。当前纳入 52 个 canonical works；数量、环比和代表工作均按本站当前分类规则生成。

### 纳入边界

核心表达：`multi-robot learning`、`multi robot learning`、`multi-robot coordination`、`multi robot coordination`、`collaborative vla`、`cooperative manipulation`、`robot-to-robot`、`robot to robot`、`multi-agent world model`、`multi agent world model`、`decentralized robot learning`、`swarm learning`、`heterogeneous robot team`、`robot team coordination`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`embodied`、`coordination`、`cooperative`、`multi-agent`。

### 月度结构与环比

| 月份 | 本月 | 对比月 | 上月 | 环比增量 | 环比 |
|---|---:|---|---:|---:|---:|
| 2024-07 | 0 | — | 0 | 0 | — |
| 2024-08 | 0 | 2024-07 | 0 | 0 | — |
| 2024-09 | 1 | 2024-08 | 0 | +1 | 新增 |
| 2024-10 | 1 | 2024-09 | 1 | 0 | 0.0% |
| 2024-11 | 1 | 2024-10 | 1 | 0 | 0.0% |
| 2024-12 | 1 | 2024-11 | 1 | 0 | 0.0% |
| 2025-01 | 1 | 2024-12 | 1 | 0 | 0.0% |
| 2025-02 | 0 | 2025-01 | 1 | -1 | -100.0% |
| 2025-03 | 6 | 2025-02 | 0 | +6 | 新增 |
| 2025-04 | 3 | 2025-03 | 6 | -3 | -50.0% |
| 2025-05 | 2 | 2025-04 | 3 | -1 | -33.3% |
| 2025-06 | 0 | 2025-05 | 2 | -2 | -100.0% |
| 2025-07 | 1 | 2025-06 | 0 | +1 | 新增 |
| 2025-08 | 2 | 2025-07 | 1 | +1 | +100.0% |
| 2025-09 | 3 | 2025-08 | 2 | +1 | +50.0% |
| 2025-10 | 3 | 2025-09 | 3 | 0 | 0.0% |
| 2025-11 | 1 | 2025-10 | 3 | -2 | -66.7% |
| 2025-12 | 0 | 2025-11 | 1 | -1 | -100.0% |
| 2026-01 | 1 | 2025-12 | 0 | +1 | 新增 |
| 2026-02 | 0 | 2026-01 | 1 | -1 | -100.0% |
| 2026-03 | 3 | 2026-02 | 0 | +3 | 新增 |
| 2026-04 | 1 | 2026-03 | 3 | -2 | -66.7% |
| 2026-05 | 4 | 2026-04 | 1 | +3 | +300.0% |
| 2026-06 | 1 | 2026-05 | 4 | -3 | -75.0% |
| 2026-07 | 1 | 2026-06 | 1 | 0 | 0.0% |

### 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [Capability-Aware Shared Hypernetworks for Flexible Heterogeneous Multi-Robot Coordination](https://arxiv.org/abs/2501.06058) | 2025-01-10 | CoRL 2025 | 是 | — |
| [Latent Theory of Mind: A Decentralized Diffusion Architecture for Cooperative Manipulation](https://arxiv.org/abs/2505.09144) | 2025-05-14 | CoRL 2025 | 是 | — |
| [Benchmarking Multi-Robot Coordination in Realistic, Unstructured Human-Shared Environments](https://ieeexplore.ieee.org/document/10611005) | 2024-05-13 | ICRA 2024 | 否 | — |
| [Behavior Tree Capabilities for Dynamic Multi-Robot Task Allocation with Heterogeneous Robot Teams](https://arxiv.org/abs/2402.02833) | — | ICRA 2024 | 否 | — |
| [Optimal Trajectory Planning for Cooperative Manipulation with Multiple Quadrotors Using Control Barrier Functions](https://arxiv.org/abs/2503.01096) | 2025-03-03 | ICRA 2025 | 否 | — |
| [Integrating Online Learning and Connectivity Maintenance for Communication-Aware Multi-Robot Coordination](https://arxiv.org/abs/2410.05798) | 2024-10-08 | IROS 2024 | 否 | — |
| [D3G: Learning Multi-robot Coordination from Demonstrations](https://ieeexplore.ieee.org/document/10801743) | 2024-01-01 | IROS 2024 | 否 | — |
| [Online Multi-Robot Coordination and Cooperation with Task Precedence Relationships](https://arxiv.org/abs/2509.15052) | 2025-09-18 | T-RO 2025 | 否 | — |
| [Deadlock-Aware Control for Multirobot Coordination With Multiple Safety Constraints](https://ieeexplore.ieee.org/document/3600159) | 2025-01-01 | T-RO 2025、ICRA 2026 | 否 | — |
| [Design of a Multi-robot Coordination System based on Functional Expressions using Large Language Models](https://ieeexplore.ieee.org/document/10802571) | 2024-01-01 | IROS 2024 | 否 | — |
| [Communicating Intent as Behaviour Trees for Decentralised Multi-Robot Coordination](https://ieeexplore.ieee.org/document/10610441) | 2024-05-13 | ICRA 2024 | 否 | — |
| [Closed-Loop Cooperative Manipulation of Deformable Tissue via Visual Feedback Using Multiple Continuum Surgical Manipulators](https://ieeexplore.ieee.org/document/3551540) | 2025-05-01 | RA-L 2025 | 否 | — |
| [Leader-Follower Cooperative Manipulation Under Spatio-Temporal Constraints](https://ieeexplore.ieee.org/document/10802449) | 2024-01-01 | IROS 2024 | 否 | — |
| [Multi-Robot Coordination in an Adversarial Graph-Traversal Game](https://ieeexplore.ieee.org/document/11247499) | 2025-01-01 | IROS 2025 | 否 | — |
| [Alternating Partition Prioritized Planning for Scalable Multi-Robot Coordination in Congested Environments](https://ieeexplore.ieee.org/document/3587841) | 2025-09-01 | RA-L 2025 | 否 | — |
| [k-Robust Conflict-Based Search with Continuous time for Multi-robot Coordination](https://ieeexplore.ieee.org/document/10801503) | 2024-01-01 | IROS 2024 | 否 | — |
| [Physical Coupling for Collaboration in Heterogeneous Robot Teams](https://ieeexplore.ieee.org/document/3655268) | 2026-03-01 | RA-L 2026 | 否 | — |
| [A Multimodal Stochastic Planning Approach for Navigation and Multi-Robot Coordination](https://arxiv.org/abs/2509.19168) | 2025-09-23 | ICRA 2026 | 否 | — |
| [Adaptive Obstacle-Aware Task Assignment and Planning for Heterogeneous Robot Teaming](https://arxiv.org/abs/2510.14063) | 2025-10-15 | 预印本 | 否 | — |
| [Adaptive Visual Perception for Robotic Construction Process: A Multi-Robot Coordination Framework](https://arxiv.org/abs/2412.11275) | 2024-12-15 | 预印本 | 否 | — |
| [BlueME: Robust Underwater Robot-to-Robot Communication Using Compact Magnetoelectric Antennas](https://arxiv.org/abs/2411.09241) | 2024-11-14 | 预印本 | 否 | — |
| [CoDiMAD: Diffusion-Based Privileged Distillation for Communication-Free Multi-Robot Coordination](https://arxiv.org/abs/2607.09587) | 2026-07-10 | 预印本 | 否 | — |
| [Commerge: Communication-Efficient, Robust, and Fast LiDAR Map Merging Framework for Multi-Robot Coordination in Resource-Constrained Scenarios](https://arxiv.org/abs/2606.25386) | 2026-06-24 | 预印本 | 否 | — |
| [Destination-to-Chutes Task Mapping Optimization for Multi-Robot Coordination in Robotic Sorting Systems](https://arxiv.org/abs/2510.03472) | 2025-10-03 | 预印本 | 否 | — |
| [Distributed GNEP Algorithms without Multiplier Sharing and Applications to Multi-Robot Coordination and Contextual Bandit-Based Active Learning](https://arxiv.org/abs/2606.00759) | 2026-05-30 | 预印本 | 否 | — |
| [Distributed Linear Quadratic Gaussian for Multi-Robot Coordination with Localization Uncertainty](https://arxiv.org/abs/2504.03126) | 2025-03-26 | 预印本 | 否 | — |
| [EmboTeam: Grounding LLM Reasoning into Reactive Behavior Trees via PDDL for Embodied Multi-Robot Collaboration](https://arxiv.org/abs/2601.11063) | 2026-01-16 | 预印本 | 否 | — |
| [Event-Based Distributed Linear Quadratic Gaussian for Multi-Robot Coordination with Localization Uncertainty](https://arxiv.org/abs/2504.03125) | 2025-03-28 | 预印本 | 否 | — |
| [Failure-Aware Multi-Robot Coordination for Resilient and Adaptive Target Tracking](https://arxiv.org/abs/2508.02529) | 2025-08-04 | 预印本 | 否 | — |
| [Fault-Tolerant Multi-Robot Coordination with Limited Sensing within Confined Environments](https://arxiv.org/abs/2505.15036) | 2025-05-21 | 预印本 | 否 | — |
| [Federated Single-Agent Robotics: Multi-Robot Coordination Without Intra-Robot Multi-Agent Fragmentation](https://arxiv.org/abs/2604.11028) | 2026-04-13 | 预印本 | 否 | — |
| [FLEET: Formal Language-Grounded Scheduling for Heterogeneous Robot Teams](https://arxiv.org/abs/2510.07417) | 2025-10-08 | 预印本 | 否 | — |
| [GA3T: A Ground-Aerial Terrain Traversability Dataset for Heterogeneous Robot Teams in Unstructured Environments](https://arxiv.org/abs/2605.06478) | 2026-05-07 | 预印本 | 否 | — |
| [Genetic Fuzzy System-Based Multi-Robot Coordination for Planetary Missions](https://arxiv.org/abs/2608.12755) | 2026-08-13 | 预印本 | 否 | — |
| [Learning Multi-Robot Coordination through Locality-Based Factorized Multi-Agent Actor-Critic Algorithm](https://arxiv.org/abs/2503.18816) | 2025-03-24 | 预印本 | 否 | — |
| [Lyapunov Stability-Driven Control Algorithm for Heterogeneous Multi-Robot Coordination (I)](https://ras.papercept.net/conferences/conferences/ICRA26/program/ICRA26_ContentListWeb_3.html#tui1i_394) | — | ICRA 2026 | 否 | — |
| [MoRoCo: An Online Topology-Adaptive Framework for Multi-Operator Multi-Robot Coordination under Restricted Communication](https://arxiv.org/abs/2508.07657) | 2025-08-11 | 预印本 | 否 | — |
| [Multi Robot Coordination in Highly Dynamic Environments: Tackling Asymmetric Obstacles and Limited Communication](https://arxiv.org/abs/2509.08859) | 2025-09-09 | 预印本 | 否 | — |
| [Multi-robot coordination for connectivity recovery after unpredictable environment changes](https://arxiv.org/abs/2503.11520) | 2025-03-14 | 预印本 | 否 | — |
| [Multi-Robot Coordination for Planning under Context Uncertainty](https://arxiv.org/abs/2603.13748) | 2026-03-14 | 预印本 | 否 | — |
| [Multi-Robot Coordination in V2X Environments](https://arxiv.org/abs/2605.06662) | 2026-05-07 | 预印本 | 否 | — |
| [Multi-Robot Coordination Induced in an Adversarial Graph-Traversal Game](https://arxiv.org/abs/2409.08222) | 2024-09-12 | 预印本 | 否 | — |
| [Multi-Robot Coordination Under Physical Limitations](https://arxiv.org/abs/2503.20723) | 2025-03-26 | 预印本 | 否 | — |
| [Multi-Robot Coordination with Adversarial Perception](https://arxiv.org/abs/2504.09047) | 2025-04-12 | 预印本 | 否 | — |
| [Programmable Assembly and Cooperative Manipulation of Heterogeneous Microspheres Via Optoelectronic Tweezers](https://ras.papercept.net/conferences/conferences/ICRA26/program/ICRA26_ContentListWeb_3.html#tui1i_237) | — | ICRA 2026 | 否 | — |
| [Reducing Mental Workload through On-Demand Human Assistance for Physical Action Failures in LLM-based Multi-Robot Coordination](https://arxiv.org/abs/2603.28156) | 2026-03-30 | 预印本 | 否 | — |
| [RoboComm: A DID-based scalable and privacy-preserving Robot-to-Robot interaction over state channels](https://arxiv.org/abs/2504.09517) | 2025-04-13 | 预印本 | 否 | — |
| [Safe and Socially Aware Multi-Robot Coordination in Multi-Human Social Care Settings](https://arxiv.org/abs/2507.02521) | 2025-07-03 | 预印本 | 否 | — |
| [Safe Consensus of Cooperative Manipulation with Hierarchical Event-Triggered Control Barrier Functions](https://arxiv.org/abs/2603.06356) | 2026-03-06 | 预印本 | 否 | — |
| [Scout-Assisted Planning for Heterogeneous Robot Teams under Partially Known Environments](https://arxiv.org/abs/2605.22693) | 2026-05-21 | 预印本 | 否 | — |
| [SDHN: Skewness-Driven Hypergraph Networks for Enhanced Localized Multi-Robot Coordination](https://arxiv.org/abs/2504.06684) | 2025-04-09 | 预印本 | 否 | — |
| [Switching control of underactuated multi-channel systems with input constraints for cooperative manipulation](https://arxiv.org/abs/2511.22810) | 2025-11-27 | 预印本 | 否 | — |

---


## D15 · 触觉、力觉与多模态身体感知

> 归属层级：学习与基础设施。当前纳入 29 个 canonical works；数量、环比和代表工作均按本站当前分类规则生成。

### 纳入边界

核心表达：`visuotactile`、`vision-tactile`、`vision tactile`、`tactile-language-action`、`tactile language action`、`force-aware policy`、`force aware policy`、`proprioceptive policy`、`contact sensing`、`robot audio`、`multisensory manipulation`、`tactile foundation model`、`contact-aware world model`、`contact aware world model`、`tactile representation`、`force-torque sensing`、`force torque sensing`。

必须同时出现的机器人/动作语境：`robot`、`robotic`、`manipulation`、`embodied`、`tactile`、`force`、`contact`。

### 月度结构与环比

| 月份 | 本月 | 对比月 | 上月 | 环比增量 | 环比 |
|---|---:|---|---:|---:|---:|
| 2024-07 | 0 | — | 0 | 0 | — |
| 2024-08 | 1 | 2024-07 | 0 | +1 | 新增 |
| 2024-09 | 1 | 2024-08 | 1 | 0 | 0.0% |
| 2024-10 | 1 | 2024-09 | 1 | 0 | 0.0% |
| 2024-11 | 1 | 2024-10 | 1 | 0 | 0.0% |
| 2024-12 | 0 | 2024-11 | 1 | -1 | -100.0% |
| 2025-01 | 0 | 2024-12 | 0 | 0 | — |
| 2025-02 | 1 | 2025-01 | 0 | +1 | 新增 |
| 2025-03 | 1 | 2025-02 | 1 | 0 | 0.0% |
| 2025-04 | 0 | 2025-03 | 1 | -1 | -100.0% |
| 2025-05 | 2 | 2025-04 | 0 | +2 | 新增 |
| 2025-06 | 1 | 2025-05 | 2 | -1 | -50.0% |
| 2025-07 | 0 | 2025-06 | 1 | -1 | -100.0% |
| 2025-08 | 1 | 2025-07 | 0 | +1 | 新增 |
| 2025-09 | 1 | 2025-08 | 1 | 0 | 0.0% |
| 2025-10 | 0 | 2025-09 | 1 | -1 | -100.0% |
| 2025-11 | 1 | 2025-10 | 0 | +1 | 新增 |
| 2025-12 | 1 | 2025-11 | 1 | 0 | 0.0% |
| 2026-01 | 0 | 2025-12 | 1 | -1 | -100.0% |
| 2026-02 | 1 | 2026-01 | 0 | +1 | 新增 |
| 2026-03 | 2 | 2026-02 | 1 | +1 | +100.0% |
| 2026-04 | 0 | 2026-03 | 2 | -2 | -100.0% |
| 2026-05 | 1 | 2026-04 | 0 | +1 | 新增 |
| 2026-06 | 3 | 2026-05 | 1 | +2 | +200.0% |
| 2026-07 | 3 | 2026-06 | 3 | 0 | 0.0% |

### 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
| [exUMI: Extensible Robot Teaching System with Action-aware Task-agnostic Tactile Representation](https://arxiv.org/abs/2509.14688) | 2025-09-18 | CoRL 2025 | 是 | — |
| [Multimodal Visual-Tactile Representation Learning through Self-Supervised Contrastive Pre-Training](https://arxiv.org/abs/2401.12024) | — | ICRA 2024 | 否 | — |
| [UniT: Data Efficient Tactile Representation with Generalization to Unseen Objects](https://arxiv.org/abs/2408.06481) | 2024-08-12 | RA-L 2025 | 否 | — |
| [Soft Magnetic Skin With Motion and Contact Sensing for Anthropomorphic Robotic Finger](https://ieeexplore.ieee.org/document/3495590) | 2024-12-01 | RA-L 2024 | 否 | — |
| [UniTac-NV: A Unified Tactile Representation For Non-Vision-Based Tactile Sensors](https://arxiv.org/abs/2506.19699) | 2025-06-24 | IROS 2025 | 否 | — |
| [Contact sensing methodology based on propagation of interaction-induced deformation in elastic beams](https://journals.sagepub.com/doi/10.1177/02783649261419836) | 2026-02-04 | IJRR 2026 | 否 | — |
| [Object Extrinsic Contact Surface Reconstruction through Extrinsic Contact Sensing from Visuo-tactile Measurements](https://ieeexplore.ieee.org/document/11247448) | 2025-01-01 | IROS 2025 | 否 | — |
| [Semantic-Geometric-Physical-Driven Robot Manipulation Skill Transfer via Skill Library and Tactile Representation](https://arxiv.org/abs/2411.11714) | 2024-11-18 | IROS 2025 | 否 | — |
| [Distributed Contact Sensing Enabled by Vibration Propagation on Robot End-Effector](https://ieeexplore.ieee.org/document/11247041) | 2025-01-01 | IROS 2025 | 否 | — |
| [Shape-Space Deformer: Unified Visuo-Tactile Representations for Robotic Manipulation of Deformable Objects](https://arxiv.org/abs/2409.12419) | 2024-09-19 | ICRA 2025 | 否 | — |
| [$N_0$-VTLA: Scaling Vision-Tactile-Language-Action Model with Latent Tactile Tokens](https://arxiv.org/abs/2607.23782) | 2026-07-26 | 预印本 | 否 | — |
| [A Model-Based Decoupling Strategy for Proprioception and Contact Sensing in an Architected Soft Manipulator](https://arxiv.org/abs/2607.15582) | 2026-07-17 | 预印本 | 否 | — |
| [Active Contact Sensing for Robust Robot-to-Human Object Handover](https://arxiv.org/abs/2605.04610) | 2026-05-06 | 预印本 | 否 | — |
| [Bayesian Active Object Recognition and 6D Pose Estimation from Multimodal Contact Sensing](https://arxiv.org/abs/2603.21410) | 2026-03-22 | 预印本 | 否 | — |
| [ContactFusion: Stochastic Poisson Surface Maps from Visual and Contact Sensing](https://arxiv.org/abs/2503.16592) | 2025-03-20 | 预印本 | 否 | — |
| [FG-CLTP: Fine-Grained Contrastive Language Tactile Pretraining for Robotic Manipulation](https://arxiv.org/abs/2603.10871) | 2026-03-11 | 预印本 | 否 | — |
| [Grasping Force Estimation for Markerless Visuotactile Sensors](https://arxiv.org/abs/2410.22825) | 2024-10-30 | 预印本 | 否 | — |
| [HapTile: A Haptic-Informed Vision-Tactile-Language-Action Dataset for Contact-Rich Imitation Learning](https://arxiv.org/abs/2606.04825) | 2026-06-03 | 预印本 | 否 | — |
| [Imagining the Sense of Touch: Touch-Informed Manipulation via Imagined Tactile Representations](https://arxiv.org/abs/2607.01684) | 2026-07-02 | 预印本 | 否 | — |
| [LightTact: A Visual-Tactile Fingertip Sensor for Deformation-Independent Contact Sensing](https://arxiv.org/abs/2512.20591) | 2025-12-23 | RSS 2026 | 否 | — |
| [MicCheck: Repurposing Off-the-Shelf Pin Microphones for Easy and Low-Cost Contact Sensing](https://arxiv.org/abs/2511.18299) | 2025-11-23 | 预印本 | 否 | — |
| [OmniVTLA: Vision-Tactile-Language-Action Models with Semantic-Aligned Tactile Sensing](https://arxiv.org/abs/2508.08706) | 2025-08-12 | 预印本 | 否 | — |
| [RETRO: REthinking Tactile Representation Learning with Material PriOrs](https://arxiv.org/abs/2505.14319) | 2025-05-20 | 预印本 | 否 | — |
| [Sensor-Invariant Tactile Representation](https://arxiv.org/abs/2502.19638) | 2025-02-27 | 预印本 | 否 | — |
| [TactX: Learning Shared Tactile Representations Across Diverse Sensors](https://arxiv.org/abs/2606.31236) | 2026-06-30 | 预印本 | 否 | — |
| [Toward Gripper-Integrated Active Electrosense for Pre-Contact Sensing in Underwater Soft Grippers](https://arxiv.org/abs/2606.03204) | 2026-06-02 | 预印本 | 否 | — |
| [UniForce: A Unified Latent Force Model for Robot Manipulation with Diverse Tactile Sensors](https://arxiv.org/abs/2602.01153) | 2026-02-01 | 预印本 | 否 | — |
| [VT-MUSE: Multimodal Unified Sequential Visuotactile Representation Learning for Manipulation](https://arxiv.org/abs/2608.21290) | 2026-08-21 | 预印本 | 否 | — |
| [VTLA: Vision-Tactile-Language-Action Model with Preference Learning for Insertion Manipulation](https://arxiv.org/abs/2505.09577) | 2025-05-14 | 预印本 | 否 | — |

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
| [OpenVLA: An Open-Source Vision-Language-Action Model](https://proceedings.mlr.press/v270/kim25c.html) | [2406.09246](https://arxiv.org/abs/2406.09246) | CoRL 2024 | 具身基础模型与通才策略 | Stanford University、UC Berkeley、Toyota Research Institute |
| [Robotic Control via Embodied Chain-of-Thought Reasoning](https://proceedings.mlr.press/v270/zawalski25a.html) | [2407.08693](https://arxiv.org/abs/2407.08693) | CoRL 2024 | 分层推理、规划与记忆 | UC Berkeley、Stanford University、University of Warsaw |
| [ReKep: Spatio-Temporal Reasoning of Relational Keypoint Constraints for Robotic Manipulation](https://proceedings.mlr.press/v270/huang25g.html) | [2409.01652](https://arxiv.org/abs/2409.01652) | CoRL 2024 | 灵巧、双臂与接触操作 | Stanford University、Columbia University |
| [HumanPlus: Humanoid Shadowing and Imitation from Humans](https://proceedings.mlr.press/v270/fu25a.html) | [2406.10454](https://arxiv.org/abs/2406.10454) | CoRL 2024 | 人形、运动与全身控制 | Stanford University |
| [OmniH2O: Universal and Dexterous Human-to-Humanoid Whole-Body Teleoperation and Learning](https://proceedings.mlr.press/v270/he25b.html) | [2406.08858](https://arxiv.org/abs/2406.08858) | CoRL 2024 | 人形、运动与全身控制 | Carnegie Mellon University、Shanghai Jiao Tong University |
| [Scaling Proprioceptive-Visual Learning with Heterogeneous Pre-trained Transformers](https://papers.nips.cc/paper_files/paper/2024/hash/e0f393e7980a24fd12fa6f15adfa25fb-Abstract-Conference.html) | [2409.20537](https://arxiv.org/abs/2409.20537) | NeurIPS 2024 | 具身基础模型与通才策略 | MIT CSAIL、Meta FAIR |
| [π₀: A Vision-Language-Action Flow Model for General Robot Control](https://www.roboticsproceedings.org/rss21/p010.html) | [2410.24164](https://arxiv.org/abs/2410.24164) | RSS 2025 | 具身基础模型与通才策略 | Physical Intelligence |
| [SpatialVLA: Exploring Spatial Representations for Visual-Language-Action Models](https://www.roboticsproceedings.org/rss21/p011.html) | [2501.15830](https://arxiv.org/abs/2501.15830) | RSS 2025 | 具身基础模型与通才策略 | Shanghai AI Laboratory、Fudan University、Shanghai Jiao Tong University |
| [FAST: Efficient Action Tokenization for Vision-Language-Action Models](https://www.roboticsproceedings.org/rss21/p012.html) | [2501.09747](https://arxiv.org/abs/2501.09747) | RSS 2025 | 具身基础模型与通才策略 | Physical Intelligence、UC Berkeley、Stanford University |
| [Learning to Act Anywhere with Task-centric Latent Actions](https://www.roboticsproceedings.org/rss21/p014.html) | [2505.06111](https://arxiv.org/abs/2505.06111) | RSS 2025 | 具身基础模型与通才策略 | The University of Hong Kong、OpenDriveLab、AgiBot |
| [Unified World Models: Coupling Video and Action Diffusion for Pretraining on Large Robotic Datasets](https://www.roboticsproceedings.org/rss21/p015.html) | [2504.02792](https://arxiv.org/abs/2504.02792) | RSS 2025 | 世界模型与预测控制 | University of Washington、Toyota Research Institute |
| [ConRFT: A Reinforced Fine-tuning Method for VLA Models via Consistency Policy](https://www.roboticsproceedings.org/rss21/p019.html) | [2502.05450](https://arxiv.org/abs/2502.05450) | RSS 2025 | 具身基础模型与通才策略 | Institute of Automation, Chinese Academy of Sciences、University of Chinese Academy of Sciences |
| [Robot Learning with Super-Linear Scaling](https://www.roboticsproceedings.org/rss21/p025.html) | [2412.01770](https://arxiv.org/abs/2412.01770) | RSS 2025 | 策略学习与优化 | MIT、University of Washington、Stanford University |
| [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html) | [2503.02881](https://arxiv.org/abs/2503.02881) | RSS 2025 | 策略学习与优化 | Shanghai Jiao Tong University、Tsinghua University、Shanghai Qizhi Institute |
| [π₀.₅: A Vision-Language-Action Model with Open-World Generalization](https://proceedings.mlr.press/v305/black25a.html) | [2504.16054](https://arxiv.org/abs/2504.16054) | CoRL 2025 | 具身基础模型与通才策略 | Physical Intelligence、UC Berkeley、Stanford University |
| [Reflective Planning: Vision-Language Models for Multi-Stage Long-Horizon Robotic Manipulation](https://proceedings.mlr.press/v305/feng25b.html) | [2502.16707](https://arxiv.org/abs/2502.16707) | CoRL 2025 | 灵巧、双臂与接触操作 | Cornell University、The Chinese University of Hong Kong、Yale University |
| [LaDi-WM: A Latent Diffusion-Based World Model for Predictive Manipulation](https://proceedings.mlr.press/v305/huang25a.html) | [2505.11528](https://arxiv.org/abs/2505.11528) | CoRL 2025 | 世界模型与预测控制 | National University of Defense Technology、Peking University、Shenzhen University |
| [DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://proceedings.mlr.press/v305/xu25b.html) | [2505.21864](https://arxiv.org/abs/2505.21864) | CoRL 2025 | 灵巧、双臂与接触操作 | Stanford University、Columbia University、J.P. Morgan AI Research |
| [Long-VLA: Unleashing Long-Horizon Capability of Vision Language Action Model for Robot Manipulation](https://proceedings.mlr.press/v305/fan25a.html) | [2508.19958](https://arxiv.org/abs/2508.19958) | CoRL 2025 | 具身基础模型与通才策略 | Westlake University、Zhejiang University、Xi'an Jiaotong University |
| [ParticleFormer: A 3D Point Cloud World Model for Multi-Object, Multi-Material Robotic Manipulation](https://proceedings.mlr.press/v305/huang25c.html) | [2506.23126](https://arxiv.org/abs/2506.23126) | CoRL 2025 | 世界模型与预测控制 | Stanford University、The RAI Institute |
| [ActiveVLA: Injecting Active Perception into Vision-Language-Action Models for Precise 3D Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_ActiveVLA_Injecting_Active_Perception_into_Vision-Language-Action_Models_for_Precise_3D_CVPR_2026_paper.html) | [2601.08325](https://arxiv.org/abs/2601.08325) | CVPR 2026 | 具身基础模型与通才策略 | Fudan University、Shanghai Innovation Institute、Nanyang Technological University |
| [ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Zhong_ACoT-VLA_Action_Chain-of-Thought_for_Vision-Language-Action_Models_CVPR_2026_paper.html) | [2601.11404](https://arxiv.org/abs/2601.11404) | CVPR 2026 | 具身基础模型与通才策略 | Beihang University、AgiBot |
| [Action-Sketcher: From Reasoning to Action via Visual Sketches for Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Tan_Action-Sketcher_From_Reasoning_to_Action_via_Visual_Sketches_for_Robotic_CVPR_2026_paper.html) | [2601.01618](https://arxiv.org/abs/2601.01618) | CVPR 2026 | 具身基础模型与通才策略 | Peking University、Beijing Academy of Artificial Intelligence、University of Sydney |
| [Motus: A Unified Latent Action World Model](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html) | [2512.13030](https://arxiv.org/abs/2512.13030) | CVPR 2026 | 世界模型与预测控制 | Tsinghua University、ShengShu、Peking University |
| [AtomicVLA: Unlocking the Potential of Atomic Skill Learning in Robots](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_AtomicVLA_Unlocking_the_Potential_of_Atomic_Skill_Learning_in_Robots_CVPR_2026_paper.html) | [2603.07648](https://arxiv.org/abs/2603.07648) | CVPR 2026 | 策略学习与优化 | Sun Yat-sen University、Peng Cheng Laboratory、Yinwang Intelligent Technology |
| [UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html) | [2603.22264](https://arxiv.org/abs/2603.22264) | CVPR 2026 | 数据引擎与人类视频学习 | Tsinghua University、Shanghai Qizhi Institute、Sun Yat-sen University |
| [Cross-Hand Latent Representation for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Jiang_Cross-Hand_Latent_Representation_for_Vision-Language-Action_Models_CVPR_2026_paper.html) | [2603.10158](https://arxiv.org/abs/2603.10158) | CVPR 2026 | 具身基础模型与通才策略 | UC San Diego、Amazon FAR、UC Berkeley |
| [VIRAL: Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/He_VIRAL_Visual_Sim-to-Real_at_Scale_for_Humanoid_Loco-Manipulation_CVPR_2026_paper.html) | [2511.15200](https://arxiv.org/abs/2511.15200) | CVPR 2026 | 人形、运动与全身控制 | NVIDIA、Carnegie Mellon University、UC Berkeley |
| [PointWorld: Scaling 3D World Models for In-The-Wild Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Huang_PointWorld_Scaling_3D_World_Models_for_In-The-Wild_Robotic_Manipulation_CVPR_2026_paper.html) | [2601.03782](https://arxiv.org/abs/2601.03782) | CVPR 2026 | 世界模型与预测控制 | Stanford University、NVIDIA |
| [SIMPACT: Simulation-Enabled Action Planning using Vision-Language Models](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_SIMPACT_Simulation-Enabled_Action_Planning_using_Vision-Language_Models_CVPR_2026_paper.html) | [2512.05955](https://arxiv.org/abs/2512.05955) | CVPR 2026 | 具身基础模型与通才策略 | University of Maryland、University of Illinois Urbana-Champaign、Harvard University |

---


## 机构 Affiliation 覆盖与兼容入口

> 旧页面曾把母机构字符串、研究院、实验室和企业研究组织混在同一排行榜里，并把不同 venue-year 数误写成“官方评审工作数”。该排名已停用。

新的[全球关键研究组雷达](/groups/)使用分层组织图和 G1–G0 归属证据。原始 affiliation 仍保留用于母机构发现，但不能自动证明具体实验室归属。

| 数据层 | 数量 |
|---|---:|
| Canonical works | 41592 |
| 带 organization 归属边的 work | 100 |
| 持续跟踪研究组 | 60 |
| 待复核 G3/G0 候选 | 2 |

### 必须保留的区别

- NVIDIA 与 NVIDIA GEAR/Cosmos/Seattle Robotics Lab 分开。
- CMU 与 CMU Robotics Institute 及其各实验室分开。
- Physical Intelligence 公司与 MPI-IS 同名部门分开。
- Amazon FAR 与 Amazon Robotics 分开。
- RAI Institute 与 Boston Dynamics 分开。

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

---


## 论文证据库

> 本表由 `data/papers.json` 自动生成。候选层用于趋势数量；“精读”表示 ID、标题、v1 日期和摘要已逐条复核，并补充贡献、局限和实验信号。

[下载 JSON](https://raw.githubusercontent.com/JoenHune/embodied-ai-radar/main/data/papers.json) · [下载 CSV](https://raw.githubusercontent.com/JoenHune/embodied-ai-radar/main/data/papers.csv) · [下载完整 Markdown 报告](https://raw.githubusercontent.com/JoenHune/embodied-ai-radar/main/embodied-ai-radar-report.md)

### 全量候选分表

- [2024 年候选](/database/2024)
- [2025 年候选](/database/2025)
- [2026 年候选](/database/2026)

JSON/CSV 包含全部 2650 条纳入统计记录；网页按年份拆分，避免单页过大。

### 精读与核验记录

| arXiv ID | 论文 | v1 月份 | 主方向 | 置信度 | 层级 | 同行评审 |
|---|---|---|---|---|---|---|
| 2507.00416 | [Evo-0: Vision-Language-Action Model with Implicit Spatial Understanding](https://arxiv.org/abs/2507.00416) | 2025-07 | 具身基础模型与通才策略 | high | 精读 | — |
| 2507.01424 | [TriVLA: A Triple-System-Based Unified Vision-Language-Action Model with Episodic World Modeling for General Robot Control](https://arxiv.org/abs/2507.01424) | 2025-07 | 具身基础模型与通才策略 | high | 精读 | — |
| 2507.05198 | [EmbodieDreamer: Advancing Real2Sim2Real Transfer for Policy Training via Embodied World Modeling](https://arxiv.org/abs/2507.05198) | 2025-07 | 世界模型与预测控制 | high | 精读 | — |
| 2507.06224 | [EC-Flow: Enabling Versatile Robotic Manipulation from Action-Unlabeled Videos via Embodiment-Centric Flow](https://arxiv.org/abs/2507.06224) | 2025-07 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2507.09117 | [Towards Human-level Dexterity via Robot Learning](https://arxiv.org/abs/2507.09117) | 2025-07 | 策略学习与优化 | high | 精读 | — |
| 2507.15493 | [GR-3 Technical Report](https://arxiv.org/abs/2507.15493) | 2025-07 | 具身基础模型与通才策略 | high | 精读 | — |
| 2507.23523 | [H-RDT: Human Manipulation Enhanced Bimanual Robotic Manipulation](https://arxiv.org/abs/2507.23523) | 2025-07 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2508.00795 | [Video Generators are Robot Policies](https://arxiv.org/abs/2508.00795) | 2025-08 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2508.02062 | [RICL: Adding In-Context Adaptability to Pre-Trained Vision-Language-Action Models](https://arxiv.org/abs/2508.02062) | 2025-08 | 具身基础模型与通才策略 | high | 精读 | — |
| 2508.03645 | [DiWA: Diffusion Policy Adaptation with World Models](https://arxiv.org/abs/2508.03645) | 2025-08 | 策略学习与优化 | high | 精读 | — |
| 2508.08706 | [OmniVTLA: Vision-Tactile-Language-Action Models with Semantic-Aligned Tactile Sensing](https://arxiv.org/abs/2508.08706) | 2025-08 | 触觉、力觉与多模态身体感知 | high | 精读 | — |
| 2508.09976 | [Masquerade: Learning from In-the-wild Human Videos using Data-Editing](https://arxiv.org/abs/2508.09976) | 2025-08 | 数据引擎与人类视频学习 | high | 精读 | — |
| 2508.17600 | [GWM: Towards Scalable Gaussian World Models for Robotic Manipulation](https://arxiv.org/abs/2508.17600) | 2025-08 | 世界模型与预测控制 | high | 精读 | — |
| 2508.21112 | [EO-1: An Open Unified Embodied Foundation Model for General Robot Control](https://arxiv.org/abs/2508.21112) | 2025-08 | 具身基础模型与通才策略 | high | 精读 | — |
| 2509.01819 | [ManiFlow: A General Robot Manipulation Policy via Consistency Flow Training](https://arxiv.org/abs/2509.01819) | 2025-09 | 策略学习与优化 | high | 精读 | — |
| 2509.05513 | [OpenEgo: A Large-Scale Multimodal Egocentric Dataset for Dexterous Manipulation](https://arxiv.org/abs/2509.05513) | 2025-09 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2509.07445 | [Text2Touch: Tactile In-Hand Manipulation with LLM-Designed Reward Functions](https://arxiv.org/abs/2509.07445) | 2025-09 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2509.18428 | [Latent Action Pretraining Through World Modeling](https://arxiv.org/abs/2509.18428) | 2025-09 | 世界模型与预测控制 | high | 精读 | — |
| 2509.20286 | [Parse-Augment-Distill: Learning Generalizable Bimanual Visuomotor Policies from Single Human Video](https://arxiv.org/abs/2509.20286) | 2025-09 | 数据引擎与人类视频学习 | high | 精读 | — |
| 2509.22643 | [VLA-Reasoner: Empowering Vision-Language-Action Models with Reasoning via Online Monte Carlo Tree Search](https://arxiv.org/abs/2509.22643) | 2025-09 | 具身基础模型与通才策略 | high | 精读 | — |
| 2509.24661 | [CEDex: Cross-Embodiment Dexterous Grasp Generation at Scale from Human-like Contact Representations](https://arxiv.org/abs/2509.24661) | 2025-09 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2510.00406 | [VLA-RFT: Vision-Language-Action Reinforcement Fine-tuning with Verified Rewards in World Simulators](https://arxiv.org/abs/2510.00406) | 2025-10 | 具身基础模型与通才策略 | high | 精读 | — |
| 2510.01623 | [VLA-R1: Enhancing Reasoning in Vision-Language-Action Models](https://arxiv.org/abs/2510.01623) | 2025-10 | 具身基础模型与通才策略 | high | 精读 | — |
| 2510.08475 | [DexMan: Learning Bimanual Dexterous Manipulation from Human and Generated Videos](https://arxiv.org/abs/2510.08475) | 2025-10 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2510.10125 | [Ctrl-World: A Controllable Generative World Model for Robot Manipulation](https://arxiv.org/abs/2510.10125) | 2025-10 | 世界模型与预测控制 | high | 精读 | — |
| 2510.10274 | [X-VLA: Soft-Prompted Transformer as Scalable Cross-Embodiment Vision-Language-Action Model](https://arxiv.org/abs/2510.10274) | 2025-10 | 策略学习与优化 | high | 精读 | — |
| 2510.18337 | [MoTVLA: A Vision-Language-Action Model with Unified Fast-Slow Reasoning](https://arxiv.org/abs/2510.18337) | 2025-10 | 具身基础模型与通才策略 | high | 精读 | — |
| 2510.21571 | [Scalable Vision-Language-Action Model Pretraining for Robotic Manipulation with Real-Life Human Activity Videos](https://arxiv.org/abs/2510.21571) | 2025-10 | 具身基础模型与通才策略 | high | 精读 | — |
| 2511.01177 | [Scaling Cross-Embodiment World Models for Dexterous Manipulation](https://arxiv.org/abs/2511.01177) | 2025-11 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2511.02504 | [Dexterous Robotic Piano Playing at Scale](https://arxiv.org/abs/2511.02504) | 2025-11 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2511.03077 | [WorldPlanner: Monte Carlo Tree Search and MPC with Action-Conditioned Visual World Models](https://arxiv.org/abs/2511.03077) | 2025-11 | 世界模型与预测控制 | high | 精读 | — |
| 2511.04671 | [X-Diffusion: Training Diffusion Policies on Cross-Embodiment Human Demonstrations](https://arxiv.org/abs/2511.04671) | 2025-11 | 策略学习与优化 | high | 精读 | — |
| 2511.14759 | [$π^{*}_{0.6}$: a VLA That Learns From Experience](https://arxiv.org/abs/2511.14759) | 2025-11 | 具身基础模型与通才策略 | high | 精读 | — |
| 2511.16651 | [InternData-A1: Pioneering High-Fidelity Synthetic Data for Pre-training Generalist Policy](https://arxiv.org/abs/2511.16651) | 2025-11 | 具身基础模型与通才策略 | high | 精读 | — |
| 2511.22134 | [DualVLA: Building a Generalizable Embodied Agent via Partial Decoupling of Reasoning and Action](https://arxiv.org/abs/2511.22134) | 2025-11 | 具身基础模型与通才策略 | high | 精读 | — |
| 2512.02729 | [RoboWheel: A Data Engine from Real-World Human Demonstrations for Cross-Embodiment Robotic Learning](https://arxiv.org/abs/2512.02729) | 2025-12 | 策略学习与优化 | high | 精读 | — |
| 2512.03044 | [Video2Act: A Dual-System Video Diffusion Policy with Robotic Spatio-Motional Modeling](https://arxiv.org/abs/2512.03044) | 2025-12 | 策略学习与优化 | high | 精读 | — |
| 2512.08186 | [Ground Slow, Move Fast: A Dual-System Foundation Model for Generalizable Vision-and-Language Navigation](https://arxiv.org/abs/2512.08186) | 2025-12 | 分层推理、规划与记忆 | high | 精读 | — |
| 2512.09297 | [One-Shot Real-World Demonstration Synthesis for Scalable Bimanual Manipulation](https://arxiv.org/abs/2512.09297) | 2025-12 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2512.13030 | [Motus: A Unified Latent Action World Model](https://arxiv.org/abs/2512.13030) | 2025-12 | 世界模型与预测控制 | high | 精读 | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html) |
| 2512.15840 | [Large Video Planner Enables Generalizable Robot Control](https://arxiv.org/abs/2512.15840) | 2025-12 | 具身基础模型与通才策略 | high | 精读 | — |
| 2512.18477 | [STORM: Search-Guided Generative World Models for Robotic Manipulation](https://arxiv.org/abs/2512.18477) | 2025-12 | 世界模型与预测控制 | high | 精读 | — |
| 2601.04629 | [UniBiDex: A Unified Teleoperation Framework for Robotic Bimanual Dexterous Manipulation](https://arxiv.org/abs/2601.04629) | 2026-01 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2601.05230 | [Learning Latent Action World Models In The Wild](https://arxiv.org/abs/2601.05230) | 2026-01 | 世界模型与预测控制 | high | 精读 | — |
| 2601.11404 | [ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://arxiv.org/abs/2601.11404) | 2026-01 | 具身基础模型与通才策略 | high | 精读 | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhong_ACoT-VLA_Action_Chain-of-Thought_for_Vision-Language-Action_Models_CVPR_2026_paper.html) |
| 2601.12993 | [Being-H0.5: Scaling Human-Centric Robot Learning for Cross-Embodiment Generalization](https://arxiv.org/abs/2601.12993) | 2026-01 | 策略学习与优化 | high | 精读 | — |
| 2601.14133 | [TwinBrainVLA: Unleashing the Potential of Generalist VLMs for Embodied Tasks via Asymmetric Mixture-of-Transformers](https://arxiv.org/abs/2601.14133) | 2026-01 | 具身基础模型与通才策略 | high | 精读 | — |
| 2601.16163 | [Cosmos Policy: Fine-Tuning Video Models for Visuomotor Control and Planning](https://arxiv.org/abs/2601.16163) | 2026-01 | 世界模型与预测控制 | high | 精读 | — |
| 2602.00919 | [Green-VLA: Staged Vision-Language-Action Model for Generalist Robots](https://arxiv.org/abs/2602.00919) | 2026-01 | 具身基础模型与通才策略 | high | 精读 | — |
| 2602.12684 | [Xiaomi-Robotics-0: An Open-Sourced Vision-Language-Action Model with Real-Time Execution](https://arxiv.org/abs/2602.12684) | 2026-02 | 具身基础模型与通才策略 | high | 精读 | — |
| 2602.13977 | [WoVR: World Models as Reliable Simulators for Post-Training VLA Policies with RL](https://arxiv.org/abs/2602.13977) | 2026-02 | 世界模型与预测控制 | high | 精读 | — |
| 2602.16710 | [EgoScale: Scaling Dexterous Manipulation with Diverse Egocentric Human Data](https://arxiv.org/abs/2602.16710) | 2026-02 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2602.21633 | [Self-Correcting VLA: Online Action Refinement via Sparse World Imagination](https://arxiv.org/abs/2602.21633) | 2026-02 | 具身基础模型与通才策略 | high | 精读 | — |
| 2602.21736 | [Joint-Aligned Latent Action: Towards Scalable VLA Pretraining in the Wild](https://arxiv.org/abs/2602.21736) | 2026-02 | 世界模型与预测控制 | high | 精读 | — |
| 2602.23648 | [FAVLA: A Force-Adaptive Fast-Slow VLA model for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2602.23648) | 2026-02 | 具身基础模型与通才策略 | high | 精读 | — |
| 2602.23721 | [StemVLA:An Open-Source Vision-Language-Action Model with Future 3D Spatial Geometry Knowledge and 4D Historical Representation](https://arxiv.org/abs/2602.23721) | 2026-02 | 具身基础模型与通才策略 | high | 精读 | — |
| 2603.16860 | [DreamPlan: Efficient Reinforcement Fine-Tuning of Vision-Language Planners via Video World Models](https://arxiv.org/abs/2603.16860) | 2026-03 | 世界模型与预测控制 | high | 精读 | — |
| 2603.17808 | [EVA: Aligning Video World Models with Executable Robot Actions via Inverse Dynamics Rewards](https://arxiv.org/abs/2603.17808) | 2026-03 | 世界模型与预测控制 | high | 精读 | — |
| 2603.19201 | [OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2603.19201) | 2026-03 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2603.22263 | [DexDrummer: In-Hand, Contact-Rich, and Long-Horizon Dexterous Robot Drumming](https://arxiv.org/abs/2603.22263) | 2026-03 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2603.22264 | [UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://arxiv.org/abs/2603.22264) | 2026-03 | 数据引擎与人类视频学习 | high | 精读 | [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html) |
| 2603.28545 | [ManipArena: Comprehensive Real-world Evaluation of Reasoning-Oriented Generalist Robot Manipulation](https://arxiv.org/abs/2603.28545) | 2026-03 | 具身基础模型与通才策略 | high | 精读 | — |
| 2603.29844 | [DIAL: Decoupling Intent and Action via Latent World Modeling for End-to-End VLA](https://arxiv.org/abs/2603.29844) | 2026-03 | 世界模型与预测控制 | high | 精读 | — |
| 2604.13015 | [Learning Versatile Humanoid Manipulation with Touch Dreaming](https://arxiv.org/abs/2604.13015) | 2026-04 | 人形、运动与全身控制 | high | 精读 | — |
| 2604.15483 | [$π_{0.7}$: a Steerable Generalist Robotic Foundation Model with Emergent Capabilities](https://arxiv.org/abs/2604.15483) | 2026-04 | 具身基础模型与通才策略 | high | 精读 | — |
| 2604.20689 | [FingerEye: Learning Dexterous Manipulation with Continuous Vision-Tactile Sensing](https://arxiv.org/abs/2604.20689) | 2026-04 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2604.21017 | [Open-H-Embodiment: A Large-Scale Dataset for Enabling Foundation Models in Medical Robotics](https://arxiv.org/abs/2604.21017) | 2026-04 | 具身基础模型与通才策略 | high | 精读 | — |
| 2604.21924 | [Long-Horizon Manipulation via Trace-Conditioned VLA Planning](https://arxiv.org/abs/2604.21924) | 2026-04 | 具身基础模型与通才策略 | high | 精读 | — |
| 2604.24921 | [Libra-VLA: Achieving Learning Equilibrium via Asynchronous Coarse-to-Fine Dual-System](https://arxiv.org/abs/2604.24921) | 2026-04 | 具身基础模型与通才策略 | high | 精读 | — |
| 2604.26848 | [STARRY: Spatial-Temporal Action-Centric World Modeling for Robotic Manipulation](https://arxiv.org/abs/2604.26848) | 2026-04 | 世界模型与预测控制 | high | 精读 | — |
| 2605.27817 | [Turning Video Models into Generalist Robot Policies](https://arxiv.org/abs/2605.27817) | 2026-05 | 具身基础模型与通才策略 | high | 精读 | — |
| 2605.30226 | [BORA: Bridging Offline Reinforcement Learning and Online Residual Adaptation for Real-World Dexterous VLA Models](https://arxiv.org/abs/2605.30226) | 2026-05 | 策略学习与优化 | high | 精读 | — |
| 2605.30280 | [Qwen-VLA: Unifying Vision-Language-Action Modeling across Tasks, Environments, and Robot Embodiments](https://arxiv.org/abs/2605.30280) | 2026-05 | 具身基础模型与通才策略 | high | 精读 | — |
| 2605.31286 | [DeMaVLA: A Vision-Language-Action Foundation Model for Generalizable Deformable Manipulation](https://arxiv.org/abs/2605.31286) | 2026-05 | 具身基础模型与通才策略 | high | 精读 | — |
| 2606.00229 | [Continuous Reasoning for Vision-Language-Action](https://arxiv.org/abs/2606.00229) | 2026-05 | 具身基础模型与通才策略 | high | 精读 | — |
| 2606.01027 | [$τ_0$-WM: A Unified Video-Action World Model for Robotic Manipulation](https://arxiv.org/abs/2606.01027) | 2026-05 | 世界模型与预测控制 | high | 精读 | — |
| 2606.01241 | [OneVLA: A Unified Framework for Embodied Tasks](https://arxiv.org/abs/2606.01241) | 2026-05 | 具身基础模型与通才策略 | high | 精读 | — |
| 2606.27375 | [Scalable Behavior Cloning with Open Data, Training, and Evaluation](https://arxiv.org/abs/2606.27375) | 2026-06 | 策略学习与优化 | high | 精读 | — |
| 2606.30552 | [Training Vision-Language-Action Models with Dense Embodied Chain-of-Thought Supervision](https://arxiv.org/abs/2606.30552) | 2026-06 | 分层推理、规划与记忆 | high | 精读 | — |
| 2606.31329 | [3D HAMSTER: Bridging Planning and Control in Hierarchical Vision Language Action Models through 3D Trajectory Guidance](https://arxiv.org/abs/2606.31329) | 2026-06 | 具身基础模型与通才策略 | high | 精读 | — |
| 2606.31723 | [UniTacVLA: Unified Tactile Understanding and Prediction in Vision Language Action Models](https://arxiv.org/abs/2606.31723) | 2026-06 | 具身基础模型与通才策略 | high | 精读 | — |
| 2606.31909 | [CoDex: Learning Compositional Dexterous Functional Manipulation without Demonstrations](https://arxiv.org/abs/2606.31909) | 2026-06 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2606.32009 | [Human-as-Humanoid: Enabling Zero-Shot Humanoid Learning from Ego-Exo Human Videos with Human-Aligned Embodiments](https://arxiv.org/abs/2606.32009) | 2026-06 | 数据引擎与人类视频学习 | high | 精读 | — |
| 2606.32028 | [DVG-WM: Disentangled Video Generation Enables Efficient Embodied World Model for Robotic Manipulation](https://arxiv.org/abs/2606.32028) | 2026-06 | 世界模型与预测控制 | high | 精读 | — |
| 2607.01212 | [FurnitureVLA: Learning Long-Horizon Bimanual Furniture Assembly with Vision-Language-Action Model](https://arxiv.org/abs/2607.01212) | 2026-07 | 具身基础模型与通才策略 | high | 精读 | — |
| 2607.01804 | [VLA-Corrector: Lightweight Detect-and-Correct Inference for Adaptive Action Horizon](https://arxiv.org/abs/2607.01804) | 2026-07 | 具身基础模型与通才策略 | high | 精读 | — |
| 2607.02604 | [DynaWM: A Base-VLA-Guided World Foundation Model for Moving-Object Manipulation](https://arxiv.org/abs/2607.02604) | 2026-07 | 具身基础模型与通才策略 | high | 精读 | — |
| 2607.03449 | [HiMe: Hierarchical Embodied Memory for Long-Horizon Vision-Language-Action Control](https://arxiv.org/abs/2607.03449) | 2026-07 | 具身基础模型与通才策略 | high | 精读 | — |
| 2607.15330 | [Xiaomi-Robotics-1: Scaling Vision-Language-Action Models with over 100K Hours of Real-World Trajectories](https://arxiv.org/abs/2607.15330) | 2026-07 | 具身基础模型与通才策略 | high | 精读 | — |
| 2607.16636 | [PhyAgentOS: A Self-Evolving Operating System for Embodied Agents with Decoupled Cognitive Planning and Physical Execution](https://arxiv.org/abs/2607.16636) | 2026-07 | 具身基础模型与通才策略 | high | 精读 | — |
| 2607.22530 | [ViTacWorld: Scaling Visuo-Tactile World Models for Contact-Rich Robot Manipulation](https://arxiv.org/abs/2607.22530) | 2026-07 | 世界模型与预测控制 | high | 精读 | — |
| 2607.24485 | [τ: Learning Touch-Augmented Vision-Language-Action Models from Future Visual Supervision](https://arxiv.org/abs/2607.24485) | 2026-07 | 具身基础模型与通才策略 | high | 精读 | — |
| 2607.24744 | [Data Pyramid for Embodied Manipulation](https://arxiv.org/abs/2607.24744) | 2026-07 | 策略学习与优化 | high | 精读 | — |
| 2607.25918 | [DC-WAM: Dynamic-Centric Visual Supervision and Reasoning for World-Action Models](https://arxiv.org/abs/2607.25918) | 2026-07 | 世界模型与预测控制 | high | 精读 | — |
| 2607.27549 | [Cross-Embodiment Transfer via Behavior-Aligned Representations](https://arxiv.org/abs/2607.27549) | 2026-07 | 策略学习与优化 | high | 精读 | — |
| 2607.27599 | [World Action Planner: Generalizable Decision-Making with Action-Conditioned World Models](https://arxiv.org/abs/2607.27599) | 2026-07 | 世界模型与预测控制 | high | 精读 | — |
| 2607.27782 | [RedFlow: Redirect Failure into Action-Level Corrections for Flow-matching VLA Policy](https://arxiv.org/abs/2607.27782) | 2026-07 | 策略学习与优化 | high | 精读 | — |
| 2607.28391 | [TacWAM: Anchor-Guided World Action Model with Mechanics-Aware Tactile Prediction](https://arxiv.org/abs/2607.28391) | 2026-07 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2607.28596 | [FA-RDP: A Frequency-Adaptive Reactive Diffusion Policy for Contact-Rich Manipulation](https://arxiv.org/abs/2607.28596) | 2026-07 | 灵巧、双臂与接触操作 | high | 精读 | — |
| 2607.28625 | [ACE-Data-0: Human-Centric Ambient Capture as Embodied Data Engine](https://arxiv.org/abs/2607.28625) | 2026-07 | 数据引擎与人类视频学习 | high | 精读 | — |
| 2607.29172 | [CLIFT: Turning Gemini Robotics On-Device into Humanoid Specialists via Non-Invasive Closed-Loop Iterative Fine-Tuning](https://arxiv.org/abs/2607.29172) | 2026-07 | 人形、运动与全身控制 | high | 精读 | — |
| 2607.29302 | [BWM: A Low-Cost High-Fidelity World Simulator for Robot Learning](https://arxiv.org/abs/2607.29302) | 2026-07 | 策略学习与优化 | high | 精读 | — |
| 2607.29569 | [Safe Vision Language Action Models via Barrier Enhanced Flow Matching](https://arxiv.org/abs/2607.29569) | 2026-07 | 具身基础模型与通才策略 | high | 精读 | — |
| 2607.29613 | [WCM: A World Critic Model for Vision-Language-Action Reinforcement Learning](https://arxiv.org/abs/2607.29613) | 2026-07 | 具身基础模型与通才策略 | high | 精读 | — |

---


## 检索、分类与趋势判定方法

> **数据截点**：2026 年 8 月 24 日（Asia/Shanghai）<br>
> 本页描述当前可复算流程；任何依赖人工判断的步骤都会明确标注。

::: tip 统一方向体系
月度结构、方向页和首页可视化统一使用 15 个研究方向。精读样本只补充实验与趋势证据，不再形成另一套方向统计。详见[语料扩充协议](/methods/expansion-protocol)与[覆盖审计](/analysis/corpus-expansion)。
:::

### 时间口径

| 层级 | 时间范围 | 用途 | 深度 |
|---|---|---|---|
| 主分析期 | 2025-07-01—2026-06-30 | 逐月趋势、重点论文、实验与开放性指标 | 精读 + 完整分类 |
| 完整月更新 | 2026-07-01—2026-07-31 | 完整趋势研判 + 早期信号 | 完整月环比/同比 |
| 前瞻快照 | 2026-08-01—2026-08-04 | 月初增量与验证路标 | 尚无 v1 时不计算误导性环比 |
| 同比基线 | 2024-07-01—2025-06-30 | 数量、主题、机构结构 | 轻量分类 |
| 同行评审窗口 | 2024-07-01—2026-08-04 | 处理提出、投稿、录用与发表之间的滞后 | 官方证据核验 |

月份统一由 [arXiv](https://arxiv.org/) 首次提交版本 `v1` 的日期确定。修订版本更新摘要、DOI 与发表信息，但不重复计数。会议发表月只表示评审完成，并不替代研究首次公开时间。

### 三阶段检索

```mermaid
flowchart LR
  A["宽召回<br/>cs.RO 为核心<br/>补 cs.AI/CV/LG<br/> "] --> B["语义边界筛选<br/>标题 + 摘要 + 方法语境<br/> "]
  B --> C["人工复核<br/>低置信度 / 跨方向 / 高影响<br/> "]
  C --> D["版本合并<br/>arXiv + proceedings + journal<br/> "]
  D --> E["结构化证据库<br/>CSV / JSON 单一来源<br/> "]
```

宽召回优先保证“不漏掉使用新命名的工作”。当前语料完整拉取窗口内 `cs.RO` 24,119 条，并补充 `cs.AI`、`cs.CV`、`cs.LG` 中 7,654 条机器人/具身交叉记录，合并去重后形成 31,773 条 arXiv 母集。正式发表管线独立采集 ICRA、IROS、RSS、CoRL、RA-L、T-RO、IJRR 与 Science Robotics，共 12,165 条版本记录、窗口内 10,404 条；母集保留窗口前的 ICRA 2024 以支持版本合并。Semantic Scholar 只用于摘要、arXiv 映射和引用快照补全，不覆盖会议年份或出版社日期，也不再作为唯一发现入口。

104 篇高信号样本继续作为精读层，逐条核对 ID、标题、`published`（v1）、摘要、实验和开放资产。分类规则只负责生成候选和初步分数；是否纳入高信号论文、是否构成趋势，以及跨方向归类均需结合摘要和方法描述复核。

### 当前研究方向

当前共有 15 类：具身基础模型、推理与规划、世界模型、灵巧操作、人形与全身控制、导航与移动操作、人机交互、策略学习、数据引擎、仿真与迁移、空间感知、安全与评测、持续/部署学习、多机器人协同、具身多感官。完整边界与代表工作见[研究方向总览](/frontiers/)。

一篇论文可以拥有多个关联方向，但只有一个主方向。全站的数量、占比和环比只按主方向计数，防止重复加总；桑基图使用多标签共现，明确不代表论文在方向之间迁移。

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
| 环比 / 同比 | 同时展示与上月 / 上年同月的绝对增量和百分比 | 7 月为完整月；8 月无 v1 时保留 7 月参照数、不计算 −100% |
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

- 分类配置固化 15 个主方向、排除词与回归规则；来源注册表固化 venue、官方容器和发现源边界。
- `data/papers.json` 保存精选精读与人工趋势证据。
- `data/preprints.json`、`data/publications.json`、`data/official-proceedings.json`、`data/official-programs.json` 与 `data/repositories.json` 是各证据层的数据源。
- `data/works.json` 是跨版本去重后的 canonical work graph；发表日期绝不覆盖 arXiv `v1` 的首次公开日期。
- `data/trends.json` 记录人工趋势判断及其论文 ID。
- 生成脚本统一派生月度统计、母库页面、发表索引、方向页、首页图表和 GitHub 页面。
- 审计脚本检查重复 ID、日期范围、官方容器对账、趋势证据、公开下载文件哈希与数字一致性。

生成页面不是数据源，不应手工修改其中的数量。修正应先进入结构化文件，再重新生成。

---


## 语料扩充协议

> 数据截点：2026-08-04。本协议解决的不是“再补几个关键词”，而是让 arXiv、正式发表和开源生态各自拥有完整、可追溯的母集。

### 一、目标与完成定义

语料扩充完成必须同时满足四件事：

1. arXiv 层能够证明每个月的完整页数与唯一 ID 数，而不是只展示检索命中的第一页。
2. 正式发表层允许没有 arXiv ID 的工作存在，并把发现来源、官方录用、正式 proceedings 和期刊发表分开。
3. GitHub 层能够回答“是否真的开放、是否持续维护、是否有独立参与”，而不只展示 stars。
4. 分类层可复现重跑；新增方向不能被固定 schema 阻挡，也不能因改词表而改写历史事实。

### 二、四层漏斗

```mermaid
flowchart LR
  A["母集<br/>完整 cs.RO / venue container"] --> B["宽召回<br/>15 方向 + 边界词"]
  B --> C["语义纳排<br/>included / candidate / review / excluded"]
  C --> D["canonical work<br/>arXiv + DOI + 标题作者去重"]
  D --> E["精读与趋势证据<br/>月度 Top / A–D 等级"]
```

| 层级 | 是否允许自动化 | 能否直接支持趋势结论 |
|---|---:|---:|
| 母集 | 是 | 否，只提供分母 |
| 自动相关候选 | 是 | 否，只提供筛选队列 |
| canonical work 与官方状态 | 自动合并 + 边界人工复核 | 可支持数量和发表覆盖 |
| 精读证据 | 必须人工核验 | 是 |

### 三、arXiv 采集

#### 3.1 母集边界

- 核心：2024-07-01 至 2026-08-04 的 `cs.RO` 月度全量。
- 补充：`cs.AI`、`cs.CV`、`cs.LG` 中包含 robot、robotic、manipulation、locomotion、humanoid、grasping、embodied intelligence、VLA、teleoperation、bimanual 等动作语境的论文。
- 月份：Atom `<published>`，即 v1 日期；修订和正式发表都不能改变首次公开月。

审计时对每月 count-only 请求复算，`cs.RO` 共 23,336 条；每条母集记录都保留 arXiv categories，确保月份与分类可以复算。

#### 3.2 分页与缓存

- 日期范围固定使用 14 位秒级边界：`YYYYMMDD000000` 至 `YYYYMMDD235959`。
- 每页 500 条，读取 `opensearch:totalResults` 后遍历全部 offset。
- 每个“月份 × 查询 × offset”保存独立 XML；历史完整页冻结，当前月按 cutoff 建新快照。
- 请求串行、间隔至少 3.1 秒；429/503、EOF、timeout 分开重试。
- 验收要求：每月唯一 ID 数等于 API 总数；页内日期全部落在冻结区间。

#### 3.3 为什么不用 Semantic Scholar 作为母集

Semantic Scholar 用于补摘要、引用和外部 ID，不决定语料边界。旧脚本没有消费 bulk search 的后续 token；现存 2026 foundation 缓存就明确少了至少 206 条。OpenAlex 同样只作机构与落地页补源。

### 四、正式发表采集

#### 4.1 三种状态不能混用

| 状态 | 严格同行评审分子 | 示例 |
|---|---:|---|
| `peer_reviewed_official_proceedings` | 是 | RSS/CoRL 官方完整卷 |
| `official_publisher_page_verified` | 是 | IEEE、SAGE、Science 单篇出版社页面核验 |
| `official_accepted_pending_proceedings` | 否 | RSS 2026 accepted list |
| `official_program_only` | 否 | ICRA 2026 PaperCept program |
| `publisher_url_from_registered_doi` | 否，待核验 | DBLP/Crossref 发现 DOI 后构造的出版社链接 |
| `discovery_only` | 否 | DBLP、Crossref、OpenAlex、Semantic Scholar |

#### 4.2 采集顺序

1. **静态官方容器**：RSS 2024/2025、CoRL 2024/2025，先验证整卷条目数。
2. **机器人会议母集**：ICRA、IROS 用 DBLP/DOI 做完整发现；有 IEEE API key 时回到 Xplore 批量核验。
3. **机器人期刊母集**：RA-L、T-RO、IJRR、Science Robotics 按精确 ISSN 与日期拉取，再回出版社页面核验。
4. **官方 program / pending**：ICRA 2026、RSS 2026 进入候选队列，但不进入严格覆盖率。
5. **跨领域 venue**：ICLR、ICML、NeurIPS、CVPR、ICCV、ECCV 只纳入与机器人动作、执行或交互直接相关的工作。

#### 4.3 当前完整容器

| 容器 | 官方条目 | 验收 |
|---|---:|---|
| RSS 2024 | 134 | 与官方索引完全一致 |
| RSS 2025 | 163 | 与官方索引完全一致 |
| CoRL 2024 / PMLR v270 | 264 | 与官方卷完全一致 |
| CoRL 2025 / PMLR v305 | 263 | 与官方卷完全一致 |

这 824 条全部保留；标题初筛没有命中的论文也进入 `manual_review`，不会因旧词表缺失而丢失。

### 五、GitHub 证据

#### 5.1 发现入口

- 论文、项目页和 README 中的 GitHub URL。
- GitHub topic/search：robot-learning、vision-language-action、dexterous-manipulation、robotics-dataset、world model、teleoperation。
- Awesome 列表与研究机构 organization 页面只负责发现；最终必须由 GitHub repo API 解析 canonical `owner/repo`。

#### 5.2 独立采用代理

IAS-GH（0–100）不使用 stars，分项为：

- 近 12 个月外部 PR 作者；
- 外部 issue 作者；
- 贡献者广度与头部贡献集中度；
- 近 100 个 PR 的合并数；
- forks；
- release 新鲜度。

stars 仍展示为传播元数据。GitHub 通用 API 没有稳定的反向依赖总数，因此缺失保持 `null`，绝不用 forks 冒充 dependents。真正的研究采用还要补第三方代码使用、包依赖、独立复现或 benchmark 渗透。

当月新论文发现的仓库先进入 `data/github-watchlist.json`：只刷新 canonical URL、stars/forks、license 和推送时间，状态固定为 `new_repo_pending_adoption_audit`。只有完成与旧仓相同的 issue/PR 外部作者、贡献者和依赖审计后，才能进入 IAS-GH 排名，避免新仓因 stars 或作者自身活跃被误读为独立采用。

### 六、canonical work 与去重

主键优先级：

1. `arxiv:{id}`；
2. `doi:{normalized-doi}`；
3. `title:{normalized-title + first-author + year hash}`。

合并优先级：

1. 同 arXiv ID；
2. 同 DOI / IEEE article number；
3. 标准化标题完全一致；
4. 标题相似度与作者重合只生成复核对，不自动合并。

特殊规则：

- RA-L 在 ICRA/IROS 展示只记一个 work；会议只写 `presented_at`。
- Early Access 与正式卷页按 DOI 合并，保留两个日期。
- CoRL event year、PMLR publish date 和 BibTeX year分别保存。
- 会议扩展期刊若有实质新方法/实验，可作为 related work 分开，但不能算独立团队验证。

### 七、15 个方向与多轴标签

当前主方向包括：

1. 具身基础模型与通才策略；
2. 分层推理、规划与记忆；
3. 世界模型与预测控制；
4. 灵巧、双臂与接触操作；
5. 人形、运动与全身控制；
6. 导航与移动操作；
7. 人机协作与交互学习；
8. 策略学习与优化；
9. 数据引擎与人类视频学习；
10. 仿真、合成数据与 Sim-to-Real；
11. 动作关联的空间感知与表征；
12. 评测、安全、可靠性与故障恢复；
13. 持续学习、部署学习与自改进；
14. 多机器人协同与群体智能；
15. 触觉、力觉与多模态身体感知。

每篇只有一个主方向，但可以有多个 secondary topics、能力标签、基础设施标签和成熟度标签。新方向正式进入趋势主页前，至少准备 15 条正例、10 条边界例和 10 条反例，并检查跨月连续性与独立团队数。

### 八、数量与质量验收

#### 8.1 arXiv

- 月度 `unique_arxiv_ids == totalResults`。
- 99% 以上记录保留原始 categories。
- 随机抽查 100 条未纳入记录，假阴性率低于 5%。

#### 8.2 正式发表

- 目标 venue-year/volume 100% 有 manifest 或明确 pending reason。
- 静态官方容器条目数与官方索引完全一致。
- 严格发表标签 100% 有官方页；作者自述 accepted 不计。
- DOI、OpenReview forum、RA-L 转投展示的残余重复为 0。

#### 8.3 GitHub

- repo URL 100% 经 API 解析；
- watchers 取 subscribers/watchers，而不是与 stars 同值的 `watchers_count`；
- code/data/model 三种状态分开，`will release` 不计已开放；
- 许可证缺失单独作为风险，不默认视为可用。

#### 8.4 趋势

- A/B 级证据门槛不因语料量增加而下降。
- 所有百分比同时显示绝对分子与分母。
- taxonomy 变更前后输出混淆矩阵，不能把分类迁移误判为技术升温。

### 九、月度更新协议

1. 冻结当月 cutoff，补齐 arXiv 页面并验证 manifest。
2. 增量拉 venue、DOI、OpenReview 与 GitHub 快照。
3. 运行 canonical 合并与分类回归。
4. 先更新母集漏斗，再选 10–15 篇精读。
5. 检查弱信号的验证路标与反证，而不是每月重写预测。
6. 发布结构化数据、生成页面、运行链接与构建审计，最后通过 GitHub 部署。

---


## 纳入、排除与研究局限

### 纳入规则

候选必须同时满足：

- 研究对象位于机器人或具身交互边界内；
- 方法直接学习、生成、规划或执行动作，或为这些能力提供数据与动力学模型；
- 标题、摘要或正式方法说明能支持至少一个主方向；
- 首次公开时间落入分析、基线、7 月完整月或 8 月前瞻窗口。

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
6. **百分比受小样本和不完整窗口影响。** 所有图表保留绝对数量；2026 年 7 月已是完整月，8 月月初若尚无 v1，明确标记不可比而不计算 −100%。
7. **一句话贡献与局限是研究判断。** 它们不是作者原文，站点将其与可核验事实分开表述。
8. **轻量统计是统一查询的候选指数。** 当前批量 arXiv Atom 接口触发限流后，宽召回改用 Semantic Scholar 的 arXiv external ID 索引；因此候选数量适合做同口径环比/同比，不应解释为 cs.RO 的完整论文总量。

### 不在本期范围

市场规模、公司融资、商业订单、供应链和公司级尽调不在本期范围。本报告只提供研究证据，可作为后续商业模块的技术底座。

---


## 研究问题层方法

### 为什么不改 D1–D15

D1–D15 是每篇工作唯一主分类，用于稳定月度曲线。问题层是多标签镜头：触觉、失败数据、软硬件共设计和主动感知天然跨越多个主方向。如果直接改主分类或分类顺序，会把历史曲线变化与真实研究变化混在一起。

### 自动层

- 数据源：已纳入的 arXiv 母库记录。
- 日期：首次提交 v1。
- 匹配：标题与摘要对公开词表做不区分大小写的子串匹配。
- 输出：`data/research-question-evidence.json`，记录论文命中的 Q 与具体词项。
- 限制：高召回计数只能表示相关工作密度，不能证明研究命题成立。

### 人工判断层

| 等级 | 使用条件 |
|---|---|
| A | 多团队或严格同行评审已确认路线，但不代表具体科学问题完全解决 |
| B | 过去 12 个月出现多个独立研究簇，仍缺统一评测、跨平台复现或成本对照 |
| C | 高价值早期假设，证据主要来自少量预印本、系统原型或内部经验 |
| D | 反证增加、缺少独立跟进，或结果只剩命名和单一 demo |

P0/P1/P2 只表示战略依赖顺序，与 A/B/C/D 外部证据等级相互独立。

### 升级与降级

- 升级优先看真机、独立团队、正式发表、跨硬件复现和决定性指标。
- 只有关键词数量增加而没有新能力，不升级。
- 反证条件被触发、连续两个季度没有独立跟进或成本不可接受时降级。
- 安全、评测和软硬件变量可以成为关键门槛，但不会仅因“论文少”被误写成弱方向。

---


## 研究组归属与周度监测方法

### 四层实体与证据

- 母机构只做向上聚合，不代表具体研究路线。
- 研究院/事业部、实验室/PI 组和独立研究公司可以成为跟踪单元。
- 论文合作组不是持久 organization。
- G1 为官方研究组/论文直接证据；G2 为带时间的成员关系重建；G3/G0 不进入正式动态。

### 每周窗口

周一北京时间 04:00 运行，冻结上周一 00:00 至周日 23:59。原始时间保存为 UTC，页面以 Asia/Shanghai 展示。不完整当周不进入周报。

### 不做跨组排名

页面只展示每组的时间线、方向变化、证据类型、开放资产、真机与合作关系。论文数量、Demo 和部署规模不压缩为一个不可比较的总分。

### 自动化边界

官方 publications/projects 页面可生成 G1 候选；当前 roster、GitHub owner、招聘页和域名只能生成 G3 观察。来源失败不会删除既有记录；连续两周失败显示 stale warning。

---


## 参考文献

> 收录月度精读、趋势卡、未来判断与同行评审页实际引用的唯一工作；官方发表版本优先链接正式页面。

### D1 · 具身基础模型与通才策略

1. Lirui Wang, Xinlei Chen, Jialiang Zhao, Kaiming He. (2024). [Scaling Proprioceptive-Visual Learning with Heterogeneous Pre-trained Transformers](https://papers.nips.cc/paper_files/paper/2024/hash/e0f393e7980a24fd12fa6f15adfa25fb-Abstract-Conference.html). *NeurIPS 2024*.
2. Kevin Black, Noah Brown, Danny Driess, A. Esmail, Michael Equi, Chelsea Finn, Niccolo Fusai, Lachy Groom, et al.. (2024). [π0: A Vision-Language-Action Flow Model for General Robot Control](https://www.roboticsproceedings.org/rss21/p010.html). *RSS 2025*.
3. Karl Pertsch, Kyle Stachowicz, Brian Ichter, Danny Driess, Suraj Nair, Quan Vuong, Oier Mees, Chelsea Finn, et al.. (2025). [FAST: Efficient Action Tokenization for Vision-Language-Action Models](https://www.roboticsproceedings.org/rss21/p012.html). *RSS 2025*.
4. Delin Qu, Haoming Song, Qizhi Chen, Yuanqi Yao, Xinyi Ye, Yani Ding, Zhigang Wang, Jiayuan Gu, et al.. (2025). [SpatialVLA: Exploring Spatial Representations for Visual-Language-Action Model](https://www.roboticsproceedings.org/rss21/p011.html). *RSS 2025*.
5. Yuhui Chen, Shuai Tian, Shugao Liu, Yingting Zhou, Haoran Li, Dongbin Zhao. (2025). [ConRFT: A Reinforced Fine-tuning Method for VLA Models via Consistency Policy](https://www.roboticsproceedings.org/rss21/p019.html). *RSS 2025*.
6. Physical Intelligence, Kevin Black, Noah Brown, James Darpinian, Karan Dhabalia, Danny Driess, A. Esmail, Michael Equi, et al.. (2025). [π0.5: a Vision-Language-Action Model with Open-World Generalization](https://proceedings.mlr.press/v305/black25a.html). *CoRL 2025*.
7. Qingwen Bu, Yanting Yang, Jisong Cai, Shenyuan Gao, Guanghui Ren, Maoqing Yao, Ping Luo, Hongyang Li. (2025). [UniVLA: Learning to Act Anywhere with Task-centric Latent Actions](https://www.roboticsproceedings.org/rss21/p014.html). *RSS 2025*.
8. Tao Lin, Gen Li, Yilei Zhong, Yanwen Zou, Yuxin Du, Jiting Liu, Encheng Gu, Bo Zhao. (2025). [Evo-0: Vision-Language-Action Model with Implicit Spatial Understanding](https://arxiv.org/abs/2507.00416). arXiv:2507.00416.
9. Zhenyang Liu, Yongchong Gu, Sixiao Zheng, Yanwei Fu, Xiangyang Xue, Yu-Gang Jiang. (2025). [TriVLA: A Triple-System-Based Unified Vision-Language-Action Model with Episodic World Modeling for General Robot Control](https://arxiv.org/abs/2507.01424). arXiv:2507.01424.
10. Chilam Cheang, Sijin Chen, Zhongren Cui, Yingdong Hu, Liqun Huang, Tao Kong, Hang Li, Yifeng Li, et al.. (2025). [GR-3 Technical Report](https://arxiv.org/abs/2507.15493). arXiv:2507.15493.
11. Kaustubh Sridhar, Souradeep Dutta, Dinesh Jayaraman, Insup Lee. (2025). [RICL: Adding In-Context Adaptability to Pre-Trained Vision-Language-Action Models](https://arxiv.org/abs/2508.02062). arXiv:2508.02062.
12. Yiguo Fan, Pengxiang Ding, Shuanghao Bai, Xinyang Tong, Yuyang Zhu, Hongchao Lu, Fengqi Dai, Wei Zhao, et al.. (2025). [Long-VLA: Unleashing Long-Horizon Capability of Vision Language Action Model for Robot Manipulation](https://proceedings.mlr.press/v305/fan25a.html). *CoRL 2025*.
13. Delin Qu, Haoming Song, Qizhi Chen, Zhaoqing Chen, Xianqiang Gao, Dong Wang, Xinyi Ye, Qi Lv, et al.. (2025). [EO-1: An Open Unified Embodied Foundation Model for General Robot Control](https://arxiv.org/abs/2508.21112). arXiv:2508.21112.
14. Moritz Reuss, Hongyi Zhou, Marcel Rühle, Ömer Erdinç Yagmurlu, Fabian Otto, Rudolf Lioutikov. (2025). [FLOWER: Democratizing Generalist Robot Policies with Efficient Vision-Language-Action Flow Policies](https://arxiv.org/abs/2509.04996). arXiv:2509.04996.
15. Wenkai Guo, Guanxing Lu, Haoyuan Deng, Zhenyu Wu, Yansong Tang, Ziwei Wang. (2025). [VLA-Reasoner: Empowering Vision-Language-Action Models with Reasoning via Online Monte Carlo Tree Search](https://arxiv.org/abs/2509.22643). arXiv:2509.22643.
16. Hengtao Li, Pengxiang Ding, Runze Suo, Yihao Wang, Zirui Ge, Dongyuan Zang, Kexian Yu, Mingyang Sun, et al.. (2025). [VLA-RFT: Vision-Language-Action Reinforcement Fine-tuning with Verified Rewards in World Simulators](https://arxiv.org/abs/2510.00406). arXiv:2510.00406.
17. Angen Ye, Zeyu Zhang, Boyuan Wang, Xiaofeng Wang, Dapeng Zhang, Zheng Zhu. (2025). [VLA-R1: Enhancing Reasoning in Vision-Language-Action Models](https://arxiv.org/abs/2510.01623). arXiv:2510.01623.
18. Wenhui Huang, Changhe Chen, Han Qi, Chen Lv, Yilun Du, Heng Yang. (2025). [MoTVLA: A Vision-Language-Action Model with Unified Fast-Slow Reasoning](https://arxiv.org/abs/2510.18337). arXiv:2510.18337.
19. Qixiu Li, Yu Deng, Yaobo Liang, Lin Luo, Lei Zhou, Chengtang Yao, Lingqi Zeng, Zhiyuan Feng, et al.. (2025). [Scalable Vision-Language-Action Model Pretraining for Robotic Manipulation with Real-Life Human Activity Videos](https://arxiv.org/abs/2510.21571). arXiv:2510.21571.
20. Physical Intelligence, Ali Amin, Raichelle Aniceto, Ashwin Balakrishna, Kevin Black, Ken Conley, Grace Connors, James Darpinian, et al.. (2025). [$π^{*}_{0.6}$: a VLA That Learns From Experience](https://arxiv.org/abs/2511.14759). arXiv:2511.14759.
21. Yang Tian, Yuyin Yang, Yiman Xie, Zetao Cai, Xu Shi, Ning Gao, Hangxu Liu, Xuekun Jiang, et al.. (2025). [InternData-A1: Pioneering High-Fidelity Synthetic Data for Pre-training Generalist Policy](https://arxiv.org/abs/2511.16651). arXiv:2511.16651.
22. Zhen Fang, Zhuoyang Liu, Jiaming Liu, Hao Chen, Yu Zeng, Shiting Huang, Zehui Chen, Lin Chen, et al.. (2025). [DualVLA: Building a Generalizable Embodied Agent via Partial Decoupling of Reasoning and Action](https://arxiv.org/abs/2511.22134). arXiv:2511.22134.
23. Haowen Liu, Shaoxiong Yao, Haonan Chen, Jiawei Gao, Jiayuan Mao, Jia-Bin Huang, Yilun Du. (2025). [SIMPACT: Simulation-Enabled Action Planning using Vision-Language Models](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_SIMPACT_Simulation-Enabled_Action_Planning_using_Vision-Language_Models_CVPR_2026_paper.html). *CVPR 2026*.
24. Boyuan Chen, Tianyuan Zhang, Haoran Geng, Caiyi Zhang, Peihao Li, Kiwhan Song, William T. Freeman, Jitendra Malik, et al.. (2025). [Large Video Planner Enables Generalizable Robot Control](https://arxiv.org/abs/2512.15840). arXiv:2512.15840.
25. Huajie Tan, P. Co, Yijie Xu, Shanyu Rong, Yuheng Ji, Cheng Chi, Xiansheng Chen, Qiongyue Zhang, et al.. (2026). [Action-Sketcher: From Reasoning to Action via Visual Sketches for Long-Horizon Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Tan_Action-Sketcher_From_Reasoning_to_Action_via_Visual_Sketches_for_Robotic_CVPR_2026_paper.html). *CVPR 2026*.
26. Zhenyang Liu, Yongchong Gu, Yikai Wang, Xiangyang Xue, Yanwei Fu. (2026). [ActiveVLA: Injecting Active Perception into Vision-Language-Action Models for Precise 3D Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_ActiveVLA_Injecting_Active_Perception_into_Vision-Language-Action_Models_for_Precise_3D_CVPR_2026_paper.html). *CVPR 2026*.
27. Linqing Zhong, Yi Liu, Yifei Wei, Ziyu Xiong, Maoqing Yao, Si Liu, Guanghui Ren. (2026). [ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Zhong_ACoT-VLA_Action_Chain-of-Thought_for_Vision-Language-Action_Models_CVPR_2026_paper.html). *CVPR 2026*.
28. Bin Yu, Shijie Lian, Xiaopeng Lin, Yuliang Wei, Zhaolong Shen, Changti Wu, Yuzhuo Miao, Xinming Wang, et al.. (2026). [TwinBrainVLA: Unleashing the Potential of Generalist VLMs for Embodied Tasks via Asymmetric Mixture-of-Transformers](https://arxiv.org/abs/2601.14133). arXiv:2601.14133.
29. I. Apanasevich, M. Artemyev, R. Babakyan, P. Fedotova, D. Grankin, E. Kupryashin, A. Misailidi, D. Nerus, et al.. (2026). [Green-VLA: Staged Vision-Language-Action Model for Generalist Robots](https://arxiv.org/abs/2602.00919). arXiv:2602.00919.
30. Wentao Zhang, Aolan Sun, Wentao Mo, Xiaoyang Qu, Yuxin Zheng, Jianzong Wang. (2026). [From Knowing to Doing Precisely: A General Self-Correction and Termination Framework for VLA models](https://arxiv.org/abs/2602.01811). arXiv:2602.01811.
31. Rui Cai, Jun Guo, Xinze He, Piaopiao Jin, Jie Li, Bingxuan Lin, Futeng Liu, Wei Liu, et al.. (2026). [Xiaomi-Robotics-0: An Open-Sourced Vision-Language-Action Model with Real-Time Execution](https://arxiv.org/abs/2602.12684). arXiv:2602.12684.
32. Chenyv Liu, Wentao Tan, Lei Zhu, Fengling Li, Jingjing Li, Guoli Yang, Heng Tao Shen. (2026). [Self-Correcting VLA: Online Action Refinement via Sparse World Imagination](https://arxiv.org/abs/2602.21633). arXiv:2602.21633.
33. Yao Li, Peiyuan Tang, Wuyang Zhang, Chengyang Zhu, Yifan Duan, Weikai Shi, Xiaodong Zhang, Zijiang Yang, et al.. (2026). [FAVLA: A Force-Adaptive Fast-Slow VLA model for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2602.23648). arXiv:2602.23648.
34. Jiasong Xiao, Yutao She, Kai Li, Yuyang Sha, Ziang Cheng. (2026). [StemVLA:An Open-Source Vision-Language-Action Model with Future 3D Spatial Geometry Knowledge and 4D Historical Representation](https://arxiv.org/abs/2602.23721). arXiv:2602.23721.
35. Guangqi Jiang, Yutong Liang, Jianglong Ye, Jiayin Huang, Changwei Jing, Rocky Duan, Pieter Abbeel, Xiaolong Wang, et al.. (2026). [Cross-Hand Latent Representation for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Jiang_Cross-Hand_Latent_Representation_for_Vision-Language-Action_Models_CVPR_2026_paper.html). *CVPR 2026*.
36. Yu Sun, Meng Cao, Yang Ping, Kaidong Zhang, Qingxuan Chen, Rongtao Xu, Liangwang Ruan, Xuecheng Chen, et al.. (2026). [ManipArena: Comprehensive Real-world Evaluation of Reasoning-Oriented Generalist Robot Manipulation](https://arxiv.org/abs/2603.28545). arXiv:2603.28545.
37. Physical Intelligence, Bo Ai, Ali Amin, Raichelle Aniceto, Ashwin Balakrishna, Greg Balke, Kevin Black, George Bokinsky, et al.. (2026). [$π_{0.7}$: a Steerable Generalist Robotic Foundation Model with Emergent Capabilities](https://arxiv.org/abs/2604.15483). arXiv:2604.15483.
38. Open-H-Embodiment Consortium, :, Nigel Nelson, Juo-Tung Chen, Jesse Haworth, Xinhao Chen, Lukas Zbinden, Dianye Huang, et al.. (2026). [Open-H-Embodiment: A Large-Scale Dataset for Enabling Foundation Models in Medical Robotics](https://arxiv.org/abs/2604.21017). arXiv:2604.21017.
39. Isabella Liu, An-Chieh Cheng, Rui Yan, Geng Chen, Ri-Zhao Qiu, Xueyan Zou, Sha Yi, Hongxu Yin, et al.. (2026). [Long-Horizon Manipulation via Trace-Conditioned VLA Planning](https://arxiv.org/abs/2604.21924). arXiv:2604.21924.
40. Yifei Wei, Linqing Zhong, Yi Liu, Yuxiang Lu, Xindong He, Maoqing Yao, Guanghui Ren. (2026). [Libra-VLA: Achieving Learning Equilibrium via Asynchronous Coarse-to-Fine Dual-System](https://arxiv.org/abs/2604.24921). arXiv:2604.24921.
41. Sizhe Lester Li, Evan Kim, Xingjian Bai, Tong Zhao, Tao Pang, Max Simchowitz, Vincent Sitzmann. (2026). [Turning Video Models into Generalist Robot Policies](https://arxiv.org/abs/2605.27817). arXiv:2605.27817.
42. Qiuyue Wang, Mingsheng Li, Jian Guan, Jinhui Ye, Sicheng Xie, Yitao Liu, Junhao Chen, Zhixuan Liang, et al.. (2026). [Qwen-VLA: Unifying Vision-Language-Action Modeling across Tasks, Environments, and Robot Embodiments](https://arxiv.org/abs/2605.30280). arXiv:2605.30280.
43. Taiyi Su, Jian Zhu, Tianjian Wang, Youzhang He, Zitai Huang, Jianjun Zhang, Chong Ma, Hanyang Wang, et al.. (2026). [DeMaVLA: A Vision-Language-Action Foundation Model for Generalizable Deformable Manipulation](https://arxiv.org/abs/2605.31286). arXiv:2605.31286.
44. Yueh-Hua Wu, Tatsuya Matsushima, Kei Ota. (2026). [Continuous Reasoning for Vision-Language-Action](https://arxiv.org/abs/2606.00229). arXiv:2606.00229.
45. Lingfeng Zhang, Xiaoshuai Hao, Yingbo Tang, Lei Zhou, Shuyi Zhang, Jinkun Liu, Hongsheng Li, Chenhao Zhang, et al.. (2026). [OneVLA: A Unified Framework for Embodied Tasks](https://arxiv.org/abs/2606.01241). arXiv:2606.01241.
46. Dongyoon Hwang, Byungkun Lee, Dongjin Kim, Hyojin Jang, Hoiyeong Jin, Jueun Mun, Minho Park, Hojoon Lee, et al.. (2026). [3D HAMSTER: Bridging Planning and Control in Hierarchical Vision Language Action Models through 3D Trajectory Guidance](https://arxiv.org/abs/2606.31329). arXiv:2606.31329.
47. Xidong Zhang, Yichi Zhang, Jiaxin Shi, Fucai Zhu, Siyu Zhu, Michael Yu Wang, Xiaojun Wu, Weihao Yuan. (2026). [UniTacVLA: Unified Tactile Understanding and Prediction in Vision Language Action Models](https://arxiv.org/abs/2606.31723). arXiv:2606.31723.
48. Chenyang Ma, Yue Yang, Radu Corcodel, Siddarth Jain, Andrew Wu, Chiori Hori, Diego Romeres. (2026). [FurnitureVLA: Learning Long-Horizon Bimanual Furniture Assembly with Vision-Language-Action Model](https://arxiv.org/abs/2607.01212). arXiv:2607.01212.
49. Yi Pan, Miao Pan, Qi Lu, Jiaming Huang, Man Zhang, Siteng Huang, Xin Li, Jie Zhang, et al.. (2026). [VLA-Corrector: Lightweight Detect-and-Correct Inference for Adaptive Action Horizon](https://arxiv.org/abs/2607.01804). arXiv:2607.01804.
50. Chongkei Chang, Zhidong Deng. (2026). [DynaWM: A Base-VLA-Guided World Foundation Model for Moving-Object Manipulation](https://arxiv.org/abs/2607.02604). arXiv:2607.02604.
51. Li Ji, Siyin Wang, Pengfang Qian, Xiaopeng Yu, Yihai Tian, Zhaoye Fei, Jingjing Gong, Xipeng Qiu. (2026). [HiMe: Hierarchical Embodied Memory for Long-Horizon Vision-Language-Action Control](https://arxiv.org/abs/2607.03449). arXiv:2607.03449.
52. Xinyi Xie, Zican Hu, Zhanyun Liu, Yicheng Dong, Wenhao Wu, Zhenhong Sun, Haoran Li, Chunlin Chen, et al.. (2026). [Look Before You Leap: Distilling Tree Search into Action Evaluation for Frozen VLA Models](https://arxiv.org/abs/2607.03751). arXiv:2607.03751.
53. Xiaomi Robotics Team, Jun Guo, Piaopiao Jin, Jason Li, Peiyan Li, Yingyan Li, Futeng Liu, Wanli Peng, et al.. (2026). [Xiaomi-Robotics-1: Scaling Vision-Language-Action Models with over 100K Hours of Real-World Trajectories](https://arxiv.org/abs/2607.15330). arXiv:2607.15330.
54. Yang Liu, Weixing Chen, Xinshuai Song, Tao Pu, Siwen Mo, Yongjie Bai, Zihao Chen, Qianran Sun, et al.. (2026). [PhyAgentOS: A Self-Evolving Operating System for Embodied Agents with Decoupled Cognitive Planning and Physical Execution](https://arxiv.org/abs/2607.16636). arXiv:2607.16636.
55. Ning Cheng, Jinan Xu, Wanlin Li, Yangzhi Chen, Jing Gao, Yiqun Wang, Kelan Peng, Wenjuan Han. (2026). [τ: Learning Touch-Augmented Vision-Language-Action Models from Future Visual Supervision](https://arxiv.org/abs/2607.24485). arXiv:2607.24485.
56. Kasra Sinaei, Hung-Chieh Wu, Donald Ebeigbe. (2026). [Safe Vision Language Action Models via Barrier Enhanced Flow Matching](https://arxiv.org/abs/2607.29569). arXiv:2607.29569.
57. Senyu Fei, Xiaopeng Yu, Siyin Wang, Xianzhong Zhao, Jingjing Gong, Xipeng Qiu. (2026). [WCM: A World Critic Model for Vision-Language-Action Reinforcement Learning](https://arxiv.org/abs/2607.29613). arXiv:2607.29613.
### D2 · 分层推理、规划与记忆

1. Michał Zawalski, William Chen, Karl Pertsch, Oier Mees, Chelsea Finn, Sergey Levine. (2024). [Robotic Control via Embodied Chain-of-Thought Reasoning](https://proceedings.mlr.press/v270/zawalski25a.html). *CoRL 2024*.
2. Meng Wei, Chenyang Wan, Jiaqi Peng, Xiqian Yu, Yuqiang Yang, Delin Feng, Wenzhe Cai, Chenming Zhu, et al.. (2025). [Ground Slow, Move Fast: A Dual-System Foundation Model for Generalizable Vision-and-Language Navigation](https://arxiv.org/abs/2512.08186). arXiv:2512.08186.
3. Tong Chen, Hang Wu, Jiasen Wang, Xiaotao Li, Lu Fang. (2026). [StreamVLA: Breaking the Reason-Act Cycle via Completion-State Gating](https://arxiv.org/abs/2602.01100). arXiv:2602.01100.
4. Haoyang Li, Guanlin Li, Youhe Feng, Chen Zhao, Zhuoran Wang, Yang Li, Qizhe Wei, Shifeng Bao, et al.. (2026). [Training Vision-Language-Action Models with Dense Embodied Chain-of-Thought Supervision](https://arxiv.org/abs/2606.30552). arXiv:2606.30552.
### D3 · 世界模型与预测控制

1. Chuning Zhu, Raymond Yu, Siyuan Feng, B. Burchfiel, Paarth Shah, Abhishek Gupta. (2025). [Unified World Models: Coupling Video and Action Diffusion for Pretraining on Large Robotic Datasets](https://www.roboticsproceedings.org/rss21/p015.html). *RSS 2025*.
2. Yuhang Huang, Jiazhao Zhang, Shilong Zou, Xinwang Liu, Ruizhen Hu, Kai Xu. (2025). [LaDi-WM: A Latent Diffusion-based World Model for Predictive Manipulation](https://proceedings.mlr.press/v305/huang25a.html). *CoRL 2025*.
3. Suning Huang, Qianzhong Chen, Xiaohan Zhang, Jiankai Sun, Mac Schwager. (2025). [ParticleFormer: A 3D Point Cloud World Model for Multi-Object, Multi-Material Robotic Manipulation](https://proceedings.mlr.press/v305/huang25c.html). *CoRL 2025*.
4. Boyuan Wang, Xinpan Meng, Xiaofeng Wang, Zheng Zhu, Angen Ye, Yang Wang, Zhiqin Yang, Chaojun Ni, et al.. (2025). [EmbodieDreamer: Advancing Real2Sim2Real Transfer for Policy Training via Embodied World Modeling](https://arxiv.org/abs/2507.05198). arXiv:2507.05198.
5. Guanxing Lu, Baoxiong Jia, Puhao Li, Yixin Chen, Ziwei Wang, Yansong Tang, Siyuan Huang. (2025). [GWM: Towards Scalable Gaussian World Models for Robotic Manipulation](https://arxiv.org/abs/2508.17600). arXiv:2508.17600.
6. Bahey Tharwat, Yara Nasser, Ali Abouzeid, Ian Reid. (2025). [Latent Action Pretraining Through World Modeling](https://arxiv.org/abs/2509.18428). arXiv:2509.18428.
7. Yanjiang Guo, Lucy Xiaoyang Shi, Jianyu Chen, Chelsea Finn. (2025). [Ctrl-World: A Controllable Generative World Model for Robot Manipulation](https://arxiv.org/abs/2510.10125). arXiv:2510.10125.
8. R. Khorrambakht, Joaquim Ortiz-Haro, Joseph Amigo, Omar Mostafa, Daniel Dugas, Franziska Meier, Ludovic Righetti. (2025). [WorldPlanner: Monte Carlo Tree Search and MPC with Action-Conditioned Visual World Models](https://arxiv.org/abs/2511.03077). arXiv:2511.03077.
9. Hongzhe Bi, Hengkai Tan, Shenghao Xie, Zeyuan Wang, Shuhe Huang, Haitian Liu, Ruowen Zhao, Yao Feng, et al.. (2025). [Motus: A Unified Latent Action World Model](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html). *CVPR 2026*.
10. Wenjun Lin, Jensen Zhang, Kaitong Cai, Keze Wang. (2025). [STORM: Search-Guided Generative World Models for Robotic Manipulation](https://arxiv.org/abs/2512.18477). arXiv:2512.18477.
11. Wenlong Huang, Yu-Wei Chao, A. Mousavian, Ming-Yu Liu, Dieter Fox, Kaichun Mo, Fei-Fei Li. (2026). [PointWorld: Scaling 3D World Models for In-The-Wild Robotic Manipulation](https://openaccess.thecvf.com/content/CVPR2026/html/Huang_PointWorld_Scaling_3D_World_Models_for_In-The-Wild_Robotic_Manipulation_CVPR_2026_paper.html). *CVPR 2026*.
12. Quentin Garrido, Tushar Nagarajan, Basile Terver, Nicolas Ballas, Yann LeCun, Michael Rabbat. (2026). [Learning Latent Action World Models In The Wild](https://arxiv.org/abs/2601.05230). arXiv:2601.05230.
13. Moo Jin Kim, Yihuai Gao, Tsung-Yi Lin, Yen-Chen Lin, Yunhao Ge, Grace Lam, Percy Liang, Shuran Song, et al.. (2026). [Cosmos Policy: Fine-Tuning Video Models for Visuomotor Control and Planning](https://arxiv.org/abs/2601.16163). arXiv:2601.16163.
14. Ansh Kumar Sharma, Yixiang Sun, Ning Lu, Yunzhe Zhang, Jiarao Liu, Sherry Yang. (2026). [World-Gymnast: Training Robots with Reinforcement Learning in a World Model](https://arxiv.org/abs/2602.02454). arXiv:2602.02454.
15. Zhennan Jiang, Shangqing Zhou, Yutong Jiang, Zefang Huang, Mingjie Wei, Yuhui Chen, Tianxing Zhou, Zhen Guo, et al.. (2026). [WoVR: World Models as Reliable Simulators for Post-Training VLA Policies with RL](https://arxiv.org/abs/2602.13977). arXiv:2602.13977.
16. Hao Luo, Ye Wang, Wanpeng Zhang, Haoqi Yuan, Yicheng Feng, Haiweng Xu, Sipeng Zheng, Zongqing Lu. (2026). [Joint-Aligned Latent Action: Towards Scalable VLA Pretraining in the Wild](https://arxiv.org/abs/2602.21736). arXiv:2602.21736.
17. Emily Yue-Ting Jia, Weiduo Yuan, Tianheng Shi, Vitor Guizilini, Jiageng Mao, Yue Wang. (2026). [DreamPlan: Efficient Reinforcement Fine-Tuning of Vision-Language Planners via Video World Models](https://arxiv.org/abs/2603.16860). arXiv:2603.16860.
18. Ruixiang Wang, Qingming Liu, Yueci Deng, Guiliang Liu, Zhen Liu, Kui Jia. (2026). [EVA: Aligning Video World Models with Executable Robot Actions via Inverse Dynamics Rewards](https://arxiv.org/abs/2603.17808). arXiv:2603.17808.
19. Yi Chen, Yuying Ge, Hui Zhou, Mingyu Ding, Yixiao Ge, Xihui Liu. (2026). [DIAL: Decoupling Intent and Action via Latent World Modeling for End-to-End VLA](https://arxiv.org/abs/2603.29844). arXiv:2603.29844.
20. Yuxuan Tian, Yurun Jin, Bin Yu, Yukun Shi, Hao Wu, Chi Harold Liu, Kai Chen, Cong Huang. (2026). [STARRY: Spatial-Temporal Action-Centric World Modeling for Robotic Manipulation](https://arxiv.org/abs/2604.26848). arXiv:2604.26848.
21. Pengfei Zhou, Shengcong Chen, Di Chen, Jiaxu Wang, Rongjun Jin, Bingwen Zhu, Yike Pan, Songen Gu, et al.. (2026). [$τ_0$-WM: A Unified Video-Action World Model for Robotic Manipulation](https://arxiv.org/abs/2606.01027). arXiv:2606.01027.
22. Ziyu Shan, Zhenyu Wu, Xiaofeng Wang, Zheng Zhu, Ziwei Wang. (2026). [DVG-WM: Disentangled Video Generation Enables Efficient Embodied World Model for Robotic Manipulation](https://arxiv.org/abs/2606.32028). arXiv:2606.32028.
23. Shengbang Liu, Yueru Jia, Yuyang Yan, Jiaming Liu, Xinran Y. Zhang, Qiuxuan Feng, Yandong Guo, Shiji Zhou, et al.. (2026). [TACO: TActile World Model as a Self-COrrector forScalable VLA Post-Training](https://arxiv.org/abs/2607.02840). arXiv:2607.02840.
24. Yunao Huang, Shiyu Sang, Haotao Lu, Suting Ni, Shijie Wu, Ziyang Guo, Ye Shi, Jingya Wang. (2026). [ViTacWorld: Scaling Visuo-Tactile World Models for Contact-Rich Robot Manipulation](https://arxiv.org/abs/2607.22530). arXiv:2607.22530.
25. Haoyuan Ji, Lingxiang Fan, Shang Su, Yinqiao Lu, Mengkai Shi, Jun Gao, Shuo Feng. (2026). [DC-WAM: Dynamic-Centric Visual Supervision and Reasoning for World-Action Models](https://arxiv.org/abs/2607.25918). arXiv:2607.25918.
26. Xiangcheng Zhang, Yilun Du. (2026). [World Action Planner: Generalizable Decision-Making with Action-Conditioned World Models](https://arxiv.org/abs/2607.27599). arXiv:2607.27599.
### D4 · 灵巧、双臂与接触操作

1. Mengda Xu, H. Zhang, Yifan Hou, Zhenjia Xu, L. Fan, Manuela Veloso, Shuran Song. (2025). [DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://proceedings.mlr.press/v305/xu25b.html). *CoRL 2025*.
2. Yixiang Chen, Peiyan Li, Yan Huang, Jiabing Yang, Kehan Chen, Liang Wang. (2025). [EC-Flow: Enabling Versatile Robotic Manipulation from Action-Unlabeled Videos via Embodiment-Centric Flow](https://arxiv.org/abs/2507.06224). arXiv:2507.06224.
3. Hongzhe Bi, Lingxuan Wu, Tianwei Lin, Hengkai Tan, Zhizhong Su, Hang Su, Jun Zhu. (2025). [H-RDT: Human Manipulation Enhanced Bimanual Robotic Manipulation](https://arxiv.org/abs/2507.23523). arXiv:2507.23523.
4. Junbang Liang, Pavel Tokmakov, Ruoshi Liu, Sruthi Sudhakar, Paarth Shah, Rares Ambrus, Carl Vondrick. (2025). [Video Generators are Robot Policies](https://arxiv.org/abs/2508.00795). arXiv:2508.00795.
5. Ahad Jawaid, Yu Xiang. (2025). [OpenEgo: A Large-Scale Multimodal Egocentric Dataset for Dexterous Manipulation](https://arxiv.org/abs/2509.05513). arXiv:2509.05513.
6. Harrison Field, Max Yang, Yijiong Lin, Efi Psomopoulou, David Barton, Nathan F. Lepora. (2025). [Text2Touch: Tactile In-Hand Manipulation with LLM-Designed Reward Functions](https://arxiv.org/abs/2509.07445). arXiv:2509.07445.
7. Zhiyuan Wu, Rolandos Alexandros Potamias, Xuyang Zhang, Zhongqun Zhang, Jiankang Deng, Shan Luo. (2025). [CEDex: Cross-Embodiment Dexterous Grasp Generation at Scale from Human-like Contact Representations](https://arxiv.org/abs/2509.24661). arXiv:2509.24661.
8. Jhen Hsieh, Kuan-Hsun Tu, Kuo-Han Hung, Tsung-Wei Ke. (2025). [DexMan: Learning Bimanual Dexterous Manipulation from Human and Generated Videos](https://arxiv.org/abs/2510.08475). arXiv:2510.08475.
9. Zihao He, Bo Ai, Tongzhou Mu, Yulin Liu, Weikang Wan, Jiawei Fu, Yilun Du, Henrik I. Christensen, et al.. (2025). [Scaling Cross-Embodiment World Models for Dexterous Manipulation](https://arxiv.org/abs/2511.01177). arXiv:2511.01177.
10. Le Chen, Yi Zhao, Jan Schneider, Quankai Gao, Simon Guist, Cheng Qian, Juho Kannala, Bernhard Schölkopf, et al.. (2025). [Dexterous Robotic Piano Playing at Scale](https://arxiv.org/abs/2511.02504). arXiv:2511.02504.
11. Huayi Zhou, Kui Jia. (2025). [One-Shot Real-World Demonstration Synthesis for Scalable Bimanual Manipulation](https://arxiv.org/abs/2512.09297). arXiv:2512.09297.
12. Zhongxuan Li, Zeliang Guo, Jun Hu, David Navarro-Alarcon, Jia Pan, Hongmin Wu, Peng Zhou. (2026). [UniBiDex: A Unified Teleoperation Framework for Robotic Bimanual Dexterous Manipulation](https://arxiv.org/abs/2601.04629). arXiv:2601.04629.
13. Ruijie Zheng, Dantong Niu, Yuqi Xie, Jing Wang, Mengda Xu, Yunfan Jiang, Fernando Castañeda, Fengyuan Hu, et al.. (2026). [EgoScale: Scaling Dexterous Manipulation with Diverse Egocentric Human Data](https://arxiv.org/abs/2602.16710). arXiv:2602.16710.
14. Yuhang Zheng, Songen Gu, Weize Li, Yupeng Zheng, Yujie Zang, Shuai Tian, Xiang Li, Ce Hao, et al.. (2026). [OmniVTA: Visuo-Tactile World Modeling for Contact-Rich Robotic Manipulation](https://arxiv.org/abs/2603.19201). arXiv:2603.19201.
15. Hung-Chieh Fang, Amber Xie, Jennifer Grannen, Kenneth Llontop, Dorsa Sadigh. (2026). [DexDrummer: In-Hand, Contact-Rich, and Long-Horizon Dexterous Robot Drumming](https://arxiv.org/abs/2603.22263). arXiv:2603.22263.
16. Zhixuan Xu, Yichen Li, Xuanye Wu, Tianyu Qiu, Lin Shao. (2026). [FingerEye: Learning Dexterous Manipulation with Continuous Vision-Tactile Sensing](https://arxiv.org/abs/2604.20689). arXiv:2604.20689.
17. Bowen Jiang, William Painter Reger, Roberto Martin-Martin. (2026). [CoDex: Learning Compositional Dexterous Functional Manipulation without Demonstrations](https://arxiv.org/abs/2606.31909). arXiv:2606.31909.
18. Lei Jin, Yiding Ma, Xin Zhang, Chen Gao, Wei Wu, Yong Li. (2026). [TacWAM: Anchor-Guided World Action Model with Mechanics-Aware Tactile Prediction](https://arxiv.org/abs/2607.28391). arXiv:2607.28391.
19. Lifeng Zhuo, Wendi Chen, Han Xue, Shirun Tang, Jun Lv, Cewu Lu, Chuan Wen. (2026). [FA-RDP: A Frequency-Adaptive Reactive Diffusion Policy for Contact-Rich Manipulation](https://arxiv.org/abs/2607.28596). arXiv:2607.28596.
### D5 · 人形、运动与全身控制

1. Yaru Niu, Zhenlong Fang, Binghong Chen, Shuai Zhou, Revanth Krishna Senthilkumaran, Hao Zhang, Bingqing Chen, Chen Qiu, et al.. (2026). [Learning Versatile Humanoid Manipulation with Touch Dreaming](https://arxiv.org/abs/2604.13015). arXiv:2604.13015.
2. Yuxin Chen, Hari Srikanth, Nathan Jew, Menglin Wu, Pengcheng Wang, Junli Ren, Masayoshi Tomizuka, Peng Xu, et al.. (2026). [CLIFT: Turning Gemini Robotics On-Device into Humanoid Specialists via Non-Invasive Closed-Loop Iterative Fine-Tuning](https://arxiv.org/abs/2607.29172). arXiv:2607.29172.
### D8 · 策略学习与优化

1. Han Xue, Jieji Ren, Wendi Chen, Gu Zhang, Yuan Fang, Guoying Gu, Huazhe Xu, Cewu Lu. (2025). [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html). *RSS 2025*.
2. Gagan Khandate. (2025). [Towards Human-level Dexterity via Robot Learning](https://arxiv.org/abs/2507.09117). arXiv:2507.09117.
3. Akshay L Chandra, Iman Nematollahi, Chenguang Huang, Tim Welschehold, Wolfram Burgard, Abhinav Valada. (2025). [DiWA: Diffusion Policy Adaptation with World Models](https://arxiv.org/abs/2508.03645). arXiv:2508.03645.
4. Ge Yan, Jiyue Zhu, Yuquan Deng, Shiqi Yang, Ri-Zhao Qiu, Xuxin Cheng, Marius Memmel, Ranjay Krishna, et al.. (2025). [ManiFlow: A General Robot Manipulation Policy via Consistency Flow Training](https://arxiv.org/abs/2509.01819). arXiv:2509.01819.
5. Jinliang Zheng, Jianxiong Li, Zhihao Wang, Dongxiu Liu, Xirui Kang, Yuchun Feng, Yinan Zheng, Jiayin Zou, et al.. (2025). [X-VLA: Soft-Prompted Transformer as Scalable Cross-Embodiment Vision-Language-Action Model](https://arxiv.org/abs/2510.10274). arXiv:2510.10274.
6. Maximus A. Pace, Prithwish Dan, Chuanruo Ning, Atiksh Bhardwaj, Audrey Du, Edward W. Duan, Wei-Chiu Ma, Kushal Kedia. (2025). [X-Diffusion: Training Diffusion Policies on Cross-Embodiment Human Demonstrations](https://arxiv.org/abs/2511.04671). arXiv:2511.04671.
7. Yuhong Zhang, Zihan Gao, Shengpeng Li, Ling-Hao Chen, Kaisheng Liu, Runqing Cheng, Xiao Lin, Junjia Liu, et al.. (2025). [RoboWheel: A Data Engine from Real-World Human Demonstrations for Cross-Embodiment Robotic Learning](https://arxiv.org/abs/2512.02729). arXiv:2512.02729.
8. Yueru Jia, Jiaming Liu, Shengbang Liu, Rui Zhou, Wanhe Yu, Yuyang Yan, Xiaowei Chi, Yandong Guo, et al.. (2025). [Video2Act: A Dual-System Video Diffusion Policy with Robotic Spatio-Motional Modeling](https://arxiv.org/abs/2512.03044). arXiv:2512.03044.
9. Hao Luo, Ye Wang, Wanpeng Zhang, Sipeng Zheng, Ziheng Xi, Chaoyi Xu, Haiweng Xu, Haoqi Yuan, et al.. (2026). [Being-H0.5: Scaling Human-Centric Robot Learning for Cross-Embodiment Generalization](https://arxiv.org/abs/2601.12993). arXiv:2601.12993.
10. Zhongxi Chen, Yifan Han, Yanming Shao, Huanming Liu, Congsheng Xu, Xiaoyu Chen, Yao Mu, Wenzhao Lian. (2026). [BORA: Bridging Offline Reinforcement Learning and Online Residual Adaptation for Real-World Dexterous VLA Models](https://arxiv.org/abs/2605.30226). arXiv:2605.30226.
11. Arthur Allshire, Himanshu Gaurav Singh, Ritvik Singh, Adam Rashid, Hongsuk Choi, David McAllister, Justin Yu, Yiyuan Chen, et al.. (2026). [Scalable Behavior Cloning with Open Data, Training, and Evaluation](https://arxiv.org/abs/2606.27375). arXiv:2606.27375.
12. Yifan Ye, Yankai Fu, Yaoxu Lv, Bohan Hou, Jun Cen, Lingdong Kong, Duo Zheng, Tianxing Chen, et al.. (2026). [Data Pyramid for Embodied Manipulation](https://arxiv.org/abs/2607.24744). arXiv:2607.24744.
13. Ajay Sridhar, Jensen Gao, Jonathan Yang, Jean Mercat, Suneel Belkhale, Dorsa Sadigh. (2026). [Cross-Embodiment Transfer via Behavior-Aligned Representations](https://arxiv.org/abs/2607.27549). arXiv:2607.27549.
14. Zhengyang Yan, Junhao Li, Fangqi Zhu, Zijun Wang, Quanxin Shou, Yikun Miao, Xiaoyi Pang, Zicong Hong, et al.. (2026). [RedFlow: Redirect Failure into Action-Level Corrections for Flow-matching VLA Policy](https://arxiv.org/abs/2607.27782). arXiv:2607.27782.
15. BWM Team. (2026). [BWM: A Low-Cost High-Fidelity World Simulator for Robot Learning](https://arxiv.org/abs/2607.29302). arXiv:2607.29302.
### D9 · 数据引擎与人类视频学习

1. Marion Lepert, Jiaying Fang, Jeannette Bohg. (2025). [Masquerade: Learning from In-the-wild Human Videos using Data-Editing](https://arxiv.org/abs/2508.09976). arXiv:2508.09976.
2. Georgios Tziafas, Jiayun Zhang, Hamidreza Kasaei. (2025). [Parse-Augment-Distill: Learning Generalizable Bimanual Visuomotor Policies from Single Human Video](https://arxiv.org/abs/2509.20286). arXiv:2509.20286.
3. Gu Zhang, Qicheng Xu, Haozhe Zhang, Jianhan Ma, Long He, Yiming Bao, Zeyu Ping, Zhecheng Yuan, et al.. (2026). [UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html). *CVPR 2026*.
4. Xiaopeng Lin, Ruoqi Yang, Shijie Lian, Zhaolong Shen, Bin Yu, Changti Wu, Haibao Liu, Yuxiang Zhang, et al.. (2026). [Human-as-Humanoid: Enabling Zero-Shot Humanoid Learning from Ego-Exo Human Videos with Human-Aligned Embodiments](https://arxiv.org/abs/2606.32009). arXiv:2606.32009.
5. Yukang Cao, Haozhe Xie, Beichen Wen, Runmao Yao, Yinghao Liu, Yue Huang, Zhichao Liao, Yunxiang Wang, et al.. (2026). [ACE-Data-0: Human-Centric Ambient Capture as Embodied Data Engine](https://arxiv.org/abs/2607.28625). arXiv:2607.28625.
### D15 · 触觉、力觉与多模态身体感知

1. Zhengxue Cheng, Yiqian Zhang, Anni Tang, Keyu Wang, Wenkang Zhang, Haoyu Li, Hengdi Zhang, Li Song. (2025). [OmniVTLA: Vision-Tactile-Language-Action Models with Semantic-Aligned Tactile Sensing](https://arxiv.org/abs/2508.08706). arXiv:2508.08706.

---
