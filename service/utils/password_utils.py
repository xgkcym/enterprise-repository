import hashlib
import hmac
import re

import bcrypt

_BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")
_MD5_HEX_RE = re.compile(r"^[a-fA-F0-9]{32}$")


def md5_hex(password: str) -> str:
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def is_bcrypt_hash(password_hash: str | None) -> bool:
    if not password_hash:
        return False
    return password_hash.startswith(_BCRYPT_PREFIXES)


def is_legacy_md5_hash(password_hash: str | None) -> bool:
    if not password_hash:
        return False
    return bool(_MD5_HEX_RE.fullmatch(password_hash))


def verify_password(plain_password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False

    if is_bcrypt_hash(password_hash):
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )

    if is_legacy_md5_hash(password_hash):
        return hmac.compare_digest(md5_hex(plain_password), password_hash.lower())

    return False


def needs_password_rehash(password_hash: str | None) -> bool:
    if not password_hash:
        return True
    return is_legacy_md5_hash(password_hash)


def verify_and_upgrade_password(plain_password: str, password_hash: str | None) -> tuple[bool, str | None]:
    if not verify_password(plain_password, password_hash):
        return False, None

    if needs_password_rehash(password_hash):
        return True, hash_password(plain_password)

    return True, None
