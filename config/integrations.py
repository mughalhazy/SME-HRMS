from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class IntegrationRuntimeConfig:
    environment: str
    endpoint: str
    auth_token: str
    timeout_seconds: float
    retry_attempts: int


@dataclass(frozen=True)
class IntegrationsConfig:
    fbr: IntegrationRuntimeConfig
    eobi: IntegrationRuntimeConfig
    pessi: IntegrationRuntimeConfig
    quickbooks: IntegrationRuntimeConfig
    sap: IntegrationRuntimeConfig


def _env_name() -> str:
    value = os.getenv("INTEGRATION_ENV", "sandbox").strip().lower()
    return "live" if value == "live" else "sandbox"


def _integration_runtime(prefix: str, environment: str) -> IntegrationRuntimeConfig:
    selected_endpoint = os.getenv(f"{prefix}_{environment.upper()}_BASE_URL", "").rstrip("/")
    if not selected_endpoint:
        selected_endpoint = os.getenv(f"{prefix}_BASE_URL", "").rstrip("/")

    return IntegrationRuntimeConfig(
        environment=environment,
        endpoint=selected_endpoint,
        auth_token=os.getenv(f"{prefix}_AUTH_TOKEN", ""),
        timeout_seconds=float(os.getenv(f"{prefix}_TIMEOUT_SECONDS", "10")),
        retry_attempts=int(os.getenv(f"{prefix}_RETRY_ATTEMPTS", "3")),
    )


def load_integrations_config() -> IntegrationsConfig:
    environment = _env_name()
    return IntegrationsConfig(
        fbr=_integration_runtime("PAKISTAN_FBR", environment),
        eobi=_integration_runtime("PAKISTAN_EOBI", environment),
        pessi=_integration_runtime("PAKISTAN_PESSI", environment),
        quickbooks=_integration_runtime("QUICKBOOKS", environment),
        sap=_integration_runtime("SAP", environment),
    )
