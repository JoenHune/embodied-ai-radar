# 具身智能研究雷达

> 双层研究情报产品：面向决策者的研究驾驶舱，以及可检索、可追溯、可复算的公开研究证据库。

现有网站地址：[具身智能研究雷达](https://joen.site/embodied-ai-radar/)。此地址不表示当前分支的 v3 改动已经发布；部署状态以 GitHub Actions 记录为准。

## v3 能做什么

- 默认看最近 12 个完整自然月；当前暂行月独立展示，无数据为未知，不与完整月折线相连。
- 月度证据可切换“当月可用”与“今天回看”，后续评审、开源和复现不倒灌成当时已知事实。
- 原始标题、摘要、作者、版本、组织、D1–D15/Q0–Q10 与正交标签统一检索；精确证据集合使用 `ids` URL 参数。
- T0 核心、T1 前沿和 T2 发现池分层组织，展示关键公司技术报告与课题组研究，不做跨组总排名；缺口保留在待归属队列。
- 议题发文动量、具体命题生命周期和 E0–E4 证据等级分开。共用 benchmark、仓库、作者或联合署名不自动成为同源/独立复现证据。
- 规范 JSONL 生成公开 JSON、SQLite、Pagefind 和网站；不需要付费搜索、X API 或后端数据库服务。

当前计数与数据截止以构建后的 `docs/public/api/v1/catalog-manifest.json` 为准，不在 README 另维护一套动态总量。方法见 [方法总览](docs/methods/index.md)，覆盖分母见 [覆盖审计](docs/methods/coverage.md)。

## 迁移前的语料基线

- 主分析：2025 年 7 月—2026 年 6 月
- 完整月更新：2026 年 7 月 1 日—8 月 31 日
- 同比基线：2024 年 7 月—2025 年 6 月
- arXiv 宽召回：32,218 条母集，其中 24,461 条属于 `cs.RO`
- 正式发表：12,249 条版本记录，窗口内 10,488 条；母集保留 ICRA 2024 作版本去重
- 严格官方层：824 条完整 proceedings 记录，另有 3,161 条官方 program / pending
- 去重工作图：42,083 个 canonical works
- 开源层：42 个已审计 GitHub 仓库 + 7 个新仓观察项
- 主题体系：五类稳定月度序列 + 15 类 v2 开放方向 + Q0–Q10 正交研究问题层
- 研究组织：60 个核心研究组 + 3 个新增初创观察位 + 23 个母机构/上级节点，按 G1–G0 归属证据持续更新

## 本地开发

先准备下节的 Python 3.12、Node.js 24 和依赖。已有派生页面数据时可启动本地开发；初次完整验证使用 `npm test`。

```bash
npm run docs:dev
```

## v3 运行与发布

v3 使用 Python 3.12、Node.js 24 和项目依赖。以下为运行接口；代码存在或 dry-run 通过不表示网站已上线、定时任务已启用。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-v3.txt
npm ci
npm test
```

`data/catalog/` 中分片 JSONL 是事实权威层；`data/editorial/` 保存独立的研究编辑、本地化与命题审阅记录。原始采集文件、配置和审核 additions 通过显式导入进入权威库，不与其并列作为网站事实来源。

`npm run v3:export` 只读事实并生成 SQLite、静态 API 和月度数据；`npm run v3:site` 生成页面数据；`npm test` 审计并构建网站与搜索。常规构建不会采集数据、调用 LLM、重迁移或写入新的权威月度 revision。不要手工修改 `docs/public/api/v1/`、SQLite 或搜索索引。

SQLite 构建入口会检查 JSON 特殊键名、超大整数、布尔值还原及 FTS5 能力，而不只比较版本号。优先使用系统库；Linux x86_64 的系统库不满足时，使用依赖文件锁定的 `pysqlite3-binary`，仅作用于本次 Python 进程，不修改系统安装。请通过 `node scripts/run-python.mjs ...` 或 npm 入口执行需要完整数据库还原的工具。下载件仍是标准 SQLite 文件，无自定义 Python SQL 函数；单独执行 `catalog_restore_*` 视图时也应使用支持上述 JSON 能力的较新 SQLite。实现依据见 [SQLite JSON 文档](https://www.sqlite.org/json1.html)与[依赖发布页](https://pypi.org/project/pysqlite3-binary/)。

`npm run v3:migrate` 仅用于初始化尚不存在的权威库。来源发生变化后才运行 `npm run v3:ingest -- --as-of YYYY-MM-DD`；人工和已保存编辑不会因生成网站而丢失。

### 常用操作边界

| 目的 | 操作 | 是否写事实/联网 |
|---|---|---|
| 从已有事实生成网站数据 | `npm run v3:export`、`npm run v3:site` | 不采集，不重写 JSONL 事实 |
| 完整本地验收 | `npm test` | 导出、审计、类型检查、构建与 Pagefind；不发布 |
| 读取已有构建 | `npm run docs:preview -- --port 4173` | 只读本地站点；重新构建后需重启预览进程避免缓存旧产物 |
| 导入新来源和审阅补充 | `npm run v3:ingest -- --as-of YYYY-MM-DD` | 写权威库与修订；应先检查变更范围 |
| 为单月生成中文编辑 | `node scripts/run-python.mjs scripts/generate_v3_editorial.py --month YYYY-MM --allow-data-only` | 调用已配置模型并写编辑记录；缺配置则数据版 |
| 只读查看周报流程或内容 | `python3 scripts/run_weekly_v3.py --dry-run` / `--preview-report` | 不采集、不提交、不外部发布 |

### 本机每周更新

本机编排接口配置为北京时间每周一 00:00：先检查干净的 `main`，取得排他锁并 fast-forward 更新，再增量采集、归属、入库、中文编辑、导出和测试。通过后按覆盖 ISO 周保存 `data/weekly-v3/YYYY-Www.json`，只提交明确列出的数据和派生页面路径，并推送 `main`。这是流程说明，不表示 LaunchAgent 已经安装。

```bash
# 只读预览：不联网、不改数据、不创建锁、不提交
python3 scripts/run_weekly_v3.py --dry-run
python3 scripts/install_weekly_launchd.py --dry-run

# 完成全局验收并切换到干净 main 后，显式执行
python3 scripts/run_weekly_v3.py --publish
python3 scripts/install_weekly_launchd.py --install
```

分支开发目录只允许预览。安装器会核查 macOS 系统时区为 `Asia/Shanghai`，因为 `launchd` 的日历触发依赖系统时区；不会仅凭 `TZ` 假定时区已改变。休眠、网络和权限造成的延迟须查看实际日志，不能承诺在电脑不可用时准点完成；远端兜底用于本机未及时运行的情况。日志保存在 `logs/weekly-v3.log` 与 `logs/weekly-v3.error.log`。

更新保留三个不同时间：实际 UTC 运行时间、各来源采集截止时间和上一完整自然周的北京时间覆盖窗口。失败来源保留旧记录及失败状态；不能把“今天运行”写成“今天语料全部补齐”。arXiv 使用最近两月重叠增量，正式发表使用近两年会议索引和近 45 天期刊窗口，并按来源 ID 合并保存。

### 本地 LLM 配置

可通过环境变量提供 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`；默认模型为 `gpt-5.6-sol`。LaunchAgent 默认从仓库外的 `~/.config/embodied-ai-radar/runtime.env` 读取这三个配置项，也可用 `--env-file /绝对路径/runtime.env` 指定。该文件不是 shell 脚本，变量值不执行命令，不进入仓库或 plist。

也可显式复用本机现有 LoggerBot 反代配置，无需复制密钥：

```bash
python3 scripts/generate_v3_editorial.py --month 2026-08 --loggerbot-env-file /绝对路径/loggerbot/.env
python3 scripts/run_weekly_v3.py --publish --loggerbot-env-file /绝对路径/loggerbot/.env
python3 scripts/install_weekly_launchd.py --dry-run --loggerbot-env-file /绝对路径/loggerbot/.env
```

该入口只映射 `CODEX_PROXY_BASE_URL`、`CODEX_PROXY_API_KEY`、`CODEX_PROXY_MODEL`，忽略其他飞书／个人授权字段，且不读写共享登录状态。显式 `LLM_BASE_URL` 环境配置优先，并作为完整配置来源处理，避免混用另一服务的密钥。这里只复用模型传输；研究统计、引用和时间校验仍由雷达负责。实际模型证据包与候选输出保存在未进入版本控制的 `logs/editorial/`，非法候选不会直接发布。

LLM 工作者负责最多三次尝试以及数据版降级；缺配置时不发送请求。每项判断要引用证据包中的数据库 ID，数字与原文片段也会校验。历史已完成编辑保持保存，但只有与当前证据包、源内容和模型相符且再次校验通过的缓存才能继续覆盖网页；失效摘要不会被当成当前研究结论。`python3 scripts/run_weekly_v3.py --publish --data-only` 完全跳过 LLM 调用。

自动生成的命题证据写入 `data/editorial/signal-evidence.jsonl`，初始状态一律为 `draft`。结构、引文和数字检查不能代替语义复核；通过 `scripts/signal_evidence.py` 的审阅接口记录 reviewer、时间、说明与 `review_history` 后，verified 且 in-scope 的记录才可支持命题生命周期。不能只手改一个 `review_status` 冒充完成复核。此接口存在不代表所有月份中文总结或命题证据已生成、已审阅。

本次文档核对（2026-09-06）保存的 `data/editorial/status.json` 仍显示数据版：12 个完整月为 `provider_not_configured`，暂行月为 `no_eligible_monthly_evidence`。这是已保存运行结果，不是对未来配置的限制；后续以重新运行后的状态和证据校验为准。

### GitHub Pages 与远端兜底

- `deploy.yml` 在 `main` push 后只做只读导出、审计、构建和部署；CI 无需本地反代或 LLM 密钥。
- `weekly-groups.yml` 在北京时间周一 04:00 检查上一完整 ISO 周；已有 `verified` 快照则跳过，缺失时增量采集并发布数据版。
- 两个工作流共用发布并发锁。兜底使用 `GITHUB_TOKEN` 提交后自行部署已验证产物，避免再触发重复 push 部署。
- `verified` 表示数据与构建已通过，并不表示外部部署已成功；部署结果以 GitHub Actions 的 deployment 记录为准。

### 飞书交付

网站部署成功后才执行独立飞书 job。实际发布需要 GitHub Encrypted Secrets：`FEISHU_APP_ID`、`FEISHU_APP_SECRET`、`FEISHU_FOLDER_TOKEN`、`FEISHU_INDEX_DOC_TOKEN`，目标文件夹需共享给专用应用；不得上传个人 OAuth/refresh token。

v3 周报生成在 `docs/pulse/weekly/yyyy-www.md`（如 `2026-w36.md`）；发布器仍兼容旧周报路径。`data/feishu-weekly-deliveries.json` 保存 ISO 周幂等状态与待补发队列。创建成功立即保存文档 ID，后续正文失败再次运行会更新同一文档。缺少配置、正文或索引失败不会回滚网站。

```bash
# 查看某周待交付内容，不发布
python3 scripts/publish_group_weekly_to_feishu.py --week YYYY-Www --dry-run
```

对可重试 API 最多尝试三次。创建文档或追加索引若出现无法确定服务器是否成功的响应，将记录 `*_uncertain_requires_reconciliation`，避免盲目重试产生副本；需核对飞书中实际文档或索引并补齐交付状态后恢复。

### 数据下载、修订与复算

已逐篇阅读的 AI 草稿输入可先离线验证，再显式保存到命题待审队列。例如：

```bash
.venv/bin/python -m scripts.compile_signal_reading data/editorial/research-inputs/2026-08-world-models.json
.venv/bin/python -m scripts.compile_signal_reading data/editorial/research-inputs/2026-08-world-models.json --write
```

这不是本地 Responses 调用，也不是人工批准：只产生 `draft`，保留具名 AI 阅读说明，不能设置 verified。短摘录从当月可用版本自动定位；改动既有记录需要明确修订，精确重复运行不增加记录。月度页提供按需展开的阅读入口，后续导出仍须通过数据审计。

若同一 AI 阅读需要纠正立场，更新输入的审核时间与说明后，显式添加 `--revise --write`；旧立场、原判断及内容摘要保留在审阅历史。该选项不能覆盖人工审核或 verified 记录。

公司报告采用独立的历史短摘录协议：`data/report-archive-proofs.jsonl` 是待核验来源证明，`data/report-text-additions.jsonl` 是短摘录输入；只有首次通过缓存/Git/部署哈希检查后，才能登记到权威 `data/catalog/report-text-snapshots.jsonl`。再次导入相同已登记证明无需读取被Git忽略的缓存，因此只读CI不依赖本机原始HTML。源证明和摘录不能在同一行自我认证；先验证来源再追加快照，标题、原始摘要、相关性与评审状态不因摘录而改变。

```bash
# 核对GEN-1.5已保存的历史来源输入；不写权威库、不调用模型
.venv/bin/python scripts/extract_report_archive.py --verify
```

报告发布日期不等于正文可用时间。每报告只公开必要短摘录及指纹/定位，全文仍在本地原始缓存；不授予CC0许可。模型不能在报告叙述里自由拼接实验数字，报告观测由程序按原条件固定呈现。历史日期、JSON/SQLite、一对一归属和月度两种证据视角均有专项审计。

网站公开 `/api/v1/catalog-manifest.json`、`monthly/{YYYY-MM}.json`、`trends.json`、`organizations/{slug}.json`、`organization-coverage.json`、`signal-evidence.json` 和 `evidence-events.json`。先查 `aliases.json`，再按 SHA-1(work ID) 前两位取 `works/{00–ff}.json`；SQLite 无损压缩下载在 `/downloads/radar.sqlite.zip`，包内仅有 `radar.sqlite`，先解压再打开（以上均相对网站 base）。压缩不删记录、字段、原文或索引；manifest 的 `downloads.sqlite_integrity` 列出原库及 ZIP 的字节数和 SHA-256。未压缩派生库仅留在本地 `.research/derived/radar.sqlite`，不随网站重复发布。

逐版标题、作者、摘要保存在权威 `text-snapshots` 分片，公开 `/api/v1/text/{00–ff}.json` 和 SQLite `text_snapshots` 提供相同原文；详情默认选择数据截止日前可用的版次，并保留原始入库摘要。后来的修订不得用于历史月份的实验判断。搜索区分“截至日版本正文”与“最新登记的标题身份／出版状态”，旧标题仍能找到同一个 work，新获会议接收也不会因预印本主源截止较早而从会议筛选中消失。

没有版次档案的已采集摘要也保留检索，标为 `unversioned_catalog_text`，不据此补造历史可用时间。普通全文检索统一连字符、下划线与空格边界；原始标题和 DOI／URL／π 模型身份不改写。Pagefind gzip 资产在构建时使用缓存的 Zopfli 优化，逐文件证明解压字节一致，不改变检索内容。SQLite 的 FTS5 从原始 `works` 的外部内容视图读取正文，不再重复保存整段摘要；仍支持 MATCH、读取和高亮，并在导出时校验索引与原文一致。

`/api/v1/release-recall.json` 和 `coverage-gold-releases.json` 公开冻结的 source-first 回归样本及逐项对账，SQLite `release_recall_gold` 保存同一分母。`config/release-recall-policy.json` 固定样本 hash、最低规模与 95% 研究发布版本链接召回门槛；`npm test` 会执行该检查。这仅验证声明的分层样本，不证明全部 T0 或互联网覆盖。新增样本必须显式修订政策，不允许删除难匹配项以通过检查。

CoRL 验证变化来自 `/api/v1/conference-changes/corl-2026.json`，区分首次公开、首次发现和接收事件；未知完整性不显示成零篇。周更逐来源窗口来自 `/api/v1/source-coverage.json`；尚无真实运行记录时明确显示 `not_run`，不能拿迁移成功冒充定时采集成功。

月度 `revisions[].url` 指向可打开的归档，差异含覆盖数量前后值及新增/移出工作或判断修订。月/年精度保留原样，不能把内部排序占位日呈现为精确发布日期。来源日期被官方复核取代时保留旧记录与 supersession，不静默改写原始证据。

### 仍待验收，不代表取消的目标

原计划的全面月度中文研究、关键组与公司技术报告持续覆盖、趋势语义核验、每周自动采集/发布及飞书交付均保留。以下须逐项拿到实测证据后才能宣称完成：

- 本机模型配置、最近 12 个完整月及暂行月的有效中文编辑与明确缺口。
- T0 官方回归样本召回率 ≥95%；没有独立金标准时报告未测量，而不是套用目标值。
- 高信号具体组归属覆盖 ≥90%；分母与待归属项公开，不能删除未匹配项提高比率。
- 首页首屏数据 ≤200 KB gzip、普通路由初始 JS ≤250 KB gzip、图表路由 ≤450 KB gzip、搜索索引 <20 MB；由最终构建的产物审计确认。
- 360/390/768/1024/1440 像素、键盘、可访问数据表及深浅色实测；移动 LCP ≤2.5 秒、CLS <0.1 需运行时测量，不能用文件体积替代。
- LaunchAgent 实际安装和执行、远端兜底真实运行、Pages deployment 成功、飞书专用应用权限及幂等投递验证。仓库代码和本地测试不等于这些外部流程已经启用。

## 旧版数据采集与复现参考

以下保留旧研究流程与语料来源，供迁移对账和历史复现；不是 v3 日常更新的推荐顺序，不要将旧生成器再次输出的页面或统计作为新的事实权威。

```bash
npm run collect:arxiv-v2
npm run collect:publications
npm run collect:official
npm run collect:official-programs
npm run collect:groups
npm run import:github
npm run refresh:github
npm run merge:v2
npm run resolve:groups
npm run generate
npm run audit
npm run audit:v2
npm run audit:questions
npm run audit:groups
npm run docs:build
```

v2 的核心结构化数据源：

- `data/preprints.json`：两年 arXiv 母集，按首次提交 `v1` 日期归档
- `data/publications.json`：会议与期刊发表版本
- `data/official-proceedings.json`：逐容器对账的严格官方记录
- `data/official-programs.json`：尚未进入正式 proceedings 的官方节目/录用记录
- `data/repositories.json`：GitHub 仓库与论文映射
- `data/github-watchlist.json`：新论文代码仓的早期观察清单，不与已评分仓库混排
- `data/works.json`：跨预印本、发表版本、官方记录和代码仓库去重后的 canonical work graph
- `data/research-question-evidence.json`：Q0–Q10 对标题/摘要的多标签证据 sidecar，不改变 D1–D15 主方向
- `config/organizations.json`：研究组、研究院和母机构的分层实体图，60 个 tracking units 固定分为 18/30/6/6
- `data/group-updates.json`：论文、模型、数据、代码、部署与组织变化的 G1/G2 正式动态
- `data/work-organization-links.json`：canonical work 到研究组的可追溯归属边及 fractional credit
- `data/research-group-radar.json`：研究组页面、筛选器、合作网络和周报的唯一派生数据源

`data/papers.json` 仍保留为旧五类月度分析的稳定序列。新母库与旧序列分层维护，避免 taxonomy 扩展被误判为真实趋势变化。页面、统计表和下载文件均由脚本生成。

完整采集边界、官方证据等级和去重规则见 `docs/methods/expansion-protocol.md`。
飞书研究问题与公开论文证据的结合方法见 `docs/methods/research-question-layer.md`。
研究组归属、官方来源监测和周报边界见 `docs/methods/research-groups.md`。

## 旧版研究组资料

旧版分组数据保留用于迁移和归属追溯。当前周更接口、调度及发布门槛以本 README 的 v3 部分为准。来源监测失败不会删除历史记录；连续两次失败会在档案页显示 `stale`。

飞书发布器只有显式传入 `--dry-run` 才是只读预览；不要把不带该参数的命令当成试运行。启用实际周报需在 GitHub Encrypted Secrets 配置：

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_FOLDER_TOKEN`
- `FEISHU_INDEX_DOC_TOKEN`

这些凭据属于专用应用身份；不得提交个人 access/refresh token。

<!-- 更新标记：v3 运行与数据口径 最后更新 2026.09 -->

## 许可

MIT License
