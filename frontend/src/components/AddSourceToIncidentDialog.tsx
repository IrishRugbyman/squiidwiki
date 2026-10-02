import { AttachSourcesDialog } from '@/components/AttachSourcesDialog'
import { useUpdateIncident } from '@/lib/queries'
import type { IncidentReadDetail } from '@/lib/types'

interface AddSourceToIncidentDialogProps {
  incident: IncidentReadDetail
  universeId: string
  open: boolean
  onClose: () => void
  onCreateNew: () => void
}

export function AddSourceToIncidentDialog({
  incident, universeId, open, onClose, onCreateNew,
}: AddSourceToIncidentDialogProps) {
  const update = useUpdateIncident(incident.id, universeId)
  return (
    <AttachSourcesDialog
      universeId={universeId}
      existingIds={incident.source_ids}
      open={open}
      onClose={onClose}
      onCreateNew={onCreateNew}
      onAttach={(source_ids) => update.mutateAsync({ source_ids })}
      attaching={update.isPending}
    />
  )
}
