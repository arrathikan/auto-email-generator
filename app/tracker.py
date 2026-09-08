import sqlite3
import os
import hashlib
import json
import secrets
import re
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

def normalize_subject_text(subject: str) -> str:
    if not subject:
        return ""
    # Strip Re:, Fwd:, [Tag], etc.
    s = re.sub(r'^(re|fwd|fw|aw|vs|antwort):\s*', '', subject, flags=re.IGNORECASE)
    s = re.sub(r'\[.*?\]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip().lower()

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
            normalized_subject TEXT DEFAULT '',
            email_body TEXT,
            status TEXT DEFAULT 'Drafted',
            last_message_id TEXT DEFAULT '',
            thread_id TEXT DEFAULT '',
            reply_status TEXT DEFAULT '',
            interview_date TEXT DEFAULT '',
            meeting_link TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            applied_at TIMESTAMP,
            last_followup_at TIMESTAMP,
            notes TEXT DEFAULT ''
        )
        """)

        # 4. Email Messages (Sent & Received conversation log)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            application_id INTEGER REFERENCES applications(id),
            direction TEXT NOT NULL, -- 'SENT' or 'RECEIVED'
            message_id TEXT UNIQUE,
            in_reply_to TEXT DEFAULT '',
            references_header TEXT DEFAULT '',
            thread_id TEXT DEFAULT '',
            sender_email TEXT NOT NULL,
            recipient_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            normalized_subject TEXT DEFAULT '',
            body_text TEXT DEFAULT '',
            cleaned_body TEXT DEFAULT '',
            confidence TEXT DEFAULT 'HIGH', -- 'HIGH', 'MEDIUM', 'LOW', 'UNMATCHED'
            received_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 5. Structured AI Reply Analyses Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reply_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER REFERENCES applications(id),
            message_id TEXT REFERENCES email_messages(message_id),
            category TEXT NOT NULL,
            confidence_level TEXT DEFAULT 'HIGH',
            interview_date TEXT DEFAULT '',
            interview_time TEXT DEFAULT '',
            interview_type TEXT DEFAULT '',
            meeting_link TEXT DEFAULT '',
            location TEXT DEFAULT '',
            recruiter_contact TEXT DEFAULT '',
            requested_documents TEXT DEFAULT '',
            deadline TEXT DEFAULT '',
            required_action TEXT DEFAULT '',
            important_notes TEXT DEFAULT '',
            raw_analysis_json TEXT DEFAULT '{}',
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 6. User Mailbox Configuration Table (for IMAP sync)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_mail_configs (
            user_id INTEGER PRIMARY KEY REFERENCES users(id),
            imap_host TEXT DEFAULT 'imap.gmail.com',
            imap_port INTEGER DEFAULT 993,
            email_address TEXT DEFAULT '',
            app_password TEXT DEFAULT '',
            last_synced_uid INTEGER DEFAULT 0,
            last_synced_at TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Migrations for existing applications table columns
        cursor.execute("PRAGMA table_info(applications)")
        cols = [r["name"] for r in cursor.fetchall()]
        if "user_id" not in cols:
            try:
                cursor.execute("ALTER TABLE applications ADD COLUMN user_id INTEGER REFERENCES users(id)")
            except Exception:
                pass
        if "last_message_id" not in cols:
            try:
                cursor.execute("ALTER TABLE applications ADD COLUMN last_message_id TEXT DEFAULT ''")
            except Exception:
                pass
        if "thread_id" not in cols:
            try:
                cursor.execute("ALTER TABLE applications ADD COLUMN thread_id TEXT DEFAULT ''")
            except Exception:
                pass
        if "normalized_subject" not in cols:
            try:
                cursor.execute("ALTER TABLE applications ADD COLUMN normalized_subject TEXT DEFAULT ''")
            except Exception:
                pass
        if "reply_status" not in cols:
            try:
                cursor.execute("ALTER TABLE applications ADD COLUMN reply_status TEXT DEFAULT ''")
            except Exception:
                pass
        if "interview_date" not in cols:
            try:
                cursor.execute("ALTER TABLE applications ADD COLUMN interview_date TEXT DEFAULT ''")
            except Exception:
                pass
        if "meeting_link" not in cols:
            try:
                cursor.execute("ALTER TABLE applications ADD COLUMN meeting_link TEXT DEFAULT ''")
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
            
            # Create default mail config entry
            cursor.execute("""
            INSERT INTO user_mail_configs (user_id, email_address)
            VALUES (?, ?)
            """, (user_id, email))
            
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
# Applications Tracker API
# ---------------------------------------------------------
def save_application(company: str, role: str, user_id: int, recipient_email: str = "", match_score: int = 0, subject_line: str = "", email_body: str = "", status: str = "Drafted", notes: str = "", message_id: str = "", thread_id: str = "", sender_email: str = "") -> int:
    applied_at = datetime.now().isoformat() if status in ["Applied", "Sent", "Interview Scheduled", "Reply Received"] else None
    norm_subject = normalize_subject_text(subject_line)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO applications (user_id, company, role, recipient_email, match_score, subject_line, normalized_subject, email_body, status, last_message_id, thread_id, applied_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, company, role, recipient_email, match_score, subject_line, norm_subject, email_body, status, message_id, thread_id, applied_at, notes))
        app_id = cursor.lastrowid

        # Also record outbound email in email_messages table if message_id exists or if sent/applied
        if status in ["Applied", "Sent"] or message_id or email_body:
            sent_msg_id = message_id or f"<outreach_{app_id}_{int(datetime.now().timestamp())}@outreachai.local>"
            cursor.execute("""
            INSERT OR IGNORE INTO email_messages (user_id, application_id, direction, message_id, thread_id, sender_email, recipient_email, subject, normalized_subject, body_text)
            VALUES (?, ?, 'SENT', ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, app_id, sent_msg_id, thread_id, sender_email, recipient_email, subject_line, norm_subject, email_body))
            
            cursor.execute("UPDATE applications SET last_message_id = ? WHERE id = ?", (sent_msg_id, app_id))

        conn.commit()
        return app_id

def get_all_applications(user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE user_id = ? ORDER BY id DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_application_by_id(app_id: int) -> dict | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_application_status(app_id: int, new_status: str, notes: str | None = None, reply_status: str | None = None, interview_date: str | None = None, meeting_link: str | None = None):
    with get_connection() as conn:
        cursor = conn.cursor()
        applied_update = "applied_at = COALESCE(applied_at, CURRENT_TIMESTAMP)," if new_status in ["Applied", "Sent", "Reply Received", "Interview Scheduled"] else ""
        
        cursor.execute(f"""
        UPDATE applications 
        SET status = ?, 
            {applied_update}
            notes = COALESCE(?, notes),
            reply_status = COALESCE(?, reply_status),
            interview_date = COALESCE(?, interview_date),
            meeting_link = COALESCE(?, meeting_link)
        WHERE id = ?
        """, (new_status, notes, reply_status, interview_date, meeting_link, app_id))
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
        cursor.execute("DELETE FROM reply_analyses WHERE application_id = ?", (app_id,))
        cursor.execute("DELETE FROM email_messages WHERE application_id = ?", (app_id,))
        cursor.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        conn.commit()

# ---------------------------------------------------------
# Email Conversation & Reply Logging API
# ---------------------------------------------------------
def save_sent_message(app_id: int, user_id: int, message_id: str, subject: str, recipient_email: str, body_text: str, sender_email: str = "", thread_id: str = ""):
    norm_subject = normalize_subject_text(subject)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO email_messages (user_id, application_id, direction, message_id, thread_id, sender_email, recipient_email, subject, normalized_subject, body_text)
        VALUES (?, ?, 'SENT', ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(message_id) DO UPDATE SET
            body_text = excluded.body_text,
            subject = excluded.subject,
            normalized_subject = excluded.normalized_subject
        """, (user_id, app_id, message_id, thread_id, sender_email, recipient_email, subject, norm_subject, body_text))
        
        cursor.execute("UPDATE applications SET last_message_id = ?, thread_id = COALESCE(NULLIF(?, ''), thread_id) WHERE id = ?", (message_id, thread_id, app_id))
        conn.commit()

def is_reply_already_processed(message_id: str) -> bool:
    if not message_id:
        return False
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM email_messages WHERE message_id = ?", (message_id,))
        return cursor.fetchone() is not None

def record_incoming_reply(app_id: int | None, user_id: int, message_id: str, in_reply_to: str, references_hdr: str, thread_id: str, sender_email: str, recipient_email: str, subject: str, body_text: str, cleaned_body: str, confidence: str = "HIGH", received_at: str | None = None) -> int:
    norm_subject = normalize_subject_text(subject)
    rec_time = received_at or datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO email_messages (user_id, application_id, direction, message_id, in_reply_to, references_header, thread_id, sender_email, recipient_email, subject, normalized_subject, body_text, cleaned_body, confidence, received_at)
        VALUES (?, ?, 'RECEIVED', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, app_id, message_id, in_reply_to, references_hdr, thread_id, sender_email, recipient_email, subject, norm_subject, body_text, cleaned_body, confidence, rec_time))
        msg_db_id = cursor.lastrowid
        conn.commit()
        return msg_db_id

def save_reply_analysis(app_id: int | None, message_id: str, analysis: dict):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO reply_analyses (
            application_id, message_id, category, confidence_level, 
            interview_date, interview_time, interview_type, meeting_link, 
            location, recruiter_contact, requested_documents, deadline, 
            required_action, important_notes, raw_analysis_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            app_id,
            message_id,
            analysis.get("category", "General Company Response"),
            analysis.get("confidence_level", "HIGH"),
            analysis.get("interview_date", ""),
            analysis.get("interview_time", ""),
            analysis.get("interview_type", ""),
            analysis.get("meeting_link", ""),
            analysis.get("location", ""),
            analysis.get("recruiter_contact", ""),
            analysis.get("requested_documents", ""),
            analysis.get("deadline", ""),
            analysis.get("required_action", ""),
            analysis.get("important_notes", ""),
            json.dumps(analysis)
        ))
        conn.commit()

def get_application_messages(app_id: int) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT m.*, a.category, a.interview_date as analysis_interview_date, a.interview_time, a.meeting_link as analysis_meeting_link, a.required_action, a.important_notes
        FROM email_messages m
        LEFT JOIN reply_analyses a ON m.message_id = a.message_id
        WHERE m.application_id = ?
        ORDER BY m.id ASC
        """, (app_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_latest_reply_analysis(app_id: int) -> dict | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM reply_analyses 
        WHERE application_id = ? 
        ORDER BY id DESC LIMIT 1
        """, (app_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_unmatched_replies(user_id: int) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT m.*, a.category, a.required_action, a.important_notes
        FROM email_messages m
        LEFT JOIN reply_analyses a ON m.message_id = a.message_id
        WHERE m.user_id = ? AND (m.application_id IS NULL OR m.confidence = 'UNMATCHED')
        ORDER BY m.id DESC
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

# ---------------------------------------------------------
# Deterministic Reply Matching Database Query
# ---------------------------------------------------------
def find_application_by_headers_or_subject(user_id: int, thread_id: str = "", in_reply_to: str = "", references_hdr: str = "", subject: str = "", sender_email: str = "") -> tuple[dict | None, str]:
    """
    Evaluates candidate applications using deterministic email headers and normalized subject.
    Returns (matched_application_dict, confidence_level).
    Confidence Levels: 'HIGH', 'MEDIUM', 'LOW', 'UNMATCHED'
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Priority 1: Gmail thread_id match (HIGH Confidence)
        if thread_id:
            cursor.execute("""
            SELECT a.* FROM applications a
            JOIN email_messages m ON a.id = m.application_id
            WHERE a.user_id = ? AND (m.thread_id = ? OR a.thread_id = ?)
            LIMIT 1
            """, (user_id, thread_id, thread_id))
            row = cursor.fetchone()
            if row:
                return dict(row), "HIGH"

        # Priority 2: In-Reply-To matches sent Message-ID (HIGH Confidence)
        if in_reply_to:
            clean_irt = in_reply_to.strip().strip("<>").strip()
            cursor.execute("""
            SELECT a.* FROM applications a
            JOIN email_messages m ON a.id = m.application_id
            WHERE a.user_id = ? AND (m.message_id = ? OR m.message_id LIKE ? OR a.last_message_id = ?)
            LIMIT 1
            """, (user_id, in_reply_to, f"%{clean_irt}%", in_reply_to))
            row = cursor.fetchone()
            if row:
                return dict(row), "HIGH"

        # Priority 3: References header contains sent Message-ID (MEDIUM Confidence)
        if references_hdr:
            cursor.execute("""
            SELECT m.message_id, a.* FROM applications a
            JOIN email_messages m ON a.id = m.application_id
            WHERE a.user_id = ? AND m.direction = 'SENT'
            """, (user_id,))
            rows = cursor.fetchall()
            for r in rows:
                mid = r["message_id"] or ""
                clean_mid = mid.strip().strip("<>").strip()
                if clean_mid and (clean_mid in references_hdr or mid in references_hdr):
                    return dict(r), "MEDIUM"

        # Fallback (Subject + Sender Domain match with safety checks)
        norm_subj = normalize_subject_text(subject)
        sender_clean = sender_email.strip().lower()
        sender_domain = sender_clean.split("@")[-1] if "@" in sender_clean else ""

        if norm_subj and len(norm_subj) > 5:
            # Check applications matching normalized subject
            cursor.execute("""
            SELECT * FROM applications 
            WHERE user_id = ? AND (normalized_subject = ? OR ? LIKE '%' || normalized_subject || '%')
            ORDER BY id DESC
            """, (user_id, norm_subj, norm_subj))
            candidates = [dict(r) for r in cursor.fetchall()]

            for cand in candidates:
                cand_recipient = (cand.get("recipient_email") or "").lower()
                cand_company = (cand.get("company") or "").lower()
                cand_domain = cand_recipient.split("@")[-1] if "@" in cand_recipient else ""

                # Safety guard: Check company name or domain match to avoid associating unrelated emails
                if (sender_domain and cand_domain and sender_domain == cand_domain) or \
                   (cand_company and len(cand_company) > 3 and cand_company in sender_clean) or \
                   (cand_recipient and cand_recipient in sender_clean):
                    return cand, "LOW"

        return None, "UNMATCHED"

# ---------------------------------------------------------
# User Mailbox Configuration API
# ---------------------------------------------------------
def get_user_mail_config(user_id: int) -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_mail_configs WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {
            "imap_host": "imap.gmail.com",
            "imap_port": 993,
            "email_address": "",
            "app_password": "",
            "last_synced_uid": 0,
            "last_synced_at": None
        }

def save_user_mail_config(user_id: int, imap_host: str, imap_port: int, email_address: str, app_password: str, last_synced_uid: int | None = None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO user_mail_configs (user_id, imap_host, imap_port, email_address, app_password, last_synced_uid, last_synced_at, updated_at)
        VALUES (?, ?, ?, ?, ?, COALESCE(?, 0), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            imap_host = excluded.imap_host,
            imap_port = excluded.imap_port,
            email_address = excluded.email_address,
            app_password = CASE WHEN excluded.app_password != '' THEN excluded.app_password ELSE user_mail_configs.app_password END,
            last_synced_uid = COALESCE(?, user_mail_configs.last_synced_uid),
            last_synced_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        """, (user_id, imap_host, imap_port, email_address, app_password, last_synced_uid, last_synced_uid))
        conn.commit()

def update_last_synced_uid(user_id: int, last_uid: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE user_mail_configs 
        SET last_synced_uid = ?, last_synced_at = CURRENT_TIMESTAMP 
        WHERE user_id = ?
        """, (last_uid, user_id))
        conn.commit()

# ---------------------------------------------------------
# Dynamic Alerts (Recruiter Replies & Follow-Ups)
# ---------------------------------------------------------
def get_user_alerts(user_id: int) -> dict:
    apps = get_all_applications(user_id=user_id)
    replies = []
    pending_followups = []
    now = datetime.now()

    for app in apps:
        status = app["status"]
        if status in ["Reply Received", "Interview Scheduled", "Offer", "Assessment / Test"]:
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
