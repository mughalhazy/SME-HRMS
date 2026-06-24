# Release Scope

Defines the exact set of services in each release tier. The source of truth for what is live vs. add-on vs. planned.

---

## Core Release — Included by Default

All services below have runtime code and are wired into docker-compose.

| Service | Port | Key capability |
|---|---|---|
| employee-service | 8001 | Workforce master data, org structure |
| attendance-service | 8002 | Attendance capture and validation |
| leave-service | 8003 | Leave lifecycle and approval |
| payroll-service | 8004 | Payroll run, tax, deductions |
| hiring-service | 8005 | Job postings, candidates, hire handoff |
| auth-service | 8006 | Identity, sessions, RBAC |
| notification-service | 8007 | Templates, delivery, preferences |
| compliance-service | 8021 | FBR, EOBI, PESSI statutory lifecycle |
| decision-service | 8022 | Anomaly detection, risk cards, AI guardian |
| bank-service | 8023 | Salary disbursement, Raast, reconciliation |
| whatsapp-service | 8024 | WhatsApp channel — leave, payslip, attendance |
| reporting-analytics-service | 8013 | Operational and compliance reports |
| automation-service | 8017 | Event-triggered and scheduled rules |

---

## Add-On — Separately Deployable

Code exists. Not included in the core release by default. Enabled per tenant/contract.

| Service | Port | Key capability |
|---|---|---|
| helpdesk-service | 8012 | HR tickets, SLA tracking, knowledge base |
| expense-service | 8015 | Expense claims, receipts, approvals |
| ewa-financial-service | — | Earned wage access, salary advances |
| performance-service | 8010 | Goals, OKRs, reviews, calibration |
| engagement-service | 8011 | Surveys, sentiment, response capture |
| integration-service | 8016 | Outbound webhooks, connector dispatch |
| settings-service | 8020 | HR policy configuration |
| search-service | 8014 | Cross-domain search |

---

## Planned — Not Yet Implemented

Defined in canon. No runtime code.

| Service | Blocked on |
|---|---|
| travel-service | Domain build — itineraries, approval flow |
| project-service | Domain build — staffing, allocation |

---

## Country Adapters

| Adapter | Status |
|---|---|
| Pakistan (PK) | Implemented — FBR, EOBI, PESSI, WPPF, WWF, Raast |
| UAE (AE) | Planned — WPS, MOHRE, DEWS (needs domain research) |
| Dummy (XX) | Test only — architecture proof adapter |
