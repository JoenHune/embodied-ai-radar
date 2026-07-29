# 具身智能研究雷达

> 面向基金战略研判的 12 个月具身智能研究趋势、同行评审锚点与结构化证据库。

在线阅读：<https://joen.site/embodied-ai-radar/>

## 覆盖范围

- 主分析：2025 年 7 月—2026 年 6 月
- 前瞻快照：2026 年 7 月 1–29 日
- 同比基线：2024 年 7 月—2025 年 6 月
- 五大方向：具身基础模型、大小脑与双系统、灵巧操作、世界模型、通用机器人学习

## 本地开发

```bash
npm install
npm run docs:dev
```

## 数据与复现

```bash
npm run collect
npm run generate
npm run audit
npm run docs:build
```

`data/papers.json` 是论文记录的唯一结构化来源；月度页、统计表、机构表和合并报告均由脚本派生。

`npm run collect` 使用 Semantic Scholar 批量发现带 arXiv external ID 的候选；`npm run collect:arxiv` 是以 `cs.RO` 为核心的 arXiv Atom 全量采集路径，可能受官方接口限流。

## 许可

MIT License
