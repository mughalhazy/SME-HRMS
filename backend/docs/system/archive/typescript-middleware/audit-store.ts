import { appendFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import type { AuditRecord } from './audit';

const DEFAULT_AUDIT_LOG_PATH = process.env.HRMS_AUDIT_LOG_PATH ?? '/tmp/sme-hrms/audit-records.jsonl';

export function appendCentralizedAuditRecord(record: AuditRecord & { source?: Record<string, unknown> }, serviceName: string): void {
  const path = process.env.HRMS_AUDIT_LOG_PATH ?? DEFAULT_AUDIT_LOG_PATH;
  mkdirSync(dirname(path), { recursive: true });
  const payload = {
    ...record,
    source: {
      service: serviceName,
      ...(record.source ?? {}),
    },
  };
  appendFileSync(path, `${JSON.stringify(payload)}\n`, { encoding: 'utf-8' });
}
