# AUTH AND TENANCY CONTRACT

Status: Draft
Authority Level: Critical
Last Reviewed: 2026-06-15
Owner: AI

---

## 1. PURPOSE

This document captures the authentication and multi-tenancy model exactly as implemented in the backend. It is derived from repository evidence only. It does not redesign, weaken, or propose changes to the model — it documents the mechanism so that future AI sessions and engineers can reason about request authentication, tenant isolation, and session lifecycle without reverse-engineering source code.

This document does NOT disclose secret values (e.g. `JWT_SECRET`). It documents how secrets are used, not their content.

---

## 2. AUTHENTICATION MODEL

### 2.1 Token format

- Algorithm: **HS256** (HMAC-SHA256), explicitly checked.
  - Auth service signs tokens with `hmac.new(self._token_secret, signing_input, hashlib.sha256)` — `backend/services/auth-service/service.py` (`_encode_token`, lines 798-805).
  - Gateway verifies with `verify_hs256_jwt(token, JWT_SECRET, audience=JWT_AUDIENCE, issuer=JWT_ISSUER)` — `backend/jwt_utils.py` (lines 16-50) and `backend/docker/api_gateway_service.py` (line 426).
  - Employee-service independently re-validates the HS256 signature using `createHmac('sha256', TOKEN_SECRET)` and `timingSafeEqual` — `backend/services/employee-service/rbac.middleware.ts` (lines 145-155).
- Token structure: standard JWT — `header.payload.signature`, base64url-encoded segments (`_b64url_encode`/`_b64url_decode`, `service.py` lines 944-951; `jwt_utils.py` lines 11-13).
- Registered claims enforced on every decode (`service.py` `_validate_registered_claims`, lines 826-836; `jwt_utils.py` lines 39-47):
  - `iss` must equal the configured issuer (`sme-hrms.auth-service` default — `service.py` line 179, `api_gateway_service.py` line 53).
  - `aud` must equal the configured audience (`sme-hrms.api` default — `service.py` line 179, `api_gateway_service.py` line 52).
  - `nbf` (not-before) must be ≤ now.
  - `exp` (expiry) must be > now. The gateway's verifier additionally allows a `clock_skew_seconds=5` grace window (`jwt_utils.py` line 22, 40-43).
- Access-token claim payload (`service.py` `_build_token_payload`, lines 680-718):

| Claim | Meaning |
|---|---|
| `sub` | UserAccount.user_id (UUID string) |
| `sid` | session_id — links token to a `SessionRecord` |
| `jti` | access_token_jti — must match the session's current `access_token_jti`; used to invalidate old access tokens on refresh/revoke |
| `tenant_id` | UserAccount.tenant_id |
| `role` | one of `Admin`, `Manager`, `Employee`, `Recruiter`, `PayrollAdmin`, `Service` |
| `employee_id` | linked Employee UUID, nullable |
| `department_id` | linked Department UUID, nullable |
| `capabilities` | sorted list of capability IDs derived from `_ROLE_CAPABILITY_MAP[role]` |
| `scopes` | list of scope strings (e.g. `scope:global`, `department:<uuid>`, `employee:<uuid>`, `service:internal`, `resource:employee-service`) — see §4 |
| `subject_type` | `'service'` if role is `Service`, else `'user'` |
| `iat`, `nbf`, `exp` | standard timestamp claims |
| `iss`, `aud` | issuer/audience strings |

- Minimum secret length enforced at construction: `AuthService.__init__` raises `ValueError` if `token_secret` is shorter than 32 characters (`service.py` lines 180-183). Employee-service enforces the same minimum for `AUTH_TOKEN_SECRET` (`rbac.middleware.ts` lines 118-124).

### 2.2 Token issuance, refresh, and logout flow

All flows are implemented in `backend/services/auth-service/service.py` and exposed via `backend/services/auth-service/api.py`. The capability matrix lists the route category as `/api/v1/auth/*` (`capability-matrix.md` line 25, `CAP-AUT-001`).

1. **Login** (`POST /api/v1/auth/login` → `post_auth_login`, `api.py` lines 25-51; `AuthService.login`, `service.py` lines 312-349):
   - Validates `username`/`password` are non-empty strings.
   - Looks up `UserAccount` by `(tenant_id, normalized_username)`.
   - Verifies password using PBKDF2 (see §6).
   - Rejects with `INVALID_CREDENTIALS` (401) if user not found or password mismatch.
   - Rejects with `ACCOUNT_DISABLED` (403) if `user.active == False`.
   - On success: updates `last_login_at`, calls `_issue_session_tokens`, emits `UserAuthenticated` event, returns `{access_token, refresh_token, token_type: 'Bearer', expires_in, refresh_expires_in, session_id}`.
   - Default TTLs: `ttl_seconds=900` (15 min access token), `refresh_ttl_seconds=604800` (7 days refresh token) — `service.py` line 312. TTLs are validated by `_validate_ttls` (lines 789-796): access token TTL must be 60–3600s, refresh TTL must be 300–2,592,000s (30 days), and refresh TTL must exceed access TTL.

2. **Refresh** (`POST /api/v1/auth/refresh` → `post_auth_refresh`, `api.py` lines 54-78; `AuthService.refresh_session`, `service.py` lines 351-407):
   - Looks up the `SessionRecord` by hashing the supplied `refresh_token` and matching `RefreshTokenRecord.token_hash` (constant-time comparison via `hmac.compare_digest`, `_get_session_by_refresh_token`, lines 736-748).
   - Rejects `TOKEN_REVOKED` if session is revoked, or the matched refresh token has `revoked_at` set.
   - Rejects `TOKEN_EXPIRED` if `session.refresh_expires_at <= now` — and as a side effect revokes the session.
   - Rejects `ACCOUNT_DISABLED` if the user no longer exists or `user.active == False` — also revokes the session.
   - On success: **rotates** the refresh token — generates a new refresh token, marks the old `RefreshTokenRecord.revoked_at`/`replaced_by_token_id`, issues a new `access_token_jti`, extends `refresh_expires_at`, and emits `RefreshTokenRotated`. This is the "rotatable refresh token" pattern referenced in `backend/docs/canon/security-model.md` line 82.

3. **Logout** (`POST /api/v1/auth/logout` → `post_auth_logout`, `api.py` lines 81-105; `AuthService.logout_refresh_token`, `service.py` lines 449-451):
   - Accepts a `refresh_token`, resolves the session, and calls `_revoke_session(..., reason='logout')`.
   - `_revoke_session` (lines 720-734) sets `session.revoked = True`, `revoked_at = now`, `revocation_reason`, audits `auth_logout`, and emits `auth.session.revoked`.
   - A separate `AuthService.logout(token)` (lines 443-447) revokes a session given an **access token** (decodes it, extracts `sid`).

4. **Token validation / principal resolution** (`AuthService.authenticate_token`, `service.py` lines 409-441):
   - Decodes and signature/claim-validates the access token (`_decode_token`).
   - Looks up the session by `sid`; rejects `TOKEN_REVOKED` if session missing or `session.revoked`.
   - Rejects `TOKEN_REVOKED` if the token's `jti` does not match `session.access_token_jti` (i.e., the access token was superseded by a refresh — this is how access tokens are invalidated before their `exp`).
   - Rejects `TOKEN_EXPIRED` if `session.refresh_expires_at <= now` (also revokes the session).
   - Looks up `UserAccount` by `sub`; rejects `ACCOUNT_DISABLED` if missing or inactive.
   - Returns an `AuthenticatedPrincipal` dataclass (`service.py` lines 28-37): `user_id`, `employee_id`, `role`, `department_id`, `tenant_id`, `capabilities`, `scopes`, `subject_type`.

5. **`GET /api/v1/auth/me`** (`get_auth_me`, `api.py` lines 108-139) — returns the authenticated principal's identity, role, tenant, and current session status. Requires `Authorization: Bearer <token>`.

6. **`GET /api/v1/auth/session`** (`get_auth_session`, `api.py` lines 146-168) — returns the current session record for the bearer token.

7. **`GET /api/v1/auth/sessions`** and **`POST /api/v1/auth/sessions/{session_id}/revoke`** (`get_auth_sessions`, `post_auth_session_revoke`, `api.py` lines 171-239) — administrative session listing and revocation (`AuthService.list_sessions`, `revoke_session`, `service.py` lines 465-491). `CAP-AUT-001` (identity and access administration) — per `capability-matrix.md` line 25 and `security-model.md` line 29, this is `Allow` for Admin only, `Deny` for all other roles. **TBD – REQUIRES VERIFICATION**: the auth-service `api.py` handlers do not themselves enforce a capability check on `get_auth_sessions`/`post_auth_session_revoke` — enforcement is expected at the gateway/role layer (see §5).

### 2.3 Gateway-level JWT enforcement

`backend/docker/api_gateway_service.py` (lines 420-431) is the single point where every inbound request (except exempt routes) is checked for a valid bearer token:

```python
_AUTH_EXEMPT_PREFIXES = ("/health", "/ready", "/metrics", "/openapi.json", "/docs", "/api/v1/auth/")
...
if JWT_SECRET and not any(path.startswith(p) for p in _AUTH_EXEMPT_PREFIXES):
    auth_header = headers.get("authorization", "")
    token = auth_header.removeprefix("Bearer ").strip() if auth_header.lower().startswith("bearer ") else ""
    if not token:
        return _error("UNAUTHORIZED", "Missing or malformed Authorization header.", 401)
    claims = verify_hs256_jwt(token, JWT_SECRET, audience=JWT_AUDIENCE, issuer=JWT_ISSUER)
    if claims is None:
        return _error("UNAUTHORIZED", "Token is invalid or expired.", 401)
else:
    claims = None
```

**Exempt route prefixes** (no JWT required at the gateway): `/health`, `/ready`, `/metrics`, `/openapi.json`, `/docs`, `/api/v1/auth/*` — `api_gateway_service.py` line 55. This matches `docs/07_governance/AI_OPERATING_CONTEXT.md` line 104, except that file lists only `/health`, `/ready`, `/metrics`, `/api/v1/auth/*` — the gateway implementation additionally exempts `/openapi.json` and `/docs` (API documentation/spec endpoints, which are static and contain no tenant data).

**Important nuance**: `/api/v1/auth/*` is fully exempt from gateway JWT enforcement — including `GET /api/v1/auth/me`, `GET /api/v1/auth/session`, `GET /api/v1/auth/sessions`, and `POST /api/v1/auth/sessions/{id}/revoke`. These endpoints perform their own bearer-token validation inside `api.py` (`get_auth_me`, `get_auth_session`, etc., each check `authorization_header.startswith('Bearer ')` and call `service.authenticate_token`). The gateway does not additionally verify these tokens, nor does it apply the `_ROUTE_ROLE_MAP` to `/api/v1/auth/*` paths (no entry exists for `/api/v1/auth` in `_ROUTE_ROLE_MAP`, `api_gateway_service.py` lines 66-71). **TBD – REQUIRES VERIFICATION**: whether `/api/v1/auth/sessions` (list/revoke — administrative) should be Admin-only is enforced solely inside the auth-service business logic; no evidence of such a check was found in `service.py` or `api.py` for `list_sessions`/`revoke_session`. This is also flagged as a security gap in `SECURITY_DISCOVERY_REPORT.md`.

If `JWT_SECRET` is unset/empty (`_JWT_SECRET_STR = os.getenv("JWT_SECRET", "")`, line 50), the gateway **skips JWT enforcement entirely** (`if JWT_SECRET and not any(...)`) and sets `claims = None` for all requests — meaning `X-User-Id`/`X-User-Role`/`X-Tenant-Id` headers are not forwarded and `_ROUTE_ROLE_MAP` checks are skipped. This is an environment-configuration dependency, not a code path that can be reached with a valid `JWT_SECRET` configured.

---

## 3. TENANT ID EXTRACTION AND PROPAGATION

### 3.1 Source of truth

`tenant_id` is a claim embedded in the JWT access token at issuance time (`service.py` `_build_token_payload`, line 697: `'tenant_id': user.tenant_id`). Per `docs/07_governance/AI_OPERATING_CONTEXT.md` line 106: "`tenant_id` must be extracted from JWT payload and propagated through request context."

### 3.2 Gateway extraction and propagation

After JWT verification, the gateway (`api_gateway_service.py` lines 433-471):

1. Extracts `jwt_tenant = str(claims.get("tenant_id", ""))`.
2. Compares against an optional `X-Tenant-Id` request header (`header_tenant`). If both are present and **do not match**, the gateway returns `403 FORBIDDEN` with code `FORBIDDEN`, message "Tenant header does not match token." (lines 436-437).
3. Forwards verified principal claims to upstream services as headers:
   - `X-User-Id` = `claims['sub']`
   - `X-User-Role` = `claims['role']`
   - `X-Tenant-Id` = `claims['tenant_id']`
   (lines 468-471)

This means downstream services receive `tenant_id` via the `X-Tenant-Id` header, sourced from the verified JWT — not from client-supplied headers alone (the gateway validates consistency before forwarding).

### 3.3 Service-level tenant context middleware

`backend/middleware/tenant-context.ts` (TypeScript services):

- `resolveTenantId(req)` (lines 10-21) resolves tenant id from, in priority order: `X-Tenant-Id` header → `X-Tenant` header → `req.auth?.tenant_id` (set by the service's own JWT decode) → `req.body.tenant_id` → falls back to `DEFAULT_TENANT_ID = 'tenant-default'` (line 3) via `normalizeTenantId` (lines 5-8).
- `tenantContextMiddleware` (lines 23-29) sets `req.tenantId`, rewrites `req.headers['x-tenant-id']`, and sets response header `X-Tenant-Id`.
- `assertTenantMatch(req, tenantId)` (lines 31-39) throws a `TenantScopeError` (`error.name = 'TenantScopeError'`) if a target entity's `tenant_id` does not match `req.tenantId` — used to prevent cross-tenant entity access within a service.

`backend/services/employee-service/rbac.middleware.ts` performs its own independent JWT decode (`parseAuth`, lines 157-212) and `ensureTenantConsistency` (lines 219-234), which throws `TENANT_SCOPE_VIOLATION` (→ 403 `FORBIDDEN`) if the `X-Tenant-Id`/`X-Tenant` header does not match `auth.tenant_id` from the token. This is a second, independent tenant-consistency check at the service layer, in addition to the gateway's check.

### 3.4 Row-level isolation pattern

Per `docs/00_authority/DOMAIN_MODEL.md` lines 21-28 ("MULTI-TENANCY INVARIANT"):

> Every primary entity table includes:
> - `tenant_id VARCHAR(80) NOT NULL`
> - Unique constraint: `(tenant_id, [entity]_id)`
> - Foreign keys reference `(tenant_id, [entity]_id)` — never `[entity]_id` alone
>
> This is a system-wide constraint. No exceptions.

This pattern is verified directly in `backend/deployment/migrations/001_core_schema.sql` and `004_persistence_normalization.sql`, e.g.:

- `departments`: `CONSTRAINT uq_departments_tenant_department UNIQUE (tenant_id, department_id)` (001, line 12).
- `employees`: `CONSTRAINT uq_employees_tenant_employee UNIQUE (tenant_id, employee_id)`; foreign keys `fk_employees_department`, `fk_employees_role`, `fk_employees_manager` all reference `(tenant_id, <id>)` composite keys (001, lines 60-75).
- `user_accounts`: `CONSTRAINT uq_user_accounts_tenant_user UNIQUE (tenant_id, user_id)`; `fk_user_accounts_employee` references `employees (tenant_id, employee_id)` (004, lines 19-26).
- `role_bindings`, `permission_policies`, `sessions`, `refresh_tokens`: all carry `tenant_id NOT NULL` with `(tenant_id, <id>)` unique constraints and `(tenant_id, ...)` composite foreign keys (004, lines 31-127).
- `tenants` table (`005_tenant_foundation.sql`, line 1) is the tenant registry: `tenant_id VARCHAR(80) NOT NULL PRIMARY KEY`. `tenant_configs` references it via `fk_tenant_configs_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)` (005, line 27).

Default tenant: `DEFAULT_TENANT_ID = 'tenant-default'`, defined in both `backend/middleware/tenant-context.ts` (line 3) and `backend/tenant_support.py` (referenced by `auth-service/service.py` line 17 as `from tenant_support import DEFAULT_TENANT_ID, normalize_tenant_id`).

---

## 4. SCOPE CLAIM AND PRINCIPAL CONTEXT

In addition to `tenant_id` and `role`, the JWT carries a `scopes` claim used for fine-grained authorization (see `USER_ROLES_AND_PERMISSIONS.md` for the full scope model). `AuthService._service_scopes_for_user` (`service.py` lines 874-883) derives default scopes by role:

| Role | Default scope value |
|---|---|
| Service | `('service:internal', 'resource:employee-service')` |
| Admin | `('scope:global',)` |
| Manager (with `department_id`) | `(f'department:{department_id}',)` |
| User with `employee_id` (typically Employee) | `(f'employee:{employee_id}',)` |
| Fallback | `('scope:global',)` |

`AuthService.require_scope(principal, scope)` (`service.py` lines 512-516): Admin always passes; otherwise the requested `scope` string must be a member of `principal.scopes`, else raises `FORBIDDEN`.

---

## 5. RATE LIMITING

Implemented at the gateway only, via `backend/rate_limiting.py` `SlidingWindowRateLimiter`:

- Default: **200 requests per 60-second sliding window, keyed by client IP** (`api_gateway_service.py` lines 45-47):
  ```python
  _RATE_LIMIT = int(os.getenv("GATEWAY_RATE_LIMIT", "200"))
  _RATE_WINDOW = float(os.getenv("GATEWAY_RATE_WINDOW_SECONDS", "60"))
  RATE_LIMITER = SlidingWindowRateLimiter(requests_per_window=_RATE_LIMIT, window_seconds=_RATE_WINDOW)
  ```
- Client IP resolution (line 362-366): `X-Forwarded-For` (first value) → `X-Real-Ip` → `"unknown"`.
- Applied to **every** request, including exempt/auth routes, before JWT enforcement (rate limiting check occurs at lines 367-380, before the JWT block at line 421).
- On exceed: `429 RATE_LIMIT_EXCEEDED` with `Retry-After` header and `X-RateLimit-*` headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`).
- The limiter is in-process (`_buckets: dict[str, deque[float]]`, `rate_limiting.py` line 22) — **TBD – REQUIRES VERIFICATION**: whether this is shared across multiple gateway instances/replicas (in-process state suggests per-instance limiting unless the gateway runs as a single replica).

---

## 6. PASSWORD HASHING

`AuthService._hash_password` / `_verify_password` (`service.py` lines 838-854):

- Algorithm: **PBKDF2-HMAC-SHA256**, 390,000 iterations, 16-byte random salt (`os.urandom(16)`).
- Stored format: `"{salt_hex}:{key_hex}"`.
- Verification uses `hmac.compare_digest` (constant-time comparison).
- Password length limit enforced at registration: max 1024 chars (`register_user`, line 270).
- Refresh tokens are stored as SHA-256 hashes (`_hash_refresh_token`, lines 860-862) — not the raw token — matching `security-model.md` line 83 ("Store only hashed refresh tokens and password hashes").

---

## 7. SESSION AND REFRESH TOKEN LIFECYCLE SUMMARY

| Entity | Table | Key fields | Source |
|---|---|---|---|
| `UserAccount` | `user_accounts` | `tenant_id`, `user_id` (PK), `employee_id`, `username`, `password_hash`, `status` (`Invited`/`Active`/`Locked`/`Disabled`) | `004_persistence_normalization.sql` lines 7-29 |
| `Session` | `sessions` | `tenant_id`, `session_id` (PK), `user_id`, `access_token_jti`, `client_type`, `started_at`, `expires_at`, `last_rotated_at`, `revoked_at` | `004_persistence_normalization.sql` lines 71-94 |
| `RefreshToken` | `refresh_tokens` | `tenant_id`, `refresh_token_id` (PK), `session_id`, `user_id`, `token_hash`, `rotated_from_token_id`, `expires_at`, `revoked_at` | `004_persistence_normalization.sql` lines 96-127 |
| `RoleBinding` | `role_bindings` | `tenant_id`, `role_binding_id` (PK), `user_id`, `role_code`, `scope_type`, `scope_id`, `status` (`Active`/`Revoked`) | `004_persistence_normalization.sql` lines 31-50 |
| `PermissionPolicy` | `permission_policies` | `tenant_id`, `permission_policy_id` (PK), `policy_code`, `subject_type`, `subject_id`, `capability_code`, `scope_type`, `scope_id`, `effect` (`Allow`/`Deny`) | `004_persistence_normalization.sql` lines 52-69 |

Lifecycle:
- A session is created on login (`_issue_session_tokens`).
- Each refresh **rotates** the refresh token and access-token `jti`, extending `refresh_expires_at`.
- A session is revoked (`revoked=True`, `revoked_at` set, `revocation_reason` recorded) on: explicit logout, refresh-token expiry detected during refresh/authenticate, account disabled, or admin-initiated `revoke_session`.
- Once revoked, `authenticate_token` and `refresh_session` both reject with `TOKEN_REVOKED`/`TOKEN_EXPIRED`.

Note: `backend/services/auth-service/service.py` operates on an in-memory/persistent KV store abstraction (`PersistentKVStore`, `service.py` lines 187-193) rather than directly issuing SQL against the `004_persistence_normalization.sql` tables in this code path — **TBD – REQUIRES VERIFICATION**: whether the auth-service's runtime persistence layer (`persistent_store.PersistentKVStore`) is backed by the Postgres schema in `004_persistence_normalization.sql` or is a separate store with an equivalent logical schema. The table definitions remain the canonical schema reference per the migration files regardless.

---

## 8. CROSS-REFERENCES

- `docs/00_authority/DOMAIN_MODEL.md` — MULTI-TENANCY INVARIANT (lines 21-28), ROLE BINDING entity.
- `docs/07_governance/AI_OPERATING_CONTEXT.md` — KNOWN_CONSTRAINTS (lines 91-107).
- `backend/docs/canon/security-model.md` — canonical security principals, scope model, authentication controls.
- `backend/docs/canon/capability-matrix.md` — `CAP-AUT-001` capability and `/api/v1/auth/*` route category.
- `docs/03_fullstack_contracts/USER_ROLES_AND_PERMISSIONS.md` — role/capability/scope authorization model.
- `docs/08_reports/SECURITY_DISCOVERY_REPORT.md` — security discovery findings and known gaps.
