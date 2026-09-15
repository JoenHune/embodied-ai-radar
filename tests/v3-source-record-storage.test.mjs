import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { createHash } from 'node:crypto'
import { readSourceRecordIds, sourceRecordFiles } from '../scripts/lib/source-record-files.mjs'

const names = Array.from({ length: 256 }, (_, i) => `${i.toString(16).padStart(2, '0')}.jsonl`)
const shard = id => `${createHash('sha1').update(id).digest('hex').slice(0, 2)}.jsonl`
function fixture(t, mode = 'legacy') {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'radar-source-storage-test-'))
  t.after(() => fs.rmSync(root, { recursive: true, force: true }))
  const rows = [{ source_record_id: 'source:a', lineage: ['past:a'], payload_hash: 'proof' }, { source_record_id: 'source:b', unknown: null }]
  if (mode === 'legacy') fs.writeFileSync(path.join(root, 'source-records.jsonl'), rows.map(r => JSON.stringify(r)).join('\n') + '\n')
  else {
    const directory = path.join(root, 'source-records'); fs.mkdirSync(directory)
    for (const name of names) fs.writeFileSync(path.join(directory, name), rows.filter(r => shard(r.source_record_id) === name).map(r => JSON.stringify(r) + '\n').join(''))
  }
  return { root, rows, directory: path.join(root, 'source-records'), legacy: path.join(root, 'source-records.jsonl') }
}

test('legacy and all 256 shards expose exactly the same source reference IDs', t => {
  const legacy = fixture(t), sharded = fixture(t, 'sharded')
  assert.deepEqual([...readSourceRecordIds(legacy.root)].sort(), [...readSourceRecordIds(sharded.root)].sort())
  assert.equal(sourceRecordFiles(sharded.root).length, 256)
  assert.equal(sourceRecordFiles(legacy.root).length, 1)
})

test('a partial or empty directory never silently shadows a legacy file', t => {
  const f = fixture(t)
  fs.mkdirSync(f.directory)
  assert.throws(() => readSourceRecordIds(f.root), /mixed_legacy/)
})

test('missing and extra partitions fail closed', t => {
  const missing = fixture(t, 'sharded')
  fs.unlinkSync(path.join(missing.directory, '00.jsonl'))
  assert.throws(() => readSourceRecordIds(missing.root), /incomplete_or_unexpected/)
  const extra = fixture(t, 'sharded')
  fs.writeFileSync(path.join(extra.directory, 'extra.jsonl'), '')
  assert.throws(() => readSourceRecordIds(extra.root), /incomplete_or_unexpected/)
})

test('migration marker blocks both legacy and newly installed source layouts', t => {
  for (const mode of ['legacy', 'sharded']) {
    const f = fixture(t, mode)
    fs.writeFileSync(path.join(f.root, '.source-records-migration.json'), '{}')
    assert.throws(() => readSourceRecordIds(f.root), /recovery_required/)
  }
})

test('duplicate source IDs are rejected rather than collapsed into a Set', t => {
  for (const mode of ['legacy', 'sharded']) {
    const f = fixture(t, mode)
    const target = mode === 'legacy' ? f.legacy : path.join(f.directory, shard('source:a'))
    fs.appendFileSync(target, JSON.stringify(f.rows[0]) + '\n')
    assert.throws(() => readSourceRecordIds(f.root), /duplicate_source_record_id/)
  }
})

test('wrong shard and malformed payload IDs cannot enter website reference audit', t => {
  const f = fixture(t, 'sharded')
  const target = path.join(f.directory, names.find(n => n !== shard('source:a')))
  fs.appendFileSync(target, JSON.stringify(f.rows[0]) + '\n')
  assert.throws(() => readSourceRecordIds(f.root), /wrong_shard|duplicate_source_record_id/)
  const bad = fixture(t)
  fs.writeFileSync(bad.legacy, '{"source_record_id":null}\n')
  assert.throws(() => readSourceRecordIds(bad.root), /invalid_source_record_id/)
  fs.writeFileSync(bad.legacy, '{not JSON}\n')
  assert.throws(() => readSourceRecordIds(bad.root), /invalid_source_json/)
})

test('symlink and directory shard substitutions are refused', t => {
  for (const replacement of ['symlink', 'directory']) {
    const f = fixture(t, 'sharded'), target = path.join(f.directory, '00.jsonl')
    fs.unlinkSync(target)
    if (replacement === 'symlink') fs.symlinkSync(path.join(f.root, 'outside.jsonl'), target)
    else fs.mkdirSync(target)
    assert.throws(() => readSourceRecordIds(f.root), /regular_source_file/)
  }
})

test('website audit uses the shared layout-aware source reader', () => {
  const text = fs.readFileSync(new URL('../scripts/audit_v3_site.mjs', import.meta.url), 'utf8')
  assert.match(text, /readSourceRecordIds\(path\.join\(root, 'data\/catalog'\)\)/)
  assert.doesNotMatch(text, /createReadStream\(sourceFile/)
})

test('a previously read shard changed later is detected by the final signature check', t => {
  const f = fixture(t, 'sharded')
  const target = path.join(f.directory, shard('source:a'))
  const original = fs.readFileSync
  let reads = 0
  fs.readFileSync = function (...args) {
    const result = original.apply(this, args)
    reads++
    if (reads === 256) fs.appendFileSync(target, '\n')
    return result
  }
  try { assert.throws(() => readSourceRecordIds(f.root), /source_changed_while_reading/) }
  finally { fs.readFileSync = original }
})
