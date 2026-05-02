import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { RELIABILITY_HEX } from '@/lib/statusColors'
import type { SourceReliability } from '@/lib/types'

interface ReliabilityDonutProps {
  counts: Record<string, number>
  className?: string
}

const ORDER: SourceReliability[] = ['HIGH', 'MEDIUM', 'LOW', 'UNVERIFIED']

export function ReliabilityDonut({ counts, className }: ReliabilityDonutProps) {
  const data = ORDER
    .map((key) => ({ name: key, value: counts[key] ?? 0 }))
    .filter((d) => d.value > 0)

  if (data.length === 0) return null

  const total = data.reduce((s, d) => s + d.value, 0)

  return (
    <div className={className} style={{ width: '100%', height: 160 }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius={40}
            outerRadius={64}
            strokeWidth={1}
            stroke="#18181b"
          >
            {data.map((d) => (
              <Cell key={d.name} fill={RELIABILITY_HEX[d.name as SourceReliability]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: '#18181b',
              border: '1px solid #27272a',
              borderRadius: 6,
              fontSize: 12,
            }}
            formatter={(value, name) => {
              const num = typeof value === 'number' ? value : Number(value) || 0
              return [`${num} (${Math.round((num / total) * 100)}%)`, String(name ?? '')] as [string, string]
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
