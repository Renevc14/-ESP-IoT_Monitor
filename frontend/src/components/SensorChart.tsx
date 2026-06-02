import { Area, AreaChart, CartesianGrid, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

interface Point {
  time: string
  value: number
}

export interface Thresholds {
  criticalLow: number
  warnLow: number
  warnHigh: number
  criticalHigh: number
}

export function SensorChart({
  data,
  color,
  unit = '',
  height = 200,
  thresholds,
}: {
  data: Point[]
  color: string
  unit?: string
  height?: number
  thresholds?: Thresholds
}) {
  const gradId = 'grad-' + color.replace('#', '')

  // Y domain that includes data and threshold bands, with a little padding
  let domain: [number, number] | undefined
  if (thresholds && data.length) {
    const values = data.map((d) => d.value)
    const lo = Math.min(...values, thresholds.criticalLow)
    const hi = Math.max(...values, thresholds.criticalHigh)
    const pad = (hi - lo) * 0.08 || 1
    domain = [Math.floor(lo - pad), Math.ceil(hi + pad)]
  }

  const WARN = 'rgba(251, 191, 36, 0.09)'
  const CRIT = 'rgba(248, 113, 113, 0.10)'

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.3} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#1c2029" vertical={false} />

        {thresholds && domain && (
          <>
            <ReferenceArea y1={domain[0]} y2={thresholds.criticalLow} fill={CRIT} strokeOpacity={0} />
            <ReferenceArea y1={thresholds.criticalLow} y2={thresholds.warnLow} fill={WARN} strokeOpacity={0} />
            <ReferenceArea y1={thresholds.warnHigh} y2={thresholds.criticalHigh} fill={WARN} strokeOpacity={0} />
            <ReferenceArea y1={thresholds.criticalHigh} y2={domain[1]} fill={CRIT} strokeOpacity={0} />
          </>
        )}

        <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#69717f' }} tickLine={false} axisLine={false} minTickGap={28} />
        <YAxis tick={{ fontSize: 11, fill: '#69717f' }} tickLine={false} axisLine={false} width={44} unit={unit} domain={domain ?? ['auto', 'auto']} />
        <Tooltip
          cursor={{ stroke: '#3a414f', strokeWidth: 1 }}
          contentStyle={{ background: '#161922', border: '1px solid #232733', borderRadius: 10, fontSize: 12, boxShadow: '0 8px 24px rgba(0,0,0,0.45)' }}
          labelStyle={{ color: '#9aa3b2', marginBottom: 4 }}
          itemStyle={{ color: '#f5f7fa' }}
          formatter={(v: any) => [`${Number(v).toFixed(2)}${unit}`, 'valor']}
        />
        <Area
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          fill={`url(#${gradId})`}
          dot={false}
          activeDot={{ r: 3.5, fill: color, stroke: '#08090c', strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
