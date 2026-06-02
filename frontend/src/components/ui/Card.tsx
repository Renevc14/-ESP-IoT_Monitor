import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from './cn'

export function Card({ className, hover, ...props }: HTMLAttributes<HTMLDivElement> & { hover?: boolean }) {
  return (
    <div
      className={cn(
        'rounded-xl border border-line bg-surface shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)]',
        hover && 'transition-colors hover:border-accent/40',
        className,
      )}
      {...props}
    />
  )
}

export function CardHeader({ title, subtitle, action }: { title: ReactNode; subtitle?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3 px-5 pt-4 pb-3">
      <div>
        <h3 className="text-sm font-medium text-foreground">{title}</h3>
        {subtitle && <p className="text-xs text-faint mt-0.5">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}
