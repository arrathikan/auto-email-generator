import os
import smtplib
import email.utils
from email.message import EmailMessage
import re
import tracker

def auto_detect_smtp_server(email_address: str) -> tuple[str, int]:
    """
    Auto-detects SMTP host and port based on the user's email domain.
    Returns (host, port).
    """
    clean_email = email_address.strip().lower()
    domain = clean_email.split("@")[-1] if "@" in clean_email else ""
    
    if domain in ["gmail.com", "googlemail.com"]:
        return "smtp.gmail.com", 465
    elif domain in ["outlook.com", "hotmail.com", "live.com", "office365.com"]:
        return "smtp.office365.com", 587
    elif domain in ["yahoo.com", "ymail.com", "rocketmail.com"]:
        return "smtp.mail.yahoo.com", 465
    elif domain in ["icloud.com", "me.com", "mac.com"]:
        return "smtp.mail.me.com", 587
    elif domain in ["zoho.com"]:
        return "smtp.zoho.com", 465
    elif domain in ["aol.com"]:
        return "smtp.aol.com", 465
    elif domain:
        return f"smtp.{domain}", 465
    return "smtp.gmail.com", 465

def send_email_smtp(
    user_id: int,
    recipient_email: str,
    subject: str,
    body_text: str,
    cv_path: str | None = None,
    sender_email: str = "",
    app_password: str = "",
    smtp_host: str = "",
    smtp_port: int | None = None,
    app_id: int | None = None
) -> dict:
    """
    Sends an email directly via SMTP with optional CV PDF attachment.
    """
    # Check configured credentials
    config = tracker.get_user_mail_config(user_id) if user_id else {}
    from_email = (sender_email or config.get("email_address", "")).strip()
    pwd = (app_password or config.get("app_password", "")).strip()

    if not from_email or not pwd:
        return {
            "success": False,
            "error": "SMTP credentials not configured. Please enter your Sender Email and App Password in the SMTP Settings below."
        }

    if not recipient_email or "@" not in recipient_email:
        return {
            "success": False,
            "error": "Please enter a valid recipient email address."
        }

    host = smtp_host.strip() if smtp_host else config.get("smtp_host", "")
    port = smtp_port or config.get("smtp_port")
    if not host or not port:
        detected_h, detected_p = auto_detect_smtp_server(from_email)
        host = host or detected_h
        port = port or detected_p

    sender_domain = from_email.split("@")[-1] if "@" in from_email else "mail.local"
    message_id = f"<outreach_{int(os.times().elapsed)}_{os.urandom(4).hex()}@{sender_domain}>"

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg["Message-ID"] = message_id
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg.set_content(body_text)

    # Attach CV PDF if present
    attached_cv = False
    if cv_path and os.path.isfile(cv_path):
        try:
            with open(cv_path, "rb") as f:
                pdf_bytes = f.read()
            cv_filename = os.path.basename(cv_path)
            clean_cv_filename = re.sub(r'^\d+_', '', cv_filename)
            msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=clean_cv_filename)
            attached_cv = True
        except Exception:
            pass

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=20) as server:
                server.login(from_email, pwd)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.starttls()
                server.login(from_email, pwd)
                server.send_message(msg)

        return {
            "success": True,
            "message_id": message_id,
            "attached_cv": attached_cv,
            "message": "Email sent successfully via SMTP!"
        }
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "error": "Authentication failed. Please verify your email and App Password (for Gmail, use a 16-character App Password, not your regular password)."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to send email: {str(e)}"
        }
