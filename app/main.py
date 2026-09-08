import streamlit as st
import pandas as pd
import re
import sys
import os
import urllib.parse
from datetime import datetime
from pypdf import PdfReader

try:
    import docx
except ImportError:
    docx = None

from langchain_community.document_loaders import WebBaseLoader
from chain import Chain
from portfolio import Portfolio
import tracker

sys.path.append(os.path.dirname(__file__))

# ---------------------------------------------------------
# Page Configuration & UI Styles
# ---------------------------------------------------------
st.set_page_config(
    layout="wide",
    page_title="OutreachAI Studio | Intelligent Cold Outreach & Application Intelligence",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Background & Ambient Glow */
.stApp {
    background: radial-gradient(circle at 10% 10%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(236, 72, 153, 0.06) 0%, transparent 40%),
                #0b0f19;
    color: #e2e8f0;
}

/* Hero Banner */
.hero-container {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.1);
    position: relative;
    overflow: hidden;
}

.hero-container::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899, #06b6d4);
}

.hero-title {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.4rem;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.4);
    color: #a5b4fc;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 0.35rem 0.85rem;
    border-radius: 9999px;
    margin-bottom: 0.6rem;
}

.hero-subtitle {
    color: #94a3b8;
    font-size: 1rem;
    max-width: 800px;
    line-height: 1.5;
}

/* Auth Portal Container */
.auth-wrapper {
    max-width: 480px;
    margin: 1.5rem auto 3rem auto;
}

.auth-card {
    background: rgba(17, 24, 39, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 2.2rem;
    backdrop-filter: blur(16px);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.1);
}

.auth-header {
    text-align: center;
    margin-bottom: 1.8rem;
}

.auth-logo {
    font-size: 2.4rem;
    margin-bottom: 0.3rem;
}

.auth-title {
    font-size: 1.6rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.02em;
}

.auth-subtitle {
    font-size: 0.88rem;
    color: #94a3b8;
    margin-top: 0.3rem;
}

/* Feature Grid */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
    margin-top: 2rem;
}

.feature-box {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 1.2rem;
}

.feature-box-title {
    font-weight: 700;
    font-size: 0.92rem;
    color: #f1f5f9;
    margin-bottom: 0.35rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.feature-box-desc {
    font-size: 0.82rem;
    color: #94a3b8;
    line-height: 1.4;
}

/* Notification Alert Boxes */
.reply-alert-banner {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(16, 185, 129, 0.25) 100%);
    border: 1px solid rgba(34, 197, 94, 0.5);
    border-radius: 14px;
    padding: 1.1rem 1.5rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: #f0fdf4;
    box-shadow: 0 10px 25px -5px rgba(34, 197, 94, 0.2);
}

.followup-alert-banner {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.12) 0%, rgba(217, 119, 6, 0.2) 100%);
    border: 1px solid rgba(245, 158, 11, 0.4);
    border-radius: 14px;
    padding: 1rem 1.4rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: #fef3c7;
}

/* Glass Cards */
.glass-card {
    background: rgba(17, 24, 39, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    backdrop-filter: blur(10px);
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
}

.card-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 1.15rem;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

/* Status Pills */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
}
.status-pill.success {
    background: rgba(34, 197, 94, 0.15);
    color: #4ade80;
    border: 1px solid rgba(34, 197, 94, 0.3);
}
.status-pill.warning {
    background: rgba(234, 179, 8, 0.15);
    color: #facc15;
    border: 1px solid rgba(234, 179, 8, 0.3);
}

.strength-tag {
    display: inline-block;
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid rgba(34, 197, 94, 0.35);
    color: #86efac;
    font-size: 0.82rem;
    font-weight: 600;
    padding: 0.3rem 0.7rem;
    border-radius: 8px;
    margin: 0.25rem;
}

.gap-tag {
    display: inline-block;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.35);
    color: #fca5a5;
    font-size: 0.82rem;
    font-weight: 600;
    padding: 0.3rem 0.7rem;
    border-radius: 8px;
    margin: 0.25rem;
}

.score-badge {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #10b981 0%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.advice-box {
    background: rgba(15, 23, 42, 0.8);
    border-left: 4px solid #6366f1;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-top: 1rem;
    font-size: 0.95rem;
    line-height: 1.6;
    color: #cbd5e1;
}

.email-preview-box {
    background: #0f172a;
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 14px;
    padding: 1.5rem;
    line-height: 1.7;
    color: #e2e8f0;
    box-shadow: 0 15px 30px -10px rgba(0, 0, 0, 0.5);
}

section[data-testid="stSidebar"] {
    background-color: #070a12;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}

/* Seamless Dark Input Fields Styling */
div[data-baseweb="input"] {
    background-color: #0f172a !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    display: flex !important;
    align-items: center !important;
    padding-right: 0.5rem !important;
}

div[data-baseweb="base-input"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    flex: 1 !important;
}

div[data-testid="stTextInput"] input {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 0.98rem !important;
    padding: 0.65rem 0.85rem !important;
}

div[data-testid="stTextInput"] input::placeholder {
    color: #64748b !important;
    -webkit-text-fill-color: #64748b !important;
}

/* Main Action Buttons Styling (Excluding input icons) */
div[data-testid="stFormSubmitButton"] > button,
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 60%, #4338ca 100%) !important;
    background-color: #2563eb !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: 1px solid #60a5fa !important;
    border-radius: 12px !important;
    padding: 0.8rem 1.8rem !important;
    font-size: 1.05rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 4px 18px rgba(37, 99, 235, 0.5) !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    min-height: 48px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

div[data-testid="stFormSubmitButton"] > button *,
div[data-testid="stButton"] > button * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 800 !important;
    font-size: 1.05rem !important;
}

div[data-testid="stFormSubmitButton"] > button:hover,
div[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 50%, #3b82f6 100%) !important;
    background-color: #1d4ed8 !important;
    border-color: #93c5fd !important;
    box-shadow: 0 6px 25px rgba(59, 130, 246, 0.7) !important;
    transform: translateY(-2px) !important;
}

/* Password Visibility Toggle Button Reset & Custom Icon States */
div[data-testid="stTextInput"] button,
div[data-baseweb="input"] button,
button[aria-label="Show password text"],
button[aria-label="Hide password text"] {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0.25rem 0.5rem !important;
    min-height: unset !important;
    height: auto !important;
    width: auto !important;
    transform: none !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

div[data-testid="stTextInput"] button:hover,
div[data-baseweb="input"] button:hover {
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    transform: none !important;
}

/* Hide default SVG and render custom icon state */
button[aria-label="Show password text"] svg,
button[aria-label="Hide password text"] svg {
    display: none !important;
}

/* State 1: Password is NOT visible (Masked dots) -> Show CROSSED-OUT EYE icon */
button[aria-label="Show password text"]::after {
    content: '';
    display: inline-block;
    width: 22px;
    height: 22px;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24'%3E%3C/path%3E%3Cline x1='1' y1='1' x2='23' y2='23'%3E%3C/line%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: center;
    background-size: contain;
    transition: opacity 0.2s ease;
}

button[aria-label="Show password text"]:hover::after {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24'%3E%3C/path%3E%3Cline x1='1' y1='1' x2='23' y2='23'%3E%3C/line%3E%3C/svg%3E");
}

/* State 2: Password IS visible (Plain text) -> Show OPEN EYE icon */
button[aria-label="Hide password text"]::after {
    content: '';
    display: inline-block;
    width: 22px;
    height: 22px;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='%2338bdf8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z'%3E%3C/path%3E%3Ccircle cx='12' cy='12' r='3'%3E%3C/circle%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: center;
    background-size: contain;
    transition: opacity 0.2s ease;
}

button[aria-label="Hide password text"]:hover::after {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z'%3E%3C/path%3E%3Ccircle cx='12' cy='12' r='3'%3E%3C/circle%3E%3C/svg%3E");
}

/* Auth Tabs Navigation Styling */
div[data-testid="stTabs"] button[data-baseweb="tab"] {
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    padding: 0.75rem 1.8rem !important;
    color: #94a3b8 !important;
    border-radius: 12px 12px 0 0 !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
}

div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #ffffff !important;
    background: rgba(99, 102, 241, 0.15) !important;
    border-bottom: 3px solid #6366f1 !important;
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

def open_in_apple_mail(recipient_email: str, subject: str, body: str, attachment_path: str | None = None) -> tuple[bool, str]:
    import subprocess
    try:
        safe_subject = subject.replace('\\', '\\\\').replace('"', '\\"')
        safe_body = body.replace('\\', '\\\\').replace('"', '\\"')
        safe_recipient = recipient_email.replace('\\', '\\\\').replace('"', '\\"') if recipient_email else ""
        
        script = 'tell application "Mail"\n'
        script += '    activate\n'
        script += f'    set newMessage to make new outgoing message with properties {{subject:"{safe_subject}", content:"{safe_body}\\n\\n", visible:true}}\n'
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
            return True, "Opened Apple Mail with your CV attached!"
        else:
            return False, res.stderr.strip() or "Failed to execute AppleScript."
    except Exception as e:
        return False, str(e)

def build_eml_message(recipient_email: str, subject: str, body: str, cv_bytes: bytes | None = None, cv_name: str | None = None) -> bytes:
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication
    
    msg = MIMEMultipart()
    if recipient_email:
        msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    
    if cv_bytes and cv_name:
        part = MIMEApplication(cv_bytes, Name=cv_name)
        part["Content-Disposition"] = f'attachment; filename="{cv_name}"'
        msg.attach(part)
        
    return msg.as_bytes()

# ---------------------------------------------------------
# User Authentication Screen (Rendered if not signed in)
# ---------------------------------------------------------
if "current_user" not in st.session_state or st.session_state.current_user is None:
    st.markdown("""
    <div class="hero-container" style="text-align: center; padding: 1.8rem 2rem 1.5rem 2rem; margin-bottom: 1.2rem;">
        <div class="hero-badge">👋 Welcome</div>
        <div class="hero-title" style="margin-bottom: 0;">Welcome to OutreachAI</div>
    </div>
    """, unsafe_allow_html=True)

    col_center, _ = st.columns([1, 0.001])
    with col_center:
        auth_tab_signin, auth_tab_signup = st.tabs(["🔑 Sign In", "✨ Create Account"])

        with auth_tab_signin:
            st.markdown('<div class="glass-card" style="max-width: 520px; margin: 1rem auto;">', unsafe_allow_html=True)
            st.markdown('<div class="card-header">🔑 Sign In to Your Workspace</div>', unsafe_allow_html=True)
            
            with st.form("signin_form", clear_on_submit=False):
                login_username = st.text_input("Username or Email Address:", placeholder="Enter your username or email")
                login_password = st.text_input("Password:", type="password", placeholder="••••••••")
                submit_signin = st.form_submit_button("Sign In ➔", type="primary", use_container_width=True)

                if submit_signin:
                    if not login_username.strip() or not login_password:
                        st.error("⚠️ Please enter both username/email and password.")
                    else:
                        success, message, user = tracker.authenticate_user(login_username, login_password)
                        if success and user:
                            st.session_state.current_user = user
                            st.session_state.profile_loaded = False
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
            st.markdown('</div>', unsafe_allow_html=True)

        with auth_tab_signup:
            st.markdown('<div class="glass-card" style="max-width: 520px; margin: 1rem auto;">', unsafe_allow_html=True)
            st.markdown('<div class="card-header">✨ Create New Account</div>', unsafe_allow_html=True)
            
            with st.form("signup_form", clear_on_submit=False):
                reg_username = st.text_input("Desired Username:", placeholder="e.g. alexdev")
                reg_email = st.text_input("Email Address:", placeholder="e.g. alex@gmail.com")
                reg_password = st.text_input("Create Password (min 6 chars):", type="password", placeholder="••••••••")
                reg_confirm = st.text_input("Confirm Password:", type="password", placeholder="••••••••")
                submit_signup = st.form_submit_button("Create Account ➔", type="primary", use_container_width=True)

                if submit_signup:
                    if not reg_username.strip() or not reg_email.strip() or not reg_password:
                        st.error("⚠️ Please fill in all required fields.")
                    elif reg_password != reg_confirm:
                        st.error("⚠️ Passwords do not match. Please re-enter.")
                    else:
                        success, message, user = tracker.register_user(reg_username, reg_email, reg_password)
                        if success and user:
                            st.session_state.current_user = user
                            st.session_state.profile_loaded = False
                            st.success("🎉 Account created successfully! Loading your workspace...")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
            st.markdown('</div>', unsafe_allow_html=True)

    # Informational Feature Highlights
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-box">
            <div class="feature-box-title">📊 Job Fit & Skill Gap Diagnosis</div>
            <div class="feature-box-desc">Evaluates your CV against target job requirements in real-time, calculating a match percentage and missing keywords.</div>
        </div>
        <div class="feature-box">
            <div class="feature-box-title">✉️ High-Converting Cold Outreach</div>
            <div class="feature-box-desc">Generates persuasive, personalized cold emails with custom subject lines and relevant portfolio project links.</div>
        </div>
        <div class="feature-box">
            <div class="feature-box-title">📎 1-Click Apple Mail Automation</div>
            <div class="feature-box-desc">Launches macOS Apple Mail with recipient, subject, custom body, and your uploaded CV automatically attached.</div>
        </div>
        <div class="feature-box">
            <div class="feature-box-title">🗂️ Persistent Application Pipeline</div>
            <div class="feature-box-desc">Tracks your outreach stages, recruiter notes, and alerts you automatically when responses or follow-ups are due.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ---------------------------------------------------------
# Authenticated User Workspace
# ---------------------------------------------------------
current_user = st.session_state.current_user
user_id = current_user["id"]

# Load user profile from database into session state
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
        with open(st.session_state.cv_file_path, "rb") as f:
            st.session_state.cv_file_bytes = f.read()

    st.session_state.job_input_mode = "Direct Job Description"
    st.session_state.job_url = ""
    st.session_state.job_text = ""
    st.session_state.recipient_email = ""
    st.session_state.generated_results = None
    st.session_state.fit_analysis_result = None
    st.session_state.profile_loaded = True

def save_current_user_profile():
    tracker.save_user_profile(
        user_id=user_id,
        full_name=st.session_state.user_name,
        position=st.session_state.user_position,
        college=st.session_state.user_college,
        degree=st.session_state.user_study,
        candidate_type=st.session_state.candidate_type,
        custom_notes=st.session_state.custom_notes,
        portfolio_data=st.session_state.portfolio_df if st.session_state.portfolio_df is not None else [],
        cv_filename=st.session_state.cv_filename or "",
        cv_file_path=st.session_state.cv_file_path or ""
    )

# ---------------------------------------------------------
# Sidebar: User Account & LLM Controls
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 👤 User Account")
    st.markdown(f"**Signed in as:** `{current_user['username']}`")
    st.caption(f"📧 {current_user['email']}")
    
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.current_user = None
        st.session_state.profile_loaded = False
        st.rerun()

    st.markdown("---")
    st.markdown("### ⚡ AI Status")
    api_key = os.getenv("API_KEY") or os.getenv("GROQ_API_KEY")
    if api_key:
        st.markdown('<span class="status-pill success">● AI Engine Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-pill warning">⚠️ .env API Key Missing</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🧠 Model & Tone")
    
    selected_model = st.selectbox(
        "LLM Engine:",
        options=[
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.8-27b",
            "groq/compound-mini",
            "groq/compound",
            "qwen/qwen3.6-27b"
        ],
        index=0,
        help="OpenAI GPT-OSS 120B produces the most persuasive outreach emails."
    )

    selected_tone = st.selectbox(
        "Email Tone & Style:",
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
            "Standard (180-250 words)",
            "Concise & Punchy (under 130 words)",
            "Comprehensive (280+ words)"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("### 💾 Profile Memory")
    col_save, col_clear = st.columns(2)
    with col_save:
        if st.button("💾 Save Profile", help="Saves your current profile information permanently"):
            save_current_user_profile()
            st.toast("✅ Profile saved to memory!", icon="💾")
    with col_clear:
        if st.button("🔄 Reset Inputs", help="Clear form inputs"):
            for k in ["job_text", "job_url", "recipient_email", "generated_results", "fit_analysis_result"]:
                if k in st.session_state:
                    st.session_state[k] = "" if "text" in k or "url" in k or "email" in k else None
            st.rerun()

    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown(
        "<div style='color: #64748b; font-size: 0.78rem; text-align: center;'>"
        "OutreachAI Studio v5.2<br>Powered by <b>Groq LLMs</b> & <b>ChromaDB</b>"
        "</div>",
        unsafe_allow_html=True
    )

# ---------------------------------------------------------
# Dynamic Alerts (Recruiter Replies & Follow-Ups for User)
# ---------------------------------------------------------
alerts = tracker.get_user_alerts(user_id=user_id)
replies = alerts.get("replies", [])
pending_followups = alerts.get("pending_followups", [])

if replies:
    company_names = ", ".join([f"<b>{r['company']}</b> ({r['status']})" for r in replies[:2]])
    st.markdown(f"""
    <div class="reply-alert-banner">
        <div>
            🎉 <b>Recruiter Update / Reply Alert:</b> You have <b>{len(replies)}</b> application update(s): {company_names}!
        </div>
        <div style="font-size: 0.85rem; font-weight: 700;">Check <b>Tab 5 (Tracker)</b> for recruiter notes & details!</div>
    </div>
    """, unsafe_allow_html=True)

if pending_followups:
    count = len(pending_followups)
    sample_company = pending_followups[0]["company"]
    st.markdown(f"""
    <div class="followup-alert-banner">
        <div>
            🔔 <b>Follow-Up Reminder:</b> You have <b>{count}</b> active application(s) awaiting response (e.g. <b>{sample_company}</b> sent {pending_followups[0].get('days_since_applied', 3)}+ days ago).
        </div>
        <div style="font-size: 0.85rem; font-weight: 600;">Check <b>Tab 5 (Tracker)</b> to generate 1-click follow-up emails!</div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# Main Page Header / Hero
# ---------------------------------------------------------
st.markdown("""
<div class="hero-container">
    <div class="hero-badge">⚡ AI-Powered Candidate Outreach & Application Tracker</div>
    <div class="hero-title">High-Converting Cold Email Studio</div>
    <div class="hero-subtitle">
        Analyze real-time job fit & skill gaps, generate tailored cold outreach with pre-attached CVs, and manage your entire application pipeline in one place.
    </div>
</div>
""", unsafe_allow_html=True)

# Initialize Chain instance
try:
    chain = Chain(model_name=selected_model, api_key=api_key)
except Exception as e:
    st.error(f"⚠️ Error initializing LLM Chain: {e}")
    chain = None

# ---------------------------------------------------------
# Main Workflow Tabs
# ---------------------------------------------------------
tab_profile, tab_job, tab_fit, tab_studio, tab_tracker = st.tabs([
    "👤 1. Profile & Portfolio",
    "🎯 2. Target Job",
    "📊 3. Fit & Gap Analysis",
    "✉️ 4. Email Studio",
    "🗂️ 5. Application Tracker"
])

# ---------------------------------------------------------
# TAB 1: Profile & Portfolio
# ---------------------------------------------------------
with tab_profile:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">👤 Your Candidate Profile</div>', unsafe_allow_html=True)
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.session_state.user_name = st.text_input(
            "Your Full Name *",
            value=st.session_state.user_name,
            placeholder="e.g. Arrathikan Sarma",
            help="Used for email signature and personalized greetings."
        )
        st.session_state.user_position = st.text_input(
            "Current Role / Headline *",
            value=st.session_state.user_position,
            placeholder="e.g. AI & Full-Stack Developer",
            help="Your professional headline or current position."
        )
    with col_p2:
        st.session_state.user_college = st.text_input(
            "University / Company / Institution",
            value=st.session_state.user_college,
            placeholder="e.g. University of Moratuwa",
            help="Where you study or work."
        )
        st.session_state.user_study = st.text_input(
            "Degree / Major / Specialization",
            value=st.session_state.user_study,
            placeholder="e.g. BSc (Hons) in Information Technology",
            help="Your academic field or core specialty."
        )

    st.session_state.candidate_type = st.radio(
        "Candidate Level:",
        ["Student / Recent Graduate", "Experienced Professional", "Freelancer / Consultant"],
        horizontal=True,
        index=["Student / Recent Graduate", "Experienced Professional", "Freelancer / Consultant"].index(st.session_state.candidate_type)
        if st.session_state.candidate_type in ["Student / Recent Graduate", "Experienced Professional", "Freelancer / Consultant"] else 0
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Portfolio / CV Section
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">📂 Portfolio & Experience Knowledge Base</div>', unsafe_allow_html=True)
    
    st.caption("Upload your CV (PDF / DOCX / CSV) to automatically extract your tech stack and matching project links.")
    
    uploaded_file = st.file_uploader(
        "Upload Resume / CV or Portfolio CSV:",
        type=["pdf", "docx", "csv", "txt"],
        help="We automatically parse your skills and project links to build vector embeddings for semantic matching."
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        saved_path = os.path.join(UPLOAD_DIR, f"{user_id}_{uploaded_file.name}")
        with open(saved_path, "wb") as f:
            f.write(file_bytes)

        st.session_state.cv_file_bytes = file_bytes
        st.session_state.cv_filename = uploaded_file.name
        st.session_state.cv_file_path = saved_path

        with st.spinner("🧠 Analyzing and vectorizing your CV portfolio..."):
            try:
                extracted_df = process_cv_to_dataframe(uploaded_file, chain)
                st.session_state.portfolio_df = extracted_df
                save_current_user_profile()
                st.success(f"✅ Successfully extracted {len(extracted_df)} portfolio items from `{uploaded_file.name}` and saved to memory!")
            except Exception as e:
                st.error(f"⚠️ Error parsing file: {e}")

    if st.session_state.cv_filename:
        st.markdown(f'<span class="status-pill success">📎 Attached CV for Outreach: <b>{st.session_state.cv_filename}</b></span>', unsafe_allow_html=True)

    if st.session_state.portfolio_df is not None and not st.session_state.portfolio_df.empty:
        st.markdown("#### 🔍 Active Portfolio Items & Project Links:")
        edited_df = st.data_editor(
            st.session_state.portfolio_df,
            num_rows="dynamic",
            use_container_width=True,
            key="portfolio_editor"
        )
        st.session_state.portfolio_df = edited_df
    else:
        st.info("💡 Upload your CV above to extract your skills and projects.")
        
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 2: Target Job Opportunity
# ---------------------------------------------------------
with tab_job:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">🎯 Target Job & Recruiter Details</div>', unsafe_allow_html=True)

    col_j1, col_j2 = st.columns([1.5, 1])
    with col_j1:
        job_mode = st.radio(
            "Job Information Source:",
            ["Direct Job Description / Paste Text (Recommended)", "Scrape Job URL"],
            index=0 if st.session_state.job_input_mode == "Direct Job Description" else 1,
            horizontal=True
        )
        st.session_state.job_input_mode = "Direct Job Description" if "Direct" in job_mode else "Job URL"
    with col_j2:
        st.session_state.recipient_email = st.text_input(
            "Company / Recruiter Email Address (Optional):",
            value=st.session_state.recipient_email,
            placeholder="e.g. careers@company.com or hr@startup.io",
            help="Pre-fills the 'To:' field in your email client."
        )

    if st.session_state.job_input_mode == "Job URL":
        st.session_state.job_url = st.text_input(
            "Enter Job Posting / Careers URL:",
            value=st.session_state.job_url,
            placeholder="e.g. https://careers.company.com/job/senior-python-developer"
        )
        st.caption("ℹ️ Note: Some protected corporate portals (like LinkedIn, Workday) may block web scrapers. In that case, switch to 'Direct Job Description' to paste the text directly.")
    else:
        st.session_state.job_text = st.text_area(
            "Paste Job Description / Requirements:",
            value=st.session_state.job_text,
            height=200,
            placeholder="Paste the full job posting, required qualifications, company mission, or recruiter note here..."
        )

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">✨ Special Instructions & Custom Angles (Optional)</div>', unsafe_allow_html=True)
    st.session_state.custom_notes = st.text_input(
        "Add any specific highlights, start date availability, or personal connection:",
        value=st.session_state.custom_notes,
        placeholder="e.g. Mention that I built an open-source tool with 500+ GitHub stars; available immediately for remote work."
    )
    st.markdown('</div>', unsafe_allow_html=True)

def get_current_job_text():
    if st.session_state.job_input_mode == "Job URL":
        if not st.session_state.job_url.strip():
            return None, "Please provide a valid Job URL in Tab 2."
        try:
            loader = WebBaseLoader([st.session_state.job_url.strip()])
            page_content = loader.load().pop().page_content
            return clean_text(page_content), None
        except Exception as e:
            return None, f"Scraping failed: {e}. Please switch to Direct Job Description."
    else:
        if not st.session_state.job_text.strip():
            return None, "Please paste the Job Description in Tab 2."
        return clean_text(st.session_state.job_text), None

# ---------------------------------------------------------
# TAB 3: Job Fit & Gap Analysis
# ---------------------------------------------------------
with tab_fit:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">📊 Real-Time Candidate-to-Job Fit Report</div>', unsafe_allow_html=True)
    
    st.caption("Evaluates your CV portfolio against the job requirements to calculate your match score, strengths, and missing skill gaps.")
    
    if st.button("🔍 Run Fit & Gap Analysis", use_container_width=True):
        if not st.session_state.user_name.strip():
            st.error("⚠️ Please enter your name in the **Profile** tab.")
        elif st.session_state.portfolio_df is None or st.session_state.portfolio_df.empty:
            st.error("⚠️ Please upload a CV in the **Profile** tab.")
        elif not api_key:
            st.error("⚠️ Missing Groq API Key in .env.")
        else:
            job_raw_text, err = get_current_job_text()
            if err:
                st.error(f"⚠️ {err}")
            else:
                with st.spinner("🤖 Evaluating skill alignment, calculating match percentage, and diagnosing skill gaps..."):
                    try:
                        jobs = chain.extract_jobs(job_raw_text)
                        target_job = jobs[0] if jobs else {"role": "Target Role", "skills": []}
                        
                        portfolio_str = ""
                        for _, row in st.session_state.portfolio_df.iterrows():
                            portfolio_str += f"- Tech: {row.get('Techstack', '')} | Project: {row.get('Links', '')}\n"

                        analysis = chain.analyze_job_fit(
                            job=target_job,
                            portfolio_summary=portfolio_str,
                            user_name=st.session_state.user_name,
                            user_position=st.session_state.user_position,
                            user_study=st.session_state.user_study
                        )
                        st.session_state.fit_analysis_result = {
                            "job": target_job,
                            "analysis": analysis
                        }
                        st.success("🎉 Fit Analysis Complete!")
                    except Exception as e:
                        st.error(f"⚠️ Analysis failed: {e}")

    if st.session_state.fit_analysis_result:
        res = st.session_state.fit_analysis_result["analysis"]
        target_job = st.session_state.fit_analysis_result["job"]
        score = res.get("match_score", 85)
        fit_level = res.get("fit_level", "Strong Match")
        strengths = res.get("matched_strengths", [])
        gaps = res.get("skill_gaps", [])
        advice = res.get("strategic_advice", "")

        st.markdown("<hr>", unsafe_allow_html=True)
        col_s1, col_s2 = st.columns([1, 2])
        with col_s1:
            st.markdown(f'<div class="score-badge">{score}%</div>', unsafe_allow_html=True)
            st.markdown(f'<span class="status-pill success">● {fit_level}</span>', unsafe_allow_html=True)
            st.progress(score / 100.0)
        with col_s2:
            st.markdown(f"### Target Role: **{target_job.get('role', 'Target Role')}**")
            st.markdown(f"Company: **{target_job.get('company', 'Target Company')}**")

        st.markdown("<br>", unsafe_allow_html=True)
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("#### ✅ Matched Strengths & Skills")
            if strengths:
                for s in strengths:
                    st.markdown(f'<span class="strength-tag">✓ {s}</span>', unsafe_allow_html=True)
            else:
                st.write("Solid foundational profile.")
        with col_g2:
            st.markdown("#### ⚠️ Skill Gaps & Missing Keywords")
            if gaps:
                for g in gaps:
                    st.markdown(f'<span class="gap-tag">! {g}</span>', unsafe_allow_html=True)
            else:
                st.write("No critical gaps detected!")

        if advice:
            st.markdown(f"""
            <div class="advice-box">
                <b>💡 Strategic Positioning & Interview Advice:</b><br>
                {advice}
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 4: Email Generation Studio
# ---------------------------------------------------------
with tab_studio:
    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        generate_clicked = st.button("🚀 Generate Cold Email", use_container_width=True)
    with col_info:
        st.caption("Matches your portfolio against job requirements and drafts personalized outreach with high-converting subject lines.")

    if generate_clicked:
        if not st.session_state.user_name.strip():
            st.error("⚠️ Please enter your name in the **Profile** tab.")
            st.stop()

        if st.session_state.portfolio_df is None or st.session_state.portfolio_df.empty:
            st.error("⚠️ Please upload a CV/portfolio in the **Profile** tab.")
            st.stop()

        if not api_key:
            st.error("⚠️ Missing Groq API Key. Please ensure your API_KEY is set in your .env file.")
            st.stop()

        job_raw_text, err = get_current_job_text()
        if err:
            st.error(f"⚠️ {err}")
            st.stop()

        with st.spinner("🤖 Extracting job requirements, vector-matching portfolio links, and generating outreach email..."):
            try:
                jobs = chain.extract_jobs(job_raw_text)
                if not jobs:
                    st.warning("Could not structure job postings, using raw description fallback.")
                    jobs = [{"role": "Target Role", "company": "Hiring Team", "skills": [], "description": job_raw_text[:300]}]

                portfolio_instance = Portfolio(data=st.session_state.portfolio_df)
                portfolio_instance.load_portfolio(clear_existing=True)

                results = []
                for job in jobs:
                    if not st.session_state.recipient_email and job.get("contact_email"):
                        st.session_state.recipient_email = job.get("contact_email")

                    skills = job.get("skills", [])
                    matched_links = portfolio_instance.query_links(skills, n_results=3)
                    
                    email_result = chain.write_mail(
                        job=job,
                        links=matched_links,
                        user_name=st.session_state.user_name,
                        user_college=st.session_state.user_college,
                        user_study=st.session_state.user_study,
                        user_position=st.session_state.user_position,
                        tone=selected_tone,
                        length=selected_length,
                        candidate_type=st.session_state.candidate_type,
                        custom_instructions=st.session_state.custom_notes
                    )

                    results.append({
                        "job": job,
                        "matched_links": matched_links,
                        "email_data": email_result
                    })

                st.session_state.generated_results = results
                save_current_user_profile()
                st.success("🎉 Email successfully crafted!")

            except Exception as e:
                st.error(f"⚠️ Generation failed: {e}")

    # Display Results if available
    if st.session_state.generated_results:
        for idx, item in enumerate(st.session_state.generated_results):
            job = item["job"]
            matched_links = item["matched_links"]
            email_data = item["email_data"]

            role_title = job.get("role", "Target Position")
            company_name = job.get("company", "Company")
            extracted_skills = job.get("skills", [])
            subject_lines = email_data.get("subject_lines", [f"Application for {role_title} - {st.session_state.user_name}"])
            email_body = email_data.get("body", "")

            st.markdown(f"### 📋 Outreach Plan for: **{role_title}** at **{company_name}**")
            
            st.markdown("#### 💡 High-Converting Subject Lines")
            chosen_subject = st.radio(
                "Choose your preferred subject line:",
                options=subject_lines,
                index=0,
                key=f"subj_radio_{idx}"
            )

            st.markdown("#### 📝 Cold Email Body")
            view_mode = st.radio("Display Mode:", ["Visual Preview", "Editable Text"], horizontal=True, key=f"mode_{idx}")
            
            if view_mode == "Visual Preview":
                st.markdown(f"""
                <div class="email-preview-box">
                    <div style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.8rem; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 0.5rem;">
                        <b>Subject:</b> <span style="color: #38bdf8;">{chosen_subject}</span>
                    </div>
                    <div style="white-space: pre-wrap; font-size: 0.95rem;">{email_body}</div>
                </div>
                """, unsafe_allow_html=True)
                final_email_content = email_body
            else:
                final_email_content = st.text_area(
                    "Edit your email before sending:",
                    value=email_body,
                    height=300,
                    key=f"editor_area_{idx}"
                )

            # -------------------------------------------------
            # ✉️ Email Dispatch & Action Hub
            # -------------------------------------------------
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-header">✉️ Email Dispatch & Attachment Hub</div>', unsafe_allow_html=True)
            
            col_target1, col_target2 = st.columns([1.5, 1])
            with col_target1:
                target_email = st.text_input(
                    "Company / Recruiter Email Address:",
                    value=st.session_state.recipient_email,
                    key=f"target_email_{idx}",
                    placeholder="e.g. careers@company.com or hr@apexai.io"
                )
                st.session_state.recipient_email = target_email
            with col_target2:
                st.markdown("<div style='margin-top: 1.8rem;'>", unsafe_allow_html=True)
                if st.session_state.cv_filename:
                    st.markdown(f'<span class="status-pill success">📎 Attached CV: <b>{st.session_state.cv_filename}</b></span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="status-pill warning">⚠️ No CV uploaded yet (upload in Tab 1)</span>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            col_act1, col_act2, col_act3, col_act4 = st.columns([1.5, 1.2, 1.3, 1.1])
            
            subject_encoded = urllib.parse.quote(chosen_subject)
            body_encoded = urllib.parse.quote(final_email_content)
            mailto_to = target_email.strip() if target_email else ""
            gmail_link = f"https://mail.google.com/mail/?view=cm&fs=1&to={mailto_to}&su={subject_encoded}&body={body_encoded}"

            with col_act1:
                if st.button("✉️ Open in Mail App (CV Auto-Attached)", key=f"btn_apple_mail_{idx}", type="primary", use_container_width=True, help="Opens Apple Mail with recipient, subject, body, AND your uploaded CV already attached!"):
                    success, msg = open_in_apple_mail(
                        recipient_email=target_email,
                        subject=chosen_subject,
                        body=final_email_content,
                        attachment_path=st.session_state.cv_file_path
                    )
                    if success:
                        st.balloons()
                        st.success(f"🎉 **Apple Mail Opened!** Recipient `{target_email or 'Draft'}`, subject, and `{st.session_state.cv_filename or 'CV'}` are automatically attached. Simply hit **Send** in your Mail app!")
                        tracker.save_application(
                            user_id=user_id,
                            company=company_name,
                            role=role_title,
                            recipient_email=target_email,
                            match_score=85,
                            subject_line=chosen_subject,
                            email_body=final_email_content,
                            status="Applied"
                        )
                    else:
                        mailto_link = f"mailto:{mailto_to}?subject={subject_encoded}&body={body_encoded}"
                        st.markdown(f'<a href="{mailto_link}" target="_blank" style="color: #38bdf8;">Click here to open default mail client</a>', unsafe_allow_html=True)
            
            with col_act2:
                st.markdown(
                    f'<a href="{gmail_link}" target="_blank" style="display: block; text-align: center; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); color: #fca5a5; padding: 0.65rem; border-radius: 10px; font-weight: 700; text-decoration: none;">📮 Open in Gmail</a>',
                    unsafe_allow_html=True
                )
            with col_act3:
                eml_data = build_eml_message(
                    recipient_email=target_email,
                    subject=chosen_subject,
                    body=final_email_content,
                    cv_bytes=st.session_state.cv_file_bytes,
                    cv_name=st.session_state.cv_filename
                )
                st.download_button(
                    label="📎 Draft with Attached CV (.eml)",
                    data=eml_data,
                    file_name=f"outreach_{role_title.replace(' ', '_').lower()}.eml",
                    mime="message/rfc822",
                    help="Downloads a pre-filled draft email with your CV already attached.",
                    use_container_width=True
                )
            with col_act4:
                st.download_button(
                    label="💾 Download TXT",
                    data=f"To: {target_email}\nSubject: {chosen_subject}\n\n{final_email_content}",
                    file_name=f"cold_email_{role_title.replace(' ', '_').lower()}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"📌 Save '{company_name}' to Application Tracker", key=f"save_tracker_{idx}"):
                tracker.save_application(
                    user_id=user_id,
                    company=company_name,
                    role=role_title,
                    recipient_email=target_email,
                    match_score=85,
                    subject_line=chosen_subject,
                    email_body=final_email_content,
                    status="Applied"
                )
                st.toast(f"✅ Saved application for {company_name} to Tracker!", icon="📂")

            st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 5: Application Tracker & History
# ---------------------------------------------------------
with tab_tracker:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">🗂️ Application Pipeline & Follow-Up Manager</div>', unsafe_allow_html=True)

    all_apps = tracker.get_all_applications(user_id=user_id)

    if not all_apps:
        st.info("💡 No applications saved yet. Generate and send an outreach email in Tab 4 to automatically log it here!")
    else:
        total_apps = len(all_apps)
        applied_count = sum(1 for a in all_apps if a["status"] in ["Applied", "Sent"])
        interview_count = sum(1 for a in all_apps if a["status"] in ["Interview Scheduled", "Interviewing"])
        offer_count = sum(1 for a in all_apps if a["status"] == "Offer")
        replied_count = sum(1 for a in all_apps if a["status"] == "Reply Received")

        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        col_stat1.metric("Total Outreach", total_apps)
        col_stat2.metric("Sent / Applied", applied_count)
        col_stat3.metric("Replies / Interviews", interview_count + replied_count)
        col_stat4.metric("Offers 🎉", offer_count)

        st.markdown("<hr>", unsafe_allow_html=True)

        col_flt1, col_flt2 = st.columns([2, 1])
        with col_flt1:
            search_query = st.text_input("🔍 Search by Company or Role:", placeholder="e.g. Apex Technologies")
        with col_flt2:
            status_filter = st.selectbox("Filter by Status:", ["All", "Applied", "Reply Received", "Interview Scheduled", "Drafted", "Offer", "Archived"])

        filtered_apps = all_apps
        if search_query:
            filtered_apps = [a for a in filtered_apps if search_query.lower() in a["company"].lower() or search_query.lower() in a["role"].lower()]
        if status_filter != "All":
            filtered_apps = [a for a in filtered_apps if a["status"] == status_filter]

        st.markdown(f"#### Active Applications ({len(filtered_apps)})")

        for app in filtered_apps:
            with st.expander(f"💼 **{app['company']}** — {app['role']} [{app['status']}]", expanded=(app["status"] in ["Interview Scheduled", "Reply Received"])):
                col_info1, col_info2 = st.columns([1.5, 1])
                with col_info1:
                    st.markdown(f"**Recipient:** `{app['recipient_email'] or 'N/A'}`")
                    st.markdown(f"**Date Applied:** {app['applied_at'] or app['created_at']}")
                    if app.get("last_followup_at"):
                        st.markdown(f"**Last Followed Up:** {app['last_followup_at']}")
                    st.markdown(f"**Subject Line:** *{app['subject_line']}*")
                with col_info2:
                    current_status = app["status"]
                    status_options = ["Drafted", "Applied", "Reply Received", "Interview Scheduled", "Offer", "Archived"]
                    status_idx = status_options.index(current_status) if current_status in status_options else 0
                    
                    new_status = st.selectbox("Update Status / Reply Received:", status_options, index=status_idx, key=f"status_select_{app['id']}")
                    if new_status != current_status:
                        tracker.update_application_status(app["id"], new_status)
                        st.toast(f"Status updated to '{new_status}'!", icon="✅")
                        st.rerun()

                current_notes = st.text_area("Recruiter Notes / Next Steps:", value=app.get("notes", ""), key=f"notes_{app['id']}", height=80)
                if st.button("💾 Save Notes", key=f"save_notes_{app['id']}"):
                    tracker.update_application_status(app["id"], app["status"], notes=current_notes)
                    st.toast("Notes saved!", icon="📝")

                st.markdown("##### ⚡ Follow-Up Sequence Generator")
                if st.button(f"✉️ Generate Follow-Up Email for {app['company']}", key=f"gen_follow_{app['id']}"):
                    with st.spinner("Drafting follow-up email..."):
                        follow_res = chain.write_followup_mail(
                            job={"role": app["role"], "company": app["company"]},
                            user_name=st.session_state.user_name or "Candidate",
                            days_since=4
                        )
                        tracker.log_followup(app["id"])
                        st.markdown(f"""
                        <div class="email-preview-box" style="margin-top: 0.8rem;">
                            <b>Subject:</b> {follow_res.get('subject')}<br><br>
                            <div style="white-space: pre-wrap;">{follow_res.get('body')}</div>
                        </div>
                        """, unsafe_allow_html=True)

                if st.button("🗑️ Delete Application", key=f"del_app_{app['id']}"):
                    tracker.delete_application(app["id"])
                    st.toast(f"Deleted application for {app['company']}", icon="🗑️")
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
