# 不调用大模型的原文研究脚本

脚本运行不消耗模型 API token：没有模型客户端、密钥读取、反代请求或代理调用。会使用本机 CPU、硬盘；主动补抓原文时会使用网络。编写脚本的这次对话本身不属于“零 token 运行”的承诺。

## 使用

在项目目录运行，或双击 `scripts/run-token-free-research.command`，默认只处理已有缓存：

```sh
bash scripts/run-token-free-research.command
```

补抓所有尚未尝试过的 arXiv HTML，并处理全部可用缓存（可能耗时很长，可中断后重跑）：

```sh
bash scripts/run-token-free-research.command --fetch --fetch-limit 0
```

先做有界批次：

```sh
bash scripts/run-token-free-research.command --fetch --fetch-limit 200 --process-limit 1000
```

查看已有进度或全文检索：

```sh
bash scripts/run-token-free-research.command --status
bash scripts/run-token-free-research.command --search 'Unitree G1'
bash scripts/run-token-free-research.command --search '世界模型'
```

词组搜索使用本地 SQLite FTS；附带少量中英文术语映射，不宣称具有大模型语义检索或完整中文分词能力。

## 输出

全部保存在忽略提交的 `.research/token-free-research/`：

| 文件 | 用途 |
|---|---|
| `REPORT.md` / `summary.json` | 全库分母、处理状态和运行边界 |
| `research.sqlite` | 全库元数据、已提取正文全文检索、逐条候选证据 |
| `cards/*.json.gz` | 每篇完整可提取正文、表格、附录、参考、图注与定位，及来源哈希 |
| `coverage.jsonl` | 每个 canonical work 一条状态，包含 candidate/manual_review/excluded |
| `hardware-candidate-frequency.json` | 按非背景正文候选提及的去重 work 数排序 |
| `hardware-candidate-sources.jsonl` | 全部设备候选出处，不截成少量样本；背景引用有单独标记 |
| `source-review-queue.jsonl` | 未获取、非 arXiv、失败或待处理来源 |
| `monthly-coverage.json` | 每月登记及处理覆盖，不冒充月度趋势结论 |

未知名称启发式线索保存在各篇 card 中，不自动合并型号或进入型号排名。图像、视频、缺失附录及非 arXiv 技术报告仍需补充核验。没有词典命中不代表没有设备。

## 续跑与安全

- 一次只运行一个脚本实例；在线采集沿用项目原有锁、单连接、至少 3 秒间隔和持久退避，403/429 停止当批网络采集。
- 已有来源不会因重跑而重新下载；失败来源不自动重试，也不会换地址绕过访问限制。后续恢复需单独核验。
- 每篇处理后提交 SQLite 事务。来源、词典或处理代码变化时重新计算；未变记录复用，不声称每次重验原始字节。
- 原始正文、历史版本卡片、现有阅读/设备权威库均保留。脚本不启动模型服务、创建精读回执、提升“已核验”标记或触发网站发布。
- 只解析文本不等于读懂论文。全量精读、模型使用关系判定、跨论文趋势叙述与独立复现，无法靠这个确定性脚本自动完成。

因此，本脚本能零模型调用地推进全库原文获取、保留、检索和线索发现，但不会虚称完成“全部论文研究理解”。

## 已完成验证（2026-09-22）

- 新脚本 14 项测试，以及复用的原文解析 16 项、采集器 43 项测试通过，共 73 项。网络行为使用 fixture，没有为测试访问外网。
- 真实语料登记 42,720 个 canonical work；离线处理 3 篇缓存原文，重复运行复用全部 3 篇，没有重新解析。
- 实测 SQLite 检索可返回结果；2609.10433 的空附录 S6 被明确写入补缺清单，没有生成完整阅读回执。
- 没有运行全量联网抓取、网站构建或发布，没有修改已有权威数据。全量运行时间和全库设备召回率尚未实测。
