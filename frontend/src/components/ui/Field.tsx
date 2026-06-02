import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react'
import { cn } from './cn'

const base =
  'h-9 w-full rounded-lg border border-line bg-surface-2 px-3 text-sm text-foreground placeholder:text-faint ' +
  'transition-colors focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/25'

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(base, className)} {...props} />
}

export function Select({ className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select className={cn(base, 'cursor-pointer', className)} {...props}>
      {children}
    </select>
  )
}

export function Label({ children, className }: { children: ReactNode; className?: string }) {
  return <label className={cn('block text-xs font-medium text-muted mb-1.5', className)}>{children}</label>
}
