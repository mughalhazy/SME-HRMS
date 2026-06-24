import { randomUUID } from 'node:crypto';
import { NextFunction, Request, RequestHandler, Response } from 'express';
import type { AuditActor, AuditRecord } from './audit';
import { appendCentralizedAuditRecord } from './audit-store';

const SENSITIVE_FIELD_NAMES = new Set([
  'password',
  'password_hash',
  'refresh_token',
  'refresh_token_hash',
  'token_hash',
  'access_token',
  'authorization',
  'secret',
  'bank_account',
  'bank_account_number',
  'routing_number',
  'tax_id',
  'ssn',
]);

export type StructuredLogRecord = {
  timestamp: string;
  level: 'INFO' | 'ERROR';
  service: string;
  event: string;
  action: string;
  status: string;
  requestId: string;
  traceId: string;
  correlationId: string;
  tenantId?: string;
  message: string;
  context: Record<string, unknown>;
};

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

export interface AuditLogInput {
  traceId: string;
  tenantId: string;
  actor: AuditActor;
  action: string;
  entity: string;
  entityId: string;
  before: Record<string, unknown>;
  after: Record<string, unknown>;
}

export function sanitizeLogContext<T>(value: T): T {
  if (Array.isArray(value)) {
    return value.map((item) => sanitizeLogContext(item)) as T;
  }

  if (!value || typeof value !== 'object') {
    return value;
  }

  const result: Record<string, unknown> = {};
  for (const [key, item] of Object.entries(value as Record<string, unknown>)) {
    result[key] = SENSITIVE_FIELD_NAMES.has(key.toLowerCase()) ? '[REDACTED]' : sanitizeLogContext(item);
  }
  return result as T;
}

function resolveTenantId(context: Record<string, unknown>): string | undefined {
  const raw = context.tenantId ?? context.tenant_id;
  return typeof raw === 'string' && raw.trim().length > 0 ? raw.trim() : undefined;
}

function resolveCorrelationId(traceId: string, context: Record<string, unknown>): string {
  const raw = context.correlationId ?? context.correlation_id ?? context.requestId ?? context.request_id ?? context.traceId ?? context.trace_id;
  return typeof raw === 'string' && raw.trim().length > 0 ? raw.trim() : traceId;
}

export class StructuredLogger {
  readonly records: StructuredLogRecord[] = [];
  private readonly auditRecordsInternal: AuditRecord[] = [];

  constructor(private readonly serviceName: string) {}

  get auditRecords(): readonly AuditRecord[] {
    return Object.freeze([...this.auditRecordsInternal]);
  }

  private write(
    level: 'INFO' | 'ERROR',
    event: string,
    traceId: string,
    message: string,
    context: Record<string, unknown> = {},
    overrides: { action?: string; status?: string; tenantId?: string; correlationId?: string } = {},
  ): StructuredLogRecord {
    const sanitizedContext = sanitizeLogContext(context);
    const record: StructuredLogRecord = {
      timestamp: new Date().toISOString(),
      level,
      service: this.serviceName,
      event,
      action: overrides.action ?? (typeof sanitizedContext.action === 'string' ? sanitizedContext.action : event),
      status: overrides.status ?? (typeof sanitizedContext.status === 'string' ? sanitizedContext.status : level === 'ERROR' ? 'error' : 'ok'),
      requestId: traceId,
      traceId,
      correlationId: overrides.correlationId ?? resolveCorrelationId(traceId, sanitizedContext),
      tenantId: overrides.tenantId ?? resolveTenantId(sanitizedContext),
      message,
      context: sanitizedContext,
    };
    this.records.push(record);
    if (this.records.length > 500) {
      this.records.shift();
    }
    process.stdout.write(`${JSON.stringify(record)}\n`);
    return record;
  }

  info(
    event: string,
    traceId: string,
    message: string,
    context: Record<string, unknown> = {},
    overrides: { action?: string; status?: string; tenantId?: string; correlationId?: string } = {},
  ): StructuredLogRecord {
    return this.write('INFO', event, traceId, message, context, overrides);
  }

  error(
    event: string,
    traceId: string,
    message: string,
    context: Record<string, unknown> = {},
    overrides: { action?: string; status?: string; tenantId?: string; correlationId?: string } = {},
  ): StructuredLogRecord {
    return this.write('ERROR', event, traceId, message, context, { status: 'error', ...overrides });
  }

  audit(input: AuditLogInput): AuditRecord {
    const record: AuditRecord = Object.freeze({
      audit_id: randomUUID(),
      tenant_id: input.tenantId,
      actor: deepFreeze({ ...input.actor }),
      action: input.action,
      entity: input.entity,
      entity_id: input.entityId,
      before: deepFreeze(sanitizeLogContext(input.before)),
      after: deepFreeze(sanitizeLogContext(input.after)),
      timestamp: new Date().toISOString(),
      trace_id: input.traceId,
    });

    this.auditRecordsInternal.push(record);
    appendCentralizedAuditRecord(record, this.serviceName);
    this.write('INFO', 'audit', input.traceId, input.action, { audit_record: record, tenantId: input.tenantId }, {
      action: input.action,
      status: 'success',
      tenantId: input.tenantId,
      correlationId: input.traceId,
    });
    return record;
  }
}

const loggers = new Map<string, StructuredLogger>();

export function getStructuredLogger(serviceName: string): StructuredLogger {
  const existing = loggers.get(serviceName);
  if (existing) {
    return existing;
  }
  const logger = new StructuredLogger(serviceName);
  loggers.set(serviceName, logger);
  return logger;
}

function resolveRequestTenant(req: Request): string | undefined {
  const headerTenant = typeof req.headers['x-tenant-id'] === 'string'
    ? req.headers['x-tenant-id']
    : typeof req.headers['x-tenant'] === 'string'
      ? req.headers['x-tenant']
      : undefined;
  const bodyTenant = req.body && typeof req.body === 'object' && typeof req.body.tenant_id === 'string'
    ? req.body.tenant_id
    : undefined;
  return req.tenantId ?? headerTenant ?? bodyTenant;
}

function resolveCorrelationIdFromRequest(req: Request): string {
  const headerCorrelationId = typeof req.headers['x-correlation-id'] === 'string' && req.headers['x-correlation-id'].length > 0
    ? req.headers['x-correlation-id']
    : undefined;
  return headerCorrelationId ?? req.traceId ?? 'missing-trace-id';
}

export function createLoggerMiddleware(serviceName: string): RequestHandler {
  const logger = getStructuredLogger(serviceName);
  return (req: Request, res: Response, next: NextFunction): void => {
    const startedAt = process.hrtime.bigint();
    const requestId = req.traceId ?? 'missing-trace-id';
    const tenantId = resolveRequestTenant(req);
    const correlationId = resolveCorrelationIdFromRequest(req);
    logger.info('request.started', requestId, `${req.method} ${req.originalUrl}`, {
      method: req.method,
      path: req.originalUrl,
      tenantId,
      correlationId,
    }, {
      action: `${req.method} ${req.path}`,
      status: 'started',
      tenantId,
      correlationId,
    });
    res.on('finish', () => {
      const latencyMs = Number(process.hrtime.bigint() - startedAt) / 1_000_000;
      logger.info('request.completed', requestId, `${req.method} ${req.originalUrl}`, {
        method: req.method,
        path: req.originalUrl,
        statusCode: res.statusCode,
        latencyMs: Number(latencyMs.toFixed(3)),
        tenantId,
        correlationId,
      }, {
        action: `${req.method} ${req.path}`,
        status: String(res.statusCode),
        tenantId,
        correlationId,
      });
    });
    next();
  };
}
