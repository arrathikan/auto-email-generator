"""
Security and authenticated cryptography operations for credentials.
Uses Fernet (AES-128-CBC + HMAC-SHA256) for SMTP app passwords.
"""
import os
from cryptography.fernet import Fernet, InvalidToken
from .config import DATA_DIR

ENCRYPTION_PREFIX = "enc_v1:"

def get_encryption_cipher(key_dir: str | None = None) -> Fernet:
    """
    Retrieves or initializes the authenticated Fernet encryption key.
    Security rules:
    - The key is NEVER stored in the database.
    - First checks environment variables (ENCRYPTION_KEY or SMTP_SECRET_KEY).
    - If absent, loads from a protected local key file (.smtp_secret.key).
    - If neither exists, generates a fresh Fernet key and saves it with 0600 permissions.
    """
    key_str = (os.getenv("ENCRYPTION_KEY") or os.getenv("SMTP_SECRET_KEY") or "").strip()
    if not key_str:
        target_dir = key_dir or DATA_DIR
        key_file = os.path.join(target_dir, ".smtp_secret.key")
        if os.path.exists(key_file):
            try:
                with open(key_file, "rb") as f:
                    key_str = f.read().decode("utf-8").strip()
            except Exception:
                pass

        if not key_str:
            new_key = Fernet.generate_key()
            try:
                with open(key_file, "wb") as f:
                    f.write(new_key)
                os.chmod(key_file, 0o600)
            except Exception:
                pass
            key_str = new_key.decode("utf-8")

    return Fernet(key_str.encode("utf-8"))

def encrypt_smtp_password(plaintext: str, key_dir: str | None = None) -> str:
    """
    Encrypts an SMTP App Password using authenticated Fernet (AES-128-CBC + HMAC-SHA256).
    Returns ciphertext prefixed with 'enc_v1:'.
    """
    if not plaintext:
        return ""
    if plaintext.startswith(ENCRYPTION_PREFIX):
        return plaintext
    cipher = get_encryption_cipher(key_dir)
    encrypted = cipher.encrypt(plaintext.encode("utf-8"))
    return f"{ENCRYPTION_PREFIX}{encrypted.decode('utf-8')}"

def decrypt_smtp_password(stored_val: str, key_dir: str | None = None) -> str:
    """
    Decrypts an encrypted SMTP password. If the stored value is legacy plaintext,
    it returns the plaintext directly so callers can transparently migrate it.
    """
    if not stored_val:
        return ""
    if not stored_val.startswith(ENCRYPTION_PREFIX):
        return stored_val

    try:
        cipher = get_encryption_cipher(key_dir)
        token = stored_val[len(ENCRYPTION_PREFIX):].encode("utf-8")
        decrypted = cipher.decrypt(token)
        return decrypted.decode("utf-8")
    except (InvalidToken, Exception):
        return ""
