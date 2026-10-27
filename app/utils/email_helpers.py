"""
Helper functions for CV extraction, text cleaning, Apple Mail AppleScript automation, and .eml file construction.
"""
import os
import sys
import re
import tempfile
import subprocess
import pandas as pd
import streamlit as st
from services.cv_parser import extract_text_from_cv, CVExtractionError

def clean_text(text: str) -> str:
    """Sanitizes raw scraped HTML/text while preserving meaningful punctuation."""
    if not text:
        return ""
    text = re.sub(r'<[^>]*?>', ' ', text)
    text = re.sub(r'http[s]?://\S+', ' ', text)
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9.,;:!?@%&\-\'\"/() ]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_text_from_file(uploaded_file) -> str:
    """Extracts text from uploaded CV file with user-friendly error wrapping."""
    try:
        return extract_text_from_cv(uploaded_file)
    except CVExtractionError as e:
        raise ValueError(str(e))
    except Exception as e:
        raise ValueError(f"Failed to read CV: {str(e)}")

def process_cv_to_dataframe(uploaded_file, chain) -> pd.DataFrame:
    """Parses CV or CSV into standard Techstack/Links DataFrame."""
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
    """Retrieves plain text of the currently active CV in session state."""
    cv_path = st.session_state.get("cv_file_path")
    if cv_path and os.path.isfile(cv_path):
        try:
            with open(cv_path, "rb") as f_cv:
                return extract_text_from_file(f_cv)
        except Exception:
            return ""
    return ""

def open_in_apple_mail(
    recipient_email: str,
    subject: str,
    body: str,
    attachment_path: str | None = None,
    sender_email: str | None = None
) -> tuple[bool, str]:
    """Generates an Apple Mail draft using osascript on macOS with optional CV attachment."""
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

def build_eml_message(
    recipient_email: str,
    subject: str,
    body: str,
    cv_bytes: bytes | None = None,
    cv_name: str | None = None,
    sender_email: str | None = None
) -> bytes:
    """Builds RFC 822 .eml MIME byte structure."""
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
    """Detects available desktop mail software on macOS and Windows."""
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

def open_in_selected_mail_client(
    client_id: str,
    recipient_email: str,
    subject: str,
    body: str,
    attachment_path: str | None = None,
    sender_email: str | None = None
) -> tuple[bool, str]:
    """Launches the selected desktop mail client with draft & CV attached."""
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
