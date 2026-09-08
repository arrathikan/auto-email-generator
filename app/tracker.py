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

        # 3. Applications Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            recipient_email TEXT,
            match_score INTEGER DEFAULT 0,
            subject_line TEXT,
            email_body TEXT,
            status TEXT DEFAULT 'Drafted',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            applied_at TIMESTAMP,
            last_followup_at TIMESTAMP,
            notes TEXT DEFAULT ''
        )
        """)

        # Check and migrate user_id if missing
        cursor.execute("PRAGMA table_info(applications)")
        cols = [r["name"] for r in cursor.fetchall()]
        if "user_id" not in cols:
            try:
                cursor.execute("ALTER TABLE applications ADD COLUMN user_id INTEGER REFERENCES users(id)")
            except Exception:
                pass

        conn.commit()

init_db()

# ---------------------------------------------------------
# User Authentication API
# ---------------------------------------------------------
def register_user(username: str, email: str, password: str) -> tuple[bool, str, dict | None]:
    username = username.strip().lower()
    email = email.strip().lower()
    if len(username) < 3:
        return False, "Username must be at least 3 characters.", None
    if len(password) < 6:
        return False, "Password must be at least 6 characters.", None
    if "@" not in email:
        return False, "Please enter a valid email address.", None

    pwd_hash, salt = hash_password(password)
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
            INSERT INTO users (username, email, password_hash, salt)
            VALUES (?, ?, ?, ?)
            """, (username, email, pwd_hash, salt))
            user_id = cursor.lastrowid
            
            # Create blank profile
            cursor.execute("""
            INSERT INTO user_profiles (user_id, full_name, position, college, degree, candidate_type, portfolio_json)
            VALUES (?, ?, '', '', '', 'Student / Recent Graduate', '[]')
            """, (user_id, username.capitalize()))
            
            conn.commit()
            return True, "Account created successfully!", {"id": user_id, "username": username, "email": email}
        except sqlite3.IntegrityError:
            return False, "Username or email already exists. Please sign in.", None

def authenticate_user(username_or_email: str, password: str) -> tuple[bool, str, dict | None]:
    query = username_or_email.strip().lower()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, username, email, password_hash, salt 
        FROM users 
        WHERE username = ? OR email = ?
        """, (query, query))
        user = cursor.fetchone()
        
        if not user:
            return False, "User not found. Please check your credentials or create an account.", None
        
        if verify_password(password, user["password_hash"], user["salt"]):
            return True, "Login successful!", {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
        else:
            return False, "Incorrect password. Please try again.", None

# ---------------------------------------------------------
# Profile Persistence API
# ---------------------------------------------------------
def save_user_profile(user_id: int, full_name: str, position: str, college: str, degree: str, candidate_type: str, custom_notes: str, portfolio_data, cv_filename: str = "", cv_file_path: str = ""):
    if isinstance(portfolio_data, list):
        portfolio_json = json.dumps(portfolio_data)
    elif hasattr(portfolio_data, "to_dict"):
        portfolio_json = json.dumps(portfolio_data.to_dict(orient="records"))
    else:
        portfolio_json = "[]"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO user_profiles (user_id, full_name, position, college, degree, candidate_type, custom_notes, portfolio_json, cv_filename, cv_file_path, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            full_name = excluded.full_name,
            position = excluded.position,
            college = excluded.college,
            degree = excluded.degree,
            candidate_type = excluded.candidate_type,
            custom_notes = excluded.custom_notes,
            portfolio_json = excluded.portfolio_json,
            cv_filename = COALESCE(NULLIF(excluded.cv_filename, ''), user_profiles.cv_filename),
            cv_file_path = COALESCE(NULLIF(excluded.cv_file_path, ''), user_profiles.cv_file_path),
            updated_at = CURRENT_TIMESTAMP
        """, (user_id, full_name, position, college, degree, candidate_type, custom_notes, portfolio_json, cv_filename, cv_file_path))
        conn.commit()

def get_user_profile(user_id: int) -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            res = dict(row)
            try:
                res["portfolio"] = json.loads(res.get("portfolio_json") or "[]")
            except Exception:
                res["portfolio"] = []
            return res
        return {
            "full_name": "", "position": "", "college": "", "degree": "",
            "candidate_type": "Student / Recent Graduate", "custom_notes": "",
            "portfolio": [], "cv_filename": "", "cv_file_path": ""
        }

# ---------------------------------------------------------
# Applications Tracker API (Scoped to User)
# ---------------------------------------------------------
def save_application(company: str, role: str, user_id: int, recipient_email: str = "", match_score: int = 0, subject_line: str = "", email_body: str = "", status: str = "Drafted", notes: str = "") -> int:
    applied_at = datetime.now().isoformat() if status in ["Applied", "Sent", "Interview Scheduled", "Reply Received"] else None
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO applications (user_id, company, role, recipient_email, match_score, subject_line, email_body, status, applied_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, company, role, recipient_email, match_score, subject_line, email_body, status, applied_at, notes))
        conn.commit()
        return cursor.lastrowid

def get_all_applications(user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE user_id = ? ORDER BY id DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def update_application_status(app_id: int, new_status: str, notes: str | None = None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if new_status in ["Applied", "Sent", "Reply Received", "Interview Scheduled"]:
            cursor.execute("""
            UPDATE applications 
            SET status = ?, applied_at = COALESCE(applied_at, CURRENT_TIMESTAMP), notes = COALESCE(?, notes)
            WHERE id = ?
            """, (new_status, notes, app_id))
        else:
            cursor.execute("""
            UPDATE applications 
            SET status = ?, notes = COALESCE(?, notes)
            WHERE id = ?
            """, (new_status, notes, app_id))
        conn.commit()

def log_followup(app_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE applications 
        SET last_followup_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (app_id,))
        conn.commit()

def delete_application(app_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        conn.commit()

def get_user_alerts(user_id: int) -> dict:
    apps = get_all_applications(user_id=user_id)
    replies = []
    pending_followups = []
    now = datetime.now()

    for app in apps:
        status = app["status"]
        if status in ["Reply Received", "Interview Scheduled", "Offer"]:
            replies.append(app)
        elif status in ["Applied", "Sent"]:
            ref_date_str = app["last_followup_at"] or app["applied_at"] or app["created_at"]
            try:
                ref_date = datetime.fromisoformat(ref_date_str.split(".")[0].replace("Z", ""))
                days_passed = (now - ref_date).days
                if days_passed >= 3:
                    app_copy = dict(app)
                    app_copy["days_since_applied"] = days_passed
                    pending_followups.append(app_copy)
            except Exception:
                continue

    return {
        "replies": replies,
        "pending_followups": pending_followups
    }
