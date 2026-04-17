import unittest

from service.utils.password_utils import (
    hash_password,
    is_bcrypt_hash,
    is_legacy_md5_hash,
    md5_hex,
    verify_and_upgrade_password,
    verify_password,
)


class PasswordUtilsTests(unittest.TestCase):
    def test_hash_password_uses_bcrypt(self):
        password_hash = hash_password("secret-123")

        self.assertTrue(is_bcrypt_hash(password_hash))
        self.assertTrue(verify_password("secret-123", password_hash))
        self.assertFalse(verify_password("wrong-password", password_hash))

    def test_verify_and_upgrade_password_upgrades_legacy_md5_hash(self):
        legacy_hash = md5_hex("secret-123")

        verified, upgraded_hash = verify_and_upgrade_password("secret-123", legacy_hash)

        self.assertTrue(verified)
        self.assertIsNotNone(upgraded_hash)
        self.assertTrue(is_legacy_md5_hash(legacy_hash))
        self.assertTrue(is_bcrypt_hash(upgraded_hash))
        self.assertTrue(verify_password("secret-123", upgraded_hash))

    def test_verify_and_upgrade_password_keeps_current_bcrypt_hash(self):
        current_hash = hash_password("secret-123")

        verified, upgraded_hash = verify_and_upgrade_password("secret-123", current_hash)

        self.assertTrue(verified)
        self.assertIsNone(upgraded_hash)

    def test_verify_and_upgrade_password_rejects_invalid_password(self):
        legacy_hash = md5_hex("secret-123")

        verified, upgraded_hash = verify_and_upgrade_password("wrong-password", legacy_hash)

        self.assertFalse(verified)
        self.assertIsNone(upgraded_hash)


if __name__ == "__main__":
    unittest.main()
