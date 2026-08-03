---
outline: deep
---

# 年度综合：从“更大 VLA”转向“可执行、可纠错、可持续学习”

> 主分析期为 2025 年 7 月—2026 年 6 月。同比增长只在同一宽召回查询口径内有效，不代表全部机器人论文的绝对市场份额。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>5221</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>3214</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>84</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>30</strong><span>官方评审锚点</span></div>
</div>

## 15 个方向年度结构

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

## A 级：已确认路线

| 判断 | 为什么升级 | 官方证据 |
|---|---|---|
| <span class="signal signal-a">A</span> VLA / generalist policy 已从预印本热点变成正式研究主线 | π0、FAST、π0.5 等独立正式工作覆盖动作生成、效率和开放世界泛化。 | [π0: A Vision-Language-Action Flow Model for General Robot Control](https://www.roboticsproceedings.org/rss21/p010.html)；[FAST: Efficient Action Tokenization for Vision-Language-Action Models](https://www.roboticsproceedings.org/rss21/p012.html)；[π0.5: a Vision-Language-Action Model with Open-World Generalization](https://proceedings.mlr.press/v305/black25a.html) |
| <span class="signal signal-a">A</span> 快慢分工与中间推理已获得独立评审验证 | Embodied CoT、Reactive Diffusion Policy 与 ACoT-VLA 从语言推理、视觉触觉控制和动作链三侧验证。 | [Robotic Control via Embodied Chain-of-Thought Reasoning](https://proceedings.mlr.press/v270/zawalski25a.html)；[Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html)；[ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models](https://openaccess.thecvf.com/content/CVPR2026/html/Zhong_ACoT-VLA_Action_Chain-of-Thought_for_Vision-Language-Action_Models_CVPR_2026_paper.html) |
| <span class="signal signal-a">A</span> 机器人世界模型从生成转向控制的路线已被多 venue 接纳 | 视频—动作联合、latent dynamics、3D 物理预测和统一 latent action 都有官方评审证据。 | [Unified World Models: Coupling Video and Action Diffusion for Pretraining on Large Robotic Datasets](https://www.roboticsproceedings.org/rss21/p015.html)；[LaDi-WM: A Latent Diffusion-based World Model for Predictive Manipulation](https://proceedings.mlr.press/v305/huang25a.html)；[ParticleFormer: A 3D Point Cloud World Model for Multi-Object, Multi-Material Robotic Manipulation](https://proceedings.mlr.press/v305/huang25c.html)；[Motus: A Unified Latent Action World Model](https://openaccess.thecvf.com/content/CVPR2026/html/Bi_Motus_A_Unified_Latent_Action_World_Model_CVPR_2026_paper.html) |
| <span class="signal signal-a">A</span> 灵巧操作的数据与触觉路线已跨团队验证 | 视觉触觉、UMI 人类示范与 egocentric 通用手控制形成连续证据链。 | [Reactive Diffusion Policy: Slow-Fast Visual-Tactile Policy Learning for Contact-Rich Manipulation](https://www.roboticsproceedings.org/rss21/p052.html)；[DexUMI: Using Human Hand as the Universal Manipulation Interface for Dexterous Manipulation](https://proceedings.mlr.press/v305/xu25b.html)；[UniDex: A Robot Foundation Suite for Universal Dexterous Hand Control from Egocentric Human Videos](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_UniDex_A_Robot_Foundation_Suite_for_Universal_Dexterous_Hand_Control_CVPR_2026_paper.html) |

## 持续升温

- **VLA 后训练与经验学习。** 从 VLA-RFT、π*0.6 到 2026 年的在线自纠错，目标从复制示范转向用部署经验改进。
- **世界模型的可执行性。** 2026 年 3 月后，inverse dynamics reward、RL simulator 和 world-action unified model 密集出现。
- **视触觉闭环。** 触觉从感知输入升级为 future prediction、world model 和 recovery 信号。
- **跨本体数据与动作表示。** 共享人类视频、latent action、接触表示与 embodiment adapter 正在收敛。

## 出现拐点

- **大小脑。** 2025 年重在 planner–policy 结构，2026 年转向异步调度、continuous reasoning、completion gating 和 3D trace。
- **通用性。** 从“同一模型做更多 benchmark”转向“同一训练栈适应真实、灵巧、软体、医疗等高约束任务”。
- **开放。** 从只放权重扩展到数据、训练、评测和低成本采集工具。

## 降温与未兑现

- **只以视频生成质量证明的世界模型：D。** 若不报告规划或控制收益，不再视为强信号。
- **堆叠模块式 VLA：D。** 更换 backbone、adapter 或 action head 而没有新能力的工作增长很快，但战略价值有限。
- **“一个权重跨所有机器人”：C/D。** 现有证据更支持共享表征 + embodiment adapter。
- **开源承诺即生态：D。** 只有出现第三方复现和采用，开源热度才升级为趋势。

## 下一步

真正领先于共识的八项判断见[弱信号探测与未来判断](/analysis/weak-signals)。每项都包含 3–24 个月验证路标和反证条件。
