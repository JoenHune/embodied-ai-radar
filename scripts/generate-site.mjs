import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const docs = path.join(root, 'docs')
const read = (name) => JSON.parse(fs.readFileSync(path.join(root, name), 'utf8'))
const papers = read('data/papers.json')
const trends = read('data/trends.json')
const forecasts = read('data/forecasts.json')
const directions = read('data/directions.json')
const peerRecords = read('data/peer-review.json').records

const topics = {
  foundation: { label: '具身基础模型', slug: 'foundation-models' },
  dual_system: { label: '大小脑与双系统', slug: 'dual-system' },
  dexterous: { label: '灵巧操作', slug: 'dexterous-manipulation' },
  world_model: { label: '世界模型', slug: 'world-models' },
  general_learning: { label: '通用机器人学习', slug: 'general-robot-learning' },
}
const topicOrder = Object.keys(topics)
const analysisMonths = [
  '2025-07', '2025-08', '2025-09', '2025-10', '2025-11', '2025-12',
  '2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06',
]
const allMonths = [...analysisMonths, '2026-07']
const included = papers.filter((paper) => paper.included)
const byId = new Map(papers.map((paper) => [paper.id, paper]))

const ensureDir = (target) => fs.mkdirSync(path.join(docs, target), { recursive: true })
for (const directory of ['monthly', 'quarterly', 'directions', 'analysis', 'database', 'public']) ensureDir(directory)
const write = (name, content) => fs.writeFileSync(path.join(docs, name), `${content.trim()}\n`)
const frontmatter = `---\noutline: deep\n---`
const clean = (value = '') => String(value).replaceAll('|', '\\|').replace(/\s+/g, ' ').trim()
const percent = (numerator, denominator) => denominator ? `${(numerator / denominator * 100).toFixed(1)}%` : '—'
const signed = (value) => value > 0 ? `+${value}` : String(value)
const monthLabel = (month) => `${month.slice(0, 4)} 年 ${Number(month.slice(5))} 月`
const periodPapers = (period) => included.filter((paper) => paper.period === period)
const monthPapers = (month) => included.filter((paper) => paper.v1_month === month)
const topicCounts = (list) => Object.fromEntries(topicOrder.map((key) => [
  key, list.filter((paper) => paper.primary_topic === key).length,
]))
const evidenceValue = (paper, key) => paper.evidence?.[key] === true
const evidenceBadges = (paper) => [
  evidenceValue(paper, 'real_robot') ? '真机' : null,
  evidenceValue(paper, 'multi_task') ? '多任务' : null,
  evidenceValue(paper, 'cross_embodiment') ? '跨本体' : null,
  evidenceValue(paper, 'long_horizon') ? '长时序' : null,
  (evidenceValue(paper, 'open_code') || evidenceValue(paper, 'open_data') || evidenceValue(paper, 'open_model')) ? '开放资产' : null,
].filter(Boolean).join(' · ') || '摘要未确认'
const titleLink = (paper) => `[${clean(paper.title)}](${paper.arxiv_url})`
const officialLink = (review) => `[${review.venue} ${review.year}](${review.official_url})`
const peerTopic = (label) => Object.entries(topics).find(([, value]) => value.label === label)?.[0] ?? label

function previousYearMonth(month) {
  return `${Number(month.slice(0, 4)) - 1}-${month.slice(5)}`
}

function curatedTop(month) {
  return papers
    .filter((paper) => paper.v1_month === month && paper.curated)
    .sort((left, right) => {
      const leftScore = Object.values(left.evidence ?? {}).filter(Boolean).length + (left.peer_review ? 4 : 0)
      const rightScore = Object.values(right.evidence ?? {}).filter(Boolean).length + (right.peer_review ? 4 : 0)
      return rightScore - leftScore || left.id.localeCompare(right.id)
    })
}

function trendCard(trend) {
  const evidence = trend.evidence_ids
    .map((id) => byId.get(id))
    .filter(Boolean)
    .map((paper) => titleLink(paper))
    .join('；')
  const kindLabel = trend.kind === 'weak' ? '弱信号' : trend.kind === 'cooling' ? '反证/降温' : '共识演进'
  return `
<div class="trend-card">

### <span class="signal signal-${trend.grade.toLowerCase()}">${trend.grade} · ${kindLabel}</span> ${trend.title}

**变化。** ${trend.change}

**对比。** ${trend.comparison}

**证据。** ${evidence}

**成熟度与瓶颈。** ${trend.maturity} 主要瓶颈是${trend.bottleneck}。

**战略含义。** ${trend.implication}

</div>`
}

function monthlyPage(month) {
  const current = monthPapers(month)
  const baselineMonth = previousYearMonth(month)
  const baseline = month === '2026-07' ? [] : monthPapers(baselineMonth)
  const curated = curatedTop(month)
  const counts = topicCounts(current)
  const baselineCounts = topicCounts(baseline)
  const realCount = curated.filter((paper) => evidenceValue(paper, 'real_robot')).length
  const openCount = curated.filter((paper) =>
    evidenceValue(paper, 'open_code') || evidenceValue(paper, 'open_data') || evidenceValue(paper, 'open_model')).length
  const monthReviews = peerRecords.filter((review) =>
    review.safe_month_anchor?.eligible && review.safe_month_anchor.month === month)
  const monthTrends = trends.months[month] ?? []
  const conclusion = monthTrends.length
    ? `${monthTrends[0].title}；与此同时，${monthTrends.at(-1).title}。`
    : '样本不足，暂不形成趋势判断。'
  const snapshotNote = month === '2026-07'
    ? '> **前瞻快照。** 本页只覆盖 2026 年 7 月 1–29 日，不计算环比、同比或与完整月份的热度排名。\n'
    : `> **统计口径。** 自动宽召回候选用于数量结构；${curated.length} 篇精读样本用于实验与开放性指标。同比月为 ${baselineMonth}。\n`
  const topicRows = topicOrder.map((key) => {
    const delta = month === '2026-07' ? '—' : signed(counts[key] - baselineCounts[key])
    return `| [${topics[key].label}](/directions/${topics[key].slug}) | ${counts[key]} | ${percent(counts[key], current.length)} | ${month === '2026-07' ? '—' : baselineCounts[key]} | ${delta} |`
  }).join('\n')
  const topRows = curated.map((paper) =>
    `| ${titleLink(paper)} | ${paper.first_submitted} | ${topics[paper.primary_topic]?.label ?? paper.primary_topic} | ${clean(paper.contribution_zh)} | ${evidenceBadges(paper)} |`
  ).join('\n')
  const peerRows = monthReviews.length
    ? monthReviews.map((review) =>
      `| [${clean(review.title)}](https://arxiv.org/abs/${review.arxiv_id}) | ${officialLink(review)} | ${clean(review.evidence_note)} |`
    ).join('\n')
    : '| — | — | 本月首次公开的精读样本尚无可安全归属到该月的官方录用证据；这不等于论文质量较低。 |'
  const weakSignals = monthTrends.filter((trend) => trend.kind === 'weak')
  const weakRows = weakSignals.length
    ? weakSignals.map((trend) =>
      `| ${trend.title} | ${trend.grade} | ${trend.bottleneck} | ${trend.maturity} |`
    ).join('\n')
    : '| — | — | — | 本月未识别到超过阈值的弱信号 |'

  return `${frontmatter}

# ${monthLabel(month)}研究雷达${month === '2026-07' ? '（前瞻）' : ''}

${snapshotNote}

<div class="radar-kpis">
  <div class="radar-kpi"><strong>${current.length}</strong><span>纳入统计候选</span></div>
  <div class="radar-kpi"><strong>${curated.length}</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>${realCount}/${curated.length}</strong><span>摘要确认真机</span></div>
  <div class="radar-kpi"><strong>${monthReviews.length}</strong><span>官方评审锚点</span></div>
</div>

## 一句话结论

${conclusion}

## 主题结构

| 主方向 | 本月候选 | 占比 | 同比候选 | 同比增量 |
|---|---:|---:|---:|---:|
${topicRows}

> 自动宽召回对 VLA 命名敏感，不能单独解释为能力增长；大小脑类因常使用隐式架构命名，自动数量是保守下界。

## 趋势证据卡

${monthTrends.map(trendCard).join('\n')}

## 蛛丝马迹：小样本领先信号

| 弱信号 | 等级 | 下一道技术门槛 | 当前判断 |
|---|---|---|---|
${weakRows}

识别逻辑不是“论文少就更前沿”，而是寻找多个弱证据是否指向同一个尚未被主流命名的瓶颈迁移。完整方法见[弱信号探测与未来判断](/analysis/weak-signals)。

## 本月精读论文

| 论文 | v1 日期 | 主方向 | 一句话贡献 | 证据标签 |
|---|---|---|---|---|
${topRows}

精读样本明确开放披露 ${openCount}/${curated.length}；只在摘要、comment 或已核验项目页明确披露时记为“是”。

## 同行评审锚点

| 工作 | 官方证据 | 为什么可作为本月锚点 |
|---|---|---|
${peerRows}

## 反证与信号质量检查

- 多篇论文共享相同数据、模型或作者团队时，不按独立证据重复加权。
- 单一 benchmark 提升若没有真实机器人迁移，不足以升级为 A 级趋势。
- “open-source / will release” 与实际可下载、可复现实验分开记录。
- 世界模型必须展示动作、规划、控制或数据生成价值；纯视频质量不计。

<!-- 更新标记：${month} 月度雷达 最后更新 2026.07 -->`
}

function monthlyIndex() {
  const rows = allMonths.map((month) => {
    const current = monthPapers(month)
    const baseline = month === '2026-07' ? [] : monthPapers(previousYearMonth(month))
    const counts = topicCounts(current)
    const dominant = topicOrder.toSorted((a, b) => counts[b] - counts[a])[0]
    const curated = curatedTop(month)
    const real = curated.filter((paper) => evidenceValue(paper, 'real_robot')).length
    return `| [${monthLabel(month)}](/monthly/${month}) | ${current.length} | ${month === '2026-07' ? '快照' : signed(current.length - baseline.length)} | ${topics[dominant].label}（${counts[dominant]}） | ${curated.length} | ${real}/${curated.length} |`
  }).join('\n')
  return `${frontmatter}

# 月度研究雷达

> 主分析期按 arXiv v1 月份归档；2026 年 7 月只覆盖 1–29 日。候选数量衡量统一查询下的研究密度，精读样本用于技术判断。

| 月份 | 候选数 | 同比增量 | 数量主导方向 | 精读 | 真机确认 |
|---|---:|---:|---|---:|---:|
${rows}

## 怎么读月度页

1. 先看绝对数量和同比，判断是否只是小样本百分比。
2. 再看精读论文的真机、跨任务/本体、长时序和开放资产。
3. 用官方同行评审锚点区分“arXiv 密集”与“已有独立评审路线”。
4. 最后看弱信号与反证；前者寻找未来，后者防止把命名潮误判为能力跃迁。

<!-- 更新标记：月度总览 最后更新 2026.07 -->`
}

function directionPage(key, direction) {
  const analysis = periodPapers('analysis')
  const baseline = periodPapers('baseline')
  const currentPapers = analysis.filter((paper) => paper.primary_topic === key)
  const baselinePapers = baseline.filter((paper) => paper.primary_topic === key)
  const reps = direction.representative_ids.map((id) => byId.get(id)).filter(Boolean)
  const repRows = reps.map((paper) =>
    `| ${titleLink(paper)} | ${paper.v1_month} | ${paper.peer_review ? officialLink(paper.peer_review) : 'arXiv'} | ${clean(paper.contribution_zh || paper.abstract.split('. ')[0])} |`
  ).join('\n')
  const routes = direction.route_comparison.map((row) => `| ${row.join(' | ')} |`).join('\n')
  const trendRows = analysisMonths.map((month) => {
    const count = monthPapers(month).filter((paper) => paper.primary_topic === key).length
    return `| ${month} | ${count} | ${'█'.repeat(Math.max(1, Math.round(count / Math.max(...analysisMonths.map((item) => monthPapers(item).filter((paper) => paper.primary_topic === key).length)) * 12)))} |`
  }).join('\n')
  const peer = peerRecords.filter((record) => peerTopic(record.primary_topic) === key)
  const peerRows = peer.map((record) =>
    `| [${clean(record.title)}](${record.official_url}) | ${record.venue} ${record.year} | ${record.arxiv_id ? `[${record.arxiv_id}](https://arxiv.org/abs/${record.arxiv_id})` : '—'} |`
  ).join('\n')
  return `${frontmatter}

# ${direction.label}

> ${direction.definition}

<div class="radar-kpis">
  <div class="radar-kpi"><strong>${currentPapers.length}</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>${baselinePapers.length}</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>${peer.length}</strong><span>官方评审锚点</span></div>
  <div class="radar-kpi"><strong>${percent(currentPapers.length, analysis.length)}</strong><span>主分析期占比</span></div>
</div>

## 跨月演进

${direction.evolution.map((item) => `- ${item}`).join('\n')}

| 月份 | 候选数 | 相对热度 |
|---|---:|---|
${trendRows}

## 技术路线对比

| 路线 | 核心表示/机制 | 优势 | 当前局限 |
|---|---|---|---|
${routes}

## 代表工作

| 论文 | v1 月份 | 状态 | 一句话贡献 |
|---|---|---|---|
${repRows}

## 同行评审锚点

| 工作 | Venue | arXiv |
|---|---|---|
${peerRows || '| — | — | — |'}

## 成熟度、瓶颈与战略判断

**成熟度。** ${direction.maturity}

**关键瓶颈。**

${direction.bottlenecks.map((item) => `- ${item}`).join('\n')}

**战略判断。** ${direction.strategic}

<!-- 更新标记：${direction.label} 最后更新 2026.07 -->`
}

function peerReviewPage() {
  const rows = peerRecords.map((record) =>
    `| [${clean(record.title)}](${record.official_url}) | ${record.arxiv_id ? `[${record.arxiv_id}](https://arxiv.org/abs/${record.arxiv_id})` : '—'} | ${record.venue} ${record.year} | ${record.primary_topic} | ${record.institutions.slice(0, 3).join('、')} |`
  ).join('\n')
  const venues = [...new Set(peerRecords.map((record) => `${record.venue} ${record.year}`))]
  const safeCount = peerRecords.filter((record) => record.safe_month_anchor?.eligible).length
  return `${frontmatter}

# 同行评审锚点

> 只接受官方 proceedings、OpenReview 最终录用状态或期刊正式页面。30 条官方链接已在 2026-07-29 批量复检。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>${peerRecords.length}</strong><span>官方评审记录</span></div>
  <div class="radar-kpi"><strong>${venues.length}</strong><span>Venue / 年份组合</span></div>
  <div class="radar-kpi"><strong>${safeCount}</strong><span>可归入主分析月</span></div>
  <div class="radar-kpi"><strong>${peerRecords.length - safeCount}</strong><span>历史路线锚点</span></div>
</div>

## 如何理解“锚点”

- 首次公开时间仍由 arXiv v1 决定，会议发表月不回写为技术出现月。
- 主分析期之前的正式工作用于证明路线基础，不进入过去 12 个月论文数量。
- 作者自述 accepted/to appear 不作为证据。
- 较新月份覆盖率低主要由评审滞后造成，不能直接解释为质量差。

## 官方证据表

| 工作 | arXiv | Venue | 主方向 | 机构（最多三家） |
|---|---|---|---|---|
${rows}

<!-- 更新标记：同行评审锚点 最后更新 2026.07 -->`
}

function institutionPage() {
  const map = new Map()
  for (const record of peerRecords) {
    for (const institution of record.institutions) {
      if (!map.has(institution)) map.set(institution, { papers: new Set(), peer: new Set(), topics: new Set(), examples: [] })
      const item = map.get(institution)
      item.papers.add(record.arxiv_id || record.title)
      item.peer.add(`${record.venue} ${record.year}`)
      item.topics.add(record.primary_topic)
      if (item.examples.length < 3) item.examples.push(`[${clean(record.title)}](${record.official_url})`)
    }
  }
  for (const paper of papers.filter((item) => item.curated)) {
    for (const institution of paper.institutions ?? []) {
      if (!map.has(institution)) map.set(institution, { papers: new Set(), peer: new Set(), topics: new Set(), examples: [] })
      const item = map.get(institution)
      item.papers.add(paper.id)
      item.topics.add(topics[paper.primary_topic]?.label ?? paper.primary_topic)
      if (item.examples.length < 3) item.examples.push(titleLink(paper))
    }
  }
  const ranking = [...map.entries()]
    .map(([name, item]) => ({ name, ...item }))
    .sort((left, right) => right.peer.size - left.peer.size || right.papers.size - left.papers.size || left.name.localeCompare(right.name))
  const rows = ranking.map((item, index) =>
    `| ${index + 1} | ${clean(item.name)} | ${item.papers.size} | ${item.peer.size} | ${[...item.topics].join('、')} | ${item.examples.join('；')} |`
  ).join('\n')
  return `${frontmatter}

# 团队与机构雷达

> 全球统一口径。排名先看官方同行评审工作覆盖，再看经核验的精读论文数；多机构合著会同时计入各机构，因此本页不能与论文总数直接相加。

| 排名 | 机构 | 相关工作 | 官方评审工作 | 方向布局 | 代表工作 |
|---:|---|---:|---:|---|---|
${rows}

## 读表原则

- 产量不是唯一质量指标；持续跨月、跨方向和独立评审证据更重要。
- arXiv 通常不含 affiliation，本页只使用官方 proceedings 和已核验作者/项目页。
- “团队”按论文作者组合与独立项目线判断，不将同一系列版本重复视为独立验证。

<!-- 更新标记：团队与机构雷达 最后更新 2026.07 -->`
}

function weakSignalsPage() {
  const signalCards = forecasts.signals.map((signal) => {
    const evidence = signal.evidence_ids.map((id) => byId.get(id)).filter(Boolean).map(titleLink).join('；')
    return `
## ${signal.rank}. ${signal.title}

**置信度 / 时间窗：** ${signal.confidence} · ${signal.horizon}

**已经观察到的事实。** ${signal.observed}

**我们的判断。** ${signal.judgment}

**论文证据。** ${evidence}

| 验证路标 | 反证条件 |
|---|---|
| ${signal.confirm} | ${signal.falsifier} |

**战略含义。** ${signal.strategic}`
  }).join('\n')
  return `${frontmatter}

# 弱信号探测与未来判断

> 热门 topic 说明共识已经形成；本页寻找的是尚未成为高频标签、却可能提前暴露下一轮瓶颈迁移的“蛛丝马迹”。预测截至 ${forecasts.as_of}，不是事实陈述。

## 共识热度与弱信号有什么不同

| 维度 | 共识热点 | 有价值的弱信号 |
|---|---|---|
| 数量 | 同月大量论文 | 初期只有 1–3 项 |
| 命名 | 已有统一标签 | 多个团队用不同名字解决同一问题 |
| 证据 | benchmark 密集 | 出现新的真机指标、失败类型或系统约束 |
| 风险 | 容易追高与同质化 | 容易误判、需要明确反证 |
| 用途 | 判断资源拥挤度 | 提前布局能力、数据和基础设施 |

## 五步弱信号探测器

\`\`\`mermaid
flowchart LR
  A["异常点<br/>新能力 / 新失败类型<br/> "] --> B["去项目簇<br/>同团队只算一次<br/> "]
  B --> C["跨名词对齐<br/>是否解决同一瓶颈<br/> "]
  C --> D["证据升级<br/>仿真→真机→独立采用<br/> "]
  D --> E["设置路标<br/>3–12 月可验证<br/> "]
  E --> F["设置反证<br/>失败即降级<br/> "]
\`\`\`

每个候选弱信号按以下维度评分：

| 维度 | 分值 | 问题 |
|---|---:|---|
| 新颖性 | 0–2 | 是否引入新的能力、数据来源、接口或评价指标？ |
| 独立性 | 0–2 | 是否有至少两个不重叠作者/机构团队？ |
| 证据升级 | 0–2 | 是否从仿真走向真机、从成功率走向恢复/长时/跨本体？ |
| 使能性 | 0–1 | 是否可能成为其他路线的基础设施？ |
| 可证伪 | 0–1 | 未来 3–12 个月是否有明确验证路标？ |
| 同项目簇惩罚 | 0 至 −2 | 是否只是同一模型/数据集的多篇衍生论文？ |
| 命名潮惩罚 | 0 至 −2 | 是否只是换模型名而没有新能力？ |

总分 5 分以上进入月度弱信号卡；只有跨月扩散或获得独立评审后才升级为 B/A。数量再大，也不会自动升级。

## 未来趋势判断

${signalCards}

## 如何持续更新

每月新增论文后，先检查路标而不是重写预测：出现第三方采用、真实机器人恢复率、跨硬件 benchmark 或开放训练资产时升级；连续两个季度没有独立跟进、只剩同团队系列工作或真机增益消失时降级。

<!-- 更新标记：弱信号与未来判断 最后更新 2026.07 -->`
}

function benchmarkPage() {
  return `${frontmatter}

# 评估基准与证据门槛

> benchmark 的作用是让不同方法可比较，不是替代真实部署。本站尤其关注测试任务泄漏、控制频率、长时失败和跨本体可比性。

| Benchmark / 评测 | 主要覆盖 | 优点 | 不能证明什么 | 官方入口 |
|---|---|---|---|---|
| LIBERO | 语言条件、多任务、持续学习 | 任务组合清晰、VLA 使用广 | 真机动力学与开放世界 | [GitHub](https://github.com/Lifelong-Robot-Learning/LIBERO) |
| CALVIN | 长时语言条件桌面操作 | 支持多步序列 | 机器人/场景单一 | [GitHub](https://github.com/mees/calvin) |
| RLBench | 多任务仿真操作 | 任务数量大、接口成熟 | sim-to-real 与真实接触 | [GitHub](https://github.com/stepjam/RLBench) |
| ManiSkill | 高性能仿真与 manipulation | 并行仿真、可复现 | 人类环境长尾 | [官网](https://maniskill.ai/) |
| RoboCasa | 日常场景与大规模仿真 | 场景多样、数据生成 | 真实家庭鲁棒性 | [官网](https://robocasa.ai/) |
| LIBERO-PRO | VLA 记忆与公平性压力测试 | 检查训练泄漏与鲁棒性 | 真实硬件故障 | [arXiv](https://arxiv.org/abs/2510.03827) |
| ManipArena | 推理型 generalist manipulation 真机评测 | 更接近真实执行 | 仍受具体硬件和任务集限制 | [arXiv](https://arxiv.org/abs/2603.28545) |

## 建议的下一代评测矩阵

| 维度 | 最低报告项 | 为什么重要 |
|---|---|---|
| 执行 | 成功率、控制频率、端到端延迟 | 区分“能推理”与“能实时控制” |
| 长时 | 子任务完成曲线、失败位置、恢复率 | 避免平均成功率掩盖级联失败 |
| 泛化 | 新任务、新场景、新物体、新本体分别报告 | “泛化”不是一个单一维度 |
| 世界模型 | 同算力控制收益、roll-out 漂移、model bias | 生成质量不等于规划价值 |
| 触觉/灵巧 | 跨传感器和跨手型迁移、接触失败恢复 | 防止硬件专用结果被误读为通用能力 |
| 开放性 | 代码、数据、权重、硬件配置与评测脚本 | 支持独立复现和后续采用 |

<!-- 更新标记：评估基准 最后更新 2026.07 -->`
}

function quarterlyPage() {
  const quarters = [
    {
      title: '2025 Q3 · 数据入口重构',
      months: ['2025-07', '2025-08', '2025-09'],
      summary: '人类视频、无标签动作和 egocentric/接触表示成为弱信号主线；flow policy 扩散，触觉首次进入 VLA 统一空间，但世界模型的闭环控制证据仍弱。',
    },
    {
      title: '2025 Q4 · 规划与预测汇合',
      months: ['2025-10', '2025-11', '2025-12'],
      summary: 'fast–slow 形成架构簇，world model 从生成与适配转向后训练、搜索和 MPC；跨本体问题从 adapter 转向数据和动作表示。',
    },
    {
      title: '2026 Q1 · 可执行性成为新门槛',
      months: ['2026-01', '2026-02', '2026-03'],
      summary: 'latent action world model 进入 in-the-wild 与 RL simulator，Action CoT/异步触发重写大小脑接口，3 月集中出现 executable alignment、长时接触和真实评测。',
    },
    {
      title: '2026 Q2 · 系统工程与触觉闭环',
      months: ['2026-04', '2026-05', '2026-06'],
      summary: '连续推理、coarse-to-fine 调度、3D trace 与 real-time execution 使 VLA 竞争进入系统层；触觉从融合模态升级为预测与 world model 通道。',
    },
  ]
  const sections = quarters.map((quarter) => {
    const list = quarter.months.flatMap((month) => monthPapers(month))
    const counts = topicCounts(list)
    const keyTrends = quarter.months.flatMap((month) => trends.months[month] ?? [])
      .filter((trend) => trend.grade !== 'D')
      .slice(0, 5)
    return `## ${quarter.title}

${quarter.summary}

| 论文候选 | 基础模型 | 双系统 | 灵巧操作 | 世界模型 | 通用学习 |
|---:|---:|---:|---:|---:|---:|
| ${list.length} | ${counts.foundation} | ${counts.dual_system} | ${counts.dexterous} | ${counts.world_model} | ${counts.general_learning} |

**阶段证据链：**

${keyTrends.map((trend) => `- **${trend.title}（${trend.grade}）**：${trend.change}`).join('\n')}`
  }).join('\n')
  return `${frontmatter}

# 季度演进

> 季度页观察一个信号如何从出现、扩散走向验证，避免逐月噪声掩盖方法迁移。

${sections}

## 2026 年 7 月前瞻

100K 小时级轨迹、视触觉 world-action model 与 Embodied Agent OS 是三个早期信号；由于只覆盖 1–29 日，全部保持 C 级。

<!-- 更新标记：季度演进 最后更新 2026.07 -->`
}

function annualPage() {
  const analysis = periodPapers('analysis')
  const baseline = periodPapers('baseline')
  const currentCounts = topicCounts(analysis)
  const baselineCounts = topicCounts(baseline)
  const rows = topicOrder.map((key) =>
    `| [${topics[key].label}](/directions/${topics[key].slug}) | ${baselineCounts[key]} | ${currentCounts[key]} | ${signed(currentCounts[key] - baselineCounts[key])} | ${percent(currentCounts[key], analysis.length)} |`
  ).join('\n')
  const confirmed = [
    {
      title: 'VLA / generalist policy 已从预印本热点变成正式研究主线',
      ids: ['2410.24164', '2501.09747', '2504.16054'],
      judgment: 'A',
      note: 'π0、FAST、π0.5 等独立正式工作覆盖动作生成、效率和开放世界泛化。',
    },
    {
      title: '快慢分工与中间推理已获得独立评审验证',
      ids: ['2407.08693', '2503.02881', '2601.11404'],
      judgment: 'A',
      note: 'Embodied CoT、Reactive Diffusion Policy 与 ACoT-VLA 从语言推理、视觉触觉控制和动作链三侧验证。',
    },
    {
      title: '机器人世界模型从生成转向控制的路线已被多 venue 接纳',
      ids: ['2504.02792', '2505.11528', '2506.23126', '2512.13030'],
      judgment: 'A',
      note: '视频—动作联合、latent dynamics、3D 物理预测和统一 latent action 都有官方评审证据。',
    },
    {
      title: '灵巧操作的数据与触觉路线已跨团队验证',
      ids: ['2503.02881', '2505.21864', '2603.22264'],
      judgment: 'A',
      note: '视觉触觉、UMI 人类示范与 egocentric 通用手控制形成连续证据链。',
    },
  ]
  const confirmedRows = confirmed.map((item) => {
    const evidence = item.ids.map((id) => byId.get(id)).filter(Boolean)
      .map((paper) => paper.peer_review ? `[${clean(paper.title)}](${paper.peer_review.official_url})` : titleLink(paper)).join('；')
    return `| <span class="signal signal-a">${item.judgment}</span> ${item.title} | ${item.note} | ${evidence} |`
  }).join('\n')
  return `${frontmatter}

# 年度综合：从“更大 VLA”转向“可执行、可纠错、可持续学习”

> 主分析期为 2025 年 7 月—2026 年 6 月。同比增长只在同一宽召回查询口径内有效，不代表全部机器人论文的绝对市场份额。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>${analysis.length}</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>${baseline.length}</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>84</strong><span>逐条核验精读</span></div>
  <div class="radar-kpi"><strong>${peerRecords.length}</strong><span>官方评审锚点</span></div>
</div>

## 五方向年度结构

| 方向 | 同比基线 | 主分析期 | 绝对增量 | 主分析期占比 |
|---|---:|---:|---:|---:|
${rows}

最显著的事实是具身基础模型候选增量远高于其他方向；但弱信号更多出现在双系统调度、触觉 world model、失败恢复和数据闭环，这些领域的论文数量反而不占主导。

## A 级：已确认路线

| 判断 | 为什么升级 | 官方证据 |
|---|---|---|
${confirmedRows}

## 持续升温

- **VLA 后训练与经验学习。** 从 VLA-RFT、π*0.6 到 2026 年的在线自纠错，目标从复制示范转向用部署经验改进。
- **世界模型的可执行性。** 2026 年 3 月后，inverse dynamics reward、RL simulator 和 world-action unified model 密集出现。
- **视触觉闭环。** 触觉从感知输入升级为 future prediction、world model 和 recovery 信号。
- **跨本体数据与动作表示。** 共享人类视频、latent action、接触表示与 embodiment adapter 正在收敛。

## 出现拐点

- **大小脑。** 2025 年重在 planner–policy 结构，2026 年转向异步调度、continuous reasoning、completion gating 和 3D trace。
- **通用性。** 从“同一模型做更多 benchmark”转向“同一训练栈适应真实、灵巧、软体、医疗等高约束任务”。
- **开放。** 从只放权重扩展到数据、训练、评测和低成本采集工具。

## 降温与未兑现

- **只以视频生成质量证明的世界模型：D。** 若不报告规划或控制收益，不再视为强信号。
- **堆叠模块式 VLA：D。** 更换 backbone、adapter 或 action head 而没有新能力的工作增长很快，但战略价值有限。
- **“一个权重跨所有机器人”：C/D。** 现有证据更支持共享表征 + embodiment adapter。
- **开源承诺即生态：D。** 只有出现第三方复现和采用，开源热度才升级为趋势。

## 下一步

真正领先于共识的八项判断见[弱信号探测与未来判断](/analysis/weak-signals)。每项都包含 3–24 个月验证路标和反证条件。

<!-- 更新标记：年度综合 最后更新 2026.07 -->`
}

function executiveSummary() {
  const analysis = periodPapers('analysis')
  const baseline = periodPapers('baseline')
  const curated = papers.filter((paper) => paper.curated && paper.period === 'analysis')
  const real = curated.filter((paper) => evidenceValue(paper, 'real_robot')).length
  const multi = curated.filter((paper) => evidenceValue(paper, 'multi_task')).length
  const cross = curated.filter((paper) => evidenceValue(paper, 'cross_embodiment')).length
  const long = curated.filter((paper) => evidenceValue(paper, 'long_horizon')).length
  const open = curated.filter((paper) =>
    evidenceValue(paper, 'open_code') || evidenceValue(paper, 'open_data') || evidenceValue(paper, 'open_model')).length
  return `${frontmatter}

# 执行摘要

> **版本**：v1.0 · **更新日期**：2026 年 7 月 29 日<br>
> **主分析期**：2025.07–2026.06 · **精读**：${curated.length} 篇 · **官方评审锚点**：${peerRecords.length} 条

过去 12 个月最显眼的共识是 VLA / generalist policy 的论文数量急升；更有战略价值的变化却发生在“模型之外”：实时调度、动作验证与恢复、部署数据飞轮、可执行 world model、视触觉闭环和跨本体接口。**综合判断（推断）：**具身智能正在从“能输出动作”进入“能在物理世界持续运行、发现错误并学习”的阶段。

## 六个年度判断

1. **基础模型是最大共识，不再是最早信号。** 主分析期统一查询口径下，具身基础模型候选占比最高；方向已经拥挤，差异转向执行、数据与后训练。
2. **大小脑的真正拐点是实时系统。** fast–slow 名称本身价值有限，completion gating、continuous reasoning、verifier 和 3D trace 才是接口创新。
3. **world model 的淘汰赛开始。** 能否在同算力下提高闭环规划、RL 样本效率或失败恢复，将把控制模型与普通视频生成分开。
4. **触觉从“小众传感器”变成领先指标。** 它最可能先在接触失败恢复、材料/滑移预测和灵巧 world model 中兑现。
5. **跨本体更可能通过共享表示 + 小型 adapter 实现。** “一个权重直接覆盖所有机器人”的证据仍不足。
6. **数据护城河正在迁移到部署闭环。** 未来关键指标不是总小时，而是失败覆盖、修正效率和新任务上线速度。

## 数据概览

<div class="radar-kpis">
  <div class="radar-kpi"><strong>${analysis.length}</strong><span>主分析期候选</span></div>
  <div class="radar-kpi"><strong>${baseline.length}</strong><span>同比基线候选</span></div>
  <div class="radar-kpi"><strong>${real}/${curated.length}</strong><span>精读真机确认</span></div>
  <div class="radar-kpi"><strong>${open}/${curated.length}</strong><span>精读明确开放披露</span></div>
</div>

| 深度指标 | 分子 / 分母 | 说明 |
|---|---:|---|
| 真实机器人 | ${real}/${curated.length} | 摘要或核验页明确披露 |
| 多任务 | ${multi}/${curated.length} | 不把任务变体自动当作多任务 |
| 跨本体 | ${cross}/${curated.length} | 至少两类机器人/硬件 |
| 长时序 | ${long}/${curated.length} | 明确长时、多阶段或连续任务 |
| 代码/数据/模型开放 | ${open}/${curated.length} | “will release” 不等于已开放 |

## 对研究布局与投资观察的含义

| 观察对象 | 应追问的证据 | 高风险信号 |
|---|---|---|
| VLA 团队 | 真机时延、失败恢复、部署数据回流 | 只报告仿真平均成功率 |
| 世界模型团队 | 同算力控制增益、model bias、闭环时长 | 只展示视频质量 |
| 灵巧/触觉团队 | 跨手型、跨传感器、长时接触 | 单次定制 demo |
| 数据团队 | 有效多样性、失败覆盖、下游边际增益 | 只强调总小时/总帧数 |
| 开源项目 | 第三方复现、外部采用、活跃维护 | 只放模型名或未来承诺 |

## 最重要的非共识机会

按当前证据排序：**实时 VLA 执行栈、verifier/自纠错、部署数据飞轮、控制导向 world model、触觉预测通道、跨本体动作接口、3D trace，以及高风险的 Embodied Agent OS。** 详见[未来判断](/analysis/weak-signals)。

<!-- 更新标记：执行摘要 最后更新 2026.07 -->`
}

function databasePage() {
  const curated = included.filter((paper) => paper.curated)
  const rows = curated.map((paper) =>
    `| ${paper.id} | ${titleLink(paper)} | ${paper.v1_month} | ${topics[paper.primary_topic]?.label ?? paper.primary_topic} | ${paper.confidence} | ${paper.curated ? '精读' : '候选'} | ${paper.peer_review ? officialLink(paper.peer_review) : '—'} |`
  ).join('\n')
  return `${frontmatter}

# 论文证据库

> 本表由 \`data/papers.json\` 自动生成。候选层用于趋势数量；“精读”表示 ID、标题、v1 日期和摘要已逐条复核，并补充贡献、局限和实验信号。

[下载 JSON](https://raw.githubusercontent.com/JoenHune/embodied-ai-radar/main/data/papers.json) · [下载 CSV](https://raw.githubusercontent.com/JoenHune/embodied-ai-radar/main/data/papers.csv) · [下载完整 Markdown 报告](https://raw.githubusercontent.com/JoenHune/embodied-ai-radar/main/embodied-ai-radar-report.md)

## 全量候选分表

- [2024 年候选](/database/2024)
- [2025 年候选](/database/2025)
- [2026 年候选](/database/2026)

JSON/CSV 包含全部 ${included.length} 条纳入统计记录；网页按年份拆分，避免单页过大。

## 精读与核验记录

| arXiv ID | 论文 | v1 月份 | 主方向 | 置信度 | 层级 | 同行评审 |
|---|---|---|---|---|---|---|
${rows}

<!-- 更新标记：论文证据库 最后更新 2026.07 -->`
}

function databaseYearPage(year) {
  const list = included.filter((paper) => paper.v1_month.startsWith(String(year)))
  const rows = list.map((paper) =>
    `| ${paper.id} | ${titleLink(paper)} | ${paper.v1_month} | ${topics[paper.primary_topic]?.label ?? paper.primary_topic} | ${paper.confidence} | ${paper.curated ? '精读' : '候选'} |`
  ).join('\n')
  return `${frontmatter}

# ${year} 年论文候选

> 共 ${list.length} 条；表头可点击排序。候选层用于统一查询口径下的数量结构，精读层已逐条复核。

| arXiv ID | 论文 | v1 月份 | 主方向 | 置信度 | 层级 |
|---|---|---|---|---|---|
${rows}

<!-- 更新标记：${year} 年论文候选 最后更新 2026.07 -->`
}

function referencesPage() {
  const citedIds = new Set([
    ...papers.filter((paper) => paper.curated).map((paper) => paper.id),
    ...peerRecords.map((record) => record.arxiv_id).filter(Boolean),
    ...forecasts.signals.flatMap((signal) => signal.evidence_ids),
    ...Object.values(trends.months).flatMap((items) => items.flatMap((item) => item.evidence_ids)),
  ])
  const cited = [...citedIds].map((id) => byId.get(id)).filter(Boolean)
    .sort((left, right) => left.id.localeCompare(right.id))
  const groups = topicOrder.map((key) => {
    const items = cited.filter((paper) => paper.primary_topic === key)
    return `## ${topics[key].label}

${items.map((paper, index) => `${index + 1}. ${paper.authors?.slice(0, 8).join(', ')}${paper.authors?.length > 8 ? ', et al.' : ''}. (${paper.first_submitted.slice(0, 4)}). [${clean(paper.title)}](${paper.peer_review?.official_url ?? paper.arxiv_url}). ${paper.peer_review ? `*${paper.peer_review.venue} ${paper.peer_review.year}*.` : `arXiv:${paper.id}.`}`).join('\n')}`
  }).join('\n')
  return `${frontmatter}

# 参考文献

> 收录月度精读、趋势卡、未来判断与同行评审页实际引用的唯一工作；官方发表版本优先链接正式页面。

${groups}

<!-- 更新标记：参考文献 最后更新 2026.07 -->`
}

write('monthly/index.md', monthlyIndex())
for (const month of allMonths) write(`monthly/${month}.md`, monthlyPage(month))
for (const [key, direction] of Object.entries(directions)) write(`directions/${direction.slug}.md`, directionPage(key, direction))
write('analysis/executive-summary.md', executiveSummary())
write('analysis/annual.md', annualPage())
write('analysis/weak-signals.md', weakSignalsPage())
write('analysis/peer-review.md', peerReviewPage())
write('analysis/institutions.md', institutionPage())
write('analysis/benchmarks.md', benchmarkPage())
write('quarterly/index.md', quarterlyPage())
write('database/index.md', databasePage())
for (const year of [2024, 2025, 2026]) write(`database/${year}.md`, databaseYearPage(year))
write('references.md', referencesPage())

fs.copyFileSync(path.join(root, 'data/papers.json'), path.join(docs, 'public/papers.json'))
fs.copyFileSync(path.join(root, 'data/papers.csv'), path.join(docs, 'public/papers.csv'))

console.log(`Generated ${allMonths.length} monthly pages, ${Object.keys(directions).length} direction pages and analysis pages.`)
