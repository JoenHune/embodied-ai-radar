import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const read = (name) => JSON.parse(fs.readFileSync(path.join(root, name), 'utf8'))
const config = read('config/x-discussion-radar.json')
const store = read('data/x-discussion-posts.json')
const weekly = read('data/x-weekly-discussions.json')
const organizations = read('config/organizations.json')
const validOrganizations = new Set(organizations.organizations.map((row) => row.organization_id))
const errors = []
const assert = (condition, message) => { if (!condition) errors.push(message) }
const unique = (values) => new Set(values).size === values.length
const hash = (target) => crypto.createHash('sha256').update(fs.readFileSync(target)).digest('hex')

assert(config.source.provider === 'x_api_v2', 'collector must use the official X API')
assert(config.source.raw_text_persisted === false, 'Post text persistence must remain disabled')
assert(config.source.poll_interval_hours <= 6, 'poll interval must cover the seven-day Recent Search window safely')
assert(config.source.lookback_hours > config.source.poll_interval_hours, 'polls need an overlap window')
assert(config.query_packs.length >= 6, 'query coverage is too narrow')
assert(unique(config.query_packs.map((row) => row.id)), 'duplicate X query pack id')
assert(unique(config.topics.map((row) => row.code)), 'duplicate X topic code')
const validTopics = new Set(config.topics.map((row) => row.code))
for (const pack of config.query_packs) {
  assert(pack.query.length <= 512, `${pack.id}: recent-search query exceeds 512 characters`)
  assert(pack.query.includes('-is:retweet'), `${pack.id}: retweets are not excluded`)
  for (const code of pack.topic_codes) assert(validTopics.has(code), `${pack.id}: unknown topic ${code}`)
}
for (const entity of config.entity_terms) assert(validOrganizations.has(entity.organization_id), `unknown entity ${entity.organization_id}`)

assert(store.source === 'x_api_v2', 'unexpected X store source')
assert(unique(store.posts.map((row) => row.post_id)), 'duplicate Post ID in store')
for (const post of store.posts) {
  assert(!Object.hasOwn(post, 'text'), `${post.post_id}: full Post text entered persistent store`)
  assert(/^\d+$/.test(post.post_id), `${post.post_id}: invalid Post ID`)
  assert(/^\d+$/.test(post.author_id), `${post.post_id}: invalid author ID`)
  assert(['live', 'unverified', 'deleted', 'protected', 'suspended'].includes(post.compliance_status), `${post.post_id}: invalid compliance status`)
  for (const code of post.topic_codes) assert(validTopics.has(code), `${post.post_id}: unknown topic ${code}`)
}

assert(unique((weekly.weeks ?? []).map((row) => row.week_id)), 'duplicate weekly X report')
for (const week of weekly.weeks ?? []) {
  assert(/^\d{4}-W\d{2}$/.test(week.week_id), `${week.week_id}: invalid ISO week`)
  for (const topic of week.top_topics ?? []) {
    assert(topic.heat_score >= 0 && topic.heat_score <= 100, `${week.week_id}: heat score out of range`)
    assert(topic.post_count >= config.publication.minimum_posts, `${week.week_id}: ranked topic below post threshold`)
    assert(topic.unique_authors >= config.publication.minimum_unique_authors, `${week.week_id}: ranked topic below author threshold`)
    assert((topic.representative_posts ?? []).every((row) => /^https:\/\/x\.com\/i\/web\/status\/\d+$/.test(row.url)), `${week.week_id}: invalid representative Post URL`)
  }
}

for (const page of ['docs/social/index.md', 'docs/social/method.md', 'docs/social/weekly/index.md']) {
  assert(fs.existsSync(path.join(root, page)), `missing X discussion page: ${page}`)
}
const publicData = path.join(root, 'docs/public/x-weekly-discussions.json')
assert(fs.existsSync(publicData), 'public X weekly JSON missing')
if (fs.existsSync(publicData)) assert(hash(publicData) === hash(path.join(root, 'data/x-weekly-discussions.json')), 'public X weekly JSON mismatch')

const sensitivePatterns = [/X_BEARER_TOKEN\s*[:=]\s*[A-Za-z0-9_-]{20,}/, /Authorization:\s*Bearer\s+[A-Za-z0-9_-]{20,}/i]
for (const target of ['config/x-discussion-radar.json', 'data/x-discussion-posts.json', 'data/x-weekly-discussions.json']) {
  const body = fs.readFileSync(path.join(root, target), 'utf8')
  for (const pattern of sensitivePatterns) assert(!pattern.test(body), `${target}: possible X credential leak`)
}

if (errors.length) {
  console.error(`X discussion audit failed (${errors.length})`)
  errors.forEach((error) => console.error(`- ${error}`))
  process.exit(1)
}
console.log(`X discussion audit passed: ${config.query_packs.length} query packs, ${store.posts.length} stored Post IDs, ${(weekly.weeks ?? []).length} weekly reports.`)
