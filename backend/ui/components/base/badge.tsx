import * as React from 'react'

import { cn } from '@/lib/utils'

const badgeVariantClassNames = {
  default: 'border-transparent bg-[var(--primary-soft)] text-[var(--primary)]',
  outline: 'border-[var(--border)] bg-transparent text-[var(--muted-foreground)]',
  info: 'border-transparent bg-[var(--accent)] text-[var(--primary)]',
  success: 'border-transparent bg-[var(--success-soft)] text-[var(--success)]',
  warning: 'border-transparent bg-amber-50 text-amber-700',
  danger: 'border-transparent bg-rose-50 text-rose-700',
} as const

type BadgeVariant = keyof typeof badgeVariantClassNames

function badgeVariants({ variant = 'default' }: { variant?: BadgeVariant }) {
  return cn('inline-flex items-center rounded-[var(--radius-control)] border px-3 py-1 text-xs font-semibold whitespace-nowrap', badgeVariantClassNames[variant])
}

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: BadgeVariant
}

function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
