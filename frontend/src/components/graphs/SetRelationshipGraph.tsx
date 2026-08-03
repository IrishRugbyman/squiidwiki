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
import type { UUID } from '@/lib/types'

export interface SetGraphNode {
  id: UUID
  name: string
  slug: string | null
}

export interface SetGraphInput {
  centerSetId: UUID
  centerSetName: string
  friendIds: UUID[]
  enemyIds: UUID[]
  sets: SetGraphNode[]
}

type SetNodeData = {
  label: string
  variant: 'center' | 'ally' | 'enemy'
  slug: string | null
}

function SetNode({ data }: NodeProps<SetNodeData>) {
  const variantClass =
    data.variant === 'center'
      ? 'bg-violet-950/80 border-violet-600 text-violet-100'
      : data.variant === 'ally'
      ? 'bg-emerald-950/60 border-emerald-700 text-emerald-200'
      : 'bg-red-950/60 border-red-700 text-red-200'

  return (
    <div className={`rounded-lg border px-3 py-2 text-xs font-medium shadow-md ${variantClass}`}>
      <Handle type="target" position={Position.Left} className="!bg-zinc-700 !border-zinc-700" />
      <Handle type="source" position={Position.Right} className="!bg-zinc-700 !border-zinc-700" />
      {data.label}
    </div>
  )
}

const nodeTypes = { set: SetNode }

export function SetRelationshipGraph({ input }: { input: SetGraphInput }) {
  const navigate = useNavigate()
  const setMap = useMemo(() => {
    const m: Record<string, SetGraphNode> = {}
    for (const s of input.sets) m[s.id] = s
    return m
  }, [input.sets])

  const { nodes, edges } = useMemo(() => {
    const friendIds = input.friendIds.filter((id) => setMap[id])
    const enemyIds = input.enemyIds.filter((id) => setMap[id])

    const RADIUS = 220
    const allRelIds = [...friendIds, ...enemyIds]
    const total = Math.max(allRelIds.length, 1)

    const nodes: Node<SetNodeData>[] = []
    const edges: Edge[] = []

    nodes.push({
      id: input.centerSetId,
      type: 'set',
      position: { x: 0, y: 0 },
      data: { label: input.centerSetName, variant: 'center', slug: null },
    })

    allRelIds.forEach((id, idx) => {
      const isAlly = friendIds.includes(id)
      const angle = (idx / total) * Math.PI * 2 - Math.PI / 2
      const x = Math.cos(angle) * RADIUS
      const y = Math.sin(angle) * RADIUS
      const s = setMap[id]

      nodes.push({
        id,
        type: 'set',
        position: { x, y },
        data: {
          label: s?.name ?? id.slice(0, 8),
          variant: isAlly ? 'ally' : 'enemy',
          slug: s?.slug ?? null,
        },
      })

      edges.push({
        id: `${input.centerSetId}-${id}`,
        source: input.centerSetId,
        target: id,
        animated: isAlly,
        style: {
          stroke: isAlly ? '#10b981' : '#ef4444',
          strokeWidth: 2,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isAlly ? '#10b981' : '#ef4444',
        },
      })
    })

    return { nodes, edges }
  }, [input, setMap])

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node<SetNodeData>) => {
      if (node.id === input.centerSetId) return
      const s = setMap[node.id]
      const to = s?.slug ?? node.id
      navigate({ to: '/sets/$id', params: { id: to } })
    },
    [navigate, input.centerSetId, setMap],
  )

  if (input.friendIds.length === 0 && input.enemyIds.length === 0) {
    return null
  }

  return (
    <div className="relative h-[420px] overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950">
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
      <div className="pointer-events-none absolute bottom-2 right-2 flex gap-3 rounded-md border border-zinc-800 bg-zinc-950/90 px-2 py-1 text-[10px] text-zinc-400">
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-emerald-500" /> Ally</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-red-500" /> Enemy</span>
      </div>
    </div>
  )
}
