# 具身智能研究雷达

> 面向基金战略研判的月度趋势、早期信号、正式发表工作与开源采用证据库。

在线阅读：<https://joen.site/embodied-ai-radar/>

## 覆盖范围

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

```bash
npm install
npm run docs:dev
```

## 数据与复现

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

## 每周研究组更新

`.github/workflows/weekly-groups.yml` 于北京时间每周一 04:00 运行，冻结上一自然周。来源监测失败不会删除历史记录；连续两次失败会在档案页显示 `stale`。

飞书发布默认执行 dry-run。启用实际周报需在 GitHub Encrypted Secrets 配置：

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_FOLDER_TOKEN`
- `FEISHU_INDEX_DOC_TOKEN`

这些凭据属于专用应用身份；不得提交个人 access/refresh token。

## 许可

MIT License
