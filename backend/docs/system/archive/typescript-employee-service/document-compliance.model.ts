export const DOCUMENT_TYPES = ['Contract', 'Policy', 'Certification', 'License', 'Identification', 'Training', 'Other'] as const;
export type DocumentType = (typeof DOCUMENT_TYPES)[number];

export const DOCUMENT_STATUSES = ['Draft', 'Active', 'Archived', 'Expired'] as const;
export type DocumentStatus = (typeof DOCUMENT_STATUSES)[number];

export const CONTRACT_KINDS = ['Employment', 'Amendment', 'NDA', 'Consulting', 'Other'] as const;
export type ContractKind = (typeof CONTRACT_KINDS)[number];

export const COMPLIANCE_TASK_TYPES = ['DocumentExpiry', 'PolicyAcknowledgement', 'CertificationRenewal', 'ManualReview'] as const;
export type ComplianceTaskType = (typeof COMPLIANCE_TASK_TYPES)[number];

export const COMPLIANCE_TASK_STATUSES = ['Open', 'InProgress', 'Completed', 'Overdue', 'Cancelled'] as const;
export type ComplianceTaskStatus = (typeof COMPLIANCE_TASK_STATUSES)[number];

export interface DocumentStorageMetadata {
  provider: string;
  bucket: string;
  object_key: string;
  content_type: string;
  size_bytes: number;
  checksum_sha256: string;
  encrypted_at_rest: boolean;
  retention_class?: string;
}

export interface ContractDetails {
  contract_kind: ContractKind;
  effective_from: string;
  effective_to?: string;
  counterparty_name?: string;
  signed_at?: string;
}

export interface EmployeeDocument {
  tenant_id: string;
  document_id: string;
  employee_id: string;
  document_type: DocumentType;
  title: string;
  status: DocumentStatus;
  storage: DocumentStorageMetadata;
  tags: string[];
  issued_on?: string;
  expiry_date?: string;
  requires_acknowledgement: boolean;
  policy_code?: string;
  contract_details?: ContractDetails;
  latest_acknowledged_at?: string;
  latest_acknowledged_by?: string;
  created_at: string;
  updated_at: string;
}

export interface PolicyAcknowledgement {
  tenant_id: string;
  acknowledgement_id: string;
  document_id: string;
  employee_id: string;
  acknowledged_by: string;
  acknowledged_at: string;
  comment?: string;
  created_at: string;
}

export interface ComplianceTask {
  tenant_id: string;
  task_id: string;
  employee_id: string;
  related_document_id?: string;
  task_type: ComplianceTaskType;
  title: string;
  description?: string;
  due_date: string;
  status: ComplianceTaskStatus;
  assigned_employee_id: string;
  completed_at?: string;
  completed_by?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateDocumentInput {
  tenant_id?: string;
  employee_id: string;
  document_type: DocumentType;
  title: string;
  status?: DocumentStatus;
  storage: DocumentStorageMetadata;
  tags?: string[];
  issued_on?: string;
  expiry_date?: string;
  requires_acknowledgement?: boolean;
  policy_code?: string;
  contract_details?: ContractDetails;
}

export interface UpdateDocumentInput {
  title?: string;
  status?: DocumentStatus;
  storage?: DocumentStorageMetadata;
  tags?: string[];
  issued_on?: string;
  expiry_date?: string;
  requires_acknowledgement?: boolean;
  policy_code?: string;
  contract_details?: ContractDetails;
  latest_acknowledged_at?: string;
  latest_acknowledged_by?: string;
}

export interface CreatePolicyAcknowledgementInput {
  tenant_id?: string;
  acknowledged_by: string;
  comment?: string;
}

export interface CreateComplianceTaskInput {
  tenant_id?: string;
  employee_id: string;
  related_document_id?: string;
  task_type: ComplianceTaskType;
  title: string;
  description?: string;
  due_date: string;
  assigned_employee_id: string;
  status?: ComplianceTaskStatus;
}

export interface UpdateComplianceTaskInput {
  title?: string;
  description?: string;
  due_date?: string;
  status?: ComplianceTaskStatus;
  assigned_employee_id?: string;
  completed_by?: string;
}

export interface DocumentFilters {
  tenant_id?: string;
  employee_id?: string;
  document_type?: DocumentType;
  status?: DocumentStatus;
  requires_acknowledgement?: boolean;
  expiry_to?: string;
}

export interface ComplianceTaskFilters {
  tenant_id?: string;
  employee_id?: string;
  assigned_employee_id?: string;
  related_document_id?: string;
  task_type?: ComplianceTaskType;
  status?: ComplianceTaskStatus;
  due_to?: string;
}
