import { Bell, Check, CheckCheck } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { cn } from '../components/ui/cn'
import { EmptyState } from '../components/ui/EmptyState'
import { Input } from '../components/ui/Field'
import { PageHeader } from '../components/ui/PageHeader'

const WS_URL = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8003'

interface Alert {
  id: string
  device_id: string
  triggered_value: number
  severity: 'warning' | 'critical'
  status: 'active' | 'acknowledged' | 'resolved'
  created_at: string
}

interface Device { id: string; name: string }

type StatusFilter = 'all' | 'active' | 'acknowledged' | 'resolved'
type SeverityFilter = 'all' | 'warning' | 'critical'

const TH = 'text-left px-4 py-2.5 text-[11px] font-medium uppercase tracking-wider text-faint'
const TD = 'px-4 py-3'
const ROW = 'border-t border-line/60 hover:bg-surface-2/40 transition-colors'

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [devices, setDevices] = useState<Device[]>([])
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const wsRef = useRef<WebSocket | null>(null)

  const deviceName = (id: string) => devices.find((d) => d.id === id)?.name ?? id.slice(0, 8) + '…'

  useEffect(() => { api.get('/devices').then((r) => setDevices(r.data)).catch(() => {}) }, [])
  useEffect(() => { api.get('/alerts').then((r) => setAlerts(r.data)).catch(() => {}) }, [])

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/alerts`)
    wsRef.current = ws
    ws.onopen = () => setWsStatus('connected')
    ws.onclose = () => setWsStatus('disconnected')
    ws.onerror = () => setWsStatus('disconnected')
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        const id = msg.id ?? msg.alert_id
        const triggered_value = msg.triggered_value ?? msg.value
        const created_at = msg.created_at ?? msg.recorded_at ?? new Date().toISOString()
        if (!id || triggered_value == null || isNaN(Number(triggered_value))) return
        const alert: Alert = {
          id,
          device_id: msg.device_id,
          triggered_value: Number(triggered_value),
          severity: msg.severity,
          status: msg.status ?? 'active',
          created_at,
        }
        setAlerts((prev) => prev.some((a) => a.id === alert.id) ? prev : [alert, ...prev])
      } catch {}
    }
    return () => ws.close()
  }, [])

  async function acknowledge(id: string) {
    try {
      await api.patch(`/alerts/${id}/acknowledge`)
      setAlerts((prev) => prev.map((a) => a.id === id ? { ...a, status: 'acknowledged' } : a))
    } catch {}
  }

  async function resolve(id: string) {
    try {
      await api.patch(`/alerts/${id}/resolve`)
      setAlerts((prev) => prev.map((a) => a.id === id ? { ...a, status: 'resolved' } : a))
    } catch {}
  }

  const fromTs = fromDate ? new Date(fromDate).getTime() : null
  const toTs = toDate ? new Date(toDate).getTime() + 86_400_000 : null
  const visible = alerts.filter((a) => {
    if (statusFilter !== 'all' && a.status !== statusFilter) return false
    if (severityFilter !== 'all' && a.severity !== severityFilter) return false
    if (a.created_at) {
      const ts = new Date(a.created_at).getTime()
      if (fromTs && ts < fromTs) return false
      if (toTs && ts > toTs) return false
    }
    return true
  })

  const activeCount = alerts.filter((a) => a.status === 'active').length
  const criticalCount = alerts.filter((a) => a.severity === 'critical' && a.status === 'active').length
  const wsColor = wsStatus === 'connected' ? 'bg-success' : wsStatus === 'connecting' ? 'bg-warning' : 'bg-danger'

  function FilterBtn<T extends string>({ value, current, onClick, children }: { value: T; current: T; onClick: (v: T) => void; children: React.ReactNode }) {
    return (
      <button
        onClick={() => onClick(value)}
        className={cn(
          'px-2.5 py-1 text-xs font-medium rounded-md transition-colors',
          current === value ? 'bg-surface-2 text-foreground' : 'text-muted hover:text-foreground',
        )}
      >
        {children}
      </button>
    )
  }

  return (
    <div>
      <PageHeader title="Alertas" subtitle="Monitor de alertas en tiempo real">
        <div className="flex items-center gap-2 rounded-lg border border-line bg-surface px-3 py-1.5">
          <span className={cn('h-2 w-2 rounded-full animate-pulse', wsColor)} />
          <span className="text-xs text-muted capitalize">{wsStatus}</span>
        </div>
      </PageHeader>

      {/* Resumen */}
      <div className="flex items-center gap-2 mb-4">
        <Badge tone={activeCount > 0 ? 'danger' : 'neutral'}>{activeCount} activas</Badge>
        {criticalCount > 0 && <Badge tone="danger">{criticalCount} críticas</Badge>}
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap items-center gap-x-5 gap-y-3 mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-faint">Estado</span>
          <div className="flex gap-0.5 rounded-lg border border-line bg-surface p-0.5">
            <FilterBtn value="all" current={statusFilter} onClick={setStatusFilter}>Todas</FilterBtn>
            <FilterBtn value="active" current={statusFilter} onClick={setStatusFilter}>Activas</FilterBtn>
            <FilterBtn value="acknowledged" current={statusFilter} onClick={setStatusFilter}>Reconocidas</FilterBtn>
            <FilterBtn value="resolved" current={statusFilter} onClick={setStatusFilter}>Resueltas</FilterBtn>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-faint">Severidad</span>
          <div className="flex gap-0.5 rounded-lg border border-line bg-surface p-0.5">
            <FilterBtn value="all" current={severityFilter} onClick={setSeverityFilter}>Todas</FilterBtn>
            <FilterBtn value="critical" current={severityFilter} onClick={setSeverityFilter}>Críticas</FilterBtn>
            <FilterBtn value="warning" current={severityFilter} onClick={setSeverityFilter}>Advertencia</FilterBtn>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-faint">Desde</span>
          <Input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} className="h-8 w-auto" />
          <span className="text-xs text-faint">Hasta</span>
          <Input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} className="h-8 w-auto" />
          {(fromDate || toDate) && (
            <button onClick={() => { setFromDate(''); setToDate('') }} className="text-xs text-faint hover:text-foreground">limpiar</button>
          )}
        </div>
      </div>

      {visible.length === 0 ? (
        <EmptyState icon={<Bell size={28} />} title={alerts.length === 0 ? 'No hay alertas todavía' : 'Ninguna alerta coincide con los filtros'} />
      ) : (
        <Card className="overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className={TH}>Dispositivo</th>
                <th className={TH}>Valor</th>
                <th className={TH}>Severidad</th>
                <th className={TH}>Estado</th>
                <th className={TH}>Hora</th>
                <th className={TH} />
              </tr>
            </thead>
            <tbody>
              {visible.map((a) => (
                <tr key={a.id} className={ROW}>
                  <td className={`${TD} font-medium text-foreground`}>{deviceName(a.device_id)}</td>
                  <td className={`${TD} tnum text-foreground`}>
                    {a.triggered_value != null && !isNaN(Number(a.triggered_value)) ? Number(a.triggered_value).toFixed(2) : '—'}
                  </td>
                  <td className={TD}><Badge tone={a.severity === 'critical' ? 'danger' : 'warning'}>{a.severity}</Badge></td>
                  <td className={TD}>
                    <Badge tone={a.status === 'active' ? 'danger' : a.status === 'acknowledged' ? 'info' : 'success'}>{a.status}</Badge>
                  </td>
                  <td className={`${TD} text-faint text-xs tnum`}>{a.created_at ? new Date(a.created_at).toLocaleString() : '—'}</td>
                  <td className={TD}>
                    <div className="flex gap-2 justify-end">
                      {a.status === 'active' && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => acknowledge(a.id)}
                          title="Reconocer: marcar la alerta como vista / en atención"
                        >
                          <Check size={14} /> Reconocer
                        </Button>
                      )}
                      {a.status !== 'resolved' && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => resolve(a.id)}
                          title="Resolver: marcar la alerta como solucionada"
                          className="text-success"
                        >
                          <CheckCheck size={14} /> Resolver
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-faint px-4 py-2.5 border-t border-line/60">Mostrando {visible.length} de {alerts.length} alertas</p>
        </Card>
      )}
    </div>
  )
}
