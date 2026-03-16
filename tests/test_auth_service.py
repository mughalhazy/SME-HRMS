from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from uuid import uuid4

AUTH_SERVICE_DIR = Path(__file__).resolve().parents[1] / "services" / "auth-service"
if str(AUTH_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AUTH_SERVICE_DIR))

service_spec = importlib.util.spec_from_file_location("service", AUTH_SERVICE_DIR / "service.py")
service_module = importlib.util.module_from_spec(service_spec)
assert service_spec and service_spec.loader
sys.modules[service_spec.name] = service_module
service_spec.loader.exec_module(service_module)

api_spec = importlib.util.spec_from_file_location("api", AUTH_SERVICE_DIR / "api.py")
api_module = importlib.util.module_from_spec(api_spec)
assert api_spec and api_spec.loader
sys.modules[api_spec.name] = api_module
api_spec.loader.exec_module(api_module)

AuthService = service_module.AuthService
AuthServiceError = service_module.AuthServiceError
post_auth_login = api_module.post_auth_login
get_auth_me = api_module.get_auth_me


class AuthServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = AuthService(token_secret="test-secret-for-hardening-1234567890")
        self.employee_id = uuid4()
        self.department_id = uuid4()
        self.service.register_user(
            username="ava.manager",
            password="Password123!",
            role="Manager",
            employee_id=self.employee_id,
            department_id=self.department_id,
        )

    def test_login_issues_bearer_token(self) -> None:
        token_payload = self.service.login("ava.manager", "Password123!")
        self.assertEqual(token_payload["token_type"], "Bearer")
        self.assertTrue(token_payload["access_token"])

    def test_token_auth_returns_authenticated_principal(self) -> None:
        token = self.service.login("ava.manager", "Password123!")["access_token"]
        principal = self.service.authenticate_token(token)
        self.assertEqual(principal.role, "Manager")
        self.assertEqual(principal.employee_id, self.employee_id)

    def test_role_validation_enforces_capability_matrix(self) -> None:
        token = self.service.login("ava.manager", "Password123!")["access_token"]
        principal = self.service.authenticate_token(token)

        self.assertTrue(self.service.validate_role(principal, "CAP-LEV-002"))
        self.assertFalse(self.service.validate_role(principal, "CAP-PAY-002"))

        with self.assertRaises(AuthServiceError):
            self.service.require_capability(principal, "CAP-PAY-002")

    def test_logout_revokes_session(self) -> None:
        token = self.service.login("ava.manager", "Password123!")["access_token"]
        self.service.logout(token)
        with self.assertRaises(AuthServiceError):
            self.service.authenticate_token(token)

    def test_api_login_and_me_follow_canonical_envelope(self) -> None:
        login_status, login_payload = post_auth_login(
            self.service,
            {"username": "ava.manager", "password": "Password123!"},
            trace_id="trace-login",
        )
        self.assertEqual(login_status, 200)
        token = login_payload["data"]["access_token"]

        me_status, me_payload = get_auth_me(self.service, f"Bearer {token}", trace_id="trace-me")
        self.assertEqual(me_status, 200)
        self.assertEqual(me_payload["data"]["role"], "Manager")

        bad_status, bad_payload = post_auth_login(
            self.service,
            {"username": "ava.manager", "password": "wrong"},
            trace_id="trace-bad",
        )
        self.assertEqual(bad_status, 401)
        self.assertEqual(bad_payload["error"]["traceId"], "trace-bad")

    def test_malformed_password_hash_is_treated_as_invalid_credentials(self) -> None:
        user = self.service.register_user(username="broken.hash", password="Password123!", role="Employee")
        user.password_hash = "not-a-valid-password-hash"

        with self.assertRaises(AuthServiceError) as ctx:
            self.service.login("broken.hash", "Password123!")

        self.assertEqual(ctx.exception.code, "INVALID_CREDENTIALS")


if __name__ == "__main__":
    unittest.main()
