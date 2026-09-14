# 研究组归属补证：2026-09-05 第一批

本批新增 **25 条 G1 归属、覆盖 20 个 canonical work**，补回 3 个原计划必含的 T0 研究组及其母机构。仅写独立增补文件，未直接改权威 catalog。

- 9 个 work 来自此前的 100 项高信号待归属队列，离线复算有效归属分子由 31 增至 40，待归属由 100 减至 91。
- 其余 11 个 work 用于补齐关键研究系列及新增必含组的作品归属。
- 20 个 work 当前为 15 个 included、3 个 manual_review、2 个 candidate。补齐归属不等于通过相关性复核，未升级这些状态。
- 本批没有 G2：全部依据实际读取的官方实验室论文页、公司研究发布页或明确写出执行组织的项目页，不使用当前 roster 反推历史归属。

## 增补清单

| Work | 新增直接证据支持的研究组 |
|---|---|
| π0.7 | Physical Intelligence |
| CP-Gen | Stanford IPRL、UT Austin RPL |
| Cross-Embodiment Transfer via Behavior-Aligned Representations | Stanford ILIAD |
| ABC：Scalable Behavior Cloning | CMU LeCAR、Amazon FAR |
| VT-Refine | NVIDIA Seattle Robotics Lab |
| Dexplore | NVIDIA Seattle Robotics Lab |
| Ctrl-World | Stanford IRIS |
| PrioriTouch | Cornell EmPRISE |
| Isaac Lab | UT Austin RPL |
| MiniBEE | Columbia ROAM |
| SpikeATac | Columbia ROAM |
| LUCID | CMU LeCAR |
| PGDG | CMU LeCAR |
| DreamDojo | NVIDIA GEAR、UT Austin RPL |
| DreamZero / World Action Models are Zero-shot Policies | NVIDIA GEAR、UT Austin RPL |
| CaP-X | CMU LeCAR、UT Austin RPL |
| World Action Verifier | Stanford IRIS |
| VLAW | Stanford IRIS |
| RoboCasa365 | UT Austin RPL |
| SoftMimicGen | UT Austin RPL |

每条原始记录的 canonical ID、官方 URL、核验日期和短摘录均在 `data/attribution-additions.jsonl`。CP-Gen 在不同页面有长短标题版本；IPRL 使用与当前 canonical 完全一致的长标题，RPL 的条目通过相同项目链接和作者表交叉确认。

## 必含组登记缺口

新增 Cornell EmPRISE、UT Austin RPL、Columbia ROAM，均保留官方主页、论文页、负责人来源和可核验母子关系。建组日期及负责人任期起点未知，保存 null。组织信息在 `data/organization-additions.json`。

ROAM 的官方 faculty 是 **Matei Ciocarlie**。不能把 Columbia 的其他机器人工作直接归入 ROAM，也不能把 VT-Refine 中 Yunzhu Li 的同校 affiliation 当作 ROAM 证据。ROAM 的 MiniBEE 和 SpikeATac 来自[官方论文列表](https://roam.me.columbia.edu/content/publications)。

NYU GRAIL、UCSD Xiaolong Wang Group、Princeton Intelligent Robot Motion 仍是原始名单中的后续登记核验项；本批没有根据名称或其他大学的组织资料虚构其主页、负责人或论文关系。

## GEAR 漏采原因

[GEAR 官方论文页](https://research.nvidia.com/labs/gear/publications/)的静态 HTML 只有栏目骨架。论文对象位于该 HTML 明确引用的同域公开 Next.js publications chunk，包含 `title`、`authors`、`paperLink`、`projectLink` 等字段。

实际读取的 chunk 明确将 DreamDojo 对应到 arXiv 2602.06949，将 DreamZero 对应到 arXiv 2602.15922。G1 记录保留论文页 URL，并附当时版本化的资源 URL；解析过程没有执行远程代码。空 HTML 的 known_links 不能解释为“该组没有研究发布”。

已新增 `scripts/group_source_adapters.py`：只发现当前官方 HTML 引用的同源 publication/project/research 资源，额外资源域需要显式登记；支持安全的对象字面量与 JSON.parse 静态字符串解析，不执行远程代码。16 项回归覆盖表达式拒绝、跨域过滤、空页面和失败时旧链接保留、去重、Unicode 与数据来源链。对本次 GEAR 公开页面实跑解析到 45 个研究标题、134 个不同类型资源链接；这只是该页面可解析的数据，不等于全球研究发布覆盖率。

## 未升级的关系

- 3D HAMSTER 的官方项目页列 KAIST AI、POSTECH、Holiday Robotics、KRAFTON AI，不能因名称包含 HAMSTER 就归入 NVIDIA GEAR。
- Learning Latent Action World Models In The Wild 的论文明确写 FAIR at Meta；当前登记将 Meta FAIR 与 Embodied AI 跟踪节点分开，本批没有把泛 FAIR affiliation 自动升级为某个具体具身小组关系。
- ABC 的项目页明确写 Amazon FAR 和相关实习工作，支持 FAR；仅凭 Berkeley/CMU 母机构 affiliation 不会生成其他实验室关系。本批只另外使用 LeCAR 的官方论文列表补入 LeCAR。
- LeCAR 等实验室网页上的 CoRL 2026 接收标签可以支持研究组归属，但本批未将它们导入为官方主会决议或伪造完整接收列表。

## 复核结果

20 个 work ID 和所有组织 ID 均可在现有 catalog 加本批新增组织中解析；25 条记录没有重复主键。6 个组织节点通过现有组织条目 Schema，包含 3 个 T0 执行组和 3 个不占名额的母机构。全部源网址已实际读取支持内容，未使用搜索摘要单独作为新增 G1 依据。
