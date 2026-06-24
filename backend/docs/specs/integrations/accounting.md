# Accounting Integration

Payroll journal export adapters for third-party accounting systems.

## Scope

- One-way integration: HRMS payroll → accounting system.
- Triggered after payroll is finalized and paid.
- Exports a structured journal entry payload to the connected accounting provider.
- Does NOT receive data back from the accounting system (no reconciliation read-back).

## Implementation

**File:** `integrations/accounting/base.py` (108 lines)

### AccountingAdapter (ABC)
```python
class AccountingAdapter(ABC):
    @abstractmethod
    def export_payroll_journal(self, payload: dict) -> dict: ...
```
All adapters implement this single interface.

### QuickBooksAdapter
- Connects to QuickBooks Online via OAuth Bearer token.
- Exports to `/v3/company/{realm_id}/journalentry`.
- Config: `base_url`, `realm_id`, `access_token`, `timeout_seconds`, `retry_attempts`.
- Returns: `{ provider, status, journal_entry_id, sync_token }` on success.
- Config loaded from `load_integrations_config().quickbooks` + env vars.

### SAPAdapter
- Connects to SAP via OData service `ZPAYROLL_JOURNAL_SRV`.
- Exports to `/sap/opu/odata/sap/ZPAYROLL_JOURNAL_SRV/JournalEntries`.
- Config: `base_url`, `company_code`, `auth_token`, `timeout_seconds`, `retry_attempts`.
- Returns: `{ provider, status, document_id }` on success.
- Config loaded from `SAPConnectorConfig.from_env()`.

## Payload schema

```json
{
  "journal_entries": [
    { "account": "...", "debit": 0, "credit": 0, "description": "..." }
  ],
  "posting_date": "YYYY-MM-DD",
  "document_date": "YYYY-MM-DD",
  "memo": "Payroll Journal - YYYY-MM",
  "reference": "PAYROLL"
}
```

## Error handling

Both adapters return a normalized failure dict (no exceptions raised) on config error or HTTP failure:
```json
{ "provider": "QuickBooks|SAP", "status": "failure", "errors": ["..."], "http_status": 400 }
```

## Configuration

Set via environment variables + `config/integrations.py`:

| Var | Adapter | Purpose |
|---|---|---|
| `QUICKBOOKS_REALM_ID` | QuickBooks | Company realm ID |
| `SAP_COMPANY_CODE` | SAP | SAP company code |
| `SAP_BASE_URL` | SAP | SAP OData endpoint |

## Notes
- This integration has no HTTP surface of its own — it is called by payroll-service after payroll finalization.
- Extend with additional providers by implementing `AccountingAdapter` and registering in the config.
- All export calls are logged via the audit-service trail (payroll finalization event).
