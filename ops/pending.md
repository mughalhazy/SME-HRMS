# Pending Work

## UI Pages (G28)

All backends ready. 10 Next.js pages to build:

| Page | Backend |
|---|---|
| `/app/compliance/page.tsx` | `compliance_api.py` |
| `/app/decisions/page.tsx` | `decision_api.py` |
| `/app/financial-wellness/page.tsx` | `services/finance/ewa.py` |
| `/app/banking/page.tsx` | `banking_api.py` |
| `/app/analytics/page.tsx` | `reporting_analytics_api.py` |
| `/app/helpdesk/page.tsx` | `helpdesk_api.py` |
| `/app/automations/page.tsx` | `automation_api.py` |
| `/app/engagement/page.tsx` | `engagement_api.py` |
| `/app/whatsapp-admin/page.tsx` | `whatsapp_api.py` |
| `/app/expenses/page.tsx` | `expense_api.py` |

## Deferred

| Item | Reason |
|---|---|
| G22 full wiring — `check_payroll_gate()` into `payroll_service.py mark_paid()` | Needs integration test coverage first |
| MN-G07 — International labor standards compliance adapter (SA8000/WRAP/BSCI) for Sialkot/Faisalabad export sector | Needs domain research on international buyer audit standards before any adapter can be designed |
| S8-G07 — Decisions UI page (`ui/app/decisions/page.tsx`, G28b) | UI pages are a separate workstream; `decision_api.py` backend is complete and ready |
