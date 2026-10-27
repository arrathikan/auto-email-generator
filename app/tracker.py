"""
Tracker and Authentication Module for CareerLens.
Exposes database operations, Argon2id auth, and authenticated SMTP credential encryption.
"""
import os
from core.config import DATA_DIR, DEFAULT_DB_PATH
from core.security import (
    ENCRYPTION_PREFIX,
    get_encryption_cipher as _core_get_cipher,
    encrypt_smtp_password as _core_encrypt_smtp,
    decrypt_smtp_password as _core_decrypt_smtp,
)
from core.auth import (
    hash_password,
    verify_password,
    check_needs_rehash,
)
from core.database import (
    get_connection,
    init_db as _core_init_db,
    register_user,
    authenticate_user,
    get_user_profile,
    save_user_profile,
    get_user_mail_config,
    save_user_mail_config,
)

# Preserve monkeypatchable attributes for backward compatibility and tests
DB_DIR = DATA_DIR
DB_PATH = DEFAULT_DB_PATH

def init_db():
    return _core_init_db(DB_PATH)

def _get_encryption_cipher():
    return _core_get_cipher(key_dir=DB_DIR)

def encrypt_smtp_password(plaintext: str) -> str:
    return _core_encrypt_smtp(plaintext, key_dir=DB_DIR)

def decrypt_smtp_password(stored_val: str) -> str:
    return _core_decrypt_smtp(stored_val, key_dir=DB_DIR)

# Initialize database on import
init_db()

__all__ = [
    "DB_DIR",
    "DB_PATH",
    "ENCRYPTION_PREFIX",
    "get_connection",
    "init_db",
    "_get_encryption_cipher",
    "encrypt_smtp_password",
    "decrypt_smtp_password",
    "hash_password",
    "verify_password",
    "check_needs_rehash",
    "register_user",
    "authenticate_user",
    "get_user_profile",
    "save_user_profile",
    "get_user_mail_config",
    "save_user_mail_config",
]
