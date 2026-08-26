import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const read = (name) => JSON.parse(fs.readFileSync(path.join(root, name), 'utf8'))
const registry = read('config/organizations.json')
const updates = read('data/group-updates.json')
const links = read('data/work-organization-links.json')
const review = read('data/group-review-queue.json')
const radar = read('data/research-group-radar.json')
const works = read('data/works.json')
const taxonomy = read('config/taxonomy-v2.json')
const agenda = read('config/research-agenda.json')
const organizations = registry.organizations
const tracked = organizations.filter((org) => org.tracking_unit)
const byId = new Map(organizations.map((org) => [org.organization_id, org]))
const workIds = new Set(works.map((work) => work.work_id))
const validDirections = new Set(Object.values(taxonomy.categories).map((item) => item.code))
const validQuestions = new Set(agenda.questions.map((item) => item.id))
const validUpdateTypes = new Set(['peer_reviewed_paper', 'preprint', 'technical_report', 'model_release', 'dataset_release', 'code_release', 'benchmark', 'project', 'deployment', 'organization_change', 'personnel_change', 'hiring_signal'])
const errors = []
const assert = (condition, message) => { if (!condition) errors.push(message) }
const unique = (values) => new Set(values).size === values.length
const hash = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')

assert(registry.tracking_target === 60, 'tracking target must remain 60')
assert(tracked.length === 63, `expected 60 core groups + 3 startup frontier groups, got ${tracked.length}`)
const categoryExpected = { corporate: 18, academic: 30, platform: 6, deployment_watch: 6, startup_frontier: 3 }
for (const [category, count] of Object.entries(categoryExpected)) {
  assert(tracked.filter((org) => org.tracking_category === category).length === count,
    `${category}: expected ${count} tracking groups`)
}
assert(unique(organizations.map((org) => org.organization_id)), 'duplicate organization_id')
assert(unique(organizations.map((org) => org.slug)), 'duplicate organization slug')

const aliasOwner = new Map()
for (const org of organizations) {
  assert(/^org:[a-z0-9-]+$/.test(org.organization_id), `${org.organization_id}: invalid id`)
  assert(/^https?:\/\//.test(org.official_urls?.home ?? Object.values(org.official_urls ?? {})[0] ?? ''),
    `${org.organization_id}: official URL missing`)
  for (const code of org.declared_direction_codes ?? []) assert(validDirections.has(code), `${org.organization_id}: unknown ${code}`)
  for (const code of org.question_codes ?? []) assert(validQuestions.has(code), `${org.organization_id}: unknown ${code}`)
  for (const leader of org.leaders ?? []) assert(/^https?:\/\//.test(leader.source_url), `${org.organization_id}: leader source missing`)
  for (const aliasRaw of [org.display_name, ...(org.aliases ?? [])]) {
    const alias = aliasRaw.toLowerCase().replace(/[^a-z0-9]+/g, '')
    if (!alias) continue
    const owner = aliasOwner.get(alias)
    assert(!owner || owner === org.organization_id, `ambiguous alias ${aliasRaw}: ${owner}/${org.organization_id}`)
    aliasOwner.set(alias, org.organization_id)
  }
  for (const relation of org.parent_relations ?? []) {
    assert(byId.has(relation.parent_id), `${org.organization_id}: missing parent ${relation.parent_id}`)
    assert(relation.parent_id !== org.organization_id, `${org.organization_id}: self parent`)
    assert(/^https?:\/\//.test(relation.evidence_url), `${org.organization_id}: parent evidence missing`)
  }
}

const visiting = new Set()
const visited = new Set()
const visit = (id) => {
  if (visiting.has(id)) { errors.push(`organization cycle at ${id}`); return }
  if (visited.has(id)) return
  visiting.add(id)
  for (const relation of byId.get(id)?.parent_relations ?? []) visit(relation.parent_id)
  visiting.delete(id)
  visited.add(id)
}
organizations.forEach((org) => visit(org.organization_id))

const updateIds = updates.updates.map((item) => item.update_id)
assert(unique(updateIds), 'duplicate group update IDs')
for (const item of updates.updates) {
  assert(byId.get(item.organization_id)?.tracking_unit, `${item.update_id}: update organization is not tracked`)
  assert(['G1', 'G2'].includes(item.evidence_grade), `${item.update_id}: G3/G0 entered public updates`)
  assert(/^https?:\/\//.test(item.url), `${item.update_id}: update URL missing`)
  assert(validUpdateTypes.has(item.update_type), `${item.update_id}: invalid update type ${item.update_type}`)
  assert(!['hiring_signal', 'organization_change'].includes(item.update_type), `${item.update_id}: strategic observation entered research updates`)
  if (item.work_id) assert(workIds.has(item.work_id), `${item.update_id}: missing work ${item.work_id}`)
  if (item.evidence_grade === 'G2') {
    assert(Boolean(item.published_at), `${item.update_id}: G2 requires a dated work`)
    const org = byId.get(item.organization_id)
    if (org?.active_from && item.published_at) assert(item.published_at >= org.active_from, `${item.update_id}: predates group membership window`)
    if (org?.active_to && item.published_at) assert(item.published_at <= org.active_to, `${item.update_id}: postdates group membership window`)
  }
  if (item.source_type === 'official_company_report') {
    assert(item.update_type === 'technical_report', `${item.update_id}: company report must use technical_report`)
    assert(item.publication_status === 'first_party_technical_report', `${item.update_id}: publication status missing`)
    assert(item.peer_reviewed === false && item.strict_peer_reviewed === false, `${item.update_id}: company report mislabeled peer reviewed`)
    assert(item.independent_validation === false, `${item.update_id}: independent validation must be explicit`)
    assert(item.metric_owner === 'company' && item.claim_status === 'company_self_report', `${item.update_id}: company claim boundary missing`)
    assert(Array.isArray(item.technical_stack_tags), `${item.update_id}: technical stack tags missing`)
  }
}
for (const item of review.candidates ?? []) {
  assert(['G3', 'G0'].includes(item.evidence_grade), `${item.update_id}: accepted-grade item left in review queue`)
}

const parentSet = (orgId) => {
  const result = new Set()
  const stack = [orgId]
  while (stack.length) {
    const current = stack.pop()
    for (const relation of byId.get(current)?.parent_relations ?? []) {
      if (!result.has(relation.parent_id)) { result.add(relation.parent_id); stack.push(relation.parent_id) }
    }
  }
  return result
}
const linksByWork = new Map()
for (const link of links.links) {
  assert(workIds.has(link.work_id), `link missing work ${link.work_id}`)
  assert(byId.get(link.organization_id)?.tracking_unit, `link organization not tracked ${link.organization_id}`)
  assert(['G1', 'G2'].includes(link.evidence_grade), `${link.work_id}: invalid public evidence grade`)
  assert(/^https?:\/\//.test(link.evidence_url), `${link.work_id}: link evidence missing`)
  if (!linksByWork.has(link.work_id)) linksByWork.set(link.work_id, [])
  linksByWork.get(link.work_id).push(link)
}
for (const [workId, rows] of linksByWork.entries()) {
  const sum = rows.reduce((total, row) => total + Number(row.fractional_credit), 0)
  assert(Math.abs(sum - 1) < 1e-6, `${workId}: fractional credit sums to ${sum}`)
  const ids = new Set(rows.map((row) => row.organization_id))
  for (const id of ids) {
    for (const parent of parentSet(id)) assert(!ids.has(parent), `${workId}: ancestor and descendant both credited`)
  }
}

const mustExist = [
  'org:nvidia-gear', 'org:physical-intelligence', 'org:cmu-robotics-institute',
  'org:amazon-far', 'org:amazon-robotics', 'org:rai-institute', 'org:boston-dynamics',
  'org:genesis-ai', 'org:generalist-ai', 'org:sunday-robotics', 'org:figure-ai', 'org:dyna-robotics',
]
for (const id of mustExist) assert(byId.has(id), `required regression organization missing: ${id}`)
assert(byId.get('org:nvidia-gear')?.parent_relations.some((item) => item.parent_id === 'org:nvidia'), 'GEAR must be child of NVIDIA')
assert(byId.get('org:amazon-far')?.organization_id !== byId.get('org:amazon-robotics')?.organization_id, 'Amazon FAR/Robotics merged')
assert(byId.get('org:rai-institute')?.organization_id !== byId.get('org:boston-dynamics')?.organization_id, 'RAI/Boston Dynamics merged')

assert(tracked.filter((org) => org.startup_frontier).length === 5, 'startup frontier cohort must contain Genesis, Generalist, Figure, DYNA and Sunday')
assert(radar.tracking_group_count === 63, 'radar count mismatch')
assert(radar.groups.length === 63, 'radar group list mismatch')
assert(radar.visualizations?.startup_reports?.length >= 16, 'startup technical report visualization data incomplete')
assert(radar.visualizations?.startup_stack_cells?.every((cell) => cell.level === 0 || cell.sources.length > 0), 'startup stack cell lacks source')
const groupsWithoutUpdates = radar.groups.filter((group) => group.update_count === 0).map((group) => group.organization_id)
assert(groupsWithoutUpdates.every((id) => id === 'org:tesla-optimus'), `unexpected groups without updates: ${groupsWithoutUpdates.join(', ')}`)
for (const org of tracked) assert(fs.existsSync(path.join(root, 'docs', 'groups', `${org.slug}.md`)), `profile missing: ${org.slug}`)
for (const page of ['index.md', 'startups.md', 'organizations.md', 'collaboration.md', 'weekly/index.md']) {
  assert(fs.existsSync(path.join(root, 'docs', 'groups', page)), `group page missing: ${page}`)
}
for (const file of ['organizations.json', 'work-organization-links.json', 'group-updates.json', 'research-group-radar.json']) {
  const source = file === 'organizations.json' ? path.join(root, 'config', file) : path.join(root, 'data', file)
  const publicFile = path.join(root, 'docs', 'public', file)
  assert(fs.existsSync(publicFile), `public ${file} missing`)
  if (fs.existsSync(publicFile)) assert(hash(source) === hash(publicFile), `public ${file} mismatch`)
}

if (errors.length) {
  console.error(`Organization audit failed (${errors.length})`)
  errors.forEach((error) => console.error(`- ${error}`))
  process.exit(1)
}
console.log(`Organization audit passed: ${tracked.length} groups, ${updates.updates.length} updates, ${links.links.length} work links.`)
