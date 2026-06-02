import { ScrollText } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'
import { Loading } from '../components/ui/Loading'
import { PageHeader } from '../components/ui/PageHeader'
import { useAuth } from '../context/AuthContext'

interface Log {
  id: number
  user_id: string | null
  action: string
  resource: string | null
  ip_address: string | null
  created_at: string
}

const TH = 'text-left px-4 py-2.5 text-[11px] font-medium uppercase tracking-wider text-faint'
const TD = 'px-4 py-3'
const ROW = 'border-t border-line/60 hover:bg-surface-2/40 transition-colors'

function tone(action: string): 'danger' | 'info' | 'neutral' {
  if (action.includes('failed') || action.includes('denied')) return 'danger'
  if (action.includes('login') || action.includes('reset')) return 'info'
  return 'neutral'
}

export default function Logs() {
  const { user } = useAuth()
  const [logs, setLogs] = useState<Log[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/audit-logs?limit=200').then((r) => setLogs(r.data)).catch(() => {}).finally(() => setLoading(false))
  }, [])

  if (user?.role !== 'admin') {
    return <EmptyState icon={<ScrollText size={28} />} title="Acceso restringido a administradores" />
  }
  if (loading) {
    return (
      <div>
        <PageHeader title="Logs de auditoría" subtitle="Eventos de seguridad del sistema" />
        <Loading />
      </div>
    )
  }

  return (
    <div>
      <PageHeader title="Logs de auditoría" subtitle="Eventos de seguridad — OWASP A09" />
      {logs.length === 0 ? (
        <EmptyState icon={<ScrollText size={28} />} title="Sin eventos registrados" />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead>
              <tr>
                <th className={TH}>Acción</th>
                <th className={TH}>Recurso</th>
                <th className={TH}>IP</th>
                <th className={TH}>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id} className={ROW}>
                  <td className={TD}><Badge tone={tone(l.action)}>{l.action}</Badge></td>
                  <td className={`${TD} text-muted`}>{l.resource ?? '—'}</td>
                  <td className={`${TD} text-faint tnum`}>{l.ip_address ?? '—'}</td>
                  <td className={`${TD} text-faint text-xs tnum`}>{new Date(l.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}
