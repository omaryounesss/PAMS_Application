import unittest

from app.config import AppConfig
from app.rbac import AuthorizationError, CurrentUser
from app.validators import ValidationError

try:
    from app.services import PamsService
except ModuleNotFoundError:  # pragma: no cover - local env may miss mysql connector
    PamsService = None  # type: ignore[assignment]


@unittest.skipIf(PamsService is None, "mysql-connector-python is not installed")
class TenantPortalRuleTests(unittest.TestCase):
    def setUp(self):
        self.service = PamsService(db=None, cfg=AppConfig())  # type: ignore[arg-type]

    def test_luhn_validation(self):
        self.assertTrue(self.service._luhn_valid("4242424242424242"))
        self.assertFalse(self.service._luhn_valid("4242424242424241"))

    def test_card_validation_rejects_expired(self):
        with self.assertRaises(ValidationError):
            self.service._validate_card_details("4242 4242 4242 4242", "01/20", "123")

    def test_tenant_city_scope_violation(self):
        tenant = CurrentUser(
            id=1,
            username="tenant_test",
            full_name="Tenant Test",
            role="TENANT",
            city_id=2,
            tenant_id=1,
        )
        with self.assertRaises(AuthorizationError):
            self.service._resolve_city_scope(tenant, 1)


if __name__ == "__main__":
    unittest.main()
