import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

interface Point {
  time: string
  value: number
}

export function SensorChart({ data, color, unit = '', height = 200 }: { data: Point[]; color: string; unit?: string; height?: number }) {
  const gradId = 'grad-' + color.replace('#', '')
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.3} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#1f1f24" vertical={false} />
        <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#71717a' }} tickLine={false} axisLine={false} minTickGap={28} />
        <YAxis tick={{ fontSize: 11, fill: '#71717a' }} tickLine={false} axisLine={false} width={44} unit={unit} />
        <Tooltip
          cursor={{ stroke: '#3f3f46', strokeWidth: 1 }}
          contentStyle={{ background: '#18181c', border: '1px solid #26262b', borderRadius: 10, fontSize: 12, boxShadow: '0 8px 24px rgba(0,0,0,0.45)' }}
          labelStyle={{ color: '#a1a1aa', marginBottom: 4 }}
          itemStyle={{ color: '#fafafa' }}
          formatter={(v: any) => [`${Number(v).toFixed(2)}${unit}`, 'valor']}
        />
        <Area
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          fill={`url(#${gradId})`}
          dot={false}
          activeDot={{ r: 3.5, fill: color, stroke: '#09090b', strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
