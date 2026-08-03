---
outline: deep
---

# 语料扩充与覆盖审计

> 数据截点：2026-08-04。这里把“母集”“自动相关候选”“边界复核”“精读锚点”分开，避免再用精选篇数冒充总覆盖量。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>30,766</strong><span>arXiv 母集</span></div>
  <div class="radar-kpi"><strong>10,404</strong><span>窗口内正式发表母集</span></div>
  <div class="radar-kpi"><strong>824</strong><span>完整官方容器记录</span></div>
  <div class="radar-kpi"><strong>3,161</strong><span>官方节目/待 proceedings</span></div>
  <div class="radar-kpi"><strong>42</strong><span>GitHub 核验仓库</span></div>
</div>

## 当前证据库结构

网站统一使用三条独立管线，并以 canonical work 合并同一研究的预印本、正式发表与代码仓库：

1. **arXiv 母集**：完整 cs.RO 月度拉取，再补 cs.AI/CV/LG 中的机器人与具身主题；月份始终按 v1。
2. **正式发表母集**：ICRA、IROS、RSS、CoRL、RA-L、T-RO、IJRR、Science Robotics 独立采集；无 arXiv ID 也可存在。
3. **开源生态**：论文链接、GitHub Search、机构组织页和 README 反向映射；stars 只作为传播元数据，不进入独立采用分。

## 正式发表漏斗

| Venue | 母集（含去重前缘） | 窗口内 | 窗口内直接候选 | 窗口内边界候选 | 窗口内待摘要/人工 | 有摘要 | 有 arXiv | 有 DOI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CoRL | 265 | 265 | 117 | 39 | 109 | 0 | 0 | 0 |
| ICRA | 3366 | 1605 | 455 | 287 | 809 | 3357 | 2037 | 3366 |
| IJRR | 263 | 263 | 75 | 47 | 137 | 222 | 98 | 263 |
| IROS | 3568 | 3568 | 922 | 621 | 1920 | 3561 | 1805 | 3568 |
| RA-L | 3740 | 3740 | 875 | 629 | 2160 | 3502 | 1314 | 3740 |
| RSS | 135 | 135 | 50 | 20 | 65 | 35 | 17 | 134 |
| Science Robotics | 274 | 274 | 44 | 48 | 178 | 245 | 16 | 274 |
| T-RO | 554 | 554 | 132 | 97 | 317 | 521 | 250 | 554 |

“母集”是 venue 内采到的全部论文版本；“直接候选”是当前词表与语境自动筛出的具身智能工作，并非最终趋势结论。DBLP/Crossref/Semantic Scholar 只承担发现或字段补全；严格同行评审标签仍需官方 proceedings、OpenReview 最终录用或出版社文章页。

## 严格官方容器对账

| 容器 | Venue | 实际条目 | 预期条目 | 状态 | 正式日期 |
|---|---|---:|---:|---|---|
| [rss20](https://www.roboticsproceedings.org/rss20/) | RSS 2024 | 134 | 134 | 完整 | 2024-07-15 |
| [rss21](https://www.roboticsproceedings.org/rss21/) | RSS 2025 | 163 | 163 | 完整 | 2025-06-21 |
| [pmlr-v270](https://proceedings.mlr.press/v270/) | CoRL 2024 | 264 | 264 | 完整 | 2025-01-12 |
| [pmlr-v305](https://proceedings.mlr.press/v305/) | CoRL 2025 | 263 | 263 | 完整 | 2025-10-07 |

四个静态官方容器共 824 条，条目数逐容器完全一致后才入“严格官方”层。RSS 2026 等只有 accepted list、尚无 proceedings 的单元将单列 pending，不混入严格覆盖率。

截至截点另有 2951 条 ICRA 2026 官方 program 记录和 210 条 RSS 2026 官方录用记录。前者可能含 RA-L/T-RO/RAM 展示，后者尚待 RSS 22 proceedings；两类均进入发现母集，但严格覆盖率分子为 0。

## 当前 15 个研究方向

| 编号 | 方向 | 层级 | 代表检索表达 |
|---|---|---|---|
| D1 | [具身基础模型与通才策略](/frontiers/foundation-models) | model_and_system | vision-language-action、vision language action、vla model、robot foundation model、robotic foundation model |
| D2 | [分层推理、规划与记忆](/frontiers/reasoning-planning) | model_and_system | system 1、system 2、system-1、system-2、fast-slow |
| D3 | [世界模型与预测控制](/frontiers/world-models) | model_and_system | world model、action-conditioned video、action conditioned video、robot video prediction、latent action |
| D4 | [灵巧、双臂与接触操作](/frontiers/dexterous-manipulation) | physical_capability | dexterous、in-hand、in hand manipulation、bimanual、dual-arm |
| D5 | [人形、运动与全身控制](/frontiers/humanoid-whole-body) | physical_capability | humanoid、whole-body control、whole body control、whole-body manipulation、whole body manipulation |
| D6 | [导航与移动操作](/frontiers/navigation-mobile-manipulation) | physical_capability | mobile manipulation、mobile manipulator、visual navigation、vision-language navigation、vision language navigation |
| D7 | [人机协作与交互学习](/frontiers/human-robot-interaction) | physical_capability | human-robot interaction、human robot interaction、human-robot collaboration、human robot collaboration、shared autonomy |
| D8 | [策略学习与优化](/frontiers/policy-learning) | learning_and_infrastructure | robot learning、imitation learning、reinforcement learning、diffusion policy、flow policy |
| D9 | [数据引擎与人类视频学习](/frontiers/data-engines) | learning_and_infrastructure | robot dataset、robotics dataset、data engine、data scaling、large-scale robot data |
| D10 | [仿真、合成数据与 Sim-to-Real](/frontiers/simulation-transfer) | learning_and_infrastructure | sim-to-real、sim2real、simulation-to-reality、simulation to reality、synthetic robot data |
| D11 | [动作关联的空间感知与表征](/frontiers/spatial-perception) | learning_and_infrastructure | affordance、actionable 3d、actionable representation、spatial reasoning、robot perception |
| D12 | [评测、安全、可靠性与故障恢复](/frontiers/safety-evaluation) | learning_and_infrastructure | robot benchmark、robotics benchmark、benchmark suite、embodied benchmark、policy evaluation |
| D13 | [持续学习、部署学习与自改进](/frontiers/continual-deployment-learning) | learning_and_infrastructure | continual robot learning、continual learning for robot、self-improving robot、self improving robot、learning from experience |
| D14 | [多机器人协同与群体智能](/frontiers/multi-robot-coordination) | physical_capability | multi-robot learning、multi robot learning、multi-robot coordination、multi robot coordination、collaborative vla |
| D15 | [触觉、力觉与多模态身体感知](/frontiers/embodied-multisensory) | learning_and_infrastructure | visuotactile、vision-tactile、vision tactile、tactile-language-action、tactile language action |

方向数不再预设。主方向只回答“论文最主要解决什么”，同一工作仍可拥有次方向、能力标签、基础设施标签和成熟度标签。新增方向是否进入月度主导航，要同时满足样本规模、跨月连续性、独立团队和回归集精度。

## 可复算数据

- [arXiv 母集 JSON](/embodied-ai-radar/preprints.json)
- [正式发表母集 JSON](/embodied-ai-radar/publications.json)
- [严格官方 proceedings JSON](/embodied-ai-radar/official-proceedings.json)
- [官方 program / pending JSON](/embodied-ai-radar/official-programs.json)
- [GitHub 证据 JSON](/embodied-ai-radar/repositories.json)
- [canonical works JSON](/embodied-ai-radar/works.json)

## 仍需继续补齐的部分

- IEEE Xplore、Science 与 SAGE 的 DOI 已进入发现母集；严格标签要继续逐条回到出版社页面核验。
- ICRA/IROS 的 PaperCept 节目单可能含 RA-L 转投展示，canonical 合并时必须避免双计。
- 分类规则持续通过正例、边界例和反例回归；每次规则变化都会单独记录，不能把分类迁移误写成趋势变化。
