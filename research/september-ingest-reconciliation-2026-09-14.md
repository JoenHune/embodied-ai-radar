# 9月导入与上下文事件对账

核验完成：2026-09-14 04:19 UTC。只读检查研究数据；本轮仅补测试及本报告，未修改业务脚本、研究记录或运行导入。

## 数量结论

不是568条输入漏了1条。准确关系为：

- **568条唯一arXiv输入 = 561个新增canonical + 7个旧canonical的新标识映射。** 568条全部匹配，映射到568个不同canonical，无缺失或一对多歧义。
- **42,153 + 561 + 6 = 42,720。** 比较重建前的旧版work分片与当前权威库，新增567、删除0；额外6项是自动组更新形成的待复核抓取条目，不能算6篇新增论文。
- 额外6项均为`manual_review`，未进入`included`研究数。

核验依据：本轮重建前的`docs/.vitepress/dist/api/v1/catalog-manifest.json`及`works/*.json`（42,153，截止2026-08-31）；当前`data/catalog/works/*.jsonl`、`work-aliases.jsonl`、`data/group-updates.json`；采集阶段的`verified-cohort-september-2026.json`（568条）。**dist随后已由主线程重建为42,720，不应再把当前dist当作旧基线重新相减。**

568条采集文件SHA-256：`e98bc87817336d6725d02b31c870bcac4fc9d5270a9724338552760160ec23d0`。

## 7条旧canonical映射

| 新arXiv标识 | 保留的旧canonical | 论文 |
|---|---|---|
| 2609.03680 | `title:8faa3de13d783aaab82f224c` | DropClick: Semi-Automated One-Click Segmentation for Agricultural Robotic Data |
| 2609.05596 | `title:60e0c8dda5355ff97766091b` | Time-Aware Assistive Navigation |
| 2609.07109 | `title:d1c18202f1c406b88da0fbc4` | Eventually Optimal and Scalable Multi-Agent Planning for Block Cave Mining |
| 2609.08220 | `title:190469835195ff2485393f44` | Bridging Language and Physics: Automated Design of Continuum Robots with Large Language Models |
| 2609.08804 | `title:581f5e02b90d480c01e3c9da` | Real-Time Puncture Detection and Recovery for Pneumatic Soft Actuators |
| 2609.10400 | `doi:10.1177/02783649261470035` | A traffic management system for large and heterogeneous vehicles in narrow industrial environments |
| 2609.12971 | `title:05ecf4a52d6d086e9ce46fdb` | Tuning ROS 2 for Energy-Efficient Navigation: Empirical Insights from Costmap 2D Configurations |

以上为6个旧标题身份与1个旧DOI身份，不是“只有1个旧报告alias”。新arXiv标识保存在`identifier_aliases.arxiv`及`aliases`。DOI记录保留首次公开日期2026-08-07；6个旧标题记录的原首次公开日期仍未知。本次未据新上传日期改写旧记录的首次公开日期。

## 额外6条抓取记录

| 新canonical | 抓取标题 | 原组更新ID |
|---|---|---|
| `artifact:ca704fe2b5d97d9fc463` | Blog | `group-update:991e63daa66049db` |
| `artifact:9a89cb64f07b281202c1` | View Publication | `group-update:789242b2fec4f6e5` |
| `artifact:84e945b9a23efc51a147` | Northeast Robotics Colloquium | `group-update:e00a5b1fceeee162` |
| `artifact:98106a8ac3bb557f3fc0` | Newsroom / AGIBOT摘要 | `group-update:53d64a438319ec6b` |
| `artifact:f3e960eff9f6e89270d1` | View model card | `group-update:0f2f0e4cd6d08ec7` |
| `artifact:00919efcbdc467896873` | CAD Modeler San Carlos, California | `group-update:2f315facd421cf11` |

这些来源原被标记为`preprint`和来源归属`G1`，但标题包括导航按钮、活动和职位。来源归属不等于已核验论文身份。应保留审计轨迹并复核提取/分类；本报告没有自动删除、改类或promote。它们也**不是**本轮6条已审阅的S层上下文事件。

## IHMC与上下文事件边界

- `arxiv:2606.26425`：2026-06-24，单作者Duncan William Calvert的学位论文。
- `arxiv:2609.01518`：2026-09-01，Duncan Calvert等7位作者的论文。
- 两者标题相同但canonical、作者表、日期及alias均独立；没有相互合并。
- 本轮已审动态为**6条事件、5种类型**：`strategic_partnership`、`research_explainer`、`deployment_update`、`technology_deployment_update`、`code_release`（两条版本发布）。它们保留S层和非研究计数标记，不能充当新增论文或模型。

## 回归验证

- 两个旧隔离fixture已显式创建设备四张空表，不放宽正式构建缺authority即失败的保护；原5项与11项测试均通过。
- 新增`tests/test_observation_updates.py`共15项测试：覆盖所有类型的有/无关联work、不新增work或manifestation、不移动原日期、S层非研究计数、6条事件整链路幂等、冲突及证据校验。
- 新测试发现的两处业务字段问题已由主线程修复：保留`original_research_eligible`原始值；事件导出保留`counts_as_new_paper`和`counts_as_new_model`显式False。
- 主线程另修复了无work事件在增量导入中丢失的问题：S事件带精确`source_record_id`，已拥有来源的恢复要求payload hash一致且事件已核验。新增测试验证完整`migrate → reconcile → ingest_delta → finalize`冷导入与重放恢复，拒绝candidate、非S、hash不一致及未注册来源；既有事件只补缺字段，不覆盖人工说明或日期。15项专题测试全通过。
- 最终全量Python回归：**826项通过**。未运行生产导入、提交、推送或部署。
