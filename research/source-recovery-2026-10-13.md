# 原文来源恢复计划

2026-10-13 新增 `scripts/recover_token_free_sources.py`。默认只读，未接入定时任务；本轮没有执行生产补抓、发布或状态重置。

## 真实只读核对

北京时间 2026-10-13 12:15，对既有生产运行目录的权威目录及 `.research/hardware-fulltext` 观察记录完成一次只读规划，实际网络请求为 0：

| 分类 | 去重 work 数 |
| --- | ---: |
| 已有来源观察 | 35,118 |
| 历史取得完整或部分 HTML 正文 | 32,409 |
| 明确瞬时传输失败，符合重试条件 | 1,037 |
| 仍需来源或身份复核 | 1,672 |
| 默认本批选中 | 8 |

当时没有待处理的 403/429 全局阻断。这里是已观察来源的分母，不包含 7,602 个尚无 arXiv 原文来源的目录 work；已有正文记录也不表示本机缓存仍保留、不表示精读或研究结论已核验。重试资格不保证下一次能成功取得原文。

## 使用边界

```bash
# 默认只读；--summary 只打印分类计数和本批候选。
.venv/bin/python scripts/recover_token_free_sources.py --dry-run --summary

# 在独立开发目录查看实际运行目录，仍然只读。
.venv/bin/python scripts/recover_token_free_sources.py \
  --repository /path/to/runtime-repository --dry-run --summary
```

完整 JSON 的 `queue` 按 work 去重，包含 `source_state`、`failure_kind`、`http_status`、`attempt`、`next_retry_at`、`reason`、`eligible`、`selected`、原 `source_url` 和 `observation_id`。总量保留全部观察；选择优先相关且最近的研究。`--summary` 省略完整队列。

只有显式 `--apply` 才会重试。它要求所选运行目录已有 `scripts/radar_resource_guard.py`；当前 main 未跟踪该生产模块时只能独立规划，apply 必须明确指定已有运行环境，不在这里复制或替换资源治理代码。

```bash
# 实施入口示例，本轮未执行。
.venv/bin/python scripts/recover_token_free_sources.py \
  --repository /path/to/runtime-repository --apply --max-records 8 --summary
```

- 仅纳入明确的网络传输错误、HTTP 5xx 和 429；404、未知错误、身份冲突与 HTML 挑战继续待复核。
- 403/访问挑战暂停整个恢复通道。429 冷却届满后，每次只探测一个原请求；多个 429 取最晚冷却时间，不切换域名或版本。
- 每个来源总尝试上限为 3；默认每批 8，硬上限 200；5 分钟预算在请求边界检查。新长退避立即结束批次并释放锁，仅常规 15 秒间隔可等待。
- apply 复用现有资源检查，至少保留 6 GiB 磁盘空间；开始和每个请求边界不满足资源条件即暂停。
- 依次取得 `runner.lock`、`collector.lock`，在 collector 锁内初始化和修复中断日志；绑定旧观察和请求状态，发生并发变化则拒绝旧计划。
- 沿用原采集器持久退避、Retry-After、观察追加与来源身份校验。运行审计写入 `.research/token-free-research/recovery-runs/`。
- 不更改提取规则、历史 processing key、权威库或发布回执。补抓成功后，现有常规任务可在下批读取新观察并提取；本工具本身不提取或发布。

自动化目前不调用此工具。后续调度接入应先只读检查 `eligible_count` 和 `global_pause_reason`，在既有资源准入允许时显式执行小批；遇新退避、资源暂停、缺失运行 guard 或复核项均保留状态，不能当作已恢复。

专项测试使用临时目录和模拟网络，覆盖只读、去重、来源绑定、429 单探针、403 阻断、总尝试/时间预算、新退避释放锁、锁冲突、锁前不修复日志、资源暂停及审计保留。原 token-free 提取与来源采集回归也通过；没有用生产抓取代替测试。
