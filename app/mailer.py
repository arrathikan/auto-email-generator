"""
Backward compatibility facade for services.mailer.
"""
from services.mailer import send_email_smtp, auto_detect_smtp_server

__all__ = ["send_email_smtp", "auto_detect_smtp_server"]
