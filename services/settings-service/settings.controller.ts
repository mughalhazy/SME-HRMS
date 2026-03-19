import { Request, Response } from 'express';
import { ApiError, sendApiError } from '../../middleware/error-handler';
import { getStructuredLogger } from '../../middleware/logger';
import { ValidationError } from '../employee-service/employee.validation';
import { ConflictError, NotFoundError } from '../employee-service/service.errors';
import { SettingsService } from './settings.service';

function sendError(
  req: Request,
  res: Response,
  status: number,
  code: string,
  message: string,
  details?: Array<{ field: string; reason: string }>,
): void {
  sendApiError(req, res, new ApiError(status, code, message, details ?? []));
}

export class SettingsController {
  private readonly logger = getStructuredLogger('settings-service');

  constructor(private readonly settingsService: SettingsService) {}

  getSettings = (req: Request, res: Response): void => {
    try {
      res.status(200).json({
        data: this.settingsService.getSettingsConfiguration(),
        read_models: this.settingsService.getSettingsReadModels(),
      });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getAttendanceRule = (req: Request, res: Response): void => {
    try {
      const data = this.settingsService.getAttendanceRuleById(req.params.attendanceRuleId);
      res.status(200).json({ data, read_models: this.settingsService.getSettingsReadModels() });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getLeavePolicy = (req: Request, res: Response): void => {
    try {
      const data = this.settingsService.getLeavePolicyById(req.params.leavePolicyId);
      res.status(200).json({ data, read_models: this.settingsService.getSettingsReadModels() });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getPayrollSettings = (req: Request, res: Response): void => {
    try {
      const data = this.settingsService.getPayrollSettings();
      res.status(200).json({ data, read_models: this.settingsService.getSettingsReadModels() });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  createAttendanceRule = (req: Request, res: Response): void => {
    try {
      const data = this.settingsService.createAttendanceRule(req.body);
      this.logger.audit('attendance_rule_created', req.traceId ?? 'missing-trace-id', { attendance_rule_id: data.attendance_rule_id, code: data.code });
      res.status(201).json({ data, read_models: this.settingsService.getSettingsReadModels() });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateAttendanceRule = (req: Request, res: Response): void => {
    try {
      const data = this.settingsService.updateAttendanceRule(req.params.attendanceRuleId, req.body);
      res.status(200).json({ data, read_models: this.settingsService.getSettingsReadModels() });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  createLeavePolicy = (req: Request, res: Response): void => {
    try {
      const data = this.settingsService.createLeavePolicy(req.body);
      this.logger.audit('leave_policy_created', req.traceId ?? 'missing-trace-id', { leave_policy_id: data.leave_policy_id, code: data.code });
      res.status(201).json({ data, read_models: this.settingsService.getSettingsReadModels() });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateLeavePolicy = (req: Request, res: Response): void => {
    try {
      const data = this.settingsService.updateLeavePolicy(req.params.leavePolicyId, req.body);
      res.status(200).json({ data, read_models: this.settingsService.getSettingsReadModels() });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  upsertPayrollSettings = (req: Request, res: Response): void => {
    try {
      const data = this.settingsService.upsertPayrollSettings(req.body);
      res.status(200).json({ data, read_models: this.settingsService.getSettingsReadModels() });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  private handleError(req: Request, res: Response, error: unknown): void {
    if (error instanceof ValidationError) {
      sendError(req, res, 422, 'VALIDATION_ERROR', error.message, error.details);
      return;
    }

    if (error instanceof NotFoundError) {
      sendError(req, res, 404, 'NOT_FOUND', error.message);
      return;
    }

    if (error instanceof ConflictError) {
      sendError(req, res, 409, 'CONFLICT', error.message);
      return;
    }

    const message = error instanceof Error ? error.message : 'Unexpected settings service error';
    sendError(req, res, 500, 'INTERNAL_SERVER_ERROR', message);
  }
}
