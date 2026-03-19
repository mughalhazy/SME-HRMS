import { clone, getMockDb, nowIso, randomId, simulateLatency } from './shared'

export async function getInboxMock(params: { subjectId: string; unreadOnly?: boolean }) {
  await simulateLatency()

  const notifications = getMockDb().notifications
    .filter((item) => item.subject_id === params.subjectId && item.channel === 'InApp')
    .filter((item) => (params.unreadOnly ? item.read_at === null : true))
    .sort((left, right) => right.queued_at.localeCompare(left.queued_at))

  return {
    data: {
      subject_id: params.subjectId,
      items: clone(
        notifications.map((item) => ({
          message_id: item.message_id,
          event_name: item.event_name,
          topic_code: item.topic_code,
          status: item.status,
          title: item.title,
          body: item.body,
          queued_at: item.queued_at,
          read_at: item.read_at,
          unread: item.read_at === null,
        })),
      ),
      summary: {
        total: notifications.length,
        unread: notifications.filter((item) => item.read_at === null).length,
        sent: notifications.filter((item) => item.status === 'Sent').length,
        suppressed: notifications.filter((item) => item.status === 'Suppressed').length,
      },
    },
  }
}

export async function listNotificationDeliveryMock(params: { subjectId?: string; channel?: string; status?: string }) {
  await simulateLatency()

  const notifications = getMockDb().notifications
    .filter((item) => (params.subjectId ? item.subject_id === params.subjectId : true))
    .filter((item) => (params.channel ? item.channel === params.channel : true))
    .filter((item) => (params.status ? item.status === params.status : true))
    .sort((left, right) => right.queued_at.localeCompare(left.queued_at))

  return {
    data: clone(
      notifications.map((item) => ({
        message_id: item.message_id,
        template_id: null,
        template_code: item.topic_code,
        subject_type: item.subject_id.startsWith('cand-') ? 'Candidate' : 'Employee',
        subject_id: item.subject_id,
        channel: item.channel,
        destination: item.destination,
        status: item.status,
        queued_at: item.queued_at,
        sent_at: item.status === 'Sent' ? item.queued_at : null,
        failure_reason: item.status === 'Suppressed' ? 'Suppressed by subject preferences' : null,
        last_provider_name: item.channel === 'InApp' ? 'inbox' : 'mock-provider',
        last_attempt_outcome: item.status,
        attempt_count: 1,
        updated_at: item.updated_at,
      })),
    ),
  }
}

export async function markInboxMessageReadMock(subjectId: string, messageId: string) {
  await simulateLatency()

  const notification = getMockDb().notifications.find((item) => item.subject_id === subjectId && item.message_id === messageId && item.channel === 'InApp')
  if (!notification) {
    throw new Error('Notification inbox item not found')
  }

  notification.read_at = notification.read_at ?? nowIso()
  notification.updated_at = nowIso()

  return {
    data: clone({
      message_id: notification.message_id,
      subject_id: notification.subject_id,
      channel: notification.channel,
      status: notification.status,
      read_at: notification.read_at,
      updated_at: notification.updated_at,
    }),
  }
}

export async function ingestNotificationEventMock(payload: Record<string, unknown>) {
  await simulateLatency()

  const subjectId = String(payload.subject_id ?? payload.employee_id ?? payload.candidate_id ?? 'emp-004')
  const eventName = String(payload.event_name ?? 'NotificationQueued')
  const messageId = randomId('msg')
  const queuedAt = nowIso()

  getMockDb().notifications.unshift({
    message_id: messageId,
    subject_id: subjectId,
    subject_name: String(payload.subject_name ?? 'Inbox recipient'),
    event_name: eventName,
    topic_code: String(payload.topic_code ?? 'notifications.general'),
    channel: 'InApp',
    destination: `inbox:${subjectId}`,
    status: 'Sent',
    title: String(payload.title ?? 'New notification'),
    body: String(payload.body ?? 'A new event was routed into your inbox.'),
    queued_at: queuedAt,
    read_at: null,
    updated_at: queuedAt,
  })

  return {
    data: {
      event_name: eventName,
      notifications: [
        {
          message_id: messageId,
          subject_id: subjectId,
          channel: 'InApp',
          status: 'Sent',
          queued_at: queuedAt,
        },
      ],
      count: 1,
    },
  }
}
