import { CheckCircle2, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Card } from '../components/ui/Card'
import { Loading } from '../components/ui/Loading'
import { PageHeader } from '../components/ui/PageHeader'

interface Svc { service: string; status: string }

export default function Health() {
  const [services, setServices] = useState<Svc[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    function load() {
      api.get('/system/health').then((r) => setServices(r.data)).catch(() => {}).finally(() => setLoading(false))
    }
    load()
    const id = setInterval(load, 10000)
    return () => clearInterval(id)
  }, [])

  if (loading) {
    return (
      <div>
        <PageHeader title="Salud del sistema" subtitle="Estado de los microservicios" />
        <Loading />
      </div>
    )
  }

  return (
    <div>
      <PageHeader title="Salud del sistema" subtitle="Estado de los microservicios (health checks · auto-refresh 10s)" />
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {services.map((s) => {
          const ok = s.status === 'healthy'
          return (
            <Card key={s.service} className="p-4 flex items-center gap-3">
              {ok ? <CheckCircle2 className="text-success" size={20} /> : <XCircle className="text-danger" size={20} />}
              <div>
                <p className="text-sm font-medium text-foreground capitalize">{s.service}</p>
                <p className={`text-xs ${ok ? 'text-success' : 'text-danger'}`}>{ok ? 'operativo' : 'caído'}</p>
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
