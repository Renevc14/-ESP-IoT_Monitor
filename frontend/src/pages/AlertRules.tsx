import { Plus, SlidersHorizontal } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'
import { Input, Label, Select } from '../components/ui/Field'
import { Modal } from '../components/ui/Modal'
import { PageHeader } from '../components/ui/PageHeader'
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
  { value: 'gt', label: '> (mayor que)' },
  { value: 'lt', label: '< (menor que)' },
  { value: 'gte', label: '>= (mayor o igual)' },
  { value: 'lte', label: '<= (menor o igual)' },
]
const SEVERITIES = ['warning', 'critical']
const OPERATOR_LABELS: Record<string, string> = { gt: '>', lt: '<', gte: '>=', lte: '<=' }

const TH = 'text-left px-4 py-2.5 text-[11px] font-medium uppercase tracking-wider text-faint'
const TD = 'px-4 py-3'
const ROW = 'border-t border-line/60 hover:bg-surface-2/40 transition-colors'

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
      setFormError(err.response?.data?.detail ?? 'No se pudo crear la regla')
    } finally {
      setCreating(false)
    }
  }

  async function toggleRule(rule: AlertRule) {
    await api.patch(`/alert-rules/${rule.id}`, { is_active: !rule.is_active })
    setRules((prev) => prev.map((r) => r.id === rule.id ? { ...r, is_active: !r.is_active } : r))
  }

  async function deleteRule(id: string) {
    if (!confirm('¿Eliminar esta regla de alerta?')) return
    await api.delete(`/alert-rules/${id}`)
    setRules((prev) => prev.filter((r) => r.id !== id))
  }

  if (loading) return <p className="text-sm text-faint">Cargando…</p>

  return (
    <div>
      <PageHeader title="Reglas de alerta" subtitle="Umbrales por dispositivo y tipo de sensor">
        <Select
          value={filterDeviceId}
          onChange={(e) => (e.target.value ? setSearchParams({ device_id: e.target.value }) : setSearchParams({}))}
          className="w-48"
        >
          <option value="">Todos los dispositivos</option>
          {devices.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </Select>
        {isAdmin && (
          <Button size="sm" onClick={() => { setForm({ ...form, device_id: filterDeviceId || (devices[0]?.id ?? '') }); setShowCreate(true) }}>
            <Plus size={15} /> Nueva regla
          </Button>
        )}
      </PageHeader>

      {rules.length === 0 ? (
        <EmptyState icon={<SlidersHorizontal size={28} />} title="No hay reglas configuradas" />
      ) : (
        <Card className="overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className={TH}>Dispositivo</th>
                <th className={TH}>Sensor</th>
                <th className={TH}>Condición</th>
                <th className={TH}>Severidad</th>
                <th className={TH}>Activa</th>
                {isAdmin && <th className={TH} />}
              </tr>
            </thead>
            <tbody>
              {rules.map((r) => (
                <tr key={r.id} className={ROW}>
                  <td className={`${TD} font-medium text-foreground`}>{deviceName(r.device_id)}</td>
                  <td className={TD}><Badge>{r.sensor_type}</Badge></td>
                  <td className={`${TD} font-mono text-xs text-foreground tnum`}>{OPERATOR_LABELS[r.operator]} {r.threshold}</td>
                  <td className={TD}><Badge tone={r.severity === 'critical' ? 'danger' : 'warning'}>{r.severity}</Badge></td>
                  <td className={TD}><Badge tone={r.is_active ? 'success' : 'neutral'}>{r.is_active ? 'sí' : 'no'}</Badge></td>
                  {isAdmin && (
                    <td className={TD}>
                      <div className="flex items-center gap-2 justify-end">
                        <Button variant="secondary" size="sm" onClick={() => toggleRule(r)}>{r.is_active ? 'Desactivar' : 'Activar'}</Button>
                        <Button variant="danger" size="sm" onClick={() => deleteRule(r.id)}>Eliminar</Button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {showCreate && (
        <Modal title="Nueva regla de alerta" onClose={() => { setShowCreate(false); setFormError('') }}>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <Label>Dispositivo</Label>
              <Select value={form.device_id} onChange={(e) => setForm({ ...form, device_id: e.target.value })} required>
                {devices.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Sensor</Label>
                <Select value={form.sensor_type} onChange={(e) => setForm({ ...form, sensor_type: e.target.value })}>
                  {SENSOR_TYPES.map((s) => <option key={s} value={s}>{s}</option>)}
                </Select>
              </div>
              <div>
                <Label>Severidad</Label>
                <Select value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })}>
                  {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Operador</Label>
                <Select value={form.operator} onChange={(e) => setForm({ ...form, operator: e.target.value })}>
                  {OPERATORS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </Select>
              </div>
              <div>
                <Label>Umbral</Label>
                <Input type="number" step="0.1" value={form.threshold} onChange={(e) => setForm({ ...form, threshold: e.target.value })} required />
              </div>
            </div>
            {formError && <p className="text-sm text-danger">{formError}</p>}
            <div className="flex gap-2 justify-end pt-1">
              <Button type="button" variant="ghost" onClick={() => { setShowCreate(false); setFormError('') }}>Cancelar</Button>
              <Button type="submit" disabled={creating}>{creating ? 'Creando…' : 'Crear regla'}</Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
