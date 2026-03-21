import { randomUUID } from 'node:crypto';
import { NextFunction, Request, RequestHandler, Response } from 'express';
import type { AuditActor, AuditRecord } from './audit';
import { appendCentralizedAuditRecord } from './audit-store';

export type StructuredLogRecord = {
  timestamp: string;
  level: 'INFO' | 'ERROR';
  service: string;
  event: string;
  traceId: string;
  message: string;
  context: Record<string, unknown>;
};

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
      context,
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
      actor: Object.freeze({ ...input.actor }),
      action: input.action,
      entity: input.entity,
      entity_id: input.entityId,
      before: input.before,
      after: input.after,
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
