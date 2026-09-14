# 硬件覆盖重建与交接 · 2026-09-14

## 结论与边界

旧设备频次页不是全库统计：原权威表只有33项研究、163条使用关系，其中正式纳入29项研究、147条关系。用户所说的42,720是canonical work总库，不能用它暗示设备证据已覆盖同等数量。

本轮完成**全库逐项账本和元数据筛查**，没有完成42,720篇全文阅读。正文处理与使用证据仍需持续补齐。现有网页频次只描述已登记的直接使用证据，不代表总体硬件流行度。

| 层次 | 全库 | 已纳入研究 |
| --- | ---: | ---: |
| canonical work分母 | 42,720 | 9,992 |
| 已筛查标题及可用摘要 | 42,720 | 9,992 |
| 缺少摘要 | 1,638 | 426 |
| 元数据出现当前字典名称线索的研究 | 1,954 | 832 |
| 本轮尝试获取正文的研究 | 152 | 116 |
| 主文结构检查通过、文本可用 | 134 | 100 |
| 仅部分正文文本可用 | 7 | 7 |
| 获取失败或暂不可用 | 11 | 9 |
| 本轮正文尚未尝试 | 42,568 | 9,876 |
| 已有已核验使用关系的研究 | 57 | 53 |
| 已核验使用关系 | 224 | 208 |

“正文尚未尝试”是新采集账本的状态；某研究此前已有一条使用关系，不代表新正文流水线已处理该研究，也不代表整篇核验完成。主文结构可用不是图片、补充材料或全文人工阅读证明。134项早期缓存未保存传输退出码，公开标记`legacy_unrecorded`，不能追认其传输审计通过。新请求则明确保留完整性，错误或截断不升级为完整文本。

## 本轮增加了什么

- 263条版本化硬件发现字典：150条明确型号、113条系列或待明确配置；覆盖九类设备，不包括电机、关节模组、电路和仿真软件。
- 每个canonical work都有唯一覆盖记录，包括未纳入研究和无命中记录；缺失、失败、未尝试与零名称命中分开。
- 第一批正文按15个方向、最近月份与稳定分散样本安排，另纳入不同相关性状态的对照。不是只从已命中G1的论文中挑样本。
- 30项研究的相关章节经AI辅助核对，其中24项新增61条使用关系；另6项只记录“所读章节未发现明确具名使用”，不能解释为整篇没有硬件。
- 新增39条设备身份；RTX 4090与GeForce RTX 4090显式归一，RTX 4090D和旧复合工作站独立。Wuji Hand 2只有仿真证据，与旧未注明代际的WUJI手分开。
- 控制计算和物理模型参数拟合新增独立用途，不误记为模型推理。仅渲染、仿真、校准、对照基线和数据源的限制保留。
- 新页面`/hardware/coverage`：全库/已纳入双分母、按方向/月/相关性查看、精确work ID状态查询、型号提及候选与出处。`/hardware/`保留严格使用频次，并在顶部显示覆盖缺口。

## 可复算与来源

权威输入为`data/catalog/works/*.jsonl`、`data/equipment/*.jsonl`、`data/hardware-review/*.jsonl`和`config/hardware-dictionary.json`。旧`data/works.json`不是42,720项的权威库。

公开派生：

- `/api/v1/equipment/coverage-summary.json`
- `/api/v1/equipment/coverage-model-candidates.json`
- `/api/v1/equipment/coverage/works/{SHA1(work_id)前两位}.json`
- `/downloads/equipment/hardware-coverage.jsonl.gz`
- `/downloads/radar.sqlite`内`hardware_coverage`及硬件相关表

原始HTML和提取正文只保存在本地忽略目录；公开的是来源、章节定位、版本、哈希、时间与中文转述。离线重解析保留父记录，不算新网络请求。同秒纠正记录按追加顺序生效，不能被旧完整状态的字母序哈希覆盖。

## 下一批执行方式

以下均从仓库根执行，不要求付费API。全队列包含35,118个arXiv研究（包含已有一条使用关系的研究），剩余7,602个非arXiv研究仍在覆盖账本待适配来源。**建立队列不等于队列已执行。**

```bash
node scripts/run-python.mjs scripts/plan_hardware_review_queue.py --all-arxiv --output .research/hardware-coverage/queue-all-arxiv.json
node scripts/run-python.mjs scripts/collect_hardware_sources.py --queue .research/hardware-coverage/queue-all-arxiv.json --limit 100 --observations .research/hardware-fulltext/observations.jsonl --transport curl
node scripts/run-python.mjs scripts/refresh_hardware_source_scans.py
```

采集器按已保存状态续跑、全局限速、禁止重复并发；遇403/429停止本批并保留冷却时间，不绕行。失败重试需使用显式`--retry-failed`且遵守冷却。不要把正文名称命中直接导入正式设备关系：须检查方法/实验/附录，记录来源与用途后再用`import_hardware_source_reviews.py`预检及导入。

剩余重点是扩大正文源适配、消除仅摘要召回盲区、复核1,954项元数据线索以及正文新增线索，并让无命中对照持续参与。不能凭当前字典无命中将42,568项未尝试正文的工作宣布为“没有硬件”。

## 审校结论

确认并修正：样本覆盖被误解为全库；同一CPU/GPU用途混称推理；传输失败可能被正文结构检查覆盖；同秒状态纠正可能回退。

保留待确认：总体硬件召回率、无arXiv来源的正文适配、未公开型号/代际、图片视频与补充材料。它们不参与“已核验使用”数量。

可以接受：按型号去重工作数降序、真实使用与仿真重叠计数分别展示、按相关性分母并列展示。无跨设备质量评分或市场份额推断。

## 验证记录

本轮`npm test`通过：943项Python测试、166项网页交互测试、权威数据与组织审计、覆盖JSON/gzip/SQLite逐项一致性、类型检查、网站与Pagefind构建、静态站点预算和搜索运行检查。站点静态审计为0错误；其警告明确静态工具不能证明移动端LCP/CLS。

本机浏览器876×987视口下已实测全库/已纳入切换、单ID状态查询及按需标题、候选出处展开和12→24追加、设备页同页覆盖分母、浅色/深色及无整页横向溢出。未把这些检查声称为五种尺寸视觉回归或移动设备性能认证。
