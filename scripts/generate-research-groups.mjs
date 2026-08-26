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
const writeJson = (target, payload) => {
  fs.mkdirSync(path.dirname(target), { recursive: true })
  fs.writeFileSync(target, `${JSON.stringify(payload, null, 2)}\n`)
}
const frontmatter = `---\noutline: deep\n---`
const clean = (value = '') => String(value).replaceAll('|', '\\|').replace(/\s+/g, ' ').trim()
const registry = read('config/organizations.json', { organizations: [], updated: '2026-08-26' })
const updatesStore = read('data/group-updates.json', { updates: [] })
const linksStore = read('data/work-organization-links.json', { links: [] })
const reviewQueue = read('data/group-review-queue.json', { candidates: [] })
const sourceStatus = read('data/group-source-status.json', { sources: [] })
const works = read('data/works.json', [])
const taxonomy = read('config/taxonomy-v2.json', { categories: {} })
const agenda = read('config/research-agenda.json', { questions: [] })
const organizations = registry.organizations
const tracked = organizations.filter((org) => org.tracking_unit)
const byOrg = new Map(organizations.map((org) => [org.organization_id, org]))
const byWork = new Map(works.map((work) => [work.work_id, work]))
const updatesByOrg = new Map(tracked.map((org) => [org.organization_id, []]))
for (const update of updatesStore.updates ?? []) {
  if (updatesByOrg.has(update.organization_id)) updatesByOrg.get(update.organization_id).push(update)
}
const linksByOrg = new Map(tracked.map((org) => [org.organization_id, []]))
for (const link of linksStore.links ?? []) {
  if (linksByOrg.has(link.organization_id)) linksByOrg.get(link.organization_id).push(link)
}
const sourcesByOrg = new Map(tracked.map((org) => [org.organization_id, []]))
for (const source of sourceStatus.sources ?? []) {
  if (sourcesByOrg.has(source.organization_id)) sourcesByOrg.get(source.organization_id).push(source)
}

const directionByCode = Object.fromEntries(Object.entries(taxonomy.categories).map(([key, value]) => [value.code, { key, ...value }]))
const questionByCode = Object.fromEntries((agenda.questions ?? []).map((item) => [item.id, item]))
const categoryLabel = {
  corporate: '企业/独立研究组织',
  academic: '学术实验室/PI 组',
  platform: '研究院/开放平台',
  deployment_watch: '部署与早期观察',
  parent: '母机构',
}
const evidenceLabel = { G1: 'G1 直接证据', G2: 'G2 时间对齐重建', G3: 'G3 推测归属', G0: 'G0 未解析' }
const updateTypeLabel = {
  peer_reviewed_paper: '同行评审论文', preprint: '预印本', technical_report: '技术报告',
  model_release: '模型', dataset_release: '数据集', code_release: '代码', benchmark: 'Benchmark',
  project: '项目', deployment: '部署', organization_change: '组织变化', personnel_change: '人员变化',
  hiring_signal: '招聘信号',
}

const dateValue = (value) => value ? new Date(`${value}T00:00:00Z`) : new Date('1900-01-01T00:00:00Z')
const generatedAt = sourceStatus.generated_at ?? updatesStore.generated_at ?? registry.updated
const snapshotDate = new Date(`${generatedAt}T00:00:00Z`)
const currentWeekMonday = new Date(snapshotDate)
const weekday = (currentWeekMonday.getUTCDay() + 6) % 7
currentWeekMonday.setUTCDate(currentWeekMonday.getUTCDate() - weekday)
const completedWeekEnd = new Date(currentWeekMonday)
completedWeekEnd.setUTCDate(completedWeekEnd.getUTCDate() - 1)
const completedWeekStart = new Date(completedWeekEnd)
completedWeekStart.setUTCDate(completedWeekStart.getUTCDate() - 6)
const isoDate = (value) => value.toISOString().slice(0, 10)
const isoWeek = (value) => {
  const date = new Date(Date.UTC(value.getUTCFullYear(), value.getUTCMonth(), value.getUTCDate()))
  const day = date.getUTCDay() || 7
  date.setUTCDate(date.getUTCDate() + 4 - day)
  const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1))
  const week = Math.ceil((((date - yearStart) / 86400000) + 1) / 7)
  return `${date.getUTCFullYear()}-W${String(week).padStart(2, '0')}`
}
const latestWeek = isoWeek(completedWeekEnd)
const within = (value, start, end) => value && value >= start && value <= end
const last12Start = new Date(snapshotDate)
last12Start.setUTCMonth(last12Start.getUTCMonth() - 12)
const previous12Start = new Date(last12Start)
previous12Start.setUTCMonth(previous12Start.getUTCMonth() - 12)

const parentNames = (org) => org.parent_relations.map((item) => byOrg.get(item.parent_id)?.display_name ?? item.parent_id)
const parentLinks = (org) => org.parent_relations.map((item) => {
  const parent = byOrg.get(item.parent_id)
  const url = parent?.official_urls?.home
  return url ? `[${clean(parent.display_name)}](${url})` : clean(parent?.display_name ?? item.parent_id)
}).join('、')
const officialLinks = (org) => Object.entries(org.official_urls ?? {}).map(([kind, url]) => `[${kind}](${url})`).join(' · ') || '—'
const leaderText = (org) => org.leaders?.length
  ? org.leaders.map((leader) => `[${clean(leader.name)}](${leader.source_url})（${clean(leader.role)}）`).join('、')
  : '官方未指定单一负责人'
const directionLinks = (codes) => codes.map((code) => directionByCode[code]
  ? `[${code} · ${directionByCode[code].label}](/frontiers/${directionByCode[code].key.replaceAll('_', '-')})`
  : code).join('、') || '—'
const questionLinks = (codes) => codes.map((code) => questionByCode[code]
  ? `[${code} · ${questionByCode[code].title}](/questions/#${code.toLowerCase()})`
  : code).join('、') || '—'
const sourceHealth = (org) => {
  const rows = sourcesByOrg.get(org.organization_id) ?? []
  if (!rows.length) return org.source_health
  if (rows.some((row) => row.status === 'stale')) return 'stale'
  if (rows.some((row) => row.status === 'partial')) return 'partial'
  return rows.every((row) => row.status === 'healthy') ? 'healthy' : org.source_health
}
const lastChanged = (org) => {
  const dates = (updatesByOrg.get(org.organization_id) ?? []).map((row) => row.published_at).filter(Boolean).sort()
  return dates.at(-1) ?? org.last_changed ?? org.last_checked
}
const updateLink = (item) => `[${clean(item.title)}](${item.url})`

const workGroups = new Map()
for (const link of linksStore.links ?? []) {
  if (!workGroups.has(link.work_id)) workGroups.set(link.work_id, [])
  workGroups.get(link.work_id).push(link.organization_id)
}
const collaborationEdges = new Map()
for (const [workId, orgIdsRaw] of workGroups.entries()) {
  const orgIds = [...new Set(orgIdsRaw)].filter((id) => byOrg.get(id)?.tracking_unit)
  for (let left = 0; left < orgIds.length; left += 1) {
    for (let right = left + 1; right < orgIds.length; right += 1) {
      const pair = [orgIds[left], orgIds[right]].sort()
      const key = pair.join('|')
      if (!collaborationEdges.has(key)) collaborationEdges.set(key, { source: pair[0], target: pair[1], work_ids: [] })
      collaborationEdges.get(key).work_ids.push(workId)
    }
  }
}

const summaries = tracked.map((org) => {
  const updates = (updatesByOrg.get(org.organization_id) ?? []).sort((a, b) => dateValue(b.published_at) - dateValue(a.published_at))
  const links = linksByOrg.get(org.organization_id) ?? []
  const current12 = updates.filter((item) => dateValue(item.published_at) >= last12Start && dateValue(item.published_at) < currentWeekMonday)
  const previous12 = updates.filter((item) => dateValue(item.published_at) >= previous12Start && dateValue(item.published_at) < last12Start)
  const week = updates.filter((item) => within(item.published_at, isoDate(completedWeekStart), isoDate(completedWeekEnd)))
  const linkedWorks = links.map((link) => byWork.get(link.work_id)).filter(Boolean)
  const observedDirectionCodes = [...new Set([
    ...org.declared_direction_codes,
    ...updates.flatMap((item) => item.direction_codes ?? []),
    ...linkedWorks.map((work) => taxonomy.categories[work.primary_topic]?.code).filter(Boolean),
  ])]
  const observedQuestionCodes = [...new Set([...org.question_codes, ...updates.flatMap((item) => item.question_codes ?? [])])]
  return {
    organization_id: org.organization_id,
    display_name: org.display_name,
    short_name: org.short_name,
    slug: org.slug,
    tracking_category: org.tracking_category,
    entity_type: org.entity_type,
    region: org.region,
    country: org.country,
    parent_names: parentNames(org),
    status: org.status,
    disclosure_level: org.disclosure_level,
    source_health: sourceHealth(org),
    last_checked: org.last_checked,
    last_changed: lastChanged(org),
    summary_zh: org.summary_zh,
    direction_codes: observedDirectionCodes,
    question_codes: observedQuestionCodes,
    update_count: updates.length,
    current_12m_count: current12.length,
    previous_12m_count: previous12.length,
    latest_week_count: week.length,
    strict_peer_work_count: new Set(linkedWorks.filter((work) => work.strict_peer_reviewed).map((work) => work.work_id)).size,
    linked_work_count: new Set(links.map((link) => link.work_id)).size,
    evidence_counts: Object.fromEntries(['G1', 'G2', 'G3', 'G0'].map((grade) => [grade, updates.filter((item) => item.evidence_grade === grade).length])),
    official_urls: org.official_urls,
  }
})

const radar = {
  version: '1.0',
  generated_at: generatedAt,
  tracking_group_count: tracked.length,
  organization_node_count: organizations.length,
  latest_completed_week: { id: latestWeek, from: isoDate(completedWeekStart), until: isoDate(completedWeekEnd) },
  groups: summaries,
  collaborations: [...collaborationEdges.values()],
  review_queue_count: reviewQueue.candidates?.length ?? 0,
}
writeJson(path.join(root, 'data', 'research-group-radar.json'), radar)
for (const [name, source] of [
  ['organizations.json', path.join(root, 'config', 'organizations.json')],
  ['work-organization-links.json', path.join(root, 'data', 'work-organization-links.json')],
  ['group-updates.json', path.join(root, 'data', 'group-updates.json')],
  ['research-group-radar.json', path.join(root, 'data', 'research-group-radar.json')],
]) {
  fs.copyFileSync(source, path.join(docs, 'public', name))
}
writeJson(path.join(docs, '.vitepress', 'data', 'research-groups.json'), radar)

for (const org of tracked) {
  const summary = summaries.find((item) => item.organization_id === org.organization_id)
  const updates = (updatesByOrg.get(org.organization_id) ?? []).sort((a, b) => dateValue(b.published_at) - dateValue(a.published_at))
  const week = updates.filter((item) => within(item.published_at, isoDate(completedWeekStart), isoDate(completedWeekEnd)))
  const links = linksByOrg.get(org.organization_id) ?? []
  const linkedWorks = links.map((link) => ({ link, work: byWork.get(link.work_id) })).filter((item) => item.work)
  const collaborations = [...collaborationEdges.values()].filter((edge) => edge.source === org.organization_id || edge.target === org.organization_id)
  const updateRows = updates.slice(0, 30).map((item) => `| ${item.published_at ?? '日期待核'} | ${updateTypeLabel[item.update_type] ?? item.update_type} | ${updateLink(item)} | ${evidenceLabel[item.evidence_grade]} | ${directionLinks(item.direction_codes ?? [])} | ${clean(item.summary_zh)} |`).join('\n') || '| — | — | 暂无已核验更新 | — | — | — |'
  const weekRows = week.map((item) => `| ${item.published_at ?? '日期待核'} | ${updateLink(item)} | ${updateTypeLabel[item.update_type] ?? item.update_type} | ${clean(item.summary_zh)} |`).join('\n') || '| — | 本周无可升级信号 | — | 官方来源未发现新的 G1/G2 更新。 |'
  const workRows = linkedWorks.slice(0, 25).map(({ link, work }) => {
    const version = work.versions?.find((item) => ['conference', 'journal', 'preprint'].includes(item.kind))
    const url = work.arxiv_id ? `https://arxiv.org/abs/${work.arxiv_id}` : version?.url
    return `| [${clean(work.title)}](${url}) | ${work.first_public_date ?? '—'} | ${work.strict_peer_reviewed ? '是' : '否'} | ${evidenceLabel[link.evidence_grade]} | [归属证据](${link.evidence_url}) |`
  }).join('\n') || '| — | — | — | — | — |'
  const collaborationRows = collaborations.map((edge) => {
    const peerId = edge.source === org.organization_id ? edge.target : edge.source
    const peer = byOrg.get(peerId)
    const examples = edge.work_ids.slice(0, 3).map((id) => byWork.get(id)).filter(Boolean).map((work) => clean(work.title)).join('；')
    return `| [${clean(peer?.display_name ?? peerId)}](/groups/${peer?.slug}) | ${edge.work_ids.length} | ${examples || '—'} |`
  }).join('\n') || '| — | — | 暂无多组 G1/G2 共同 work |'
  const sourceRows = (sourcesByOrg.get(org.organization_id) ?? []).map((source) => `| ${source.kind} | [${clean(source.url)}](${source.url}) | ${source.status} | ${source.last_success?.slice(0, 10) ?? '—'} | ${source.consecutive_failures} |`).join('\n') || '| 官方登记 | 见页面顶部链接 | 尚未运行周度监测 | — | 0 |'
  const gaps = [
    summary.linked_work_count === 0 ? '尚无 canonical work 归属边；当前档案主要依赖官方项目更新。' : null,
    summary.source_health !== 'healthy' ? `来源健康状态为 ${summary.source_health}，请谨慎解读最近更新。` : null,
    org.disclosure_level === 'low' ? '该组织公开披露较少，公司 Demo、招聘和实际研究成果必须分开理解。' : null,
  ].filter(Boolean)
  write(`groups/${org.slug}.md`, `${frontmatter}

# ${org.display_name}

> ${categoryLabel[org.tracking_category]} · ${org.region} / ${org.country} · **来源状态：${summary.source_health}** · 最后核验 ${org.last_checked}

${org.summary_zh}

| 项目 | 内容 |
|---|---|
| 母机构/上级 | ${parentLinks(org) || '独立研究组织'} |
| 负责人 | ${leaderText(org)} |
| 官方入口 | ${officialLinks(org)} |
| 官方自述方向 | ${directionLinks(org.declared_direction_codes)} |
| 雷达问题映射 | ${questionLinks(org.question_codes)} |
| 披露水平 | ${org.disclosure_level} |

## 本周新增（${latestWeek}）

| 日期 | 动态 | 类型 | 为什么重要 |
|---|---|---|---|
${weekRows}

## 最近 12 个月与前一窗口

| 当前 12 个月更新 | 前一 12 个月更新 | 已关联 work | 严格评审 work | 最新实质变化 |
|---:|---:|---:|---:|---|
| ${summary.current_12m_count} | ${summary.previous_12m_count} | ${summary.linked_work_count} | ${summary.strict_peer_work_count} | ${summary.last_changed ?? '—'} |

**观察到的方向：** ${directionLinks(summary.direction_codes)}

**观察到的问题轴：** ${questionLinks(summary.question_codes)}

## 研究与发布动态

| 日期 | 类型 | 工作/项目 | 证据 | 方向 | 摘要 |
|---|---|---|---|---|---|
${updateRows}

## Canonical works 与归属证据

| 工作 | 首次公开 | 严格同行评审 | 归属等级 | 证据 |
|---|---|---|---|---|
${workRows}

## 合作研究组

| 研究组 | 共同 work | 代表合作 |
|---|---:|---|
${collaborationRows}

## 来源健康与信息缺口

| 来源 | URL | 状态 | 最近成功 | 连续失败 |
|---|---|---|---|---:|
${sourceRows}

${gaps.length ? gaps.map((item) => `- ${item}`).join('\n') : '- 当前没有影响档案解读的重大来源缺口。'}
`)
}

const categoryCounts = Object.fromEntries(['corporate', 'academic', 'platform', 'deployment_watch'].map((category) => [category, tracked.filter((org) => org.tracking_category === category).length]))
write('groups/index.md', `${frontmatter}

# 全球关键研究组雷达

> 这里追踪 60 个研究执行单元，不做跨组排行榜。母机构、研究院、实验室、独立研究公司和部署观察团队分层保存；默认按最近发生实质变化排序。

<div class="radar-kpis">
  <div class="radar-kpi"><strong>${tracked.length}</strong><span>持续跟踪研究组</span></div>
  <div class="radar-kpi"><strong>${categoryCounts.corporate}</strong><span>企业/独立组织</span></div>
  <div class="radar-kpi"><strong>${categoryCounts.academic}</strong><span>学术实验室</span></div>
  <div class="radar-kpi"><strong>${categoryCounts.platform + categoryCounts.deployment_watch}</strong><span>平台 + 部署观察</span></div>
</div>

::: warning 归属边界
Affiliation 只能证明母机构，不能自动证明具体研究组：NVIDIA 不等于 GEAR，CMU 不等于 RI 或某个实验室，当前员工也不能反向改写历史论文归属。正式动态只使用 G1/G2，G3/G0 保留在复核队列。
:::

<ResearchGroupExplorer />

## 周报与方法

- [${latestWeek} 周报](/groups/weekly/${latestWeek.toLowerCase()})
- [组织层级图](/groups/organizations)
- [研究组合作网络](/groups/collaboration)
- [组织归属与每周更新方法](/methods/research-groups)
- [旧机构页兼容入口](/analysis/institutions)
`)

const parentRows = organizations.filter((org) => !org.tracking_unit).map((parent) => {
  const children = tracked.filter((org) => org.parent_relations.some((relation) => relation.parent_id === parent.organization_id))
  return `| [${clean(parent.display_name)}](${parent.official_urls?.home}) | ${children.length} | ${children.map((child) => `[${clean(child.display_name)}](/groups/${child.slug})`).join('、') || '—'} |`
}).join('\n')
const independentRows = tracked.filter((org) => org.parent_relations.length === 0).map((org) => `| [${clean(org.display_name)}](/groups/${org.slug}) | ${categoryLabel[org.tracking_category]} | ${clean(org.summary_zh)} |`).join('\n')
write('groups/organizations.md', `${frontmatter}

# 研究组织层级图

> 母机构节点不占 60 个跟踪名额。子研究组的 work 可以向母机构汇总，但母机构不会额外获得第二份 work credit。

## 母机构与直接子组

| 母机构 | 跟踪子组 | 子研究组 |
|---|---:|---|
${parentRows}

## 独立研究执行单元

| 研究组 | 类型 | 定位 |
|---|---|---|
${independentRows || '| — | — | — |'}
`)

const collaborationRows = [...collaborationEdges.values()].sort((a, b) => b.work_ids.length - a.work_ids.length).map((edge) => {
  const source = byOrg.get(edge.source)
  const target = byOrg.get(edge.target)
  return `| [${clean(source?.display_name ?? edge.source)}](/groups/${source?.slug}) | [${clean(target?.display_name ?? edge.target)}](/groups/${target?.slug}) | ${edge.work_ids.length} | ${edge.work_ids.slice(0, 3).map((id) => clean(byWork.get(id)?.title ?? id)).join('；')} |`
}).join('\n') || '| — | — | 0 | 当前尚无多个研究组共同拥有 G1/G2 work |'
write('groups/collaboration.md', `${frontmatter}

# 研究组合作网络

> 合作边只来自同一 canonical work 上的多个 G1/G2 研究组归属。母机构共同出现、作者相识或当前人员关系都不会自动创建合作边。

| 研究组 A | 研究组 B | 共同 work | 代表合作 |
|---|---|---:|---|
${collaborationRows}
`)

const weekUpdates = (updatesStore.updates ?? []).filter((item) => within(item.published_at, isoDate(completedWeekStart), isoDate(completedWeekEnd))).sort((a, b) => dateValue(b.published_at) - dateValue(a.published_at))
const changedGroups = [...new Set(weekUpdates.map((item) => item.organization_id))].map((id) => byOrg.get(id)).filter(Boolean)
const weeklyRows = weekUpdates.slice(0, 12).map((item) => {
  const org = byOrg.get(item.organization_id)
  return `| ${item.published_at} | [${clean(org?.display_name ?? item.organization_id)}](/groups/${org?.slug}) | ${updateLink(item)} | ${updateTypeLabel[item.update_type] ?? item.update_type} | ${directionLinks(item.direction_codes ?? [])} | ${clean(item.summary_zh)} |`
}).join('\n') || '| — | — | 本周无可升级信号 | — | — | 60 个组的官方来源未出现新的 G1/G2 动态。 |'
const weeklyTitle = `具身智能关键研究组周报 · ${latestWeek}`
write(`groups/weekly/${latestWeek.toLowerCase()}.md`, `${frontmatter}

# ${weeklyTitle}

> 覆盖 ${isoDate(completedWeekStart)}—${isoDate(completedWeekEnd)}（Asia/Shanghai） · 生成于 ${generatedAt}

## 三条总判断

1. 本周共有 **${weekUpdates.length}** 条 G1/G2 更新，涉及 **${changedGroups.length}** 个研究组。
2. 企业 Demo、招聘与未核验人员归属不会进入本表，只在待复核队列中保存。
3. ${weekUpdates.length ? '以下更新已关联公开来源；是否升级为研究趋势仍需跨组或同行评审验证。' : '本周没有达到公开证据门槛的新信号，历史档案保持不变。'}

## 本周重点变化

| 日期 | 研究组 | 工作/项目 | 类型 | 方向 | 为什么重要 |
|---|---|---|---|---|---|
${weeklyRows}

## 发生变化的研究组

${changedGroups.length ? changedGroups.map((org) => `- [${clean(org.display_name)}](/groups/${org.slug})`).join('\n') : '- 无。'}

## 信息边界

- 周报只纳入 G1/G2；G3/G0、招聘、未经官方确认的人员流动不写成研究事实。
- 网站保存完整档案和来源；飞书周报只是同一结构化数据的派生物。
`)
write('groups/weekly/index.md', `${frontmatter}

# 关键研究组周报

| 周次 | 覆盖窗口 | G1/G2 更新 | 变化研究组 | 链接 |
|---|---|---:|---:|---|
| ${latestWeek} | ${isoDate(completedWeekStart)}—${isoDate(completedWeekEnd)} | ${weekUpdates.length} | ${changedGroups.length} | [阅读](/groups/weekly/${latestWeek.toLowerCase()}) |
`)

write('methods/research-groups.md', `${frontmatter}

# 研究组归属与周度监测方法

## 四层实体与证据

- 母机构只做向上聚合，不代表具体研究路线。
- 研究院/事业部、实验室/PI 组和独立研究公司可以成为跟踪单元。
- 论文合作组不是持久 organization。
- G1 为官方研究组/论文直接证据；G2 为带时间的成员关系重建；G3/G0 不进入正式动态。

## 每周窗口

周一北京时间 04:00 运行，冻结上周一 00:00 至周日 23:59。原始时间保存为 UTC，页面以 Asia/Shanghai 展示。不完整当周不进入周报。

## 不做跨组排名

页面只展示每组的时间线、方向变化、证据类型、开放资产、真机与合作关系。论文数量、Demo 和部署规模不压缩为一个不可比较的总分。

## 自动化边界

官方 publications/projects 页面可生成 G1 候选；当前 roster、GitHub owner、招聘页和域名只能生成 G3 观察。来源失败不会删除既有记录；连续两周失败显示 stale warning。
`)

write('analysis/institutions.md', `${frontmatter}

# 机构 Affiliation 覆盖与兼容入口

> 旧页面曾把母机构字符串、研究院、实验室和企业研究组织混在同一排行榜里，并把不同 venue-year 数误写成“官方评审工作数”。该排名已停用。

新的[全球关键研究组雷达](/groups/)使用分层组织图和 G1–G0 归属证据。原始 affiliation 仍保留用于母机构发现，但不能自动证明具体实验室归属。

| 数据层 | 数量 |
|---|---:|
| Canonical works | ${works.length} |
| 带 organization 归属边的 work | ${new Set((linksStore.links ?? []).map((link) => link.work_id)).size} |
| 持续跟踪研究组 | ${tracked.length} |
| 待复核 G3/G0 候选 | ${reviewQueue.candidates?.length ?? 0} |

## 必须保留的区别

- NVIDIA 与 NVIDIA GEAR/Cosmos/Seattle Robotics Lab 分开。
- CMU 与 CMU Robotics Institute 及其各实验室分开。
- Physical Intelligence 公司与 MPI-IS 同名部门分开。
- Amazon FAR 与 Amazon Robotics 分开。
- RAI Institute 与 Boston Dynamics 分开。
`)

console.log(`Generated ${tracked.length} research-group profiles and weekly digest ${latestWeek}.`)
