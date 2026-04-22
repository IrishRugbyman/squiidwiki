import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from 'recharts'

interface Point {
  month: string
  count: number
}

interface IncidentsOverTimeProps {
  data: Point[]
  className?: string
}

export function IncidentsOverTime({ data, className }: IncidentsOverTimeProps) {
  if (!data.length) return null

  // recharts draws something weird with a single data point; pad with a
  // zero-start point for a cleaner visual.
  const points = data.length === 1
    ? [{ month: '', count: 0 }, ...data]
    : data

  return (
    <div className={className} style={{ width: '100%', height: 160 }}>
      <ResponsiveContainer>
        <LineChart data={points} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
          <CartesianGrid stroke="#27272a" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="month"
            stroke="#52525b"
            tick={{ fontSize: 10, fill: '#71717a' }}
            tickFormatter={(m: string) => (m ? m.slice(5) : '')}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            stroke="#52525b"
            tick={{ fontSize: 10, fill: '#71717a' }}
            allowDecimals={false}
            axisLine={false}
            tickLine={false}
            width={32}
          />
          <Tooltip
            cursor={{ stroke: '#3f3f46', strokeWidth: 1 }}
            contentStyle={{
              background: '#18181b',
              border: '1px solid #27272a',
              borderRadius: 6,
              fontSize: 12,
            }}
            labelFormatter={(m) => String(m ?? '')}
          />
          <Line
            type="monotone"
            dataKey="count"
            stroke="#a78bfa"
            strokeWidth={2}
            dot={{ r: 2, fill: '#a78bfa' }}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
