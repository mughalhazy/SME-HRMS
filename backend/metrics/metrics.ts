import { NextFunction, Request, RequestHandler, Response } from 'express';

export type RequestMetric = {
  traceId: string;
  requestId: string;
  correlationId: string;
  tenantId?: string;
  method: string;
  route: string;
  statusCode: number;
  status: string;
  latencyMs: number;
  success: boolean;
  recordedAt: string;
};

export class ServiceMetrics {
  private requestCount = 0;
  private errorCount = 0;
  private latencyTotalMs = 0;
  private maxLatencyMs = 0;
  private readonly recentRequests: RequestMetric[] = [];
  private readonly routeMetrics = new Map<string, { count: number; errors: number; latencyTotalMs: number; maxLatencyMs: number }>();
  private readonly tenantMetrics = new Map<string, { requests: number; errors: number }>();

  constructor(private readonly serviceName: string) {}

  record(metric: RequestMetric): void {
    this.requestCount += 1;
    if (!metric.success) {
      this.errorCount += 1;
    }
    this.latencyTotalMs += metric.latencyMs;
    this.maxLatencyMs = Math.max(this.maxLatencyMs, metric.latencyMs);
    this.recentRequests.push(metric);
    if (this.recentRequests.length > 50) {
      this.recentRequests.shift();
    }

    const routeBucket = this.routeMetrics.get(metric.route) ?? { count: 0, errors: 0, latencyTotalMs: 0, maxLatencyMs: 0 };
    routeBucket.count += 1;
    routeBucket.latencyTotalMs += metric.latencyMs;
    routeBucket.maxLatencyMs = Math.max(routeBucket.maxLatencyMs, metric.latencyMs);
    if (!metric.success) {
      routeBucket.errors += 1;
    }
    this.routeMetrics.set(metric.route, routeBucket);

    if (metric.tenantId) {
      const tenantBucket = this.tenantMetrics.get(metric.tenantId) ?? { requests: 0, errors: 0 };
      tenantBucket.requests += 1;
      if (!metric.success) {
        tenantBucket.errors += 1;
      }
      this.tenantMetrics.set(metric.tenantId, tenantBucket);
    }
  }

  snapshot(): Record<string, unknown> {
    const averageLatencyMs = this.requestCount === 0
      ? 0
      : this.latencyTotalMs / this.requestCount;

    const routes = Object.fromEntries(Array.from(this.routeMetrics.entries()).map(([route, stats]) => [route, {
      count: stats.count,
      errorCount: stats.errors,
      errorRate: stats.count === 0 ? 0 : Number((stats.errors / stats.count).toFixed(4)),
      latencyMs: {
        avg: stats.count === 0 ? 0 : Number((stats.latencyTotalMs / stats.count).toFixed(3)),
        max: Number(stats.maxLatencyMs.toFixed(3)),
      },
    }]));

    return {
      service: this.serviceName,
      requestCount: this.requestCount,
      errorCount: this.errorCount,
      errorRate: this.requestCount === 0 ? 0 : Number((this.errorCount / this.requestCount).toFixed(4)),
      latencyMs: {
        average: Number(averageLatencyMs.toFixed(3)),
        max: Number(this.maxLatencyMs.toFixed(3)),
      },
      routes,
      tenantMetrics: Object.fromEntries(this.tenantMetrics.entries()),
      recentRequests: this.recentRequests,
    };
  }
}

const registries = new Map<string, ServiceMetrics>();

export function getServiceMetrics(serviceName: string): ServiceMetrics {
  const existing = registries.get(serviceName);
  if (existing) {
    return existing;
  }
  const created = new ServiceMetrics(serviceName);
  registries.set(serviceName, created);
  return created;
}

function resolveTenantId(req: Request): string | undefined {
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

function resolveCorrelationId(req: Request): string {
  const headerCorrelationId = typeof req.headers['x-correlation-id'] === 'string' && req.headers['x-correlation-id'].length > 0
    ? req.headers['x-correlation-id']
    : undefined;
  return headerCorrelationId ?? req.traceId ?? 'missing-trace-id';
}

export function createMetricsMiddleware(serviceName: string): RequestHandler {
  const metrics = getServiceMetrics(serviceName);
  return (req: Request, res: Response, next: NextFunction): void => {
    const startedAt = process.hrtime.bigint();
    res.on('finish', () => {
      const latencyMs = Number(process.hrtime.bigint() - startedAt) / 1_000_000;
      const traceId = req.traceId ?? 'missing-trace-id';
      metrics.record({
        traceId,
        requestId: traceId,
        correlationId: resolveCorrelationId(req),
        tenantId: resolveTenantId(req),
        method: req.method,
        route: req.route?.path ?? req.path,
        statusCode: res.statusCode,
        status: String(res.statusCode),
        latencyMs: Number(latencyMs.toFixed(3)),
        success: res.statusCode < 500,
        recordedAt: new Date().toISOString(),
      });
    });
    next();
  };
}
