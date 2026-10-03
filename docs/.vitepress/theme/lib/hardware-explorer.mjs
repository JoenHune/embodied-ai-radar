export const emptyFilters = () => ({ categories: [], devices: [], evidence: 'candidate', from: '', to: '', query: '' })
export const normalize = value => String(value || '').normalize('NFKC').toLocaleLowerCase().replace(/[\s_:/-]+/g, '')
export const deviceSearch = (device, query) => query.trim().split(/\s+/).every(token => [device.name, ...device.aliases].some(name => normalize(name).includes(normalize(token))))
export const evidenceMatch = (match, evidence) => evidence === 'verified' ? match.usage_verified === true : evidence === 'background' ? match.context_only : evidence === 'simulation' ? match.simulation : evidence === 'all' ? true : !match.context_only
export function matchingMentions(row, filters) {
  return row.matches.filter(m => (!filters.categories.length || filters.categories.includes(m.group)) && (!filters.devices.length || filters.devices.includes(m.device_id)) && evidenceMatch(m, filters.evidence))
}
export function filterRows(rows, filters) {
  const key = normalize(filters.query)
  return rows.filter(row => (!key || normalize(row.title + ' ' + row.id).includes(key)) && (!filters.from || row.month && row.month >= filters.from) && (!filters.to || row.month && row.month <= filters.to) && matchingMentions(row, filters).length)
}
const dateCompare = (a, b) => (b.date || '').localeCompare(a.date || '')
export function sortRows(rows, order) {
  return [...rows].sort((a,b) => {
    if (order === 'citations') {
      const x = a.citation?.count, y = b.citation?.count
      if (x != null || y != null) {
        if (x == null) return 1
        if (y == null) return -1
        if (x !== y) return y-x
      }
    }
    if (!a.date && b.date) return 1
    if (!b.date && a.date) return -1
    const dates=dateCompare(a,b)
    if (dates) return order === 'oldest' ? -dates : dates
    return a.title.localeCompare(b.title, 'en') || a.id.localeCompare(b.id, 'en')
  })
}
export const periodOf = (month, granularity) => granularity === 'quarter' ? `${month.slice(0,4)} Q${Math.ceil(Number(month.slice(5,7))/3)}` : month
export function trendSeries(data, filters, granularity='quarter') {
  const counts=new Map(), denominators=new Map(), catalog=new Map()
  const inRange = m => (!filters.from || m>=filters.from) && (!filters.to || m<=filters.to)
  for (const [month,n] of Object.entries(data.catalog_months)) if(inRange(month)) {
    const period=periodOf(month,granularity);catalog.set(period,(catalog.get(period)||0)+n)
  }
  for (const row of data.rows) {
    if (!row.month || !inRange(row.month) || row.process_state !== 'extracted_not_read') continue
    const period=periodOf(row.month,granularity)
    denominators.set(period,(denominators.get(period)||0)+1)
    // Denominator intentionally independent of hardware/evidence selections.
    if(matchingMentions(row,filters).length) counts.set(period,(counts.get(period)||0)+1)
  }
  return [...new Set([...catalog.keys(),...denominators.keys()])].sort().map(period => {
    const analyzed=denominators.get(period)||0,total=catalog.get(period)||0,count=counts.get(period)||0
    return {period,count,analyzed,catalog:total,share:analyzed ? count/analyzed : null,coverage:total ? analyzed/total : null}
  })
}
export function growthRanking(data, filters, granularity='quarter', minimum=5) {
  const series=trendSeries(data,filters,granularity)
  const cutoff=data.data_through
  if(!/^\d{4}-\d{2}-\d{2}$/.test(cutoff||''))return {periods:[],rows:[],reason:'Catalog cutoff unavailable'}
  const bounds=period=>{
    const year=Number(period.slice(0,4)),endMonth=granularity==='quarter'?Number(period.slice(-1))*3:Number(period.slice(5,7))
    const beginMonth=granularity==='quarter'?endMonth-2:endMonth
    const start=`${year}-${String(beginMonth).padStart(2,'0')}`
    const end=`${year}-${String(endMonth).padStart(2,'0')}`
    const lastDay=new Date(Date.UTC(year,endMonth,0)).getUTCDate()
    return {start,end,endDate:`${end}-${lastDay}`}
  }
  const complete=series.filter(p=>{
    const b=bounds(p.period)
    return b.endDate<=cutoff&&(!filters.from||filters.from<=b.start)&&(!filters.to||filters.to>=b.end)
  })
  const last=complete.slice(-2)
  if(last.length!==2) return {periods:last.map(p=>p.period),rows:[],reason:'需要两个完整时期'}
  const [base,current]=last
  // Require adjacent equal-length periods; never bridge an empty/missing time gap.
  const index=p=>granularity==='quarter' ? Number(p.slice(0,4))*4+Number(p.slice(-1))-1 : Number(p.slice(0,4))*12+Number(p.slice(5,7))-1
  if(index(current.period)-index(base.period)!==1 || base.coverage==null || current.coverage==null || base.coverage<.5 || current.coverage<.5) return {periods:last.map(p=>p.period),rows:[],reason:'两个时期的目录覆盖均需达到 50%'}
  const allowed=new Set(data.devices.filter(d => (!filters.categories.length || filters.categories.includes(d.group)) && (!filters.devices.length || filters.devices.includes(d.id))).map(d=>d.id))
  const values=new Map()
  for(const row of data.rows) {
    if(!row.month || row.process_state!=='extracted_not_read')continue
    const period=periodOf(row.month,granularity)
    if(period!==base.period&&period!==current.period)continue
    for(const id of new Set(row.matches.filter(m=>allowed.has(m.device_id)&&evidenceMatch(m,filters.evidence)).map(m=>m.device_id))) {
      const n=values.get(id)||[0,0];n[period===base.period?0:1]++;values.set(id,n)
    }
  }
  const rows=[...values].filter(([,n])=>n[1]>=minimum&&(n[0]===0||n[0]>=minimum)).map(([id,[previous,count]])=>({id,previous,count,growth:previous ? (count/current.analyzed)/(previous/base.analyzed)-1 : null}))
  rows.sort((a,b)=>(b.growth??-Infinity)-(a.growth??-Infinity)||b.count-a.count||a.id.localeCompare(b.id))
  return {periods:last.map(p=>p.period),rows:rows.slice(0,5),reason:rows.length?'':'样本未达到门槛（每期至少 5 篇；新增设备当期至少 5 篇）'}
}
