import AppShell from '@/components/hrms/shell/app-shell'
import { NotificationsPage } from '@/components/surfaces/notifications-page'

export default function NotificationsRoute() {
  return (
    <AppShell pageTitle="Notifications" pageDescription="Review event-driven inbox items, delivery outcomes, and suppressed channels in one place.">
      <NotificationsPage />
    </AppShell>
  )
}
