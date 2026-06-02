import type { ReactNode } from 'react'
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
}: {
  label: string
  value: ReactNode
  hint?: ReactNode
  icon?: ReactNode
  accent?: Accent
}) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4 transition-colors hover:border-zinc-700">
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-medium uppercase tracking-wider text-faint">{label}</p>
        {icon && <span className="text-faint">{icon}</span>}
      </div>
      <p className={cn('mt-2 text-2xl font-semibold tnum leading-none', VALUE_COLOR[accent])}>{value}</p>
      {hint && <p className="mt-1.5 text-xs text-muted">{hint}</p>}
    </div>
  )
}
