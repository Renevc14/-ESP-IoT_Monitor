import { gql } from '@apollo/client/core'
import { useQuery } from '@apollo/client/react'
import { Download } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { SensorChart } from '../components/SensorChart'
import { buttonClasses } from '../components/ui/Button'
import { Card, CardHeader } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'
import { Select } from '../components/ui/Field'
import { PageHeader } from '../components/ui/PageHeader'
import { Segmented } from '../components/ui/Segmented'
import { StatCard } from '../components/ui/StatCard'

const ANALYTICS_URL = import.meta.env.VITE_ANALYTICS_URL ?? 'http://localhost:8004'

const DEVICE_SUMMARY = gql`
  query AnalyticsSummary($deviceId: String!, $hours: Int!) {
    deviceSummary(deviceId: $deviceId, hours: $hours) {
      sensorType avgValue minValue maxValue p95Value trend readingCount
    }
  }
`

const BUCKETED = gql`
  query AnalyticsBuckets($deviceId: String!, $sensorType: String!, $hours: Int!, $bucketMinutes: Int!) {
    bucketedReadings(deviceId: $deviceId, sensorType: $sensorType, hours: $hours, bucketMinutes: $bucketMinutes) {
      bucket avgValue minValue maxValue
    }
  }
`

function autoBucket(hours: number): number {
  if (hours <= 1) return 1
  if (hours <= 6) return 5
  if (hours <= 24) return 30
  return 60
}

const SENSORS = ['temperature', 'humidity', 'energy']
const AGGREGATIONS = [
  { key: 'avgValue', label: 'Promedio' },
  { key: 'minValue', label: 'Mínimo' },
  { key: 'maxValue', label: 'Máximo' },
] as const
const PERIODS = [
  { label: '6h', value: 6 },
  { label: '24h', value: 24 },
  { label: '7d', value: 168 },
  { label: '30d', value: 720 },
]
const SENSOR_COLOR: Record<string, string> = { temperature: '#f97316', humidity: '#38bdf8', energy: '#34d399' }

interface Device { id: string; name: string }

export default function Analytics() {
  const [devices, setDevices] = useState<Device[]>([])
  const [deviceId, setDeviceId] = useState('')
  const [sensorType, setSensorType] = useState<string>('temperature')
  const [hours, setHours] = useState(24)
  const [agg, setAgg] = useState<typeof AGGREGATIONS[number]['key']>('avgValue')

  useEffect(() => {
    api.get('/devices').then((r) => {
      const list: Device[] = r.data
      setDevices(list)
      if (list.length && !deviceId) setDeviceId(list[0].id)
    }).catch(() => {})
  }, [])

  const { data: sumData } = useQuery(DEVICE_SUMMARY, { variables: { deviceId, hours }, skip: !deviceId })
  const { data: bucketData } = useQuery(BUCKETED, {
    variables: { deviceId, sensorType, hours, bucketMinutes: autoBucket(hours) },
    skip: !deviceId,
  })

  const summary = ((sumData as any)?.deviceSummary ?? []).find((s: any) => s.sensorType === sensorType)
  const chartData = ((bucketData as any)?.bucketedReadings ?? []).map((r: any) => ({
    time: new Date(r.bucket).toLocaleString([], { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }),
    value: Number(r[agg]),
  }))

  function exportUrl(fmt: 'csv' | 'json') {
    const params = new URLSearchParams({ device_id: deviceId, sensor_type: sensorType, hours: String(hours) })
    return `${ANALYTICS_URL}/export/readings.${fmt}?${params.toString()}`
  }

  return (
    <div>
      <PageHeader title="Analytics" subtitle="Exploración de métricas y exportación de datos">
        <a href={exportUrl('csv')} className={buttonClasses('secondary', 'sm')}><Download size={14} /> CSV</a>
        <a href={exportUrl('json')} className={buttonClasses('secondary', 'sm')}><Download size={14} /> JSON</a>
      </PageHeader>

      <div className="flex flex-wrap items-center gap-2 mb-5">
        <Select value={deviceId} onChange={(e) => setDeviceId(e.target.value)} className="w-52">
          {devices.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </Select>
        <Select value={sensorType} onChange={(e) => setSensorType(e.target.value)} className="w-36">
          {SENSORS.map((s) => <option key={s} value={s}>{s}</option>)}
        </Select>
        <Select value={agg} onChange={(e) => setAgg(e.target.value as any)} className="w-36">
          {AGGREGATIONS.map((a) => <option key={a.key} value={a.key}>{a.label}</option>)}
        </Select>
        <Segmented options={PERIODS} value={hours} onChange={setHours} />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <StatCard label="Promedio" value={fmt(summary?.avgValue)} />
        <StatCard label="Mínimo" value={fmt(summary?.minValue)} />
        <StatCard label="Máximo" value={fmt(summary?.maxValue)} />
        <StatCard label="Percentil 95" value={fmt(summary?.p95Value)} accent="accent" />
        <StatCard label="Tendencia" value={fmtSigned(summary?.trend)} accent={(summary?.trend ?? 0) >= 0 ? 'success' : 'danger'} />
      </div>

      <Card>
        <CardHeader title="Serie temporal" subtitle={`${sensorType} · ${AGGREGATIONS.find((a) => a.key === agg)?.label} · últimas ${hours}h`} />
        <div className="px-2 pb-3">
          {chartData.length === 0 ? (
            <EmptyState title="Sin datos para el periodo seleccionado" />
          ) : (
            <SensorChart data={chartData} color={SENSOR_COLOR[sensorType] ?? '#6366f1'} height={300} />
          )}
        </div>
      </Card>
    </div>
  )
}

function fmt(v?: number) {
  return v != null ? Number(v).toFixed(2) : '—'
}
function fmtSigned(v?: number) {
  if (v == null) return '—'
  const n = Number(v)
  return `${n >= 0 ? '+' : ''}${n.toFixed(2)}`
}
