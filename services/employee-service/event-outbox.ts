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
  BusinessUnitCreated: 'organization.business_unit.created',
  BusinessUnitUpdated: 'organization.business_unit.updated',
  LegalEntityCreated: 'organization.legal_entity.created',
  LegalEntityUpdated: 'organization.legal_entity.updated',
  LocationCreated: 'organization.location.created',
  LocationUpdated: 'organization.location.updated',
  CostCenterCreated: 'organization.cost_center.created',
  CostCenterUpdated: 'organization.cost_center.updated',
  GradeBandCreated: 'organization.grade_band.created',
  GradeBandUpdated: 'organization.grade_band.updated',
  JobPositionCreated: 'organization.job_position.created',
  JobPositionUpdated: 'organization.job_position.updated',
  DocumentStored: 'employee.document.stored',
  DocumentUpdated: 'employee.document.updated',
  ContractActivated: 'employee.contract.activated',
  PolicyAcknowledged: 'employee.policy.acknowledged',
  DocumentExpiryTracked: 'employee.document.expiry.tracked',
  ComplianceTaskCreated: 'employee.compliance.task.created',
  ComplianceTaskAssigned: 'employee.compliance.task.assigned',
  ComplianceTaskCompleted: 'employee.compliance.task.completed',
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
