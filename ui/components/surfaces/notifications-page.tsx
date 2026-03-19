'use client'

import { useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { BellRing, CheckCheck, MailWarning, RefreshCw, ShieldCheck } from 'lucide-react'

import { EmptyState, ErrorState, StatSkeletonGrid, TableSkeleton } from '@/components/ui/feedback'
import { Button } from '@/components/ui/button'
import { PageGrid, PageHero, PageStack, SectionHeading, StatCard } from '@/components/ui/page'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { apiRequest } from '@/lib/api/client'

const CURRENT_SUBJECT_ID = 'emp-004'

type InboxItem = {
  message_id: string
  event_name: string
  topic_code: string
  status: string
  title: string
  body: string
  queued_at: string
  read_at: string | null
  unread: boolean
}

type InboxResponse = {
  data: {
    subject_id: string
    items: InboxItem[]
    summary: {
      total: number
      unread: number
      sent: number
      suppressed: number
    }
  }
}

type DeliveryRow = {
  message_id: string
  template_code: string | null
  subject_id: string
  channel: string
  destination: string
  status: string
  queued_at: string
  sent_at: string | null
  failure_reason: string | null
  last_provider_name: string | null
  last_attempt_outcome: string | null
}

type DeliveryResponse = {
  data: DeliveryRow[]
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export function NotificationsPage() {
  const queryClient = useQueryClient()

  const inboxQuery = useQuery({
    queryKey: ['notifications', 'inbox', CURRENT_SUBJECT_ID],
    queryFn: () => apiRequest<InboxResponse>(`/api/v1/notifications/inbox/${CURRENT_SUBJECT_ID}`),
  })

  const deliveryQuery = useQuery({
    queryKey: ['notifications', 'delivery', CURRENT_SUBJECT_ID],
    queryFn: () => apiRequest<DeliveryResponse>(`/api/v1/notifications/delivery?subject_id=${CURRENT_SUBJECT_ID}`),
  })

  const inbox = inboxQuery.data?.data
  const deliveryRows = deliveryQuery.data?.data ?? []

  const stats = useMemo(
    () => [
      {
        label: 'Inbox items',
        value: String(inbox?.summary.total ?? 0),
        hint: 'In-app notifications routed from domain events',
        icon: BellRing,
      },
      {
        label: 'Unread now',
        value: String(inbox?.summary.unread ?? 0),
        hint: 'Actionable or newly delivered messages',
        icon: MailWarning,
      },
      {
        label: 'Delivered',
        value: String(inbox?.summary.sent ?? 0),
        hint: 'Successfully routed into the inbox',
        icon: ShieldCheck,
      },
      {
        label: 'Suppressed',
        value: String(deliveryRows.filter((row) => row.status === 'Suppressed').length),
        hint: 'Preference-based channel suppression',
        icon: CheckCheck,
      },
    ],
    [deliveryRows, inbox],
  )

  const refreshAll = async () => {
    await Promise.all([inboxQuery.refetch(), deliveryQuery.refetch()])
  }

  const markRead = async (messageId: string) => {
    await apiRequest(`/api/v1/notifications/inbox/${CURRENT_SUBJECT_ID}/read/${messageId}`, { method: 'POST' })
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['notifications', 'inbox', CURRENT_SUBJECT_ID] }),
      queryClient.invalidateQueries({ queryKey: ['notifications', 'delivery', CURRENT_SUBJECT_ID] }),
    ])
  }

  return (
    <PageStack>
      <PageHero
        eyebrow="Notifications"
        title="Route operational events into one user inbox"
        description="Domain events from leave, payroll, hiring, and security workflows are translated into inbox-ready notifications with delivery visibility and suppression context."
        actions={
          <Button variant="outline" onClick={refreshAll} disabled={inboxQuery.isFetching || deliveryQuery.isFetching}>
            <RefreshCw className={`h-4 w-4 ${(inboxQuery.isFetching || deliveryQuery.isFetching) ? 'animate-spin' : ''}`} />
            Refresh inbox
          </Button>
        }
      />

      {inboxQuery.isLoading || deliveryQuery.isLoading ? (
        <>
          <StatSkeletonGrid count={4} />
          <TableSkeleton rows={5} columns={4} />
        </>
      ) : inboxQuery.isError ? (
        <ErrorState title="Unable to load notification inbox" message={inboxQuery.error.message} onRetry={refreshAll} />
      ) : deliveryQuery.isError ? (
        <ErrorState title="Unable to load delivery log" message={deliveryQuery.error.message} onRetry={refreshAll} />
      ) : (
        <>
          <PageGrid className="md:grid-cols-2 xl:grid-cols-4">
            {stats.map((stat) => (
              <StatCard key={stat.label} title={stat.label} value={stat.value} hint={stat.hint} icon={stat.icon} />
            ))}
          </PageGrid>

          <section className="overflow-hidden rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-surface)]">
            <SectionHeading
              title="User inbox"
              description="In-app messages generated from upstream events stay readable, auditable, and quick to clear."
              badge={<span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">Canonical surface: Notification inbox</span>}
            />

            {(inbox?.items.length ?? 0) === 0 ? (
              <div className="p-5">
                <EmptyState icon={BellRing} title="No inbox items" message="Once upstream services emit routed events, they will appear here for the current user." />
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Message</TableHead>
                    <TableHead>Topic</TableHead>
                    <TableHead>Received</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {inbox?.items.map((item) => (
                    <TableRow key={item.message_id}>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-slate-950">{item.title}</p>
                            {item.unread ? <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-blue-700">Unread</span> : null}
                          </div>
                          <p className="max-w-2xl text-sm text-slate-600">{item.body}</p>
                          {item.unread ? (
                            <Button variant="ghost" className="h-auto px-0 py-0 text-sm font-medium text-blue-600 hover:bg-transparent hover:text-blue-700" onClick={() => markRead(item.message_id)}>
                              Mark as read
                            </Button>
                          ) : null}
                        </div>
                      </TableCell>
                      <TableCell className="text-sm text-slate-600">{item.topic_code}</TableCell>
                      <TableCell className="text-sm text-slate-600">{formatDateTime(item.queued_at)}</TableCell>
                      <TableCell>
                        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${item.status === 'Sent' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                          {item.status}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </section>

          <section className="overflow-hidden rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-surface)]">
            <SectionHeading
              title="Delivery log"
              description="Trace every routed message back to its channel decision and latest delivery outcome."
              badge={<span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">Read model: notification_delivery_view</span>}
            />

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Channel</TableHead>
                  <TableHead>Destination</TableHead>
                  <TableHead>Queued</TableHead>
                  <TableHead>Outcome</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {deliveryRows.map((row) => (
                  <TableRow key={row.message_id}>
                    <TableCell>
                      <div>
                        <p className="font-medium text-slate-950">{row.channel}</p>
                        <p className="text-sm text-slate-500">{row.template_code ?? 'direct notification'}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-slate-600">{row.destination}</TableCell>
                    <TableCell className="text-sm text-slate-600">{formatDateTime(row.queued_at)}</TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${row.status === 'Sent' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                          {row.status}
                        </span>
                        <p className="text-xs text-slate-500">{row.failure_reason ?? row.last_provider_name ?? 'Delivered successfully'}</p>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </section>
        </>
      )}
    </PageStack>
  )
}
