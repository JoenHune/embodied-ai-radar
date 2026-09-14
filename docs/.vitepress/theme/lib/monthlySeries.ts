export type MonthlyValue = number | null

/** Never connect incomplete-month observations to a complete-month trend. */
export function splitMonthlySeries(
  months: string[], values: Array<number | null | undefined>, completeMonths: string[],
  provisionalMonth: string, provisionalHasData: boolean,
) {
  const completeSet = new Set(completeMonths)
  const known = (value: number | null | undefined): MonthlyValue => typeof value === 'number' && Number.isFinite(value) ? value : null
  const complete = months.map((month, index) => completeSet.has(month) ? known(values[index]) : null)
  const provisional = months.map((month, index) => month === provisionalMonth && !completeSet.has(month) && provisionalHasData ? known(values[index]) : null)
  const display = months.map((_, index) => complete[index] ?? provisional[index])
  return { complete, provisional, display }
}

export function monthlyValueLabel(value: MonthlyValue, metric: string): string {
  return value === null ? '未知（暂无采集数据）' : metric === 'shares' ? `${(value * 100).toFixed(1)}%` : String(value)
}

export function completeMonthRange(completeMonths: string[], provisionalMonth: string): string {
  const range = completeMonths.length ? `${completeMonths[0]}—${completeMonths.at(-1)} 完整月` : '完整月待登记'
  return `${range}；${provisionalMonth} 暂行月独立展示`
}
