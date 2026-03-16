import { randomUUID } from 'node:crypto';
import { NextFunction, Request, RequestHandler, Response } from 'express';

export type ValidationDetail = {
  field: string;
  reason: string;
};

export class RequestValidationError extends Error {
  constructor(
    public readonly details: ValidationDetail[],
    message = 'One or more fields are invalid.',
  ) {
    super(message);
    this.name = 'RequestValidationError';
  }
}

function getTraceId(req: Request): string {
  const incomingTraceId = req.headers['x-trace-id'];

  if (typeof incomingTraceId === 'string' && incomingTraceId.length > 0) {
    return incomingTraceId;
  }

  return randomUUID().replace(/-/g, '').slice(0, 16);
}

function sendValidationError(
  req: Request,
  res: Response,
  details: ValidationDetail[],
  message = 'One or more fields are invalid.',
): void {
  res.status(422).json({
    error: {
      code: 'VALIDATION_ERROR',
      message,
      details,
      traceId: getTraceId(req),
    },
  });
}

function isValidationDetailArray(value: unknown): value is ValidationDetail[] {
  return Array.isArray(value) && value.every((entry) => {
    return (
      entry !== null
      && typeof entry === 'object'
      && typeof (entry as ValidationDetail).field === 'string'
      && typeof (entry as ValidationDetail).reason === 'string'
    );
  });
}

type ValidationTarget = 'body' | 'params' | 'query';

export function validationMiddleware<T>(
  validator: (value: unknown, req: Request) => T,
  target: ValidationTarget = 'body',
): RequestHandler {
  return (req: Request, res: Response, next: NextFunction): void => {
    try {
      const validated = validator(req[target], req);
      (req as Record<ValidationTarget, unknown>)[target] = validated;
      next();
    } catch (error) {
      if (error instanceof RequestValidationError) {
        sendValidationError(req, res, error.details, error.message);
        return;
      }

      if (error instanceof Error && 'details' in error && isValidationDetailArray(error.details)) {
        sendValidationError(req, res, error.details, error.message);
        return;
      }

      sendValidationError(req, res, [
        {
          field: target,
          reason: 'is invalid',
        },
      ]);
    }
  };
}
