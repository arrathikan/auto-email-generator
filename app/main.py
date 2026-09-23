import os
import sys
import re
import json
import base64
import smtplib
from email.message import EmailMessage
import pandas as pd
import streamlit as st
from pypdf import PdfReader
try:
    import docx
except ImportError:
    docx = None

from langchain_community.document_loaders import WebBaseLoader
from chain import Chain
from portfolio import Portfolio
import tracker
import mailer

sys.path.append(os.path.dirname(__file__))

# ---------------------------------------------------------
# Page Configuration & Clean Career-Tech Theme
# ---------------------------------------------------------
st.set_page_config(
    page_title="CareerLens — Job Fit & Application Studio",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    letter-spacing: -0.01em;
}

h1, h2, h3, .career-title, .card-title {
    font-family: 'Outfit', 'Plus Jakarta Sans', sans-serif !important;
}

/* Neutral Deep Slate Canvas */
.stApp {
    background-color: #0b0f19;
    background-image: 
        radial-gradient(at 15% 15%, rgba(79, 70, 229, 0.07) 0px, transparent 50%),
        radial-gradient(at 85% 85%, rgba(14, 165, 233, 0.05) 0px, transparent 50%);
    color: #e2e8f0;
}

/* Smooth Micro-Animations (150-250ms) */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulseDot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(0.9); }
}

.animate-fade-in {
    animation: fadeIn 0.22s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

/* Career Platform Cards */
.career-card {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.35);
    transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
    animation: fadeIn 0.25s ease-out;
}

.career-card:hover {
    border-color: rgba(99, 102, 241, 0.3);
    box-shadow: 0 8px 25px -4px rgba(0, 0, 0, 0.45);
}

.card-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 0.85rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Welcome Hero Box */
.welcome-banner {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 18px;
    padding: 2rem 2.25rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}

.welcome-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #4f46e5, #06b6d4, #10b981);
}

.welcome-title {
    font-size: 1.95rem;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: -0.03em;
    margin-bottom: 0.35rem;
}

.welcome-desc {
    color: #94a3b8;
    font-size: 1rem;
    line-height: 1.55;
    max-width: 780px;
}

/* Real Status Overview Tiles (No Fake Stats) */
.status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
    margin-top: 1.25rem;
}

.status-tile {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    padding: 1rem 1.15rem;
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.status-tile:hover {
    border-color: rgba(99, 102, 241, 0.35);
    transform: translateY(-1.5px);
}

.tile-label {
    font-size: 0.76rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.3rem;
}

.tile-value {
    font-size: 1.05rem;
    font-weight: 700;
    color: #f1f5f9;
}

.tile-sub {
    font-size: 0.8rem;
    color: #94a3b8;
    margin-top: 0.2rem;
}

/* Workflow Step Indicator */
.workflow-stepper {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    margin: 1.25rem 0;
    padding: 0.85rem 1.15rem;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    align-items: center;
}

.step-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.84rem;
    font-weight: 600;
    color: #94a3b8;
}

.step-item.active {
    color: #818cf8;
}

.step-item.completed {
    color: #10b981;
}

.step-badge {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.72rem;
    font-weight: 700;
    background: rgba(255, 255, 255, 0.08);
    color: #94a3b8;
}

.step-item.active .step-badge {
    background: #4f46e5;
    color: #ffffff;
}

.step-item.completed .step-badge {
    background: #10b981;
    color: #ffffff;
}

.step-arrow {
    color: #475569;
    font-size: 0.8rem;
}

/* Accessible Skill Chips */
.skill-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.75rem;
    border-radius: 8px;
    font-size: 0.84rem;
    font-weight: 600;
    margin: 0.25rem;
    transition: transform 0.15s ease, background 0.15s ease;
}

.skill-chip:hover {
    transform: translateY(-1px);
}

.skill-chip.matched {
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #a7f3d0;
}

.skill-chip.partial {
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.35);
    color: #fde68a;
}

.skill-chip.gap {
    background: rgba(100, 116, 139, 0.15);
    border: 1px solid rgba(100, 116, 139, 0.35);
    color: #cbd5e1;
}

/* Match Score Visualization */
.score-hero-card {
    background: #0f172a;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.score-display {
    font-size: 3.2rem;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.04em;
}

.score-label-badge {
    display: inline-block;
    padding: 0.25rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.84rem;
    font-weight: 700;
    margin-top: 0.5rem;
}

/* Requirement Audit Comparison Rows */
.audit-row {
    background: rgba(15, 23, 42, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 0.85rem 1.15rem;
    margin-bottom: 0.65rem;
    transition: border-color 0.15s ease;
}

.audit-row:hover {
    border-color: rgba(255, 255, 255, 0.14);
}

/* Clean Professional Email Composer Window */
.email-composer-frame {
    background: #080c16;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    overflow: hidden;
    margin: 1rem 0 1.5rem 0;
    box-shadow: 0 16px 36px -8px rgba(0, 0, 0, 0.5);
}

.composer-toolbar {
    background: #0f172a;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding: 0.65rem 1.25rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.composer-dots {
    display: flex;
    gap: 0.4rem;
}

.composer-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
}

.composer-dot.red { background: #ef4444; }
.composer-dot.yellow { background: #f59e0b; }
.composer-dot.green { background: #10b981; }

.composer-headers {
    background: rgba(15, 23, 42, 0.4);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    padding: 0.85rem 1.35rem;
}

.composer-row {
    display: flex;
    gap: 0.65rem;
    font-size: 0.88rem;
    line-height: 1.8;
}

.composer-field-label {
    width: 60px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    font-size: 0.74rem;
}

.composer-field-value {
    color: #f1f5f9;
    font-weight: 500;
}

.composer-body {
    padding: 1.6rem 1.8rem;
    font-size: 1rem;
    line-height: 1.8;
    color: #f8fafc;
    white-space: pre-wrap;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

/* Polished Dark Form Controls */
div[data-baseweb="input"] {
    background-color: #0f172a !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
}

div[data-baseweb="input"]:focus-within {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
}

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    color: #ffffff !important;
    background-color: transparent !important;
    font-size: 0.96rem !important;
}

div.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
    padding: 0.6rem 1.4rem !important;
    transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
}

div.stButton > button:hover {
    transform: translateY(-1.5px) !important;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.35) !important;
}

div.stButton > button:active {
    transform: translateY(0) scale(0.99) !important;
}

div.stButton > button[kind="primary"] {
    background: #4f46e5 !important;
    color: #ffffff !important;
    border-color: #6366f1 !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35) !important;
}

div.stButton > button[kind="primary"]:hover {
    background: #4338ca !important;
    border-color: #818cf8 !important;
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.5) !important;
}

/* -----------------------------------------
   Auth Split-Screen System (Login & Register)
-------------------------------------------- */
.auth-split-container {
    max-width: 1180px;
    margin: 1.5rem auto 2.5rem auto;
}

.auth-visual-panel {
    background: linear-gradient(145deg, rgba(17, 24, 39, 0.95) 0%, rgba(11, 15, 25, 0.98) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 2.2rem 2rem;
    box-shadow: 0 12px 36px -8px rgba(0, 0, 0, 0.5);
    animation: fadeIn 0.25s ease-out;
}

.auth-workflow-card {
    background: #0d1322;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.65rem;
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.auth-workflow-card:hover {
    border-color: rgba(99, 102, 241, 0.35);
    transform: translateY(-1.5px);
}

.auth-node-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.4rem;
}

.auth-node-title {
    font-size: 0.92rem;
    font-weight: 700;
    color: #f1f5f9;
}

.auth-node-badge {
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.15rem 0.55rem;
    border-radius: 6px;
    background: rgba(99, 102, 241, 0.15);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.3);
}

.auth-connector {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: -0.15rem 0 0.5rem 0;
}

.auth-connector-line {
    width: 2px;
    height: 14px;
    background: linear-gradient(180deg, #4f46e5 0%, rgba(99, 102, 241, 0.25) 100%);
}

.auth-form-card {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 20px;
    padding: 2.25rem 2.2rem;
    box-shadow: 0 16px 40px -10px rgba(0, 0, 0, 0.55);
    animation: fadeIn 0.25s ease-out;
}

.auth-brand-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.85rem;
    background: rgba(79, 70, 229, 0.12);
    border: 1px solid rgba(79, 70, 229, 0.25);
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 700;
    color: #818cf8;
    margin-bottom: 0.85rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.auth-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.85rem;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: -0.03em;
    line-height: 1.2;
    margin-bottom: 0.35rem;
}

.auth-subtitle {
    font-size: 0.94rem;
    color: #94a3b8;
    margin-bottom: 1.5rem;
    line-height: 1.5;
}

.auth-strength-container {
    margin: 0.35rem 0 0.65rem 0;
}

.auth-strength-bar {
    height: 4px;
    border-radius: 2px;
    background: rgba(255, 255, 255, 0.08);
    overflow: hidden;
    margin-top: 0.35rem;
}

.auth-strength-fill {
    height: 100%;
    transition: width 0.25s ease, background-color 0.25s ease;
}

.auth-checklist {
    font-size: 0.8rem;
    color: #94a3b8;
    margin: 0.5rem 0 0.85rem 0;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.auth-check-item {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    transition: color 0.18s ease;
}

.auth-check-item.valid {
    color: #10b981;
    font-weight: 600;
}

.auth-switch-link {
    text-align: center;
    margin-top: 1.25rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    color: #94a3b8;
    font-size: 0.88rem;
}

@media (max-width: 880px) {
    .auth-visual-panel {
        padding: 1.25rem;
        margin-bottom: 1.25rem;
    }
    .auth-form-card {
        padding: 1.5rem 1.25rem;
    }
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #070a13;
    border-right: 1px solid rgba(255, 255, 255, 0.07);
}

/* Respect user accessibility motion settings */
@media (prefers-reduced-motion: reduce) {
    * {
        animation: none !important;
        transition: none !important;
    }
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<[^>]*?>', ' ', text)
    text = re.sub(r'http[s]?://\S+', ' ', text)
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9.,;:!?@%&\-\'\"/() ]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_text_from_file(uploaded_file) -> str:
    filename = uploaded_file.name.lower()
    raw_text = ""
    if filename.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                raw_text += t + "\n"
    elif filename.endswith(".docx") or filename.endswith(".doc"):
        if docx is None:
            raise NotImplementedError("python-docx is required for Word document parsing.")
        doc = docx.Document(uploaded_file)
        paragraphs = [p.text for p in doc.paragraphs if p.text]
        raw_text = "\n".join(paragraphs)
    elif filename.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        raw_text = df.to_string()
    else:
        raw_text = uploaded_file.read().decode("utf-8", errors="ignore")
    return raw_text.strip()

def process_cv_to_dataframe(uploaded_file, chain: Chain) -> pd.DataFrame:
    if uploaded_file.name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        if "Techstack" not in df.columns or "Links" not in df.columns:
            cols = list(df.columns)
            if len(cols) >= 2:
                df = df.rename(columns={cols[0]: "Techstack", cols[1]: "Links"})
            else:
                df["Links"] = ""
        return df

    raw_text = extract_text_from_file(uploaded_file)
    if not raw_text:
        raise ValueError("Could not extract readable text from the uploaded CV file.")
    structured_data = chain.extract_portfolio_data(raw_text)
    return pd.DataFrame(structured_data)

def get_candidate_cv_text() -> str:
    cv_path = st.session_state.get("cv_file_path")
    if cv_path and os.path.isfile(cv_path):
        try:
            with open(cv_path, "rb") as f_cv:
                return extract_text_from_file(f_cv)
        except Exception:
            return ""
    return ""

def open_in_apple_mail(recipient_email: str, subject: str, body: str, attachment_path: str | None = None, sender_email: str | None = None) -> tuple[bool, str]:
    import subprocess
    try:
        safe_subject = subject.replace('\\', '\\\\').replace('"', '\\"')
        safe_body = body.replace('\\', '\\\\').replace('"', '\\"')
        safe_recipient = recipient_email.replace('\\', '\\\\').replace('"', '\\"') if recipient_email else ""
        safe_sender = sender_email.replace('\\', '\\\\').replace('"', '\\"') if sender_email else ""
        
        script = 'tell application "Mail"\n'
        script += '    activate\n'
        props = f'subject:"{safe_subject}", content:"{safe_body}\\n\\n", visible:true'
        if safe_sender:
            props += f', sender:"{safe_sender}"'
        script += f'    set newMessage to make new outgoing message with properties {{{props}}}\n'
        script += '    tell newMessage\n'
        if safe_recipient:
            script += f'        make new to recipient at end of to recipients with properties {{address:"{safe_recipient}"}}\n'
        if attachment_path and os.path.exists(attachment_path):
            abs_path = os.path.abspath(attachment_path)
            script += f'        make new attachment with properties {{file name:(POSIX file "{abs_path}")}} at after the last paragraph\n'
        script += '    end tell\n'
        script += 'end tell'
        
        res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        if res.returncode == 0:
            return True, "Opened Apple Mail with pre-filled draft & CV attached!"
        else:
            return False, res.stderr.strip() or "Failed to open Apple Mail."
    except Exception as e:
        return False, str(e)

def build_eml_message(recipient_email: str, subject: str, body: str, cv_bytes: bytes | None = None, cv_name: str | None = None, sender_email: str | None = None) -> bytes:
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication
    
    msg = MIMEMultipart()
    if sender_email:
        msg["From"] = sender_email
    if recipient_email:
        msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    
    if cv_bytes and cv_name:
        part = MIMEApplication(cv_bytes, Name=cv_name)
        part["Content-Disposition"] = f'attachment; filename="{cv_name}"'
        msg.attach(part)
        
    return msg.as_bytes()

def get_installed_mail_clients() -> list[dict]:
    clients = []
    if sys.platform == "darwin":
        mac_apps = [
            ("apple_mail", "Apple Mail", "/System/Applications/Mail.app", "🍎"),
            ("outlook", "Microsoft Outlook", "/Applications/Microsoft Outlook.app", "🔷"),
            ("thunderbird", "Mozilla Thunderbird", "/Applications/Thunderbird.app", "🦅"),
            ("spark", "Spark Desktop", "/Applications/Spark Desktop.app", "⚡")
        ]
        for cid, label, path, icon in mac_apps:
            if os.path.exists(path):
                clients.append({"id": cid, "label": f"{icon} {label}", "name": label, "icon": icon, "path": path})
    elif sys.platform == "win32":
        win_apps = [
            ("outlook", "Microsoft Outlook", os.path.expandvars(r"%ProgramFiles%\Microsoft Office\root\Office16\OUTLOOK.EXE"), "🔷"),
            ("thunderbird", "Mozilla Thunderbird", os.path.expandvars(r"%ProgramFiles%\Mozilla Thunderbird\thunderbird.exe"), "🦅"),
        ]
        for cid, label, path, icon in win_apps:
            if os.path.exists(path):
                clients.append({"id": cid, "label": f"{icon} {label}", "name": label, "icon": icon, "path": path})

    clients.append({"id": "default", "label": "💻 System Default Mail Client", "name": "Default Mail Reader", "icon": "💻", "path": None})
    return clients

def open_in_selected_mail_client(client_id: str, recipient_email: str, subject: str, body: str, attachment_path: str | None = None, sender_email: str | None = None) -> tuple[bool, str]:
    import subprocess
    import tempfile
    
    if client_id == "apple_mail":
        return open_in_apple_mail(recipient_email, subject, body, attachment_path, sender_email)
    
    try:
        cv_bytes = None
        cv_name = None
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                cv_bytes = f.read()
            cv_name = os.path.basename(attachment_path)
            
        eml_content = build_eml_message(recipient_email, subject, body, cv_bytes, cv_name, sender_email)
        temp_eml = tempfile.NamedTemporaryFile(delete=False, suffix=".eml")
        temp_eml.write(eml_content)
        temp_eml.close()
        
        if sys.platform == "darwin":
            if client_id == "outlook" and os.path.exists("/Applications/Microsoft Outlook.app"):
                subprocess.Popen(["open", "-a", "Microsoft Outlook", temp_eml.name])
                return True, "Opened Microsoft Outlook with draft & CV attached!"
            elif client_id == "thunderbird" and os.path.exists("/Applications/Thunderbird.app"):
                subprocess.Popen(["open", "-a", "Thunderbird", temp_eml.name])
                return True, "Opened Mozilla Thunderbird with draft & CV attached!"
            else:
                subprocess.Popen(["open", temp_eml.name])
                return True, "Opened in your default email client with draft & CV attached!"
        elif sys.platform == "win32":
            os.startfile(temp_eml.name)
            return True, "Opened in your Windows mail client with draft & CV attached!"
        else:
            subprocess.Popen(["xdg-open", temp_eml.name])
            return True, "Opened in your default desktop email client!"
    except Exception as e:
        return False, str(e)

# ---------------------------------------------------------
# User Authentication Screen (Rendered if not signed in)
# ---------------------------------------------------------
if "current_user" not in st.session_state or st.session_state.current_user is None:
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "signin"

    st.markdown('<div class="auth-split-container">', unsafe_allow_html=True)
    col_visual, col_form = st.columns([1.18, 1.0], gap="large")

    with col_visual:
        auth_img_path = os.path.join(os.path.dirname(__file__), "assets", "career_auth_visual.jpg")
        if os.path.exists(auth_img_path):
            st.image(
                auth_img_path,
                use_container_width=True,
                caption="CareerLens • Resume Verification ➔ Job Match Radar ➔ Tailored Application Email"
            )
        else:
            st.markdown("""
            <div class="welcome-banner" style="padding: 2.5rem 2rem;">
                <div class="welcome-title">CareerLens Platform</div>
                <div class="welcome-desc">
                    Compare your verified profile with real job descriptions, discover genuine skill gaps, and create persuasive application emails.
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_form:
        st.markdown('<div class="auth-form-card">', unsafe_allow_html=True)
        
        # Product Brand Header
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.65rem; margin-bottom: 0.75rem;">
            <div style="width: 34px; height: 34px; background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%); border-radius: 9px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.05rem; color: white;">
                CL
            </div>
            <div style="font-family: 'Outfit', sans-serif; font-size: 1.3rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em;">
                CareerLens
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.auth_mode == "signin":
            st.markdown("""
            <div class="auth-title">Welcome back</div>
            <div class="auth-subtitle">Sign in to continue preparing your next application.</div>
            """, unsafe_allow_html=True)

            with st.form("signin_form", clear_on_submit=False):
                login_username = st.text_input(
                    "Email or Username",
                    placeholder="name@example.com",
                    key="signin_user_input"
                )
                
                show_login_pwd = st.checkbox("Show password", key="chk_show_login_pwd")
                login_password = st.text_input(
                    "Password",
                    type="default" if show_login_pwd else "password",
                    placeholder="Enter your password",
                    key="signin_pwd_input"
                )

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                submit_signin = st.form_submit_button("Sign In ➔", type="primary", use_container_width=True)

                if submit_signin:
                    if not login_username.strip() or not login_password:
                        st.error("Please enter your email or username and password.")
                    else:
                        with st.spinner("Signing in..."):
                            success, message, user = tracker.authenticate_user(login_username, login_password)
                            if success and user:
                                st.session_state.current_user = user
                                st.session_state.profile_loaded = False
                                st.session_state.current_page = "dashboard"
                                st.toast("Signed in successfully. Welcome back!", icon="👋")
                                st.rerun()
                            else:
                                st.error("We couldn't sign you in with those details. Check your email and password and try again.")

            st.markdown('<div class="auth-switch-link">New here?</div>', unsafe_allow_html=True)
            if st.button("Create an account →", key="switch_to_signup_btn", use_container_width=True):
                st.session_state.auth_mode = "signup"
                st.rerun()

        else:
            st.markdown("""
            <div class="auth-title">Create your account</div>
            <div class="auth-subtitle">Build your profile and start comparing it with opportunities.</div>
            """, unsafe_allow_html=True)

            with st.form("signup_form", clear_on_submit=False):
                reg_username = st.text_input(
                    "Full Name or Username",
                    placeholder="e.g. Alex Rivera",
                    key="signup_user_input"
                )
                reg_email = st.text_input(
                    "Email Address",
                    placeholder="e.g. alex@example.com",
                    key="signup_email_input"
                )

                show_reg_pwd = st.checkbox("Show password", key="chk_show_reg_pwd")
                reg_password = st.text_input(
                    "Password (min 6 characters)",
                    type="default" if show_reg_pwd else "password",
                    placeholder="Create a secure password",
                    key="signup_pwd_input"
                )
                reg_confirm = st.text_input(
                    "Confirm Password",
                    type="default" if show_reg_pwd else "password",
                    placeholder="Re-enter your password",
                    key="signup_confirm_input"
                )

                # Real backend requirements checklist & strength feedback
                pwd_val = reg_password or ""
                has_len = len(pwd_val) >= 6
                has_upper = any(c.isupper() for c in pwd_val)
                has_digit = any(c.isdigit() for c in pwd_val)
                
                # Calculate subtle strength
                score = 0
                if len(pwd_val) >= 6: score += 1
                if len(pwd_val) >= 8: score += 1
                if has_upper: score += 1
                if has_digit: score += 1
                
                if score <= 1:
                    strength_label, strength_color, strength_pct = "Basic", "#ef4444", 25
                elif score <= 2:
                    strength_label, strength_color, strength_pct = "Moderate", "#f59e0b", 60
                else:
                    strength_label, strength_color, strength_pct = "Strong", "#10b981", 100

                if pwd_val:
                    st.markdown(f"""
                    <div class="auth-strength-container">
                        <div style="display: flex; justify-content: space-between; font-size: 0.74rem; color: #94a3b8; font-weight: 600;">
                            <span>Password Strength</span>
                            <span style="color: {strength_color};">{strength_label}</span>
                        </div>
                        <div class="auth-strength-bar">
                            <div class="auth-strength-fill" style="width: {strength_pct}%; background-color: {strength_color};"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="auth-checklist">
                    <div class="auth-check-item {'valid' if has_len else ''}">
                        {'✓' if has_len else '○'} At least 6 characters
                    </div>
                    <div class="auth-check-item {'valid' if has_upper else ''}">
                        {'✓' if has_upper else '○'} Uppercase letter (recommended)
                    </div>
                    <div class="auth-check-item {'valid' if has_digit else ''}">
                        {'✓' if has_digit else '○'} Number (recommended)
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                submit_signup = st.form_submit_button("Create Account ➔", type="primary", use_container_width=True)

                if submit_signup:
                    u_clean = reg_username.strip()
                    e_clean = reg_email.strip().lower()
                    p_clean = reg_password

                    if not u_clean or not e_clean or not p_clean:
                        st.error("Please fill in all required fields.")
                    elif len(u_clean) < 3:
                        st.error("Username or name must be at least 3 characters long.")
                    elif "@" not in e_clean or "." not in e_clean:
                        st.error("Please provide a valid email address.")
                    elif len(p_clean) < 6:
                        st.error("Password must be at least 6 characters long.")
                    elif p_clean != reg_confirm:
                        st.error("Passwords do not match yet. Please verify and try again.")
                    else:
                        with st.spinner("Creating account..."):
                            success, message, user = tracker.register_user(u_clean, e_clean, p_clean)
                            if success and user:
                                st.session_state.current_user = user
                                st.session_state.profile_loaded = False
                                st.session_state.current_page = "profile"  # Seamless onboarding bridge!
                                st.toast("Account created! Let's set up your profile and upload your CV.", icon="🎉")
                                st.rerun()
                            else:
                                st.error(message)

            st.markdown('<div class="auth-switch-link">Already have an account?</div>', unsafe_allow_html=True)
            if st.button("Sign in to your account →", key="switch_to_signin_btn", use_container_width=True):
                st.session_state.auth_mode = "signin"
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ---------------------------------------------------------
# Authenticated User Workspace Initialization
# ---------------------------------------------------------
current_user = st.session_state.current_user
user_id = current_user["id"]

if not st.session_state.get("profile_loaded"):
    user_prof = tracker.get_user_profile(user_id)
    st.session_state.user_name = user_prof.get("full_name") or current_user.get("username", "").capitalize()
    st.session_state.user_position = user_prof.get("position") or ""
    st.session_state.user_college = user_prof.get("college") or ""
    st.session_state.user_study = user_prof.get("degree") or ""
    st.session_state.candidate_type = user_prof.get("candidate_type") or "Student / Recent Graduate"
    st.session_state.custom_notes = user_prof.get("custom_notes") or ""

    if user_prof.get("portfolio"):
        st.session_state.portfolio_df = pd.DataFrame(user_prof["portfolio"])
    else:
        st.session_state.portfolio_df = None

    st.session_state.cv_filename = user_prof.get("cv_filename") or None
    st.session_state.cv_file_path = user_prof.get("cv_file_path") or None
    st.session_state.cv_file_bytes = None
    if st.session_state.cv_file_path and os.path.exists(st.session_state.cv_file_path):
        try:
            with open(st.session_state.cv_file_path, "rb") as f:
                st.session_state.cv_file_bytes = f.read()
        except Exception:
            pass

    st.session_state.job_input_mode = "Paste Job Description"
    st.session_state.job_url = ""
    st.session_state.job_text = ""
    st.session_state.recipient_email = ""
    st.session_state.generated_results = None
    st.session_state.fit_analysis_result = None
    st.session_state.current_page = "dashboard"
    st.session_state.profile_loaded = True

def save_current_user_profile():
    p_data = st.session_state.portfolio_df.to_dict("records") if st.session_state.portfolio_df is not None and not st.session_state.portfolio_df.empty else []
    tracker.save_user_profile(
        user_id=user_id,
        full_name=st.session_state.user_name,
        position=st.session_state.user_position,
        college=st.session_state.user_college,
        degree=st.session_state.user_study,
        candidate_type=st.session_state.candidate_type,
        custom_notes=st.session_state.custom_notes,
        portfolio=p_data,
        cv_filename=st.session_state.cv_filename or "",
        cv_file_path=st.session_state.cv_file_path or ""
    )

def get_current_job_text() -> tuple[str, str | None]:
    if st.session_state.job_input_mode == "Paste Job Description":
        text = st.session_state.get("job_text", "").strip()
        if not text:
            return "", "Please paste the job description text first."
        return text, None
    else:
        url = st.session_state.get("job_url", "").strip()
        if not url:
            return "", "Please enter a valid job posting URL."
        try:
            loader = WebBaseLoader([url])
            docs = loader.load()
            if not docs or not docs[0].page_content.strip():
                return "", "Could not extract text from the provided URL. Please try pasting the job description directly."
            return clean_text(docs[0].page_content), None
        except Exception as e:
            return "", f"Scraping error: {str(e)}. Please paste the job description directly."

# ---------------------------------------------------------
# Sidebar Navigation & Settings
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="padding: 0.5rem 0 1rem 0;">
        <div style="font-size: 1.25rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em; display: flex; align-items: center; gap: 0.5rem;">
            💼 CareerLens
        </div>
        <div style="font-size: 0.78rem; color: #94a3b8;">Job Fit & Application Studio</div>
    </div>
    """, unsafe_allow_html=True)

    # Candidate Profile Snippet
    user_initials = "".join([part[0].upper() for part in st.session_state.user_name.split() if part])[:2] or "CA"
    cv_status_text = f"Attached ({st.session_state.cv_filename})" if st.session_state.cv_filename else "Not uploaded"
    cv_status_color = "#10b981" if st.session_state.cv_filename else "#f59e0b"

    st.markdown(f"""
    <div style="background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 12px; padding: 0.85rem; margin-bottom: 1.25rem;">
        <div style="display: flex; align-items: center; gap: 0.65rem;">
            <div style="width: 36px; height: 36px; border-radius: 8px; background: #4f46e5; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.95rem;">
                {user_initials}
            </div>
            <div style="flex: 1; min-width: 0;">
                <div style="font-size: 0.92rem; font-weight: 700; color: #f8fafc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    {st.session_state.user_name}
                </div>
                <div style="font-size: 0.76rem; color: #94a3b8;">
                    CV: <span style="color: {cv_status_color}; font-weight: 600;">{cv_status_text}</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Navigation")
    
    # Navigation options mapped to keys
    nav_map = {
        "dashboard": "🏠 Dashboard",
        "profile": "👤 Profile / CV",
        "analyze": "🎯 Analyze Job",
        "audit": "📊 Match & Gap Audit",
        "email": "✉️ Application Email"
    }

    current_idx = list(nav_map.keys()).index(st.session_state.get("current_page", "dashboard")) if st.session_state.get("current_page") in nav_map else 0

    selected_nav_label = st.radio(
        "Go to page:",
        options=list(nav_map.values()),
        index=current_idx,
        label_visibility="collapsed"
    )

    # Synchronize selected navigation page
    for k, v in nav_map.items():
        if v == selected_nav_label:
            st.session_state.current_page = k
            break

    st.markdown("<hr style='margin: 1.25rem 0; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

    # Clean Configuration Expander
    with st.expander("⚙️ Preferences & Tone", expanded=False):
        api_key = os.getenv("API_KEY") or os.getenv("GROQ_API_KEY")
        selected_model = st.selectbox(
            "Model:",
            options=[
                "openai/gpt-oss-120b",
                "openai/gpt-oss-20b",
                "qwen/qwen3.8-27b",
                "groq/compound-mini",
                "groq/compound",
                "qwen/qwen3.6-27b"
            ],
            index=0,
            help="Language model used for requirement extraction and outreach drafting."
        )
        selected_tone = st.selectbox(
            "Outreach Tone:",
            options=[
                "Professional & Persuasive (Recommended)",
                "Enthusiastic & Academic",
                "Casual & Startup-Friendly",
                "Confident Executive",
                "Short & Direct / No Fluff"
            ],
            index=0
        )
        selected_length = st.selectbox(
            "Email Length:",
            options=[
                "Standard (120-180 words)",
                "Concise & Punchy (under 120 words)",
                "Comprehensive (200+ words)"
            ],
            index=0
        )

    col_save, col_clear = st.columns(2)
    with col_save:
        if st.button("💾 Save", use_container_width=True, help="Saves your current profile and settings"):
            save_current_user_profile()
            st.toast("Profile saved successfully.", icon="✅")
    with col_clear:
        if st.button("🔄 Reset", use_container_width=True, help="Clears analyzed job and drafts"):
            for k in ["job_text", "job_url", "recipient_email", "generated_results", "fit_analysis_result"]:
                if k in st.session_state:
                    st.session_state[k] = "" if "text" in k or "url" in k or "email" in k else None
            st.session_state.current_page = "analyze"
            st.rerun()

    st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.current_user = None
        st.session_state.profile_loaded = False
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Initialize Chain instance
try:
    chain = Chain(model_name=selected_model, api_key=api_key)
except Exception as e:
    st.error(f"Error initializing analysis engine: {e}")
    chain = None

# =========================================================
# VIEW 1: DASHBOARD
# =========================================================
if st.session_state.current_page == "dashboard":
    st.markdown("""
    <div class="welcome-banner">
        <div class="welcome-title">See how well your profile fits your next opportunity.</div>
        <div class="welcome-desc">
            Compare target job descriptions with your profile, identify critical skill gaps, and generate tailored, credible outreach emails.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Real Status Summary Cards (Strictly genuine data, no fake stats)
    has_cv = bool(st.session_state.cv_filename)
    has_skills = st.session_state.portfolio_df is not None and not st.session_state.portfolio_df.empty
    skills_count = len(st.session_state.portfolio_df) if has_skills else 0
    has_analysis = st.session_state.fit_analysis_result is not None
    target_role_text = st.session_state.fit_analysis_result["job"].get("role", "Ready to analyze") if has_analysis else "None yet"
    target_company_text = st.session_state.fit_analysis_result["job"].get("company", "") if has_analysis else "Paste a job to begin"

    st.markdown(f"""
    <div class="status-grid">
        <div class="status-tile">
            <div class="tile-label">Candidate Profile</div>
            <div class="tile-value">{st.session_state.user_name}</div>
            <div class="tile-sub">{st.session_state.user_position or 'Role unassigned'} • {st.session_state.candidate_type}</div>
        </div>
        <div class="status-tile">
            <div class="tile-label">Resume / CV Status</div>
            <div class="tile-value">{'✓ ' + st.session_state.cv_filename if has_cv else '○ Pending Upload'}</div>
            <div class="tile-sub">{f'{skills_count} verified projects/skills indexed' if has_skills else 'Upload CV to extract skills'}</div>
        </div>
        <div class="status-tile">
            <div class="tile-label">Active Job Analysis</div>
            <div class="tile-value">{target_role_text}</div>
            <div class="tile-sub">{target_company_text}</div>
        </div>
        <div class="status-tile">
            <div class="tile-label">Match Score Status</div>
            <div class="tile-value">{str(st.session_state.fit_analysis_result['analysis'].get('match_score', 0)) + '%' if has_analysis else 'Not Analyzed'}</div>
            <div class="tile-sub">{st.session_state.fit_analysis_result['analysis'].get('fit_level', 'Run analysis to view') if has_analysis else 'Compare against a job'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Workflow Road-map Stepper
    st.markdown("""
    <div class="workflow-stepper">
        <div class="step-item completed">
            <div class="step-badge">1</div>
            <span>Profile & CV</span>
        </div>
        <span class="step-arrow">➔</span>
        <div class="step-item active">
            <div class="step-badge">2</div>
            <span>Job Description</span>
        </div>
        <span class="step-arrow">➔</span>
        <div class="step-item">
            <div class="step-badge">3</div>
            <span>Match & Gap Audit</span>
        </div>
        <span class="step-arrow">➔</span>
        <div class="step-item">
            <div class="step-badge">4</div>
            <span>Application Email</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Primary Action CTAs
    col_cta1, col_cta2 = st.columns([1.5, 1])
    with col_cta1:
        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        st.markdown("### Ready to evaluate a role?")
        st.markdown("Paste any job description to deconstruct its must-have requirements, calculate your weighted fit score, and highlight verified evidence.")
        if st.button("🎯 Analyze a Target Job ➔", type="primary", use_container_width=True):
            st.session_state.current_page = "analyze"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_cta2:
        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        st.markdown("### Profile & CV")
        st.markdown("Ensure your candidate background, projects, and degree are up-to-date so evidence matches accurately.")
        if st.button("👤 View / Update Profile", use_container_width=True):
            st.session_state.current_page = "profile"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# VIEW 2: PROFILE / CV
# =========================================================
elif st.session_state.current_page == "profile":
    st.markdown('<div class="career-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">👤 Candidate Profile & CV Vault</div>', unsafe_allow_html=True)

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.session_state.user_name = st.text_input("Full Name *", value=st.session_state.user_name, placeholder="e.g. Jane Doe")
        st.session_state.user_position = st.text_input("Current / Target Job Title", value=st.session_state.user_position, placeholder="e.g. Software Engineer, Data Scientist")
        st.session_state.candidate_type = st.selectbox(
            "Experience Level / Category",
            options=["Student / Recent Graduate", "Experienced Professional", "Career Switcher", "Freelancer / Consultant"],
            index=["Student / Recent Graduate", "Experienced Professional", "Career Switcher", "Freelancer / Consultant"].index(st.session_state.candidate_type) if st.session_state.candidate_type in ["Student / Recent Graduate", "Experienced Professional", "Career Switcher", "Freelancer / Consultant"] else 0
        )
    with col_p2:
        st.session_state.user_college = st.text_input("University / College", value=st.session_state.user_college, placeholder="e.g. Stanford University")
        st.session_state.user_study = st.text_input("Degree / Major", value=st.session_state.user_study, placeholder="e.g. B.S. in Computer Science")
        st.session_state.custom_notes = st.text_input("Key Accomplishments / Focus Areas", value=st.session_state.custom_notes, placeholder="e.g. Distributed backend systems, open-source contributor")

    st.markdown("<hr style='margin: 1.25rem 0; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

    # Polished CV Upload Area
    st.markdown("#### 📄 Upload Your Resume / CV")
    st.caption("Upload your CV in PDF or DOCX format. Your verified technical skills and project citations will be extracted automatically.")

    uploaded_file = st.file_uploader("Select CV file", type=["pdf", "docx", "csv"], label_visibility="collapsed")
    if uploaded_file is not None:
        save_path = os.path.join(UPLOAD_DIR, f"{user_id}_{uploaded_file.name}")
        with open(save_path, "wb") as f_out:
            f_out.write(uploaded_file.getbuffer())

        st.session_state.cv_filename = uploaded_file.name
        st.session_state.cv_file_path = save_path
        st.session_state.cv_file_bytes = uploaded_file.getvalue()

        with st.spinner("Processing CV and indexing your projects..."):
            try:
                extracted_df = process_cv_to_dataframe(uploaded_file, chain)
                st.session_state.portfolio_df = extracted_df
                save_current_user_profile()
                st.toast("CV processed and saved to memory.", icon="✅")
            except Exception as e:
                st.error(f"Could not parse file: {e}")

    if st.session_state.cv_filename:
        col_cv_stat1, col_cv_stat2 = st.columns([1.6, 1])
        with col_cv_stat1:
            st.markdown(f'<div class="status-tile"><div class="tile-label">Active CV File</div><div class="tile-value">📎 {st.session_state.cv_filename}</div><div class="tile-sub">Ready to attach in desktop email clients.</div></div>', unsafe_allow_html=True)
        with col_cv_stat2:
            st.markdown("<div style='margin-top: 0.5rem;'>", unsafe_allow_html=True)
            if st.button("🪄 Auto-Fill Details from CV", use_container_width=True, help="Extracts name, title, degree, and skills from your uploaded file"):
                if st.session_state.cv_file_path and os.path.isfile(st.session_state.cv_file_path):
                    with st.spinner("Extracting profile details..."):
                        with open(st.session_state.cv_file_path, "rb") as f_cv:
                            cv_raw_text = extract_text_from_file(f_cv)
                        if cv_raw_text:
                            p_info = chain.parse_candidate_profile_from_cv(cv_raw_text)
                            if p_info.get("full_name") and p_info["full_name"] != "Candidate":
                                st.session_state.user_name = p_info["full_name"]
                            if p_info.get("position"):
                                st.session_state.user_position = p_info["position"]
                            if p_info.get("college"):
                                st.session_state.user_college = p_info["college"]
                            if p_info.get("degree"):
                                st.session_state.user_study = p_info["degree"]
                            if p_info.get("candidate_type"):
                                st.session_state.candidate_type = p_info["candidate_type"]
                            if p_info.get("portfolio"):
                                st.session_state.portfolio_df = pd.DataFrame(p_info["portfolio"])
                            save_current_user_profile()
                            st.toast("Profile details updated from CV.", icon="🪄")
                            st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 💼 Verified Technical Skills & Project Links")
    st.caption("These items provide verified evidence when matching against job postings and tailoring email citations.")

    if st.session_state.portfolio_df is not None and not st.session_state.portfolio_df.empty:
        edited_df = st.data_editor(
            st.session_state.portfolio_df,
            num_rows="dynamic",
            use_container_width=True,
            key="portfolio_editor"
        )
        st.session_state.portfolio_df = edited_df
    else:
        st.info("Upload your resume above to automatically index your skills and projects.")

    if st.button("💾 Save Profile Changes", type="primary"):
        save_current_user_profile()
        st.toast("Profile saved successfully.", icon="✅")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# VIEW 3: ANALYZE JOB
# =========================================================
elif st.session_state.current_page == "analyze":
    st.markdown('<div class="career-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🎯 Analyze a Job Description</div>', unsafe_allow_html=True)
    st.markdown("Paste a job description to extract its core requirements, identify skill alignment, and detect genuine skill gaps.")

    mode_choice = st.radio(
        "Input Format:",
        options=["Paste Job Description", "Import from Job URL"],
        index=0 if st.session_state.job_input_mode == "Paste Job Description" else 1,
        horizontal=True
    )
    st.session_state.job_input_mode = mode_choice

    if mode_choice == "Paste Job Description":
        st.session_state.job_text = st.text_area(
            "Job Description Text *",
            value=st.session_state.job_text,
            height=280,
            placeholder="Paste the full job posting here (responsibilities, required qualifications, nice-to-haves)..."
        )
    else:
        st.session_state.job_url = st.text_input(
            "Target Job Posting URL *",
            value=st.session_state.job_url,
            placeholder="https://jobs.lever.co/company/role-id or https://boards.greenhouse.io/..."
        )

    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        target_role_hint = st.text_input("Job Title (Optional — auto-detected if blank):", placeholder="e.g. Backend Software Engineer")
    with col_opt2:
        target_comp_hint = st.text_input("Company Name (Optional — auto-detected if blank):", placeholder="e.g. Stripe, OpenAI")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Analyze Job ➔", type="primary", use_container_width=True):
        if not st.session_state.user_name.strip():
            st.error("Please enter your name in the Profile tab first.")
        elif not api_key:
            st.error("Missing API key. Please check your .env configuration.")
        else:
            job_raw_text, err = get_current_job_text()
            if err:
                st.error(err)
            else:
                progress_placeholder = st.empty()
                progress_placeholder.info("Reading job description...")

                try:
                    jobs = chain.extract_jobs(job_raw_text)
                    target_job = jobs[0] if jobs else {"role": target_role_hint or "Target Role", "skills": []}
                    if target_role_hint:
                        target_job["role"] = target_role_hint
                    if target_comp_hint:
                        target_job["company"] = target_comp_hint

                    progress_placeholder.info("Comparing requirements against your profile and CV evidence...")

                    portfolio_str = ""
                    if st.session_state.portfolio_df is not None and not st.session_state.portfolio_df.empty:
                        for _, row in st.session_state.portfolio_df.iterrows():
                            portfolio_str += f"- Tech: {row.get('Techstack', '')} | Project: {row.get('Links', '')}\n"

                    cv_text = get_candidate_cv_text()

                    analysis = chain.analyze_job_fit(
                        job=target_job,
                        portfolio_summary=portfolio_str,
                        user_name=st.session_state.user_name,
                        user_position=st.session_state.user_position,
                        user_study=st.session_state.user_study,
                        candidate_type=st.session_state.candidate_type,
                        cv_text=cv_text
                    )

                    st.session_state.fit_analysis_result = {
                        "job": target_job,
                        "analysis": analysis
                    }

                    progress_placeholder.empty()
                    st.toast("Analysis complete!", icon="✅")
                    st.session_state.current_page = "audit"
                    st.rerun()

                except Exception as e:
                    progress_placeholder.empty()
                    st.error(f"Analysis could not be completed: {str(e)}. Please check the job description and try again.")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# VIEW 4: MATCH & GAP AUDIT
# =========================================================
elif st.session_state.current_page == "audit":
    if not st.session_state.fit_analysis_result:
        st.markdown('<div class="career-card" style="text-align: center; padding: 3rem 2rem;">', unsafe_allow_html=True)
        st.markdown("### No Job Analyzed Yet")
        st.markdown("Paste a job description to view your verified match score, skill breakdown, and gap analysis.")
        if st.button("Go to Job Analysis ➔", type="primary"):
            st.session_state.current_page = "analyze"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        res = st.session_state.fit_analysis_result["analysis"]
        target_job = st.session_state.fit_analysis_result["job"]
        score = res.get("match_score", 75)
        fit_level = res.get("fit_level", "Strong Match")
        strengths = res.get("matched_strengths", [])
        gaps = res.get("skill_gaps", [])
        advice = res.get("strategic_advice", "")
        evidence_breakdown = res.get("evidence_breakdown", [])
        noise_filtered = res.get("noise_filtered", [])
        audit_meta = res.get("audit_meta", {})

        score_color = "#10b981" if score >= 80 else ("#f59e0b" if score >= 65 else "#64748b")

        # Top Header Summary
        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        col_res1, col_res2 = st.columns([1, 2.2])

        with col_res1:
            st.markdown(f"""
            <div class="score-hero-card">
                <div class="score-display" style="color: {score_color};">{score}%</div>
                <div class="score-label-badge" style="background: {score_color}1a; color: {score_color}; border: 1px solid {score_color}40;">
                    {fit_level}
                </div>
                <div style="font-size: 0.78rem; color: #64748b; margin-top: 0.5rem;">Weighted Evidence Alignment</div>
            </div>
            """, unsafe_allow_html=True)

        with col_res2:
            st.markdown(f"## {target_job.get('role', 'Target Role')}")
            st.markdown(f"**Company:** {target_job.get('company', 'Target Company')}")
            domain_val = target_job.get("domain", "Technology")
            focus_items = target_job.get("key_focus_areas", [])
            focus_str = " • ".join(focus_items) if focus_items else "Core Engineering"
            
            st.markdown(f"""
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem;">
                <span class="skill-chip matched">🏷️ {domain_val}</span>
                <span class="skill-chip partial">🎯 Focus: {focus_str}</span>
            </div>
            """, unsafe_allow_html=True)

            if st.button("✉️ Draft Application Email for this Role ➔", type="primary"):
                st.session_state.current_page = "email"
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # 3 Distinct Skill Sections
        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        col_sk1, col_sk2 = st.columns(2)

        with col_sk1:
            st.markdown("#### ✓ Matched Skills")
            st.caption("Requirements verified with concrete evidence in your profile/CV.")
            if strengths:
                for s in strengths:
                    st.markdown(f'<span class="skill-chip matched">✓ {s}</span>', unsafe_allow_html=True)
            else:
                st.info("Found foundational alignment.")

        with col_sk2:
            st.markdown("#### ○ Skills to Develop")
            st.caption("Important requirements not found in your current profile.")
            if gaps:
                for g in gaps:
                    st.markdown(f'<span class="skill-chip gap">○ {g}</span>', unsafe_allow_html=True)
            else:
                st.success("No critical gaps identified for this role.")

        # Partial Matches Section
        partial_items = [e for e in evidence_breakdown if "PARTIAL" in str(e.get("status", "")).upper()]
        if partial_items:
            st.markdown("<hr style='margin: 1.25rem 0; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
            st.markdown("#### ◐ Partial Matches & Scope Differences")
            st.caption("Related foundation found, but lacking specific production scale or depth demanded by this posting.")
            for p in partial_items:
                req_title = p.get("requirement", "")
                expl = p.get("explanation", "")
                st.markdown(f'<span class="skill-chip partial">◐ {req_title}</span> <span style="font-size: 0.85rem; color: #94a3b8; margin-left: 0.5rem;">— {expl}</span>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Requirement Breakdown Audit Table
        if evidence_breakdown:
            st.markdown('<div class="career-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">📋 Requirement Comparison Breakdown</div>', unsafe_allow_html=True)
            st.caption("Item-by-item verification showing exact evidence extracted from your CV.")

            for ev in evidence_breakdown:
                req = ev.get("requirement", "")
                imp = ev.get("importance", "Core requirement")
                status = str(ev.get("status", "MISSING")).upper()
                cand_ev = ev.get("candidate_evidence", "")
                expl = ev.get("explanation", "")

                is_match = "MATCHED" in status and "PARTIAL" not in status
                is_part = "PARTIAL" in status
                is_noise = "NOT RELEVANT" in status

                stat_badge = "✓ Matched" if is_match else ("◐ Partial" if is_part else ("— Excluded Noise" if is_noise else "○ Not Found"))
                badge_class = "matched" if is_match else ("partial" if is_part else "gap")

                st.markdown(f"""
                <div class="audit-row">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                        <span style="font-weight: 700; color: #f8fafc; font-size: 0.94rem;">{req}</span>
                        <span class="skill-chip {badge_class}" style="margin: 0; padding: 0.2rem 0.6rem; font-size: 0.76rem;">{stat_badge} ({imp})</span>
                    </div>
                    <div style="font-size: 0.84rem; color: #94a3b8;">
                        <b style="color: #cbd5e1;">Profile Evidence:</b> {cand_ev if cand_ev else "No direct evidence found in uploaded resume"}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        # "Why this match score?" (Mathematical breakdown)
        if audit_meta:
            with st.expander("Why this match score?", expanded=False):
                c_acc = audit_meta.get("critical_accuracy", {})
                p_acc = audit_meta.get("preferred_accuracy", {})
                s_acc = audit_meta.get("soft_accuracy", {})
                formula_str = audit_meta.get("formula", "")

                st.markdown(f"""
                <div style="padding: 0.5rem 0;">
                    <p style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.6;">
                        Your match score is calculated using weighted mathematical scoring based on verified evidence in your profile:
                    </p>
                    <ul style="font-size: 0.86rem; color: #94a3b8; line-height: 1.8;">
                        <li><b>Critical Core Requirements (65% Weight):</b> {c_acc.get('percentage', 0)}% satisfied ({c_acc.get('matched', 0)} of {c_acc.get('total', 0)} verified)</li>
                        <li><b>Preferred Requirements (25% Weight):</b> {p_acc.get('percentage', 0)}% satisfied ({p_acc.get('matched', 0)} of {p_acc.get('total', 0)} verified)</li>
                        <li><b>Soft / Collaborative Skills (10% Weight):</b> {s_acc.get('percentage', 0)}% satisfied ({s_acc.get('matched', 0)} of {s_acc.get('total', 0)} verified)</li>
                    </ul>
                    <div style="font-family: monospace; font-size: 0.8rem; background: rgba(0,0,0,0.3); padding: 0.5rem 0.85rem; border-radius: 8px; color: #818cf8;">
                        Audit Calculation: {formula_str} = {score}%
                    </div>
                </div>
                """, unsafe_allow_html=True)

        if advice:
            st.markdown(f"""
            <div class="career-card" style="border-left: 4px solid #4f46e5;">
                <div style="font-weight: 700; color: #f8fafc; font-size: 0.95rem; margin-bottom: 0.35rem;">💡 Application & Interview Advice</div>
                <div style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.6;">{advice}</div>
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# VIEW 5: PERSONALIZED EMAIL COMPOSER
# =========================================================
elif st.session_state.current_page == "email":
    if not st.session_state.fit_analysis_result:
        st.markdown('<div class="career-card" style="text-align: center; padding: 3rem 2rem;">', unsafe_allow_html=True)
        st.markdown("### Analyze a Job First")
        st.markdown("Analyze a target job posting before generating an email so it can be personalized with verified evidence.")
        if st.button("Go to Job Analysis ➔", type="primary"):
            st.session_state.current_page = "analyze"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        target_job = st.session_state.fit_analysis_result["job"]
        role_title = target_job.get("role", "Target Position")
        company_name = target_job.get("company", "Company")

        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        col_gen1, col_gen2 = st.columns([1.6, 1])
        with col_gen1:
            st.markdown(f"### Application Email for **{role_title}** at **{company_name}**")
            st.caption("Crafted using your verified projects, genuine accomplishments, and anti-cliché phrasing.")
        with col_gen2:
            st.markdown("<div style='margin-top: 0.4rem;'>", unsafe_allow_html=True)
            draft_clicked = st.button("✉️ Draft / Regenerate Email", type="primary", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        if draft_clicked or not st.session_state.generated_results:
            with st.spinner("Drafting personalized application email..."):
                try:
                    portfolio_instance = Portfolio(data=st.session_state.portfolio_df) if st.session_state.portfolio_df is not None else None
                    if portfolio_instance:
                        portfolio_instance.load_portfolio(clear_existing=True)

                    skills = target_job.get("skills", [])
                    matched_links = portfolio_instance.query_links(skills, n_results=3) if portfolio_instance else []
                    cv_text = get_candidate_cv_text()

                    email_result = chain.write_mail(
                        job=target_job,
                        links=matched_links,
                        user_name=st.session_state.user_name,
                        user_college=st.session_state.user_college,
                        user_study=st.session_state.user_study,
                        user_position=st.session_state.user_position,
                        tone=selected_tone,
                        length=selected_length,
                        candidate_type=st.session_state.candidate_type,
                        custom_instructions=st.session_state.custom_notes,
                        cv_text=cv_text
                    )

                    st.session_state.generated_results = [{
                        "job": target_job,
                        "matched_links": matched_links,
                        "email_data": email_result
                    }]
                    if not st.session_state.recipient_email and target_job.get("contact_email"):
                        st.session_state.recipient_email = target_job.get("contact_email")

                    st.toast("Email drafted successfully.", icon="✅")
                except Exception as e:
                    st.error(f"Could not draft email: {e}")

        if st.session_state.generated_results:
            item = st.session_state.generated_results[0]
            email_data = item["email_data"]
            subject_lines = email_data.get("subject_lines", [f"Application for {role_title} - {st.session_state.user_name}"])
            email_body = email_data.get("body", "")

            st.markdown("#### Subject Line Options")
            chosen_subject = st.radio(
                "Choose preferred subject line:",
                options=subject_lines,
                index=0,
                label_visibility="collapsed"
            )

            # Email Composer Window
            word_count = len(email_body.split())
            read_time = max(1, round(word_count / 150 * 60))

            view_mode = st.radio("Editor View:", ["Formatted Preview", "Text Editor"], horizontal=True)

            if view_mode == "Formatted Preview":
                st.markdown(f"""
                <div class="email-composer-frame">
                    <div class="composer-toolbar">
                        <div class="composer-dots">
                            <span class="composer-dot red"></span>
                            <span class="composer-dot yellow"></span>
                            <span class="composer-dot green"></span>
                        </div>
                        <div style="font-size: 0.78rem; color: #94a3b8; font-weight: 600;">
                            {word_count} words (~{read_time}s read)
                        </div>
                    </div>
                    <div class="composer-headers">
                        <div class="composer-row">
                            <span class="composer-field-label">To:</span>
                            <span class="composer-field-value">{st.session_state.recipient_email or 'Hiring Team / Recruiter'}</span>
                        </div>
                        <div class="composer-row">
                            <span class="composer-field-label">Subject:</span>
                            <span class="composer-field-value" style="font-weight: 700; color: #f8fafc;">{chosen_subject}</span>
                        </div>
                    </div>
                    <div class="composer-body">{email_body}</div>
                </div>
                """, unsafe_allow_html=True)
                final_email_content = email_body
            else:
                final_email_content = st.text_area(
                    "Edit email content:",
                    value=email_body,
                    height=280
                )

            # Quick Refinement Actions
            col_ref1, col_ref2, col_ref3, col_ref4 = st.columns(4)
            with col_ref1:
                if st.button("✂️ Make Shorter", use_container_width=True):
                    with st.spinner("Shortening email..."):
                        res = chain.write_mail(job=target_job, links=item["matched_links"], user_name=st.session_state.user_name, tone=selected_tone, length="Concise & Punchy (under 120 words)", custom_instructions="Make it concise, direct, under 110 words.")
                        st.session_state.generated_results[0]["email_data"] = res
                        st.rerun()
            with col_ref2:
                if st.button("👔 More Professional", use_container_width=True):
                    with st.spinner("Adjusting tone..."):
                        res = chain.write_mail(job=target_job, links=item["matched_links"], user_name=st.session_state.user_name, tone="Professional & Persuasive", custom_instructions="Professional executive tone with clean value proposition.")
                        st.session_state.generated_results[0]["email_data"] = res
                        st.rerun()
            with col_ref3:
                if st.button("💬 More Natural", use_container_width=True):
                    with st.spinner("Adjusting tone..."):
                        res = chain.write_mail(job=target_job, links=item["matched_links"], user_name=st.session_state.user_name, tone="Casual & Startup-Friendly", custom_instructions="Conversational, natural phrasing, low friction.")
                        st.session_state.generated_results[0]["email_data"] = res
                        st.rerun()
            with col_ref4:
                copy_js = f"navigator.clipboard.writeText(`Subject: {chosen_subject}\\n\\n{final_email_content}`);"
                if st.button("📋 Copy Email", use_container_width=True):
                    st.toast("Email copied to clipboard!", icon="📋")

            # "Personalized using" Evidence Citations
            highlights = email_data.get("key_highlights_used", []) or target_job.get("critical_requirements", [])[:2]
            focus_used = email_data.get("focus_areas_addressed", "")
            if highlights:
                st.markdown("<div style='margin-top: 1rem; padding: 0.75rem 1rem; background: rgba(255,255,255,0.03); border-radius: 10px; border: 1px solid rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
                st.markdown(f"<span style='font-size: 0.78rem; font-weight: 700; color: #818cf8; text-transform: uppercase;'>Personalized using:</span> <span style='font-size: 0.84rem; color: #cbd5e1;'>{', '.join(highlights[:3])}</span>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Dispatch Options
            st.markdown("<hr style='margin: 1.5rem 0; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
            st.markdown("#### 🚀 Dispatch to Email Client")
            st.caption("Open pre-filled draft in your desktop mail app with your CV attached automatically.")

            col_disp1, col_disp2 = st.columns([1.5, 1])
            with col_disp1:
                st.session_state.recipient_email = st.text_input("Recipient / Recruiter Email:", value=st.session_state.recipient_email, placeholder="e.g. hiring@company.com")
                available_clients = get_installed_mail_clients()
                client_labels = [c["label"] for c in available_clients]
                chosen_client_label = st.selectbox("Select Desktop Client:", options=client_labels, index=0)
                chosen_client = next((c for c in available_clients if c["label"] == chosen_client_label), available_clients[0])

            with col_disp2:
                st.markdown("<div style='margin-top: 1.7rem;'>", unsafe_allow_html=True)
                if st.button(f"Open in {chosen_client['name']} ➔", type="primary", use_container_width=True):
                    success, msg = open_in_selected_mail_client(
                        client_id=chosen_client["id"],
                        recipient_email=st.session_state.recipient_email,
                        subject=chosen_subject,
                        body=final_email_content,
                        attachment_path=st.session_state.cv_file_path,
                        sender_email=current_user.get("email")
                    )
                    if success:
                        st.toast(f"Opened {chosen_client['name']} with draft and CV attached!", icon="🎉")
                    else:
                        st.error(msg)
                st.markdown("</div>", unsafe_allow_html=True)

            col_alt1, col_alt2 = st.columns(2)
            with col_alt1:
                safe_recip = st.session_state.recipient_email.strip()
                import urllib.parse
                gmail_link = f"https://mail.google.com/mail/?view=cm&fs=1&to={urllib.parse.quote(safe_recip)}&su={urllib.parse.quote(chosen_subject)}&body={urllib.parse.quote(final_email_content)}"
                st.markdown(f'<a href="{gmail_link}" target="_blank" style="display: block; text-align: center; background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.35); color: #fca5a5; padding: 0.6rem; border-radius: 8px; font-weight: 600; text-decoration: none;">📮 Compose in Gmail Web</a>', unsafe_allow_html=True)
            with col_alt2:
                eml_data = build_eml_message(
                    recipient_email=st.session_state.recipient_email,
                    subject=chosen_subject,
                    body=final_email_content,
                    cv_bytes=st.session_state.cv_file_bytes,
                    cv_name=st.session_state.cv_filename,
                    sender_email=current_user.get("email")
                )
                st.download_button(
                    label="📎 Download .eml Draft (CV Attached)",
                    data=eml_data,
                    file_name=f"outreach_{role_title.replace(' ', '_').lower()}.eml",
                    mime="message/rfc822",
                    use_container_width=True
                )

        st.markdown('</div>', unsafe_allow_html=True)
