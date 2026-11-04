import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { FuzzyDateInput } from './FuzzyDateInput'

// The input once reported a value from a mount-time effect, so merely opening
// a form re-encoded the date on file: June 2022 became circa 2022 on an
// unchanged save. It may only speak when the user changes something.

describe('FuzzyDateInput', () => {
  it('reports nothing on mount, whatever it was given', () => {
    for (const value of [
      { year: 2022, month: 6, precision: 'YM' as const, approx: false },
      { year: 2022, precision: 'Y' as const, approx: false },
      { year: 2022, month: 6, day: 1, precision: 'YMD' as const, approx: false },
      { precision: 'UNKNOWN' as const, approx: false },
      null,
    ]) {
      const onChange = vi.fn()
      const { unmount } = render(<FuzzyDateInput value={value} onChange={onChange} idPrefix="t" />)
      expect(onChange).not.toHaveBeenCalled()
      unmount()
    }
  })

  it('does not tell a life-sentence form anything on mount either', () => {
    const lifeChange = vi.fn()
    render(<FuzzyDateInput value={null} onChange={vi.fn()} idPrefix="t" life={{ value: true, onChange: lifeChange }} />)
    expect(lifeChange).not.toHaveBeenCalled()
  })

  it('reports a year the user types', () => {
    const onChange = vi.fn()
    render(<FuzzyDateInput value={{ year: 2022, precision: 'Y', approx: false }} onChange={onChange} idPrefix="t" />)
    fireEvent.change(screen.getByPlaceholderText('YYYY'), { target: { value: '2021' } })
    expect(onChange).toHaveBeenLastCalledWith({ year: 2021, precision: 'Y', approx: true })
  })

  it('reports a switch to unknown', () => {
    const onChange = vi.fn()
    render(<FuzzyDateInput value={{ year: 2022, precision: 'Y', approx: false }} onChange={onChange} idPrefix="t" />)
    fireEvent.click(screen.getByLabelText('unknown'))
    expect(onChange).toHaveBeenLastCalledWith({ precision: 'UNKNOWN', approx: false })
  })

  it('reports an exact date the user picks', () => {
    const onChange = vi.fn()
    const { container } = render(<FuzzyDateInput value={null} onChange={onChange} idPrefix="t" />)
    fireEvent.click(screen.getByLabelText('exact'))
    fireEvent.change(container.querySelector('input[type="date"]')!, { target: { value: '2020-11-17' } })
    expect(onChange).toHaveBeenLastCalledWith({ year: 2020, month: 11, day: 17, precision: 'YMD', approx: false })
  })
})
