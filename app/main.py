"""
CareerLens — Intelligent AI Auto Email Generator & Job Match Studio.
Streamlit application orchestrator and view router.
"""
import os
import sys
import pandas as pd
import streamlit as st

# Ensure app directory is in sys.path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from core.config import UPLOADS_DIR, ASSETS_DIR
from styles.theme import apply_custom_theme
from services.llm_chain import Chain
from services.job_loader import extract_job_posting_text
from utils.email_helpers import clean_text
import tracker

from ui import (
    render_auth_view,
    render_sidebar,
    render_dashboard_view,
    render_profile_view,
    render_analyze_view,
    render_audit_view,
    render_email_view,
)

# ---------------------------------------------------------
# Page Configuration & Clean Theme
# ---------------------------------------------------------
st.set_page_config(
    page_title="CareerLens — Job Fit & Application Studio",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_theme()

# ---------------------------------------------------------
# Authentication Gate
# ---------------------------------------------------------
if "current_user" not in st.session_state or st.session_state.current_user is None:
    auth_img_path = os.path.join(ASSETS_DIR, "career_auth_visual.jpg")
    render_auth_view(auth_img_path)
    st.stop()

# ---------------------------------------------------------
# Authenticated User Workspace Initialization
# ---------------------------------------------------------
current_user = st.session_state.current_user
user_id = current_user["id"]

if not st.session_state.get("profile_loaded"):
    user_prof = tracker.get_user_profile(user_id)
    st.session_state.user_name = user_prof.get("full_name") or current_user.get("username", "").capitalize()
    st.session_state.user_position = user_prof.get("position") or ""
    st.session_state.user_college = user_prof.get("college") or ""
    st.session_state.user_study = user_prof.get("degree") or ""
    st.session_state.candidate_type = user_prof.get("candidate_type") or "Student / Recent Graduate"
    st.session_state.custom_notes = user_prof.get("custom_notes") or ""

    if user_prof.get("portfolio"):
        st.session_state.portfolio_df = pd.DataFrame(user_prof["portfolio"])
    else:
        st.session_state.portfolio_df = None

    st.session_state.cv_filename = user_prof.get("cv_filename") or None
    st.session_state.cv_file_path = user_prof.get("cv_file_path") or None
    st.session_state.cv_file_bytes = None
    if st.session_state.cv_file_path and os.path.exists(st.session_state.cv_file_path):
        try:
            with open(st.session_state.cv_file_path, "rb") as f:
                st.session_state.cv_file_bytes = f.read()
        except Exception:
            pass

    st.session_state.job_input_mode = "Paste Job Description"
    st.session_state.job_url = ""
    st.session_state.job_text = ""
    st.session_state.recipient_email = ""
    st.session_state.generated_results = None
    st.session_state.fit_analysis_result = None
    st.session_state.current_page = "dashboard"
    st.session_state.profile_loaded = True

def save_current_user_profile():
    p_data = (
        st.session_state.portfolio_df.to_dict("records")
        if st.session_state.get("portfolio_df") is not None and not st.session_state.portfolio_df.empty
        else []
    )
    tracker.save_user_profile(
        user_id=user_id,
        full_name=st.session_state.get("user_name", ""),
        position=st.session_state.get("user_position", ""),
        college=st.session_state.get("user_college", ""),
        degree=st.session_state.get("user_study", ""),
        candidate_type=st.session_state.get("candidate_type", "Student / Recent Graduate"),
        custom_notes=st.session_state.get("custom_notes", ""),
        portfolio=p_data,
        cv_filename=st.session_state.get("cv_filename") or "",
        cv_file_path=st.session_state.get("cv_file_path") or ""
    )

def get_current_job_text() -> tuple[str, str | None]:
    if st.session_state.get("job_input_mode") == "Paste Job Description":
        text = st.session_state.get("job_text", "").strip()
        if not text:
            return "", "Please paste the job description text first."
        return text, None
    else:
        url = st.session_state.get("job_url", "").strip()
        if not url:
            return "", "Please enter a valid job posting URL."
        text, err = extract_job_posting_text(url)
        if err:
            return "", err
        return clean_text(text), None

# ---------------------------------------------------------
# Sidebar Navigation & Model Settings
# ---------------------------------------------------------
selected_model, selected_tone, selected_length = render_sidebar(save_current_user_profile)

api_key = os.getenv("API_KEY") or os.getenv("GROQ_API_KEY")
try:
    chain = Chain(model_name=selected_model, api_key=api_key)
except Exception as e:
    st.error(f"Error initializing analysis engine: {e}")
    chain = None

# ---------------------------------------------------------
# Route Views
# ---------------------------------------------------------
page = st.session_state.get("current_page", "dashboard")

if page == "dashboard":
    render_dashboard_view()
elif page == "profile":
    render_profile_view(user_id, current_user, chain, save_current_user_profile, UPLOADS_DIR)
elif page == "analyze":
    render_analyze_view(chain, get_current_job_text, api_key)
elif page == "audit":
    render_audit_view()
elif page == "email":
    render_email_view(user_id, current_user, chain, selected_tone, selected_length)
