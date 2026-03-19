import AppShell from '@/components/hrms/shell/app-shell'
import { SurfaceSkeleton, StatSkeletonGrid } from '@/components/ui/feedback'

export default function EmployeeDetailLoading() {
  return (
    <AppShell pageTitle="Employee Profile" pageDescription="Loading employee context, profile details, and related workspace data.">
      <div className="flex flex-col gap-6">
        <SurfaceSkeleton lines={4} />
        <StatSkeletonGrid count={4} />
        <SurfaceSkeleton lines={6} />
      </div>
    </AppShell>
  )
}
