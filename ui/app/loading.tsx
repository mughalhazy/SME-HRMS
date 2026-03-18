import { StatSkeletonGrid, SurfaceSkeleton, TableSkeleton } from '@/components/ui/feedback'

export default function Loading() {
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="fixed inset-x-0 top-0 z-50 h-1 animate-pulse bg-slate-950/85" aria-hidden="true" />
      <div className="mx-auto flex min-h-screen w-full max-w-7xl animate-[page-enter_180ms_ease-out] flex-col px-6 py-6">
        <div className="flex flex-col gap-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <SurfaceSkeleton lines={3} />
          <StatSkeletonGrid count={3} />
          <TableSkeleton rows={6} columns={5} />
        </div>
      </div>
    </div>
  )
}
