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
const frontmatter = `---\noutline: deep\n---`
const clean = (value = '') => String(value).replaceAll('|', '\\|').replace(/\s+/g, ' ').trim()
const pct = (n, d) => d ? `${(n / d * 100).toFixed(1)}%` : '—'
const fmt = (n) => Number(n ?? 0).toLocaleString('zh-CN')
const signed = (n) => n > 0 ? `+${n}` : String(n)
const change = (n, d) => {
  if (!d) return n ? '新增' : '—'
  const value = (n - d) / d * 100
  return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`
}
const taxonomy = read('config/taxonomy-v2.json', { categories: {} })
const sourceRegistry = read('config/source-registry.json', {})
const preprints = read('data/preprints.json', [])
const preprintCoverage = read('data/preprint-coverage.json', {})
const publications = read('data/publications.json', [])
const publicationCoverage = read('data/publication-coverage.json', { by_venue: {} })
const official = read('data/official-proceedings.json', [])
const officialCoverage = read('data/official-container-coverage.json', {})
const officialPrograms = read('data/official-programs.json', [])
const officialProgramCoverage = read('data/official-program-coverage.json', {})
const repositories = read('data/repositories.json', [])
const repositoryCoverage = read('data/repository-coverage.json', {})
const works = read('data/works.json', [])
const workCoverage = read('data/work-coverage.json', {})
const legacyPapers = read('data/papers.json', [])
const legacyPeers = read('data/peer-review.json', { records: [] }).records
const includedPreprints = preprints.filter((row) => row.relevance?.status === 'included')

const topicEntries = Object.entries(taxonomy.categories)
const topicSlug = (key) => key.replaceAll('_', '-')
const topicLabel = (key) => taxonomy.categories[key]?.label ?? key ?? '待复核'
const screeningLabel = {
  included: '直接候选',
  candidate: '边界候选',
  manual_review: '待摘要/人工复核',
  excluded: '排除',
}
const verificationLabel = {
  peer_reviewed_official_proceedings: '官方 proceedings',
  official_publisher_page_verified: '出版社页面已核验',
  publisher_url_from_registered_doi: 'DOI 已登记，待逐页核验',
  discovered_needs_official_check: '仅发现，待官方核验',
}

for (const [source, publicName] of [
  ['data/preprints.json', 'preprints.json'],
  ['data/publications.json', 'publications.json'],
  ['data/official-proceedings.json', 'official-proceedings.json'],
  ['data/official-programs.json', 'official-programs.json'],
  ['data/repositories.json', 'repositories.json'],
  ['data/works.json', 'works.json'],
]) {
  const input = path.join(root, source)
  if (fs.existsSync(input)) {
    const output = path.join(docs, 'public', publicName)
    fs.mkdirSync(path.dirname(output), { recursive: true })
    fs.copyFileSync(input, output)
  }
}

const coverageRows = Object.entries(publicationCoverage.by_venue ?? {})
  .map(([venue, item]) =>
    `| ${venue} | ${item.mother_corpus ?? 0} | ${item.in_window ?? 0} | ${item.included_in_window ?? 0} | ${item.candidate_in_window ?? 0} | ${item.manual_review_in_window ?? 0} | ${item.with_abstract ?? 0} | ${item.with_arxiv ?? 0} | ${item.with_doi ?? 0} |`
  ).join('\n') || '| — | — | — | — | — | — | — | — |'

const officialRows = (officialCoverage.manifests ?? []).map((item) =>
  `| [${item.container_id}](${item.url}) | ${item.venue} ${item.event_year} | ${item.observed_count} | ${item.expected_count} | ${item.complete ? '完整' : '不完整'} | ${item.publication_date} |`
).join('\n') || '| — | — | — | — | — | — |'

const taxonomyRows = topicEntries.map(([key, item]) =>
  `| ${item.code} | [${item.label}](/frontiers/${topicSlug(key)}) | ${item.layer} | ${item.include.slice(0, 5).map(clean).join('、')} |`
).join('\n')

write('analysis/corpus-expansion.md', `${frontmatter}

# 语料扩充与覆盖审计

> 数据截点：2026-07-29。这里把“母集”“自动相关候选”“边界复核”“精读锚点”分开，避免再用精选篇数冒充总覆盖量。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>${fmt(preprintCoverage.mother_corpus ?? preprints.length)}</strong><span>arXiv 母集</span></div>
  <div class="radar-kpi"><strong>${fmt(publicationCoverage.in_window_records ?? publicationCoverage.mother_corpus ?? publications.length)}</strong><span>窗口内正式发表母集</span></div>
  <div class="radar-kpi"><strong>${fmt(officialCoverage.strict_official_records ?? official.length)}</strong><span>完整官方容器记录</span></div>
  <div class="radar-kpi"><strong>${fmt(officialProgramCoverage.records ?? officialPrograms.length)}</strong><span>官方节目/待 proceedings</span></div>
  <div class="radar-kpi"><strong>${fmt(repositoryCoverage.repository_count ?? repositories.length)}</strong><span>GitHub 核验仓库</span></div>
</div>

## 为什么旧数据看起来很多，实际仍然小

旧版的 ${legacyPapers.length.toLocaleString('zh-CN')} 条记录来自五组 Semantic Scholar 关键词宽召回，其中只有 ${legacyPeers.length} 条正式发表锚点。它没有把 arXiv 全量采集结果并入主库，Semantic Scholar 的分页 token 也未完整消费；同时，旧 schema 强制要求 arXiv ID，导致没有预印本映射的期刊/会议论文无法入库。

新版拆成三条独立管线：

1. **arXiv 母集**：完整 cs.RO 月度拉取，再补 cs.AI/CV/LG 中的机器人与具身主题；月份始终按 v1。
2. **正式发表母集**：ICRA、IROS、RSS、CoRL、RA-L、T-RO、IJRR、Science Robotics 独立采集；无 arXiv ID 也可存在。
3. **开源生态**：论文链接、GitHub Search、机构组织页和 README 反向映射；stars 只作为传播元数据，不进入独立采用分。

## 正式发表漏斗

| Venue | 母集（含去重前缘） | 窗口内 | 窗口内直接候选 | 窗口内边界候选 | 窗口内待摘要/人工 | 有摘要 | 有 arXiv | 有 DOI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
${coverageRows}

“母集”是 venue 内采到的全部论文版本；“直接候选”是 v2 词表与语境自动筛出的具身智能工作，并非最终趋势结论。DBLP/Crossref/Semantic Scholar 只承担发现或字段补全；严格同行评审标签仍需官方 proceedings、OpenReview 最终录用或出版社文章页。

## 严格官方容器对账

| 容器 | Venue | 实际条目 | 预期条目 | 状态 | 正式日期 |
|---|---|---:|---:|---|---|
${officialRows}

四个静态官方容器共 ${officialCoverage.strict_official_records ?? official.length} 条，条目数逐容器完全一致后才入“严格官方”层。RSS 2026 等只有 accepted list、尚无 proceedings 的单元将单列 pending，不混入严格覆盖率。

截至截点另有 ${officialProgramCoverage.by_venue?.ICRA ?? 0} 条 ICRA 2026 官方 program 记录和 ${officialProgramCoverage.by_venue?.RSS ?? 0} 条 RSS 2026 官方录用记录。前者可能含 RA-L/T-RO/RAM 展示，后者尚待 RSS 22 proceedings；两类均进入发现母集，但严格覆盖率分子为 0。

## v2 方向体系：从五类扩展到 ${topicEntries.length} 类

| 编号 | 方向 | 层级 | 代表检索表达 |
|---|---|---|---|
${taxonomyRows}

方向数不再预设。主方向只回答“论文最主要解决什么”，同一工作仍可拥有次方向、能力标签、基础设施标签和成熟度标签。新增方向是否进入月度主导航，要同时满足样本规模、跨月连续性、独立团队和回归集精度。

## 可复算数据

- [arXiv 母集 JSON](/embodied-ai-radar/preprints.json)
- [正式发表母集 JSON](/embodied-ai-radar/publications.json)
- [严格官方 proceedings JSON](/embodied-ai-radar/official-proceedings.json)
- [官方 program / pending JSON](/embodied-ai-radar/official-programs.json)
- [GitHub 证据 JSON](/embodied-ai-radar/repositories.json)
- [canonical works JSON](/embodied-ai-radar/works.json)

## 仍需继续补齐的部分

- IEEE Xplore、Science 与 SAGE 的 DOI 已进入发现母集；严格标签要继续逐条回到出版社页面核验。
- ICRA/IROS 的 PaperCept 节目单可能含 RA-L 转投展示，canonical 合并时必须避免双计。
- 新 taxonomy 正在通过正例、边界例和反例回归；完成前，旧五类月度序列保留作稳定对照，不把分类变化误写成趋势变化。

<!-- 更新标记：语料扩充与覆盖审计 最后更新 2026.07 -->
`)

const repoRows = repositories.map((repo) => {
  const badge = `![GitHub stars](https://img.shields.io/github/stars/${repo.repo_full_name}?style=flat-square&label=stars)`
  const paperLinks = [
    ...(repo.paper_ids ?? []).map((id) => `[${id}](https://arxiv.org/abs/${id})`),
    ...(repo.dois ?? []).map((doi) => `[DOI](https://doi.org/${doi})`),
  ].join('、') || '待映射'
  return `| [${repo.repo_full_name}](${repo.html_url}) ${badge} | ${repo.category_zh} | ${paperLinks} | ${repo.independent_adoption.score}（${repo.independent_adoption.band_zh}） | ${repo.forks} / ${repo.watchers_subscribers} | ${repo.license ?? '未识别'} | ${repo.pushed_at?.slice(0, 10) ?? '—'} |`
}).join('\n')

write('analysis/open-source-ecosystem.md', `${frontmatter}

# GitHub 与开源生态证据

> 快照：2026-07-29。所有 ${repositories.length} 个仓库 URL 均通过 GitHub API 解析；stars 仅作传播规模旁证，不进入独立采用分。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>${repositoryCoverage.repository_count ?? repositories.length}</strong><span>已核验仓库</span></div>
  <div class="radar-kpi"><strong>${repositoryCoverage.paper_mapped ?? 0}</strong><span>关联论文证据</span></div>
  <div class="radar-kpi"><strong>${repositoryCoverage.independent_adoption_bands?.高 ?? 0}</strong><span>高独立参与代理</span></div>
  <div class="radar-kpi"><strong>${repositoryCoverage.license_missing_or_unrecognized ?? 0}</strong><span>许可证缺失/未识别</span></div>
</div>

## 如何读这个表

IAS-GH（0–100）由近 12 个月外部 issue/PR 作者、贡献者广度、合并 PR、forks 与 release 新鲜度构成。它衡量公开 GitHub 协作与独立参与，不等于论文质量、商业采用或安全成熟度。GitHub 通用 API 没有稳定的反向依赖总数，缺失值保持 null，绝不用 forks 冒充 dependents。

| 仓库 | 类别 | 论文 | IAS-GH | forks / watchers | License | 最近推送 |
|---|---|---|---:|---:|---|---|
${repoRows}

## 下一层采用证据

仓库进入“独立研究采用”还需要至少一种更强证据：第三方仓库真实 import/配置使用、包注册表依赖、无作者重叠的独立复现，或后续论文把它作为 benchmark/训练基础设施而非 related work 引用。

[下载完整仓库证据 JSON](/embodied-ai-radar/repositories.json)

<!-- 更新标记：GitHub 与开源生态证据 最后更新 2026.07 -->
`)

const publicationPagesDirectory = path.join(docs, 'database', 'publications')
fs.rmSync(publicationPagesDirectory, { recursive: true, force: true })
fs.mkdirSync(publicationPagesDirectory, { recursive: true })
const publicationGroups = new Map()
for (const row of publications) {
  const key = `${row.venue}-${row.year}`
  if (!publicationGroups.has(key)) publicationGroups.set(key, [])
  publicationGroups.get(key).push(row)
}
const groupLinks = []
for (const [key, rows] of [...publicationGroups].sort(([a], [b]) => a.localeCompare(b))) {
  const slug = key.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
  const venue = rows[0].venue
  const year = rows[0].year
  const sortedRows = rows.sort((a, b) =>
    Number(b.included) - Number(a.included)
    || (b.citation_count_snapshot ?? -1) - (a.citation_count_snapshot ?? -1)
    || a.title.localeCompare(b.title)
  )
  const table = sortedRows.map((paper) => {
    const arxiv = paper.arxiv_id ? `[${paper.arxiv_id}](https://arxiv.org/abs/${paper.arxiv_id})` : '—'
    const doi = paper.doi ? `[DOI](https://doi.org/${paper.doi})` : '—'
    return `| [${clean(paper.title)}](${paper.official_url}) | ${topicLabel(paper.primary_topic)} | ${screeningLabel[paper.relevance?.status] ?? '—'} | ${verificationLabel[paper.verification_status] ?? paper.verification_status} | ${arxiv} | ${doi} | ${paper.citation_count_snapshot ?? '—'} |`
  }).join('\n')
  write(`database/publications/${slug}.md`, `${frontmatter}

# ${venue} ${year} 正式发表母集

> 本页共 ${rows.length} 条；直接候选 ${rows.filter((row) => row.relevance?.status === 'included').length}，边界候选 ${rows.filter((row) => row.relevance?.status === 'candidate').length}。DOI/发现记录不自动等于严格官方核验。

| 工作 | v2 主方向 | 相关性状态 | 发表证据状态 | arXiv | DOI | 引用快照 |
|---|---|---|---|---|---|---:|
${table}
`)
  groupLinks.push(`| [${venue} ${year}](/database/publications/${slug}) | ${rows.length} | ${rows.filter((row) => row.included).length} | ${rows.filter((row) => row.relevance?.status === 'candidate').length} |`)
}

write('database/publications.md', `${frontmatter}

# 正式发表数据库

> ${publications.length} 条会议/期刊版本。这里展示完整 venue-year 母集，严格官方状态与 DOI 发现状态分列。

| Venue-year | 母集 | 直接候选 | 边界候选 |
|---|---:|---:|---:|
${groupLinks.join('\n') || '| — | — | — | — |'}

[下载完整正式发表 JSON](/embodied-ai-radar/publications.json)
`)

const previousCalendarMonth = (month) => {
  const [year, value] = month.split('-').map(Number)
  return value === 1
    ? `${year - 1}-12`
    : `${year}-${String(value - 1).padStart(2, '0')}`
}

for (const month of [
  '2025-07', '2025-08', '2025-09', '2025-10', '2025-11', '2025-12',
  '2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07',
]) {
  const target = path.join(docs, 'monthly', `${month}.md`)
  if (!fs.existsSync(target)) continue
  const previousMonth = previousCalendarMonth(month)
  const currentAll = preprints.filter((row) => row.first_submitted?.startsWith(month))
  const currentIncluded = includedPreprints.filter((row) => row.first_submitted?.startsWith(month))
  const previousIncluded = includedPreprints.filter((row) => row.first_submitted?.startsWith(previousMonth))
  const currentCandidate = currentAll.filter((row) => row.relevance?.status === 'candidate').length
  const expandedRows = topicEntries.map(([key, item]) => {
    const current = currentIncluded.filter((row) => row.primary_topic === key).length
    const previous = previousIncluded.filter((row) => row.primary_topic === key).length
    return `| ${item.code} · [${item.label}](/frontiers/${topicSlug(key)}) | ${current} | ${pct(current, currentIncluded.length)} | ${previous} | ${signed(current - previous)} | ${change(current, previous)} |`
  }).join('\n')
  const expandedSection = `
## v2 扩展主题结构（15 类）

> 本表来自完整 arXiv 宽召回母库，只统计 v2 自动判为“直接候选”的记录；它与上方旧五类稳定序列使用不同 taxonomy，不能直接相加。2026 年 7 月截至 29 日，负环比仍按临时值处理。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>${fmt(currentAll.length)}</strong><span>当月 arXiv 母集</span></div>
  <div class="radar-kpi"><strong>${fmt(currentIncluded.length)}</strong><span>v2 直接候选</span></div>
  <div class="radar-kpi"><strong>${fmt(currentCandidate)}</strong><span>边界候选</span></div>
  <div class="radar-kpi"><strong>${fmt(previousIncluded.length)}</strong><span>上月直接候选</span></div>
</div>

| v2 主方向 | 本月 | 占比 | 上月 | 环比增量 | 环比 |
|---|---:|---:|---:|---:|---:|
${expandedRows}
| **总计** | **${currentIncluded.length}** | **100.0%** | **${previousIncluded.length}** | **${signed(currentIncluded.length - previousIncluded.length)}** | **${change(currentIncluded.length, previousIncluded.length)}** |

跨月比较时，应先看绝对数量与独立论文簇，再用正式发表和 GitHub 采用证据判断是否从 arXiv 热点走向兑现。
`
  const content = fs.readFileSync(target, 'utf8')
  const topicStart = content.indexOf('## 主题结构')
  const insertAt = topicStart >= 0
    ? content.indexOf('\n\n## ', topicStart + '## 主题结构'.length)
    : -1
  if (insertAt < 0) {
    throw new Error(`cannot locate topic-structure insertion point in ${target}`)
  }
  fs.writeFileSync(target, `${content.slice(0, insertAt)}\n${expandedSection}${content.slice(insertAt)}`)
}

const monthKeys = [...new Set(preprints.map((row) => row.first_submitted?.slice(0, 7)).filter(Boolean))].sort()
for (const [key, item] of topicEntries) {
  const rows = works
    .filter((work) => work.primary_topic === key)
    .sort((a, b) =>
      Number(b.strict_peer_reviewed) - Number(a.strict_peer_reviewed)
      || (b.citation_count_snapshot ?? -1) - (a.citation_count_snapshot ?? -1)
      || a.title.localeCompare(b.title)
    )
  const monthRows = monthKeys.map((month, index) => {
    const current = includedPreprints.filter((row) => row.first_submitted?.startsWith(month) && row.primary_topic === key).length
    const previousMonth = monthKeys[index - 1]
    const previous = previousMonth
      ? includedPreprints.filter((row) => row.first_submitted?.startsWith(previousMonth) && row.primary_topic === key).length
      : 0
    return `| ${month} | ${current} | ${previousMonth ?? '—'} | ${previous} | ${signed(current - previous)} | ${change(current, previous)} |`
  }).join('\n') || '| — | — | — | — | — | — |'
  const representativeRows = rows.slice(0, 60).map((work) => {
    const url = work.arxiv_id
      ? `https://arxiv.org/abs/${work.arxiv_id}`
      : work.versions?.find((version) => version.kind === 'conference' || version.kind === 'journal')?.url
    const venue = work.versions?.filter((version) => ['conference', 'journal'].includes(version.kind)).map((version) => `${version.venue} ${version.year}`).join('、') || '预印本'
    const repo = work.repositories?.map((name) => `[${name}](https://github.com/${name})`).join('、') || '—'
    return `| [${clean(work.title)}](${url}) | ${work.first_public_date ?? '—'} | ${venue} | ${work.strict_peer_reviewed ? '是' : '否'} | ${repo} |`
  }).join('\n') || '| — | — | — | — | — |'
  write(`frontiers/${topicSlug(key)}.md`, `${frontmatter}

# ${item.code} · ${item.label}

> v2 层级：${item.layer}。当前 canonical works ${rows.length} 条；此页是扩展分类试运行，不直接改写旧五类历史序列。

## 纳入边界

核心表达：${item.include.map((term) => `\`${term}\``).join('、')}。

必须同时出现的机器人/动作语境：${(item.required_context ?? []).map((term) => `\`${term}\``).join('、')}。

## 月度结构与环比

| 月份 | 本月 | 对比月 | 上月 | 环比增量 | 环比 |
|---|---:|---|---:|---:|---:|
${monthRows}

## 代表工作与证据

| 工作 | 首次公开 | 发表版本 | 严格同行评审 | GitHub |
|---|---|---|---|---|
${representativeRows}
`)
}

write('frontiers/index.md', `${frontmatter}

# ${topicEntries.length} 个研究前沿

> 五类旧体系保留作稳定趋势对照；v2 从扩充后的 arXiv、正式发表和 GitHub 语料中拆出更细科学问题。

| 编号 | 方向 | 层级 | v2 included works |
|---|---|---|---:|
${topicEntries.map(([key, item]) => `| ${item.code} | [${item.label}](/frontiers/${topicSlug(key)}) | ${item.layer} | ${works.filter((work) => work.primary_topic === key && work.relevance?.status === 'included').length} |`).join('\n')}
`)

console.log(`Generated v2 coverage pages: ${preprints.length} preprints, ${publications.length} publications, ${official.length} strict official records, ${officialPrograms.length} program/pending records, ${repositories.length} repositories, ${works.length} works.`)
