import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const read = (name) => JSON.parse(fs.readFileSync(path.join(root, name), 'utf8'))
const agenda = read('config/research-agenda.json')
const taxonomy = read('config/taxonomy-v2.json')
const evidence = read('data/research-question-evidence.json')
const preprints = read('data/preprints.json')
const errors = []

if (evidence.generated_at !== '2026-08-31') errors.push('question evidence cutoff must be 2026-08-31')
if (evidence.rolling_window?.from !== '2025-09-01' || evidence.rolling_window?.until !== '2026-08-31') {
  errors.push('question evidence rolling window must cover 2025-09 through 2026-08')
}
if (evidence.rolling_window?.months?.length !== 12 || evidence.rolling_window?.months?.at(-1) !== '2026-08') {
  errors.push('question evidence must contain 12 complete months ending 2026-08')
}
if (evidence.snapshot?.status !== 'complete') errors.push('August question snapshot must be complete')

const expected = ['Q0', 'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8', 'Q9', 'Q10']
const ids = agenda.questions.map((item) => item.id)
if (new Set(ids).size !== ids.length) errors.push('question IDs are not unique')
for (const id of expected) if (!ids.includes(id)) errors.push(`missing ${id}`)
if (Object.keys(taxonomy.categories).length !== 15) errors.push('stable D1-D15 taxonomy changed size')
for (const question of agenda.questions) {
  for (const field of ['priority', 'title', 'assessment', 'role', 'claim', 'falsifier']) {
    if (!question[field]) errors.push(`${question.id} missing ${field}`)
  }
  if (!['A', 'B', 'C', 'D'].includes(question.assessment)) errors.push(`${question.id} invalid assessment`)
  if (!question.query_terms?.length) errors.push(`${question.id} has no query terms`)
  if (!question.metrics?.length) errors.push(`${question.id} has no metrics`)
  if (question.evidence?.length < 2) errors.push(`${question.id} has insufficient editorial evidence`)
  for (const topic of question.mapped_topics ?? []) {
    if (!taxonomy.categories[topic]) errors.push(`${question.id} maps to unknown topic ${topic}`)
  }
}
for (const gap of agenda.omitted_directions ?? []) {
  if (gap.evidence?.length < 2) errors.push(`${gap.id} has insufficient public evidence`)
  for (const topic of gap.mapped_topics ?? []) {
    if (!taxonomy.categories[topic]) errors.push(`${gap.id} maps to unknown topic ${topic}`)
  }
}
const preprintIds = new Set(preprints.map((paper) => paper.preprint_id))
for (const record of evidence.records) {
  if (!preprintIds.has(record.preprint_id)) errors.push(`sidecar references unknown ${record.preprint_id}`)
  for (const id of record.question_ids) if (!ids.includes(id)) errors.push(`sidecar references unknown ${id}`)
}
for (const page of [
  'docs/questions/index.md',
  'docs/questions/blind-spots.md',
  'docs/methods/research-question-layer.md',
  'docs/public/research-question-evidence.json',
]) {
  if (!fs.existsSync(path.join(root, page))) errors.push(`missing ${page}`)
}
if (errors.length) {
  console.error(`Research agenda audit failed (${errors.length})`)
  for (const error of errors) console.error(`- ${error}`)
  process.exit(1)
}
console.log(`Research agenda audit passed: ${ids.length} questions, ${evidence.records.length} matched preprints.`)
