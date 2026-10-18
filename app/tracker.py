import sqlite3
import os
import hashlib
import json
import secrets
from datetime import datetime
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from cryptography.fernet import Fernet, InvalidToken

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "tracker.db")

# Initialize Argon2id password hasher (RFC 9106 recommended parameters)
_password_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MB
    parallelism=1,
    hash_len=32,
    salt_len=16
)

# Prefix used to distinguish authenticated encrypted credentials from legacy plaintext
ENCRYPTION_PREFIX = "enc_v1:"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- SMTP Encryption Key Management ---
def _get_encryption_cipher() -> Fernet:
    """
    Retrieves or initializes the authenticated Fernet encryption key.
    Security rules:
    - The key is NEVER stored in the tracker.db database.
    - First checks environment variables (ENCRYPTION_KEY or SMTP_SECRET_KEY).
    - If absent from environment, loads from a protected local key file (.smtp_secret.key).
    - If neither exists, generates a fresh Fernet key and saves it to .smtp_secret.key with 0600 permissions.
    """
    key_str = (os.getenv("ENCRYPTION_KEY") or os.getenv("SMTP_SECRET_KEY") or "").strip()
    if not key_str:
        key_file = os.path.join(DB_DIR, ".smtp_secret.key")
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

def encrypt_smtp_password(plaintext: str) -> str:
    """
    Encrypts an SMTP App Password using authenticated Fernet (AES-128-CBC + HMAC-SHA256).
    Returns ciphertext prefixed with 'enc_v1:'.
    """
    if not plaintext:
        return ""
    if plaintext.startswith(ENCRYPTION_PREFIX):
        return plaintext  # Already encrypted
    cipher = _get_encryption_cipher()
    encrypted = cipher.encrypt(plaintext.encode("utf-8"))
    return f"{ENCRYPTION_PREFIX}{encrypted.decode('utf-8')}"

def decrypt_smtp_password(stored_val: str) -> str:
    """
    Decrypts an encrypted SMTP password. If the stored value is legacy plaintext,
    it returns the plaintext directly so callers can transparently migrate it.
    """
    if not stored_val:
        return ""
    if not stored_val.startswith(ENCRYPTION_PREFIX):
        return stored_val  # Legacy plaintext, return as-is for migration

    try:
        cipher = _get_encryption_cipher()
        token = stored_val[len(ENCRYPTION_PREFIX):].encode("utf-8")
        decrypted = cipher.decrypt(token)
        return decrypted.decode("utf-8")
    except (InvalidToken, Exception):
        # Never leak ciphertext or key details on decryption error
        return ""

# --- Password Hashing API ---
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

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Users Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 2. User Profiles Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY REFERENCES users(id),
            full_name TEXT DEFAULT '',
            position TEXT DEFAULT '',
            college TEXT DEFAULT '',
            degree TEXT DEFAULT '',
            candidate_type TEXT DEFAULT 'Student / Recent Graduate',
            custom_notes TEXT DEFAULT '',
            portfolio_json TEXT DEFAULT '[]',
            cv_filename TEXT DEFAULT '',
            cv_file_path TEXT DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 3. User Mail Config (for direct SMTP dispatch)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_mail_configs (
            user_id INTEGER PRIMARY KEY REFERENCES users(id),
            email_address TEXT DEFAULT '',
            app_password TEXT DEFAULT '',
            smtp_host TEXT DEFAULT '',
            smtp_port INTEGER DEFAULT 465,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()

# Initialize DB upon import
init_db()

# --- User Authentication API ---
def register_user(username: str, email_addr: str, password: str) -> tuple[bool, str, dict | None]:
    username = username.strip().lower()
    email_addr = email_addr.strip().lower()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long.", None
    if len(password) < 6:
        return False, "Password must be at least 6 characters long.", None
    if "@" not in email_addr:
        return False, "Please provide a valid email address.", None

    # Hash with Argon2id
    pwd_hash, salt = hash_password(password)
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)",
                (username, email_addr, pwd_hash, salt)
            )
            user_id = cursor.lastrowid
            
            # Create default empty profile
            cursor.execute(
                "INSERT INTO user_profiles (user_id, full_name) VALUES (?, ?)",
                (user_id, username.title())
            )
            cursor.execute(
                "INSERT INTO user_mail_configs (user_id, email_address) VALUES (?, ?)",
                (user_id, email_addr)
            )
            conn.commit()
            
            return True, "Account created successfully!", {
                "id": user_id,
                "username": username,
                "email": email_addr
            }
    except sqlite3.IntegrityError as e:
        err_msg = str(e).lower()
        if "username" in err_msg:
            return False, f"Username '{username}' is already taken.", None
        elif "email" in err_msg:
            return False, f"Email '{email_addr}' is already registered.", None
        return False, "User with this username or email already exists.", None

def authenticate_user(username: str, password: str) -> tuple[bool, str, dict | None]:
    username = username.strip().lower()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username))
        user = cursor.fetchone()
        
        if not user:
            return False, "We couldn't sign you in with those details. Check your email and password and try again.", None
            
        stored_hash = user["password_hash"]
        salt = user["salt"] or ""

        if verify_password(password, stored_hash, salt):
            # Automatic rehash & migration on successful login
            if check_needs_rehash(stored_hash):
                try:
                    new_hash, _ = hash_password(password)
                    cursor.execute(
                        "UPDATE users SET password_hash = ?, salt = '' WHERE id = ?",
                        (new_hash, user["id"])
                    )
                    conn.commit()
                except Exception:
                    pass  # Non-blocking rehash failure

            return True, "Login successful!", {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
        else:
            return False, "We couldn't sign you in with those details. Check your email and password and try again.", None

def get_user_profile(user_id: int) -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            d = dict(row)
            try:
                d["portfolio"] = json.loads(d.get("portfolio_json") or "[]")
            except Exception:
                d["portfolio"] = []
            return d
        return {}

def save_user_profile(
    user_id: int,
    full_name: str,
    position: str,
    college: str,
    degree: str,
    candidate_type: str,
    custom_notes: str,
    portfolio: list[dict],
    cv_filename: str = "",
    cv_file_path: str = ""
):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO user_profiles (
            user_id, full_name, position, college, degree, 
            candidate_type, custom_notes, portfolio_json, cv_filename, cv_file_path, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            full_name = excluded.full_name,
            position = excluded.position,
            college = excluded.college,
            degree = excluded.degree,
            candidate_type = excluded.candidate_type,
            custom_notes = excluded.custom_notes,
            portfolio_json = excluded.portfolio_json,
            cv_filename = CASE WHEN excluded.cv_filename != '' THEN excluded.cv_filename ELSE user_profiles.cv_filename END,
            cv_file_path = CASE WHEN excluded.cv_file_path != '' THEN excluded.cv_file_path ELSE user_profiles.cv_file_path END,
            updated_at = CURRENT_TIMESTAMP
        """, (
            user_id, full_name, position, college, degree,
            candidate_type, custom_notes, json.dumps(portfolio),
            cv_filename, cv_file_path
        ))
        conn.commit()

def get_user_mail_config(user_id: int) -> dict:
    """
    Retrieves SMTP settings for user.
    Transparently decrypts encrypted app_password and migrates legacy plaintext credentials to ciphertext.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_mail_configs WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            d = dict(row)
            stored_pwd = d.get("app_password", "")
            if stored_pwd and not stored_pwd.startswith(ENCRYPTION_PREFIX):
                # Legacy plaintext password detected: silently migrate to authenticated encryption
                try:
                    encrypted_pwd = encrypt_smtp_password(stored_pwd)
                    cursor.execute(
                        "UPDATE user_mail_configs SET app_password = ? WHERE user_id = ?",
                        (encrypted_pwd, user_id)
                    )
                    conn.commit()
                except Exception:
                    pass
                d["app_password"] = stored_pwd
            elif stored_pwd:
                d["app_password"] = decrypt_smtp_password(stored_pwd)
            return d
        return {}

def save_user_mail_config(
    user_id: int,
    email_address: str,
    app_password: str = "",
    smtp_host: str = "",
    smtp_port: int = 465
):
    """
    Saves SMTP settings with authenticated encryption for app_password.
    Never stores app_password in plaintext.
    """
    # Encrypt password before storing if a non-empty password is provided
    stored_password = encrypt_smtp_password(app_password) if app_password else ""

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO user_mail_configs (user_id, email_address, app_password, smtp_host, smtp_port, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            email_address = excluded.email_address,
            app_password = CASE WHEN excluded.app_password != '' THEN excluded.app_password ELSE user_mail_configs.app_password END,
            smtp_host = CASE WHEN excluded.smtp_host != '' THEN excluded.smtp_host ELSE user_mail_configs.smtp_host END,
            smtp_port = excluded.smtp_port,
            updated_at = CURRENT_TIMESTAMP
        """, (user_id, email_address, stored_password, smtp_host, smtp_port))
        conn.commit()
