from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from uuid import uuid4

AUTH_SERVICE_DIR = Path(__file__).resolve().parents[1] / 'services' / 'auth-service'
if str(AUTH_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AUTH_SERVICE_DIR))

service_spec = importlib.util.spec_from_file_location('service', AUTH_SERVICE_DIR / 'service.py')
service_module = importlib.util.module_from_spec(service_spec)
assert service_spec and service_spec.loader
sys.modules[service_spec.name] = service_module
service_spec.loader.exec_module(service_module)

api_spec = importlib.util.spec_from_file_location('api', AUTH_SERVICE_DIR / 'api.py')
api_module = importlib.util.module_from_spec(api_spec)
assert api_spec and api_spec.loader
sys.modules[api_spec.name] = api_module
api_spec.loader.exec_module(api_module)

AuthService = service_module.AuthService
AuthServiceError = service_module.AuthServiceError
post_auth_login = api_module.post_auth_login
post_auth_refresh = api_module.post_auth_refresh
post_auth_logout = api_module.post_auth_logout
get_auth_me = api_module.get_auth_me
get_auth_session = api_module.get_auth_session
get_auth_sessions = api_module.get_auth_sessions
post_auth_session_revoke = api_module.post_auth_session_revoke


class AuthServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = AuthService(token_secret='test-secret-for-hardening-1234567890')
        self.employee_id = uuid4()
        self.department_id = uuid4()
        self.service.register_user(
            username='ava.manager',
            password='Password123!',
            role='Manager',
            employee_id=self.employee_id,
            department_id=self.department_id,
        )

    def test_login_issues_bearer_and_refresh_tokens(self) -> None:
        self.assertEqual(self.service.events[0]['event_type'], 'auth.user.provisioned')
        token_payload = self.service.login('ava.manager', 'Password123!')
        self.assertEqual(token_payload['token_type'], 'Bearer')
        self.assertTrue(token_payload['access_token'])
        self.assertTrue(token_payload['refresh_token'])
        self.assertTrue(token_payload['session_id'])

    def test_token_auth_returns_authenticated_principal(self) -> None:
        token = self.service.login('ava.manager', 'Password123!')['access_token']
        principal = self.service.authenticate_token(token)
        self.assertEqual(principal.role, 'Manager')
        self.assertEqual(principal.employee_id, self.employee_id)


    def test_same_username_can_exist_in_different_tenants_and_tokens_preserve_tenant_context(self) -> None:
        other_employee = uuid4()
        self.service.register_user(
            username='ava.manager',
            password='Password123!',
            role='Manager',
            employee_id=other_employee,
            department_id=self.department_id,
            tenant_id='tenant-beta',
        )

        default_login = self.service.login('ava.manager', 'Password123!', tenant_id='tenant-default')
        beta_login = self.service.login('ava.manager', 'Password123!', tenant_id='tenant-beta')

        default_principal = self.service.authenticate_token(default_login['access_token'])
        beta_principal = self.service.authenticate_token(beta_login['access_token'])

        self.assertEqual(default_principal.tenant_id, 'tenant-default')
        self.assertEqual(beta_principal.tenant_id, 'tenant-beta')
        self.assertNotEqual(default_principal.employee_id, beta_principal.employee_id)

    def test_login_api_accepts_tenant_id_and_me_returns_it(self) -> None:
        self.service.register_user(
            username='tenant.user',
            password='Password123!',
            role='Employee',
            tenant_id='tenant-gamma',
        )

        login_status, login_payload = post_auth_login(
            self.service,
            {'username': 'tenant.user', 'password': 'Password123!', 'tenant_id': 'tenant-gamma'},
            trace_id='trace-login-tenant',
        )
        self.assertEqual(login_status, 200)
        me_status, me_payload = get_auth_me(self.service, f"Bearer {login_payload['data']['access_token']}", trace_id='trace-me-tenant')
        self.assertEqual(me_status, 200)
        self.assertEqual(me_payload['data']['tenant_id'], 'tenant-gamma')

    def test_refresh_rotates_token_and_preserves_session(self) -> None:
        login_payload = self.service.login('ava.manager', 'Password123!')
        original_access_token = login_payload['access_token']
        refreshed = self.service.refresh_session(login_payload['refresh_token'])

        self.assertNotEqual(login_payload['refresh_token'], refreshed['refresh_token'])
        self.assertEqual(login_payload['session_id'], refreshed['session_id'])
        principal = self.service.authenticate_token(refreshed['access_token'])
        self.assertEqual(principal.role, 'Manager')

        with self.assertRaises(AuthServiceError) as revoked_access_ctx:
            self.service.authenticate_token(original_access_token)
        self.assertEqual(revoked_access_ctx.exception.code, 'TOKEN_REVOKED')

        with self.assertRaises(AuthServiceError) as ctx:
            self.service.refresh_session(login_payload['refresh_token'])
        self.assertEqual(ctx.exception.code, 'TOKEN_INVALID')

    def test_login_tracks_session_metadata_and_preserves_it_in_session_views(self) -> None:
        login_payload = self.service.login(
            'ava.manager',
            'Password123!',
            client_type='Web',
            device_id='device-001',
            ip_address='203.0.113.10',
            user_agent='pytest-agent',
        )
        session = self.service.get_current_session(login_payload['access_token'])

        self.assertEqual(session['client_type'], 'Web')
        self.assertEqual(session['device_id'], 'device-001')
        self.assertEqual(session['ip_address'], '203.0.113.10')
        self.assertEqual(session['user_agent'], 'pytest-agent')

    def test_role_validation_enforces_capability_matrix(self) -> None:
        token = self.service.login('ava.manager', 'Password123!')['access_token']
        principal = self.service.authenticate_token(token)

        self.assertTrue(self.service.validate_role(principal, 'CAP-LEV-002'))
        self.assertFalse(self.service.validate_role(principal, 'CAP-PAY-002'))

        with self.assertRaises(AuthServiceError):
            self.service.require_capability(principal, 'CAP-PAY-002')

    def test_tenant_and_scope_checks_deny_cross_tenant_access(self) -> None:
        token = self.service.login('ava.manager', 'Password123!')['access_token']
        principal = self.service.authenticate_token(token)

        self.service.require_tenant_access(principal, 'tenant-default')
        self.service.require_scope(principal, f'department:{self.department_id}')

        with self.assertRaises(AuthServiceError) as tenant_ctx:
            self.service.require_tenant_access(principal, 'tenant-beta')
        self.assertEqual(tenant_ctx.exception.code, 'FORBIDDEN')

        with self.assertRaises(AuthServiceError) as scope_ctx:
            self.service.require_scope(principal, 'resource:payroll-service')
        self.assertEqual(scope_ctx.exception.code, 'FORBIDDEN')

    def test_logout_revokes_session(self) -> None:
        token = self.service.login('ava.manager', 'Password123!')['access_token']
        self.service.logout(token)
        with self.assertRaises(AuthServiceError):
            self.service.authenticate_token(token)
        self.assertEqual(self.service.events[-1]['event_type'], 'auth.session.revoked')

    def test_role_binding_and_permission_policy_changes_are_audited(self) -> None:
        user = self.service.register_user(username='policy.admin', password='Password123!', role='Admin')
        binding = self.service.assign_role_binding(user.user_id, role_name='Manager', scope_type='Department', scope_id='dept-123', actor_id='security-admin')
        policy = self.service.upsert_permission_policy(
            capability_id='CAP-EMP-002',
            role_name='Manager',
            resource_type='Employee',
            scope_rule='department-match',
            effect='Deny',
            version=1,
            actor_id='security-admin',
        )

        self.assertEqual(binding['scope_type'], 'Department')
        self.assertEqual(policy['effect'], 'Deny')
        event_types = {event['event_type'] for event in self.service.events}
        self.assertIn('auth.role_binding.changed', event_types)
        self.assertIn('auth.authorization_policy.updated', event_types)

    def test_explicit_permission_policy_can_deny_capability(self) -> None:
        self.service.upsert_permission_policy(
            capability_id='CAP-LEV-002',
            role_name='Manager',
            resource_type='LeaveRequest',
            scope_rule='department-match',
            effect='Deny',
            version=1,
            actor_id='security-admin',
        )

        token = self.service.login('ava.manager', 'Password123!')['access_token']
        principal = self.service.authenticate_token(token)
        self.assertFalse(self.service.validate_role(principal, 'CAP-LEV-002'))
        with self.assertRaises(AuthServiceError):
            self.service.require_capability(principal, 'CAP-LEV-002')

    def test_api_login_refresh_logout_and_me_follow_scs_envelope(self) -> None:
        login_status, login_payload = post_auth_login(
            self.service,
            {'username': 'ava.manager', 'password': 'Password123!'},
            trace_id='trace-login',
        )
        self.assertEqual(login_status, 200)
        self.assertEqual(login_payload['status'], 'success')
        self.assertEqual(login_payload['meta']['request_id'], 'trace-login')
        token = login_payload['data']['access_token']
        refresh_token = login_payload['data']['refresh_token']

        me_status, me_payload = get_auth_me(self.service, f'Bearer {token}', trace_id='trace-me')
        self.assertEqual(me_status, 200)
        self.assertEqual(me_payload['status'], 'success')
        self.assertEqual(me_payload['data']['role'], 'Manager')

        refresh_status, refresh_payload = post_auth_refresh(
            self.service,
            {'refresh_token': refresh_token},
            trace_id='trace-refresh',
        )
        self.assertEqual(refresh_status, 200)
        self.assertNotEqual(refresh_payload['data']['refresh_token'], refresh_token)

        logout_status, logout_payload = post_auth_logout(
            self.service,
            {'refresh_token': refresh_payload['data']['refresh_token']},
            trace_id='trace-logout',
        )
        self.assertEqual(logout_status, 200)
        self.assertTrue(logout_payload['data']['logged_out'])

        revoked_status, revoked_payload = get_auth_me(self.service, f"Bearer {refresh_payload['data']['access_token']}", trace_id='trace-revoked')
        self.assertEqual(revoked_status, 401)
        self.assertEqual(revoked_payload['status'], 'error')
        self.assertEqual(revoked_payload['error']['code'], 'TOKEN_REVOKED')

        bad_status, bad_payload = post_auth_login(
            self.service,
            {'username': 'ava.manager', 'password': 'wrong'},
            trace_id='trace-bad',
        )
        self.assertEqual(bad_status, 401)
        self.assertEqual(bad_payload['meta']['request_id'], 'trace-bad')

    def test_malformed_password_hash_is_treated_as_invalid_credentials(self) -> None:
        user = self.service.register_user(username='broken.hash', password='Password123!', role='Employee')
        user.password_hash = 'not-a-valid-password-hash'

        with self.assertRaises(AuthServiceError) as ctx:
            self.service.login('broken.hash', 'Password123!')

        self.assertEqual(ctx.exception.code, 'INVALID_CREDENTIALS')

    def test_current_session_listing_and_revocation_api_support(self) -> None:
        login_payload = self.service.login('ava.manager', 'Password123!')
        token = login_payload['access_token']

        session_status, session_payload = get_auth_session(self.service, f'Bearer {token}', trace_id='trace-session')
        self.assertEqual(session_status, 200)
        self.assertEqual(session_payload['data']['status'], 'Active')
        self.assertEqual(session_payload['data']['session_id'], login_payload['session_id'])

        sessions_status, sessions_payload = get_auth_sessions(
            self.service,
            {'user_id': str(self.service.authenticate_token(token).user_id), 'status': 'Active'},
            trace_id='trace-sessions',
        )
        self.assertEqual(sessions_status, 200)
        self.assertEqual(len(sessions_payload['data']), 1)
        self.assertEqual(sessions_payload['meta']['pagination'], {})

        revoke_status, revoke_payload = post_auth_session_revoke(
            self.service,
            login_payload['session_id'],
            {'actor': 'security-test'},
            trace_id='trace-revoke-session',
        )
        self.assertEqual(revoke_status, 200)
        self.assertEqual(revoke_payload['data']['status'], 'Revoked')

        revoked_status, revoked_payload = get_auth_session(self.service, f'Bearer {token}', trace_id='trace-session-revoked')
        self.assertEqual(revoked_status, 401)
        self.assertEqual(revoked_payload['error']['code'], 'TOKEN_REVOKED')

    def test_auth_observability_tracks_api_calls(self) -> None:
        post_auth_login(
            self.service,
            {'username': 'ava.manager', 'password': 'Password123!'},
            trace_id='trace-auth-login',
        )
        metrics = self.service.observability.metrics.snapshot()
        self.assertEqual(metrics['request_count'], 1)
        self.assertEqual(metrics['recent_requests'][0]['trace_id'], 'trace-auth-login')
        self.assertEqual(self.service.health_snapshot()['status'], 'ok')


if __name__ == '__main__':
    unittest.main()
