import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { FuzzyDate, type FuzzyDateValue } from './FuzzyDate'

function value(over: Partial<FuzzyDateValue>): FuzzyDateValue {
  return { precision: 'YMD', approx: false, ...over }
}

describe('FuzzyDate', () => {
  it('renders a full date as a machine-readable <time>', () => {
    render(<FuzzyDate value={value({ year: 1994, month: 3, day: 7 })} />)
    const el = screen.getByText('Mar 7, 1994')
    expect(el.tagName).toBe('TIME')
    expect(el).toHaveAttribute('datetime', '1994-03-07')
  })

  it('zero-pads the datetime attribute', () => {
    // "1994-3-7" is not a valid datetime value and assistive tech drops it.
    render(<FuzzyDate value={value({ year: 1994, month: 3, day: 7 })} />)
    expect(screen.getByText('Mar 7, 1994')).toHaveAttribute('datetime', '1994-03-07')
  })

  it('renders month precision without inventing a day', () => {
    render(<FuzzyDate value={value({ year: 1994, month: 11, precision: 'YM' })} />)
    const el = screen.getByText('Nov 1994')
    expect(el).toHaveAttribute('datetime', '1994-11')
  })

  it('renders year precision without inventing a month', () => {
    render(<FuzzyDate value={value({ year: 1994, precision: 'Y' })} />)
    expect(screen.getByText('1994')).toHaveAttribute('datetime', '1994')
  })

  it('marks an approximate date with c. and says so in the title', () => {
    render(<FuzzyDate value={value({ year: 1994, precision: 'Y', approx: true })} />)
    const el = screen.getByText('c. 1994')
    expect(el).toHaveAttribute('title', 'Approximate: c. 1994')
  })

  it('titles an exact date with the date itself, not an approximation note', () => {
    render(<FuzzyDate value={value({ year: 1994, precision: 'Y' })} />)
    expect(screen.getByText('1994')).toHaveAttribute('title', '1994')
  })

  describe('falls back rather than rendering a half-date', () => {
    it('on UNKNOWN precision', () => {
      render(<FuzzyDate value={value({ precision: 'UNKNOWN' })} />)
      expect(screen.getByText('Unknown')).toBeInTheDocument()
    })

    it('on null', () => {
      render(<FuzzyDate value={null} />)
      expect(screen.getByText('Unknown')).toBeInTheDocument()
    })

    it('on undefined', () => {
      render(<FuzzyDate value={undefined} />)
      expect(screen.getByText('Unknown')).toBeInTheDocument()
    })

    it('when precision claims a day the value does not have', () => {
      // Rather than rendering "Mar undefined, 1994".
      render(<FuzzyDate value={value({ year: 1994, month: 3, precision: 'YMD' })} />)
      expect(screen.getByText('Unknown')).toBeInTheDocument()
    })

    it('when precision claims a year the value does not have', () => {
      render(<FuzzyDate value={value({ month: 3, precision: 'Y' })} />)
      expect(screen.getByText('Unknown')).toBeInTheDocument()
    })

    it('as a <span>, so nothing claims a datetime it does not have', () => {
      render(<FuzzyDate value={null} />)
      expect(screen.getByText('Unknown').tagName).toBe('SPAN')
    })
  })

  it('uses a caller-supplied fallback', () => {
    render(<FuzzyDate value={null} fallback="No date recorded" />)
    expect(screen.getByText('No date recorded')).toBeInTheDocument()
  })

  it('passes className through on both the rendered and the fallback branch', () => {
    const { unmount } = render(<FuzzyDate value={value({ year: 1994, precision: 'Y' })} className="text-xs" />)
    expect(screen.getByText('1994')).toHaveClass('text-xs')
    unmount()
    render(<FuzzyDate value={null} className="text-xs" />)
    expect(screen.getByText('Unknown')).toHaveClass('text-xs')
  })
})
