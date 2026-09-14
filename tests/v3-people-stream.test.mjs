import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { PEOPLE_BATCH_SIZE, nextPeopleCount, peopleStreamKey, observePeopleEnd, preservePeoplePage } from '../docs/.vitepress/theme/lib/people-stream.mjs'

test('successive batches retain earlier people and stop at the result count', () => {
  const people = Array.from({ length: 32 }, (_, i) => i)
  let count = PEOPLE_BATCH_SIZE
  for (const expected of [24, 32, 32]) {
    const before = people.slice(0, count)
    count = nextPeopleCount(count, people.length)
    assert.equal(count, expected)
    assert.deepEqual(people.slice(0, count).slice(0, before.length), before)
  }
  assert.equal(nextPeopleCount(12, 0), 0)
  assert.equal(nextPeopleCount(12, 5), 5)
})

test('profiles share a stream; changed search, direction, lens or sort starts a new one', () => {
  const state = { q: '', direction: '', lens: 'contribution', sort: 'name', person: '' }
  assert.equal(peopleStreamKey(state), peopleStreamKey({ ...state, person: 'yilun-du' }))
  for (const change of [{ q: 'Du' }, { direction: 'D3' }, { lens: 'recent' }, { sort: 'active' }]) {
    assert.notEqual(peopleStreamKey(state), peopleStreamKey({ ...state, ...change }))
  }
})

test('near-end observer honors loading/modal guards and ignores callbacks after disposal', () => {
  let instance, allowed = true, loads = 0
  class Observer {
    constructor(callback, options) { this.callback = callback; this.options = options; instance = this }
    observe(element) { this.element = element }
    disconnect() { this.disconnected = true }
  }
  const element = {}
  const stop = observePeopleEnd(element, () => allowed, () => loads++, Observer)
  assert.equal(instance.element, element)
  assert.equal(instance.options.rootMargin, '360px 0px')
  instance.callback([{ isIntersecting: false }])
  assert.equal(loads, 0)
  instance.callback([{ isIntersecting: true }])
  assert.equal(loads, 1)
  allowed = false
  instance.callback([{ isIntersecting: true }])
  assert.equal(loads, 1)
  stop()
  allowed = true
  instance.callback([{ isIntersecting: true }])
  assert.equal(loads, 1)
  assert.equal(instance.disconnected, true)
})

test('observer-less browsers keep the manual append fallback', () => {
  let loads = 0
  const stop = observePeopleEnd({}, () => true, () => loads++, null)
  assert.equal(loads, 0)
  assert.doesNotThrow(stop)
  const component = fs.readFileSync(new URL('../docs/.vitepress/theme/components/PeopleRadar.vue', import.meta.url), 'utf8')
  assert.match(component, /filtered\.value\.slice\(0, visibleCount\.value\)/)
  assert.match(component, /@click="loadMorePeople\(true\)"/)
  assert.doesNotMatch(component, /people-pagination|上一页|下一页/)
  assert.match(component, /stopStreamObserver\(\); personDialog/)
  assert.match(component, /resetStream && streamKey\.value !== peopleStreamKey/)
  assert.match(component, /watch\(\[streamEnd, streamKey, visibleCount, hasMore/)
  const links = [...component.matchAll(/<a\b[^>]*:href="profileHref\(/g)]
  assert.equal(links.length, 5)
  for (const [link] of links) assert.match(link, /class="vp-raw"/)
})

test('query/history stays in the current people component; cross-page navigation is unchanged', () => {
  const previous = href => href === '/blocked' ? false : undefined
  const router = { onBeforePageLoad: previous }
  let restores = 0
  const release = preservePeoplePage(router, '/embodied-ai-radar/organizations/people/', () => restores++)
  assert.equal(router.onBeforePageLoad('/embodied-ai-radar/organizations/people/?person=yilun-du'), false)
  assert.equal(router.onBeforePageLoad('/embodied-ai-radar/organizations/people/'), false)
  assert.equal(router.onBeforePageLoad('/embodied-ai-radar/database/'), undefined)
  assert.equal(router.onBeforePageLoad('/blocked'), false)
  assert.equal(restores, 2)
  release()
  assert.equal(router.onBeforePageLoad, previous)
  const releaseAgain = preservePeoplePage(router, '/embodied-ai-radar/organizations/people/')
  const replacement = () => true
  router.onBeforePageLoad = replacement
  releaseAgain()
  assert.equal(router.onBeforePageLoad, replacement)
})
