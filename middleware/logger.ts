import { NextFunction, Request, RequestHandler, Response } from 'express';

export type StructuredLogRecord = {
  timestamp: string;
  level: 'INFO' | 'ERROR';
  service: string;
  event: string;
  traceId: string;
  message: string;
  context: Record<string, unknown>;
};

export class StructuredLogger {
  readonly records: StructuredLogRecord[] = [];

  constructor(private readonly serviceName: string) {}

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

  audit(action: string, traceId: string, context: Record<string, unknown> = {}): StructuredLogRecord {
    return this.write('INFO', 'audit', traceId, action, context);
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
