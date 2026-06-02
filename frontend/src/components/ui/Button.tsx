import type { ButtonHTMLAttributes } from 'react'
import { cn } from './cn'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
type Size = 'sm' | 'md'

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-accent text-accent-foreground hover:bg-accent-hover shadow-sm shadow-accent/25',
  secondary: 'bg-surface-2 text-foreground border border-line hover:border-zinc-600',
  ghost: 'text-muted hover:text-foreground hover:bg-surface-2',
  danger: 'bg-danger/15 text-danger hover:bg-danger/25',
}

const SIZES: Record<Size, string> = {
  sm: 'h-8 px-3 text-xs gap-1.5',
  md: 'h-9 px-4 text-sm gap-2',
}

export function buttonClasses(variant: Variant = 'primary', size: Size = 'md', className?: string) {
  return cn(
    'inline-flex items-center justify-center rounded-lg font-medium transition-colors',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60 focus-visible:ring-offset-2 focus-visible:ring-offset-background',
    'disabled:opacity-50 disabled:pointer-events-none',
    VARIANTS[variant],
    SIZES[size],
    className,
  )
}

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
}

export function Button({ variant = 'primary', size = 'md', className, ...props }: Props) {
  return <button className={buttonClasses(variant, size, className)} {...props} />
}
