import { cn } from '@/lib/utils'

export interface MemberIdentityData {
  nickname: string | null
  legal_name: string | null
  nickname_unknown: boolean
  display_name: string
}

interface MemberIdentityProps {
  member: MemberIdentityData
  showLegalName?: boolean
  className?: string
  secondaryClassName?: string
}

export function MemberIdentity({ member, showLegalName = false, className, secondaryClassName }: MemberIdentityProps) {
  const primary = member.display_name
  const secondary = showLegalName && !member.nickname_unknown && member.legal_name ? member.legal_name : null

  return (
    <span className="inline-flex flex-col">
      <span className={cn('font-medium', className)}>{primary}</span>
      {secondary && (
        <span className={cn('text-xs text-zinc-500', secondaryClassName)}>
          a/k/a {secondary}
        </span>
      )}
    </span>
  )
}
