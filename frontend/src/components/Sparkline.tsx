import { useId } from 'react'
import { Area, AreaChart, ResponsiveContainer } from 'recharts'
import { cn } from './ui/cn'

export function Sparkline({ data, className, width = 88, height = 34 }: { data: number[]; className?: string; width?: number; height?: number }) {
  const id = useId().replace(/:/g, '')
  const points = data.map((v, i) => ({ i, v }))
  return (
    <div className={cn('text-accent shrink-0', className)} style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={points} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="currentColor" stopOpacity={0.4} />
              <stop offset="100%" stopColor="currentColor" stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area type="monotone" dataKey="v" stroke="currentColor" strokeWidth={1.5} fill={`url(#${id})`} dot={false} isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
