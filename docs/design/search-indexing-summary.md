# Search / Indexing Service Summary

This change introduces a projection-backed `search-service` that extends existing read-model patterns instead of bypassing them.

## Read models extended
- Reused `employee_directory_view` for employee search documents.
- Reused `organization_structure_view` for department and role search documents.
- Reused `candidate_pipeline_view` for candidate search documents.
- Extended the catalog with `document_library_view` for document metadata search.
- Reused `payroll_summary_view` to build optional payroll-run summary search documents.
- Added `global_search_view` as the unified search projection exposed by the search service.

## Event and job flow
1. Domain services publish canonical/normalized events through the outbox pipeline.
2. `search-service` consumes supported events and enqueues `search.reindex` background jobs.
3. Background jobs rebuild the affected search projections from stored read models.
4. Search APIs query only the indexed search documents.

## Guardrails satisfied
- No search-heavy transactional DB reads.
- Tenant filters are mandatory at query time and preserved in indexed documents.
- Domain business rules stay in source services; search only denormalizes read-model data.
