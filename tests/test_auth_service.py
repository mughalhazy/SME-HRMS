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

    def test_refresh_rotates_token_and_preserves_session(self) -> None:
        login_payload = self.service.login('ava.manager', 'Password123!')
        refreshed = self.service.refresh_session(login_payload['refresh_token'])

        self.assertNotEqual(login_payload['refresh_token'], refreshed['refresh_token'])
        self.assertEqual(login_payload['session_id'], refreshed['session_id'])
        principal = self.service.authenticate_token(refreshed['access_token'])
        self.assertEqual(principal.role, 'Manager')

        with self.assertRaises(AuthServiceError) as ctx:
            self.service.refresh_session(login_payload['refresh_token'])
        self.assertEqual(ctx.exception.code, 'TOKEN_INVALID')

    def test_role_validation_enforces_capability_matrix(self) -> None:
        token = self.service.login('ava.manager', 'Password123!')['access_token']
        principal = self.service.authenticate_token(token)

        self.assertTrue(self.service.validate_role(principal, 'CAP-LEV-002'))
        self.assertFalse(self.service.validate_role(principal, 'CAP-PAY-002'))

        with self.assertRaises(AuthServiceError):
            self.service.require_capability(principal, 'CAP-PAY-002')

    def test_logout_revokes_session(self) -> None:
        token = self.service.login('ava.manager', 'Password123!')['access_token']
        self.service.logout(token)
        with self.assertRaises(AuthServiceError):
            self.service.authenticate_token(token)

    def test_api_login_refresh_logout_and_me_follow_canonical_envelope(self) -> None:
        login_status, login_payload = post_auth_login(
            self.service,
            {'username': 'ava.manager', 'password': 'Password123!'},
            trace_id='trace-login',
        )
        self.assertEqual(login_status, 200)
        token = login_payload['data']['access_token']
        refresh_token = login_payload['data']['refresh_token']

        me_status, me_payload = get_auth_me(self.service, f'Bearer {token}', trace_id='trace-me')
        self.assertEqual(me_status, 200)
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
        self.assertEqual(revoked_payload['error']['code'], 'TOKEN_REVOKED')

        bad_status, bad_payload = post_auth_login(
            self.service,
            {'username': 'ava.manager', 'password': 'wrong'},
            trace_id='trace-bad',
        )
        self.assertEqual(bad_status, 401)
        self.assertEqual(bad_payload['error']['traceId'], 'trace-bad')

    def test_malformed_password_hash_is_treated_as_invalid_credentials(self) -> None:
        user = self.service.register_user(username='broken.hash', password='Password123!', role='Employee')
        user.password_hash = 'not-a-valid-password-hash'

        with self.assertRaises(AuthServiceError) as ctx:
            self.service.login('broken.hash', 'Password123!')

        self.assertEqual(ctx.exception.code, 'INVALID_CREDENTIALS')

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
