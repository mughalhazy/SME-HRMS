from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from config.integrations import load_integrations_config
from integrations.http_client import IntegrationHTTPError, JsonHTTPClient, RetryPolicy


class AccountingAdapter(ABC):
    @abstractmethod
    def export_payroll_journal(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(frozen=True)
class SAPConnectorConfig:
    base_url: str
    company_code: str
    auth_token: str
    timeout_seconds: float = 10.0
    retry_attempts: int = 3

    @classmethod
    def from_env(cls) -> "SAPConnectorConfig":
        shared = load_integrations_config().sap
        return cls(
            base_url=shared.endpoint,
            company_code=os.getenv("SAP_COMPANY_CODE", ""),
            auth_token=shared.auth_token,
            timeout_seconds=shared.timeout_seconds,
            retry_attempts=shared.retry_attempts,
        )


class QuickBooksAdapter(AccountingAdapter):
    def __init__(self, *, config: dict[str, Any] | None = None, http_client: JsonHTTPClient | None = None) -> None:
        cfg = config or {}
        shared = load_integrations_config().quickbooks
        self.base_url = str(cfg.get("base_url") or shared.endpoint).rstrip("/")
        self.realm_id = str(cfg.get("realm_id") or os.getenv("QUICKBOOKS_REALM_ID", ""))
        self.access_token = str(cfg.get("access_token") or shared.auth_token)
        timeout = float(cfg.get("timeout_seconds") or shared.timeout_seconds)
        attempts = int(cfg.get("retry_attempts") or shared.retry_attempts)
        self.http_client = http_client or JsonHTTPClient(timeout_seconds=timeout, retry_policy=RetryPolicy(attempts=attempts))

    def export_payroll_journal(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.base_url or not self.realm_id or not self.access_token:
            return {"provider": "QuickBooks", "status": "failure", "errors": ["Missing QuickBooks config (base_url/realm_id/access_token)."]}

        endpoint = f"{self.base_url}/v3/company/{self.realm_id}/journalentry"
        quickbooks_payload = {
            "Line": list(payload.get("journal_entries", [])),
            "PrivateNote": str(payload.get("memo", "Payroll Journal")),
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        try:
            response = self.http_client.post_json(endpoint, quickbooks_payload, headers=headers)
            body = response.get("body", {})
            journal_entry = body.get("JournalEntry") or {}
            if not journal_entry.get("Id"):
                return {"provider": "QuickBooks", "status": "failure", "errors": ["QuickBooks response missing JournalEntry.Id"], "raw": body}
            return {
                "provider": "QuickBooks",
                "status": "success",
                "journal_entry_id": str(journal_entry["Id"]),
                "sync_token": str(journal_entry.get("SyncToken", "")),
            }
        except IntegrationHTTPError as exc:
            return {"provider": "QuickBooks", "status": "failure", "errors": [f"{exc.code}: {exc.message}"], "http_status": exc.status_code}


class SAPAdapter(AccountingAdapter):
    """Structured SAP connector interface; concrete transport can be injected per deployment."""

    def __init__(self, config: SAPConnectorConfig, *, http_client: JsonHTTPClient | None = None) -> None:
        self.config = config
        self.http_client = http_client or JsonHTTPClient(
            timeout_seconds=config.timeout_seconds,
            retry_policy=RetryPolicy(attempts=config.retry_attempts),
        )

    def export_payroll_journal(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.config.base_url or not self.config.company_code or not self.config.auth_token:
            return {"provider": "SAP", "status": "failure", "errors": ["Missing SAP config (base_url/company_code/auth_token)."]}

        endpoint = f"{self.config.base_url}/sap/opu/odata/sap/ZPAYROLL_JOURNAL_SRV/JournalEntries"
        sap_payload = {
            "CompanyCode": self.config.company_code,
            "PostingDate": str(payload.get("posting_date", "")),
            "DocumentDate": str(payload.get("document_date", "")),
            "Items": list(payload.get("journal_entries", [])),
            "Reference": str(payload.get("reference", "PAYROLL")),
        }
        try:
            response = self.http_client.post_json(endpoint, sap_payload, headers={"Authorization": f"Bearer {self.config.auth_token}"})
            body = response.get("body", {})
            document_id = body.get("document_id")
            if not document_id:
                return {"provider": "SAP", "status": "failure", "errors": ["SAP response missing document_id"], "raw": body}
            return {"provider": "SAP", "status": "success", "document_id": str(document_id)}
        except IntegrationHTTPError as exc:
            return {"provider": "SAP", "status": "failure", "errors": [f"{exc.code}: {exc.message}"], "http_status": exc.status_code}
