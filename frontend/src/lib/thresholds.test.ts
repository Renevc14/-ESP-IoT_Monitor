import { describe, expect, it } from 'vitest'

import { statusFor } from './thresholds'

describe('statusFor', () => {
  it('clasifica como normal dentro de rango', () => {
    expect(statusFor('temperature', 22)).toBe('normal')
    expect(statusFor('humidity', 50)).toBe('normal')
  })

  it('clasifica como advertencia cerca de los umbrales', () => {
    expect(statusFor('temperature', 37)).toBe('warning')
    expect(statusFor('temperature', 12)).toBe('warning')
  })

  it('clasifica como crítico fuera de los umbrales', () => {
    expect(statusFor('temperature', 45)).toBe('critical')
    expect(statusFor('temperature', 5)).toBe('critical')
  })

  it('trata un sensor desconocido como normal', () => {
    expect(statusFor('desconocido', 9999)).toBe('normal')
  })
})
