"""
Dashboard overview view for CareerLens.
Displays candidate profile highlights, active analysis state, and workflow road-map.
"""
import streamlit as st

def render_dashboard_view():
    st.markdown("""
    <div class="welcome-banner">
        <div class="welcome-title">See how well your profile fits your next opportunity.</div>
        <div class="welcome-desc">
            Compare target job descriptions with your profile, identify critical skill gaps, and generate tailored, credible outreach emails.
        </div>
    </div>
    """, unsafe_allow_html=True)

    has_cv = bool(st.session_state.get("cv_filename"))
    has_skills = st.session_state.get("portfolio_df") is not None and not st.session_state.portfolio_df.empty
    skills_count = len(st.session_state.portfolio_df) if has_skills else 0
    has_analysis = st.session_state.get("fit_analysis_result") is not None
    target_role_text = st.session_state.fit_analysis_result["job"].get("role", "Ready to analyze") if has_analysis else "None yet"
    target_company_text = st.session_state.fit_analysis_result["job"].get("company", "") if has_analysis else "Paste a job to begin"

    st.markdown(f"""
    <div class="status-grid">
        <div class="status-tile">
            <div class="tile-label">Candidate Profile</div>
            <div class="tile-value">{st.session_state.get('user_name', 'Candidate')}</div>
            <div class="tile-sub">{st.session_state.get('user_position') or 'Role unassigned'} • {st.session_state.get('candidate_type', 'Candidate')}</div>
        </div>
        <div class="status-tile">
            <div class="tile-label">Resume / CV Status</div>
            <div class="tile-value">{'✓ ' + str(st.session_state.get('cv_filename')) if has_cv else '○ Pending Upload'}</div>
            <div class="tile-sub">{f'{skills_count} verified projects/skills indexed' if has_skills else 'Upload CV to extract skills'}</div>
        </div>
        <div class="status-tile">
            <div class="tile-label">Active Job Analysis</div>
            <div class="tile-value">{target_role_text}</div>
            <div class="tile-sub">{target_company_text}</div>
        </div>
        <div class="status-tile">
            <div class="tile-label">Match Score Status</div>
            <div class="tile-value">{str(st.session_state.fit_analysis_result['analysis'].get('match_score', 0)) + '%' if has_analysis else 'Not Analyzed'}</div>
            <div class="tile-sub">{st.session_state.fit_analysis_result['analysis'].get('fit_level', 'Run analysis to view') if has_analysis else 'Compare against a job'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div class="workflow-stepper">
        <div class="step-item completed">
            <div class="step-badge">1</div>
            <span>Profile & CV</span>
        </div>
        <span class="step-arrow">➔</span>
        <div class="step-item active">
            <div class="step-badge">2</div>
            <span>Job Description</span>
        </div>
        <span class="step-arrow">➔</span>
        <div class="step-item">
            <div class="step-badge">3</div>
            <span>Match & Gap Audit</span>
        </div>
        <span class="step-arrow">➔</span>
        <div class="step-item">
            <div class="step-badge">4</div>
            <span>Application Email</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_cta1, col_cta2 = st.columns([1.5, 1])
    with col_cta1:
        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        st.markdown("### Ready to evaluate a role?")
        st.markdown("Paste any job description to deconstruct its must-have requirements, calculate your weighted fit score, and highlight verified evidence.")
        if st.button("🎯 Analyze a Target Job ➔", type="primary", use_container_width=True):
            st.session_state.current_page = "analyze"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_cta2:
        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        st.markdown("### Profile & CV")
        st.markdown("Ensure your candidate background, projects, and degree are up-to-date so evidence matches accurately.")
        if st.button("👤 View / Update Profile", use_container_width=True):
            st.session_state.current_page = "profile"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
