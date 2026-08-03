import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const docs = path.join(root, 'docs')
const read = (name) => JSON.parse(fs.readFileSync(path.join(root, name), 'utf8'))
const papers = read('data/papers.json')
const trends = read('data/trends.json')
const forecasts = read('data/forecasts.json')
const directions = read('data/directions.json')
const peers = read('data/peer-review.json').records
const validTopics = new Set(['foundation', 'dual_system', 'dexterous', 'world_model', 'general_learning'])
const errors = []
const warnings = []
const assert = (condition, message) => { if (!condition) errors.push(message) }
const warn = (condition, message) => { if (!condition) warnings.push(message) }
const byId = new Map()
const topicLabels = {
  foundation: '具身基础模型',
  dual_system: '大小脑与双系统',
  dexterous: '灵巧操作',
  world_model: '世界模型',
  general_learning: '通用机器人学习',
}
const topicSlugs = {
  foundation: 'foundation-models',
  dual_system: 'dual-system',
  dexterous: 'dexterous-manipulation',
  world_model: 'world-models',
  general_learning: 'general-robot-learning',
}
const signed = (value) => value > 0 ? `+${value}` : String(value)
const percent = (numerator, denominator) => denominator ? `${(numerator / denominator * 100).toFixed(1)}%` : '—'
const changeRate = (current, previous) => {
  if (previous === 0) return current === 0 ? '—' : '新增'
  const value = (current - previous) / previous * 100
  return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`
}
const previousYearMonth = (month) => `${Number(month.slice(0, 4)) - 1}-${month.slice(5)}`
const previousMonth = (month) => {
  const year = Number(month.slice(0, 4))
  const monthNumber = Number(month.slice(5))
  return monthNumber === 1
    ? `${year - 1}-12`
    : `${year}-${String(monthNumber - 1).padStart(2, '0')}`
}
const topicCounts = (list) => Object.fromEntries([...validTopics].map((topic) => [
  topic,
  list.filter((paper) => paper.primary_topic === topic).length,
]))

assert(Array.isArray(papers), 'data/papers.json must be an array')
for (const paper of papers) {
  assert(/^\d{4}\.\d{4,5}$/.test(paper.id), `invalid arXiv ID: ${paper.id}`)
  assert(!byId.has(paper.id), `duplicate arXiv ID: ${paper.id}`)
  byId.set(paper.id, paper)
  assert(Boolean(paper.title), `${paper.id}: missing title`)
  assert(/^\d{4}-\d{2}-\d{2}$/.test(paper.first_submitted), `${paper.id}: invalid first_submitted`)
  assert(/^\d{4}-\d{2}$/.test(paper.v1_month), `${paper.id}: invalid v1_month`)
  assert(validTopics.has(paper.primary_topic), `${paper.id}: invalid primary topic ${paper.primary_topic}`)
  assert(paper.arxiv_url === `https://arxiv.org/abs/${paper.id}`, `${paper.id}: non-canonical arXiv URL`)
  if (paper.curated) {
    assert(paper.v1_month === paper.first_submitted.slice(0, 7), `${paper.id}: curated v1 month/date mismatch`)
    assert(Boolean(paper.contribution_zh), `${paper.id}: curated contribution missing`)
    assert(Boolean(paper.limitation_zh), `${paper.id}: curated limitation missing`)
    assert(Boolean(paper.verification), `${paper.id}: curated verification missing`)
    const verified = paper.verification?.title_and_id_match ?? paper.verification?.id_title_match
    assert(verified === true, `${paper.id}: curated title/ID not verified`)
  }
}

const included = papers.filter((paper) => paper.included)
const curated = papers.filter((paper) => paper.curated)
assert(included.length >= 2000, `included corpus unexpectedly small: ${included.length}`)
assert(curated.length === 104, `expected 104 curated papers, got ${curated.length}`)
assert(curated.filter((paper) => paper.period === 'analysis').length === 84, 'expected 84 main-period curated papers')
assert(curated.filter((paper) => paper.period === 'provisional').length === 20, 'expected 20 complete-July curated papers')

const normalizedTitles = new Map()
for (const paper of included) {
  const key = paper.title.toLowerCase().replace(/[^a-z0-9]+/g, '')
  if (normalizedTitles.has(key)) errors.push(`duplicate normalized title: ${paper.id} / ${normalizedTitles.get(key)}`)
  normalizedTitles.set(key, paper.id)
  assert(!/(autonomous driving|self-driving|autonomous vehicle|gui visual agent|web agent)/i.test(paper.title),
    `${paper.id}: hard-excluded title entered corpus`)
}

assert(peers.length >= 25, `peer-review anchors unexpectedly small: ${peers.length}`)
const peerKeys = new Set()
const officialDomains = new Set([
  'proceedings.mlr.press', 'openaccess.thecvf.com', 'www.roboticsproceedings.org',
  'papers.nips.cc', 'openreview.net', 'ieeexplore.ieee.org', 'journals.sagepub.com',
  'www.science.org', 'www.nature.com',
])
for (const peer of peers) {
  const key = peer.arxiv_id || peer.title.toLowerCase()
  assert(!peerKeys.has(key), `duplicate peer-review record: ${key}`)
  peerKeys.add(key)
  assert(/^https:\/\//.test(peer.official_url), `${key}: official URL must use HTTPS`)
  const domain = new URL(peer.official_url).hostname
  assert(officialDomains.has(domain), `${key}: unapproved official domain ${domain}`)
  assert(/peer_reviewed|published|accepted|official/i.test(peer.status), `${key}: unsupported peer status ${peer.status}`)
  assert(validTopics.has(
    Object.entries({
      foundation: '具身基础模型',
      dual_system: '大小脑与双系统',
      dexterous: '灵巧操作',
      world_model: '世界模型',
      general_learning: '通用机器人学习',
    }).find(([, label]) => label === peer.primary_topic)?.[0],
  ), `${key}: invalid peer-review topic`)
}

const expectedMonths = [
  '2025-07', '2025-08', '2025-09', '2025-10', '2025-11', '2025-12',
  '2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07',
]
assert(JSON.stringify(Object.keys(trends.months)) === JSON.stringify(expectedMonths), 'trend months missing or out of order')
for (const [month, items] of Object.entries(trends.months)) {
  assert(items.length >= 3 && items.length <= 5, `${month}: expected 3–5 trends`)
  for (const item of items) {
    assert(['A', 'B', 'C', 'D'].includes(item.grade), `${month}: invalid trend grade`)
    assert(item.evidence_ids.length >= 1, `${month}/${item.title}: missing evidence`)
    for (const id of item.evidence_ids) assert(byId.has(id), `${month}/${item.title}: missing paper ${id}`)
    if (item.grade === 'B') {
      assert(item.evidence_ids.length >= 3, `${month}/${item.title}: B grade needs at least 3 papers`)
      const teams = new Set(item.evidence_ids.map((id) => byId.get(id)?.authors?.[0]).filter(Boolean))
      assert(teams.size >= 2, `${month}/${item.title}: B grade needs at least 2 independent author teams`)
    }
  }
  const page = path.join(docs, 'monthly', `${month}.md`)
  assert(fs.existsSync(page), `${month}: generated page missing`)
  if (fs.existsSync(page)) {
    const text = fs.readFileSync(page, 'utf8')
    const current = included.filter((paper) => paper.v1_month === month)
    const previous = included.filter((paper) => paper.v1_month === previousMonth(month))
    const baseline = included.filter((paper) => paper.v1_month === previousYearMonth(month))
    const currentCounts = topicCounts(current)
    const previousCounts = topicCounts(previous)
    const baselineCounts = topicCounts(baseline)
    assert(text.includes(`<strong>${current.length}</strong><span>纳入统计候选</span>`), `${month}: generated count mismatch`)
    assert(text.includes('| 环比增量 | 环比 |'), `${month}: month-over-month topic columns missing`)
    for (const topic of validTopics) {
      const expectedRow = `| [${topicLabels[topic]}](/directions/${topicSlugs[topic]}) | ${currentCounts[topic]} | ${percent(currentCounts[topic], current.length)} | ${previousCounts[topic]} | ${signed(currentCounts[topic] - previousCounts[topic])} | ${changeRate(currentCounts[topic], previousCounts[topic])} | ${baselineCounts[topic]} | ${signed(currentCounts[topic] - baselineCounts[topic])} | ${changeRate(currentCounts[topic], baselineCounts[topic])} |`
      assert(text.includes(expectedRow), `${month}/${topic}: MoM/YoY topic row mismatch`)
    }
    const expectedTotal = `| **总计** | **${current.length}** | **100.0%** | **${previous.length}** | **${signed(current.length - previous.length)}** | **${changeRate(current.length, previous.length)}** | **${baseline.length}** | **${signed(current.length - baseline.length)}** | **${changeRate(current.length, baseline.length)}** |`
    assert(text.includes(expectedTotal), `${month}: MoM/YoY total row mismatch`)
    if (month === '2026-07') {
      assert(text.includes('**7 月完整月。**'), 'July complete-month coverage note missing')
      assert(text.includes('## 7 月完整月研判'), 'July deep-dive section missing')
      assert(items.length === 5, 'July must contain 5 full trend cards')
    }
  }
}

const augustPage = path.join(docs, 'monthly', '2026-08.md')
assert(fs.existsSync(augustPage), 'August early-snapshot page missing')
if (fs.existsSync(augustPage)) {
  const text = fs.readFileSync(augustPage, 'utf8')
  assert(text.includes('月初快照，截至 4 日'), 'August snapshot cutoff missing')
  assert(text.includes('月初空窗，不计算 −100%'), 'August no-false-MoM warning missing')
  assert(text.includes('## 8 月要验证的六条早期命题'), 'August forward-signal section missing')
}

assert(forecasts.signals.length >= 6, 'future signals unexpectedly sparse')
for (const signal of forecasts.signals) {
  assert(Boolean(signal.confirm), `forecast ${signal.title}: missing confirmation signpost`)
  assert(Boolean(signal.falsifier), `forecast ${signal.title}: missing falsifier`)
  for (const id of signal.evidence_ids) assert(byId.has(id), `forecast ${signal.title}: missing paper ${id}`)
}

for (const [key, direction] of Object.entries(directions)) {
  assert(validTopics.has(key), `invalid direction key ${key}`)
  assert(direction.representative_ids.length >= 6, `${key}: representative set too small`)
  for (const id of direction.representative_ids) assert(byId.has(id), `${key}: missing representative ${id}`)
  assert(fs.existsSync(path.join(docs, 'directions', `${direction.slug}.md`)), `${key}: generated direction page missing`)
}

const publicJson = path.join(docs, 'public/papers.json')
const hash = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')
assert(fs.existsSync(publicJson), 'public papers.json missing')
if (fs.existsSync(publicJson)) assert(hash(publicJson) === hash(path.join(root, 'data/papers.json')), 'public/data JSON mismatch')
const csvLines = fs.readFileSync(path.join(root, 'data/papers.csv'), 'utf8').trimEnd().split('\n').length
assert(csvLines === papers.length + 1, `CSV row count mismatch: ${csvLines} vs ${papers.length + 1}`)

const requiredPages = [
  'analysis/executive-summary.md', 'analysis/annual.md', 'analysis/weak-signals.md',
  'analysis/peer-review.md', 'analysis/institutions.md', 'analysis/benchmarks.md',
  'quarterly/index.md', 'database/index.md', 'references.md',
]
for (const page of requiredPages) assert(fs.existsSync(path.join(docs, page)), `required page missing: ${page}`)

const contentFiles = fs.readdirSync(path.join(docs, 'analysis')).map((file) => path.join(docs, 'analysis', file))
for (const file of contentFiles) {
  const text = fs.readFileSync(file, 'utf8')
  warn(!/(^|\s)(TODO|TBD)(\s|$)|待填充/i.test(text), `placeholder-like text in ${path.relative(root, file)}`)
}

if (warnings.length) console.warn(`Warnings (${warnings.length}):\n- ${warnings.join('\n- ')}`)
if (errors.length) {
  console.error(`Audit failed (${errors.length}):\n- ${errors.join('\n- ')}`)
  process.exit(1)
}
console.log(`Audit passed: ${papers.length} records, ${included.length} included, ${curated.length} curated, ${peers.length} official peer-review anchors, ${forecasts.signals.length} forecasts.`)
