import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const docs = path.join(root, 'docs')
const read = (name, fallback) => {
  const target = path.join(root, name)
  return fs.existsSync(target) ? JSON.parse(fs.readFileSync(target, 'utf8')) : fallback
}
const write = (name, content) => {
  const target = path.join(docs, name)
  fs.mkdirSync(path.dirname(target), { recursive: true })
  fs.writeFileSync(target, `${content.trim()}\n`)
}
const clean = (value = '') => String(value).replaceAll('|', '\\|').replace(/\s+/g, ' ').trim()
const frontmatter = `---\noutline: deep\n---`

const agenda = read('config/research-agenda.json', { questions: [], omitted_directions: [] })
const taxonomy = read('config/taxonomy-v2.json', { categories: {} })
const registry = read('config/source-registry.json', { window: {} })
const preprints = read('data/preprints.json', [])
const included = preprints.filter((paper) => paper.relevance?.status === 'included')
const snapshotDate = registry.window?.until ?? agenda.updated

const topicLink = (key) => {
  const topic = taxonomy.categories[key]
  return topic ? `[${topic.code}](/frontiers/${key.replaceAll('_', '-')})` : `\`${key}\``
}
const gradeClass = (grade) => `signal signal-${grade.toLowerCase()}`
const paperText = (paper) => `${paper.title ?? ''} ${paper.abstract ?? ''}`.toLowerCase()
const questionMatch = (paper, question) => {
  const text = paperText(paper)
  const hits = question.query_terms.filter((term) => text.includes(term.toLowerCase()))
  return { matched: hits.length > 0, hits }
}

const cutoff = new Date(`${snapshotDate}T00:00:00Z`)
const previousMonthEnd = new Date(Date.UTC(cutoff.getUTCFullYear(), cutoff.getUTCMonth(), 0))
const cutoffMonthEndDay = new Date(Date.UTC(cutoff.getUTCFullYear(), cutoff.getUTCMonth() + 1, 0)).getUTCDate()
const snapshotStatus = cutoff.getUTCDate() === cutoffMonthEndDay ? 'complete' : 'partial'
const latestCompleteDate = snapshotStatus === 'complete' ? cutoff : previousMonthEnd
const monthKey = (date) => `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}`
const latestCompleteMonth = monthKey(latestCompleteDate)
const rollingMonths = []
for (let offset = 11; offset >= 0; offset -= 1) {
  rollingMonths.push(monthKey(new Date(Date.UTC(
    latestCompleteDate.getUTCFullYear(),
    latestCompleteDate.getUTCMonth() - offset,
    1,
  ))))
}
const snapshotMonth = snapshotDate.slice(0, 7)

const evidenceRecords = []
const summaries = {}
for (const question of agenda.questions) {
  const matches = []
  for (const paper of included) {
    const result = questionMatch(paper, question)
    if (!result.matched) continue
    matches.push(paper)
    let record = evidenceRecords.find((item) => item.preprint_id === paper.preprint_id)
    if (!record) {
      record = {
        preprint_id: paper.preprint_id,
        work_id: paper.work_id,
        arxiv_id: paper.arxiv_id,
        first_submitted: paper.first_submitted,
        question_ids: [],
        hits: {},
      }
      evidenceRecords.push(record)
    }
    record.question_ids.push(question.id)
    record.hits[question.id] = result.hits
  }
  const monthly = Object.fromEntries(rollingMonths.map((month) => [
    month,
    matches.filter((paper) => paper.first_submitted?.startsWith(month)).length,
  ]))
  summaries[question.id] = {
    rolling_12_complete_months: Object.values(monthly).reduce((sum, value) => sum + value, 0),
    current_snapshot: matches.filter((paper) => paper.first_submitted?.startsWith(snapshotMonth)).length,
    monthly,
    strict_peer_anchors: question.evidence.filter((item) => item.type === '同行评审').length,
  }
}
evidenceRecords.sort((left, right) => left.first_submitted.localeCompare(right.first_submitted) || left.arxiv_id.localeCompare(right.arxiv_id))

const sidecar = {
  version: agenda.version,
  generated_at: snapshotDate,
  rolling_window: { from: `${rollingMonths[0]}-01`, until: latestCompleteDate.toISOString().slice(0, 10), months: rollingMonths },
  snapshot: { month: snapshotMonth, until: snapshotDate, status: snapshotStatus },
  counting_rule: agenda.design.counting_rule,
  question_summaries: summaries,
  records: evidenceRecords,
}
const sidecarText = `${JSON.stringify(sidecar, null, 2)}\n`
fs.writeFileSync(path.join(root, 'data', 'research-question-evidence.json'), sidecarText)
fs.writeFileSync(path.join(docs, 'public', 'research-question-evidence.json'), sidecarText)

const summaryRows = agenda.questions.map((question) => {
  const summary = summaries[question.id]
  const topics = question.mapped_topics.map(topicLink).join(' / ')
  return `| ${question.id} | ${question.priority} | [${clean(question.title)}](#${question.id.toLowerCase()}) | <span class="${gradeClass(question.assessment)}">${question.assessment}</span> | ${clean(question.role)} | ${topics} | ${summary.rolling_12_complete_months} | ${summary.current_snapshot} | ${summary.strict_peer_anchors} |`
}).join('\n')

const heatRows = agenda.questions.map((question) => {
  const summary = summaries[question.id]
  return `| ${question.id} · ${clean(question.title)} | ${rollingMonths.map((month) => summary.monthly[month]).join(' | ')} |`
}).join('\n')

const questionCards = agenda.questions.map((question) => {
  const evidence = question.evidence.map((item) =>
    `- [${clean(item.title)}](${item.url}) — ${item.type} · ${clean(item.note)}`
  ).join('\n')
  return `## ${question.id} · ${question.title}

**战略优先级：** ${question.priority} · **外部证据等级：** <span class="${gradeClass(question.assessment)}">${question.assessment}</span> · **性质：** ${question.role}

**当前判断。** ${question.claim}

**对应主方向。** ${question.mapped_topics.map(topicLink).join('、')}

**公开证据：**

${evidence}

**决定性指标。** ${question.metrics.join('；')}。

**反证条件。** ${question.falsifier}`
}).join('\n\n')

write('questions/index.md', `${frontmatter}

# 问题地图：哪些瓶颈正在接近解决

> 本页把 Alphaist 内部研究材料转为雷达的正交“问题层”；公开站点不暴露私有飞书地址。D1–D15 回答论文主要研究什么；Q0–Q10 回答关键系统瓶颈是否正在被解决。两层不能相加，P0/P1/P2 也不等于 A/B/C 证据等级。

::: warning 证据边界
${agenda.source.note} 自动计数只是标题/摘要词表命中的相关工作密度，不自动升级趋势；每项判断仍需结合独立团队、真机、正式发表和反证。
:::

## 总判断

飞书文档抓住了一个真实变化：具身智能的领先差异正在从单一模型扩展到**接触表征—可执行动作—运行时验证—失败回流—软硬件迭代**。但其中既有当前主线，也有开放科学问题和工程门槛，不能全部写成“已确认趋势”。

| ID | 战略优先级 | 研究问题 | 证据 | 性质 | D 类映射 | 最近 12 个完整月词表命中 | ${snapshotMonth} ${snapshotStatus === 'complete' ? '完整月（已含在 12 月窗口）' : `截至 ${Number(snapshotDate.slice(-2))} 日`} | 严格评审锚点 |
|---|---|---|---|---|---|---:|---:|---:|
${summaryRows}

## 最近 12 个完整月问题密度

> 时间窗：${rollingMonths[0]}—${latestCompleteMonth}。这是多标签高召回代理；同一论文可进入多个 Q，不能用行列合计替代主方向统计。

| 问题轴 | ${rollingMonths.join(' | ')} |
|---|${rollingMonths.map(() => '---:').join('|')}|
${heatRows}

${questionCards}

## 如何进入月度雷达

1. 月度页继续先报告 D1–D15 的互斥主方向数量。
2. 问题层只报告工作密度、证据升级和反证，不制造第二套互斥 taxonomy。
3. A/B/C 由人工证据判断；自动词表只负责发现候选。
4. 每次更新优先检查决定性指标，而不是论文是否使用同一个热门名称。

[下载问题证据 sidecar](/embodied-ai-radar/research-question-evidence.json)
`)

const gapRows = agenda.omitted_directions.map((gap) =>
  `| ${gap.id} | ${clean(gap.title)} | ${clean(gap.type)} | ${gap.mapped_topics.map(topicLink).join(' / ')} | ${clean(gap.why)} | ${gap.evidence.map((item) => `[${clean(item.title)}](${item.url})`).join('；')} | ${clean(gap.radar_action)} |`
).join('\n')

write('questions/blind-spots.md', `${frontmatter}

# 文档之外：具身研究雷达还必须看什么

> 原文是一份很强的“单机器人灵巧操作迭代纲领”，但不是完整的具身智能地图。以下缺口大多已经由 D1–D15 覆盖，因此重点是补充研究叙事与横向证据，而不是继续增加互斥主方向。

| ID | 文档遗漏/弱覆盖方向 | 类型 | 已有 D 类 | 为什么重要 | 公开锚点 | 雷达处理 |
|---|---|---|---|---|---|---|
${gapRows}

## 是否需要新增 D16

当前不正式新增。**本体、软体机器人与学习驱动形态设计**值得建立观察池，但升级前应同时满足：至少 3 个独立团队、2 个正式 venue，并且论文主贡献确实是“本体设计与学习联合优化”，而不是纯机械、材料或没有自主学习闭环的硬件论文。

## 最重要的补充判断

- 失败恢复不等于安全保证；风险校准、运行时保障、形式约束和物理攻防需要独立观察。
- Loco-manipulation 不等于开放世界导航；建筑级移动操作、动态语义地图和长期空间记忆仍有独立问题结构。
- 人不只是示范者或接管者，也是协作者、被服务者和共同决策者。
- 单机数据飞轮不等于 fleet learning；异构多机器人协作、策略分发与集体回归测试仍被低估。
- 端侧算力、能耗、网络依赖、标定、维护和数据权利属于战略看板变量，不应伪装成论文主方向。
`)

write('methods/research-question-layer.md', `${frontmatter}

# 研究问题层方法

## 为什么不改 D1–D15

D1–D15 是每篇工作唯一主分类，用于稳定月度曲线。问题层是多标签镜头：触觉、失败数据、软硬件共设计和主动感知天然跨越多个主方向。如果直接改主分类或分类顺序，会把历史曲线变化与真实研究变化混在一起。

## 自动层

- 数据源：已纳入的 arXiv 母库记录。
- 日期：首次提交 v1。
- 匹配：标题与摘要对公开词表做不区分大小写的子串匹配。
- 输出：\`data/research-question-evidence.json\`，记录论文命中的 Q 与具体词项。
- 限制：高召回计数只能表示相关工作密度，不能证明研究命题成立。

## 人工判断层

| 等级 | 使用条件 |
|---|---|
| A | 多团队或严格同行评审已确认路线，但不代表具体科学问题完全解决 |
| B | 过去 12 个月出现多个独立研究簇，仍缺统一评测、跨平台复现或成本对照 |
| C | 高价值早期假设，证据主要来自少量预印本、系统原型或内部经验 |
| D | 反证增加、缺少独立跟进，或结果只剩命名和单一 demo |

P0/P1/P2 只表示战略依赖顺序，与 A/B/C/D 外部证据等级相互独立。

## 升级与降级

- 升级优先看真机、独立团队、正式发表、跨硬件复现和决定性指标。
- 只有关键词数量增加而没有新能力，不升级。
- 反证条件被触发、连续两个季度没有独立跟进或成本不可接受时降级。
- 安全、评测和软硬件变量可以成为关键门槛，但不会仅因“论文少”被误写成弱方向。
`)

console.log(`Generated research question layer: ${agenda.questions.length} questions, ${evidenceRecords.length} matched preprints.`)
