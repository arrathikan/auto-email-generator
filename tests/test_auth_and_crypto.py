import pytest
import sqlite3
import hashlib
import tracker
from tracker import (
    register_user,
    authenticate_user,
    verify_password,
    hash_password,
    save_user_mail_config,
    get_user_mail_config,
    encrypt_smtp_password,
    decrypt_smtp_password,
    get_connection,
    ENCRYPTION_PREFIX
)

class TestAuthAndCryptoSecurity:
    def test_registration_hashes_with_argon2id(self, temp_db):
        ok, msg, user = register_user("secuser", "secuser@example.com", "Password123!")
        assert ok
        assert user is not None
        assert user["username"] == "secuser"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user["id"],))
            stored_hash = cursor.fetchone()[0]
            # Must be an Argon2id hash
            assert stored_hash.startswith("$argon2id")

    def test_successful_and_failed_login(self, temp_db):
        register_user("loginuser", "login@example.com", "SecurePass456!")
        
        # Valid login
        ok, msg, user = authenticate_user("loginuser", "SecurePass456!")
        assert ok
        assert user["username"] == "loginuser"

        # Invalid password
        bad_ok, bad_msg, bad_user = authenticate_user("loginuser", "WrongPassword!")
        assert not bad_ok
        assert bad_user is None

    def test_legacy_sha256_verification_and_automatic_migration(self, temp_db):
        # Insert a simulated legacy user with salted SHA-256
        salt = "abcdef1234567890"
        legacy_pwd = "OldLegacyPass789!"
        legacy_hash = hashlib.sha256((legacy_pwd + salt).encode("utf-8")).hexdigest()

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)",
                ("legacyuser", "legacy@example.com", legacy_hash, salt)
            )
            user_id = cursor.lastrowid
            cursor.execute("INSERT INTO user_profiles (user_id, full_name) VALUES (?, ?)", (user_id, "Legacy User"))
            conn.commit()

        # Step 1: Verify legacy hash works before migration
        assert verify_password(legacy_pwd, legacy_hash, salt)

        # Step 2: Authenticate legacy user - should succeed and automatically rehash to Argon2id
        ok, msg, user = authenticate_user("legacyuser", legacy_pwd)
        assert ok
        assert user["id"] == user_id

        # Step 3: Check database to confirm hash was migrated to Argon2id
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash, salt FROM users WHERE id = ?", (user_id,))
            new_hash, new_salt = cursor.fetchone()
            assert new_hash.startswith("$argon2id")
            assert new_salt == ""

    def test_sql_injection_resistance(self, temp_db):
        # Attempt standard SQL injection payloads
        injection_username = "admin' OR '1'='1"
        ok, msg, user = authenticate_user(injection_username, "any_pass")
        assert not ok
        assert user is None

    def test_smtp_credential_authenticated_encryption(self, temp_db):
        plain_secret = "app_secret_token_1234"
        
        # 1. Test encrypt / decrypt primitives
        encrypted = encrypt_smtp_password(plain_secret)
        assert encrypted.startswith(ENCRYPTION_PREFIX)
        assert plain_secret not in encrypted  # Plaintext never present in ciphertext
        decrypted = decrypt_smtp_password(encrypted)
        assert decrypted == plain_secret

        # 2. Test saving mail config
        register_user("smtpuser", "smtp@example.com", "Password123!")
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = 'smtpuser'")
            uid = cursor.fetchone()[0]

        save_user_mail_config(
            user_id=uid,
            email_address="smtp@example.com",
            app_password=plain_secret,
            smtp_host="smtp.gmail.com",
            smtp_port=465
        )

        # 3. Verify SQLite DB row stores ciphertext, NOT plaintext
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT app_password FROM user_mail_configs WHERE user_id = ?", (uid,))
            db_stored = cursor.fetchone()[0]
            assert db_stored.startswith(ENCRYPTION_PREFIX)
            assert plain_secret not in db_stored

        # 4. Verify retrieval decrypts transparently
        cfg = get_user_mail_config(uid)
        assert cfg["app_password"] == plain_secret
