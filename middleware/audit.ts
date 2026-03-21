import { Request } from 'express';
import type { StructuredLogger } from './logger';

export type AuditActorType = 'user' | 'service' | 'system';

export interface AuditActor {
  id: string;
  type: AuditActorType;
  role?: string;
  department_id?: string;
}

export interface AuditRecord {
  audit_id: string;
  tenant_id: string;
  actor: AuditActor;
  action: string;
  entity: string;
  entity_id: string;
  before: Record<string, unknown>;
  after: Record<string, unknown>;
  timestamp: string;
  trace_id: string;
}

export interface AuditMutationContext {
  logger: StructuredLogger;
  req: Request;
  tenantId?: string;
  action: string;
  entity: string;
  entityId: string;
  before?: unknown;
  after?: unknown;
}

function cloneObject(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object') {
    return {};
  }

  return JSON.parse(JSON.stringify(value)) as Record<string, unknown>;
}

function deepFreeze<T>(value: T): T {
  if (!value || typeof value !== 'object' || Object.isFrozen(value)) {
    return value;
  }

  const entries = Array.isArray(value) ? value : Object.values(value as Record<string, unknown>);
  for (const entry of entries) {
    deepFreeze(entry);
  }

  return Object.freeze(value);
}

export function resolveAuditActor(req: Request): AuditActor {
  if (req.auth) {
    return {
      id: req.auth.employee_id ?? req.auth.role,
      type: 'user',
      role: req.auth.role,
      department_id: req.auth.department_id,
    };
  }

  const actorIdHeader = req.headers['x-actor-id'];
  const actorTypeHeader = req.headers['x-actor-type'];
  const actorRoleHeader = req.headers['x-actor-role'];
  const actorDepartmentHeader = req.headers['x-actor-department-id'];

  const actorType = actorTypeHeader === 'user' || actorTypeHeader === 'service' || actorTypeHeader === 'system'
    ? actorTypeHeader
    : 'system';

  return {
    id: typeof actorIdHeader === 'string' && actorIdHeader.trim() !== '' ? actorIdHeader : 'system',
    type: actorType,
    role: typeof actorRoleHeader === 'string' && actorRoleHeader.trim() !== '' ? actorRoleHeader : undefined,
    department_id: typeof actorDepartmentHeader === 'string' && actorDepartmentHeader.trim() !== '' ? actorDepartmentHeader : undefined,
  };
}

export function logAuditMutation(context: AuditMutationContext): AuditRecord {
  const before = cloneObject(context.before);
  const after = cloneObject(context.after);
  const tenantId = context.tenantId
    ?? (typeof after.tenant_id === 'string' ? after.tenant_id : undefined)
    ?? (typeof before.tenant_id === 'string' ? before.tenant_id : undefined)
    ?? 'tenant-default';

  return context.logger.audit({
    traceId: context.req.traceId ?? 'missing-trace-id',
    tenantId,
    actor: resolveAuditActor(context.req),
    action: context.action,
    entity: context.entity,
    entityId: context.entityId,
    before: deepFreeze(before),
    after: deepFreeze(after),
  });
}
