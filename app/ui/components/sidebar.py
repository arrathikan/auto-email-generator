"""
Sidebar navigation, model preferences, and session controls.
"""
import os
import streamlit as st

def render_sidebar(save_profile_callback) -> tuple[str, str, str]:
    """
    Renders the app sidebar and returns (selected_model, selected_tone, selected_length).
    """
    with st.sidebar:
        st.markdown("""
        <div style="padding: 0.5rem 0 1rem 0;">
            <div style="font-size: 1.25rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em; display: flex; align-items: center; gap: 0.5rem;">
                💼 CareerLens
            </div>
            <div style="font-size: 0.78rem; color: #94a3b8;">Job Fit & Application Studio</div>
        </div>
        """, unsafe_allow_html=True)

        user_name = st.session_state.get("user_name", "Candidate")
        user_initials = "".join([part[0].upper() for part in user_name.split() if part])[:2] or "CA"
        cv_name = st.session_state.get("cv_filename")
        cv_status_text = f"Attached ({cv_name})" if cv_name else "Not uploaded"
        cv_status_color = "#10b981" if cv_name else "#f59e0b"

        st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 12px; padding: 0.85rem; margin-bottom: 1.25rem;">
            <div style="display: flex; align-items: center; gap: 0.65rem;">
                <div style="width: 36px; height: 36px; border-radius: 8px; background: #4f46e5; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.95rem;">
                    {user_initials}
                </div>
                <div style="flex: 1; min-width: 0;">
                    <div style="font-size: 0.92rem; font-weight: 700; color: #f8fafc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        {user_name}
                    </div>
                    <div style="font-size: 0.76rem; color: #94a3b8;">
                        CV: <span style="color: {cv_status_color}; font-weight: 600;">{cv_status_text}</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Navigation")
        
        nav_map = {
            "dashboard": "🏠 Dashboard",
            "profile": "👤 Profile / CV",
            "analyze": "🎯 Analyze Job",
            "audit": "📊 Match & Gap Audit",
            "email": "✉️ Application Email"
        }

        current_idx = list(nav_map.keys()).index(st.session_state.get("current_page", "dashboard")) if st.session_state.get("current_page") in nav_map else 0

        selected_nav_label = st.radio(
            "Go to page:",
            options=list(nav_map.values()),
            index=current_idx,
            label_visibility="collapsed"
        )

        for k, v in nav_map.items():
            if v == selected_nav_label:
                st.session_state.current_page = k
                break

        st.markdown("<hr style='margin: 1.25rem 0; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

        with st.expander("⚙️ Preferences & Tone", expanded=False):
            selected_model = st.selectbox(
                "Model:",
                options=[
                    "openai/gpt-oss-120b",
                    "openai/gpt-oss-20b",
                    "qwen/qwen3.8-27b",
                    "groq/compound-mini",
                    "groq/compound",
                    "qwen/qwen3.6-27b"
                ],
                index=0,
                help="Language model used for requirement extraction and outreach drafting."
            )
            selected_tone = st.selectbox(
                "Outreach Tone:",
                options=[
                    "Professional & Persuasive (Recommended)",
                    "Enthusiastic & Academic",
                    "Casual & Startup-Friendly",
                    "Confident Executive",
                    "Short & Direct / No Fluff"
                ],
                index=0
            )
            selected_length = st.selectbox(
                "Email Length:",
                options=[
                    "Standard (120-180 words)",
                    "Concise & Punchy (under 120 words)",
                    "Comprehensive (200+ words)"
                ],
                index=0
            )

        col_save, col_clear = st.columns(2)
        with col_save:
            if st.button("💾 Save", use_container_width=True, help="Saves your current profile and settings"):
                save_profile_callback()
                st.toast("Profile saved successfully.", icon="✅")
        with col_clear:
            if st.button("🔄 Reset", use_container_width=True, help="Clears analyzed job and drafts"):
                for k in ["job_text", "job_url", "recipient_email", "generated_results", "fit_analysis_result"]:
                    if k in st.session_state:
                        st.session_state[k] = "" if "text" in k or "url" in k or "email" in k else None
                st.session_state.current_page = "analyze"
                st.rerun()

        st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.profile_loaded = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    return selected_model, selected_tone, selected_length
