import { Plus, Users as UsersIcon } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'
import { Input, Label, Select } from '../components/ui/Field'
import { Modal } from '../components/ui/Modal'
import { PageHeader } from '../components/ui/PageHeader'
import { useAuth } from '../context/AuthContext'

interface User {
  id: string
  email: string
  role: 'admin' | 'operator' | 'viewer'
  full_name: string | null
  is_active: boolean
  created_at: string
}

const ROLES = ['admin', 'operator', 'viewer'] as const
const ROLE_TONE: Record<User['role'], 'accent' | 'info' | 'neutral'> = { admin: 'accent', operator: 'info', viewer: 'neutral' }

const TH = 'text-left px-4 py-2.5 text-[11px] font-medium uppercase tracking-wider text-faint'
const TD = 'px-4 py-3'
const ROW = 'border-t border-line/60 hover:bg-surface-2/40 transition-colors'

export default function Users() {
  const { user } = useAuth()
  const [users, setUsers] = useState<User[]>([])
  const [showModal, setShowModal] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({ email: '', password: '', full_name: '', role: 'viewer' })

  function load() {
    api.get('/users').then((r) => setUsers(r.data)).catch(() => {})
  }
  useEffect(load, [])

  async function createUser(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    try {
      await api.post('/users', form)
      setShowModal(false)
      setForm({ email: '', password: '', full_name: '', role: 'viewer' })
      load()
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'No se pudo crear el usuario')
    }
  }

  async function updateUser(id: string, patch: Partial<Pick<User, 'role' | 'is_active'>>) {
    try {
      await api.patch(`/users/${id}`, patch)
      setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, ...patch } : u)))
    } catch {}
  }

  if (user?.role !== 'admin') {
    return <EmptyState icon={<UsersIcon size={28} />} title="Acceso restringido a administradores" />
  }

  return (
    <div>
      <PageHeader title="Usuarios" subtitle="Gestión de cuentas y roles (RBAC)">
        <Button size="sm" onClick={() => setShowModal(true)}><Plus size={15} /> Nuevo usuario</Button>
      </PageHeader>

      {users.length === 0 ? (
        <EmptyState icon={<UsersIcon size={28} />} title="Sin usuarios" />
      ) : (
        <Card className="overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className={TH}>Email</th>
                <th className={TH}>Nombre</th>
                <th className={TH}>Rol</th>
                <th className={TH}>Estado</th>
                <th className={TH} />
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className={ROW}>
                  <td className={`${TD} font-medium text-foreground`}>{u.email}</td>
                  <td className={`${TD} text-muted`}>{u.full_name ?? '—'}</td>
                  <td className={TD}>
                    {u.id === user.id ? (
                      <Badge tone={ROLE_TONE[u.role]}>{u.role}</Badge>
                    ) : (
                      <Select
                        value={u.role}
                        onChange={(e) => updateUser(u.id, { role: e.target.value as User['role'] })}
                        className="h-8 w-32"
                      >
                        {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                      </Select>
                    )}
                  </td>
                  <td className={TD}><Badge tone={u.is_active ? 'success' : 'neutral'}>{u.is_active ? 'activo' : 'inactivo'}</Badge></td>
                  <td className={TD}>
                    <div className="flex justify-end">
                      {u.id !== user.id && (
                        <Button variant="secondary" size="sm" onClick={() => updateUser(u.id, { is_active: !u.is_active })}>
                          {u.is_active ? 'Desactivar' : 'Activar'}
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {showModal && (
        <Modal title="Nuevo usuario" onClose={() => setShowModal(false)}>
          <form onSubmit={createUser} className="space-y-4">
            {error && <p className="text-sm text-danger">{error}</p>}
            <div>
              <Label>Email</Label>
              <Input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="usuario@iot.local" />
            </div>
            <div>
              <Label>Contraseña (mín. 8)</Label>
              <Input type="password" required minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="••••••••" />
            </div>
            <div>
              <Label>Nombre completo</Label>
              <Input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} placeholder="Nombre Apellido" />
            </div>
            <div>
              <Label>Rol</Label>
              <Select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
              </Select>
            </div>
            <div className="flex gap-2 justify-end pt-1">
              <Button type="button" variant="ghost" onClick={() => setShowModal(false)}>Cancelar</Button>
              <Button type="submit">Crear</Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
