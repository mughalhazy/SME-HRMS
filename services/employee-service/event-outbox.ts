export type CanonicalEvent = {
  event_id: string;
  event_type: string;
  tenant_id: string;
  timestamp: string;
  source: string;
  data: Record<string, unknown>;
  metadata: {
    version: 'v1';
    correlation_id: string;
    idempotency_key?: string;
  };
  legacy_event_name: string;
};

const EVENT_TYPES: Record<string, string> = {
  EmployeeCreated: 'employee.created',
  EmployeeUpdated: 'employee.updated',
  EmployeeStatusChanged: 'employee.status.changed',
};

export class EmployeeEventOutbox {
  readonly events: CanonicalEvent[] = [];
  readonly outbox: CanonicalEvent[] = [];

  enqueue(legacyEventName: keyof typeof EVENT_TYPES, tenantId: string, data: Record<string, unknown>, idempotencyKey?: string): CanonicalEvent {
    const event: CanonicalEvent = {
      event_id: randomUUID(),
      event_type: EVENT_TYPES[legacyEventName],
      tenant_id: tenantId,
      timestamp: new Date().toISOString(),
      source: 'employee-service',
      data,
      metadata: {
        version: 'v1',
        correlation_id: randomUUID(),
        idempotency_key: idempotencyKey,
      },
      legacy_event_name: legacyEventName,
    };
    this.outbox.push(event);
    return event;
  }

  dispatchPending(): CanonicalEvent[] {
    const pending = this.outbox.splice(0, this.outbox.length);
    this.events.push(...pending);
    return pending;
  }
}
import { randomUUID } from 'node:crypto';
