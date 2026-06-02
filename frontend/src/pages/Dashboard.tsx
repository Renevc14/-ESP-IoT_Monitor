import { gql } from '@apollo/client/core'
import { useQuery } from '@apollo/client/react'
import { Activity, AlertTriangle, Bell, Cpu, Radio } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import { onConnectionChange, subscribeReadings } from '../api/realtime'
import { SensorChart } from '../components/SensorChart'
import { Badge } from '../components/ui/Badge'
import { Card, CardHeader } from '../components/ui/Card'
import { cn } from '../components/ui/cn'
import { EmptyState } from '../components/ui/EmptyState'
import { PageHeader } from '../components/ui/PageHeader'
import { Segmented } from '../components/ui/Segmented'
import { SelectMenu } from '../components/ui/SelectMenu'
import { StatCard } from '../components/ui/StatCard'
import { STATUS_LABEL, STATUS_TEXT, STATUS_TONE, THRESHOLDS, statusFor } from '../lib/thresholds'

const DEVICE_SUMMARY = gql`
  query DeviceSummary($deviceId: String!, $hours: Int!) {
    deviceSummary(deviceId: $deviceId, hours: $hours) {
      sensorType readingCount periodEnd
    }
  }
`
const ALERT_SUMMARY = gql`query AlertSummary { alertSummary { active critical } }`
const BUCKETED = gql`
  query Bucketed($deviceId: String!, $sensorType: String!, $hours: Int!, $bucketMinutes: Int!) {
    bucketedReadings(deviceId: $deviceId, sensorType: $sensorType, hours: $hours, bucketMinutes: $bucketMinutes) {
      bucket avgValue
    }
  }
`

function autoBucket(hours: number): number {
  if (hours <= 1) return 1
  if (hours <= 6) return 5
  if (hours <= 24) return 30
  return 60
}

interface Device { id: string; name: string; device_type: string; is_active: boolean }

const SENSOR_META: Record<string, { color: string; unit: string; label: string }> = {
  temperature: { color: '#fb923c', unit: '°C', label: 'Temperatura' },
  humidity:    { color: '#22d3ee', unit: '%',  label: 'Humedad' },
  energy:      { color: '#34d399', unit: ' kW', label: 'Energía' },
}

const TIME_OPTIONS = [
  { label: '1h', value: 1 }, { label: '6h', value: 6 }, { label: '24h', value: 24 },
  { label: '7d', value: 168 }, { label: '30d', value: 720 },
]

function fmtTime(iso: string, hours: number) {
  const d = new Date(iso)
  if (hours <= 6) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  if (hours <= 24) return d.toLocaleString([], { hour: '2-digit', minute: '2-digit' })
  return d.toLocaleString([], { month: '2-digit', day: '2-digit', hour: '2-digit' })
}

export default function Dashboard() {
  const [devices, setDevices] = useState<Device[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [hours, setHours] = useState(24)
  const [activeByDevice, setActiveByDevice] = useState<Record<string, number>>({})
  const [live, setLive] = useState(false)

  useEffect(() => onConnectionChange(setLive), [])

  useEffect(() => {
    api.get('/devices').then((r) => {
      const active: Device[] = r.data.filter((d: Device) => d.is_active)
      setDevices(active)
      if (active.length && !selectedId) setSelectedId(active[0].id)
    }).catch(() => {})
  }, [])

  useEffect(() => {
    function load() {
      api.get('/alerts').then((r) => {
        const map: Record<string, number> = {}
        r.data.filter((a: any) => a.status === 'active').forEach((a: any) => { map[a.device_id] = (map[a.device_id] ?? 0) + 1 })
        setActiveByDevice(map)
      }).catch(() => {})
    }
    load()
    const id = setInterval(load, 30000)
    return () => clearInterval(id)
  }, [])

  const { data: summaryData } = useQuery(DEVICE_SUMMARY, { variables: { deviceId: selectedId, hours }, skip: !selectedId, pollInterval: 30000 })
  const { data: alertData } = useQuery(ALERT_SUMMARY, { pollInterval: 30000 })
  const { data: sparkData } = useQuery(BUCKETED, { variables: { deviceId: selectedId, sensorType: 'temperature', hours, bucketMinutes: autoBucket(hours) }, skip: !selectedId, pollInterval: 30000 })

  const summaries: any[] = (summaryData as any)?.deviceSummary ?? []
  const activeSensors = summaries.map((s) => s.sensorType)
  const selectedDevice = devices.find((d) => d.id === selectedId)

  const activeAlerts = (alertData as any)?.alertSummary?.active ?? 0
  const criticalAlerts = (alertData as any)?.alertSummary?.critical ?? 0
  const totalReadings = summaries.reduce((acc, s) => acc + s.readingCount, 0)
  const spark = ((sparkData as any)?.bucketedReadings ?? []).map((b: any) => Number(b.avgValue))

  return (
    <div className="space-y-6">
      <PageHeader title="Dashboard" subtitle="Monitoreo en tiempo real de sensores IoT">
        <span className="flex items-center gap-1.5 rounded-lg border border-line bg-surface px-2.5 py-1.5 text-xs text-muted">
          <Radio size={13} className={live ? 'text-success' : 'text-faint'} />
          {live ? 'En vivo' : 'Sin conexión'}
        </span>
        <SelectMenu value={selectedId} onChange={setSelectedId} options={devices.map((d) => ({ value: d.id, label: d.name }))} className="w-52" />
        <Segmented options={TIME_OPTIONS} value={hours} onChange={setHours} />
      </PageHeader>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Dispositivos activos" value={devices.length} icon={<Cpu size={16} />} accent="accent" />
        <StatCard label="Alertas activas" value={activeAlerts} icon={<Bell size={16} />} accent={activeAlerts > 0 ? 'danger' : 'success'} />
        <StatCard label="Críticas" value={criticalAlerts} icon={<AlertTriangle size={16} />} accent={criticalAlerts > 0 ? 'danger' : 'default'} />
        <StatCard label={`Lecturas · ${hours}h`} value={totalReadings || '—'} icon={<Activity size={16} />} spark={spark} hint={selectedDevice?.name} />
      </div>

      {/* Estado por dispositivo */}
      {devices.length > 0 && (
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wider text-faint mb-2">Estado por dispositivo</p>
          <div className="flex flex-wrap gap-2">
            {devices.map((d) => {
              const act = activeByDevice[d.id] ?? 0
              const sel = d.id === selectedId
              return (
                <button
                  key={d.id}
                  onClick={() => setSelectedId(d.id)}
                  className={cn(
                    'flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm transition-colors',
                    sel ? 'border-accent/50 bg-accent/10 text-foreground' : 'border-line bg-surface text-muted hover:border-accent/30 hover:text-foreground',
                  )}
                >
                  <span className={cn('h-2 w-2 rounded-full', act > 0 ? 'bg-danger animate-pulse' : 'bg-success')} />
                  {d.name}
                  {act > 0 && <Badge tone="danger">{act}</Badge>}
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Sensores del dispositivo seleccionado */}
      {!selectedId ? (
        <EmptyState title="No hay dispositivos disponibles" />
      ) : activeSensors.length === 0 ? (
        <EmptyState icon={<Activity size={28} />} title={`Sin lecturas para ${selectedDevice?.name ?? 'el dispositivo'} en las últimas ${hours}h`} hint="Inicia el simulador para generar datos" />
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {activeSensors.map((sensor) => (
            <SensorPanel key={`${selectedId}-${sensor}-${hours}`} deviceId={selectedId} sensor={sensor} hours={hours} deviceName={selectedDevice?.name ?? ''} />
          ))}
        </div>
      )}
    </div>
  )
}

function SensorPanel({ deviceId, sensor, hours, deviceName }: { deviceId: string; sensor: string; hours: number; deviceName: string }) {
  const meta = SENSOR_META[sensor] ?? { color: '#22d3ee', unit: '', label: sensor }
  const { data, loading, refetch } = useQuery(BUCKETED, {
    variables: { deviceId, sensorType: sensor, hours, bucketMinutes: autoBucket(hours) },
    pollInterval: 60000, // respaldo; el tiempo real llega por suscripción WebSocket
  })

  // Real-time: refetch (debounced) cuando llega una lectura nueva por suscripción
  const refetchRef = useRef(refetch)
  refetchRef.current = refetch
  const timer = useRef<number | undefined>(undefined)
  useEffect(() => {
    const unsub = subscribeReadings({ deviceId, sensorType: sensor }, () => {
      if (timer.current) return
      timer.current = window.setTimeout(() => {
        timer.current = undefined
        refetchRef.current()
      }, 1500)
    })
    return () => {
      unsub()
      if (timer.current) window.clearTimeout(timer.current)
    }
  }, [deviceId, sensor, hours])

  const buckets = (data as any)?.bucketedReadings ?? []
  const series = buckets.map((b: any) => ({ time: fmtTime(b.bucket, hours), value: Number(b.avgValue) }))
  const current: number | null = series.length ? series[series.length - 1].value : null
  const status = current != null ? statusFor(sensor, current) : 'normal'

  return (
    <Card>
      <CardHeader
        title={
          <span className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full" style={{ background: meta.color }} />
            {meta.label}
          </span>
        }
        subtitle={`${deviceName} · últimas ${hours}h`}
        action={current != null && <Badge tone={STATUS_TONE[status]}>{STATUS_LABEL[status]}</Badge>}
      />
      <div className="px-5 -mt-1 mb-2">
        <span className={cn('text-3xl font-semibold tnum', STATUS_TEXT[status])}>
          {current != null ? current.toFixed(1) : '—'}
        </span>
        <span className="text-sm text-faint ml-1">{meta.unit.trim()}</span>
      </div>
      <div className="px-2 pb-3">
        {loading && series.length === 0 ? (
          <div className="h-[200px] flex items-center justify-center text-sm text-faint">Cargando…</div>
        ) : series.length === 0 ? (
          <div className="h-[200px] flex items-center justify-center text-sm text-faint">Sin lecturas</div>
        ) : (
          <SensorChart data={series} color={meta.color} unit={meta.unit} thresholds={THRESHOLDS[sensor]} />
        )}
      </div>
    </Card>
  )
}
