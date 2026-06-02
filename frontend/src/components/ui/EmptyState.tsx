import type { ReactNode } from 'react'

export function EmptyState({ icon, title, hint }: { icon?: ReactNode; title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-line py-16 text-center">
      {icon && <div className="text-faint mb-3">{icon}</div>}
      <p className="text-sm text-muted">{title}</p>
      {hint && <p className="text-xs text-faint mt-1">{hint}</p>}
    </div>
  )
}
