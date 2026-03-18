import { Request, RequestHandler, Response } from 'express';
import { getTraceId } from './error-handler';

type RateLimitKey = string;

type RateLimitWindow = {
  count: number;
  resetAt: number;
};

export type RateLimitOptions = {
  windowMs: number;
  maxRequests: number;
  keyPrefix?: string;
  keyGenerator?: (req: Request) => string;
  skip?: (req: Request) => boolean;
};

const MAX_TRACKED_WINDOWS = 10_000;
const windows = new Map<RateLimitKey, RateLimitWindow>();

function pruneExpired(now: number): void {
  if (windows.size < MAX_TRACKED_WINDOWS) {
    return;
  }

  for (const [key, window] of windows.entries()) {
    if (window.resetAt <= now) {
      windows.delete(key);
    }
  }
}

function getClientAddress(req: Request): string {
  const forwardedFor = req.headers['x-forwarded-for'];
  if (typeof forwardedFor === 'string' && forwardedFor.length > 0) {
    return forwardedFor.split(',')[0].trim();
  }

  return req.ip || req.socket.remoteAddress || 'unknown';
}

function defaultKeyGenerator(req: Request): string {
  const principal = req.auth?.employee_id ?? req.auth?.role ?? 'anonymous';
  return `${getClientAddress(req)}:${principal}`;
}

function setHeaders(res: Response, maxRequests: number, remaining: number, resetAt: number): void {
  const resetSeconds = Math.max(0, Math.ceil((resetAt - Date.now()) / 1000));
  res.setHeader('X-RateLimit-Limit', String(maxRequests));
  res.setHeader('X-RateLimit-Remaining', String(Math.max(0, remaining)));
  res.setHeader('X-RateLimit-Reset', String(resetSeconds));
}

export function createRateLimitMiddleware(options: RateLimitOptions): RequestHandler {
  const keyPrefix = options.keyPrefix ?? 'global';
  const keyGenerator = options.keyGenerator ?? defaultKeyGenerator;

  return (req, res, next): void => {
    if (options.skip?.(req)) {
      next();
      return;
    }

    const now = Date.now();
    pruneExpired(now);

    const bucketKey = `${keyPrefix}:${req.method}:${req.route?.path ?? req.path}:${keyGenerator(req)}`;
    const current = windows.get(bucketKey);

    if (!current || current.resetAt <= now) {
      const resetAt = now + options.windowMs;
      windows.set(bucketKey, { count: 1, resetAt });
      setHeaders(res, options.maxRequests, options.maxRequests - 1, resetAt);
      next();
      return;
    }

    current.count += 1;
    const remaining = options.maxRequests - current.count;
    setHeaders(res, options.maxRequests, remaining, current.resetAt);

    if (current.count > options.maxRequests) {
      res.status(429).json({
        error: {
          code: 'RATE_LIMIT_EXCEEDED',
          message: 'Rate limit exceeded. Please retry later.',
          details: [
            {
              field: 'request',
              reason: `allowed ${options.maxRequests} requests per ${options.windowMs}ms window`,
            },
          ],
          traceId: getTraceId(req),
        },
      });
      return;
    }

    next();
  };
}
