"""
Lightweight mail dispatch module.
(All IMAP mailbox syncing and email reply analysis systems have been permanently removed.)
"""
from mailer import send_email_smtp, auto_detect_smtp_server

__all__ = ["send_email_smtp", "auto_detect_smtp_server"]
