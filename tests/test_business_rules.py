import unittest
from datetime import date

from app.business_rules import (
    calculate_early_leave_penalty,
    is_invoice_late,
    requires_notice_period,
)


class BusinessRuleTests(unittest.TestCase):
    def test_penalty(self):
        self.assertEqual(calculate_early_leave_penalty(1250), 62.5)

    def test_notice_rule(self):
        self.assertTrue(requires_notice_period(date(2026, 2, 1), date(2026, 3, 5), 30))
        self.assertFalse(requires_notice_period(date(2026, 2, 1), date(2026, 2, 20), 30))

    def test_invoice_late(self):
        due = date(2026, 2, 5)
        self.assertTrue(is_invoice_late(due, None, date(2026, 2, 6)))
        self.assertFalse(is_invoice_late(due, date(2026, 2, 5), date(2026, 2, 6)))


if __name__ == "__main__":
    unittest.main()
