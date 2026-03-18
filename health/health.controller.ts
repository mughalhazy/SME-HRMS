import { Request, Response } from 'express';
import { getStructuredLogger } from '../middleware/logger';
import { getServiceMetrics } from '../metrics/metrics';

export class HealthController {
  constructor(private readonly serviceName: string) {}

  getHealth = (req: Request, res: Response): void => {
    res.status(200).json({
      service: this.serviceName,
      status: 'ok',
      traceId: req.traceId,
      metrics: getServiceMetrics(this.serviceName).snapshot(),
    });
  };

  getReady = (req: Request, res: Response): void => {
    res.status(200).json({
      service: this.serviceName,
      status: 'ok',
      traceId: req.traceId,
    });
  };

  getMetrics = (_req: Request, res: Response): void => {
    res.status(200).json({
      data: getServiceMetrics(this.serviceName).snapshot(),
      logs: getStructuredLogger(this.serviceName).records.slice(-20),
    });
  };
}
