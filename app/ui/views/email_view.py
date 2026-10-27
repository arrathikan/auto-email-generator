"""
Tailored application email composer, desktop mail dispatch, and SMTP transmission view.
"""
import urllib.parse
import streamlit as st
from services.portfolio import Portfolio
import mailer
from utils.email_helpers import (
    get_candidate_cv_text,
    get_installed_mail_clients,
    open_in_selected_mail_client,
    build_eml_message
)

def render_email_view(user_id: int, current_user: dict, chain, selected_tone: str, selected_length: str):
    if not st.session_state.get("fit_analysis_result"):
        st.markdown('<div class="career-card" style="text-align: center; padding: 3rem 2rem;">', unsafe_allow_html=True)
        st.markdown("### Analyze a Job First")
        st.markdown("Analyze a target job posting before generating an email so it can be personalized with verified evidence.")
        if st.button("Go to Job Analysis ➔", type="primary"):
            st.session_state.current_page = "analyze"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        target_job = st.session_state.fit_analysis_result["job"]
        role_title = target_job.get("role", "Target Position")
        company_name = target_job.get("company", "Company")

        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        col_gen1, col_gen2 = st.columns([1.6, 1])
        with col_gen1:
            st.markdown(f"### Application Email for **{role_title}** at **{company_name}**")
            st.caption("Crafted using your verified projects, genuine accomplishments, and anti-cliché phrasing.")
        with col_gen2:
            st.markdown("<div style='margin-top: 0.4rem;'>", unsafe_allow_html=True)
            draft_clicked = st.button("✉️ Draft / Regenerate Email", type="primary", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        if draft_clicked or not st.session_state.get("generated_results"):
            with st.spinner("Drafting personalized application email..."):
                try:
                    portfolio_instance = Portfolio(data=st.session_state.get("portfolio_df"), user_id=user_id) if st.session_state.get("portfolio_df") is not None else None
                    if portfolio_instance:
                        portfolio_instance.load_portfolio(clear_existing=True)

                    skills = target_job.get("skills", [])
                    matched_links = portfolio_instance.query_links(skills, n_results=3) if portfolio_instance else []
                    cv_text = get_candidate_cv_text()

                    email_result = chain.write_mail(
                        job=target_job,
                        links=matched_links,
                        user_name=st.session_state.get("user_name", "Candidate"),
                        user_college=st.session_state.get("user_college", ""),
                        user_study=st.session_state.get("user_study", ""),
                        user_position=st.session_state.get("user_position", ""),
                        tone=selected_tone,
                        length=selected_length,
                        candidate_type=st.session_state.get("candidate_type", "Student / Recent Graduate"),
                        custom_instructions=st.session_state.get("custom_notes", ""),
                        cv_text=cv_text
                    )

                    st.session_state.generated_results = [{
                        "job": target_job,
                        "matched_links": matched_links,
                        "email_data": email_result
                    }]
                    if not st.session_state.get("recipient_email") and target_job.get("contact_email"):
                        st.session_state.recipient_email = target_job.get("contact_email")

                    st.toast("Email drafted successfully.", icon="✅")
                except Exception as e:
                    st.error(f"Could not draft email: {e}")

        if st.session_state.get("generated_results"):
            item = st.session_state.generated_results[0]
            email_data = item["email_data"]
            subject_lines = email_data.get("subject_lines", [f"Application for {role_title} - {st.session_state.get('user_name', 'Candidate')}"])
            email_body = email_data.get("body", "")

            st.markdown("#### Subject Line Options")
            chosen_subject = st.radio(
                "Choose preferred subject line:",
                options=subject_lines,
                index=0,
                label_visibility="collapsed"
            )

            word_count = len(email_body.split())
            read_time = max(1, round(word_count / 150 * 60))

            view_mode = st.radio("Editor View:", ["Formatted Preview", "Text Editor"], horizontal=True)

            if view_mode == "Formatted Preview":
                st.markdown(f"""
                <div class="email-composer-frame">
                    <div class="composer-toolbar">
                        <div class="composer-dots">
                            <span class="composer-dot red"></span>
                            <span class="composer-dot yellow"></span>
                            <span class="composer-dot green"></span>
                        </div>
                        <div style="font-size: 0.78rem; color: #94a3b8; font-weight: 600;">
                            {word_count} words (~{read_time}s read)
                        </div>
                    </div>
                    <div class="composer-headers">
                        <div class="composer-row">
                            <span class="composer-field-label">To:</span>
                            <span class="composer-field-value">{st.session_state.get('recipient_email') or 'Hiring Team / Recruiter'}</span>
                        </div>
                        <div class="composer-row">
                            <span class="composer-field-label">Subject:</span>
                            <span class="composer-field-value" style="font-weight: 700; color: #f8fafc;">{chosen_subject}</span>
                        </div>
                    </div>
                    <div class="composer-body">{email_body}</div>
                </div>
                """, unsafe_allow_html=True)
                final_email_content = email_body
            else:
                final_email_content = st.text_area(
                    "Edit email content:",
                    value=email_body,
                    height=280
                )

            col_ref1, col_ref2, col_ref3, col_ref4 = st.columns(4)
            with col_ref1:
                if st.button("✂️ Make Shorter", use_container_width=True):
                    with st.spinner("Shortening email..."):
                        res = chain.write_mail(job=target_job, links=item["matched_links"], user_name=st.session_state.get("user_name"), tone=selected_tone, length="Concise & Punchy (under 120 words)", custom_instructions="Make it concise, direct, under 110 words.")
                        st.session_state.generated_results[0]["email_data"] = res
                        st.rerun()
            with col_ref2:
                if st.button("👔 More Professional", use_container_width=True):
                    with st.spinner("Adjusting tone..."):
                        res = chain.write_mail(job=target_job, links=item["matched_links"], user_name=st.session_state.get("user_name"), tone="Professional & Persuasive", custom_instructions="Professional executive tone with clean value proposition.")
                        st.session_state.generated_results[0]["email_data"] = res
                        st.rerun()
            with col_ref3:
                if st.button("💬 More Natural", use_container_width=True):
                    with st.spinner("Adjusting tone..."):
                        res = chain.write_mail(job=target_job, links=item["matched_links"], user_name=st.session_state.get("user_name"), tone="Casual & Startup-Friendly", custom_instructions="Conversational, natural phrasing, low friction.")
                        st.session_state.generated_results[0]["email_data"] = res
                        st.rerun()
            with col_ref4:
                if st.button("📋 Copy Email", use_container_width=True):
                    st.toast("Email copied to clipboard!", icon="📋")

            highlights = email_data.get("key_highlights_used", []) or target_job.get("critical_requirements", [])[:2]
            if highlights:
                st.markdown("<div style='margin-top: 1rem; padding: 0.75rem 1rem; background: rgba(255,255,255,0.03); border-radius: 10px; border: 1px solid rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
                st.markdown(f"<span style='font-size: 0.78rem; font-weight: 700; color: #818cf8; text-transform: uppercase;'>Personalized using:</span> <span style='font-size: 0.84rem; color: #cbd5e1;'>{', '.join(highlights[:3])}</span>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<hr style='margin: 1.5rem 0; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
            st.markdown("#### 🚀 Dispatch to Email Client")
            st.caption("Open pre-filled draft in your desktop mail app with your CV attached automatically.")

            col_disp1, col_disp2 = st.columns([1.5, 1])
            with col_disp1:
                st.session_state.recipient_email = st.text_input("Recipient / Recruiter Email:", value=st.session_state.get("recipient_email", ""), placeholder="e.g. hiring@company.com")
                available_clients = get_installed_mail_clients()
                client_labels = [c["label"] for c in available_clients]
                chosen_client_label = st.selectbox("Select Desktop Client:", options=client_labels, index=0)
                chosen_client = next((c for c in available_clients if c["label"] == chosen_client_label), available_clients[0])

            with col_disp2:
                st.markdown("<div style='margin-top: 1.7rem;'>", unsafe_allow_html=True)
                if st.button(f"Open in {chosen_client['name']} ➔", type="primary", use_container_width=True):
                    success, msg = open_in_selected_mail_client(
                        client_id=chosen_client["id"],
                        recipient_email=st.session_state.recipient_email,
                        subject=chosen_subject,
                        body=final_email_content,
                        attachment_path=st.session_state.get("cv_file_path"),
                        sender_email=current_user.get("email")
                    )
                    if success:
                        st.toast(f"Opened {chosen_client['name']} with draft and CV attached!", icon="🎉")
                    else:
                        st.error(msg)
                st.markdown("</div>", unsafe_allow_html=True)

            col_alt1, col_alt2 = st.columns(2)
            with col_alt1:
                safe_recip = st.session_state.recipient_email.strip()
                gmail_link = f"https://mail.google.com/mail/?view=cm&fs=1&to={urllib.parse.quote(safe_recip)}&su={urllib.parse.quote(chosen_subject)}&body={urllib.parse.quote(final_email_content)}"
                st.markdown(f'<a href="{gmail_link}" target="_blank" style="display: block; text-align: center; background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.35); color: #fca5a5; padding: 0.6rem; border-radius: 8px; font-weight: 600; text-decoration: none;">📮 Compose in Gmail Web</a>', unsafe_allow_html=True)
            with col_alt2:
                eml_data = build_eml_message(
                    recipient_email=st.session_state.recipient_email,
                    subject=chosen_subject,
                    body=final_email_content,
                    cv_bytes=st.session_state.get("cv_file_bytes"),
                    cv_name=st.session_state.get("cv_filename"),
                    sender_email=current_user.get("email")
                )
                st.download_button(
                    label="📎 Download .eml Draft (CV Attached)",
                    data=eml_data,
                    file_name=f"outreach_{role_title.replace(' ', '_').lower()}.eml",
                    mime="message/rfc822",
                    use_container_width=True
                )

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            if st.button("🚀 Send Directly via Configured SMTP", use_container_width=True):
                with st.spinner("Connecting securely to SMTP server and dispatching..."):
                    send_res = mailer.send_email_smtp(
                        user_id=user_id,
                        recipient_email=st.session_state.recipient_email,
                        subject=chosen_subject,
                        body_text=final_email_content,
                        cv_path=st.session_state.get("cv_file_path")
                    )
                    if send_res.get("success"):
                        st.toast("Email dispatched successfully via SMTP!", icon="🚀")
                        st.success("Email sent successfully via SMTP with CV attachment.")
                    else:
                        st.error(send_res.get("error", "Failed to dispatch email."))

        st.markdown('</div>', unsafe_allow_html=True)
