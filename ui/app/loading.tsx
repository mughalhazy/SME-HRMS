import AppShell from '@/components/hrms/shell/app-shell'
import { StatSkeletonGrid, SurfaceSkeleton, TableSkeleton } from '@/components/ui/feedback'

export default function Loading() {
  return (
    <AppShell pageTitle="Loading workspace" pageDescription="Preparing the next HRMS route with preserved layout context and loading placeholders.">
      <div className="flex flex-col gap-6 animate-[page-enter_180ms_ease-out]">
        <SurfaceSkeleton lines={3} />
        <StatSkeletonGrid count={3} />
        <TableSkeleton rows={6} columns={5} />
      </div>
    </AppShell>
  )
}
