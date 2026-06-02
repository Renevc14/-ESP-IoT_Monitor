import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { AuthShell } from '../components/AuthShell'
import { Button } from '../components/ui/Button'
import { Input, Label } from '../components/ui/Field'

export default function ResetPassword() {
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [ok, setOk] = useState(false)
  const [loading, setLoading] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.post('/auth/reset-password', { token, new_password: password })
      setOk(true)
      setTimeout(() => navigate('/login'), 1600)
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'No se pudo restablecer la contraseña')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell title="Nueva contraseña" subtitle="Define tu nueva contraseña">
      {!token ? (
        <p className="text-sm text-danger">Enlace inválido o incompleto.</p>
      ) : ok ? (
        <p className="text-sm text-success">Contraseña actualizada. Redirigiendo al inicio de sesión…</p>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          <div>
            <Label>Nueva contraseña (mín. 8)</Label>
            <Input type="password" minLength={8} required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
          </div>
          {error && <p className="text-sm text-danger">{error}</p>}
          <Button type="submit" disabled={loading} className="w-full">{loading ? 'Guardando…' : 'Restablecer'}</Button>
        </form>
      )}
      <p className="mt-5 text-center text-xs text-faint">
        <Link to="/login" className="text-accent hover:underline">Volver a iniciar sesión</Link>
      </p>
    </AuthShell>
  )
}
