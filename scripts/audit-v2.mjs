import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const read = (name) => JSON.parse(fs.readFileSync(path.join(root, name), 'utf8'))
const preprints = read('data/preprints.json')
const preprintCoverage = read('data/preprint-coverage.json')
const publications = read('data/publications.json')
const publicationCoverage = read('data/publication-coverage.json')
const official = read('data/official-proceedings.json')
const officialCoverage = read('data/official-container-coverage.json')
const programs = read('data/official-programs.json')
const programCoverage = read('data/official-program-coverage.json')
const repositories = read('data/repositories.json')
const repositoryCoverage = read('data/repository-coverage.json')
const works = read('data/works.json')
const workCoverage = read('data/work-coverage.json')
const taxonomy = read('config/taxonomy-v2.json')
const errors = []
const warnings = []
const assert = (condition, message) => { if (!condition) errors.push(message) }
const warn = (condition, message) => { if (!condition) warnings.push(message) }
const unique = (values) => new Set(values).size === values.length
const hash = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')
const fileSize = (file) => fs.statSync(path.join(root, file)).size
const publicCopy = (name) => path.join(root, 'docs', 'public', path.basename(name))

assert(Object.keys(taxonomy.categories).length === 15,
  `expected 15 v2 topics, got ${Object.keys(taxonomy.categories).length}`)
assert(taxonomy.version === '2.1', `unexpected taxonomy version: ${taxonomy.version}`)

assert(preprints.length === preprintCoverage.mother_corpus,
  'preprint mother-corpus count mismatch')
assert(preprints.length >= 30000, `preprint corpus unexpectedly small: ${preprints.length}`)
assert(unique(preprints.map((row) => row.arxiv_id)), 'duplicate arXiv IDs in v2 preprints')
assert(preprints.every((row) => /^\d{4}\.\d{4,5}$/.test(row.arxiv_id)),
  'invalid arXiv ID in v2 preprints')
assert(preprints.every((row) => row.categories?.length), 'preprint categories missing')
assert(preprints.every((row) =>
  row.first_submitted >= '2024-07-01' && row.first_submitted <= '2026-07-29'),
  'preprint outside frozen window')
assert(preprints.filter((row) => row.categories.includes('cs.RO')).length === 23225,
  'cs.RO complete count must equal 23,225')
assert(Object.values(preprintCoverage.months).reduce((sum, row) => sum + row.mother_corpus, 0) === preprints.length,
  'preprint monthly funnel does not sum to mother corpus')
assert(Object.values(preprintCoverage.months).reduce((sum, row) => sum + row.cs_ro, 0) === 23225,
  'monthly cs.RO counts do not sum to 23,225')
assert(preprintCoverage.included >= 8800, 'v2 included preprints unexpectedly small')

assert(publications.length === publicationCoverage.mother_corpus,
  'publication mother-corpus count mismatch')
assert(publications.length >= 12000,
  `publication corpus unexpectedly small: ${publications.length}`)
assert(unique(publications.map((row) => row.publication_id)),
  'duplicate publication IDs')
assert(publications.every((row) => row.title && row.venue && row.official_url),
  'publication required metadata missing')
assert(publications.filter((row) => row.doi).length >= 11700,
  'publication DOI coverage unexpectedly low')
assert(publications.filter((row) => row.abstract).length >= 11400,
  'publication abstract enrichment unexpectedly low')
assert(publicationCoverage.in_window_records === publications.length - 1761,
  `unexpected publication-window count: ${publicationCoverage.in_window_records}/${publications.length}`)
assert(publications.every((row) => [2024, 2025, 2026].includes(row.year)),
  'publication venue/publisher year escaped the 2024–2026 collection window')
assert(publications.filter((row) => row.venue === 'ICRA' && row.year === 2024)
  .every((row) => row.publication_date === '2024-05-13' && !row.in_peer_review_window),
  'ICRA 2024 must remain outside the 2024-07 peer-review window')
assert(publications.every((row) =>
  !row.semantic_scholar_publication_date
  || row.publication_date !== row.semantic_scholar_publication_date
  || row.year === Number(row.publication_date.slice(0, 4))),
  'Semantic Scholar enrichment corrupted a publisher/venue year')

assert(official.length === 824, `expected 824 strict official records, got ${official.length}`)
assert(officialCoverage.containers_complete === officialCoverage.containers_expected,
  'not all strict official containers are complete')
assert(officialCoverage.manifests.every((item) =>
  item.complete && item.observed_count === item.expected_count),
  'official container count mismatch')
assert(unique(official.map((row) => row.official_url)),
  'duplicate official proceedings URLs')
assert(official.every((row) =>
  row.verification_status === 'peer_reviewed_official_proceedings'),
  'non-strict status entered official proceedings store')
assert(official.every((row) =>
  ['www.roboticsproceedings.org', 'proceedings.mlr.press'].includes(new URL(row.official_url).hostname)),
  'unapproved domain in strict official proceedings')

assert(programs.length === 3161, `expected 3,161 program/pending records, got ${programs.length}`)
assert(programCoverage.strict_peer_reviewed_records === 0,
  'program/pending records entered strict numerator')
assert(programCoverage.by_venue.ICRA === 2951, 'ICRA 2026 program count mismatch')
assert(programCoverage.by_venue.RSS === 210, 'RSS 2026 accepted count mismatch')
assert(programs.every((row) => row.strict_peer_reviewed === false),
  'strict flag found in program/pending store')

assert(repositories.length === 42, `expected 42 GitHub repositories, got ${repositories.length}`)
assert(repositoryCoverage.url_verified === repositories.length,
  'not all GitHub URLs verified')
assert(unique(repositories.map((row) => row.repo_full_name.toLowerCase())),
  'duplicate GitHub repositories')
assert(repositories.every((row) =>
  row.html_url === `https://github.com/${row.repo_full_name}`),
  'non-canonical GitHub URL')
assert(repositories.every((row) =>
  Number.isInteger(row.stars) && Number.isInteger(row.forks)
  && Number.isInteger(row.watchers_subscribers)),
  'GitHub count field missing')
assert(repositories.every((row) =>
  row.independent_adoption.score >= 0 && row.independent_adoption.score <= 100),
  'invalid IAS-GH score')
assert(repositoryCoverage.warning.includes('Stars') && repositoryCoverage.warning.includes('forks'),
  'GitHub scoring warning missing')

assert(works.length === workCoverage.canonical_works, 'canonical work count mismatch')
assert(works.length >= 40000, `canonical work graph unexpectedly small: ${works.length}`)
assert(unique(works.map((row) => row.work_id)), 'duplicate canonical work IDs')
assert(workCoverage.strict_peer_reviewed_works >= 830,
  'strict peer-reviewed canonical works unexpectedly small')
assert(workCoverage.works_with_repository >= 20,
  'paper-to-repository canonical links unexpectedly small')
assert(works.every((row) => !('abstract' in row)),
  'canonical works should not duplicate source abstracts')
for (const work of works.filter((row) => row.arxiv_id && row.first_public_date)) {
  assert(work.versions.some((version) =>
    version.kind === 'preprint' && version.date === work.first_public_date),
  `${work.work_id}: publication date overwrote arXiv v1`)
}

for (const file of [
  'data/preprints.json',
  'data/publications.json',
  'data/official-proceedings.json',
  'data/official-programs.json',
  'data/repositories.json',
  'data/works.json',
]) {
  assert(fileSize(file) < 100 * 1024 * 1024, `${file} exceeds GitHub 100 MiB file limit`)
  const publicFile = publicCopy(file)
  assert(fs.existsSync(publicFile), `public copy missing: ${path.basename(file)}`)
  if (fs.existsSync(publicFile)) {
    assert(hash(path.join(root, file)) === hash(publicFile),
      `public copy mismatch: ${path.basename(file)}`)
  }
}

const requiredPages = [
  'docs/analysis/corpus-expansion.md',
  'docs/analysis/open-source-ecosystem.md',
  'docs/database/publications.md',
  'docs/frontiers/index.md',
  'docs/methods/expansion-protocol.md',
]
for (const file of requiredPages) {
  assert(fs.existsSync(path.join(root, file)), `v2 generated page missing: ${file}`)
}
assert(fs.readdirSync(path.join(root, 'docs', 'frontiers')).filter((name) => name.endsWith('.md')).length === 16,
  'expected 15 frontier pages plus index')
const expectedPublicationPages = new Set(
  publications.map((row) => `${row.venue}|${row.year}`)
).size
assert(fs.readdirSync(path.join(root, 'docs', 'database', 'publications')).filter((name) => name.endsWith('.md')).length === expectedPublicationPages,
  'venue-year publication page count does not match current corpus')
for (const month of [
  '2025-07', '2025-08', '2025-09', '2025-10', '2025-11', '2025-12',
  '2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07',
]) {
  const monthlyPage = fs.readFileSync(path.join(root, 'docs', 'monthly', `${month}.md`), 'utf8')
  assert(monthlyPage.includes('## v2 扩展主题结构（15 类）'),
    `${month} monthly page missing v2 month-over-month topic structure`)
}
const corpusPage = fs.readFileSync(path.join(root, 'docs', 'analysis', 'corpus-expansion.md'), 'utf8')
assert(corpusPage.includes(preprints.length.toLocaleString('zh-CN')),
  'corpus page preprint KPI mismatch')
assert(corpusPage.includes(String(official.length)),
  'corpus page official KPI mismatch')
const githubPage = fs.readFileSync(path.join(root, 'docs', 'analysis', 'open-source-ecosystem.md'), 'utf8')
assert((githubPage.match(/img\.shields\.io\/github\/stars/g) ?? []).length === repositories.length,
  'not every GitHub row has a star badge')

if (warnings.length) console.warn(`V2 warnings (${warnings.length}):\n- ${warnings.join('\n- ')}`)
if (errors.length) {
  console.error(`V2 audit failed (${errors.length}):\n- ${errors.slice(0, 80).join('\n- ')}`)
  if (errors.length > 80) console.error(`...and ${errors.length - 80} more`)
  process.exit(1)
}
console.log(
  `V2 audit passed: ${preprints.length} preprints, ${publications.length} publication versions, `
  + `${official.length} strict official records, ${programs.length} program/pending records, `
  + `${repositories.length} repositories, ${works.length} canonical works.`
)
