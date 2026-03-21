# Read Models

This compatibility document points to the canonical read-model contract in `docs/canon/read-model-catalog.md` and records the search/indexing extensions added for projection-backed discovery.

## Canonical source
- The authoritative field-level catalog remains `docs/canon/read-model-catalog.md`.

## Search/indexing extensions
- `document_library_view` extends document metadata coverage for search and compliance-friendly document discovery.
- `global_search_view` is a search-owned projection that denormalizes canonical read models into query-optimized search documents.

## Guardrails
- Search APIs must read from `global_search_view` / search projections only.
- Upstream domain services remain authoritative for writes and business rules.
- Rebuilds and partial updates are driven by canonical D2-aligned events plus background job execution.
