import { Check, ChevronDown } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { cn } from './cn'

export interface SelectOption {
  value: string
  label: string
}

export function SelectMenu({
  value,
  onChange,
  options,
  className,
  placeholder = 'Seleccionar',
}: {
  value: string
  onChange: (v: string) => void
  options: SelectOption[]
  className?: string
  placeholder?: string
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDoc)
      document.removeEventListener('keydown', onKey)
    }
  }, [])

  const current = options.find((o) => o.value === value)

  return (
    <div ref={ref} className={cn('relative', className)}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex h-9 w-full items-center justify-between gap-2 rounded-lg border border-line bg-surface-2 px-3 text-sm text-foreground transition-colors hover:border-accent/40 focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/25"
      >
        <span className={cn('truncate', !current && 'text-faint')}>{current?.label ?? placeholder}</span>
        <ChevronDown size={15} className={cn('shrink-0 text-faint transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div className="absolute z-50 mt-1.5 w-full min-w-max max-h-64 overflow-y-auto rounded-lg border border-line bg-surface p-1 shadow-2xl shadow-black/50 animate-fade-in">
          {options.map((o) => (
            <button
              key={o.value}
              type="button"
              onClick={() => { onChange(o.value); setOpen(false) }}
              className={cn(
                'flex w-full items-center justify-between gap-3 rounded-md px-2.5 py-1.5 text-left text-sm transition-colors',
                o.value === value ? 'bg-accent/15 text-accent' : 'text-muted hover:bg-surface-2 hover:text-foreground',
              )}
            >
              <span className="truncate">{o.label}</span>
              {o.value === value && <Check size={14} className="shrink-0" />}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
