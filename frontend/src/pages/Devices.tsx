import { Cpu, Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'
import { Input, Label, Select } from '../components/ui/Field'
import { Modal } from '../components/ui/Modal'
import { PageHeader } from '../components/ui/PageHeader'
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

const TH = 'text-left px-4 py-2.5 text-[11px] font-medium uppercase tracking-wider text-faint'
const TD = 'px-4 py-3'
const ROW = 'border-t border-line/60 hover:bg-surface-2/40 transition-colors'

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
      .catch(() => setError('No se pudieron cargar los dispositivos'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadDevices() }, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setFormError('')
    if (form.auth_token.length < 8) { setFormError('El token debe tener al menos 8 caracteres'); return }
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
      setFormError(err.response?.data?.detail ?? 'No se pudo crear el dispositivo')
    } finally {
      setCreating(false)
    }
  }

  async function toggleActive(device: Device) {
    await api.patch(`/devices/${device.id}`, { is_active: !device.is_active })
    setDevices((prev) => prev.map((d) => d.id === device.id ? { ...d, is_active: !d.is_active } : d))
  }

  async function deleteDevice(id: string) {
    if (!confirm('¿Eliminar este dispositivo? Esta acción no se puede deshacer.')) return
    await api.delete(`/devices/${id}`)
    setDevices((prev) => prev.filter((d) => d.id !== id))
  }

  if (loading) return <p className="text-sm text-faint">Cargando…</p>
  if (error) return <p className="text-sm text-danger">{error}</p>

  return (
    <div>
      <PageHeader title="Dispositivos" subtitle="Inventario de sensores IoT registrados">
        {isAdmin && (
          <Button onClick={() => setShowCreate(true)} size="sm">
            <Plus size={15} /> Registrar dispositivo
          </Button>
        )}
      </PageHeader>

      {devices.length === 0 ? (
        <EmptyState icon={<Cpu size={28} />} title="No hay dispositivos registrados" />
      ) : (
        <Card className="overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className={TH}>Nombre</th>
                <th className={TH}>Tipo</th>
                <th className={TH}>Ubicación</th>
                <th className={TH}>Estado</th>
                <th className={TH}>Registrado</th>
                <th className={TH} />
              </tr>
            </thead>
            <tbody>
              {devices.map((d) => (
                <tr key={d.id} className={ROW}>
                  <td className={`${TD} font-medium text-foreground`}>{d.name}</td>
                  <td className={TD}><Badge>{d.device_type.replace(/_/g, ' ')}</Badge></td>
                  <td className={`${TD} text-muted`}>{d.location ?? '—'}</td>
                  <td className={TD}><Badge tone={d.is_active ? 'success' : 'neutral'}>{d.is_active ? 'activo' : 'inactivo'}</Badge></td>
                  <td className={`${TD} text-faint text-xs tnum`}>{new Date(d.created_at).toLocaleDateString()}</td>
                  <td className={TD}>
                    <div className="flex items-center gap-2 justify-end">
                      <button onClick={() => navigate(`/alert-rules?device_id=${d.id}`)} className="text-xs text-accent hover:underline underline-offset-2">
                        Reglas
                      </button>
                      {isAdmin && (
                        <>
                          <Button variant="secondary" size="sm" onClick={() => toggleActive(d)}>
                            {d.is_active ? 'Desactivar' : 'Activar'}
                          </Button>
                          <Button variant="danger" size="sm" onClick={() => deleteDevice(d.id)}>Eliminar</Button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {showCreate && (
        <Modal title="Registrar dispositivo" onClose={() => { setShowCreate(false); setFormError('') }}>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <Label>Nombre</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Server Room Sensor" required />
            </div>
            <div>
              <Label>Tipo de dispositivo</Label>
              <Select value={form.device_type} onChange={(e) => setForm({ ...form, device_type: e.target.value })}>
                {DEVICE_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </Select>
            </div>
            <div>
              <Label>Ubicación</Label>
              <Input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} placeholder="Data Center - Rack A1" />
            </div>
            <div>
              <Label>Token de autenticación (mín. 8)</Label>
              <Input value={form.auth_token} onChange={(e) => setForm({ ...form, auth_token: e.target.value })} placeholder="device-secret-token" minLength={8} required />
            </div>
            {formError && <p className="text-sm text-danger">{formError}</p>}
            <div className="flex gap-2 justify-end pt-1">
              <Button type="button" variant="ghost" onClick={() => { setShowCreate(false); setFormError('') }}>Cancelar</Button>
              <Button type="submit" disabled={creating}>{creating ? 'Registrando…' : 'Registrar'}</Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
