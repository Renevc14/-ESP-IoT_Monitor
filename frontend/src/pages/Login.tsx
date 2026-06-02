import { Activity } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Input, Label } from '../components/ui/Field'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/')
    } catch {
      setError('Credenciales inválidas')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-background px-4 overflow-hidden">
      {/* glow de acento */}
      <div
        className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 h-[420px] w-[620px] rounded-full opacity-25 blur-[120px]"
        style={{ background: 'radial-gradient(closest-side, #22d3ee, transparent)' }}
      />

      <div className="relative w-full max-w-sm">
        <div className="flex flex-col items-center mb-7">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent/15 text-accent mb-3 ring-1 ring-accent/20">
            <Activity size={22} />
          </div>
          <h1 className="text-lg font-semibold text-foreground">IoT Monitor</h1>
          <p className="text-sm text-muted mt-1">Inicia sesión para continuar</p>
        </div>

        <div className="rounded-2xl border border-line bg-surface p-7 shadow-2xl shadow-black/40">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label>Email</Label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@iot.local"
                autoComplete="username"
                required
              />
            </div>
            <div>
              <Label>Contraseña</Label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                required
              />
            </div>

            {error && (
              <div className="rounded-lg border border-danger/25 bg-danger/10 px-3 py-2 text-sm text-danger">
                {error}
              </div>
            )}

            <Button type="submit" disabled={loading} className="w-full">
              {loading ? 'Ingresando…' : 'Ingresar'}
            </Button>
          </form>
        </div>

        <p className="mt-5 text-center text-xs text-faint">
          Demo: <span className="text-muted">admin@iot.local</span> · <span className="text-muted">Admin1234!</span>
        </p>
      </div>
    </div>
  )
}
