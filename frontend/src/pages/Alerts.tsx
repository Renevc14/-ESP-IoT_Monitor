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

function SeverityBadge({ severity }: { severity: string }) {
  const cls =
    severity === 'critical'
      ? 'bg-red-500/20 text-red-400'
      : 'bg-yellow-500/20 text-yellow-400'
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${cls}`}>
      {severity}
    </span>
  )
}

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === 'active'
      ? 'bg-red-500/20 text-red-400'
      : status === 'acknowledged'
      ? 'bg-blue-500/20 text-blue-400'
      : 'bg-green-500/20 text-green-400'
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${cls}`}>
      {status}
    </span>
  )
}

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting')
  const wsRef = useRef<WebSocket | null>(null)

  // Fetch existing alerts
  useEffect(() => {
    api.get('/alerts').then((r) => setAlerts(r.data)).catch(() => {})
  }, [])

  // WebSocket for live updates
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/alerts`)
    wsRef.current = ws

    ws.onopen = () => setWsStatus('connected')
    ws.onclose = () => setWsStatus('disconnected')
    ws.onerror = () => setWsStatus('disconnected')

    ws.onmessage = (event) => {
      try {
        const alert: Alert = JSON.parse(event.data)
        setAlerts((prev) => {
          const exists = prev.some((a) => a.id === alert.id)
          return exists ? prev : [alert, ...prev]
        })
      } catch {}
    }

    return () => ws.close()
  }, [])

  async function acknowledge(id: string) {
    try {
      await api.patch(`/alerts/${id}/acknowledge`)
      setAlerts((prev) =>
        prev.map((a) => (a.id === id ? { ...a, status: 'acknowledged' } : a)),
      )
    } catch {}
  }

  const wsColor =
    wsStatus === 'connected'
      ? 'bg-green-500'
      : wsStatus === 'connecting'
      ? 'bg-yellow-500'
      : 'bg-red-500'

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-white">Alerts</h2>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${wsColor}`} />
          <span className="text-xs text-slate-400">Live feed {wsStatus}</span>
        </div>
      </div>

      {alerts.length === 0 ? (
        <div className="bg-slate-800 rounded-xl p-8 text-center text-slate-400 text-sm">
          No alerts yet
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
              {alerts.map((a) => (
                <tr key={a.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                  <td className="px-4 py-3 text-slate-300 font-mono text-xs">
                    …{a.device_id.slice(-8)}
                  </td>
                  <td className="px-4 py-3 text-white">{Number(a.triggered_value).toFixed(2)}</td>
                  <td className="px-4 py-3">
                    <SeverityBadge severity={a.severity} />
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={a.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-xs">
                    {new Date(a.created_at).toLocaleString()}
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
        </div>
      )}
    </div>
  )
}
