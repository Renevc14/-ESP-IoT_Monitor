import { Loader2 } from 'lucide-react'

export function Loading({ label = 'Cargando…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-24 text-sm text-faint">
      <Loader2 size={16} className="animate-spin" />
      {label}
    </div>
  )
}
