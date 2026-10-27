"""
Backward compatibility facade for services.portfolio.
"""
from services.portfolio import Portfolio, sanitize_collection_name

__all__ = ["Portfolio", "sanitize_collection_name"]