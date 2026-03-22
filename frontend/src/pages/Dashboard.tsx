import { gql } from '@apollo/client/core'
import { useQuery } from '@apollo/client/react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const DEVICE_SUMMARIES = gql`
  query DeviceSummaries {
    deviceSummary(deviceId: "d0000000-0000-0000-0000-000000000001", sensorType: "temperature", hours: 24) {
      deviceId
      sensorType
      readingCount
      minValue
      maxValue
      avgValue
      lastValue
      lastRecordedAt
    }
  }
`

const RECENT_READINGS = gql`
  query RecentReadings($deviceId: String!, $sensorType: String!) {
    readings(deviceId: $deviceId, sensorType: $sensorType, limit: 30) {
      value
      unit
      recordedAt
    }
  }
`

function SummaryCard({
  label,
  value,
  unit,
  color,
}: {
  label: string
  value: number | null | undefined
  unit: string
  color: string
}) {
  return (
    <div className="bg-slate-800 rounded-xl p-4">
      <p className="text-xs text-slate-400 mb-1">{label}</p>
      <p className={`text-2xl font-semibold ${color}`}>
        {value != null ? `${Number(value).toFixed(1)}${unit}` : '—'}
      </p>
    </div>
  )
}

function ReadingsChart({
  deviceId,
  sensorType,
  color,
  unit,
}: {
  deviceId: string
  sensorType: string
  color: string
  unit: string
}) {
  const { data, loading } = useQuery(RECENT_READINGS, {
    variables: { deviceId, sensorType },
    pollInterval: 10000,
  })

  const chartData = ((data as any)?.readings ?? [])
    .map((r: any) => ({
      time: new Date(r.recordedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      value: Number(r.value),
    }))
    .reverse()

  if (loading && chartData.length === 0) {
    return <div className="h-48 flex items-center justify-center text-slate-500 text-sm">Loading…</div>
  }

  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} />
        <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} unit={unit} width={45} />
        <Tooltip
          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
          labelStyle={{ color: '#94a3b8' }}
          itemStyle={{ color: color }}
        />
        <Line type="monotone" dataKey="value" stroke={color} dot={false} strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  )
}

const DEVICES = [
  { id: 'd0000000-0000-0000-0000-000000000001', name: 'Server Room', sensors: ['temperature', 'humidity'] },
  { id: 'd0000000-0000-0000-0000-000000000002', name: 'Office North', sensors: ['temperature', 'humidity'] },
  { id: 'd0000000-0000-0000-0000-000000000003', name: 'Solar Panel', sensors: ['energy'] },
]

const SENSOR_META: Record<string, { color: string; unit: string; label: string }> = {
  temperature: { color: '#f97316', unit: '°C', label: 'Temperature' },
  humidity: { color: '#38bdf8', unit: '%', label: 'Humidity' },
  energy: { color: '#4ade80', unit: ' kW', label: 'Power' },
}

export default function Dashboard() {
  const { data: summaryData } = useQuery(DEVICE_SUMMARIES, { pollInterval: 30000 })

  const summary = (summaryData as any)?.deviceSummary

  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-4">Dashboard</h2>

      {/* Summary row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <SummaryCard label="Last Temp (Rack A1)" value={summary?.lastValue} unit="°C" color="text-orange-400" />
        <SummaryCard label="Avg (24h)" value={summary?.avgValue} unit="°C" color="text-yellow-400" />
        <SummaryCard label="Min (24h)" value={summary?.minValue} unit="°C" color="text-blue-400" />
        <SummaryCard label="Max (24h)" value={summary?.maxValue} unit="°C" color="text-red-400" />
      </div>

      {/* Charts grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {DEVICES.flatMap((device) =>
          device.sensors.map((sensor) => {
            const meta = SENSOR_META[sensor]
            return (
              <div key={`${device.id}-${sensor}`} className="bg-slate-800 rounded-xl p-4">
                <p className="text-sm font-medium text-white mb-1">{device.name}</p>
                <p className="text-xs text-slate-400 mb-3">{meta.label}</p>
                <ReadingsChart
                  deviceId={device.id}
                  sensorType={sensor}
                  color={meta.color}
                  unit={meta.unit}
                />
              </div>
            )
          }),
        )}
      </div>
    </div>
  )
}
