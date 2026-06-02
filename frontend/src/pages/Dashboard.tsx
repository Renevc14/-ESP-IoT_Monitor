import { gql } from '@apollo/client/core'
import { useQuery } from '@apollo/client/react'
import { Activity, Bell, Clock, Cpu } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { SensorChart } from '../components/SensorChart'
import { Card, CardHeader } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'
import { Select } from '../components/ui/Field'
import { PageHeader } from '../components/ui/PageHeader'
import { Segmented } from '../components/ui/Segmented'
import { StatCard } from '../components/ui/StatCard'

const DEVICE_SUMMARY = gql`
  query DeviceSummary($deviceId: String!, $hours: Int!) {
    deviceSummary(deviceId: $deviceId, hours: $hours) {
      sensorType
      readingCount
      minValue
      maxValue
      avgValue
      periodEnd
    }
  }
`

const ALERT_SUMMARY = gql`
  query AlertSummary {
    alertSummary { active critical }
  }
`

const BUCKETED_READINGS = gql`
  query BucketedReadings($deviceId: String!, $sensorType: String!, $hours: Int!, $bucketMinutes: Int!) {
    bucketedReadings(deviceId: $deviceId, sensorType: $sensorType, hours: $hours, bucketMinutes: $bucketMinutes) {
      bucket
      avgValue
    }
  }
`

function autoBucket(hours: number): number {
  if (hours <= 1) return 1
  if (hours <= 6) return 5
  if (hours <= 24) return 30
  return 60
}

interface Device {
  id: string
  name: string
  device_type: string
  is_active: boolean
}

const SENSOR_META: Record<string, { color: string; unit: string; label: string }> = {
  temperature: { color: '#f97316', unit: '°C', label: 'Temperatura' },
  humidity:    { color: '#38bdf8', unit: '%',  label: 'Humedad' },
  energy:      { color: '#34d399', unit: ' kW', label: 'Energía' },
}

const TIME_OPTIONS = [
  { label: '1h',  value: 1   },
  { label: '6h',  value: 6   },
  { label: '24h', value: 24  },
  { label: '7d',  value: 168 },
  { label: '30d', value: 720 },
]

export default function Dashboard() {
  const [devices, setDevices] = useState<Device[]>([])
  const [selectedId, setSelectedId] = useState<string>('')
  const [hours, setHours] = useState(24)

  useEffect(() => {
    api.get('/devices').then((r) => {
      const active: Device[] = r.data.filter((d: Device) => d.is_active)
      setDevices(active)
      if (active.length > 0 && !selectedId) setSelectedId(active[0].id)
    }).catch(() => {})
  }, [])

  const { data: summaryData } = useQuery(DEVICE_SUMMARY, {
    variables: { deviceId: selectedId, hours },
    skip: !selectedId,
    pollInterval: 30000,
  })
  const { data: alertData } = useQuery(ALERT_SUMMARY, { pollInterval: 30000 })

  const summaries: any[] = (summaryData as any)?.deviceSummary ?? []
  const activeSensors = summaries.map((s) => s.sensorType)
  const selectedDevice = devices.find((d) => d.id === selectedId)

  const activeAlerts = (alertData as any)?.alertSummary?.active ?? 0
  const totalReadings = summaries.reduce((acc, s) => acc + s.readingCount, 0)
  const lastReadingAt = summaries.reduce<string | null>((latest, s) => {
    if (!s.periodEnd) return latest
    return !latest || new Date(s.periodEnd) > new Date(latest) ? s.periodEnd : latest
  }, null)
  const lastReadingLabel = lastReadingAt
    ? new Date(lastReadingAt).toLocaleString([], { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
    : '—'

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Monitoreo en tiempo real de sensores IoT">
        <Select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} className="w-52">
          {devices.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </Select>
        <Segmented options={TIME_OPTIONS} value={hours} onChange={setHours} />
      </PageHeader>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Dispositivos activos" value={devices.length} icon={<Cpu size={16} />} accent="accent" />
        <StatCard label="Alertas activas" value={activeAlerts} icon={<Bell size={16} />} accent={activeAlerts > 0 ? 'danger' : 'success'} />
        <StatCard label="Última lectura" value={<span className="text-lg">{lastReadingLabel}</span>} icon={<Clock size={16} />} />
        <StatCard label={`Lecturas · ${hours}h`} value={totalReadings || '—'} icon={<Activity size={16} />} hint={selectedDevice?.name} />
      </div>

      {/* Charts */}
      {!selectedId ? (
        <EmptyState title="No hay dispositivos disponibles" />
      ) : activeSensors.length === 0 ? (
        <EmptyState
          icon={<Activity size={28} />}
          title={`Sin lecturas para ${selectedDevice?.name ?? 'el dispositivo'} en las últimas ${hours}h`}
          hint="Inicia el simulador para generar datos"
        />
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {activeSensors.map((sensor) => {
            const meta = SENSOR_META[sensor] ?? { color: '#a78bfa', unit: '', label: sensor }
            return (
              <Card key={`${selectedId}-${sensor}-${hours}`}>
                <CardHeader
                  title={
                    <span className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full" style={{ background: meta.color }} />
                      {meta.label}
                    </span>
                  }
                  subtitle={`${selectedDevice?.name} · últimas ${hours}h`}
                  action={<span className="text-[11px] text-faint">auto-refresh 30s</span>}
                />
                <div className="px-2 pb-3">
                  <LiveChart deviceId={selectedId} sensor={sensor} hours={hours} color={meta.color} unit={meta.unit} />
                </div>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}

function LiveChart({ deviceId, sensor, hours, color, unit }: { deviceId: string; sensor: string; hours: number; color: string; unit: string }) {
  const { data, loading } = useQuery(BUCKETED_READINGS, {
    variables: { deviceId, sensorType: sensor, hours, bucketMinutes: autoBucket(hours) },
    pollInterval: 30000,
  })

  const fmt = (iso: string) => {
    const d = new Date(iso)
    if (hours <= 6) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    if (hours <= 24) return d.toLocaleString([], { hour: '2-digit', minute: '2-digit' })
    return d.toLocaleString([], { month: '2-digit', day: '2-digit', hour: '2-digit' })
  }

  const chartData = ((data as any)?.bucketedReadings ?? []).map((r: any) => ({
    time: fmt(r.bucket),
    value: Number(r.avgValue),
  }))

  if (loading && chartData.length === 0) {
    return <div className="h-[200px] flex items-center justify-center text-sm text-faint">Cargando…</div>
  }
  if (chartData.length === 0) {
    return <div className="h-[200px] flex items-center justify-center text-sm text-faint">Sin lecturas</div>
  }
  return <SensorChart data={chartData} color={color} unit={unit} />
}
