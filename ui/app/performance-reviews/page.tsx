import { AppShell } from '@/components/shared/app-shell'
import { PerformanceReviewsPage } from '@/components/surfaces/performance-reviews-page'

export default function PerformanceReviewsRoute() {
  return (
    <AppShell currentPath="/performance-reviews">
      <PerformanceReviewsPage />
    </AppShell>
  )
}
