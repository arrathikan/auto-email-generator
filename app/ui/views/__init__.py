"""
Views package for CareerLens UI.
"""
from .auth_view import render_auth_view
from .dashboard_view import render_dashboard_view
from .profile_view import render_profile_view
from .analyze_view import render_analyze_view
from .audit_view import render_audit_view
from .email_view import render_email_view

__all__ = [
    "render_auth_view",
    "render_dashboard_view",
    "render_profile_view",
    "render_analyze_view",
    "render_audit_view",
    "render_email_view",
]
