import { useEffect, useState } from 'react'
import { api } from '../api/client'
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
    return <p className="text-slate-400 text-sm">Acceso restringido a administradores.</p>
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-5">
        <h2 className="text-xl font-semibold text-white">Usuarios</h2>
        <button
          onClick={() => setShowModal(true)}
          className="ml-auto bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-1.5 rounded-lg transition-colors"
        >
          Nuevo usuario
        </button>
      </div>

      <div className="bg-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Email</th>
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Nombre</th>
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Rol</th>
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Estado</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                <td className="px-4 py-3 text-white">{u.email}</td>
                <td className="px-4 py-3 text-slate-300">{u.full_name ?? '—'}</td>
                <td className="px-4 py-3">
                  <select
                    value={u.role}
                    disabled={u.id === user.id}
                    onChange={(e) => updateUser(u.id, { role: e.target.value as User['role'] })}
                    className="bg-slate-700 border border-slate-600 rounded px-2 py-1 text-xs text-white disabled:opacity-50"
                  >
                    {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                  </select>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${u.is_active ? 'bg-green-500/20 text-green-400' : 'bg-slate-600/40 text-slate-400'}`}>
                    {u.is_active ? 'activo' : 'inactivo'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  {u.id !== user.id && (
                    <button
                      onClick={() => updateUser(u.id, { is_active: !u.is_active })}
                      className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 px-2 py-1 rounded transition-colors"
                    >
                      {u.is_active ? 'Desactivar' : 'Activar'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {users.length === 0 && <p className="text-slate-500 text-sm px-4 py-6 text-center">Sin usuarios</p>}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowModal(false)}>
          <form
            onClick={(e) => e.stopPropagation()}
            onSubmit={createUser}
            className="bg-slate-800 rounded-xl p-6 w-full max-w-md space-y-4"
          >
            <h3 className="text-lg font-semibold text-white">Nuevo usuario</h3>
            {error && <p className="text-sm text-red-400">{error}</p>}
            <input
              type="email" required placeholder="Email"
              value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            />
            <input
              type="password" required minLength={8} placeholder="Contraseña (mín. 8)"
              value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            />
            <input
              type="text" placeholder="Nombre completo"
              value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            />
            <select
              value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            >
              {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
            <div className="flex gap-2 justify-end">
              <button type="button" onClick={() => setShowModal(false)} className="text-sm text-slate-400 px-4 py-2">Cancelar</button>
              <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded-lg">Crear</button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
