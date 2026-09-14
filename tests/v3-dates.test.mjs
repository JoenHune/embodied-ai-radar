import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { eventDate, eventMonth, publicationEventDate } from '../docs/.vitepress/theme/lib/dates.ts'

test('publication events retain month precision instead of selecting an old exact-day fallback', () => {
  assert.equal(publicationEventDate({ published_at: '2026-08-01', occurred_at: '2026-08-27', date_precision: 'month' }), '2026-08（仅月份）')
  assert.equal(publicationEventDate({ published_at: '2026-01-01', date_precision: 'year' }), '2026（仅年份）')
  assert.equal(publicationEventDate({ published_at: '2026-08-01', date_precision: 'unknown' }), '日期待核验')
})
test('event cards and company reports use the precision-carrying formatter', () => {
  for (const name of ['PulseFeed.vue', 'RadarDashboard.vue']) {
    const source = fs.readFileSync(new URL(`../docs/.vitepress/theme/components/${name}`, import.meta.url), 'utf8')
    assert.match(source, /publicationEventDate\((?:event|update)\)/)
    assert.doesNotMatch(source, /eventDate\((?:event|update)\.(?:published_at|occurred_at)[^)]*\)/)
  }
})

test('UTC instants cross the Shanghai day and month boundary', () => {
  assert.equal(eventDate('2026-08-31T20:00:00Z'), '2026-09-01 04:00（北京时间）')
  assert.equal(eventMonth('2026-08-31T20:00:00Z'), '2026-09')
})
test('second-precision archive bounds retain seconds in the local display', () => {
  assert.equal(eventDate('2026-08-26T17:31:56Z','second'), '2026-08-27 01:31:56（北京时间）')
})
test('explicit offsets convert and date-only precision is preserved', () => {
  assert.equal(eventDate('2026-09-01T04:00:00+08:00'), '2026-09-01 04:00（北京时间）')
  assert.equal(eventDate('2026-09-01'), '2026-09-01')
  assert.equal(eventDate('2026-09'), '2026-09')
  assert.equal(eventMonth('2026-09-01'), '2026-09')
})
test('unknown timezone and invalid instants are not silently converted', () => {
  assert.equal(eventDate('2026-09-01T04:00:00'), '2026-09-01T04:00:00（时区未注明）')
  assert.equal(eventMonth('2026-09-01T04:00:00'), '')
  assert.equal(eventDate('invalidZ'), '日期待核验')
  assert.equal(eventMonth('invalidZ'), '')
  assert.equal(eventDate(null), '日期待核验')
})
test('month, year and unknown precision do not display invented exact dates', () => {
  assert.equal(eventDate('2026-08-01', 'month'), '2026-08（仅月份）')
  assert.equal(eventDate('2026-01-01', 'year'), '2026（仅年份）')
  assert.equal(eventDate('2026-01-01', 'unknown'), '日期待核验')
})
