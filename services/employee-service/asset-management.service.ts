import { EmployeeRepository } from './employee.repository';
import { EmployeeEventOutbox } from './event-outbox';
import { ValidationError } from './employee.validation';
import { ConflictError, NotFoundError } from './service.errors';
import {
  AllocateAssetInput,
  Asset,
  AssetFilters,
  AssetLifecycleEntry,
  ASSET_STATUSES,
  CreateAssetInput,
  ReturnAssetInput,
  UpdateAssetStatusInput,
} from './asset-management.model';
import { AssetManagementRepository } from './asset-management.repository';

function isIsoDate(value: string | undefined): boolean {
  if (!value) {
    return false;
  }
  return /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value));
}

export class AssetManagementService {
  readonly eventOutbox = new EmployeeEventOutbox();

  constructor(
    private readonly repository: AssetManagementRepository,
    private readonly employeeRepository: EmployeeRepository,
    private readonly tenantId: string = 'tenant-default',
  ) {}

  createAsset(input: CreateAssetInput): { asset: Asset; lifecycle: AssetLifecycleEntry[] } {
    this.assertActorTenant(input.tenant_id);
    this.validateCreateAssetInput(input);
    this.ensureUniqueAssetTag(input.asset_tag);

    if (input.assigned_employee_id) {
      this.ensureEmployeeExists(input.assigned_employee_id);
    }

    const asset = this.repository.createAsset({ ...input, tenant_id: this.tenantId });
    const lifecycle: AssetLifecycleEntry[] = [];

    lifecycle.push(this.recordLifecycle({
      asset_id: asset.asset_id,
      employee_id: asset.assigned_employee_id,
      action: 'Registered',
      status_after: asset.assigned_employee_id ? 'Allocated' : asset.status,
      actor_id: input.allocated_by,
      notes: input.notes,
    }));

    this.eventOutbox.enqueue('AssetRegistered', this.tenantId, {
      asset_id: asset.asset_id,
      asset_tag: asset.asset_tag,
      asset_type: asset.asset_type,
      category: asset.category,
      status: asset.status,
      employee_id: asset.assigned_employee_id,
    }, asset.asset_id);

    if (asset.assigned_employee_id) {
      lifecycle.push(this.recordLifecycle({
        asset_id: asset.asset_id,
        employee_id: asset.assigned_employee_id,
        action: 'Allocated',
        status_before: 'InStock',
        status_after: asset.status,
        actor_id: input.allocated_by,
        notes: input.notes,
      }));
      this.eventOutbox.enqueue('AssetAllocated', this.tenantId, {
        asset_id: asset.asset_id,
        asset_tag: asset.asset_tag,
        employee_id: asset.assigned_employee_id,
        expected_return_date: asset.assignment?.expected_return_date,
      }, `${asset.asset_id}:${asset.assigned_employee_id}:allocated`);
    }

    this.eventOutbox.dispatchPending();
    return { asset, lifecycle };
  }

  getAssetById(assetId: string): Asset {
    const asset = this.repository.findAssetById(assetId);
    if (!asset || asset.tenant_id !== this.tenantId) {
      throw new NotFoundError('asset not found');
    }
    return asset;
  }

  listAssets(filters: AssetFilters): Asset[] {
    this.assertActorTenant(filters.tenant_id);
    return this.repository.listAssets({ ...filters, tenant_id: this.tenantId });
  }

  allocateAsset(assetId: string, input: AllocateAssetInput): { asset: Asset; lifecycle: AssetLifecycleEntry } {
    this.assertActorTenant(input.tenant_id);
    this.validateAllocationInput(input);
    this.ensureEmployeeExists(input.employee_id);

    const existing = this.getAssetById(assetId);
    if (existing.assigned_employee_id) {
      throw new ConflictError('asset is already allocated to an employee');
    }
    if (existing.status === 'Retired' || existing.status === 'Disposed') {
      throw new ConflictError(`cannot allocate asset in ${existing.status} status`);
    }

    const asset = this.repository.allocateAsset(assetId, input);
    if (!asset) {
      throw new NotFoundError('asset not found');
    }

    const lifecycle = this.recordLifecycle({
      asset_id: asset.asset_id,
      employee_id: input.employee_id,
      action: 'Allocated',
      status_before: existing.status,
      status_after: asset.status,
      actor_id: input.allocated_by,
      notes: input.notes,
    });

    this.eventOutbox.enqueue('AssetAllocated', this.tenantId, {
      asset_id: asset.asset_id,
      asset_tag: asset.asset_tag,
      employee_id: asset.assigned_employee_id,
      expected_return_date: asset.assignment?.expected_return_date,
    }, `${asset.asset_id}:${input.employee_id}:allocated`);
    this.eventOutbox.dispatchPending();

    return { asset, lifecycle };
  }

  returnAsset(assetId: string, input: ReturnAssetInput): { asset: Asset; lifecycle: AssetLifecycleEntry } {
    this.assertActorTenant(input.tenant_id);
    this.validateReturnInput(input);

    const existing = this.getAssetById(assetId);
    if (!existing.assigned_employee_id) {
      throw new ConflictError('asset is not currently allocated');
    }

    const asset = this.repository.returnAsset(assetId, input);
    if (!asset) {
      throw new NotFoundError('asset not found');
    }

    const lifecycle = this.recordLifecycle({
      asset_id: asset.asset_id,
      employee_id: existing.assigned_employee_id,
      action: 'Returned',
      status_before: existing.status,
      status_after: asset.status,
      actor_id: input.returned_by,
      notes: input.notes,
    });

    this.eventOutbox.enqueue('AssetReturned', this.tenantId, {
      asset_id: asset.asset_id,
      asset_tag: asset.asset_tag,
      employee_id: existing.assigned_employee_id,
      return_status: asset.status,
    }, `${asset.asset_id}:${existing.assigned_employee_id}:returned`);
    this.eventOutbox.dispatchPending();

    return { asset, lifecycle };
  }

  updateAssetStatus(assetId: string, input: UpdateAssetStatusInput): { asset: Asset; lifecycle: AssetLifecycleEntry } {
    this.assertActorTenant(input.tenant_id);
    this.validateStatusInput(input);

    const existing = this.getAssetById(assetId);
    if (input.status === existing.status) {
      const currentLifecycle = this.recordLifecycle({
        asset_id: existing.asset_id,
        employee_id: existing.assigned_employee_id,
        action: 'StatusChanged',
        status_before: existing.status,
        status_after: existing.status,
        actor_id: input.actor_id,
        notes: input.notes,
      });
      return { asset: existing, lifecycle: currentLifecycle };
    }
    if (existing.assigned_employee_id && input.status === 'InStock') {
      throw new ConflictError('use the return endpoint before moving an allocated asset back to stock');
    }

    const asset = this.repository.updateAssetStatus(assetId, input);
    if (!asset) {
      throw new NotFoundError('asset not found');
    }

    const lifecycle = this.recordLifecycle({
      asset_id: asset.asset_id,
      employee_id: asset.assigned_employee_id,
      action: 'StatusChanged',
      status_before: existing.status,
      status_after: asset.status,
      actor_id: input.actor_id,
      notes: input.notes,
    });

    this.eventOutbox.enqueue('AssetStatusChanged', this.tenantId, {
      asset_id: asset.asset_id,
      asset_tag: asset.asset_tag,
      employee_id: asset.assigned_employee_id,
      from_status: existing.status,
      to_status: asset.status,
    }, `${asset.asset_id}:${existing.status}:${asset.status}`);
    this.eventOutbox.dispatchPending();

    return { asset, lifecycle };
  }

  listAssetLifecycle(assetId: string): AssetLifecycleEntry[] {
    this.getAssetById(assetId);
    return this.repository.listLifecycle(assetId, this.tenantId);
  }

  private recordLifecycle(entry: Omit<AssetLifecycleEntry, 'tenant_id' | 'lifecycle_event_id' | 'occurred_at' | 'created_at'> & { occurred_at?: string }): AssetLifecycleEntry {
    return this.repository.createLifecycleEntry({
      tenant_id: this.tenantId,
      occurred_at: entry.occurred_at ?? new Date().toISOString(),
      ...entry,
    });
  }

  private validateCreateAssetInput(input: CreateAssetInput): void {
    const details: Array<{ field: string; reason: string }> = [];

    if (!input.asset_tag?.trim()) {
      details.push({ field: 'asset_tag', reason: 'must be a non-empty string' });
    }
    if (!input.asset_type?.trim()) {
      details.push({ field: 'asset_type', reason: 'must be a non-empty string' });
    }
    if (input.procurement_date && !isIsoDate(input.procurement_date)) {
      details.push({ field: 'procurement_date', reason: 'must be an ISO date in YYYY-MM-DD format' });
    }
    if (input.expected_return_date && !isIsoDate(input.expected_return_date)) {
      details.push({ field: 'expected_return_date', reason: 'must be an ISO date in YYYY-MM-DD format' });
    }
    if (input.status && !(ASSET_STATUSES as readonly string[]).includes(input.status)) {
      details.push({ field: 'status', reason: `must be one of: ${ASSET_STATUSES.join(', ')}` });
    }
    if (input.status === 'Allocated' && !input.assigned_employee_id) {
      details.push({ field: 'assigned_employee_id', reason: 'allocated assets must be linked to an employee' });
    }
    if (input.assigned_employee_id && input.status && input.status !== 'Allocated') {
      details.push({ field: 'status', reason: 'assets linked to an employee at creation must use Allocated status' });
    }

    if (details.length > 0) {
      throw new ValidationError(details);
    }
  }

  private validateAllocationInput(input: AllocateAssetInput): void {
    const details: Array<{ field: string; reason: string }> = [];
    if (!input.employee_id?.trim()) {
      details.push({ field: 'employee_id', reason: 'must be a non-empty string' });
    }
    if (input.expected_return_date && !isIsoDate(input.expected_return_date)) {
      details.push({ field: 'expected_return_date', reason: 'must be an ISO date in YYYY-MM-DD format' });
    }
    if (details.length > 0) {
      throw new ValidationError(details);
    }
  }

  private validateReturnInput(input: ReturnAssetInput): void {
    const details: Array<{ field: string; reason: string }> = [];
    if (details.length > 0) {
      throw new ValidationError(details);
    }
  }

  private validateStatusInput(input: UpdateAssetStatusInput): void {
    const details: Array<{ field: string; reason: string }> = [];
    if (!input.status || !(ASSET_STATUSES as readonly string[]).includes(input.status)) {
      details.push({ field: 'status', reason: 'use a non-Allocated asset status value' });
    }
    if (details.length > 0) {
      throw new ValidationError(details);
    }
  }

  private ensureUniqueAssetTag(assetTag: string): void {
    if (this.repository.findAssetByTag(assetTag, this.tenantId)) {
      throw new ConflictError('asset tag already exists');
    }
  }

  private ensureEmployeeExists(employeeId: string): void {
    if (!this.employeeRepository.findById(employeeId)) {
      throw new ValidationError([{ field: 'employee_id', reason: 'employee was not found' }]);
    }
  }

  private assertActorTenant(tenantId?: string): void {
    if (tenantId && tenantId !== this.tenantId) {
      throw new ValidationError([{ field: 'tenant_id', reason: `must match tenant ${this.tenantId}` }]);
    }
  }
}
