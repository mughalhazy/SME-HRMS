# DATABASE DISCOVERY REPORT

Status: Active
Authority Level: High
Last Reviewed: 2026-06-15
Owner: AI

---

## 1. Total Table Count

**57 tables** across 13 migration files.

---

## 2. Tables Grouped by Migration

| Migration File | Tables Created | Count |
|---------------|---------------|-------|
| 001_core_schema.sql | departments, roles, employees | 3 |
| 002_workflow_schema.sql | attendance_records, leave_requests, payroll_records, job_postings, candidates, candidate_stage_transitions, interviews, attendance_rules, leave_policies, payroll_settings, performance_review_cycles, performance_goals, performance_feedback, performance_calibrations, performance_pip_plans, performance_pip_milestones | 16 |
| 003_centralized_workflow_engine.sql | workflow_definitions, workflow_instances, workflow_steps, workflow_history | 4 |
| 004_persistence_normalization.sql | user_accounts, role_bindings, permission_policies, sessions, refresh_tokens | 5 (+ ALTER on attendance_records) |
| 005_tenant_foundation.sql | tenants, tenant_configs | 2 |
| 006_notification_service.sql | notification_templates, notification_messages, delivery_attempts, notification_preferences | 4 |
| 007_event_outbox.sql | service_outbox, processed_events | 2 |
| 008_background_jobs_schema.sql | event_outbox, background_jobs, background_job_failures | 3 |
| 009_audit_service.sql | audit_records | 1 |
| 010_engagement_service.sql | engagement_surveys, engagement_survey_questions, engagement_survey_responses, engagement_survey_answers, engagement_survey_aggregates | 5 |
| 011_addon_domains.sql | helpdesk_tickets, helpdesk_ticket_sla_events, workforce_intelligence_snapshots, learning_paths, workforce_cost_plans | 5 |
| 012_compensation_domain.sql | compensation_bands, salary_revisions, benefits_plans, benefits_enrollments, allowances | 5 |
| 013_travel_domain.sql | travel_requests, travel_itinerary_segments | 2 |
| **TOTAL** | | **57** |

---

## 3. Key Schema Patterns

### 3.1 Multi-Tenancy Invariant

**Pattern (migrations 001–010):** Every primary table carries `tenant_id VARCHAR(80) NOT NULL` and a `UNIQUE (tenant_id, <entity>_id)` constraint. Foreign keys are compound: `FOREIGN KEY (tenant_id, fk_col) REFERENCES target (tenant_id, pk_col)`. This ensures cross-tenant data isolation is enforced at the database level.

**Deviation (migrations 012–013):** `salary_revisions`, `benefits_enrollments`, `allowances`, `travel_requests`, and `travel_itinerary_segments` carry `tenant_id` as a column but reference `employees (employee_id)` without the tenant_id scope — e.g., `FOREIGN KEY (employee_id) REFERENCES employees (employee_id)`. This means the FK does not prevent cross-tenant joins at the database level for these tables. `compensation_bands` similarly references `grade_bands (grade_band_id)` without tenant scoping.

### 3.2 Outbox Pattern (Dual Implementation)

Two distinct outbox implementations exist in separate files:

| Table | File | Purpose |
|-------|------|---------|
| `service_outbox` | 007_event_outbox.sql | Service-level event dispatch with retry/status tracking |
| `processed_events` | 007_event_outbox.sql | Idempotency deduplication per consumer |
| `event_outbox` | 008_background_jobs_schema.sql | Aggregate-level domain event outbox (published_at NULL = unpublished) |

These appear to be two different outbox patterns used by different parts of the system. Relationship between them is TBD – REQUIRES VERIFICATION.

### 3.3 Audit Immutability via DB Triggers

`audit_records` (migration 009) is the only table protected by database-level mutation triggers:
- `trg_audit_records_prevent_update` — raises exception on any UPDATE
- `trg_audit_records_prevent_delete` — raises exception on any DELETE

No other table uses this pattern. The `audit_records` primary key is `BIGSERIAL` (sequential integer), unlike all other tables which use `UUID` PKs. A secondary `audit_id UUID` unique key allows stable external references.

### 3.4 Workflow Integration (loose coupling)

`workflow_id UUID NULL` appears as a nullable column in `performance_review_cycles`, `performance_goals`, `performance_calibrations`, `performance_pip_plans`, and `travel_requests`. This is a soft reference to `workflow_instances.workflow_id` — no FK is defined in the SQL, coupling is by convention only (TBD – REQUIRES VERIFICATION whether application code enforces this).

### 3.5 Partial Unique Index (Policy Enforcement)

`leave_policies` defines a partial unique index:
```sql
CREATE UNIQUE INDEX uq_leave_policies_active_type ON leave_policies (tenant_id, leave_type) WHERE status = 'Active';
```
This enforces at most one active policy per leave type per tenant. No other table uses this pattern.

### 3.6 JSONB for Flexible Attributes

JSONB is used extensively for semi-structured data:
- `workflow_definitions.steps`, `workflow_instances.metadata`, `workflow_steps.metadata`
- `workflow_history.details`
- `audit_records.actor`, `audit_records.before`, `audit_records.after`, `audit_records.source`
- `tenant_configs.feature_flags`, `legal_entity`, `leave_policy_refs`, `payroll_rule_refs`, `enabled_locations`
- `engagement_survey_aggregates.question_scores`, `dimension_scores`, `score_distribution`
- `notification_preferences.quiet_hours`
- `event_outbox.payload`, `service_outbox.event_payload`

### 3.7 Cascade DELETE chains

Notable CASCADE chains that could propagate deletes widely:
- `job_postings` → `candidates` (CASCADE) → `candidate_stage_transitions` (CASCADE) and `interviews` (CASCADE)
- `sessions` → `refresh_tokens` (CASCADE)
- `engagement_surveys` → `engagement_survey_questions` (CASCADE) → `engagement_survey_answers` (CASCADE)
- `engagement_surveys` → `engagement_survey_responses` (CASCADE) → `engagement_survey_answers` (CASCADE)
- `engagement_surveys` → `engagement_survey_aggregates` (CASCADE)
- `tenants` → `tenant_configs`, `notification_templates`, `notification_messages`, `delivery_attempts`, `notification_preferences` (all CASCADE)
- `background_jobs` → `background_job_failures` (CASCADE)
- `travel_requests` → `travel_itinerary_segments` (CASCADE)
- `performance_pip_plans` → `performance_pip_milestones` (CASCADE)

---

## 4. Tables with Potentially Unusual Characteristics

The following tables may warrant review. They are not claimed to be dead code — TBD – REQUIRES VERIFICATION in each case.

| Table | Migration | Observation |
|-------|-----------|-------------|
| `workforce_intelligence_snapshots` | 011 | No FK to `tenants`, no indexes, no related tables; purpose unclear from SQL alone |
| `workforce_cost_plans` | 011 | No FK to `tenants`; `forecast_currency` defaults to 'USD' while most of the system defaults to 'PKR' |
| `learning_paths` | 011 | No FK to `tenants`, no indexes, no service implementation; feature explicitly out of scope (see §6) |
| `candidate_stage_transitions` | 002 | Transition log for `candidates`; `from_status` is nullable (first transition has no prior state) — by design, but worth noting |
| `engagement_survey_aggregates` | 010 | `survey_id` is both PK and FK — 1:1 with `engagement_surveys`; no indexes beyond the PK |

---

## 5. Schema-Level Inconsistencies

### 5.1 Leave Type Enum Mismatch (Critical)

The `leave_type` enum differs between the two leave-domain tables:

| Table | Column | Allowed Values |
|-------|--------|---------------|
| `leave_policies` | leave_type | `'Annual'`, `'Sick'`, `'Casual'`, `'Unpaid'`, **`'Parental'`**, `'Other'` |
| `leave_requests` | leave_type | `'Annual'`, `'Sick'`, `'Casual'`, `'Unpaid'`, `'Other'` |

`'Parental'` is present in `leave_policies` but absent from `leave_requests`. A policy for parental leave can be configured, but no leave request can be filed under that type at the database level. This is a functional inconsistency.

Source: `002_workflow_schema.sql` (both tables).

---

### 5.2 Missing `grade_bands` Table (Critical)

`compensation_bands` (migration 012) has a FK:
```sql
CONSTRAINT fk_compensation_bands_grade_band
    FOREIGN KEY (grade_band_id) REFERENCES grade_bands (grade_band_id)
```

The `grade_bands` table is **not defined in any of the 13 migration files**. A search of the migrations directory confirms only this one reference. If migrations are applied in order without `grade_bands` being pre-existing, migration 012 will fail at the `compensation_bands` CREATE. Source: `012_compensation_domain.sql` line 28.

---

### 5.3 Multi-Tenant FK Pattern Broken in Migrations 012–013

Migrations 001–010 use compound `(tenant_id, <id>)` foreign keys uniformly. Migrations 012 and 013 revert to single-column FKs on `employee_id`, `compensation_band_id`, `benefits_plan_id`, and `travel_request_id`. This means:
- Cross-tenant data references are no longer prevented at the DB level for these tables.
- The `(tenant_id, <entity_id>)` unique constraint is absent from `salary_revisions`, `allowances`, `travel_requests`, and `travel_itinerary_segments`.

Source: `012_compensation_domain.sql`, `013_travel_domain.sql`.

---

### 5.4 Workflow Table Status Enum Case Inconsistency

`workflow_instances.status` and `workflow_steps.status` use lowercase values (`'pending'`, `'completed'`, `'approved'`, `'rejected'`), while all other status columns across the schema use PascalCase (`'Active'`, `'Draft'`, `'Submitted'`, etc.). This is an inconsistency that could cause application-level bugs if status values are compared without case normalization.

Source: `003_centralized_workflow_engine.sql`.

---

### 5.5 `helpdesk_tickets` Missing CHECK Constraints

`helpdesk_tickets.priority` and `helpdesk_tickets.status` are declared as `VARCHAR(20) NOT NULL` with no CHECK constraints. All comparable status/priority columns elsewhere in the schema have DB-level CHECK constraints. Allowed values are TBD – REQUIRES VERIFICATION from application code.

Source: `011_addon_domains.sql`.

---

### 5.6 `benefits_plans.plan_type` Missing CHECK Constraint

`plan_type VARCHAR(50) NOT NULL` has no CHECK constraint defining allowed plan types. Allowed values are TBD – REQUIRES VERIFICATION.

Source: `012_compensation_domain.sql`.

---

### 5.7 `learning_paths.status` Missing CHECK Constraint

`status VARCHAR(20) NOT NULL DEFAULT 'Active'` has no CHECK constraint. Allowed values beyond `'Active'` are TBD – REQUIRES VERIFICATION.

Source: `011_addon_domains.sql`.

---

### 5.8 Inconsistent `ON DELETE` for `review_cycle_id` FK

All three performance tables that reference `performance_review_cycles` via `review_cycle_id` treat deletion differently:

| Table | FK Name | On Delete |
|-------|---------|-----------|
| `performance_goals` | fk_performance_goals_cycle | RESTRICT |
| `performance_feedback` | fk_performance_feedback_cycle | SET NULL |
| `performance_pip_plans` | fk_performance_pip_plans_cycle | SET NULL |

Goals are blocked from orphaning; feedback and PIPs are allowed to survive a deleted cycle. Whether this is intentional is TBD – REQUIRES VERIFICATION.

Source: `002_workflow_schema.sql`.

---

### 5.9 UUID Auto-Generation Missing in Migration 011

Tables in `011_addon_domains.sql` declare UUID primary keys without `DEFAULT uuid_generate_v4()`:
- `helpdesk_tickets.ticket_id`
- `helpdesk_ticket_sla_events.event_id`
- `workforce_intelligence_snapshots.snapshot_id`
- `learning_paths.learning_path_id`
- `workforce_cost_plans.plan_id`

The application must supply UUIDs for these columns on INSERT. All tables in migrations 001–010 and 012–013 use `DEFAULT uuid_generate_v4()`.

Source: `011_addon_domains.sql`.

---

### 5.10 Migration Filename / Content Mismatch

| Migration Filename | Actual Primary Content |
|-------------------|----------------------|
| `002_workflow_schema.sql` | Core domain tables (attendance, leave, payroll, hiring, performance) — not workflow |
| `007_event_outbox.sql` | `service_outbox` and `processed_events` — not the `event_outbox` table |
| `008_background_jobs_schema.sql` | `event_outbox`, `background_jobs`, `background_job_failures` — contains the misnamed table |

---

## 6. Tables Referencing Out-of-Scope Features (`011_addon_domains.sql`)

Per `docs/00_authority/FEATURE_SCOPE.md`, the following features are OUT OF SCOPE:

| Out-of-Scope Feature | Table in `011_addon_domains.sql` | Finding |
|---------------------|----------------------------------|---------|
| Learning Management System (LMS) | `learning_paths` | Table exists with no corresponding service, no FK enforcement, no indexes. Out of scope per FEATURE_SCOPE.md. |

No other tables in migration 011 directly map to a confirmed out-of-scope feature. `workforce_intelligence_snapshots` and `workforce_cost_plans` are not explicitly named as out-of-scope features but have no corresponding feature entry in FEATURE_SCOPE.md — TBD – REQUIRES VERIFICATION.

---

## 7. Migration Ordering Dependencies

The following dependency chain must be respected (lower numbers must run before higher numbers):

| Must Run First | Required By | Reason |
|---------------|-------------|--------|
| 001 (departments, roles, employees) | 002 | attendance_records, leave_requests, payroll_records, job_postings, candidates, interviews, all performance tables FK to employees, departments, or roles |
| 001 (employees) | 001 itself | departments.head_employee_id FK to employees — circular dep resolved by deferred DO block in 001 |
| 001 (employees, departments) | 010 | engagement_surveys FKs to employees and departments |
| 002 (performance_review_cycles) | 002 itself | performance_goals, performance_feedback, performance_calibrations, performance_pip_plans FK to performance_review_cycles — all in same file |
| 002 (candidates) | 002 itself | candidate_stage_transitions and interviews FK to candidates — all in same file |
| 002 (performance_pip_plans) | 002 itself | performance_pip_milestones FK to performance_pip_plans — same file |
| 003 (workflow_definitions) | 003 | workflow_instances FK to workflow_definitions — same file |
| 003 (workflow_instances) | 003 | workflow_steps FK to workflow_instances — same file |
| 003 (workflow_steps) | 003 | workflow_history FK to workflow_steps — same file |
| 004 (user_accounts) | 004 | role_bindings FK to user_accounts; sessions FK to user_accounts — same file |
| 004 (sessions) | 004 | refresh_tokens FK to sessions — same file |
| 005 (tenants) | 006 | notification_templates, notification_messages, delivery_attempts, notification_preferences all FK to tenants |
| 005 (tenants) | 009 | audit_records FK to tenants |
| 006 (notification_templates) | 006 | notification_messages FK to notification_templates — same file |
| 006 (notification_messages) | 006 | delivery_attempts FK to notification_messages — same file |
| 008 (background_jobs) | 008 | background_job_failures FK to background_jobs — same file |
| 010 (engagement_surveys) | 010 | all child tables FK to engagement_surveys — same file |
| 011 (helpdesk_tickets) | 011 | helpdesk_ticket_sla_events FK to helpdesk_tickets — same file |
| 001 (employees) | 012 | salary_revisions, benefits_enrollments, allowances FK to employees |
| 012 (compensation_bands) | 012 | salary_revisions FK to compensation_bands — same file |
| 012 (benefits_plans) | 012 | benefits_enrollments FK to benefits_plans — same file |
| *(grade_bands — MISSING)* | 012 | compensation_bands FK to grade_bands — table not found in any migration |
| 001 (employees) | 013 | travel_requests FK to employees |
| 013 (travel_requests) | 013 | travel_itinerary_segments FK to travel_requests — same file |

**Critical ordering note:** Migration 005 (tenants) runs after migrations 001–004 which already create domain tables with `tenant_id` columns. Those early tables have no FK to `tenants` — the tenant_id is an unvalidated string in migrations 001–004. Only tables from migration 006 onward enforce the FK to `tenants`.

---

## 8. Summary of Critical Findings

| Priority | Finding | Source |
|----------|---------|--------|
| CRITICAL | `grade_bands` table not defined anywhere — migration 012 will fail at runtime | 012_compensation_domain.sql |
| CRITICAL | `leave_type = 'Parental'` allowed in `leave_policies` but blocked in `leave_requests` — Parental leave cannot be requested | 002_workflow_schema.sql |
| HIGH | Migrations 012–013 break the compound multi-tenant FK pattern; cross-tenant references not prevented at DB level | 012, 013 |
| HIGH | `learning_paths` table present for out-of-scope LMS feature | 011_addon_domains.sql |
| MEDIUM | Workflow status enums use lowercase; all other statuses use PascalCase | 003_centralized_workflow_engine.sql |
| MEDIUM | Two separate outbox implementations (`service_outbox` vs `event_outbox`) with unclear relationship | 007, 008 |
| MEDIUM | `helpdesk_tickets.priority` and `.status` have no CHECK constraints; allowed values undocumented in DB | 011_addon_domains.sql |
| MEDIUM | Inconsistent ON DELETE behavior for `review_cycle_id` across performance tables | 002_workflow_schema.sql |
| LOW | Migration 011 tables missing `DEFAULT uuid_generate_v4()` — application must supply UUIDs | 011_addon_domains.sql |
| LOW | Migration filename / content mismatch for 002, 007, 008 | 002, 007, 008 |
| INFO | `tenants` table created at migration 005; domain tables in 001–004 carry tenant_id with no FK enforcement | 001–005 |
