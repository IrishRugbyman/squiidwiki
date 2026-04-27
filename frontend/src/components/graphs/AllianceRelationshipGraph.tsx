import { useMemo, useCallback } from 'react'
import ReactFlow, {
  Background,
  Controls,
  Handle,
  Position,
  MarkerType,
  type Edge,
  type Node,
  type NodeProps,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useNavigate } from '@tanstack/react-router'
import { useQueries } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { SetListItem, SetReadDetail, UUID } from '@/lib/types'

type SetNodeData = {
  label: string
  variant: 'internal' | 'external'
  slug: string | null
  size: number
}

function SetNode({ data }: NodeProps<SetNodeData>) {
  const cls =
    data.variant === 'internal'
      ? 'bg-violet-950/80 border-violet-600 text-violet-100'
      : 'bg-zinc-900/80 border-zinc-700 text-zinc-300'
  return (
    <div
      className={`flex items-center justify-center rounded-full border text-xs font-medium shadow-md ${cls}`}
      style={{ width: data.size, height: data.size }}
    >
      <Handle type="target" position={Position.Left} className="!bg-zinc-700 !border-zinc-700" />
      <Handle type="source" position={Position.Right} className="!bg-zinc-700 !border-zinc-700" />
      <span className="px-2 text-center leading-tight" style={{ fontSize: Math.max(10, data.size / 6) }}>
        {data.label}
      </span>
    </div>
  )
}

const nodeTypes = { set: SetNode }

interface AllianceRelationshipGraphProps {
  allianceSets: SetListItem[]
  allSets: SetListItem[]
  memberCountBySetId: Record<string, number>
  universeId: UUID
}

export function AllianceRelationshipGraph({
  allianceSets, allSets, memberCountBySetId, universeId,
}: AllianceRelationshipGraphProps) {
  const navigate = useNavigate()

  const setMap = useMemo(() => {
    const m: Record<string, SetListItem> = {}
    for (const s of allSets) m[s.id] = s
    return m
  }, [allSets])

  // Fetch each alliance set's detail in parallel for friend/enemy ids.
  const detailQueries = useQueries({
    queries: allianceSets.map((s) => ({
      queryKey: ['sets', s.id],
      queryFn: () => api.get<SetReadDetail>(`/sets/${s.id}?universe_id=${universeId}`),
      enabled: !!universeId && !!s.id,
    })),
  })

  const { nodes, edges, externalCount, loading } = useMemo(() => {
    const internalIds = new Set(allianceSets.map((s) => s.id))
    const externalIds = new Set<string>()
    const edgeKeys = new Set<string>()
    const edgesOut: Edge[] = []

    // Collect external set ids from each loaded detail.
    for (const q of detailQueries) {
      const d = q.data
      if (!d) continue
      for (const fid of d.friend_ids ?? []) if (!internalIds.has(fid)) externalIds.add(fid)
      for (const eid of d.enemy_ids ?? []) if (!internalIds.has(eid)) externalIds.add(eid)
    }

    // Filter externals to ones we can name.
    const externals = Array.from(externalIds).filter((id) => setMap[id])

    // Node sizing: scale with sqrt(memberCount), clamped to [44, 96] px.
    const sizeFor = (count: number) => {
      const base = 44
      const scaled = base + Math.sqrt(count) * 10
      return Math.max(44, Math.min(96, scaled))
    }

    const INTERNAL_R = 220
    const EXTERNAL_R = 460

    const nodesOut: Node<SetNodeData>[] = []

    allianceSets.forEach((s, idx) => {
      const angle = (idx / Math.max(allianceSets.length, 1)) * Math.PI * 2 - Math.PI / 2
      const size = sizeFor(memberCountBySetId[s.id] ?? 0)
      nodesOut.push({
        id: s.id,
        type: 'set',
        position: { x: Math.cos(angle) * INTERNAL_R, y: Math.sin(angle) * INTERNAL_R },
        data: { label: s.name, variant: 'internal', slug: s.slug, size },
      })
    })

    externals.forEach((eid, idx) => {
      const angle = (idx / Math.max(externals.length, 1)) * Math.PI * 2 - Math.PI / 2
      const ext = setMap[eid]
      const size = sizeFor(memberCountBySetId[eid] ?? 0)
      nodesOut.push({
        id: eid,
        type: 'set',
        position: { x: Math.cos(angle) * EXTERNAL_R, y: Math.sin(angle) * EXTERNAL_R },
        data: { label: ext.name, variant: 'external', slug: ext.slug, size },
      })
    })

    // Build edges, deduped by sorted-pair key + relation type.
    function addEdge(a: string, b: string, isAlly: boolean) {
      const lo = a < b ? a : b
      const hi = a < b ? b : a
      const k = `${lo}-${hi}-${isAlly ? 'A' : 'E'}`
      if (edgeKeys.has(k)) return
      edgeKeys.add(k)
      edgesOut.push({
        id: k,
        source: a,
        target: b,
        animated: isAlly,
        style: { stroke: isAlly ? '#10b981' : '#ef4444', strokeWidth: 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: isAlly ? '#10b981' : '#ef4444' },
      })
    }

    for (const q of detailQueries) {
      const d = q.data
      if (!d) continue
      for (const fid of d.friend_ids ?? []) {
        if (internalIds.has(fid) || externalIds.has(fid)) addEdge(d.id, fid, true)
      }
      for (const eid of d.enemy_ids ?? []) {
        if (internalIds.has(eid) || externalIds.has(eid)) addEdge(d.id, eid, false)
      }
    }

    return {
      nodes: nodesOut,
      edges: edgesOut,
      externalCount: externals.length,
      loading: detailQueries.some((q) => q.isLoading),
    }
  }, [allianceSets, detailQueries, setMap, memberCountBySetId])

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node<SetNodeData>) => {
      const id = node.data.slug ?? node.id
      navigate({ to: '/sets/$id', params: { id } })
    },
    [navigate],
  )

  if (allianceSets.length === 0) {
    return <p className="py-6 text-sm text-zinc-600">No sets in this alliance to graph.</p>
  }

  return (
    <div className="relative h-[480px] overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        onNodeClick={onNodeClick}
        proOptions={{ hideAttribution: true }}
        panOnScroll
        zoomOnScroll={false}
        nodesDraggable={false}
        className="bg-zinc-950"
      >
        <Background color="#27272a" gap={20} size={1} />
        <Controls className="!bg-zinc-900 !border-zinc-700 [&>button]:!bg-zinc-900 [&>button]:!border-zinc-700 [&>button]:!text-zinc-400 [&>button:hover]:!bg-zinc-800" />
      </ReactFlow>
      <div className="pointer-events-none absolute bottom-2 right-2 flex gap-3 rounded-md border border-zinc-800 bg-zinc-950/90 px-2 py-1 text-[10px] text-zinc-500">
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-violet-500" /> In alliance</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-emerald-500" /> Ally</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-red-500" /> Enemy</span>
        {loading && <span className="text-zinc-600">· loading…</span>}
        {!loading && externalCount > 0 && <span className="text-zinc-600">· {externalCount} external</span>}
      </div>
    </div>
  )
}

export default AllianceRelationshipGraph
