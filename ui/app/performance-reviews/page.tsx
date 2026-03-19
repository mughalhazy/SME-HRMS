import { PerformanceReviewsPage } from '@/components/surfaces/performance-reviews-page'
import AppShell from '@/components/hrms/shell/app-shell'

export default function PerformanceReviewsRoute() {
  return (
    <AppShell pageTitle="Performance" pageDescription="Review cycle progress, calibration status, and manager follow-up across the business.">
      <PerformanceReviewsPage />
    </AppShell>
  )
}
