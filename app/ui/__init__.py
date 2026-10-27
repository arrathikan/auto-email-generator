"""
Streamlit user interface module for CareerLens.
"""
from .components.sidebar import render_sidebar
from .views.auth_view import render_auth_view
from .views.dashboard_view import render_dashboard_view
from .views.profile_view import render_profile_view
from .views.analyze_view import render_analyze_view
from .views.audit_view import render_audit_view
from .views.email_view import render_email_view

__all__ = [
    "render_sidebar",
    "render_auth_view",
    "render_dashboard_view",
    "render_profile_view",
    "render_analyze_view",
    "render_audit_view",
    "render_email_view",
]
