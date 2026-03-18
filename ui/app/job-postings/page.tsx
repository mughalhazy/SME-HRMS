import { AppShell } from '@/components/shared/app-shell'
import { JobPostingsPage } from '@/components/surfaces/job-postings-page'

export default function JobPostingsRoute() {
  return (
    <AppShell currentPath="/job-postings">
      <JobPostingsPage />
    </AppShell>
  )
}
