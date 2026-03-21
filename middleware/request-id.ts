import { randomUUID } from 'node:crypto';
import { NextFunction, Request, RequestHandler, Response } from 'express';

export function generateRequestId(): string {
  return randomUUID().replace(/-/g, '').slice(0, 16);
}

export function getRequestId(req: Request): string {
  return req.traceId
    ?? (typeof req.headers['x-request-id'] === 'string' && req.headers['x-request-id'].length > 0 ? req.headers['x-request-id'] : undefined)
    ?? (typeof req.headers['x-trace-id'] === 'string' && req.headers['x-trace-id'].length > 0 ? req.headers['x-trace-id'] : undefined)
    ?? (typeof req.headers['x-correlation-id'] === 'string' && req.headers['x-correlation-id'].length > 0 ? req.headers['x-correlation-id'] : undefined)
    ?? generateRequestId();
}

export const requestIdMiddleware: RequestHandler = (req: Request, res: Response, next: NextFunction): void => {
  const traceId = getRequestId(req);
  req.traceId = traceId;
  req.headers['x-request-id'] = traceId;
  req.headers['x-trace-id'] = traceId;
  if (typeof req.headers['x-correlation-id'] !== 'string' || req.headers['x-correlation-id'].length === 0) {
    req.headers['x-correlation-id'] = traceId;
  }
  res.setHeader('X-Request-Id', traceId);
  res.setHeader('X-Trace-Id', traceId);
  res.setHeader('X-Correlation-Id', typeof req.headers['x-correlation-id'] === 'string' ? req.headers['x-correlation-id'] : traceId);
  next();
};

declare global {
  namespace Express {
    interface Request {
      traceId?: string;
    }
  }
}
