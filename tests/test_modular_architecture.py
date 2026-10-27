"""
Tests verifying clean modular package layout and facade backward compatibility.
"""
import pytest

def test_core_package_imports():
    from core.config import DATA_DIR, UPLOADS_DIR, ASSETS_DIR
    from core.security import ENCRYPTION_PREFIX, encrypt_smtp_password, decrypt_smtp_password
    from core.auth import hash_password, verify_password
    from core.database import get_connection, init_db
    
    assert DATA_DIR is not None
    assert ENCRYPTION_PREFIX == "enc_v1:"
    
    # Test auth roundtrip
    h, _ = hash_password("TestPassword123")
    assert verify_password("TestPassword123", h)
    assert not verify_password("WrongPassword", h)

def test_services_package_imports():
    from services.cv_parser import extract_text_from_cv, CVExtractionError
    from services.job_loader import is_safe_url, extract_job_posting_text
    from services.portfolio import Portfolio, sanitize_collection_name
    from services.mailer import send_email_smtp, auto_detect_smtp_server
    from services.llm_chain import Chain, audit_and_calculate_score
    
    assert callable(extract_text_from_cv)
    assert callable(is_safe_url)
    assert callable(sanitize_collection_name)
    assert callable(send_email_smtp)
    assert callable(audit_and_calculate_score)

def test_ui_and_styles_package_imports():
    from styles.theme import CUSTOM_CSS, apply_custom_theme
    from ui import (
        render_sidebar,
        render_auth_view,
        render_dashboard_view,
        render_profile_view,
        render_analyze_view,
        render_audit_view,
        render_email_view
    )
    from utils.email_helpers import clean_text, build_eml_message
    
    assert "stApp" in CUSTOM_CSS
    assert clean_text("<p>Hello   World!</p>") == "Hello World!"
    assert callable(build_eml_message)
    assert callable(render_sidebar)
