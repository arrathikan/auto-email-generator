"""
Profile, CV vault, technical skills, and SMTP configuration view for CareerLens.
"""
import os
import pandas as pd
import streamlit as st
import tracker
from utils.email_helpers import process_cv_to_dataframe, extract_text_from_file

def render_profile_view(user_id: int, current_user: dict, chain, save_profile_callback, upload_dir: str):
    st.markdown('<div class="career-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">👤 Candidate Profile & CV Vault</div>', unsafe_allow_html=True)

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.session_state.user_name = st.text_input("Full Name *", value=st.session_state.user_name, placeholder="e.g. Jane Doe")
        st.session_state.user_position = st.text_input("Current / Target Job Title", value=st.session_state.user_position, placeholder="e.g. Software Engineer, Data Scientist")
        st.session_state.candidate_type = st.selectbox(
            "Experience Level / Category",
            options=["Student / Recent Graduate", "Experienced Professional", "Career Switcher", "Freelancer / Consultant"],
            index=["Student / Recent Graduate", "Experienced Professional", "Career Switcher", "Freelancer / Consultant"].index(st.session_state.candidate_type) if st.session_state.candidate_type in ["Student / Recent Graduate", "Experienced Professional", "Career Switcher", "Freelancer / Consultant"] else 0
        )
    with col_p2:
        st.session_state.user_college = st.text_input("University / College", value=st.session_state.user_college, placeholder="e.g. Stanford University")
        st.session_state.user_study = st.text_input("Degree / Major", value=st.session_state.user_study, placeholder="e.g. B.S. in Computer Science")
        st.session_state.custom_notes = st.text_input("Key Accomplishments / Focus Areas", value=st.session_state.custom_notes, placeholder="e.g. Distributed backend systems, open-source contributor")

    st.markdown("<hr style='margin: 1.25rem 0; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

    st.markdown("#### 📄 Upload Your Resume / CV")
    st.caption("Upload your CV in PDF or DOCX format. Your verified technical skills and project citations will be extracted automatically.")

    uploaded_file = st.file_uploader("Select CV file", type=["pdf", "docx", "csv"], label_visibility="collapsed")
    if uploaded_file is not None:
        save_path = os.path.join(upload_dir, f"{user_id}_{uploaded_file.name}")
        with open(save_path, "wb") as f_out:
            f_out.write(uploaded_file.getbuffer())

        st.session_state.cv_filename = uploaded_file.name
        st.session_state.cv_file_path = save_path
        st.session_state.cv_file_bytes = uploaded_file.getvalue()

        with st.spinner("Processing CV and indexing your projects..."):
            try:
                extracted_df = process_cv_to_dataframe(uploaded_file, chain)
                st.session_state.portfolio_df = extracted_df
                save_profile_callback()
                st.toast("CV processed and saved to memory.", icon="✅")
            except Exception as e:
                st.error(f"Could not parse file: {e}")

    if st.session_state.get("cv_filename"):
        col_cv_stat1, col_cv_stat2 = st.columns([1.6, 1])
        with col_cv_stat1:
            st.markdown(f'<div class="status-tile"><div class="tile-label">Active CV File</div><div class="tile-value">📎 {st.session_state.cv_filename}</div><div class="tile-sub">Ready to attach in desktop email clients.</div></div>', unsafe_allow_html=True)
        with col_cv_stat2:
            st.markdown("<div style='margin-top: 0.5rem;'>", unsafe_allow_html=True)
            if st.button("🪄 Auto-Fill Details from CV", use_container_width=True, help="Extracts name, title, degree, and skills from your uploaded file"):
                if st.session_state.cv_file_path and os.path.isfile(st.session_state.cv_file_path):
                    with st.spinner("Extracting profile details..."):
                        with open(st.session_state.cv_file_path, "rb") as f_cv:
                            cv_raw_text = extract_text_from_file(f_cv)
                        if cv_raw_text and chain:
                            p_info = chain.parse_candidate_profile_from_cv(cv_raw_text)
                            if p_info.get("full_name") and p_info["full_name"] != "Candidate":
                                st.session_state.user_name = p_info["full_name"]
                            if p_info.get("position"):
                                st.session_state.user_position = p_info["position"]
                            if p_info.get("college"):
                                st.session_state.user_college = p_info["college"]
                            if p_info.get("degree"):
                                st.session_state.user_study = p_info["degree"]
                            if p_info.get("candidate_type"):
                                st.session_state.candidate_type = p_info["candidate_type"]
                            if p_info.get("portfolio"):
                                st.session_state.portfolio_df = pd.DataFrame(p_info["portfolio"])
                            save_profile_callback()
                            st.toast("Profile details updated from CV.", icon="🪄")
                            st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 💼 Verified Technical Skills & Project Links")
    st.caption("These items provide verified evidence when matching against job postings and tailoring email citations.")

    if st.session_state.get("portfolio_df") is not None and not st.session_state.portfolio_df.empty:
        edited_df = st.data_editor(
            st.session_state.portfolio_df,
            num_rows="dynamic",
            use_container_width=True,
            key="portfolio_editor"
        )
        st.session_state.portfolio_df = edited_df
    else:
        st.info("Upload your resume above to automatically index your skills and projects.")

    if st.button("💾 Save Profile Changes", type="primary"):
        save_profile_callback()
        st.toast("Profile saved successfully.", icon="✅")

    st.markdown("<hr style='margin: 1.5rem 0; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
    with st.expander("🔐 SMTP Email Settings & Direct Dispatch (Encrypted)"):
        st.caption("Store your email credentials securely using authenticated encryption (AES-128-CBC + HMAC-SHA256). Passwords are never stored in plaintext.")
        mail_cfg = tracker.get_user_mail_config(user_id)
        c_smtp1, c_smtp2 = st.columns(2)
        with c_smtp1:
            smtp_user = st.text_input("Sender Email Address", value=mail_cfg.get("email_address", current_user.get("email", "")), key="smtp_email_input")
            smtp_host = st.text_input("SMTP Host (leave blank to auto-detect)", value=mail_cfg.get("smtp_host", ""), placeholder="e.g. smtp.gmail.com", key="smtp_host_input")
        with c_smtp2:
            has_pwd = bool(mail_cfg.get("app_password"))
            pwd_placeholder = "•••••••••••••••• (Leave blank to keep existing)" if has_pwd else "Enter 16-character App Password"
            new_smtp_pwd = st.text_input("App Password", type="password", placeholder=pwd_placeholder, key="smtp_pwd_input", help="For Gmail, create an App Password in your Google Account security settings.")
            smtp_port = st.number_input("SMTP Port", value=int(mail_cfg.get("smtp_port") or 465), step=1, key="smtp_port_input")

        if st.button("Save Encrypted SMTP Credentials", key="btn_save_smtp"):
            tracker.save_user_mail_config(
                user_id=user_id,
                email_address=smtp_user,
                app_password=new_smtp_pwd,
                smtp_host=smtp_host,
                smtp_port=smtp_port
            )
            st.toast("SMTP credentials encrypted and saved successfully.", icon="🔐")

    st.markdown('</div>', unsafe_allow_html=True)
