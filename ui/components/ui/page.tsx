import type { ComponentType, ReactNode } from 'react'

import { cn } from '@/lib/utils'

export const pageSurfaceClassName =
  'rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-surface)]'

export const pageMutedSurfaceClassName =
  'rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface-subtle)] shadow-[var(--shadow-surface)]'

export const pagePanelClassName =
  'rounded-[var(--radius-control)] border border-[var(--border)] bg-[var(--surface-subtle)]'

export const pagePillClassName =
  'inline-flex items-center rounded-[var(--radius-control)] border border-[var(--border)] bg-[var(--surface-subtle)] px-3 py-1 text-xs font-semibold text-[var(--muted-foreground)]'

export const pageSectionPaddingClassName = 'p-4 sm:p-5'
export const pageSectionHeaderClassName = 'flex flex-col gap-3 border-b border-[var(--border)] px-4 py-4 sm:px-5'
export const pageEyebrowClassName = 'text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted-foreground)]'
export const pageSectionTitleClassName = 'text-lg font-semibold tracking-tight text-[var(--foreground)]'
export const pageSectionBodyClassName = 'text-sm leading-6 text-[var(--muted-foreground)]'
export const pageMetaTextClassName = 'text-xs font-medium text-[var(--muted-foreground)]'
export const pageIconChipClassName = 'rounded-[var(--radius-control)] bg-[var(--surface-subtle)] p-2 text-[var(--foreground)]'

export function PageStack({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('flex flex-col gap-6', className)} {...props} />
}

export function PageGrid({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('grid gap-6', className)} {...props} />
}

export function PageHero({
  eyebrow,
  title,
  description,
  actions,
  children,
  className,
}: {
  eyebrow: string
  title: string
  description: ReactNode
  actions?: ReactNode
  children?: ReactNode
  className?: string
}) {
  return (
    <section className={cn('border-b border-[var(--border)] pb-6', className)}>
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl space-y-2">
          <p className={pageEyebrowClassName}>{eyebrow}</p>
          <h1 className="text-2xl font-semibold tracking-tight text-[var(--foreground)] sm:text-[2rem]">{title}</h1>
          <div className={pageSectionBodyClassName}>{description}</div>
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
      </div>
      {children ? <div className="mt-4">{children}</div> : null}
    </section>
  )
}

export function PageSection({ className, ...props }: React.HTMLAttributes<HTMLElement>) {
  return <section className={cn(pageSurfaceClassName, className)} {...props} />
}

export function PageSectionHeader({
  title,
  description,
  eyebrow,
  badge,
  actions,
  className,
}: {
  title: string
  description: ReactNode
  eyebrow?: string
  badge?: ReactNode
  actions?: ReactNode
  className?: string
}) {
  return (
    <div className={cn('flex flex-col gap-4 border-b border-[var(--border)] px-4 py-4 sm:px-5', className)}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 space-y-2">
          {eyebrow ? <p className={pageEyebrowClassName}>{eyebrow}</p> : null}
          <div className="space-y-1">
            <h2 className={pageSectionTitleClassName}>{title}</h2>
            <div className={pageSectionBodyClassName}>{description}</div>
          </div>
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
      </div>
      {badge ? <div>{badge}</div> : null}
    </div>
  )
}

export function StatCard({
  title,
  value,
  hint,
  icon: Icon,
  className,
}: {
  title: string
  value: string
  hint: string
  icon: ComponentType<{ className?: string }>
  className?: string
}) {
  return (
    <div className={cn(pageSurfaceClassName, 'p-5', className)}>
      <div className={cn('w-fit', pageIconChipClassName)}>
        <Icon className="h-4 w-4" />
      </div>
      <p className={cn('mt-4', pageEyebrowClassName)}>{title}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-[var(--foreground)]">{value}</p>
      <p className={cn('mt-2', pageSectionBodyClassName)}>{hint}</p>
    </div>
  )
}

export function SectionHeading({
  title,
  description,
  badge,
}: {
  title: string
  description: ReactNode
  badge?: ReactNode
}) {
  return (
    <div className="flex flex-col gap-3 border-b border-[var(--border)] bg-[var(--surface)] px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h3 className="font-semibold text-[var(--foreground)]">{title}</h3>
        <div className={pageSectionBodyClassName}>{description}</div>
      </div>
      {badge ? <div>{badge}</div> : null}
    </div>
  )
}
