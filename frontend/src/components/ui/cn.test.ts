import { describe, expect, it } from 'vitest'

import { cn } from './cn'

describe('cn', () => {
  it('une clases válidas con espacios', () => {
    expect(cn('a', 'b', 'c')).toBe('a b c')
  })

  it('descarta valores falsy (condicionales)', () => {
    expect(cn('a', false, null, undefined, '', 'b')).toBe('a b')
  })
})
