from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from country.base.banking_interface import BankingInterface
from core.country_resolver import CountryResolver
from event_contract import EventRegistry, emit_canonical_event
from tenant_support import DEFAULT_TENANT_ID


# ---------------------------------------------------------------------------
# Enums & Value Objects
# ---------------------------------------------------------------------------

class DisbursementState(str, Enum):
    PENDING = "PENDING"
    GENERATED = "GENERATED"
    SUBMITTED = "SUBMITTED"
    # SPEC §18 canonical state names: bank received/credited/rejected the file
    SENT = "SENT"           # bank acknowledged receipt of the salary file
    ACCEPTED = "ACCEPTED"   # bank confirmed all individual credits processed
    REJECTED = "REJECTED"   # bank rejected the file (format error, insufficient funds, etc.)
    CONFIRMED = "CONFIRMED" # legacy alias for ACCEPTED — kept for backward compat
    RECONCILED = "RECONCILED"
    FAILED = "FAILED"
    RETRY = "RETRY"


class PaymentMethod(str, Enum):
    RAAST = "RAAST"
    BANK_FILE = "BANK_FILE"


@dataclass
class DisbursementBatch:
    disbursement_id: str
    organization_id: str
    period: str
    method: PaymentMethod
    state: DisbursementState = DisbursementState.PENDING
    employee_count: int = 0
    total_amount: str = "0.00"
    bank_format: str | None = None
    export_payload: dict | None = None
    submitted_at: str | None = None
    confirmed_at: str | None = None
    created_at: str = field(default_factory=lambda: _now())
    updated_at: str = field(default_factory=lambda: _now())


@dataclass
class PaymentRecord:
    payment_id: str
    disbursement_id: str
    employee_id: str
    expected_amount: str
    paid_amount: str | None = None
    status: str = "pending"
    failure_reason: str | None = None
    confirmed_at: str | None = None
    created_at: str = field(default_factory=lambda: _now())


@dataclass
class ReconciliationReport:
    reconciliation_id: str
    disbursement_id: str
    period: str
    summary: dict = field(default_factory=dict)
    mismatches: list[dict] = field(default_factory=list)
    missing_payments: list[str] = field(default_factory=list)
    failures: list[dict] = field(default_factory=list)
    unmatched_payments: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: _now())


@dataclass
class EmployeeBankAccount:
    account_id: str
    employee_id: str
    organization_id: str
    iban: str
    bank_code: str
    account_holder: str
    is_primary: bool = True
    is_verified: bool = False
    created_at: str = field(default_factory=lambda: _now())
    updated_at: str = field(default_factory=lambda: _now())


# ---------------------------------------------------------------------------
# In-process stores (replace with DB repository in production)
# ---------------------------------------------------------------------------

_batches: dict[str, DisbursementBatch] = {}
_payments: dict[str, PaymentRecord] = {}
_reconciliations: dict[str, ReconciliationReport] = {}
_bank_accounts: dict[str, EmployeeBankAccount] = {}
_outbox: list[dict] = []
_registry = EventRegistry()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _transition(batch: DisbursementBatch, new_state: DisbursementState) -> None:
    batch.state = new_state
    batch.updated_at = _now()


# ---------------------------------------------------------------------------
# BankService — disbursement, Raast payouts, reconciliation
# ---------------------------------------------------------------------------

class BankService:
    """
    Bridges payroll-service and ewa-financial-service to banking channels.

    Responsibilities:
    - Generate bank-specific salary disbursement files (CSV/Excel per bank format).
    - Execute Raast instant payment exports.
    - Track payment status per employee per pay period.
    - Run reconciliation against payroll records.

    Does NOT own payroll calculations — receives finalized payroll data and executes disbursement only.
    Country-specific banking logic is accessed via CountryResolver → BankingInterface only.

    Audit: All state-transition methods produce an immutable audit record per BEHAVIOR SPEC §10.
    """

    def __init__(self, resolver: CountryResolver | None = None) -> None:
        self._resolver = resolver
        self._audit_log: list[dict] = []   # replace with persistent store in production
        self._outbox: list[dict] = _outbox
        self._registry: EventRegistry = _registry

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    def _audit(
        self,
        action: str,
        entity_id: str,
        actor: str,
        before_state: str | None,
        after_state: str,
        extra: dict | None = None,
    ) -> None:
        """
        Emit an immutable audit record for every state-transition.
        BEHAVIOR SPEC §10 — disbursement state transitions must be logged.
        Fields: timestamp, actor, action, affected_entities, result.
        """
        record = {
            "timestamp": _now(),
            "actor": actor,
            "action": action,
            "affected_entities": {"disbursement_id": entity_id},
            "result": {
                "before_state": before_state,
                "after_state": after_state,
                **(extra or {}),
            },
        }
        self._audit_log.append(record)

    def get_audit_log(self) -> list[dict]:
        """Return a copy of all audit records for this service instance."""
        return list(self._audit_log)

    def _get_banking_adapter(self, organization_id: str) -> BankingInterface:
        """Resolve the country banking adapter for the given org. Raises if no resolver configured."""
        if self._resolver is None:
            raise RuntimeError(
                "BankService requires a CountryResolver to execute disbursements. "
                "Inject one at construction time."
            )
        adapter = self._resolver.resolve(organization_id)
        if not hasattr(adapter, "banking"):
            raise RuntimeError(
                f"Adapter for org {organization_id} does not implement a banking attribute."
            )
        return adapter.banking

    # ------------------------------------------------------------------
    # Disbursement batch management
    # ------------------------------------------------------------------

    def create_disbursement(
        self,
        organization_id: str,
        period: str,
        method: str,
        employees: list[dict],
        bank_format: str | None = None,
        actor: str = "system",
    ) -> DisbursementBatch:
        """
        Initiate a disbursement batch. Validates employees and calculates totals.
        Triggers after PayrollPaid event.
        """
        from decimal import Decimal
        total = sum(Decimal(str(e.get("net_salary", 0))) for e in employees)

        batch = DisbursementBatch(
            disbursement_id=str(uuid.uuid4()),
            organization_id=organization_id,
            period=period,
            method=PaymentMethod(method),
            employee_count=len(employees),
            total_amount=f"{total:.2f}",
            bank_format=bank_format,
        )
        _batches[batch.disbursement_id] = batch
        emit_canonical_event(
            self._outbox,
            legacy_event_name="DisbursementBatchCreated",
            data={"disbursement_id": batch.disbursement_id, "organization_id": organization_id,
                  "period": period, "method": method, "employee_count": batch.employee_count,
                  "total_amount": batch.total_amount},
            source="bank-service",
            tenant_id=organization_id,
            registry=self._registry,
        )

        for emp in employees:
            pr = PaymentRecord(
                payment_id=str(uuid.uuid4()),
                disbursement_id=batch.disbursement_id,
                employee_id=str(emp["employee_id"]),
                expected_amount=f"{Decimal(str(emp.get('net_salary', 0))):.2f}",
            )
            _payments[pr.payment_id] = pr

        return batch

    def get_disbursement(self, disbursement_id: str) -> DisbursementBatch | None:
        return _batches.get(disbursement_id)

    def list_disbursements(
        self,
        period: str | None = None,
        status: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> list[DisbursementBatch]:
        results = list(_batches.values())
        if period:
            results = [b for b in results if b.period == period]
        if status:
            results = [b for b in results if b.state == status]
        if cursor:
            ids = sorted(_batches.keys())
            start = ids.index(cursor) + 1 if cursor in ids else 0
            results = [b for b in results if b.disbursement_id in ids[start:]]
        return results[:limit]

    # ------------------------------------------------------------------
    # Disbursement execution
    # ------------------------------------------------------------------

    def execute_disbursement(
        self,
        disbursement_id: str,
        payroll_data: dict[str, Any],
        actor: str = "system",
    ) -> dict[str, Any]:
        """
        Generate bank export file or Raast payment batch and mark as SUBMITTED.
        Actual transmission to bank/Raast is handled by the integrations layer.
        """
        batch = self._require_batch(disbursement_id, DisbursementState.PENDING)
        banking = self._get_banking_adapter(batch.organization_id)

        if batch.method == PaymentMethod.RAAST:
            export = banking.build_raast_payment_export(payroll_data)
        else:
            fmt = batch.bank_format or "standard"
            export = {
                "csv": banking.generate_salary_bank_csv({**payroll_data, "bank_format": fmt}),
                "excel": banking.generate_salary_bank_excel_rows({**payroll_data, "bank_format": fmt}),
                "bank_format": fmt,
            }

        batch.export_payload = export
        batch.submitted_at = _now()
        _transition(batch, DisbursementState.SUBMITTED)
        self._audit("execute_disbursement", disbursement_id, actor, "PENDING", batch.state.value,
                    {"method": batch.method.value})
        emit_canonical_event(
            self._outbox,
            legacy_event_name="DisbursementSubmitted",
            data={"disbursement_id": disbursement_id, "organization_id": batch.organization_id,
                  "method": batch.method.value, "period": batch.period},
            source="bank-service",
            tenant_id=batch.organization_id,
            registry=self._registry,
        )
        return {"disbursement_id": disbursement_id, "state": batch.state, "export": export}

    # ------------------------------------------------------------------
    # Payment status
    # ------------------------------------------------------------------

    def list_payments(
        self,
        disbursement_id: str | None = None,
        employee_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> list[PaymentRecord]:
        results = list(_payments.values())
        if disbursement_id:
            results = [p for p in results if p.disbursement_id == disbursement_id]
        if employee_id:
            results = [p for p in results if p.employee_id == employee_id]
        if status:
            results = [p for p in results if p.status == status]
        return results[:limit]

    def confirm_payment(self, payment_id: str, paid_amount: str, actor: str = "system") -> PaymentRecord:
        pr = _payments.get(payment_id)
        if pr is None:
            raise ValueError(f"Payment {payment_id} not found")
        pr.paid_amount = paid_amount
        pr.status = "confirmed"
        pr.confirmed_at = _now()
        batch = _batches.get(pr.disbursement_id)
        emit_canonical_event(
            self._outbox,
            legacy_event_name="PaymentConfirmed",
            data={"payment_id": payment_id, "disbursement_id": pr.disbursement_id,
                  "employee_id": pr.employee_id, "paid_amount": paid_amount},
            source="bank-service",
            tenant_id=batch.organization_id if batch else DEFAULT_TENANT_ID,
            registry=self._registry,
        )
        return pr

    def fail_payment(self, payment_id: str, reason: str, actor: str = "system") -> PaymentRecord:
        pr = _payments.get(payment_id)
        if pr is None:
            raise ValueError(f"Payment {payment_id} not found")
        pr.status = "failed"
        pr.failure_reason = reason
        batch = _batches.get(pr.disbursement_id)
        emit_canonical_event(
            self._outbox,
            legacy_event_name="PaymentFailed",
            data={"payment_id": payment_id, "disbursement_id": pr.disbursement_id,
                  "employee_id": pr.employee_id, "reason": reason},
            source="bank-service",
            tenant_id=batch.organization_id if batch else DEFAULT_TENANT_ID,
            registry=self._registry,
        )
        return pr

    # ------------------------------------------------------------------
    # Reconciliation
    # ------------------------------------------------------------------

    def run_reconciliation(
        self,
        disbursement_id: str,
        payroll_rows: list[dict],
        payment_rows: list[dict],
        actor: str = "system",
    ) -> ReconciliationReport:
        """
        Match payment confirmations against payroll records.
        Flags mismatches, missing payments, and failures.
        """
        batch = _batches.get(disbursement_id)
        org_id = batch.organization_id if batch else None
        if org_id is None:
            raise ValueError(f"Disbursement {disbursement_id} not found")
        banking = self._get_banking_adapter(org_id)
        result = banking.reconcile_payroll_payments({
            "payroll": payroll_rows,
            "payments": payment_rows,
        })
        period = batch.period if batch else "unknown"

        report = ReconciliationReport(
            reconciliation_id=str(uuid.uuid4()),
            disbursement_id=disbursement_id,
            period=period,
            summary=result["summary"],
            mismatches=result["mismatches"],
            missing_payments=result["missing_payments"],
            failures=result["failures"],
            unmatched_payments=result["unmatched_payments"],
        )
        _reconciliations[report.reconciliation_id] = report

        before_state = batch.state.value if batch else "unknown"
        if batch and result["summary"].get("is_balanced"):
            _transition(batch, DisbursementState.RECONCILED)
            self._audit("run_reconciliation", disbursement_id, actor, before_state, "RECONCILED",
                        {"is_balanced": True})
            emit_canonical_event(
                self._outbox,
                legacy_event_name="ReconciliationCompleted",
                data={"reconciliation_id": report.reconciliation_id,
                      "disbursement_id": disbursement_id, "organization_id": batch.organization_id,
                      "period": period, "is_balanced": True},
                source="bank-service",
                tenant_id=batch.organization_id,
                registry=self._registry,
            )
        elif batch:
            batch.updated_at = _now()
            self._audit("run_reconciliation", disbursement_id, actor, before_state, before_state,
                        {"is_balanced": False, "mismatches": len(result.get("mismatches", []))})
            emit_canonical_event(
                self._outbox,
                legacy_event_name="ReconciliationExceptionRaised",
                data={"reconciliation_id": report.reconciliation_id,
                      "disbursement_id": disbursement_id, "organization_id": batch.organization_id,
                      "mismatch_count": len(result.get("mismatches", []))},
                source="bank-service",
                tenant_id=batch.organization_id,
                registry=self._registry,
            )

        return report

    def get_reconciliation(self, reconciliation_id: str) -> ReconciliationReport | None:
        return _reconciliations.get(reconciliation_id)

    # ------------------------------------------------------------------
    # SPEC §18 — canonical payout state transitions
    # ------------------------------------------------------------------

    def mark_sent(self, disbursement_id: str, actor: str = "system") -> DisbursementBatch:
        """Bank has acknowledged receipt of the salary file (SUBMITTED → SENT)."""
        batch = self._require_batch(disbursement_id, DisbursementState.SUBMITTED)
        _transition(batch, DisbursementState.SENT)
        self._audit("mark_sent", disbursement_id, actor, "SUBMITTED", "SENT")
        return batch

    def mark_accepted(self, disbursement_id: str, actor: str = "system") -> DisbursementBatch:
        """Bank confirms all individual credits have been processed (SENT → ACCEPTED)."""
        batch = self._require_batch(disbursement_id, DisbursementState.SENT)
        batch.confirmed_at = _now()
        _transition(batch, DisbursementState.ACCEPTED)
        self._audit("mark_accepted", disbursement_id, actor, "SENT", "ACCEPTED")
        return batch

    def mark_rejected(
        self,
        disbursement_id: str,
        reason: str,
        actor: str = "system",
    ) -> DisbursementBatch:
        """Bank rejected the salary file — format error, insufficient funds, etc.
        Can occur from SUBMITTED or SENT state."""
        batch = _batches.get(disbursement_id)
        if batch is None:
            raise ValueError(f"Disbursement {disbursement_id} not found")
        before_state = batch.state.value
        if batch.state not in (DisbursementState.SUBMITTED, DisbursementState.SENT):
            raise ValueError(
                f"Disbursement {disbursement_id} cannot be rejected from state {batch.state}"
            )
        _transition(batch, DisbursementState.REJECTED)
        self._audit("mark_rejected", disbursement_id, actor, before_state, "REJECTED",
                    {"reason": reason})
        return batch

    # ------------------------------------------------------------------
    # Raast single payout (EWA / salary advance)
    # ------------------------------------------------------------------

    def raast_payout(
        self,
        organization_id: str,
        batch_id: str,
        company: str,
        payments: list[dict],
        payroll_total: float | None = None,
        actor: str = "system",
    ) -> dict[str, Any]:
        """
        Single Raast payout for EWA or advance disbursements.
        Triggered by EWADisbursed / AdvanceDisbursed events.
        """
        banking = self._get_banking_adapter(organization_id)
        payload: dict[str, Any] = {
            "batch_id": batch_id,
            "company": company,
            "payments": payments,
        }
        if payroll_total is not None:
            payload["payroll_total"] = payroll_total
        return banking.build_raast_payment_export(payload)

    # ------------------------------------------------------------------
    # Bank account management
    # ------------------------------------------------------------------

    def register_bank_account(
        self,
        employee_id: str,
        organization_id: str,
        iban: str,
        bank_code: str,
        account_holder: str,
        actor: str = "system",
    ) -> EmployeeBankAccount:
        acct = EmployeeBankAccount(
            account_id=str(uuid.uuid4()),
            employee_id=employee_id,
            organization_id=organization_id,
            iban=iban,
            bank_code=bank_code,
            account_holder=account_holder,
        )
        _bank_accounts[acct.account_id] = acct
        return acct

    def get_bank_accounts(self, employee_id: str) -> list[EmployeeBankAccount]:
        return [a for a in _bank_accounts.values() if a.employee_id == employee_id]

    def update_bank_account(
        self,
        account_id: str,
        updates: dict[str, Any],
        actor: str = "system",
    ) -> EmployeeBankAccount:
        acct = _bank_accounts.get(account_id)
        if acct is None:
            raise ValueError(f"Bank account {account_id} not found")
        for key in ("iban", "bank_code", "account_holder", "is_primary"):
            if key in updates:
                setattr(acct, key, updates[key])
        acct.updated_at = _now()
        acct.is_verified = False  # re-verification required after any update
        return acct

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _require_batch(self, disbursement_id: str, expected_state: DisbursementState) -> DisbursementBatch:
        batch = _batches.get(disbursement_id)
        if batch is None:
            raise ValueError(f"Disbursement {disbursement_id} not found")
        if batch.state != expected_state:
            raise ValueError(
                f"Disbursement {disbursement_id} is in state {batch.state}, expected {expected_state}"
            )
        return batch
