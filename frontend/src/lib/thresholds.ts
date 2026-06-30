export interface Thresholds {
  criticalLow: number
  warnLow: number
  warnHigh: number
  criticalHigh: number
}

/** ASHRAE TC 9.9 + industry thresholds used across the platform. */
export const THRESHOLDS: Record<string, Thresholds> = {
  temperature: { criticalLow: 10, warnLow: 15, warnHigh: 35, criticalHigh: 40 },
  humidity: { criticalLow: 20, warnLow: 30, warnHigh: 80, criticalHigh: 90 },
  // Energía en kW con signo (modelo de panel solar): valores negativos = descarga/fallo
  // del inversor; valores altos = sobreconsumo. Coherente con el seed de reglas de alerta.
  energy: { criticalLow: -3, warnLow: -2, warnHigh: 4, criticalHigh: 5 },
}

export type Status = 'normal' | 'warning' | 'critical'

export function statusFor(sensor: string, value: number): Status {
  const t = THRESHOLDS[sensor]
  if (!t) return 'normal'
  if (value <= t.criticalLow || value >= t.criticalHigh) return 'critical'
  if (value <= t.warnLow || value >= t.warnHigh) return 'warning'
  return 'normal'
}

export const STATUS_TONE: Record<Status, 'success' | 'warning' | 'danger'> = {
  normal: 'success',
  warning: 'warning',
  critical: 'danger',
}

export const STATUS_LABEL: Record<Status, string> = {
  normal: 'normal',
  warning: 'advertencia',
  critical: 'crítico',
}

export const STATUS_TEXT: Record<Status, string> = {
  normal: 'text-foreground',
  warning: 'text-warning',
  critical: 'text-danger',
}
