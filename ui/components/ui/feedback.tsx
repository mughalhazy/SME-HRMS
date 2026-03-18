import type { ComponentType, ReactNode } from 'react'
import { AlertTriangle, LoaderCircle } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn('animate-pulse rounded-xl bg-slate-200/70', className)} aria-hidden="true" />
}

export function SurfaceSkeleton({
  lines = 4,
  className,
}: {
  lines?: number
  className?: string
}) {
  return (
    <div className={cn('rounded-2xl border border-slate-200 bg-white p-5 shadow-sm', className)}>
      <div className="space-y-3">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-8 w-72 max-w-full" />
        <Skeleton className="h-4 w-full max-w-2xl" />
      </div>
      <div className="mt-6 space-y-3">
        {Array.from({ length: lines }).map((_, index) => (
          <Skeleton key={index} className="h-12 w-full" />
        ))}
      </div>
    </div>
  )
}

export function StatSkeletonGrid({ count = 3 }: { count?: number }) {
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <Skeleton className="h-10 w-10 rounded-2xl" />
          <Skeleton className="mt-4 h-4 w-28" />
          <Skeleton className="mt-3 h-8 w-20" />
          <Skeleton className="mt-2 h-4 w-40" />
        </div>
      ))}
    </div>
  )
}

export function TableSkeleton({ rows = 5, columns = 5 }: { rows?: number; columns?: number }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-5 py-3.5">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="mt-2 h-4 w-72 max-w-full" />
      </div>
      <div className="space-y-0">
        <div className="grid gap-4 border-b border-slate-200 bg-slate-50 px-5 py-3" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}>
          {Array.from({ length: columns }).map((_, index) => (
            <Skeleton key={index} className="h-3 w-20" />
          ))}
        </div>
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div
            key={rowIndex}
            className="grid gap-4 border-b border-slate-100 px-5 py-3.5 last:border-b-0"
            style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
          >
            {Array.from({ length: columns }).map((_, columnIndex) => (
              <Skeleton key={columnIndex} className="h-4 w-full" />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
  className,
}: {
  title?: string
  message: string
  onRetry?: () => void
  className?: string
}) {
  return (
    <div className={cn('rounded-2xl border border-rose-200 bg-rose-50/70 p-5 shadow-sm', className)} role="alert">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-2xl bg-white p-2 text-rose-600 shadow-sm">
            <AlertTriangle className="h-4 w-4" />
          </div>
          <div className="space-y-1">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-rose-700">Error state</p>
            <h3 className="text-lg font-semibold text-rose-950">{title}</h3>
            <p className="max-w-2xl text-sm leading-6 text-rose-700/90">{message}</p>
          </div>
        </div>
        {onRetry ? (
          <Button type="button" variant="outline" className="border-rose-200 bg-white text-rose-700 hover:bg-rose-100" onClick={onRetry}>
            Retry
          </Button>
        ) : null}
      </div>
    </div>
  )
}

export function EmptyState({
  icon: Icon,
  title,
  message,
  action,
  className,
}: {
  icon: ComponentType<{ className?: string }>
  title: string
  message: string
  action?: ReactNode
  className?: string
}) {
  return (
    <div className={cn('rounded-2xl border border-dashed border-slate-300 bg-slate-50/80 p-6 text-center shadow-sm', className)}>
      <div className="mx-auto flex max-w-md flex-col items-center gap-4">
        <div className="rounded-2xl bg-white p-3 text-slate-700 shadow-sm ring-1 ring-slate-200">
          <Icon className="h-5 w-5" />
        </div>
        <div className="space-y-2">
          <h3 className="text-lg font-semibold tracking-tight text-slate-950">{title}</h3>
          <p className="text-sm leading-6 text-slate-600">{message}</p>
        </div>
        {action ? <div className="pt-1">{action}</div> : null}
      </div>
    </div>
  )
}

export function InlineLoading({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-slate-500">
      <LoaderCircle className="h-4 w-4 animate-spin" />
      {label}
    </span>
  )
}
