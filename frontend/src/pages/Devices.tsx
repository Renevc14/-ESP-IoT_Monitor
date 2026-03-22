import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

interface Device {
  id: string
  name: string
  device_type: string
  location: string | null
  is_active: boolean
  created_at: string
}

const DEVICE_TYPES = [
  { value: 'multi_sensor', label: 'Multi Sensor' },
  { value: 'temperature_sensor', label: 'Temperature Sensor' },
  { value: 'humidity_sensor', label: 'Humidity Sensor' },
  { value: 'energy_meter', label: 'Energy Meter' },
]

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-xl p-6 w-full max-w-md shadow-xl">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-white font-semibold text-base">{title}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xl leading-none">×</button>
        </div>
        {children}
      </div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="mb-4">
      <label className="block text-xs text-slate-400 mb-1">{label}</label>
      {children}
    </div>
  )
}

const inputCls = 'w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500'

export default function Devices() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const isAdmin = user?.role === 'admin'

  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ name: '', device_type: 'multi_sensor', location: '', auth_token: '' })
  const [formError, setFormError] = useState('')

  function loadDevices() {
    return api.get('/devices')
      .then((r) => setDevices(r.data))
      .catch(() => setError('Failed to load devices'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadDevices() }, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setFormError('')
    if (form.auth_token.length < 8) { setFormError('Auth token must be at least 8 characters'); return }
    setCreating(true)
    try {
      await api.post('/devices', {
        name: form.name,
        device_type: form.device_type,
        location: form.location || null,
        auth_token: form.auth_token,
      })
      setShowCreate(false)
      setForm({ name: '', device_type: 'multi_sensor', location: '', auth_token: '' })
      setLoading(true)
      await loadDevices()
    } catch (err: any) {
      setFormError(err.response?.data?.detail ?? 'Failed to create device')
    } finally {
      setCreating(false)
    }
  }

  async function toggleActive(device: Device) {
    await api.patch(`/devices/${device.id}`, { is_active: !device.is_active })
    setDevices((prev) => prev.map((d) => d.id === device.id ? { ...d, is_active: !d.is_active } : d))
  }

  async function deleteDevice(id: string) {
    if (!confirm('Delete this device? This cannot be undone.')) return
    await api.delete(`/devices/${id}`)
    setDevices((prev) => prev.filter((d) => d.id !== id))
  }

  if (loading) return <p className="text-slate-400 text-sm">Loading…</p>
  if (error) return <p className="text-red-400 text-sm">{error}</p>

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-white">Devices</h2>
        {isAdmin && (
          <button
            onClick={() => setShowCreate(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded-lg transition-colors"
          >
            + Register Device
          </button>
        )}
      </div>

      <div className="bg-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Name</th>
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Type</th>
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Location</th>
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Status</th>
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Registered</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {devices.map((d) => (
              <tr key={d.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                <td className="px-4 py-3 text-white font-medium">{d.name}</td>
                <td className="px-4 py-3 text-slate-300">
                  <span className="bg-slate-700 px-2 py-0.5 rounded text-xs">
                    {d.device_type.replace(/_/g, ' ')}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-400">{d.location ?? '—'}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${d.is_active ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                    {d.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-400 text-xs">
                  {new Date(d.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2 justify-end">
                    <button
                      onClick={() => navigate(`/alert-rules?device_id=${d.id}`)}
                      className="text-xs text-blue-400 hover:text-blue-300 underline underline-offset-2"
                    >
                      Rules
                    </button>
                    {isAdmin && (
                      <>
                        <button
                          onClick={() => toggleActive(d)}
                          className={`text-xs px-2 py-1 rounded transition-colors ${d.is_active ? 'bg-yellow-600/30 hover:bg-yellow-600/50 text-yellow-400' : 'bg-green-600/30 hover:bg-green-600/50 text-green-400'}`}
                        >
                          {d.is_active ? 'Disable' : 'Enable'}
                        </button>
                        <button
                          onClick={() => deleteDevice(d.id)}
                          className="text-xs bg-red-600/20 hover:bg-red-600/40 text-red-400 px-2 py-1 rounded transition-colors"
                        >
                          Delete
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {devices.length === 0 && (
          <p className="text-center text-slate-400 text-sm py-8">No devices registered</p>
        )}
      </div>

      {showCreate && (
        <Modal title="Register Device" onClose={() => { setShowCreate(false); setFormError('') }}>
          <form onSubmit={handleCreate}>
            <Field label="Name *">
              <input
                className={inputCls}
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Server Room Sensor"
                required
              />
            </Field>
            <Field label="Device Type *">
              <select
                className={inputCls}
                value={form.device_type}
                onChange={(e) => setForm({ ...form, device_type: e.target.value })}
              >
                {DEVICE_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </Field>
            <Field label="Location">
              <input
                className={inputCls}
                value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
                placeholder="Data Center - Rack A1"
              />
            </Field>
            <Field label="Auth Token * (min 8 chars)">
              <input
                className={inputCls}
                value={form.auth_token}
                onChange={(e) => setForm({ ...form, auth_token: e.target.value })}
                placeholder="device-secret-token"
                minLength={8}
                required
              />
            </Field>
            {formError && <p className="text-red-400 text-xs mb-3">{formError}</p>}
            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={() => { setShowCreate(false); setFormError('') }}
                className="text-sm text-slate-400 hover:text-white px-4 py-2 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={creating}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-2 rounded-lg transition-colors"
              >
                {creating ? 'Registering…' : 'Register'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
