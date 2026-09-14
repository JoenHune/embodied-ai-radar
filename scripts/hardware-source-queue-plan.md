# 全量正文队列规划（不启动采集）

`plan_hardware_source_queue.py` 从原始队列、本地 canonical 库、一次固定前缀的采集日志、缓存文件状态、请求状态、完整阅读回执和本地月报重新计算处理次序。不联网、不调用模型、不修改来源、相关性、阅读状态或重试冷却，也不生成研究结论。

## 用法

在项目根目录使用项目 Python 环境。以下命令只有只读规划，不会创建输出目录：

```sh
node scripts/run-python.mjs -B scripts/plan_hardware_source_queue.py \
  --queue .research/hardware-coverage/queue-all-arxiv-priority-v2.json \
  --catalog data/catalog \
  --cache-dir .research/hardware-fulltext \
  --observations .research/hardware-fulltext/observations.jsonl \
  --readings data/hardware-review/fulltext-readings.jsonl \
  --monthly-dir docs/public/api/v1/monthly \
  --output-dir .research/hardware-coverage/source-plan-2026-09-15 \
  --as-of 2026-09-15 --limit 100 --dry-run
```

去掉 `--dry-run` 才会写入这个**必须不存在**的新目录。原队列不能作为输出，也不能把输出放在输入目录内。日期和批次数必须显式给出，日期决定最近 12 个完整自然月及当前暂行月，不声称把今天的私有缓存恢复到那个历史日期。

输出：

- `inventory.json`：全清单，原有每条 job 的全部字段原样保留，ID 恰好一次，只排序。**不能交给采集器执行**，其中含保留桶。
- `first-fetch.json`：最多 `--limit` 条、本次确需首次获取且目标版本明确的工作，范围是原清单的子集，不扩大范围。保留原 job，不偷偷更换 URL 或版本。
- `ordering.json`：全量逐项的排序理由、日期、相关性、T0 证据、目标版本和缓存状态。
- `holds.json`：已读/已有正文、缓存但缺成功 state、其他或不明版本、失败待修复、历史版本未知/不一致和规划日期之后的条目。
- `report.json`：数量与集合对账、输入哈希、范围、分桶、前 20 条、当月已知版本覆盖率、本地月报来源和缺失月份。
- `plan-complete.json`：最后写入的完成标记与各文件哈希；缺此文件意味着计划没有写完，不得使用。

## 执行边界

规划器从不执行抓取。当前采集批次应自然结束后，再重新规划和检查输出；计划不是执行锁，采集日志仍可能在规划期间增长。执行前须重新确认输入队列、catalog、实际解析目标以及缓存/state 未变化，不能把旧计划长期当作待抓取清单。

`first-fetch.json` 才是有界执行输入。不要将 `inventory.json`、`holds.json` 或 `ordering.json` 传给采集器；不要因它们包含记录而扩大 `--limit` 或加入自动重试。失败项既有 `next_retry_at` 和全局 backoff 完全不变。

采集入口会拒绝带有 `source_queue_plan` 但未明确标记 `executable: true` 的清单，避免误把总清单当执行队列。这只是输入类型保护，不替代完成标记、文件哈希和当前状态核验；原来的非规划队列保持兼容。

## 口径

- 当前月和近窗可靠 T0/月报所选优先于旧 included；标题主题关键词和 G1/G2 归属只帮助取文复核，不是相关性批准。仅同组的非机器人研究没有 T0 优先保证。
- 版本未知的新工作会暂时保留在 H0。它们未被丢弃，报告明确给出数量和当月覆盖率；本规划器不会猜 v1。原采集器仍有无版本 URL 解析能力，但该能力不在本次首次获取子队列中自动启用。
- 月报选择由现存月报快照及当前 catalog 重新构建，每月保留源文件哈希、revision、data_through 与 packet 哈希；不宣称旧月报是最新选文。无 work 的组织事件只报告事件数，不新增 work。非 arXiv 工作仍在 canonical 库，不自动加入本适配器队列。
- 同版缓存只检查观察状态、传输状态、受控本地路径及文件存在/大小，不重新散列数千份 HTML。这是避免重复获取的依据，**不是完整阅读、内容一致性或缓存原文保真认证**。
- 请求键包含 work、URL/版本、解析器及阈值。无阈值的旧网络失败只接受按本次显式参数验证过的键。旧失败被维护脚本原样搬到新解析器键时，必须同时匹配既有日志的完整记录；仍作为失败隔离，不升格为成功。
- 语法损坏、重复/未知 ID、无效日期、伪造 state identity 或越界缓存路径会拒绝生成。活跃日志末尾合法但未写完的 JSON 会明确报告，原日志不修剪。

测试：

```sh
node scripts/run-python.mjs -B -m unittest discover -s tests -p test_hardware_source_queue_plan.py -v
```
