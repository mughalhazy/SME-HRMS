export const ASSET_STATUSES = ['InStock', 'Allocated', 'InRepair', 'Retired', 'Lost', 'Disposed'] as const;
export type AssetStatus = (typeof ASSET_STATUSES)[number];

export const ASSET_LIFECYCLE_ACTIONS = ['Registered', 'Allocated', 'Returned', 'StatusChanged'] as const;
export type AssetLifecycleAction = (typeof ASSET_LIFECYCLE_ACTIONS)[number];

export interface AssetAssignment {
  employee_id: string;
  allocated_at: string;
  allocated_by?: string;
  expected_return_date?: string;
  notes?: string;
}

export interface Asset {
  tenant_id: string;
  asset_id: string;
  asset_tag: string;
  asset_type: string;
  category?: string;
  model?: string;
  serial_number?: string;
  vendor?: string;
  procurement_date?: string;
  status: AssetStatus;
  assigned_employee_id?: string;
  assignment?: AssetAssignment;
  last_returned_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AssetLifecycleEntry {
  tenant_id: string;
  lifecycle_event_id: string;
  asset_id: string;
  employee_id?: string;
  action: AssetLifecycleAction;
  status_before?: AssetStatus;
  status_after: AssetStatus;
  actor_id?: string;
  notes?: string;
  occurred_at: string;
  created_at: string;
}

export interface CreateAssetInput {
  tenant_id?: string;
  asset_tag: string;
  asset_type: string;
  category?: string;
  model?: string;
  serial_number?: string;
  vendor?: string;
  procurement_date?: string;
  status?: AssetStatus;
  assigned_employee_id?: string;
  allocated_by?: string;
  expected_return_date?: string;
  notes?: string;
}

export interface AllocateAssetInput {
  tenant_id?: string;
  employee_id: string;
  allocated_by?: string;
  expected_return_date?: string;
  notes?: string;
}

export interface ReturnAssetInput {
  tenant_id?: string;
  returned_by?: string;
  return_status?: Exclude<AssetStatus, 'Allocated'>;
  notes?: string;
}

export interface UpdateAssetStatusInput {
  tenant_id?: string;
  status: Exclude<AssetStatus, 'Allocated'>;
  actor_id?: string;
  notes?: string;
}

export interface AssetFilters {
  tenant_id?: string;
  employee_id?: string;
  status?: AssetStatus;
  asset_type?: string;
  category?: string;
}
