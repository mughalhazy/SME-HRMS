import { NextFunction, Request, RequestHandler, Response } from 'express';

export type RequestMetric = {
  traceId: string;
  method: string;
  route: string;
  statusCode: number;
  latencyMs: number;
  success: boolean;
  recordedAt: string;
};

export class ServiceMetrics {
  private requestCount = 0;
  private errorCount = 0;
  private readonly latencies: number[] = [];
  private readonly recentRequests: RequestMetric[] = [];

  constructor(private readonly serviceName: string) {}

  record(metric: RequestMetric): void {
    this.requestCount += 1;
    if (!metric.success) {
      this.errorCount += 1;
    }
    this.latencies.push(metric.latencyMs);
    this.recentRequests.push(metric);
    if (this.recentRequests.length > 50) {
      this.recentRequests.shift();
    }
  }

  snapshot(): Record<string, unknown> {
    const averageLatencyMs = this.latencies.length === 0
      ? 0
      : this.latencies.reduce((sum, value) => sum + value, 0) / this.latencies.length;

    return {
      service: this.serviceName,
      requestCount: this.requestCount,
      errorCount: this.errorCount,
      errorRate: this.requestCount === 0 ? 0 : Number((this.errorCount / this.requestCount).toFixed(4)),
      latencyMs: {
        average: Number(averageLatencyMs.toFixed(3)),
        max: Number((Math.max(0, ...this.latencies)).toFixed(3)),
      },
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

export function createMetricsMiddleware(serviceName: string): RequestHandler {
  const metrics = getServiceMetrics(serviceName);
  return (req: Request, res: Response, next: NextFunction): void => {
    const startedAt = process.hrtime.bigint();
    res.on('finish', () => {
      const latencyMs = Number(process.hrtime.bigint() - startedAt) / 1_000_000;
      metrics.record({
        traceId: req.traceId ?? 'missing-trace-id',
        method: req.method,
        route: req.route?.path ?? req.path,
        statusCode: res.statusCode,
        latencyMs: Number(latencyMs.toFixed(3)),
        success: res.statusCode < 500,
        recordedAt: new Date().toISOString(),
      });
    });
    next();
  };
}
