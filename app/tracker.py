import sqlite3
import os
import hashlib
import json
import secrets
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "tracker.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    salted = password + salt
    pwd_hash = hashlib.sha256(salted.encode("utf-8")).hexdigest()
    return pwd_hash, salt

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    pwd_hash, _ = hash_password(password, salt)
    return pwd_hash == stored_hash

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
            
        if verify_password(password, user["password_hash"], user["salt"]):
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
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_mail_configs WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {}

def save_user_mail_config(
    user_id: int,
    email_address: str,
    app_password: str = "",
    smtp_host: str = "",
    smtp_port: int = 465
):
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
        """, (user_id, email_address, app_password, smtp_host, smtp_port))
        conn.commit()
