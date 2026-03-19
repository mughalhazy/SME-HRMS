import { JobPostingsPage } from '@/components/surfaces/job-postings-page'
import AppShell from '@/components/hrms/shell/app-shell'

export default function JobPostingsRoute() {
  return (
    <AppShell pageTitle="Jobs" pageDescription="Manage open requisitions, monitor posting health, and keep recruiting activity visible.">
      <JobPostingsPage />
    </AppShell>
  )
}
