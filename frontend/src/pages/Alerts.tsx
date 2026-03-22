import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'

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

function SeverityBadge({ severity }: { severity: string }) {
  const cls = severity === 'critical' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'
  return <span className={`text-xs px-2 py-0.5 rounded-full ${cls}`}>{severity}</span>
}

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === 'active'       ? 'bg-red-500/20 text-red-400'    :
    status === 'acknowledged' ? 'bg-blue-500/20 text-blue-400'  :
                                'bg-green-500/20 text-green-400'
  return <span className={`text-xs px-2 py-0.5 rounded-full ${cls}`}>{status}</span>
}

type StatusFilter   = 'all' | 'active' | 'acknowledged'
type SeverityFilter = 'all' | 'warning' | 'critical'

export default function Alerts() {
  const [alerts, setAlerts]     = useState<Alert[]>([])
  const [devices, setDevices]   = useState<Device[]>([])
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting')
  const [statusFilter,   setStatusFilter]   = useState<StatusFilter>('all')
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all')
  const wsRef = useRef<WebSocket | null>(null)

  // Device lookup map
  const deviceName = (id: string) => devices.find((d) => d.id === id)?.name ?? id.slice(0, 8) + '…'

  // Load devices for name lookup
  useEffect(() => {
    api.get('/devices').then((r) => setDevices(r.data)).catch(() => {})
  }, [])

  // Fetch existing alerts
  useEffect(() => {
    api.get('/alerts').then((r) => setAlerts(r.data)).catch(() => {})
  }, [])

  // WebSocket live feed
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/alerts`)
    wsRef.current = ws

    ws.onopen  = () => setWsStatus('connected')
    ws.onclose = () => setWsStatus('disconnected')
    ws.onerror = () => setWsStatus('disconnected')

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        // WebSocket payload (evaluator.py) uses different field names than REST — normalize
        const id              = msg.id              ?? msg.alert_id
        const triggered_value = msg.triggered_value ?? msg.value
        const created_at      = msg.created_at      ?? msg.recorded_at ?? new Date().toISOString()
        // Discard malformed messages missing required fields
        if (!id || triggered_value == null || isNaN(Number(triggered_value))) return
        const alert: Alert = {
          id,
          device_id:  msg.device_id,
          triggered_value: Number(triggered_value),
          severity:   msg.severity,
          status:     msg.status ?? 'active',
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

  // Client-side filtering
  const visible = alerts.filter((a) => {
    if (statusFilter   !== 'all' && a.status   !== statusFilter)   return false
    if (severityFilter !== 'all' && a.severity !== severityFilter) return false
    return true
  })

  const activeCount   = alerts.filter((a) => a.status === 'active').length
  const criticalCount = alerts.filter((a) => a.severity === 'critical' && a.status === 'active').length

  const wsColor = wsStatus === 'connected' ? 'bg-green-500' : wsStatus === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'

  function FilterBtn<T extends string>({
    value, current, onClick, children,
  }: { value: T; current: T; onClick: (v: T) => void; children: React.ReactNode }) {
    return (
      <button
        onClick={() => onClick(value)}
        className={`px-3 py-1 text-xs rounded-lg transition-colors ${
          current === value ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-400 hover:text-white'
        }`}
      >
        {children}
      </button>
    )
  }

  return (
    <div>
      {/* ── Header ── */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <h2 className="text-xl font-semibold text-white">Alerts</h2>

        {/* Live counts */}
        {activeCount > 0 && (
          <div className="flex gap-2">
            <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full">
              {activeCount} active
            </span>
            {criticalCount > 0 && (
              <span className="text-xs bg-red-600/30 text-red-300 px-2 py-0.5 rounded-full font-medium">
                {criticalCount} critical
              </span>
            )}
          </div>
        )}

        {/* WebSocket status */}
        <div className="flex items-center gap-2 ml-auto">
          <div className={`w-2 h-2 rounded-full animate-pulse ${wsColor}`} />
          <span className="text-xs text-slate-400">Live · {wsStatus}</span>
        </div>
      </div>

      {/* ── Filters ── */}
      <div className="flex flex-wrap gap-4 mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Status:</span>
          <div className="flex gap-1">
            <FilterBtn value="all"          current={statusFilter} onClick={setStatusFilter}>All</FilterBtn>
            <FilterBtn value="active"       current={statusFilter} onClick={setStatusFilter}>Active</FilterBtn>
            <FilterBtn value="acknowledged" current={statusFilter} onClick={setStatusFilter}>Acknowledged</FilterBtn>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Severity:</span>
          <div className="flex gap-1">
            <FilterBtn value="all"      current={severityFilter} onClick={setSeverityFilter}>All</FilterBtn>
            <FilterBtn value="critical" current={severityFilter} onClick={setSeverityFilter}>Critical</FilterBtn>
            <FilterBtn value="warning"  current={severityFilter} onClick={setSeverityFilter}>Warning</FilterBtn>
          </div>
        </div>
      </div>

      {/* ── Table ── */}
      {visible.length === 0 ? (
        <div className="bg-slate-800 rounded-xl p-8 text-center text-slate-400 text-sm">
          {alerts.length === 0 ? 'No alerts yet' : 'No alerts match the selected filters'}
        </div>
      ) : (
        <div className="bg-slate-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left px-4 py-3 text-slate-400 font-medium">Device</th>
                <th className="text-left px-4 py-3 text-slate-400 font-medium">Value</th>
                <th className="text-left px-4 py-3 text-slate-400 font-medium">Severity</th>
                <th className="text-left px-4 py-3 text-slate-400 font-medium">Status</th>
                <th className="text-left px-4 py-3 text-slate-400 font-medium">Time</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {visible.map((a) => (
                <tr key={a.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                  <td className="px-4 py-3 text-white font-medium">{deviceName(a.device_id)}</td>
                  <td className="px-4 py-3 text-white">
                    {a.triggered_value != null && !isNaN(Number(a.triggered_value))
                      ? Number(a.triggered_value).toFixed(2)
                      : '—'}
                  </td>
                  <td className="px-4 py-3"><SeverityBadge severity={a.severity} /></td>
                  <td className="px-4 py-3"><StatusBadge status={a.status} /></td>
                  <td className="px-4 py-3 text-slate-400 text-xs">
                    {a.created_at ? new Date(a.created_at).toLocaleString() : '—'}
                  </td>
                  <td className="px-4 py-3">
                    {a.status === 'active' && (
                      <button
                        onClick={() => acknowledge(a.id)}
                        className="text-xs bg-blue-600/30 hover:bg-blue-600/50 text-blue-400 px-2 py-1 rounded transition-colors"
                      >
                        Acknowledge
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-slate-500 px-4 py-2">
            Showing {visible.length} of {alerts.length} alerts
          </p>
        </div>
      )}
    </div>
  )
}
