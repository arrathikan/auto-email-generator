"""
Job description input and requirement extraction view for CareerLens.
"""
import streamlit as st
from utils.email_helpers import get_candidate_cv_text

def render_analyze_view(chain, get_current_job_text_func, api_key: str | None):
    st.markdown('<div class="career-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🎯 Analyze a Job Description</div>', unsafe_allow_html=True)
    st.markdown("Paste a job description to extract its core requirements, identify skill alignment, and detect genuine skill gaps.")

    mode_choice = st.radio(
        "Input Format:",
        options=["Paste Job Description", "Import from Job URL"],
        index=0 if st.session_state.get("job_input_mode") == "Paste Job Description" else 1,
        horizontal=True
    )
    st.session_state.job_input_mode = mode_choice

    if mode_choice == "Paste Job Description":
        st.session_state.job_text = st.text_area(
            "Job Description Text *",
            value=st.session_state.get("job_text", ""),
            height=280,
            placeholder="Paste the full job posting here (responsibilities, required qualifications, nice-to-haves)..."
        )
    else:
        st.session_state.job_url = st.text_input(
            "Target Job Posting URL *",
            value=st.session_state.get("job_url", ""),
            placeholder="https://jobs.lever.co/company/role-id or https://boards.greenhouse.io/..."
        )

    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        target_role_hint = st.text_input("Job Title (Optional — auto-detected if blank):", placeholder="e.g. Backend Software Engineer")
    with col_opt2:
        target_comp_hint = st.text_input("Company Name (Optional — auto-detected if blank):", placeholder="e.g. Stripe, OpenAI")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Analyze Job ➔", type="primary", use_container_width=True):
        if not st.session_state.get("user_name", "").strip():
            st.error("Please enter your name in the Profile tab first.")
        elif not api_key:
            st.error("Missing API key. Please check your .env configuration.")
        elif not chain:
            st.error("Analysis engine is not initialized. Please configure a valid API key.")
        else:
            job_raw_text, err = get_current_job_text_func()
            if err:
                st.error(err)
            else:
                progress_placeholder = st.empty()
                progress_placeholder.info("Reading job description...")

                try:
                    jobs = chain.extract_jobs(job_raw_text)
                    target_job = jobs[0] if jobs else {"role": target_role_hint or "Target Role", "skills": []}
                    if target_role_hint:
                        target_job["role"] = target_role_hint
                    if target_comp_hint:
                        target_job["company"] = target_comp_hint

                    progress_placeholder.info("Comparing requirements against your profile and CV evidence...")

                    portfolio_str = ""
                    if st.session_state.get("portfolio_df") is not None and not st.session_state.portfolio_df.empty:
                        for _, row in st.session_state.portfolio_df.iterrows():
                            portfolio_str += f"- Tech: {row.get('Techstack', '')} | Project: {row.get('Links', '')}\n"

                    cv_text = get_candidate_cv_text()

                    analysis = chain.analyze_job_fit(
                        job=target_job,
                        portfolio_summary=portfolio_str,
                        user_name=st.session_state.user_name,
                        user_position=st.session_state.user_position,
                        user_study=st.session_state.user_study,
                        candidate_type=st.session_state.candidate_type,
                        cv_text=cv_text
                    )

                    st.session_state.fit_analysis_result = {
                        "job": target_job,
                        "analysis": analysis
                    }

                    progress_placeholder.empty()
                    st.toast("Analysis complete!", icon="✅")
                    st.session_state.current_page = "audit"
                    st.rerun()

                except Exception as e:
                    progress_placeholder.empty()
                    st.error(f"Analysis could not be completed: {str(e)}. Please check the job description and try again.")

    st.markdown('</div>', unsafe_allow_html=True)
