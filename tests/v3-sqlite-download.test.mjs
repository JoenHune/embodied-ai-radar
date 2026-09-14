import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { createHash } from 'node:crypto'
import { spawnSync } from 'node:child_process'
import { parse, compileScript, compileTemplate } from '@vue/compiler-sfc'
import { auditSqliteDownload } from '../scripts/audit_v3_site.mjs'

const root = path.resolve(import.meta.dirname, '..')
const sha = bytes => createHash('sha256').update(bytes).digest('hex')
const makeZipCode = [
  'import json,sys,zipfile',
  'from pathlib import Path',
  'options=json.loads(sys.argv[2])',
  "raw=b'A'*1000 if options.get('invalidHeader') else b'SQLite format 3\\x00'+b'*'*200000",
  "with zipfile.ZipFile(sys.argv[1],'w',compression=zipfile.ZIP_DEFLATED) as package:",
  " for name in options.get('names',['radar.sqlite']):",
  "  with package.open(name,'w',force_zip64=bool(options.get('zip64'))) as entry:",
  '   entry.write(raw)',
  'payload=bytearray(Path(sys.argv[1]).read_bytes())',
  // Corrupt the central-directory CRC, keeping DEFLATED data valid so this
  // exercises the checksum gate rather than the compression-method gate.
  "if options.get('mode')=='crc': payload[payload.index(b'PK\\x01\\x02')+16]^=1",
  "if options.get('mode')=='truncated': payload=payload[:-22]",
  'Path(sys.argv[1]).write_bytes(payload)',
].join('\n')

function fixture(t, options = {}) {
  // Shell metacharacters exercise argv transport without invoking a shell.
  const dist = fs.mkdtempSync(path.join(os.tmpdir(), "radar-sqlite-audit ' $()-"))
  t.after(() => fs.rmSync(dist, { recursive: true, force: true }))
  fs.mkdirSync(path.join(dist, 'downloads'))
  const archivePath = path.join(dist, 'downloads/radar.sqlite.zip')
  const prepared = spawnSync(process.execPath, [path.join(root, 'scripts/run-python.mjs'), '-B', '-c', makeZipCode,
    archivePath, JSON.stringify(options)], { cwd: root, encoding: 'utf8', shell: false })
  assert.equal(prepared.status, 0, prepared.stderr)
  const raw = options.invalidHeader ? Buffer.alloc(1000, 65) : Buffer.concat([Buffer.from('SQLite format 3\0'), Buffer.alloc(200_000, 42)])
  const archive = fs.readFileSync(archivePath)
  return { dist, raw, archive, archivePath, downloads: { sqlite: '/downloads/radar.sqlite.zip', sqlite_integrity: {
    encoding: 'zip', sha256: sha(raw), archive_sha256: sha(archive), bytes: raw.length, archive_bytes: archive.length
  } } }
}

test('complete ZIP and ZIP64 are streamed by shared verifier without writing decompressed files', async t => {
  for (const zip64 of [false, true]) {
    const f = fixture(t, { zip64 }), before = structuredClone(f.downloads)
    const result = await auditSqliteDownload(f.dist, f.downloads)
    assert.deepEqual(result, { status: 'passed', ...f.downloads.sqlite_integrity })
    assert.deepEqual(f.downloads, before)
    assert.deepEqual(fs.readFileSync(f.archivePath), f.archive)
    assert.deepEqual(fs.readdirSync(path.join(f.dist, 'downloads')), ['radar.sqlite.zip'])
  }
})

test('bad entry CRC and truncation fail even with matching archive hash and length', async t => {
  for (const mode of ['crc', 'truncated']) {
    const f = fixture(t, { mode })
    await assert.rejects(auditSqliteDownload(f.dist, f.downloads), /^Error: sqlite_archive_verification_failed$/)
  }
})

test('archive must have the unique safe radar.sqlite entry, not extras or traversal names', async t => {
  for (const names of [['other.sqlite'], ['../radar.sqlite'], ['/radar.sqlite'], ['sub/radar.sqlite'], ['radar.sqlite/'],
                       ['radar.sqlite', 'extra.txt'], ['radar.sqlite', 'radar.sqlite']]) {
    const f = fixture(t, { names })
    await assert.rejects(auditSqliteDownload(f.dist, f.downloads), /sqlite_archive_verification_failed/)
  }
})

test('all four byte/hash fields bind the archive and decompressed bytes', async t => {
  const f = fixture(t)
  for (const field of ['bytes', 'archive_bytes', 'sha256', 'archive_sha256']) {
    const downloads = structuredClone(f.downloads)
    downloads.sqlite_integrity[field] = field.endsWith('sha256') ? '0'.repeat(64) : downloads.sqlite_integrity[field] + 1
    await assert.rejects(auditSqliteDownload(f.dist, downloads), /sqlite_archive_(?:verification_failed|size_mismatch)/)
  }
  f.downloads.sqlite_integrity.bytes = 16
  await assert.rejects(auditSqliteDownload(f.dist, f.downloads), /sqlite_archive_verification_failed/)
})

test('correct hashes cannot turn a non-SQLite entry into a database', async t => {
  const f = fixture(t, { invalidHeader: true })
  await assert.rejects(auditSqliteDownload(f.dist, f.downloads), /sqlite_archive_verification_failed/)
})

test('raw or gzip leftovers, including broken links, and archive symlinks are rejected', async t => {
  for (const name of ['radar.sqlite', 'radar.sqlite.gz']) {
    const f = fixture(t)
    const legacy = path.join(f.dist, 'downloads', name)
    fs.writeFileSync(legacy, Buffer.from('legacy derived file'))
    await assert.rejects(auditSqliteDownload(f.dist, f.downloads), /legacy_public_duplicate/)
    fs.unlinkSync(legacy)
    fs.symlinkSync(path.join(f.dist, 'not-present'), legacy)
    await assert.rejects(auditSqliteDownload(f.dist, f.downloads), /legacy_public_duplicate/)
  }
  const g = fixture(t)
  const target = path.join(g.dist, 'other.zip')
  fs.renameSync(g.archivePath, target)
  fs.symlinkSync(target, g.archivePath)
  await assert.rejects(auditSqliteDownload(g.dist, g.downloads), /regular_file_required/)
})

test('missing archive, legacy fallback and malformed integrity fail with fixed codes', async t => {
  const f = fixture(t)
  for (const sqlite of [undefined, '/downloads/radar.sqlite', '/downloads/radar.sqlite.gz', 'https://example.test/radar.sqlite.zip', '/downloads/../radar.sqlite.zip']) {
    await assert.rejects(auditSqliteDownload(f.dist, { ...f.downloads, sqlite }), /manifest_download_required/)
  }
  for (const change of [{ encoding: 'gzip' }, { sha256: null }, { bytes: '200016' }, { bytes: -1 }, { archive_bytes: NaN }, { status: 'passed' }]) {
    await assert.rejects(auditSqliteDownload(f.dist, { ...f.downloads, sqlite_integrity: { ...f.downloads.sqlite_integrity, ...change } }), /integrity_manifest_invalid/)
  }
  await assert.rejects(auditSqliteDownload(f.dist, { sqlite: '/downloads/radar.sqlite.zip' }), /integrity_manifest_invalid/)
  fs.unlinkSync(f.archivePath)
  await assert.rejects(auditSqliteDownload(f.dist, f.downloads), /^Error: sqlite_archive_missing$/)
})

test('unavailable Python verifier cannot silently skip integrity verification', async t => {
  const f = fixture(t), old = process.env.V3_PYTHON
  process.env.V3_PYTHON = path.join(f.dist, 'no-python-here')
  try { await assert.rejects(auditSqliteDownload(f.dist, f.downloads), /^Error: sqlite_archive_verification_failed$/) }
  finally { if (old === undefined) delete process.env.V3_PYTHON; else process.env.V3_PYTHON = old }
})

test('all download explanations require ZIP extraction and the Vue template compiles', () => {
  const urlRoot = new URL('../', import.meta.url)
  const ui = fs.readFileSync(new URL('docs/.vitepress/theme/components/DatabaseExplorer.vue', urlRoot), 'utf8')
  const descriptor = parse(ui).descriptor
  const script = compileScript(descriptor, { id: 'sqlite-download' })
  assert.deepEqual(compileTemplate({ id: 'sqlite-download', source: descriptor.template.content, compilerOptions: { bindingMetadata: script.bindings } }).errors, [])
  for (const name of ['README.md', 'docs/methods/index.md', 'docs/methods/people.md', 'docs/.vitepress/theme/components/DatabaseExplorer.vue']) {
    const source = fs.readFileSync(new URL(name, urlRoot), 'utf8')
    assert.match(source, /\/downloads\/radar\.sqlite\.zip/)
    assert.match(source, /ZIP/)
    assert.match(source, /解压/)
    assert.doesNotMatch(source, /\/downloads\/radar\.sqlite(?:\.gz)?['"\x60)]/)
  }
  const audit = fs.readFileSync(new URL('scripts/audit_v3_site.mjs', urlRoot), 'utf8')
  assert.match(audit, /deploymentBytes > 1_000_000_000/)
})
