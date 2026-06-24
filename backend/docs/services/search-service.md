# search-service

Projection-backed cross-domain search: indexes canonical read models from employee, hiring, document, and payroll services into tenant-safe search documents, and serves fast full-text + filtered queries without touching transactional domain stores.

## Scope
- Add-on service (`search-service`, `search_service.py` + `search_api.py`).
- Maintains a `global_search_view` built from 5 upstream read models.
- Consumes D2-aligned domain events to schedule incremental reindex jobs via `background-jobs`.
- Serves 4 query endpoints: universal search + 3 entity-type-scoped shortcuts.
- Does NOT read transactional domain DBs — all data flows through read models and event-triggered projections.
- Results are tenant-scoped; cross-tenant leakage is structurally prevented by `assert_tenant_access()`.

## HTTP surface (`/api/v1`)
- `GET /api/v1/search?tenant_id=&q=&entity_type=&domain=&department_id=&role_id=&status=&limit=&cursor=&sort=` — universal search across all indexed entities
- `GET /api/v1/search/employees?tenant_id=&q=&department_id=&role_id=&status=&limit=&cursor=&sort=` — employees only (sets `entity_type=employee`)
- `GET /api/v1/search/candidates?tenant_id=&q=&department_id=&status=&limit=&cursor=&sort=` — candidates only
- `GET /api/v1/search/documents?tenant_id=&q=&department_id=&status=&limit=&cursor=&sort=` — documents only

All endpoints are read-only GET requests. `tenant_id` is required on every query.

## Indexed read models → entity types

| Read Model | Domain | Entity Types |
|---|---|---|
| `employee_directory_view` | employees | `employee` |
| `organization_structure_view` | organization | `department`, `role` |
| `candidate_pipeline_view` | hiring | `candidate` |
| `document_library_view` | documents | `document` |
| `payroll_summary_view` | payroll | `payroll_run` |

## SearchDocument schema
```yaml
document_id: string       # derived from tenant + source_view + entity keys
tenant_id: string
source_view: string       # e.g. "employee_directory_view"
source_key: string        # unique key within source view
domain: string            # e.g. "employees", "hiring"
entity_type: string       # e.g. "employee", "candidate", "document"
display_name: string      # primary label shown in search results
search_blob: string       # concatenated searchable text for term matching
keywords: list[string]    # structured facets for scoring
department_id: string | null
department_name: string | null
role_id: string | null
role_title: string | null
status: string | null
```

## Scoring and ranking
- `_score_row()` computes a relevance score by counting query term hits across `search_blob` and `keywords`.
- `_sort_rows()` applies sort order: when a query string is present, results rank by score DESC; without a query, sort defaults to `display_name` alphabetically (or an explicit `sort` param).
- Results cached in `CachedSearchResult` (TTL-based) per `(tenant_id, query_fingerprint)` to reduce re-scoring overhead on repeated identical queries.

## Indexing pipeline
1. Domain event received by `consume_event()`.
2. Event type normalized and matched to a `SOURCE_MODEL_CONFIG` entry.
3. Reindex background job dispatched via `background-jobs` (`search.reindex`).
4. `process_reindex_job()` calls `ingest_read_model()` for the affected model, rebuilds affected `SearchDocument` records, and updates the `SearchProjectionState` checkpoint.

`rebuild_index()` performs a full re-projection for all (or specified) models for a tenant — used after bulk imports or data corrections.

## Events subscribed
- `EmployeeCreated`, `EmployeeUpdated`, `EmployeeStatusChanged`
- `DepartmentCreated`, `DepartmentUpdated`
- `RoleCreated`, `RoleUpdated`
- `CandidateApplied`, `CandidateStageChanged`, `InterviewScheduled`, `InterviewCompleted`, `CandidateHired`
- `DocumentStored`, `DocumentUpdated`
- `PayrollProcessed`, `PayrollPaid`, `PayrollCancelled`

## Events published
- None — search-service indexing side effects remain internal projections.

## Read models produced
- `global_search_view` (search-owned projection, built from upstream read model ingestion)
- `SearchProjectionState` — checkpoint tracking per-model indexing progress

## Owned entities
- `SearchDocument`
- `SearchProjectionState`
- `SearchEventCheckpoint`

## Supported workflows
- `projection_search_indexing`

## Dependencies
- `employee-service` read models — `employee_directory_view`, `organization_structure_view`
- `hiring-service` read models — `candidate_pipeline_view`
- Document service projections — `document_library_view`
- `payroll-service` projections — `payroll_summary_view`
- `background-jobs` — asynchronous reindex job dispatch
- `integration-service` / event-outbox pipeline — upstream event source
- `resilience` (`Observability`) — metrics and trace recording
- `tenant_support` — `assert_tenant_access()` on every document read

## Notes
- `ingest_read_model()` validates each row against its model's `key_fields`; rows missing required key fields raise `SearchServiceError(422, 'INVALID_READ_MODEL_ROW', ...)`.
- `health_snapshot()` returns index size, last-event-checkpoint, and per-model document counts — useful for ops monitoring.
- `get_projection_state()` exposes indexing lag per model per tenant for SLA tracking.
- The service has no write-through mutations — all updates flow through event consumption and background jobs.
