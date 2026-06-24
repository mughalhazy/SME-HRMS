# System Purpose and Design Principles

## System Identity

**AURA HRMS — Pakistan Compliance OS + AI Workforce Decision System**

## Core Purpose

Build a system that:
- Guarantees payroll accuracy (zero-error target)
- Automates Pakistan statutory compliance (FBR, EOBI, PESSI/SESSI)
- Converts HR from data-entry into a decision system
- Supports multi-country expansion WITHOUT changing core services

## Core Truth

> This is NOT an HR tool.
> This is a **TRUST INFRASTRUCTURE** for workforce operations.

Every design decision must be evaluated against this truth. If a feature makes data visible but doesn't improve trust, compliance, or decision quality — it doesn't belong at the core.

---

## Design Principles

### P1 — Compliance is the product
Statutory compliance (FBR, EOBI, PESSI) is not a feature — it is the foundation. Every payroll run must be compliance-validated before finalization. No exceptions.

### P2 — Payroll must never break
A payroll run that cannot complete cleanly must halt and surface errors explicitly — never partially apply. Zero-error is the target. Any run that would produce incorrect output must fail loudly.

### P3 — Decisions > Dashboards
Surfaces must lead with actions, not data. Every screen should help users identify a problem, decide, and act — not explore data. Replace passive charts with Decision Cards, exception queues, and guided actions.

### P4 — AI must be explainable and reversible
Every AI output (anomaly flag, risk score, recommendation) must include a human-readable explanation and confidence level. High-risk decisions require human-in-the-loop approval. No silent automation.

### P5 — Country logic must be isolated
All statutory logic lives in `country/{country}/` adapters only. Core services never contain country conditionals. Adding a new country requires an adapter only — no service changes.

### P6 — System must work on mobile-first environments
Optimize for low bandwidth, compact payloads, and unstable networks. Return only fields required for the current step. Mobile is not a reduced feature set — it is the primary delivery environment for many users.

### P7 — WhatsApp is an access channel, not a feature
WhatsApp is a first-class employee interface that executes real HRMS workflows (payslip, leave, approvals). It is not a notification relay. Actions via WhatsApp are subject to the same RBAC and audit trail as web UI actions.

---

## Architecture Principle Summary

| Layer | Rule |
|---|---|
| Data | Immutable audit logs; cross-service integration via events and read models only |
| Domain | Each service owns its business logic and exposes interfaces |
| Country | ALL statutory logic lives in `country/{country}/` adapters |
| Services | Orchestration only; NO country logic; NO hardcoded jurisdictions |
| Integrations | FBR, EOBI, PESSI, bank, Raast adapters in integration layer |
| Experience | Decision-first; actions surface before data; confidence always shown |

---

## Strategic Product Model

Five layers. Each layer depends on the one below it being stable.

| Layer | Content | Build phase |
|---|---|---|
| Layer 1 | Payroll + Compliance Core | Phase 1 + 2 |
| Layer 2 | Attendance + Workforce Ops | Phase 1 |
| Layer 3 | Decision Engine (AI) | Phase 3 |
| Layer 4 | Access Layer (Mobile + WhatsApp) | Phase 4 |
| Layer 5 | Multi-country expansion | Phase 5 |

This model defines the product from the market up. A feature that does not fit one of these five layers does not belong in the core system.

---

## What This System Is NOT

- Not a data warehouse or reporting portal
- Not a passive HR record system
- Not a country-specific payroll tool (it is country-agnostic by design)
- Not a chatbot (WhatsApp executes real workflows)
- Not a dashboard system (decisions replace dashboards)

---

## Related Documents
- Architecture: `docs/canon/service-map.md`
- Country abstraction: `docs/canon/country-layer.md`
- Decision system: `docs/canon/decision-system.md`
- Experience layer: `docs/specs/experience-layer.md`
- Roadmap: `docs/system/roadmap.md`
- Success criteria: `docs/system/success-criteria.md`
