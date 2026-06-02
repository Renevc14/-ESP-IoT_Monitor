import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { AuthShell } from '../components/AuthShell'
import { Button } from '../components/ui/Button'
import { Input, Label } from '../components/ui/Field'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/auth/forgot-password', { email })
      setSent(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell title="Recuperar contraseña" subtitle="Te enviaremos un enlace por email">
      {sent ? (
        <p className="text-sm text-muted">
          Si el email existe, enviamos un enlace de recuperación. Revisa tu bandeja de entrada.
        </p>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          <div>
            <Label>Email</Label>
            <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="tu@email.com" />
          </div>
          <Button type="submit" disabled={loading} className="w-full">{loading ? 'Enviando…' : 'Enviar enlace'}</Button>
        </form>
      )}
      <p className="mt-5 text-center text-xs text-faint">
        <Link to="/login" className="text-accent hover:underline">Volver a iniciar sesión</Link>
      </p>
    </AuthShell>
  )
}
