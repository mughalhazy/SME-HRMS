import { Request, Response } from 'express';
import { logAuditMutation } from '../../middleware/audit';
import { ApiError, sendApiError } from '../../middleware/error-handler';
import { getStructuredLogger } from '../../middleware/logger';
import { ValidationError } from './employee.validation';
import { ConflictError, NotFoundError } from './service.errors';
import { AuthContext } from './rbac.middleware';
import { DocumentComplianceService } from './document-compliance.service';
import { EmployeeService } from './employee.service';

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

function getAuth(req: Request): AuthContext {
  if (!req.auth) {
    throw new Error('UNAUTHORIZED');
  }
  return req.auth;
}

export class DocumentComplianceController {
  private readonly logger = getStructuredLogger('employee-service');

  constructor(
    private readonly documentService: DocumentComplianceService,
    private readonly employeeService: EmployeeService,
  ) {}

  private canAccessEmployee(auth: AuthContext, employeeId: string): boolean {
    if (auth.role === 'Admin' || auth.role === 'Service') {
      return true;
    }
    if (auth.role === 'Employee') {
      return auth.employee_id === employeeId;
    }
    if (auth.role === 'PayrollAdmin') {
      return auth.employee_id === employeeId;
    }
    if (auth.role === 'Manager') {
      return this.employeeService.canManagerAccessEmployee(auth.employee_id, auth.department_id, employeeId);
    }
    return false;
  }

  private ensureEmployeeScope(req: Request, res: Response, auth: AuthContext, employeeId: string): boolean {
    if (this.canAccessEmployee(auth, employeeId)) {
      return true;
    }
    sendError(req, res, 403, 'FORBIDDEN', 'Insufficient team scope');
    return false;
  }

  createDocument = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureEmployeeScope(req, res, auth, req.body.employee_id)) {
        return;
      }
      const result = this.documentService.createDocument({ ...req.body, tenant_id: req.tenantId });
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: result.document.tenant_id,
        action: 'document_created',
        entity: 'EmployeeDocument',
        entityId: result.document.document_id,
        before: {},
        after: result,
      });
      res.status(201).json({ data: result });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getDocument = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const document = this.documentService.getDocumentById(req.params.documentId);
      if (!this.ensureEmployeeScope(req, res, auth, document.employee_id)) {
        return;
      }
      res.status(200).json({ data: document, acknowledgements: this.documentService.listAcknowledgements(document.document_id) });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listDocuments = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const employeeId = typeof req.query.employee_id === 'string' ? req.query.employee_id : auth.role === 'Employee' ? auth.employee_id : undefined;
      if (employeeId && !this.ensureEmployeeScope(req, res, auth, employeeId)) {
        return;
      }
      const documents = this.documentService.listDocuments({
        tenant_id: req.tenantId,
        employee_id: employeeId,
        document_type: typeof req.query.document_type === 'string' ? req.query.document_type as never : undefined,
        status: typeof req.query.status === 'string' ? req.query.status as never : undefined,
        requires_acknowledgement: typeof req.query.requires_acknowledgement === 'string' ? req.query.requires_acknowledgement === 'true' : undefined,
        expiry_to: typeof req.query.expiry_to === 'string' ? req.query.expiry_to : undefined,
      });
      res.status(200).json({ data: documents });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listExpiringDocuments = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const employeeId = typeof req.query.employee_id === 'string' ? req.query.employee_id : auth.role === 'Employee' ? auth.employee_id : undefined;
      if (employeeId && !this.ensureEmployeeScope(req, res, auth, employeeId)) {
        return;
      }
      const documents = this.documentService.listExpiringDocuments({
        tenant_id: req.tenantId,
        employee_id: employeeId,
        expiry_to: typeof req.query.expiry_to === 'string' ? req.query.expiry_to : undefined,
      });
      res.status(200).json({ data: documents });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateDocument = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const before = this.documentService.getDocumentById(req.params.documentId);
      if (!this.ensureEmployeeScope(req, res, auth, before.employee_id)) {
        return;
      }
      const updated = this.documentService.updateDocument(req.params.documentId, req.body);
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: updated.tenant_id,
        action: 'document_updated',
        entity: 'EmployeeDocument',
        entityId: updated.document_id,
        before,
        after: updated,
      });
      res.status(200).json({ data: updated });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  acknowledgePolicy = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const document = this.documentService.getDocumentById(req.params.documentId);
      if (!this.ensureEmployeeScope(req, res, auth, document.employee_id)) {
        return;
      }
      const acknowledgement = this.documentService.acknowledgePolicy(req.params.documentId, {
        ...req.body,
        tenant_id: req.tenantId,
        acknowledged_by: req.body?.acknowledged_by ?? auth.employee_id ?? auth.role,
      });
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: document.tenant_id,
        action: 'policy_acknowledged',
        entity: 'PolicyAcknowledgement',
        entityId: acknowledgement.acknowledgement_id,
        before: {},
        after: acknowledgement,
      });
      res.status(201).json({ data: acknowledgement });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  createComplianceTask = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureEmployeeScope(req, res, auth, req.body.employee_id) || !this.ensureEmployeeScope(req, res, auth, req.body.assigned_employee_id)) {
        return;
      }
      const task = this.documentService.createComplianceTask({ ...req.body, tenant_id: req.tenantId });
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: task.tenant_id,
        action: 'compliance_task_created',
        entity: 'ComplianceTask',
        entityId: task.task_id,
        before: {},
        after: task,
      });
      res.status(201).json({ data: task });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getComplianceTask = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const task = this.documentService.getComplianceTaskById(req.params.taskId);
      if (!this.ensureEmployeeScope(req, res, auth, task.employee_id) || !this.ensureEmployeeScope(req, res, auth, task.assigned_employee_id)) {
        return;
      }
      res.status(200).json({ data: task });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listComplianceTasks = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const employeeId = typeof req.query.employee_id === 'string' ? req.query.employee_id : auth.role === 'Employee' ? auth.employee_id : undefined;
      const assignedEmployeeId = typeof req.query.assigned_employee_id === 'string' ? req.query.assigned_employee_id : auth.role === 'Employee' ? auth.employee_id : undefined;
      if ((employeeId && !this.ensureEmployeeScope(req, res, auth, employeeId)) || (assignedEmployeeId && !this.ensureEmployeeScope(req, res, auth, assignedEmployeeId))) {
        return;
      }
      const tasks = this.documentService.listComplianceTasks({
        tenant_id: req.tenantId,
        employee_id: employeeId,
        assigned_employee_id: assignedEmployeeId,
        related_document_id: typeof req.query.related_document_id === 'string' ? req.query.related_document_id : undefined,
        task_type: typeof req.query.task_type === 'string' ? req.query.task_type as never : undefined,
        status: typeof req.query.status === 'string' ? req.query.status as never : undefined,
        due_to: typeof req.query.due_to === 'string' ? req.query.due_to : undefined,
      });
      res.status(200).json({ data: tasks });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateComplianceTask = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const before = this.documentService.getComplianceTaskById(req.params.taskId);
      if (!this.ensureEmployeeScope(req, res, auth, before.employee_id) || !this.ensureEmployeeScope(req, res, auth, before.assigned_employee_id)) {
        return;
      }
      const updated = this.documentService.updateComplianceTask(req.params.taskId, {
        ...req.body,
        completed_by: req.body?.completed_by ?? auth.employee_id,
      });
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: updated.tenant_id,
        action: 'compliance_task_updated',
        entity: 'ComplianceTask',
        entityId: updated.task_id,
        before,
        after: updated,
      });
      res.status(200).json({ data: updated });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  private handleError(req: Request, res: Response, error: unknown): void {
    if (error instanceof ValidationError) {
      sendError(req, res, 422, 'VALIDATION_ERROR', error.message, error.details);
      return;
    }
    if (error instanceof ConflictError) {
      sendError(req, res, 409, 'CONFLICT', error.message);
      return;
    }
    if (error instanceof NotFoundError) {
      sendError(req, res, 404, 'NOT_FOUND', error.message);
      return;
    }
    if (error instanceof Error && error.message === 'TENANT_SCOPE_VIOLATION') {
      sendError(req, res, 403, 'FORBIDDEN', 'Tenant scope mismatch');
      return;
    }
    if (error instanceof Error && error.message === 'UNAUTHORIZED') {
      sendError(req, res, 401, 'TOKEN_INVALID', 'Missing or invalid bearer token');
      return;
    }
    sendError(req, res, 500, 'INTERNAL_ERROR', 'An unexpected error occurred.');
  }
}
