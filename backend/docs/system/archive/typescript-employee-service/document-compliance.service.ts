import { EmployeeRepository } from './employee.repository';
import { EmployeeEventOutbox } from './event-outbox';
import {
  COMPLIANCE_TASK_STATUSES,
  COMPLIANCE_TASK_TYPES,
  CONTRACT_KINDS,
  ComplianceTask,
  ComplianceTaskFilters,
  CreateComplianceTaskInput,
  CreateDocumentInput,
  CreatePolicyAcknowledgementInput,
  DOCUMENT_STATUSES,
  DOCUMENT_TYPES,
  DocumentFilters,
  EmployeeDocument,
  PolicyAcknowledgement,
  UpdateComplianceTaskInput,
  UpdateDocumentInput,
} from './document-compliance.model';
import { DocumentComplianceRepository } from './document-compliance.repository';
import { ValidationError } from './employee.validation';
import { ConflictError, NotFoundError } from './service.errors';

function isIsoDate(value: string | undefined): boolean {
  if (!value) {
    return false;
  }
  return /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value));
}

export class DocumentComplianceService {
  readonly eventOutbox = new EmployeeEventOutbox();

  constructor(
    private readonly repository: DocumentComplianceRepository,
    private readonly employeeRepository: EmployeeRepository,
    private readonly tenantId: string = 'tenant-default',
  ) {}

  createDocument(input: CreateDocumentInput): { document: EmployeeDocument; compliance_task?: ComplianceTask } {
    this.assertActorTenant(input.tenant_id);
    this.validateDocumentInput(input);
    this.ensureEmployeeExists(input.employee_id);

    const document = this.repository.createDocument({ ...input, tenant_id: this.tenantId });
    let complianceTask: ComplianceTask | undefined;

    if (document.expiry_date) {
      this.eventOutbox.enqueue('DocumentExpiryTracked', this.tenantId, {
        employee_id: document.employee_id,
        employee_email: this.employeeRepository.findById(document.employee_id)?.email,
        document_id: document.document_id,
        document_title: document.title,
        expiry_date: document.expiry_date,
        document_type: document.document_type,
      }, `${document.document_id}:expiry:${document.expiry_date}`);

      complianceTask = this.ensureExpiryTask(document);
    }

    this.eventOutbox.enqueue('DocumentStored', this.tenantId, {
      employee_id: document.employee_id,
      employee_email: this.employeeRepository.findById(document.employee_id)?.email,
      document_id: document.document_id,
      title: document.title,
      document_type: document.document_type,
      expiry_date: document.expiry_date,
      requires_acknowledgement: document.requires_acknowledgement,
    }, document.document_id);

    if (document.contract_details) {
      this.eventOutbox.enqueue('ContractActivated', this.tenantId, {
        employee_id: document.employee_id,
        employee_email: this.employeeRepository.findById(document.employee_id)?.email,
        document_id: document.document_id,
        contract_kind: document.contract_details.contract_kind,
        effective_from: document.contract_details.effective_from,
        effective_to: document.contract_details.effective_to,
      }, `${document.document_id}:contract`);
    }

    this.eventOutbox.dispatchPending();
    return { document, compliance_task: complianceTask };
  }

  getDocumentById(documentId: string): EmployeeDocument {
    const document = this.repository.findDocumentById(documentId);
    if (!document || document.tenant_id !== this.tenantId) {
      throw new NotFoundError('document not found');
    }
    return document;
  }

  listDocuments(filters: DocumentFilters): EmployeeDocument[] {
    this.assertActorTenant(filters.tenant_id);
    return this.repository.listDocuments({ ...filters, tenant_id: this.tenantId });
  }

  listExpiringDocuments(filters: DocumentFilters): EmployeeDocument[] {
    this.assertActorTenant(filters.tenant_id);
    return this.repository.listDocuments({ ...filters, tenant_id: this.tenantId }).filter((document) => Boolean(document.expiry_date));
  }

  updateDocument(documentId: string, patch: UpdateDocumentInput): EmployeeDocument {
    this.validateDocumentPatch(patch);
    const existing = this.getDocumentById(documentId);
    const employeeId = existing.employee_id;

    const updated = this.repository.updateDocument(documentId, patch);
    if (!updated) {
      throw new NotFoundError('document not found');
    }

    if (updated.expiry_date) {
      this.ensureExpiryTask(updated);
      this.eventOutbox.enqueue('DocumentExpiryTracked', this.tenantId, {
        employee_id: employeeId,
        employee_email: this.employeeRepository.findById(employeeId)?.email,
        document_id: updated.document_id,
        document_title: updated.title,
        expiry_date: updated.expiry_date,
        document_type: updated.document_type,
      }, `${updated.document_id}:expiry:${updated.expiry_date}`);
    }

    this.eventOutbox.enqueue('DocumentUpdated', this.tenantId, {
      employee_id: employeeId,
      employee_email: this.employeeRepository.findById(employeeId)?.email,
      document_id: updated.document_id,
      title: updated.title,
      document_type: updated.document_type,
      status: updated.status,
      expiry_date: updated.expiry_date,
    }, updated.document_id);
    this.eventOutbox.dispatchPending();
    return updated;
  }

  acknowledgePolicy(documentId: string, input: CreatePolicyAcknowledgementInput): PolicyAcknowledgement {
    this.assertActorTenant(input.tenant_id);
    const document = this.getDocumentById(documentId);
    if (!document.requires_acknowledgement || document.document_type !== 'Policy') {
      throw new ConflictError('document does not require policy acknowledgement');
    }

    const actor = input.acknowledged_by?.trim();
    if (!actor) {
      throw new ValidationError([{ field: 'acknowledged_by', reason: 'must be a non-empty string' }]);
    }

    const existing = this.repository.findLatestAcknowledgement(documentId, document.employee_id, this.tenantId);
    if (existing) {
      throw new ConflictError('policy already acknowledged');
    }

    const acknowledgement = this.repository.createAcknowledgement({
      tenant_id: this.tenantId,
      document_id: document.document_id,
      employee_id: document.employee_id,
      acknowledged_by: actor,
      acknowledged_at: new Date().toISOString(),
      comment: input.comment,
    });

    this.repository.updateDocument(document.document_id, {
      latest_acknowledged_at: acknowledgement.acknowledged_at,
      latest_acknowledged_by: acknowledgement.acknowledged_by,
    });

    const linkedTask = this.repository.findOpenTaskByDocument(document.document_id, this.tenantId);
    if (linkedTask?.task_type === 'PolicyAcknowledgement') {
      this.repository.updateTask(linkedTask.task_id, {
        status: 'Completed',
        completed_by: acknowledgement.acknowledged_by,
      });
    }

    this.eventOutbox.enqueue('PolicyAcknowledged', this.tenantId, {
      employee_id: document.employee_id,
      employee_email: this.employeeRepository.findById(document.employee_id)?.email,
      document_id: document.document_id,
      title: document.title,
      policy_code: document.policy_code,
      acknowledged_at: acknowledgement.acknowledged_at,
      acknowledged_by: acknowledgement.acknowledged_by,
    }, `${document.document_id}:acknowledged`);
    this.eventOutbox.dispatchPending();
    return acknowledgement;
  }

  listAcknowledgements(documentId: string): PolicyAcknowledgement[] {
    this.getDocumentById(documentId);
    return this.repository.listAcknowledgementsForDocument(documentId, this.tenantId);
  }

  createComplianceTask(input: CreateComplianceTaskInput): ComplianceTask {
    this.assertActorTenant(input.tenant_id);
    this.validateComplianceTaskInput(input);
    this.ensureEmployeeExists(input.employee_id);
    this.ensureEmployeeExists(input.assigned_employee_id);
    if (input.related_document_id) {
      const document = this.getDocumentById(input.related_document_id);
      if (document.employee_id !== input.employee_id) {
        throw new ValidationError([{ field: 'related_document_id', reason: 'related document must belong to the specified employee' }]);
      }
    }
    const task = this.repository.createTask({ ...input, tenant_id: this.tenantId });
    this.enqueueComplianceTaskEvents(task);
    this.eventOutbox.dispatchPending();
    return task;
  }

  getComplianceTaskById(taskId: string): ComplianceTask {
    const task = this.repository.findTaskById(taskId);
    if (!task || task.tenant_id !== this.tenantId) {
      throw new NotFoundError('compliance task not found');
    }
    return task;
  }

  listComplianceTasks(filters: ComplianceTaskFilters): ComplianceTask[] {
    this.assertActorTenant(filters.tenant_id);
    return this.repository.listTasks({ ...filters, tenant_id: this.tenantId }).map((task) => this.withDerivedTaskStatus(task));
  }

  updateComplianceTask(taskId: string, patch: UpdateComplianceTaskInput): ComplianceTask {
    this.validateComplianceTaskPatch(patch);
    const existing = this.getComplianceTaskById(taskId);
    if (patch.assigned_employee_id) {
      this.ensureEmployeeExists(patch.assigned_employee_id);
    }
    const updated = this.repository.updateTask(taskId, patch);
    if (!updated) {
      throw new NotFoundError('compliance task not found');
    }
    const derived = this.withDerivedTaskStatus(updated);
    if (derived.status === 'Completed') {
      this.eventOutbox.enqueue('ComplianceTaskCompleted', this.tenantId, {
        employee_id: derived.employee_id,
        employee_email: this.employeeRepository.findById(derived.assigned_employee_id)?.email,
        task_id: derived.task_id,
        title: derived.title,
        due_date: derived.due_date,
        completed_by: derived.completed_by,
      }, `${derived.task_id}:completed`);
    } else if (patch.assigned_employee_id && patch.assigned_employee_id !== existing.assigned_employee_id) {
      this.eventOutbox.enqueue('ComplianceTaskAssigned', this.tenantId, {
        employee_id: derived.assigned_employee_id,
        employee_email: this.employeeRepository.findById(derived.assigned_employee_id)?.email,
        related_employee_id: derived.employee_id,
        task_id: derived.task_id,
        title: derived.title,
        due_date: derived.due_date,
      }, `${derived.task_id}:assigned:${derived.assigned_employee_id}`);
    }
    this.eventOutbox.dispatchPending();
    return derived;
  }

  private ensureExpiryTask(document: EmployeeDocument): ComplianceTask {
    if (!document.expiry_date) {
      throw new ConflictError('document does not have an expiry date');
    }
    const existing = this.repository.findOpenTaskByDocument(document.document_id, this.tenantId);
    if (existing) {
      const refreshed = this.repository.updateTask(existing.task_id, {
        due_date: document.expiry_date,
        title: `Renew ${document.title}`,
      });
      return this.withDerivedTaskStatus(refreshed ?? existing);
    }
    const taskType = document.requires_acknowledgement ? 'PolicyAcknowledgement' : 'DocumentExpiry';
    const task = this.repository.createTask({
      tenant_id: this.tenantId,
      employee_id: document.employee_id,
      related_document_id: document.document_id,
      task_type: taskType,
      title: document.requires_acknowledgement ? `Acknowledge ${document.title}` : `Renew ${document.title}`,
      description: document.requires_acknowledgement
        ? `Acknowledge policy ${document.title} before ${document.expiry_date}.`
        : `Renew ${document.document_type.toLowerCase()} ${document.title} before ${document.expiry_date}.`,
      due_date: document.expiry_date,
      assigned_employee_id: document.employee_id,
      status: 'Open',
    });
    this.enqueueComplianceTaskEvents(task);
    return task;
  }

  private enqueueComplianceTaskEvents(task: ComplianceTask): void {
    this.eventOutbox.enqueue('ComplianceTaskCreated', this.tenantId, {
      employee_id: task.employee_id,
      employee_email: this.employeeRepository.findById(task.assigned_employee_id)?.email,
      task_id: task.task_id,
      title: task.title,
      task_type: task.task_type,
      due_date: task.due_date,
      assigned_employee_id: task.assigned_employee_id,
      related_document_id: task.related_document_id,
    }, task.task_id);
    this.eventOutbox.enqueue('ComplianceTaskAssigned', this.tenantId, {
      employee_id: task.assigned_employee_id,
      employee_email: this.employeeRepository.findById(task.assigned_employee_id)?.email,
      related_employee_id: task.employee_id,
      task_id: task.task_id,
      title: task.title,
      task_type: task.task_type,
      due_date: task.due_date,
      related_document_id: task.related_document_id,
    }, `${task.task_id}:assigned:${task.assigned_employee_id}`);
  }

  private validateDocumentInput(input: CreateDocumentInput): void {
    const details: Array<{ field: string; reason: string }> = [];
    if (!input.employee_id?.trim()) {
      details.push({ field: 'employee_id', reason: 'must be a non-empty string' });
    }
    if (!DOCUMENT_TYPES.includes(input.document_type)) {
      details.push({ field: 'document_type', reason: `must be one of: ${DOCUMENT_TYPES.join(', ')}` });
    }
    if (!input.title?.trim()) {
      details.push({ field: 'title', reason: 'must be a non-empty string' });
    }
    if (input.status && !DOCUMENT_STATUSES.includes(input.status)) {
      details.push({ field: 'status', reason: `must be one of: ${DOCUMENT_STATUSES.join(', ')}` });
    }
    this.validateStorage(details, input.storage);
    this.validateOptionalDates(details, input.issued_on, 'issued_on');
    this.validateOptionalDates(details, input.expiry_date, 'expiry_date');
    if (input.document_type === 'Contract') {
      if (!input.contract_details) {
        details.push({ field: 'contract_details', reason: 'must be provided for contract documents' });
      } else {
        this.validateContractDetails(details, input.contract_details);
      }
    }
    if (input.document_type === 'Policy' && input.requires_acknowledgement && !input.policy_code?.trim()) {
      details.push({ field: 'policy_code', reason: 'must be provided when a policy requires acknowledgement' });
    }
    if (details.length > 0) {
      throw new ValidationError(details);
    }
  }

  private validateDocumentPatch(patch: UpdateDocumentInput): void {
    const details: Array<{ field: string; reason: string }> = [];
    if (Object.keys(patch).length === 0) {
      details.push({ field: 'body', reason: 'must include at least one updatable field' });
    }
    if (patch.title !== undefined && !patch.title.trim()) {
      details.push({ field: 'title', reason: 'must be a non-empty string when provided' });
    }
    if (patch.status !== undefined && !DOCUMENT_STATUSES.includes(patch.status)) {
      details.push({ field: 'status', reason: `must be one of: ${DOCUMENT_STATUSES.join(', ')}` });
    }
    if (patch.storage !== undefined) {
      this.validateStorage(details, patch.storage);
    }
    this.validateOptionalDates(details, patch.issued_on, 'issued_on');
    this.validateOptionalDates(details, patch.expiry_date, 'expiry_date');
    if (patch.contract_details !== undefined) {
      this.validateContractDetails(details, patch.contract_details);
    }
    if (details.length > 0) {
      throw new ValidationError(details);
    }
  }

  private validateComplianceTaskInput(input: CreateComplianceTaskInput): void {
    const details: Array<{ field: string; reason: string }> = [];
    if (!input.employee_id?.trim()) {
      details.push({ field: 'employee_id', reason: 'must be a non-empty string' });
    }
    if (!input.assigned_employee_id?.trim()) {
      details.push({ field: 'assigned_employee_id', reason: 'must be a non-empty string' });
    }
    if (!COMPLIANCE_TASK_TYPES.includes(input.task_type)) {
      details.push({ field: 'task_type', reason: `must be one of: ${COMPLIANCE_TASK_TYPES.join(', ')}` });
    }
    if (!input.title?.trim()) {
      details.push({ field: 'title', reason: 'must be a non-empty string' });
    }
    if (!isIsoDate(input.due_date)) {
      details.push({ field: 'due_date', reason: 'must be an ISO date (YYYY-MM-DD)' });
    }
    if (input.status && !COMPLIANCE_TASK_STATUSES.includes(input.status)) {
      details.push({ field: 'status', reason: `must be one of: ${COMPLIANCE_TASK_STATUSES.join(', ')}` });
    }
    if (details.length > 0) {
      throw new ValidationError(details);
    }
  }

  private validateComplianceTaskPatch(patch: UpdateComplianceTaskInput): void {
    const details: Array<{ field: string; reason: string }> = [];
    if (Object.keys(patch).length === 0) {
      details.push({ field: 'body', reason: 'must include at least one updatable field' });
    }
    if (patch.title !== undefined && !patch.title.trim()) {
      details.push({ field: 'title', reason: 'must be a non-empty string when provided' });
    }
    if (patch.assigned_employee_id !== undefined && !patch.assigned_employee_id.trim()) {
      details.push({ field: 'assigned_employee_id', reason: 'must be a non-empty string when provided' });
    }
    if (patch.due_date !== undefined && !isIsoDate(patch.due_date)) {
      details.push({ field: 'due_date', reason: 'must be an ISO date (YYYY-MM-DD)' });
    }
    if (patch.status !== undefined && !COMPLIANCE_TASK_STATUSES.includes(patch.status)) {
      details.push({ field: 'status', reason: `must be one of: ${COMPLIANCE_TASK_STATUSES.join(', ')}` });
    }
    if (details.length > 0) {
      throw new ValidationError(details);
    }
  }

  private validateStorage(details: Array<{ field: string; reason: string }>, storage: CreateDocumentInput['storage']): void {
    if (!storage || typeof storage !== 'object') {
      details.push({ field: 'storage', reason: 'must be an object with storage metadata' });
      return;
    }
    for (const field of ['provider', 'bucket', 'object_key', 'content_type', 'checksum_sha256'] as const) {
      if (typeof storage[field] !== 'string' || storage[field].trim() === '') {
        details.push({ field: `storage.${field}`, reason: 'must be a non-empty string' });
      }
    }
    if (!Number.isInteger(storage.size_bytes) || storage.size_bytes <= 0) {
      details.push({ field: 'storage.size_bytes', reason: 'must be a positive integer' });
    }
    if (typeof storage.encrypted_at_rest !== 'boolean') {
      details.push({ field: 'storage.encrypted_at_rest', reason: 'must be a boolean' });
    }
  }

  private validateContractDetails(details: Array<{ field: string; reason: string }>, contractDetails: NonNullable<CreateDocumentInput['contract_details']>): void {
    if (!CONTRACT_KINDS.includes(contractDetails.contract_kind)) {
      details.push({ field: 'contract_details.contract_kind', reason: `must be one of: ${CONTRACT_KINDS.join(', ')}` });
    }
    this.validateOptionalDates(details, contractDetails.effective_from, 'contract_details.effective_from', true);
    this.validateOptionalDates(details, contractDetails.effective_to, 'contract_details.effective_to');
    this.validateOptionalDates(details, contractDetails.signed_at, 'contract_details.signed_at');
    if (contractDetails.effective_to && contractDetails.effective_from && contractDetails.effective_to < contractDetails.effective_from) {
      details.push({ field: 'contract_details.effective_to', reason: 'must be greater than or equal to effective_from' });
    }
  }

  private validateOptionalDates(details: Array<{ field: string; reason: string }>, value: string | undefined, field: string, required: boolean = false): void {
    if (!value) {
      if (required) {
        details.push({ field, reason: 'must be provided as an ISO date (YYYY-MM-DD)' });
      }
      return;
    }
    if (!isIsoDate(value)) {
      details.push({ field, reason: 'must be an ISO date (YYYY-MM-DD)' });
    }
  }

  private withDerivedTaskStatus(task: ComplianceTask): ComplianceTask {
    if (task.status === 'Completed' || task.status === 'Cancelled') {
      return task;
    }
    if (task.due_date < new Date().toISOString().slice(0, 10)) {
      return { ...task, status: 'Overdue' };
    }
    return task;
  }

  private ensureEmployeeExists(employeeId: string): void {
    if (!this.employeeRepository.findById(employeeId)) {
      throw new ValidationError([{ field: 'employee_id', reason: 'employee was not found' }]);
    }
  }

  private assertActorTenant(actorTenantId?: string): void {
    if (actorTenantId && actorTenantId !== this.tenantId) {
      throw new Error('TENANT_SCOPE_VIOLATION');
    }
  }
}
