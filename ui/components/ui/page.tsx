import type { ComponentType, ReactNode } from 'react'

import { cn } from '@/lib/utils'

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
    <section className={cn('border-b border-slate-200 pb-6', className)}>
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl space-y-1.5">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{eyebrow}</p>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-950 sm:text-[2rem]">{title}</h1>
          <div className="text-sm leading-6 text-slate-600">{description}</div>
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
      </div>
      {children ? <div className="mt-4">{children}</div> : null}
    </section>
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
    <div className={cn('rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-surface)]', className)}>
      <div className="w-fit rounded-[var(--radius-control)] bg-[var(--surface-subtle)] p-2 text-slate-700">
        <Icon className="h-4 w-4" />
      </div>
      <p className="mt-4 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{title}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{value}</p>
      <p className="mt-2 text-sm leading-6 text-slate-600">{hint}</p>
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
        <h3 className="font-semibold text-slate-950">{title}</h3>
        <div className="text-sm leading-6 text-slate-600">{description}</div>
      </div>
      {badge ? <div>{badge}</div> : null}
    </div>
  )
}
