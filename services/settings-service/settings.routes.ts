import { Router } from 'express';
import { HealthController } from '../../health/health.controller';
import { createRateLimitMiddleware } from '../../middleware/rate-limit';
import { createLoggerMiddleware } from '../../middleware/logger';
import { requestIdMiddleware } from '../../middleware/request-id';
import { createThrottleMiddleware } from '../../middleware/throttle';
import { createPayloadLimitMiddleware } from '../../middleware/validation';
import { createMetricsMiddleware } from '../../metrics/metrics';
import { SettingsController } from './settings.controller';
import { SettingsRepository } from './settings.repository';
import { SettingsService } from './settings.service';

const serviceThrottle = createThrottleMiddleware({
  maxConcurrent: 16,
  maxQueue: 32,
  queueTimeoutMs: 200,
  keyGenerator: () => 'settings-service',
});

const writeSettingsRateLimit = createRateLimitMiddleware({
  keyPrefix: 'settings:write',
  windowMs: 60_000,
  maxRequests: 30,
});

const readSettingsRateLimit = createRateLimitMiddleware({
  keyPrefix: 'settings:read',
  windowMs: 60_000,
  maxRequests: 180,
});

export function createSettingsRouter(): Router {
  const repository = new SettingsRepository();
  const service = new SettingsService(repository);
  const controller = new SettingsController(service);
  const healthController = new HealthController('settings-service');
  const router = Router();

  router.use(requestIdMiddleware);
  router.use(serviceThrottle);
  router.use(createLoggerMiddleware('settings-service'));
  router.use(createMetricsMiddleware('settings-service'));
  router.use(createPayloadLimitMiddleware(16 * 1024));

  router.get('/health', healthController.getHealth);
  router.get('/ready', healthController.getReady);
  router.get('/metrics', healthController.getMetrics);

  router.get('/api/v1/settings', readSettingsRateLimit, controller.getSettings);
  router.get('/api/v1/settings/attendance-rules/:attendanceRuleId', readSettingsRateLimit, controller.getAttendanceRule);
  router.post('/api/v1/settings/attendance-rules', writeSettingsRateLimit, controller.createAttendanceRule);
  router.patch('/api/v1/settings/attendance-rules/:attendanceRuleId', writeSettingsRateLimit, controller.updateAttendanceRule);
  router.get('/api/v1/settings/leave-policies/:leavePolicyId', readSettingsRateLimit, controller.getLeavePolicy);
  router.post('/api/v1/settings/leave-policies', writeSettingsRateLimit, controller.createLeavePolicy);
  router.patch('/api/v1/settings/leave-policies/:leavePolicyId', writeSettingsRateLimit, controller.updateLeavePolicy);
  router.get('/api/v1/settings/payroll', readSettingsRateLimit, controller.getPayrollSettings);
  router.put('/api/v1/settings/payroll', writeSettingsRateLimit, controller.upsertPayrollSettings);

  return router;
}
