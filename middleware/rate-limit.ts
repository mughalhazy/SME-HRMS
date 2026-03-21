import { Request, RequestHandler, Response } from 'express';
import { getTraceId } from './error-handler';
import { normalizeTenantId } from './tenant-context';

type RateLimitKey = string;

type RateLimitWindow = {
  count: number;
  resetAt: number;
};

export type RateLimitWindowConfig = {
  windowMs: number;
  maxRequests: number;
};

export type CompositeRateLimitConfig = {
  tenantBurst?: RateLimitWindowConfig;
  tenantSustained?: RateLimitWindowConfig;
  userBurst?: RateLimitWindowConfig;
  userSustained?: RateLimitWindowConfig;
  abusiveClientBurst?: RateLimitWindowConfig;
};

export type RateLimitOptions = {
  windowMs: number;
  maxRequests: number;
  keyPrefix?: string;
  keyGenerator?: (req: Request) => string;
  skip?: (req: Request) => boolean;
  configResolver?: (req: Request) => Partial<CompositeRateLimitConfig> | undefined;
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

function resolvePolicy(req: Request, options: RateLimitOptions): CompositeRateLimitConfig {
  const fallback = { windowMs: options.windowMs, maxRequests: options.maxRequests };
  const overrides = options.configResolver?.(req) ?? {};

  return {
    tenantBurst: overrides.tenantBurst ?? fallback,
    tenantSustained: overrides.tenantSustained,
    userBurst: overrides.userBurst ?? fallback,
    userSustained: overrides.userSustained,
    abusiveClientBurst: overrides.abusiveClientBurst,
  };
}

function setHeaders(res: Response, maxRequests: number, remaining: number, resetAt: number, scope: string): void {
  const resetSeconds = Math.max(0, Math.ceil((resetAt - Date.now()) / 1000));
  res.setHeader('X-RateLimit-Limit', String(maxRequests));
  res.setHeader('X-RateLimit-Remaining', String(Math.max(0, remaining)));
  res.setHeader('X-RateLimit-Reset', String(resetSeconds));
  res.setHeader('X-RateLimit-Scope', scope);
}

function incrementWindow(bucketKey: string, config: RateLimitWindowConfig, now: number): { allowed: boolean; remaining: number; resetAt: number } {
  const current = windows.get(bucketKey);

  if (!current || current.resetAt <= now) {
    const resetAt = now + config.windowMs;
    windows.set(bucketKey, { count: 1, resetAt });
    return { allowed: true, remaining: config.maxRequests - 1, resetAt };
  }

  current.count += 1;
  return {
    allowed: current.count <= config.maxRequests,
    remaining: config.maxRequests - current.count,
    resetAt: current.resetAt,
  };
}

function resolveSubjects(req: Request): { tenantId: string; userKey: string; clientKey: string } {
  const tenantId = normalizeTenantId(req.tenantId ?? (typeof req.headers['x-tenant-id'] === 'string' ? req.headers['x-tenant-id'] : undefined));
  const actorId = typeof req.auth?.employee_id === 'string' && req.auth.employee_id.length > 0
    ? req.auth.employee_id
    : typeof req.auth?.sub === 'string' && req.auth.sub.length > 0
      ? req.auth.sub
      : typeof req.headers['x-actor-id'] === 'string' && req.headers['x-actor-id'].length > 0
        ? req.headers['x-actor-id']
        : 'anonymous';

  return {
    tenantId,
    userKey: `${tenantId}:${actorId}`,
    clientKey: `${tenantId}:${getClientAddress(req)}`,
  };
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

    const policy = resolvePolicy(req, options);
    const subjects = resolveSubjects(req);
    const routeKey = `${req.method}:${req.route?.path ?? req.path}:${keyGenerator(req)}`;
    const checks: Array<{ scope: string; subject: string; config?: RateLimitWindowConfig }> = [
      { scope: 'tenant-burst', subject: subjects.tenantId, config: policy.tenantBurst },
      { scope: 'tenant-sustained', subject: subjects.tenantId, config: policy.tenantSustained },
      { scope: 'user-burst', subject: subjects.userKey, config: policy.userBurst },
      { scope: 'user-sustained', subject: subjects.userKey, config: policy.userSustained },
      { scope: 'abusive-client-burst', subject: subjects.clientKey, config: policy.abusiveClientBurst },
    ];

    for (const check of checks) {
      if (!check.config) {
        continue;
      }

      const bucketKey = `${keyPrefix}:${check.scope}:${routeKey}:${check.subject}`;
      const decision = incrementWindow(bucketKey, check.config, now);
      setHeaders(res, check.config.maxRequests, decision.remaining, decision.resetAt, check.scope);

      if (!decision.allowed) {
        res.status(429).json({
          error: {
            code: 'RATE_LIMIT_EXCEEDED',
            message: 'Rate limit exceeded. Please retry later.',
            details: [
              {
                field: 'request',
                reason: `${check.scope} allows ${check.config.maxRequests} requests per ${check.config.windowMs}ms window`,
              },
              {
                field: 'tenant_id',
                reason: subjects.tenantId,
              },
            ],
            traceId: getTraceId(req),
          },
        });
        return;
      }
    }

    next();
  };
}
