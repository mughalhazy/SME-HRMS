import { randomUUID } from 'node:crypto';
import {
  AllocateAssetInput,
  Asset,
  AssetFilters,
  AssetLifecycleEntry,
  CreateAssetInput,
  ReturnAssetInput,
  UpdateAssetStatusInput,
} from './asset-management.model';

export class AssetManagementRepository {
  private readonly assets = new Map<string, Asset>();
  private readonly assetTagIndex = new Map<string, string>();
  private readonly lifecycle = new Map<string, AssetLifecycleEntry>();

  createAsset(input: CreateAssetInput & { tenant_id: string }): Asset {
    const timestamp = new Date().toISOString();
    const assignedEmployeeId = input.assigned_employee_id?.trim() || undefined;
    const status = input.status ?? (assignedEmployeeId ? 'Allocated' : 'InStock');
    const asset: Asset = {
      tenant_id: input.tenant_id,
      asset_id: randomUUID(),
      asset_tag: input.asset_tag,
      asset_type: input.asset_type,
      category: input.category,
      model: input.model,
      serial_number: input.serial_number,
      vendor: input.vendor,
      procurement_date: input.procurement_date,
      status,
      assigned_employee_id: assignedEmployeeId,
      assignment: assignedEmployeeId ? {
        employee_id: assignedEmployeeId,
        allocated_at: timestamp,
        allocated_by: input.allocated_by,
        expected_return_date: input.expected_return_date,
        notes: input.notes,
      } : undefined,
      created_at: timestamp,
      updated_at: timestamp,
    };

    this.assets.set(asset.asset_id, asset);
    this.assetTagIndex.set(this.assetTagKey(asset.tenant_id, asset.asset_tag), asset.asset_id);
    return asset;
  }

  findAssetById(assetId: string): Asset | null {
    return this.assets.get(assetId) ?? null;
  }

  findAssetByTag(assetTag: string, tenantId: string): Asset | null {
    const assetId = this.assetTagIndex.get(this.assetTagKey(tenantId, assetTag));
    return assetId ? this.findAssetById(assetId) : null;
  }

  listAssets(filters: AssetFilters & { tenant_id: string }): Asset[] {
    return [...this.assets.values()]
      .filter((asset) => asset.tenant_id === filters.tenant_id)
      .filter((asset) => !filters.employee_id || asset.assigned_employee_id === filters.employee_id)
      .filter((asset) => !filters.status || asset.status === filters.status)
      .filter((asset) => !filters.asset_type || asset.asset_type === filters.asset_type)
      .filter((asset) => !filters.category || asset.category === filters.category)
      .sort((left, right) => {
        if (left.updated_at === right.updated_at) {
          return left.asset_tag.localeCompare(right.asset_tag);
        }
        return right.updated_at.localeCompare(left.updated_at);
      });
  }

  allocateAsset(assetId: string, input: AllocateAssetInput): Asset | null {
    const existing = this.findAssetById(assetId);
    if (!existing) {
      return null;
    }
    const timestamp = new Date().toISOString();
    const updated: Asset = {
      ...existing,
      status: 'Allocated',
      assigned_employee_id: input.employee_id,
      assignment: {
        employee_id: input.employee_id,
        allocated_at: timestamp,
        allocated_by: input.allocated_by,
        expected_return_date: input.expected_return_date,
        notes: input.notes,
      },
      updated_at: timestamp,
    };
    this.assets.set(assetId, updated);
    return updated;
  }

  returnAsset(assetId: string, input: ReturnAssetInput): Asset | null {
    const existing = this.findAssetById(assetId);
    if (!existing) {
      return null;
    }
    const timestamp = new Date().toISOString();
    const updated: Asset = {
      ...existing,
      status: input.return_status ?? 'InStock',
      assigned_employee_id: undefined,
      assignment: undefined,
      last_returned_at: timestamp,
      updated_at: timestamp,
    };
    this.assets.set(assetId, updated);
    return updated;
  }

  updateAssetStatus(assetId: string, input: UpdateAssetStatusInput): Asset | null {
    const existing = this.findAssetById(assetId);
    if (!existing) {
      return null;
    }
    const updated: Asset = {
      ...existing,
      status: input.status,
      updated_at: new Date().toISOString(),
    };
    this.assets.set(assetId, updated);
    return updated;
  }

  createLifecycleEntry(entry: Omit<AssetLifecycleEntry, 'lifecycle_event_id' | 'created_at'>): AssetLifecycleEntry {
    const record: AssetLifecycleEntry = {
      ...entry,
      lifecycle_event_id: randomUUID(),
      created_at: new Date().toISOString(),
    };
    this.lifecycle.set(record.lifecycle_event_id, record);
    return record;
  }

  listLifecycle(assetId: string, tenantId: string): AssetLifecycleEntry[] {
    return [...this.lifecycle.values()]
      .filter((entry) => entry.tenant_id === tenantId && entry.asset_id === assetId)
      .sort((left, right) => left.occurred_at.localeCompare(right.occurred_at));
  }

  private assetTagKey(tenantId: string, assetTag: string): string {
    return `${tenantId}:${assetTag}`;
  }
}
