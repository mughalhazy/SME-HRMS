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
  traceId: string;
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

export class StructuredLogger {
  readonly records: StructuredLogRecord[] = [];
  private readonly auditRecordsInternal: AuditRecord[] = [];

  constructor(private readonly serviceName: string) {}

  get auditRecords(): readonly AuditRecord[] {
    return Object.freeze([...this.auditRecordsInternal]);
  }

  private write(level: 'INFO' | 'ERROR', event: string, traceId: string, message: string, context: Record<string, unknown> = {}): StructuredLogRecord {
    const record: StructuredLogRecord = {
      timestamp: new Date().toISOString(),
      level,
      service: this.serviceName,
      event,
      traceId,
      message,
      context: sanitizeLogContext(context),
    };
    this.records.push(record);
    if (this.records.length > 500) {
      this.records.shift();
    }
    process.stdout.write(`${JSON.stringify(record)}\n`);
    return record;
  }

  info(event: string, traceId: string, message: string, context: Record<string, unknown> = {}): StructuredLogRecord {
    return this.write('INFO', event, traceId, message, context);
  }

  error(event: string, traceId: string, message: string, context: Record<string, unknown> = {}): StructuredLogRecord {
    return this.write('ERROR', event, traceId, message, context);
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
    this.write('INFO', 'audit', input.traceId, input.action, { audit_record: record });
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

export function createLoggerMiddleware(serviceName: string): RequestHandler {
  const logger = getStructuredLogger(serviceName);
  return (req: Request, res: Response, next: NextFunction): void => {
    const startedAt = process.hrtime.bigint();
    logger.info('request.started', req.traceId ?? 'missing-trace-id', `${req.method} ${req.originalUrl}`, {
      method: req.method,
      path: req.originalUrl,
    });
    res.on('finish', () => {
      const latencyMs = Number(process.hrtime.bigint() - startedAt) / 1_000_000;
      logger.info('request.completed', req.traceId ?? 'missing-trace-id', `${req.method} ${req.originalUrl}`, {
        method: req.method,
        path: req.originalUrl,
        statusCode: res.statusCode,
        latencyMs: Number(latencyMs.toFixed(3)),
      });
    });
    next();
  };
}
