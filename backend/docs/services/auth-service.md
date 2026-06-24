# Auth Service

Identity, session management, role bindings, and policy enforcement for all human and service principals.

## Scope
- Authenticates principals and issues short-lived access tokens + rotatable refresh tokens.
- Maintains user accounts, sessions, refresh tokens, and role bindings.
- Evaluates capability/role policy for human and service principals.
- Enforces deny-by-default; access requires both a granted capability and a matching scope.
- Provisions service-principal credentials for service-to-service calls.

## HTTP surface (`/api/v1`)
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/users`
- `PATCH /api/v1/auth/users/{user_id}`
- `POST /api/v1/auth/users/{user_id}/lock`
- `POST /api/v1/auth/users/{user_id}/unlock`
- `GET /api/v1/auth/sessions?user_id=&status=&limit=&cursor=`
- `POST /api/v1/auth/sessions/{session_id}/revoke`
- `POST /api/v1/auth/roles/bindings`
- `DELETE /api/v1/auth/roles/bindings/{binding_id}`
- `POST /api/v1/auth/policies`
- `PATCH /api/v1/auth/policies/{policy_id}`
- `GET /api/v1/auth/policies?capability_id=&role_name=&effect=&limit=&cursor=`
- `GET /api/v1/auth/access?user_id=`

## Security principals
- **Admin**: unrestricted tenant-wide HR operations and access administration.
- **Manager**: scoped to assigned department and reporting hierarchy.
- **Employee**: self-service scope plus limited organizational visibility.
- **Recruiter**: scoped hiring operations for assigned requisitions.
- **PayrollAdmin**: payroll administration and disbursement authority.
- **Service**: non-human service principal for service-to-service calls.

## Authorization capabilities
- `CAP-AUT-001`: identity and access administration (Admin only)

## Owned entities
- `UserAccount`
- `RoleBinding`
- `PermissionPolicy`
- `Session`
- `RefreshToken`

## Supported workflows
- `access_provisioning`

## Events published
- `UserAuthenticated`
- `SessionRevoked`
- `UserProvisioned`
- `UserAccountStatusChanged`
- `RoleBindingChanged`
- `RefreshTokenRotated`
- `AuthorizationPolicyUpdated`

## Events subscribed
- `EmployeeCreated` — trigger user account provisioning
- `EmployeeStatusChanged` — lock/revoke accounts for terminated employees

## Read models produced
- `access_control_view` — user accounts, active sessions, role bindings

## Security controls
- Short-lived access tokens; rotatable refresh tokens (stored hashed only).
- MFA required for Admin and PayrollAdmin principals.
- Sessions revoked on credential compromise, employee termination, or admin lock.
- Sensitive attributes (password hashes, refresh tokens) never exposed in API responses.

## Dependencies
- `employee-service` — workforce identity linkage
- `notification-service` — password reset and security alert notifications

## Notes
- See `docs/canon/security-model.md` for full capability-to-role authorization matrix and scope enforcement rules.
