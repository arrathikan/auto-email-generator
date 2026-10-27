"""
Backward compatibility facade for services.job_loader.
"""
from services.job_loader import is_safe_url, extract_job_posting_text

__all__ = ["is_safe_url", "extract_job_posting_text"]
