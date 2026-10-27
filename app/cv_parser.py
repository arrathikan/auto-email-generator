"""
Backward compatibility facade for services.cv_parser.
"""
from services.cv_parser import (
    extract_text_from_cv,
    validate_cv_file,
    CVExtractionError,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
)

__all__ = [
    "extract_text_from_cv",
    "validate_cv_file",
    "CVExtractionError",
    "ALLOWED_EXTENSIONS",
    "MAX_FILE_SIZE_BYTES",
]
