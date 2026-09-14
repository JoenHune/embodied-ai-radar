# T0 官方公开发布召回：独立分层回归样本

## 范围与冻结规则

本轮检查覆盖 Genesis AI、Generalist AI、Figure AI、Dyna Robotics、Sunday Robotics、NVIDIA GEAR、Physical Intelligence、CMU LeCAR、Pathak Research Group、Google DeepMind Robotics、TRI Robotics、RAI Institute 共 12 个指定研究执行单元。发布窗口为 2025-09-01 至 2026-08-31，按 Asia/Shanghai 自然日判断，共冻结 24 条公开发布，每组 2 条。

这是一个来源独立、分层选择的回归样本，不是 69 个 T0 的完整普查，不是互联网全部相关工作的全集，也不是可向全集外推的随机抽样召回率。每组取两条，不表示其他发布已经完整收录。每条保留原始标题、官方发布或论文 URL、发布日期、官方索引来源、采集时间、原文摘录及 HTTP 响应体 SHA-256；共捕获 38 个不同来源响应体。先完成官方来源取样并冻结，再读取 catalog 进行匹配，未从既有入库结果倒推样本。

冻结文件为 `data/coverage-gold-releases.jsonl`，原始文件 SHA-256：

`a8291aabe825391e02b4223cfb5129b69f9f08a9269430ca8a77fef90964819d`

审计程序另对解析后的规范化 JSON 计算语义哈希，因此报告中的 `gold_hash` 与上述原始文件哈希不同。这不是样本变更。后续修复应保持这 24 个 `gold_id`、标题、URL、日期及采样成员不变，重新运行同一个审计；不得为达到 95% 删除漏项、重复项或观察类发布。新增扩展样本应另建有版本的采样框。

## 实际采样步骤

1. 从各组官方 publications、research、blog 或 resources 索引开始，先记录符合时间和研究范围的发布，再检查其独立发布页。
2. 公司、PI、DeepMind、RAI 选择官方索引中最近两项有日期、与研究或技术落地相关的发布；纯融资、招聘、投资者风险提示等不在本轮发布范围。Figure 的 BMW 部署和 Dyna 的客户部署仍保留，但归为部署观察，不冒充同行评审论文。
3. GEAR 使用官方 publications 高亮条目顺序，取前两项首次公开日期位于窗口内的工作。高亮顺序不是全量发布日期降序，不声称是 GEAR 最近两篇论文。
4. LeCAR 的本轮学术子层是直接机器人控制/操作贡献；按官方列表顺序排除通用综述或纯理论条目后取前两项。Pathak 的子层是机器人世界模型/控制贡献；在读取库之前排除通用物理问答或文本反馈大模型条目后取前两项。两者均不是实验室全方向普查。
5. TRI 使用官方 publications 的 Robotics 分类（页面实际选项值为 18），不是未过滤的能源材料或其他部门成果；选取窗口内前两项。
6. 源网页依赖公开前端数据时，同时记录官方数据资源 URL 和响应体哈希，例如 GEAR publications 数据及 LeCAR 项目资源。HTTP 重定向只记录真实观察到的目标，不以相关链接代替等价 URL。

早期个别网页读取方式返回 403，之后普通公开 HTTP GET 可读取并保存哈希与摘录；本轮冻结行没有未解决的抓取缺口。这不代表这些来源在持续采集中永远健康。将来无法访问的来源应保留 `source_gap` / `access_gap`，其含义是未知，不能解释成该组发布了零项工作。

## 发布类型和时间口径

24 条中，21 条为论文、技术报告、模型报告、数据报告或基础设施报告；另外 3 条是观察发布：Figure BMW 部署、Dyna 客户部署、RAI Koala 视频。整体和两个子层各自报告分母，观察发布不进入研究证据成熟度计数。

论文保留 arXiv 首次公开 UTC 时间；只有年月日的公司报告保留 day 精度，不伪造具体时刻。官方发布页日期与 canonical work 首次公开日期是不同事实：TRI 的 SAFE 官方条目发表于 2025-10-30，但工作首次公开在 2025-06；不能因此将它计成十月新增工作。PI RLT 官方报告日期 2026-03-19 早于当前 arXiv 工作日期 2026-04-24，经身份复核后应修订首次公开日期并保留三月/四月快照修订记录。

实验室自行标注会议名称只用于发现，不是本轮同行评审验收证据。例如 LeCAR 页面中的 CoRL 2026 标签，不会通过这份召回金标准自动升级为官方接收结论。

## 身份匹配与指标定义

审计入口 `scripts/audit_release_recall.py` 是只读纯计算，不改 catalog。硬匹配只接受规范化官方 URL、去版本 arXiv ID、DOI、已核验历史 alias，或真实观察到的官方 HTTP 重定向目标。URL 规范化去除跟踪参数、片段、尾斜线并处理标准点路径；不能将任意相关项目 URL 当成同一发布。精确规范化标题仅产生 `title_candidate`，不直接取得召回分数；模糊标题不用于身份判定。

几个分开报告的指标分别回答不同问题：

- `release_url_present`：原始来源/版本表中是否存在这个官方发布 URL，即使尚未唯一绑定工作；这是链接回执覆盖率。
- `canonical_work_present`：是否有 URL/ID 的工作硬回执；多个 canonical 命中表示有数据但身份冲突，因此计“存在”，不计“唯一解析”。
- `canonical_identity_resolved`：硬身份是否唯一确定，重复 canonical 不能算通过。
- `release_captured`：该发布 URL 是否唯一绑定到 canonical work。已有论文不等于新模型/报告/视频链接已捕获。
- `formal_visible`：发布唯一可追溯且关联工作为 `included`。`candidate`、`manual_review`、`excluded` 均保留在库中但不暗示默认界面可见。

状态包括 included、candidate、manual_review、excluded、ambiguous、title_candidate、known_work_missing_release、unlinked_source、missing，分母保留所有冻结发布。`missing` 的准确含义是“本次机器规则没有找到相符身份”，不是证明语义上不存在同一工作。身份复核可找到尚未入库的官方映射，修复前仍保留原机器基线。

## 首次运行基线：未修复目录

目录哈希：`22e75cac546c7434f7c51d0a207c07eb964f368170d4fa7683cee644d72561ab`。完整结果保存在 `research/coverage-gold-audit-2026-09-06.json`。

| 指标 | 全部发布 24 项 | 研究发布 21 项 | 观察发布 3 项 |
| --- | ---: | ---: | ---: |
| 官方 URL 有回执 | 17/24（70.8%） | 16/21（76.2%） | 1/3（33.3%） |
| canonical work 有硬回执 | 17/24（70.8%） | 16/21（76.2%） | 1/3（33.3%） |
| 唯一 canonical 身份 | 12/24（50.0%） | 11/21（52.4%） | 1/3（33.3%） |
| 发布 URL 唯一绑定 | 12/24（50.0%） | 11/21（52.4%） | 1/3（33.3%） |
| included 且发布唯一可追溯 | 10/24（41.7%） | 9/21（42.9%） | 1/3（33.3%） |

24 条机器状态为 10 included、2 manual_review、5 ambiguous、5 missing、2 title_candidate。不能把所有 12 个未唯一匹配的状态笼统称为“漏了 12 篇论文”。

| 研究组 | 两条样本的首次机器状态 |
| --- | --- |
| Genesis AI | 2 ambiguous，同一 URL 被 artifact/report 重复建档 |
| Generalist AI | 2 ambiguous，同一 URL 被 artifact/report 重复建档 |
| Figure AI | INDEX included；BMW 部署 missing |
| Dyna Robotics | 2 included |
| Sunday Robotics | 2 included |
| NVIDIA GEAR | EgoScale included；DreamDojo manual_review |
| Physical Intelligence | π0.7 ambiguous；RLT 官方报告 missing |
| CMU LeCAR | FADA included；WANDA manual_review |
| Pathak Research Group | ViPRA included；LPWM missing |
| Google DeepMind Robotics | Robotics 2 included；ER2 发布 missing |
| TRI Robotics | SAFE、RoLA 均为 title_candidate |
| RAI Institute | 乒乓球论文 included；Koala 后续视频 missing |

本轮独立样本不满足 95% 的严格发布绑定验收。DreamDojo 与 WANDA 已有数据，只是待相关性复核；不应为了默认可见率把它们无条件改为 included。

## 身份与缺项复核：修复建议，不自动改库

`research/coverage-gold-identity-reviews.json` 保存 5 组可核验合并建议及每个 canonical 的 ID、标题、版本类型、研究组、日期和来源。Genesis World、GENE-26.5、GEN-1.5、Thousand Hands 的重复来自索引卡片全文被当成新工作标题；π0.7 的官方博客与 PDF/arXiv 为同一模型报告贡献。应合并明确身份并保留旧 ID、来源、版本、组织关联和 lineage，不采用“凡共享 URL 就批量合并”的规则。

两项 TRI 标题候选已在独立复核中取得官方项目页到 arXiv 的直接链：SAFE 为 `arxiv:2506.09937`，RoLA 为 `arxiv:2509.22970`，且标题/作者一致。它们不是缺失论文，而是官方发布链接尚未关联。侧文件提供证据，审计不会偷偷读取该侧文件抬高既有目录成绩。

机器未匹配的五项分别为：

- Figure F.03 BMW：现有 Helix 02/Figure 03 产品系列的部署发布，应补部署版本/事件，不冒充新同行评审成果。
- PI RLT：官方 PDF 与现有 `arxiv:2604.23073` 标题和全作者一致，应补三月报告及 PDF 链接并修订首次公开日期，不新建重复工作。
- Pathak LPWM：直接标识 `arxiv:2603.04553` 在本轮目录中不存在，是已确认的论文采集缺项；应按正常相关性和归属规则导入。
- DeepMind ER2：官方模型发布与 Robotics 2 同产品家族但模型输出不同；应补 ER2 模型/报告 URL，并审阅它是独立贡献还是父项目版本，不能仅因同公司同日就强制合并。
- RAI Koala 视频：既有 `arxiv:2608.20546` 与官方项目页证明同一硬件研究项目；8 月 29 日视频 ID 与论文项目视频不同，应作为后续视频发布保留。它没有因此产生独立验证证据，也不从样本删除。

身份修复后，由主流程更新规范数据，再对同一冻结样本重跑；首次基线报告不覆盖。新报告应同时展示改善来自补 URL、身份合并、真正补采还是相关性人工复核。

## 验证与边界

只读复算：

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/audit_release_recall.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p test_release_recall.py
```

`config/coverage-gold-release.schema.json` 校验冻结发布；专项测试覆盖漏项不缩分母、标题不冒充身份、重复身份、缺发布链接、当前不可见状态、仅来源回执、观察层分离、真实重定向和纯计算确定性。

来源响应体只保留哈希、字节数与必要摘录，不镜像全部官方 HTML/PDF。这能检测后续内容变更并复查摘录，但不保证离线重建完整历史网页；若要长期审计，应另建立合规的原文快照存档。每组两项不检验全部 T0 的来源适配器，也不能直接验收 95% 全量覆盖；下一轮应在不改变本轮成员的情况下，扩充其余 T0、纳入各组所有窗口内官方发布并逐项保留 access_gap。
