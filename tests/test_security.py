import unittest

from app.security import hash_password, verify_password


class SecurityTests(unittest.TestCase):
    def test_hash_and_verify_roundtrip(self):
        p = hash_password("StrongPass!9")
        self.assertTrue(verify_password("StrongPass!9", p.hash_b64, p.salt_b64))
        self.assertFalse(verify_password("WrongPass!9", p.hash_b64, p.salt_b64))

    def test_short_password_rejected(self):
        with self.assertRaises(ValueError):
            hash_password("short")


if __name__ == "__main__":
    unittest.main()
