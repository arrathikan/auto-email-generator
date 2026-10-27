"""
Database management and SQLite data operations for CareerLens.
Manages users, user profiles, and encrypted mail configurations.
"""
import sqlite3
import json
import sys
from .config import DEFAULT_DB_PATH
from .auth import hash_password, verify_password, check_needs_rehash
from .security import (
    ENCRYPTION_PREFIX,
    encrypt_smtp_password,
    decrypt_smtp_password
)

DB_PATH = DEFAULT_DB_PATH

def get_db_path() -> str:
    """Returns currently active database path, respecting any test monkeypatching on tracker.DB_PATH."""
    tracker_mod = sys.modules.get("tracker")
    if tracker_mod and hasattr(tracker_mod, "DB_PATH"):
        return getattr(tracker_mod, "DB_PATH")
    return DB_PATH

def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str | None = None):
    with get_connection(db_path) as conn:
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

def register_user(username: str, email_addr: str, password: str, db_path: str | None = None) -> tuple[bool, str, dict | None]:
    username = username.strip().lower()
    email_addr = email_addr.strip().lower()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long.", None
    if len(password) < 6:
        return False, "Password must be at least 6 characters long.", None
    if "@" not in email_addr:
        return False, "Please provide a valid email address.", None

    pwd_hash, salt = hash_password(password)
    
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)",
                (username, email_addr, pwd_hash, salt)
            )
            user_id = cursor.lastrowid
            
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

def authenticate_user(username: str, password: str, db_path: str | None = None) -> tuple[bool, str, dict | None]:
    username = username.strip().lower()
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username))
        user = cursor.fetchone()
        
        if not user:
            return False, "We couldn't sign you in with those details. Check your email and password and try again.", None
            
        stored_hash = user["password_hash"]
        salt = user["salt"] or ""

        if verify_password(password, stored_hash, salt):
            if check_needs_rehash(stored_hash):
                try:
                    new_hash, _ = hash_password(password)
                    cursor.execute(
                        "UPDATE users SET password_hash = ?, salt = '' WHERE id = ?",
                        (new_hash, user["id"])
                    )
                    conn.commit()
                except Exception:
                    pass

            return True, "Login successful!", {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
        else:
            return False, "We couldn't sign you in with those details. Check your email and password and try again.", None

def get_user_profile(user_id: int, db_path: str | None = None) -> dict:
    with get_connection(db_path) as conn:
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
    cv_file_path: str = "",
    db_path: str | None = None
):
    with get_connection(db_path) as conn:
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

def _get_key_dir() -> str | None:
    tracker_mod = sys.modules.get("tracker")
    if tracker_mod and hasattr(tracker_mod, "DB_DIR"):
        return getattr(tracker_mod, "DB_DIR")
    return None

def get_user_mail_config(user_id: int, db_path: str | None = None) -> dict:
    key_dir = _get_key_dir()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_mail_configs WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            d = dict(row)
            stored_pwd = d.get("app_password", "")
            if stored_pwd and not stored_pwd.startswith(ENCRYPTION_PREFIX):
                try:
                    encrypted_pwd = encrypt_smtp_password(stored_pwd, key_dir=key_dir)
                    cursor.execute(
                        "UPDATE user_mail_configs SET app_password = ? WHERE user_id = ?",
                        (encrypted_pwd, user_id)
                    )
                    conn.commit()
                except Exception:
                    pass
                d["app_password"] = stored_pwd
            elif stored_pwd:
                d["app_password"] = decrypt_smtp_password(stored_pwd, key_dir=key_dir)
            return d
        return {}

def save_user_mail_config(
    user_id: int,
    email_address: str,
    app_password: str = "",
    smtp_host: str = "",
    smtp_port: int = 465,
    db_path: str | None = None
):
    key_dir = _get_key_dir()
    stored_password = encrypt_smtp_password(app_password, key_dir=key_dir) if app_password else ""

    with get_connection(db_path) as conn:
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
