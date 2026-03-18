import type { ComponentType, ReactNode } from 'react'

import { cn } from '@/lib/utils'

export function PageStack({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('flex flex-col gap-6', className)} {...props} />
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
    <section className={cn('rounded-3xl border border-slate-200 bg-white p-6 shadow-sm', className)}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl space-y-2">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">{eyebrow}</p>
          <h1 className="text-3xl font-semibold tracking-tight text-slate-950">{title}</h1>
          <div className="text-sm leading-6 text-slate-600">{description}</div>
        </div>
        {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
      </div>
      {children ? <div className="mt-6">{children}</div> : null}
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
    <div className={cn('rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition-transform duration-150 hover:-translate-y-0.5', className)}>
      <div className="w-fit rounded-2xl bg-slate-100 p-2 text-slate-700">
        <Icon className="h-4 w-4" />
      </div>
      <p className="mt-4 text-sm font-medium text-slate-500">{title}</p>
      <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">{value}</p>
      <p className="mt-1 text-sm text-slate-600">{hint}</p>
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
    <div className="flex flex-col gap-2 border-b border-slate-200 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h3 className="font-semibold text-slate-950">{title}</h3>
        <div className="text-sm text-slate-600">{description}</div>
      </div>
      {badge ? <div>{badge}</div> : null}
    </div>
  )
}
