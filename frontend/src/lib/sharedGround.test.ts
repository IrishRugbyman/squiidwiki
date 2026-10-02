import { describe, expect, it } from 'vitest'
import { groupBySameGround, groundKey, nextSetOnClick } from './sharedGround'
import type { UUID } from './types'

const square = (x: number): GeoJSON.Polygon => ({
  type: 'Polygon',
  coordinates: [[[x, 0], [x + 1, 0], [x + 1, 1], [x, 1], [x, 0]]],
})
const set = (id: string, polygon: GeoJSON.Polygon | GeoJSON.MultiPolygon | null) => ({
  id: id as UUID,
  territory_polygon: polygon,
})

describe('groupBySameGround', () => {
  it('puts sets carrying the same outline in one group, in order', () => {
    // The Parkside case: three sets, one polygon copied onto each.
    const parkside = square(0)
    const groups = groupBySameGround([
      set('264', { ...parkside }),
      set('752', { ...parkside }),
      set('elsewhere', square(5)),
      set('YS', { ...parkside }),
    ])
    expect(groups.map((g) => g.map((s) => s.id))).toEqual([['264', '752', 'YS'], ['elsewhere']])
  })

  it('keeps overlapping but different outlines apart', () => {
    const groups = groupBySameGround([set('a', square(0)), set('b', square(0.5))])
    expect(groups).toHaveLength(2)
  })

  it('groups multi-part territories by all their pieces', () => {
    const pieces = (x: number): GeoJSON.MultiPolygon => ({
      type: 'MultiPolygon',
      coordinates: [square(x).coordinates, square(x + 10).coordinates],
    })
    const groups = groupBySameGround([set('a', pieces(0)), set('b', pieces(0)), set('c', pieces(1))])
    expect(groups.map((g) => g.map((s) => s.id))).toEqual([['a', 'b'], ['c']])
  })

  it('drops sets with no polygon', () => {
    expect(groupBySameGround([set('point-only', null)])).toEqual([])
  })

  it('treats a vertex difference as different ground', () => {
    const nudged = square(0)
    nudged.coordinates[0][2] = [1, 1.0001]
    expect(groundKey(set('a', square(0)))).not.toBe(groundKey(set('b', nudged)))
  })
})

describe('nextSetOnClick', () => {
  const ids = ['264', '752', 'YS'] as UUID[]

  it('starts at the lead when none of the shape is selected', () => {
    expect(nextSetOnClick(ids, null, '264' as UUID)).toBe('264')
    expect(nextSetOnClick(ids, 'unrelated' as UUID, '264' as UUID)).toBe('264')
  })

  it('steps to the next set and wraps round', () => {
    expect(nextSetOnClick(ids, '264' as UUID, '264' as UUID)).toBe('752')
    expect(nextSetOnClick(ids, '752' as UUID, '752' as UUID)).toBe('YS')
    expect(nextSetOnClick(ids, 'YS' as UUID, 'YS' as UUID)).toBe('264')
  })

  it('leaves a shape of one set on that set', () => {
    const one = ['solo'] as UUID[]
    expect(nextSetOnClick(one, 'solo' as UUID, 'solo' as UUID)).toBe('solo')
  })
})
