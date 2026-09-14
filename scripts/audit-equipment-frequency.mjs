import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
import { hardwareFrequency } from '../docs/.vitepress/theme/lib/hardware-frequency.mjs'

const root = path.resolve(import.meta.dirname, '..')
const api = path.join(root, 'docs/.vitepress/dist/api/v1')
const read = name => JSON.parse(fs.readFileSync(path.join(api, name), 'utf8'))
const index = read('equipment/index.json')
const works = read('equipment/works.json')
const actual = read('equipment/frequency.json')
assert.equal(actual.dataset_version, index.dataset_version)
assert.equal(actual.dataset_version, works.dataset_version)
const expected = hardwareFrequency(index.devices, works.rows)
assert.deepEqual(actual.models, expected.models)
assert.deepEqual(actual.unresolved, expected.unresolved)
for (const row of [...actual.models, ...actual.unresolved]) {
  assert.equal(row.work_count, new Set(row.sources.map(source => source.work_id)).size)
  assert.ok(row.sources.every(source => source.title && source.usages.length && source.usages.every(usage => usage.source_url && usage.statement)))
}
console.log(JSON.stringify({ status: 'passed', equipment_models: actual.models.length, unresolved: actual.unresolved.length, counting_unit: actual.counting_unit }))
