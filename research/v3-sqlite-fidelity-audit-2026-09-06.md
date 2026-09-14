# SQLite 下载件逐字段保真审计

审计日期：2026-09-06。审校方式：Codex AI 本地只读核对；不是人工专家批准、独立研究验证或网络来源再采集。

审计对象：`data/catalog` 的 16 个 JSONL 权威表（含分片），以及 `docs/public/downloads/radar.sqlite`。本次读取的 SQLite 为 **471,527,424 字节**，权威库 `catalog_hash` 为 `9e244d6511b74838db8ba54702df53c2682661fd83e317760633dd937b0dd59c`。SQLite 连接使用只读模式；未编辑或重建下载文件。

## 结论

**当前 SQLite 是可查询的研究下载件，不是可无损还原全部权威 JSONL 与编辑档案的备份。** 不能以主表行数一致宣称所有字段与关系保真。主要问题是日期精度、组织树及人员任期、G2 归属边界、字段来源依据没有完整保存；另有一处分类记录被导出阶段重新生成、改变原值的问题。

本轮已确认的分类导出 P1 将仅修复生成代码，并增加逐值、多重集合回归；本报告中对现有 SQLite 的观察仍是**修复前下载件**，需主任务重建后重新审计。其余完整性问题本轮不修改。

## 对账方法

- 有完整 `payload_json` 的表，解析 JSON 后规范化键顺序，用逐记录哈希的多重集合比较，包含重复记录数量；不是只比较计数。
- `work_payloads` 视图逐作品核对权威记录的每个原始字段，避免把规范化存储误报为字段丢失。
- 只有标量列的表，对照实际权威字段及 SQL 列映射；分类记录另外逐 `(work_id, axis, code)` 比较值。SQLite 的 `is_primary` 整数明确还原为布尔后再比较。
- 对 G2 的 `membership_evidence`，额外扫描全部现有完整 JSON 存储表，未找到可用副本。组织覆盖派生矩阵不能代替原始归属/组织实体表。
- 容量估算以实际权威 JSON 编码字节数计算；压缩数为内存 zlib 测量，不是承诺 SQLite 文件或部署包的实际增量。

## 逐表结果

| 权威表 | 权威 / SQLite 行数 | 字段级结果 |
|---|---:|---|
| `works` | 42,153 / 42,153 | 公共字段可经 `work_payloads` 还原。另有内部管理哈希省略、8 条已知中文编辑覆盖；见下文，不应误报成作品缺少完整 payload。 |
| `manifestations` | 48,697 / 48,697 | 不完整：日期精度、发表状态、track 及部分版本/审校来源字段丢失。 |
| `organizations` | 200 / 200 | 不完整：父子关系、负责人及其有效期/出处、官方 URL 分类、别名等丢失。 |
| `work-organization-links` | 276 / 276 | 不完整：12 条 G2 人员时间证据及其它归属依据未完整保存。 |
| `source-records` | 174,847 / 174,847 | 逐记录完整 JSON 多重集合一致。 |
| `field-provenance` | 302,310 / 302,310 | 不完整：所有记录的 `basis` 丢失，另有审校/旧 ID 字段丢失。 |
| `work-aliases` | 52,185 / 52,185 | 逐记录完整 JSON 多重集合一致。 |
| `evidence-events` | 1,137 / 1,137 | 逐记录完整 JSON 多重集合一致。 |
| `editorial-claims` | 0 / 88 | SQL 中是导出生成的编辑判断，不是当前空权威表的镜像；完整月报编辑对象也不在 SQL 中。 |
| `work-relations` | 9,276 / 9,276 | 逐记录完整 JSON 多重集合一致。 |
| `reconciliation` | 93,862 / 93,862 | 逐记录完整 JSON 多重集合一致。 |
| `taxonomy-assignments` | 117,547 / 117,547 | 字段齐但原值变了：94,242 条记录与权威记录不一致；属于 P1。 |
| `source-health` | 150 / 无原始表 | 只有其它派生结果，不能恢复含 `known_links`、内容哈希及失败历史的原始记录。 |
| `organization-candidates` | 553 / 无原始表 | 发现池的候选、歧义说明、待核验动作和证据工作列表未完整保存。 |
| `text-snapshots` | 32,207 / 32,207 | 逐记录完整 JSON 多重集合一致。 |
| `report-text-snapshots` | 1 / 1 | 逐记录完整 JSON 多重集合一致；单份试点不代表全部公司报告已具备正文档案。 |

## 具体问题与可复现样例

### P1：分类导出改变权威值

`scripts/build_v3_catalog.py` 的导出块先清空 `taxonomy_assignments`，随后从 `works`、`relevance` 和当前 `VERSION` 重算，覆盖权威表已有的置信度与分类版本。

- 117,547 条记录中，94,242 条记录至少一个字段变化。
- `confidence` 改变 94,242 次；`classifier_version` 改变 84,720 次。
- 当前权威 `(work_id, axis, code)` 没有重复键；比较并未被去重或排序误差干扰。
- 例：`arxiv:2407.03245` / `capabilities` / `bimanual_manipulation` 的权威值为 `confidence="accepted"`、`classifier_version="3.0"`，SQL 为 `"lexical"`、`"3.1"`。

最小修复：导出直接使用 `payload['taxonomy-assignments']`，不在导出阶段重新分类或补写置信度/版本。该表现有六字段本可由标量列保存；修复原值不需要新增重复 payload，也不意味着 `accepted` 是人工批准。

### P1：日期精度与发表身份不足以还原

Manifestation 缺失字段的记录数：

- `date_precision`：39,227；`publication_status` 与 `track`：各 48,697。
- `date_source_record_id`：15；`date_history`：2；`original_source_record_id`：2。
- `evidence_layer`、`observed_at`、`research_eligible`、`review_id`：各 13；另有 `title` 25、`asset_id` 3、`version` 1。

例：Dyna-2 的 `manifest:2b1df35386e9c88c3276` 和部署报告的 `manifest:4a80d2b2f2a67bd27e86` 在 SQL 中都只剩 `published_at="2026-08-01"`。权威数据明确为 **month 精度**，并保存从旧 8 月 15 日/27 日修正的日期历史与审校来源。仅依 SQL 主表的日期容易被误解成精确日。相关来源记录虽仍存在，也不能代替每个 manifestation 的明确日期选择与历史关系。

正式发表记录的 `status` 与布尔 `peer_reviewed` 被保存，但这不等于完整保存其发表身份、精度和版本层 provenance。不能凭此把“venue + year”恢复成正确的逐版本评审口径。

### P1：组织与 G2 归属不能完整复算

200 个组织均缺 `parent_relations`、`leaders`、`official_urls`、`aliases`、`active_from/active_to`、`tracking_unit`、`status` 等权威字段。8 个标量列保存名称、层级标签和地区，不足以还原组织树、负责人任期或官方来源。`report_coverage` 中的祖先路径及来源检查只是部分派生投影。

276 条工作归属均缺 `attribution_basis`、`verified_at`；12 条缺 `membership_evidence`。另有 121 条的 `source_record_id`/源摘录、85 条的补充来源 URL、114 条批次信息等没有完整保存。

例：`title:d245a5b2b1caf2781699781b` → `org:hkust-gz-jie-song` 的 G2 证据包含作者 Linyi Huang、官方人员页、保守有效期 `2024-10-01` 至 `2026-09-05`，以及原始入组信息只精确到月的说明。SQL 的 G2 标签与 URL 无法恢复这些时间边界。另一例 `arxiv:2607.29569` → `org:psu-carl` 保存了原始年精度与保守有效起点，SQL 同样缺失。

全库现有 payload 表中未找到 `membership_evidence` 副本；这不是“字段藏在另一个 JSON 列”的误报。

### P2：字段来源依据和发现/健康状态不完整

FieldProvenance 保留 `(work_id, field, source_record_id, observed_at)` 四列，但全部 302,310 条的 `basis` 被省略；另有 85 条 `review_id`、2 条 `original_work_id`。例如 StemVLA v1 的摘要、作者、标题来源虽可追到版本源 ID，具体的字段赋值依据不能从该关系表直接恢复。

150 条原始 source-health 记录与 553 条 organization-candidates 记录没有原始表镜像。派生覆盖看板不能还原 source-health 的 `known_links`/内容哈希/失败日期，也不能还原候选发现池全部歧义与下一步核验状态。

### 编辑层与作品还原边界

- `work_payloads` 已保存作品公共结构，不建议重复存全库作品正文来修本轮问题。
- 所有 42,153 条作品的内部 `_managed_field_hashes` 被主动省略；这是增量更新操作状态，不应混同研究事实缺失。但若承诺“逐 JSONL 完全恢复仓库权威库”，它也必须纳入契约或明确排除。
- 8 条作品的 `title_zh`/`summary_zh` 与权威原值不同，来自已保存的中文编辑覆盖；原始外文标题/摘要等未因此丢失。若需要精确恢复原始 JSONL 的旧中译值，还需单独保留基线，而不能只返回最新展示译文。
- 当前权威 `editorial-claims.jsonl` 为零行，SQL 的 88 行为导出生成判断，因此不能把这 88 行说成该权威表的无损镜像。
- SQL `editorial_claims` 仅保存 claim ID、月份、kind、text、支持/反例 ID 和 generator。完整月报的 D/Q 摘要、数值引用结构、原响应 ID、输入 digest、post-edit review 链不在该表；作品 payload 中也没有 `post_edit_reviews` 副本。当前已审校 8 月编辑 artifact 仅 45,941 字节，补存完整编辑对象的成本很小。

## 补齐容量估算

以下按实际记录规范化 JSON 计算，均不含 SQLite 页面/索引开销：

| 补齐方式 | 原始 JSON 字节 | 内存压缩测量 |
|---|---:|---:|
| 六类不完整权威表全部补存原始 payload：manifestations、organizations、work-organization-links、field-provenance、source-health、organization-candidates | 70,189,142 | 8,674,178 |
| 上述表仅补现有列未覆盖的字段 | 约 14,154,376 | 未作为可独立恢复包测量；仍需处理原键是否存在、行绑定等细节 |
| 若还要求保存作品内部 `_managed_field_hashes`（含绑定 work ID） | 44,251,425 | 9,859,525 |
| 当前 8 月完整编辑 artifact | 45,941 | 未单独测量 |

实用路线：在已有不完整关系表补 `extra_payload_json`/可恢复视图，或仅对这些表补原始 payload；不要重复已有完整 source/text/work 正文。前者额外原始内容约 14.2 MB、加页面开销预计为若干 MB；后者约 70.2 MB 起。分类原值修复可使用已有六列，基本无额外容量。压缩数据是测量参考，不能直接当作未来 SQLite 增量或 GitHub Pages 包体结果。

若要保证连内部管理状态都能恢复，应另外计入约 44.3 MB，并重新验证部署包体预算。否则应明确称为“公开研究数据下载”，而非完整仓库备份。

## 后续验收建议

1. 以权威表为分母，对每个表定义恢复函数，比较规范化完整记录的多重集合；主键表也检查未知/缺失键及原值。
2. 保留原表顺序或稳定行标识，避免无主键关系表的不同证据行被 `INSERT OR IGNORE` 或去重合并。
3. Dyna 月精度、12 条 G2、组织负责人任期与父子来源、审校后的编辑链设为下载回归样例。
4. 将“最新展示译文”“原始权威字段”“编辑修订档案”分开，避免为了展示覆盖原始可恢复数据。
5. 补齐后再测 SQLite 实际体积、压缩下载体积与完整部署包体；本报告不宣称其它 SQL 缺口已经修复。
