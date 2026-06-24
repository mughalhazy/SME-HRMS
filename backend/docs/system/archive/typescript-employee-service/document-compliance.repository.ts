import { randomUUID } from 'node:crypto';
import {
  ComplianceTask,
  ComplianceTaskFilters,
  CreateComplianceTaskInput,
  CreateDocumentInput,
  EmployeeDocument,
  DocumentFilters,
  PolicyAcknowledgement,
  UpdateComplianceTaskInput,
  UpdateDocumentInput,
} from './document-compliance.model';

export class DocumentComplianceRepository {
  private readonly documents = new Map<string, EmployeeDocument>();
  private readonly acknowledgements = new Map<string, PolicyAcknowledgement>();
  private readonly tasks = new Map<string, ComplianceTask>();

  createDocument(input: CreateDocumentInput & { tenant_id: string }): EmployeeDocument {
    const timestamp = new Date().toISOString();
    const document: EmployeeDocument = {
      tenant_id: input.tenant_id,
      document_id: randomUUID(),
      employee_id: input.employee_id,
      document_type: input.document_type,
      title: input.title,
      status: input.status ?? 'Active',
      storage: { ...input.storage },
      tags: [...(input.tags ?? [])],
      issued_on: input.issued_on,
      expiry_date: input.expiry_date,
      requires_acknowledgement: input.requires_acknowledgement ?? false,
      policy_code: input.policy_code,
      contract_details: input.contract_details ? { ...input.contract_details } : undefined,
      created_at: timestamp,
      updated_at: timestamp,
    };
    this.documents.set(document.document_id, document);
    return document;
  }

  findDocumentById(documentId: string): EmployeeDocument | null {
    return this.documents.get(documentId) ?? null;
  }

  updateDocument(documentId: string, patch: UpdateDocumentInput): EmployeeDocument | null {
    const existing = this.findDocumentById(documentId);
    if (!existing) {
      return null;
    }
    const updated: EmployeeDocument = {
      ...existing,
      ...patch,
      storage: patch.storage ? { ...patch.storage } : existing.storage,
      tags: patch.tags ? [...patch.tags] : existing.tags,
      contract_details: patch.contract_details ? { ...patch.contract_details } : existing.contract_details,
      updated_at: new Date().toISOString(),
    };
    this.documents.set(documentId, updated);
    return updated;
  }

  listDocuments(filters: DocumentFilters & { tenant_id: string }): EmployeeDocument[] {
    return [...this.documents.values()]
      .filter((document) => document.tenant_id === filters.tenant_id)
      .filter((document) => !filters.employee_id || document.employee_id === filters.employee_id)
      .filter((document) => !filters.document_type || document.document_type === filters.document_type)
      .filter((document) => !filters.status || document.status === filters.status)
      .filter((document) => filters.requires_acknowledgement === undefined || document.requires_acknowledgement === filters.requires_acknowledgement)
      .filter((document) => !filters.expiry_to || (document.expiry_date !== undefined && document.expiry_date <= filters.expiry_to))
      .sort((left, right) => {
        if (left.updated_at === right.updated_at) {
          return left.document_id.localeCompare(right.document_id);
        }
        return right.updated_at.localeCompare(left.updated_at);
      });
  }

  createAcknowledgement(input: Omit<PolicyAcknowledgement, 'acknowledgement_id' | 'created_at'>): PolicyAcknowledgement {
    const record: PolicyAcknowledgement = {
      ...input,
      acknowledgement_id: randomUUID(),
      created_at: new Date().toISOString(),
    };
    this.acknowledgements.set(record.acknowledgement_id, record);
    return record;
  }

  listAcknowledgementsForDocument(documentId: string, tenantId: string): PolicyAcknowledgement[] {
    return [...this.acknowledgements.values()]
      .filter((item) => item.tenant_id === tenantId && item.document_id === documentId)
      .sort((left, right) => right.acknowledged_at.localeCompare(left.acknowledged_at));
  }

  findLatestAcknowledgement(documentId: string, employeeId: string, tenantId: string): PolicyAcknowledgement | null {
    return this.listAcknowledgementsForDocument(documentId, tenantId)
      .find((item) => item.employee_id === employeeId) ?? null;
  }

  createTask(input: CreateComplianceTaskInput & { tenant_id: string }): ComplianceTask {
    const timestamp = new Date().toISOString();
    const task: ComplianceTask = {
      tenant_id: input.tenant_id,
      task_id: randomUUID(),
      employee_id: input.employee_id,
      related_document_id: input.related_document_id,
      task_type: input.task_type,
      title: input.title,
      description: input.description,
      due_date: input.due_date,
      status: input.status ?? 'Open',
      assigned_employee_id: input.assigned_employee_id,
      created_at: timestamp,
      updated_at: timestamp,
    };
    this.tasks.set(task.task_id, task);
    return task;
  }

  findTaskById(taskId: string): ComplianceTask | null {
    return this.tasks.get(taskId) ?? null;
  }

  updateTask(taskId: string, patch: UpdateComplianceTaskInput): ComplianceTask | null {
    const existing = this.findTaskById(taskId);
    if (!existing) {
      return null;
    }
    const completed = patch.status === 'Completed';
    const updated: ComplianceTask = {
      ...existing,
      ...patch,
      completed_at: completed ? new Date().toISOString() : existing.completed_at,
      completed_by: completed ? patch.completed_by ?? existing.completed_by : existing.completed_by,
      updated_at: new Date().toISOString(),
    };
    this.tasks.set(taskId, updated);
    return updated;
  }

  listTasks(filters: ComplianceTaskFilters & { tenant_id: string }): ComplianceTask[] {
    return [...this.tasks.values()]
      .filter((task) => task.tenant_id === filters.tenant_id)
      .filter((task) => !filters.employee_id || task.employee_id === filters.employee_id)
      .filter((task) => !filters.assigned_employee_id || task.assigned_employee_id === filters.assigned_employee_id)
      .filter((task) => !filters.related_document_id || task.related_document_id === filters.related_document_id)
      .filter((task) => !filters.task_type || task.task_type === filters.task_type)
      .filter((task) => !filters.status || task.status === filters.status)
      .filter((task) => !filters.due_to || task.due_date <= filters.due_to)
      .sort((left, right) => {
        if (left.due_date === right.due_date) {
          return left.task_id.localeCompare(right.task_id);
        }
        return left.due_date.localeCompare(right.due_date);
      });
  }

  findOpenTaskByDocument(documentId: string, tenantId: string): ComplianceTask | null {
    return [...this.tasks.values()].find((task) => (
      task.tenant_id === tenantId
      && task.related_document_id === documentId
      && task.status !== 'Completed'
      && task.status !== 'Cancelled'
    )) ?? null;
  }
}
