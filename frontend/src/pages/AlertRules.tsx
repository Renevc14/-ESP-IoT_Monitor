import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

interface Device { id: string; name: string }

interface AlertRule {
  id: string
  device_id: string
  sensor_type: string
  operator: string
  threshold: number
  severity: 'warning' | 'critical'
  is_active: boolean
  created_at: string
}

const SENSOR_TYPES = ['temperature', 'humidity', 'energy']
const OPERATORS = [
  { value: 'gt', label: '> (greater than)' },
  { value: 'lt', label: '< (less than)' },
  { value: 'gte', label: '>= (greater or equal)' },
  { value: 'lte', label: '<= (less or equal)' },
]
const SEVERITIES = ['warning', 'critical']

const OPERATOR_LABELS: Record<string, string> = { gt: '>', lt: '<', gte: '>=', lte: '<=' }

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

export default function AlertRules() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const [searchParams, setSearchParams] = useSearchParams()
  const filterDeviceId = searchParams.get('device_id') ?? ''

  const [devices, setDevices] = useState<Device[]>([])
  const [rules, setRules] = useState<AlertRule[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [creating, setCreating] = useState(false)
  const [formError, setFormError] = useState('')
  const [form, setForm] = useState({
    device_id: filterDeviceId,
    sensor_type: 'temperature',
    operator: 'gt',
    threshold: '40',
    severity: 'critical',
  })

  function deviceName(id: string) {
    return devices.find((d) => d.id === id)?.name ?? id.slice(0, 8) + '…'
  }

  async function loadData() {
    const [devRes, rulesRes] = await Promise.all([
      api.get('/devices'),
      api.get('/alert-rules' + (filterDeviceId ? `?device_id=${filterDeviceId}` : '')),
    ])
    setDevices(devRes.data)
    setRules(rulesRes.data)
    setLoading(false)
  }

  useEffect(() => { loadData() }, [filterDeviceId])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setFormError('')
    setCreating(true)
    try {
      await api.post('/alert-rules', {
        device_id: form.device_id,
        sensor_type: form.sensor_type,
        operator: form.operator,
        threshold: parseFloat(form.threshold),
        severity: form.severity,
        is_active: true,
      })
      setShowCreate(false)
      setLoading(true)
      await loadData()
    } catch (err: any) {
      setFormError(err.response?.data?.detail ?? 'Failed to create rule')
    } finally {
      setCreating(false)
    }
  }

  async function toggleRule(rule: AlertRule) {
    await api.patch(`/alert-rules/${rule.id}`, { is_active: !rule.is_active })
    setRules((prev) => prev.map((r) => r.id === rule.id ? { ...r, is_active: !r.is_active } : r))
  }

  async function deleteRule(id: string) {
    if (!confirm('Delete this alert rule?')) return
    await api.delete(`/alert-rules/${id}`)
    setRules((prev) => prev.filter((r) => r.id !== id))
  }

  if (loading) return <p className="text-slate-400 text-sm">Loading…</p>

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-white">Alert Rules</h2>
        {isAdmin && (
          <button
            onClick={() => { setForm({ ...form, device_id: filterDeviceId || (devices[0]?.id ?? '') }); setShowCreate(true) }}
            className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded-lg transition-colors"
          >
            + Add Rule
          </button>
        )}
      </div>

      {/* Filter by device */}
      <div className="mb-4 flex items-center gap-3">
        <label className="text-slate-400 text-sm">Filter by device:</label>
        <select
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
          value={filterDeviceId}
          onChange={(e) => {
            if (e.target.value) setSearchParams({ device_id: e.target.value })
            else setSearchParams({})
          }}
        >
          <option value="">All devices</option>
          {devices.map((d) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
        {filterDeviceId && (
          <button
            onClick={() => setSearchParams({})}
            className="text-xs text-slate-400 hover:text-white underline underline-offset-2"
          >
            Clear filter
          </button>
        )}
      </div>

      <div className="bg-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Device</th>
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Sensor</th>
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Condition</th>
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Severity</th>
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Active</th>
              {isAdmin && <th className="px-4 py-3" />}
            </tr>
          </thead>
          <tbody>
            {rules.map((r) => (
              <tr key={r.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                <td className="px-4 py-3 text-white font-medium">{deviceName(r.device_id)}</td>
                <td className="px-4 py-3 text-slate-300">
                  <span className="bg-slate-700 px-2 py-0.5 rounded text-xs">{r.sensor_type}</span>
                </td>
                <td className="px-4 py-3 text-slate-100 font-mono text-xs">
                  {OPERATOR_LABELS[r.operator]} {r.threshold}
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${r.severity === 'critical' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                    {r.severity}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${r.is_active ? 'bg-green-500/20 text-green-400' : 'bg-slate-600 text-slate-400'}`}>
                    {r.is_active ? 'yes' : 'no'}
                  </span>
                </td>
                {isAdmin && (
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2 justify-end">
                      <button
                        onClick={() => toggleRule(r)}
                        className={`text-xs px-2 py-1 rounded transition-colors ${r.is_active ? 'bg-yellow-600/30 hover:bg-yellow-600/50 text-yellow-400' : 'bg-green-600/30 hover:bg-green-600/50 text-green-400'}`}
                      >
                        {r.is_active ? 'Disable' : 'Enable'}
                      </button>
                      <button
                        onClick={() => deleteRule(r.id)}
                        className="text-xs bg-red-600/20 hover:bg-red-600/40 text-red-400 px-2 py-1 rounded transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>

        {rules.length === 0 && (
          <p className="text-center text-slate-400 text-sm py-8">No alert rules configured</p>
        )}
      </div>

      {showCreate && (
        <Modal title="Add Alert Rule" onClose={() => { setShowCreate(false); setFormError('') }}>
          <form onSubmit={handleCreate}>
            <Field label="Device *">
              <select
                className={inputCls}
                value={form.device_id}
                onChange={(e) => setForm({ ...form, device_id: e.target.value })}
                required
              >
                {devices.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </Field>
            <Field label="Sensor Type *">
              <select
                className={inputCls}
                value={form.sensor_type}
                onChange={(e) => setForm({ ...form, sensor_type: e.target.value })}
              >
                {SENSOR_TYPES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </Field>
            <Field label="Operator *">
              <select
                className={inputCls}
                value={form.operator}
                onChange={(e) => setForm({ ...form, operator: e.target.value })}
              >
                {OPERATORS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </Field>
            <Field label="Threshold *">
              <input
                type="number"
                step="0.1"
                className={inputCls}
                value={form.threshold}
                onChange={(e) => setForm({ ...form, threshold: e.target.value })}
                required
              />
            </Field>
            <Field label="Severity *">
              <select
                className={inputCls}
                value={form.severity}
                onChange={(e) => setForm({ ...form, severity: e.target.value })}
              >
                {SEVERITIES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
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
                {creating ? 'Creating…' : 'Create Rule'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
