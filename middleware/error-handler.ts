import { randomUUID } from 'node:crypto';
import { NextFunction, Request, RequestHandler, Response } from 'express';

export type ApiErrorDetail = {
  field?: string;
  reason: string;
};

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details: ApiErrorDetail[] = [],
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function getTraceId(req: Request): string {
  const incomingTraceId = req.headers['x-trace-id'];
  if (typeof incomingTraceId === 'string' && incomingTraceId.length > 0) {
    return incomingTraceId;
  }
  return randomUUID().replace(/-/g, '').slice(0, 16);
}

export function sendApiError(req: Request, res: Response, error: ApiError): void {
  res.status(error.status).json({
    error: {
      code: error.code,
      message: error.message,
      details: error.details,
      traceId: getTraceId(req),
    },
  });
}

export function errorHandler(error: unknown, req: Request, res: Response, _next: NextFunction): void {
  if (error instanceof ApiError) {
    sendApiError(req, res, error);
    return;
  }

  res.status(500).json({
    error: {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'Unexpected server failure.',
      details: [],
      traceId: getTraceId(req),
    },
  });
}

export function withErrorHandling(handler: RequestHandler): RequestHandler {
  return (req, res, next) => {
    Promise.resolve(handler(req, res, next)).catch(next);
  };
}
