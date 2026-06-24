C1 — expense-service vs ewa-financial-service
DECISION: SEPARATE

- expense-service:
  → reimbursements (claims, receipts, approvals)
  → accounting-facing

- ewa-financial-service:
  → earned wage access
  → salary advances
  → payroll-linked finance

RULE:
Expense ≠ Payroll-linked finance

---

C2 — helpdesk-service
DECISION: ADD-ON (NOT CORE HRMS)

- belongs to:
  → HR service delivery / ticketing
  → employee queries (HR ops)

- NOT required for:
  → payroll
  → compliance
  → core HR

RULE:
Keep OUT of core system.
Add later if needed.

---

C3 — automation-service
DECISION: INFRASTRUCTURE SERVICE (NOT BUSINESS DOMAIN)

- yes → same concept as automation_service.py
- role:
  → workflows
  → triggers
  → scheduling
  → orchestration

DO NOT:
- treat as business module

RULE:
Infrastructure layer, not HR feature

---

C4 — decision-service
DECISION: STANDALONE SERVICE (CRITICAL)

NOT inside payroll.

WHY:
- decisions span:
  → payroll
  → attendance
  → compliance
  → performance

IF inside payroll:
→ architecture breaks

RULE:
decision-service = cross-domain intelligence layer

---

C5 — WhatsApp
DECISION: STANDALONE SERVICE (NOT JUST INTEGRATION)

NOT just adapter.

WHY:
- requires:
  → identity mapping
  → session handling
  → security (OTP)
  → workflow execution

STRUCTURE:
- whatsapp-service
  → sits in integration layer
  → exposes API to system

RULE:
Treat as ACCESS CHANNEL SERVICE

---

FINAL SERVICE MAP (CLEAN)

CORE DOMAIN:
- payroll-service
- compliance-service
- attendance-service
- employee-service

FINANCIAL:
- ewa-financial-service
- expense-service

INTELLIGENCE:
- decision-service

INFRASTRUCTURE:
- automation-service

INTEGRATION / ACCESS:
- whatsapp-service
- bank-service
- government-adapters

OPTIONAL:
- helpdesk-service