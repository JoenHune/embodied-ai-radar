# 会议正式证据源

`corl-2026/records.jsonl` 只保存官方 OpenReview 主会已接收且公开的 forum。
`source-status.json` 是覆盖状态的权威来源：`complete=false` 时不能从文件条数推断当年接收总数，空文件表示尚未取得已核验快照。

主会 group 和 accepted venue ID 均从 `config/conference-editions.json` 读取。接口按官方文档用 `content.venueid` 获取已接收稿件，分页校验 `count` 后逐 forum 获取公开 reviews、meta-reviews、rebuttals 和 decisions。Workshop、作者自述接收、非公开 notes 都不能升级为主会接收。

```sh
python3 scripts/collect_corl_openreview.py
python3 -m unittest discover -s tests -p 'test_corl_collector.py'
```

采集失败默认写状态并正常退出，以便周更仍能发布已有研究数据；要求完整会议快照的独立作业可以加 `--require-complete`。401/403 不重试、不解验证、不使用私有账户。分页不足、数量变化、重复 ID、冲突决定、未公开结果都保留旧快照。连续两次失败显示 stale warning。

## 官方导出导入

如公共 API 受限，可由正常获得官方公开导出的操作者提供 JSON 文件。导入器不接受镜像整理的标题列表，也不接受已经归一化的所谓“接收结果”。导出须保留原生 API v2 notes、公共 readers、正式 venueid 和官方 group 元数据，并提供以下 envelope：

```json
{
  "schema_version": "openreview-public-export-v1",
  "source_url": "https://api2.openreview.net/notes?content.venueid=robot-learning.org%2FCoRL%2F2026%2FConference",
  "exported_at": "<UTC export timestamp>",
  "group": {"id": "<official group id>", "readers": ["everyone"], "content": {}},
  "notes": [],
  "count": 0,
  "complete": true,
  "forum_notes": {
    "<forum id>": {"notes": [], "count": 0, "complete": true}
  },
  "invitations": []
}
```

上面的空列表仅说明格式，不是论文数据。`count` 必须是官方 accepted-venue 查询的总数；`notes` 必须合并全部分页，每个 forum 也须带完整分页的公开回复和对应 count。`invitations` 可保存公开评分表定义；取不到时 `scale_status=unavailable`，评分原文保留但不进行跨年归一化。

```sh
python3 scripts/collect_corl_openreview.py --official-export /absolute/path/to/official-export.json --require-complete
```

`accepted_at` 只来自正式 decision note 的创建时间，不来自会议通知日、论文创建日或首次采集日。没有公开 decision 日期时保存 `null` 和 `unknown`。`published_at` 只来自官方 `pdate`，`observed_at` 保留第一次采集时间，`last_observed_at` 表示最近完整核验。它们不能互相替代。评分保存原始字段名、文本、邀请定义和 note 链接。

完整快照的 `snapshot_sha256` 用于内容对账；受限状态仍保留 `last_successful_at`、`last_successful_count` 和 `records_retained`。导入文件只是对官方导出来源的操作声明，并不是数字签名；来源声明之外的元数据、公开权限和分页完整性均由适配器验证。

官方接口规则：[OpenReview API v2 notes retrieval](https://docs.openreview.net/how-to-guides/data-retrieval-and-modification/how-to-get-all-notes-for-submissions-reviews-rebuttals-etc)。
