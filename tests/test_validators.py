import unittest
from datetime import date

from app.validators import (
    ValidationError,
    validate_date_order,
    validate_email,
    validate_ni,
    validate_phone,
    validate_positive_money,
)


class ValidatorTests(unittest.TestCase):
    def test_validate_ni(self):
        self.assertEqual(validate_ni("ab123456c"), "AB123456C")
        with self.assertRaises(ValidationError):
            validate_ni("123")

    def test_validate_email(self):
        self.assertEqual(validate_email("A@B.COM"), "a@b.com")
        with self.assertRaises(ValidationError):
            validate_email("invalid")

    def test_validate_phone(self):
        self.assertEqual(validate_phone("+44 7900 123456"), "+44 7900 123456")
        with self.assertRaises(ValidationError):
            validate_phone("abc")

    def test_positive_money(self):
        self.assertEqual(validate_positive_money("12.345", "Money"), 12.35)
        with self.assertRaises(ValidationError):
            validate_positive_money("-1", "Money")

    def test_date_order(self):
        validate_date_order(date(2026, 1, 1), date(2026, 1, 2))
        with self.assertRaises(ValidationError):
            validate_date_order(date(2026, 1, 1), date(2026, 1, 1))


if __name__ == "__main__":
    unittest.main()
