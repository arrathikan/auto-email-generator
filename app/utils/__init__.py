"""
CareerLens utilities module for text sanitization, desktop client dispatch, and EML creation.
"""
from .email_helpers import (
    clean_text,
    extract_text_from_file,
    process_cv_to_dataframe,
    get_candidate_cv_text,
    open_in_apple_mail,
    build_eml_message,
    get_installed_mail_clients,
    open_in_selected_mail_client,
)

__all__ = [
    "clean_text",
    "extract_text_from_file",
    "process_cv_to_dataframe",
    "get_candidate_cv_text",
    "open_in_apple_mail",
    "build_eml_message",
    "get_installed_mail_clients",
    "open_in_selected_mail_client",
]
