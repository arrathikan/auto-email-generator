"""
User authentication and password hashing using Argon2id with legacy SHA-256 fallback.
"""
import secrets
import hashlib
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
try:
    from argon2.exceptions import InvalidHashError
except ImportError:
    from argon2.exceptions import InvalidHash as InvalidHashError

# Initialize Argon2id password hasher (RFC 9106 recommended parameters)
_password_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MB
    parallelism=1,
    hash_len=32,
    salt_len=16
)

def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """
    Hashes a password using Argon2id.
    Returns (argon2_hash, "").
    The salt parameter is preserved for backwards compatibility with legacy call signatures.
    """
    pwd_hash = _password_hasher.hash(password)
    return pwd_hash, ""

def verify_password(password: str, stored_hash: str, salt: str = "") -> bool:
    """
    Verifies a password against either a modern Argon2id hash or a legacy salted SHA-256 hash.
    Constant-time comparison is enforced for legacy verification.
    """
    if not stored_hash or not password:
        return False

    # 1. Modern Argon2id hash
    if stored_hash.startswith("$argon2"):
        try:
            return _password_hasher.verify(stored_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    # 2. Legacy salted SHA-256 fallback
    try:
        legacy_salted = password + (salt or "")
        legacy_hash = hashlib.sha256(legacy_salted.encode("utf-8")).hexdigest()
        return secrets.compare_digest(legacy_hash, stored_hash)
    except Exception:
        return False

def check_needs_rehash(stored_hash: str) -> bool:
    """
    Returns True if the hash is a legacy SHA-256 hash or an outdated Argon2 parameter format.
    """
    if not stored_hash or not stored_hash.startswith("$argon2"):
        return True
    try:
        return _password_hasher.check_needs_rehash(stored_hash)
    except Exception:
        return True
