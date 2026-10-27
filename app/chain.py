"""
Backward compatibility facade for services.llm_chain.
Ensures existing tests, modules, and scripts import Chain smoothly.
"""
from services.llm_chain import (
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
]
