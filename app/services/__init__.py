"""
Service layer containing LLM orchestration, CV parsing, job scraping, portfolio storage, and mail dispatch.
"""
from .llm_chain import (
    Chain,
    skill_match_regex,
    find_cv_evidence,
    is_valid_url,
    sanitize_extracted_portfolio,
    audit_and_calculate_score,
    SUPPORTED_MODELS,
    CANONICAL_ALIASES,
    RELATED_ECOSYSTEMS,
)
from .cv_parser import (
    extract_text_from_cv,
    validate_cv_file,
    CVExtractionError,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
)
from .job_loader import is_safe_url, extract_job_posting_text
from .portfolio import Portfolio, sanitize_collection_name
from .mailer import send_email_smtp, auto_detect_smtp_server

__all__ = [
    "Chain",
    "skill_match_regex",
    "find_cv_evidence",
    "is_valid_url",
    "sanitize_extracted_portfolio",
    "audit_and_calculate_score",
    "SUPPORTED_MODELS",
    "CANONICAL_ALIASES",
    "RELATED_ECOSYSTEMS",
    "extract_text_from_cv",
    "validate_cv_file",
    "CVExtractionError",
    "ALLOWED_EXTENSIONS",
    "MAX_FILE_SIZE_BYTES",
    "is_safe_url",
    "extract_job_posting_text",
    "Portfolio",
    "sanitize_collection_name",
    "send_email_smtp",
    "auto_detect_smtp_server",
]
