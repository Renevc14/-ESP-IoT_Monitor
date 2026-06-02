import type { ReactNode } from 'react'
import { Sparkline } from '../Sparkline'
import { cn } from './cn'

type Accent = 'default' | 'success' | 'warning' | 'danger' | 'accent'

const VALUE_COLOR: Record<Accent, string> = {
  default: 'text-foreground',
  success: 'text-success',
  warning: 'text-warning',
  danger: 'text-danger',
  accent: 'text-accent',
}

export function StatCard({
  label,
  value,
  hint,
  icon,
  accent = 'default',
  spark,
}: {
  label: string
  value: ReactNode
  hint?: ReactNode
  icon?: ReactNode
  accent?: Accent
  spark?: number[]
}) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)] transition-colors hover:border-accent/40">
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-medium uppercase tracking-wider text-faint">{label}</p>
        {icon && <span className="text-faint">{icon}</span>}
      </div>
      <div className="mt-2 flex items-end justify-between gap-3">
        <p className={cn('text-2xl font-semibold tnum leading-none', VALUE_COLOR[accent])}>{value}</p>
        {spark && spark.length > 1 && <Sparkline data={spark} className="text-accent" />}
      </div>
      {hint && <p className="mt-1.5 text-xs text-muted">{hint}</p>}
    </div>
  )
}
