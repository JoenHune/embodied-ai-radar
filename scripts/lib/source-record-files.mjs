import fs from 'node:fs'
import path from 'node:path'
import { createHash } from 'node:crypto'

const shardNames = Array.from({ length: 256 }, (_, i) => `${i.toString(16).padStart(2, '0')}.jsonl`)
const stat = file => fs.lstatSync(file, { throwIfNoEntry: false })
const fail = code => { throw new Error(`source_record_store:${code}`) }
const regular = file => {
  const value = stat(file)
  if (!value?.isFile() || value.isSymbolicLink()) fail('regular_source_file_required')
}

export function sourceRecordFiles(catalog) {
  if (stat(catalog)?.isSymbolicLink()) fail('catalog_symlink_not_allowed')
  if (stat(path.join(catalog, '.source-records-migration.json'))) fail('migration_in_progress_recovery_required')
  const legacy = path.join(catalog, 'source-records.jsonl')
  const directory = path.join(catalog, 'source-records')
  const flat = stat(legacy), shards = stat(directory)
  if (flat && shards) fail('mixed_legacy_and_sharded_layout')
  if (shards) {
    if (!shards.isDirectory() || shards.isSymbolicLink()) fail('regular_shard_directory_required')
    if (fs.readdirSync(directory).sort().join('\n') !== shardNames.join('\n')) fail('incomplete_or_unexpected_shard_files')
    const files = shardNames.map(name => path.join(directory, name))
    files.forEach(regular)
    return files
  }
  if (!flat) fail('source_table_missing')
  regular(legacy)
  return [legacy]
}

function readStableFile(file) {
  regular(file)
  const fd = fs.openSync(file, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK)
  try {
    const before = fs.fstatSync(fd, { bigint: true })
    if (!before.isFile()) fail('regular_source_file_required')
    const text = fs.readFileSync(fd, 'utf8')
    const after = fs.fstatSync(fd, { bigint: true }), current = fs.lstatSync(file, { bigint: true, throwIfNoEntry: false })
    const fields = ['dev', 'ino', 'size', 'mtimeNs', 'ctimeNs', 'mode']
    if (!current || fields.some(key => before[key] !== after[key] || after[key] !== current[key])) fail('source_changed_while_reading')
    return { text, signature: fields.map(key => after[key]) }
  } finally { fs.closeSync(fd) }
}

// ID/reference audit only. Python's catalogue/fidelity audit verifies complete
// payload values. Do not convert these parsed JS numbers back into authority.
export function readSourceRecordIds(catalog) {
  const files = sourceRecordFiles(catalog)
  const ids = new Set()
  const signatures = new Map()
  for (const file of files) {
    const reading = readStableFile(file)
    signatures.set(file, reading.signature)
    for (const line of reading.text.split(/\r?\n/)) {
      if (!line.trim()) continue
      let row
      try { row = JSON.parse(line) } catch { fail('invalid_source_json') }
      if (!row || Array.isArray(row) || typeof row !== 'object' || typeof row.source_record_id !== 'string' || !row.source_record_id) fail('missing_or_invalid_source_record_id')
      if (ids.has(row.source_record_id)) fail('duplicate_source_record_id')
      if (path.dirname(file) === path.join(catalog, 'source-records') &&
          `${createHash('sha1').update(row.source_record_id).digest('hex').slice(0, 2)}.jsonl` !== path.basename(file)) fail('source_record_in_wrong_shard')
      ids.add(row.source_record_id)
    }
  }
  if (sourceRecordFiles(catalog).join('\n') !== files.join('\n')) fail('source_layout_changed_while_reading')
  for (const file of files) {
    const current = fs.lstatSync(file, { bigint: true, throwIfNoEntry: false })
    if (!current || ['dev', 'ino', 'size', 'mtimeNs', 'ctimeNs', 'mode'].some((key, i) => current[key] !== signatures.get(file)[i])) fail('source_changed_while_reading')
  }
  return ids
}
