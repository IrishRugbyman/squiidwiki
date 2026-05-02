const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

export interface FuzzyDateValue {
  year?: number | null
  month?: number | null
  day?: number | null
  precision: 'Y' | 'YM' | 'YMD' | 'UNKNOWN'
  approx: boolean
}

interface FuzzyDateProps {
  value: FuzzyDateValue | null | undefined
  fallback?: string
  className?: string
}

export function FuzzyDate({ value, fallback = 'Unknown', className }: FuzzyDateProps) {
  if (!value || value.precision === 'UNKNOWN') {
    return <span className={className}>{fallback}</span>
  }

  const prefix = value.approx ? 'c. ' : ''

  let text: string
  if (value.precision === 'YMD' && value.year && value.month && value.day) {
    text = `${prefix}${MONTHS[value.month - 1]} ${value.day}, ${value.year}`
  } else if (value.precision === 'YM' && value.year && value.month) {
    text = `${prefix}${MONTHS[value.month - 1]} ${value.year}`
  } else if (value.precision === 'Y' && value.year) {
    text = `${prefix}${value.year}`
  } else {
    return <span className={className}>{fallback}</span>
  }

  return (
    <time
      className={className}
      dateTime={buildIso(value)}
      title={value.approx ? `Approximate: ${text}` : text}
    >
      {text}
    </time>
  )
}

function buildIso(v: FuzzyDateValue): string {
  if (!v.year) return ''
  if (v.precision === 'YMD' && v.month && v.day) return `${v.year}-${String(v.month).padStart(2, '0')}-${String(v.day).padStart(2, '0')}`
  if (v.precision === 'YM' && v.month) return `${v.year}-${String(v.month).padStart(2, '0')}`
  return String(v.year)
}
