/** Preserve date-only precision; convert actual instants for the reader. */
export function eventDate(value?: string | null, precision?: string | null): string {
  if (!value) return '日期待核验'
  if (precision === 'unknown') return '日期待核验'
  if (precision === 'year' && /^\d{4}/.test(value)) return `${value.slice(0, 4)}（仅年份）`
  if (precision === 'month' && /^\d{4}-\d{2}/.test(value)) return `${value.slice(0, 7)}（仅月份）`
  if (/^\d{4}(?:-\d{2})?(?:-\d{2})?$/.test(value)) return value
  // A timezone-free datetime is not a UTC instant. Preserve that uncertainty.
  if (!/(?:Z|[+-]\d{2}:?\d{2})$/i.test(value)) return `${value}（时区未注明）`
  const date = new Date(value)
  if (!Number.isFinite(date.getTime())) return '日期待核验'
  const parts = new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
    ...(precision === 'second' ? { second: '2-digit' as const } : {}),
  }).formatToParts(date)
  const item = (type: Intl.DateTimeFormatPartTypes) => parts.find(part => part.type === type)?.value
  return `${item('year')}-${item('month')}-${item('day')} ${item('hour')}:${item('minute')}${precision === 'second' ? `:${item('second')}` : ''}（北京时间）`
}

/** Publication displays must carry the source's declared date precision. */
export function publicationEventDate(row: {
  published_at?: string | null
  occurred_at?: string | null
  date?: string | null
  date_precision?: string | null
}): string {
  return eventDate(row.published_at || row.occurred_at || row.date, row.date_precision)
}

/** Month for presentation only; never replace authoritative statistical dates. */
export function eventMonth(value?: string | null): string {
  if (!value) return ''
  if (/^\d{4}-\d{2}(?:-\d{2})?$/.test(value)) return value.slice(0, 7)
  if (!/(?:Z|[+-]\d{2}:?\d{2})$/i.test(value)) return ''
  const date = new Date(value)
  if (!Number.isFinite(date.getTime())) return ''
  const parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit' }).formatToParts(date)
  return `${parts.find(part => part.type === 'year')?.value}-${parts.find(part => part.type === 'month')?.value}`
}
