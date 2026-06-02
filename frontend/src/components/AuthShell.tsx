import { Activity } from 'lucide-react'
import type { ReactNode } from 'react'

export function AuthShell({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <div className="relative min-h-screen flex items-center justify-center bg-background px-4 overflow-hidden">
      <div
        className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 h-[420px] w-[620px] rounded-full opacity-25 blur-[120px]"
        style={{ background: 'radial-gradient(closest-side, #22d3ee, transparent)' }}
      />
      <div className="relative w-full max-w-sm">
        <div className="flex flex-col items-center mb-7">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent/15 text-accent mb-3 ring-1 ring-accent/20">
            <Activity size={22} />
          </div>
          <h1 className="text-lg font-semibold text-foreground">{title}</h1>
          {subtitle && <p className="text-sm text-muted mt-1 text-center">{subtitle}</p>}
        </div>
        <div className="rounded-2xl border border-line bg-surface p-7 shadow-2xl shadow-black/40">{children}</div>
      </div>
    </div>
  )
}
