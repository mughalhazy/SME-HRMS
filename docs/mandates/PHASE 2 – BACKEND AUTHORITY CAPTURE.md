PHASE 2 – BACKEND AUTHORITY CAPTURE

OBJECTIVE

Convert the existing backend implementation into authoritative documentation.

The backend implementation is the source of truth.

Document reality exactly as implemented.

Do not redesign architecture.

Do not add features.

Do not refactor code.

Do not change database structures.

Do not modify APIs.

Do not modify infrastructure.

This is a backend discovery, extraction, mapping, and authority-building phase.

---

EXECUTION RULES

1. Analyze the entire backend.
2. Extract information from implementation only.
3. Prefer evidence over assumptions.
4. Do not invent future-state architecture.
5. Do not invent missing functionality.
6. Mark unknowns as:

TBD – REQUIRES VERIFICATION

7. Preserve existing governance documents.
8. Update traceability where evidence exists.
9. Stop after documentation and reporting are complete.

---

REQUIRED DOCUMENTS

Populate or create:

docs/01_backend/

BACKEND_ARCHITECTURE.md

DATABASE_SCHEMA.md

API_CONTRACT.md

ERROR_CONTRACT.md

SERVICE_CATALOG.md

INTEGRATION_CATALOG.md

VALIDATION_RULES.md

EVENT_AND_QUEUE_ARCHITECTURE.md

---

Populate or create:

docs/03_fullstack_contracts/

AUTH_AND_TENANCY_CONTRACT.md

USER_ROLES_AND_PERMISSIONS.md

DATA_SHAPE_REGISTRY.md

VALIDATION_PARITY.md

CONTRACT_VERSION_REGISTRY.md

---

BACKEND DISCOVERY

Document:

Modules

Services

Repositories

Controllers

Handlers

Workers

Schedulers

Jobs

Queues

Events

Storage systems

Caching systems

Authentication

Authorization

Validation

External integrations

Observability

Audit mechanisms

Dependency relationships

---

DATABASE DISCOVERY

Document every:

Table

Entity

Collection

View

Index

Constraint

Enum

Relationship

Ownership boundary

Tenant boundary

Lifecycle state

Retention rule

Deletion rule

Consumer

Workflow dependency

---

API DISCOVERY

Document every endpoint.

Capture:

Route

Method

Purpose

Authentication

Authorization

Validation

Request schema

Response schema

Error schema

Dependencies

Consumer systems

Related workflows

Version

Status

---

SECURITY DISCOVERY

Document:

Authentication model

Authorization model

Roles

Permissions

Tenant isolation

Ownership rules

Protected operations

Administrative access paths

Security assumptions

Known security gaps

---

EVENT DISCOVERY

Document:

Events

Publishers

Consumers

Queues

Jobs

Retry behavior

Delivery guarantees

Processing flows

Failure handling

Dependencies

---

TRACEABILITY UPDATE

Update:

FULLSTACK_STITCHING_CONTRACT.md

Populate verified backend traceability:

Feature
→ Workflow
→ Entity
→ Service
→ Repository
→ API
→ Validation
→ Permission
→ Event
→ Dependency

Use repository evidence only.

---

GAP ANALYSIS

Identify:

Undocumented modules

Undocumented services

Undocumented entities

Undocumented APIs

Undocumented permissions

Dead code

Unused services

Unused entities

Unused endpoints

Security concerns

Architecture concerns

Contract inconsistencies

Validation inconsistencies

Documentation gaps

---

REQUIRED REPORTS

Create:

BACKEND_AUTHORITY_CAPTURE_REPORT.md

BACKEND_ARCHITECTURE_REPORT.md

DATABASE_DISCOVERY_REPORT.md

API_DISCOVERY_REPORT.md

SECURITY_DISCOVERY_REPORT.md

EVENT_DISCOVERY_REPORT.md

BACKEND_GAP_REGISTER.md

BACKEND_RISK_REGISTER.md

---

SUCCESS CRITERIA

A new AI session must be able to answer:

- What modules exist?
- What services exist?
- What entities exist?
- What APIs exist?
- What validations exist?
- What permissions exist?
- What events exist?
- What integrations exist?
- What security model exists?
- What tenancy model exists?
- What workflows are supported?

without reverse-engineering source code.

Produce reports.

Stop.

Do not start Frontend Authority Capture.

Do not start Testing Authority Capture.

Do not start Deployment Authority Capture.

Do not implement features.

Do not modify application code unless a documentation-blocking defect prevents analysis.
