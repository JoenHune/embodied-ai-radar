import test from 'node:test'
import assert from 'node:assert/strict'
import { createPulseSource, loadPulseSource } from '../docs/.vitepress/theme/lib/pulse-sources.mjs'

const json = body => new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } })
const organization = { organization_id: 'org:lab', updates: [{ event_id: 'event:paper' }] }
const event = { event_id: 'event:accepted', event_type: 'accepted' }

test('one successful source remains available when the other fails and can recover independently', async () => {
  const organizations = createPulseSource(), events = createPulseSource()
  await Promise.all([
    loadPulseSource(organizations, '/organizations', 'organizations', { fetcher: async () => json({ rows: [organization] }) }),
    loadPulseSource(events, '/events', 'events', { fetcher: async () => new Response('', { status: 503 }) }),
  ])
  assert.deepEqual(organizations.rows, [organization])
  assert.equal(organizations.loaded, true)
  assert.equal(organizations.error, '')
  assert.equal(events.loaded, false)
  assert.match(events.error, /证据升级记录暂时无法读取/)
  await loadPulseSource(events, '/events', 'events', { fetcher: async () => json({ events: [event] }) })
  assert.deepEqual(events.rows, [event])
  assert.equal(events.loaded, true)
  assert.equal(events.error, '')
  assert.equal(organizations.request, 1)
})

test('failed refresh preserves the successful payload, without implying a successful empty result', async () => {
  const state = createPulseSource()
  await loadPulseSource(state, '/events', 'events', { fetcher: async () => json([event]) })
  await loadPulseSource(state, '/events', 'events', { fetcher: async () => { throw new Error('offline') } })
  assert.deepEqual(state.rows, [event])
  assert.equal(state.loaded, true)
  assert.equal(state.loading, false)
  assert.match(state.error, /保留上次成功载入的数据/)
})

test('successful empty payloads are distinct from bad schema, bad JSON and HTTP failures', async () => {
  for (const [kind, payload] of [['organizations', { rows: [] }], ['events', []], ['events', { events: [] }]]) {
    const state = createPulseSource()
    await loadPulseSource(state, '/source', kind, { fetcher: async () => json(payload) })
    assert.equal(state.loaded, true)
    assert.equal(state.error, '')
    assert.deepEqual(state.rows, [])
  }
  for (const response of [json({}), json({ events: [null] }), json({ events: [{}] }), new Response('invalid JSON'), new Response('', { status: 404 })]) {
    const state = createPulseSource()
    await loadPulseSource(state, '/events', 'events', { fetcher: async () => response })
    assert.equal(state.loaded, false)
    assert.notEqual(state.error, '')
    assert.equal(state.loading, false)
  }
})

test('a late older request cannot replace a newer successful retry', async () => {
  const state = createPulseSource()
  let finishOld
  const old = loadPulseSource(state, '/events', 'events', { fetcher: () => new Promise(resolve => { finishOld = resolve }) })
  assert.equal(state.loading, true)
  await loadPulseSource(state, '/events', 'events', { fetcher: async () => json([event]) })
  finishOld(json([{ event_id: 'event:stale' }]))
  await old
  assert.deepEqual(state.rows, [event])
  assert.equal(state.loading, false)
})

test('an aborted view does not publish a late response or a false source error', async () => {
  const state = createPulseSource(), controller = new AbortController()
  let finish
  const request = loadPulseSource(state, '/events', 'events', { signal: controller.signal, fetcher: () => new Promise(resolve => { finish = resolve }) })
  controller.abort()
  finish(json([event]))
  await request
  assert.deepEqual(state.rows, [])
  assert.equal(state.loaded, false)
  assert.equal(state.error, '')
  assert.equal(state.loading, false)
})
