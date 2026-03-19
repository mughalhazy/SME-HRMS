import AppShell from '@/components/hrms/shell/app-shell'
import { PerformanceReviewsPage } from '@/components/surfaces/performance-reviews-page'

export default function PerformanceRoute() {
  return (
    <AppShell pageTitle="Performance" pageDescription="Review cycle progress, calibration status, and manager follow-up across the business.">
      <PerformanceReviewsPage />
    </AppShell>
  )
}
