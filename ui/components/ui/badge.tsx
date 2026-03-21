import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold tracking-[0.14em] whitespace-nowrap',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-[var(--primary-soft)] text-[var(--primary)]',
        outline: 'border-[var(--border)] bg-transparent text-[var(--muted-foreground)]',
        info: 'border-transparent bg-[var(--accent)] text-[var(--primary)]',
        success: 'border-transparent bg-[var(--success-soft)] text-[var(--success)]',
        warning: 'border-transparent bg-amber-50 text-amber-700',
        danger: 'border-transparent bg-rose-50 text-rose-700',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
