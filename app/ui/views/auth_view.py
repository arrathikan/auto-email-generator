"""
Authentication view for CareerLens.
Renders split-screen sign-in and registration interface with password security checks.
"""
import os
import streamlit as st
import tracker

def render_auth_view(auth_img_path: str):
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "signin"

    st.markdown('<div class="auth-split-container">', unsafe_allow_html=True)
    col_visual, col_form = st.columns([1.18, 1.0], gap="large")

    with col_visual:
        if os.path.exists(auth_img_path):
            st.image(
                auth_img_path,
                use_container_width=True,
                caption="CareerLens • Resume Verification ➔ Job Match Radar ➔ Tailored Application Email"
            )
        else:
            st.markdown("""
            <div class="welcome-banner" style="padding: 2.5rem 2rem;">
                <div class="welcome-title">CareerLens Platform</div>
                <div class="welcome-desc">
                    Compare your verified profile with real job descriptions, discover genuine skill gaps, and create persuasive application emails.
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_form:
        st.markdown('<div class="auth-form-card">', unsafe_allow_html=True)
        
        # Product Brand Header
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.65rem; margin-bottom: 0.75rem;">
            <div style="width: 34px; height: 34px; background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%); border-radius: 9px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.05rem; color: white;">
                CL
            </div>
            <div style="font-family: 'Outfit', sans-serif; font-size: 1.3rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em;">
                CareerLens
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.auth_mode == "signin":
            st.markdown("""
            <div class="auth-title">Welcome back</div>
            <div class="auth-subtitle">Sign in to continue preparing your next application.</div>
            """, unsafe_allow_html=True)

            with st.form("signin_form", clear_on_submit=False):
                login_username = st.text_input(
                    "Email or Username",
                    placeholder="name@example.com",
                    key="signin_user_input"
                )
                
                show_login_pwd = st.checkbox("Show password", key="chk_show_login_pwd")
                login_password = st.text_input(
                    "Password",
                    type="default" if show_login_pwd else "password",
                    placeholder="Enter your password",
                    key="signin_pwd_input"
                )

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                submit_signin = st.form_submit_button("Sign In ➔", type="primary", use_container_width=True)

                if submit_signin:
                    if not login_username.strip() or not login_password:
                        st.error("Please enter your email or username and password.")
                    else:
                        with st.spinner("Signing in..."):
                            success, message, user = tracker.authenticate_user(login_username, login_password)
                            if success and user:
                                st.session_state.current_user = user
                                st.session_state.profile_loaded = False
                                st.session_state.current_page = "dashboard"
                                st.toast("Signed in successfully. Welcome back!", icon="👋")
                                st.rerun()
                            else:
                                st.error("We couldn't sign you in with those details. Check your email and password and try again.")

            st.markdown('<div class="auth-switch-link">New here?</div>', unsafe_allow_html=True)
            if st.button("Create an account →", key="switch_to_signup_btn", use_container_width=True):
                st.session_state.auth_mode = "signup"
                st.rerun()

        else:
            st.markdown("""
            <div class="auth-title">Create your account</div>
            <div class="auth-subtitle">Build your profile and start comparing it with opportunities.</div>
            """, unsafe_allow_html=True)

            with st.form("signup_form", clear_on_submit=False):
                reg_username = st.text_input(
                    "Full Name or Username",
                    placeholder="e.g. Alex Rivera",
                    key="signup_user_input"
                )
                reg_email = st.text_input(
                    "Email Address",
                    placeholder="e.g. alex@example.com",
                    key="signup_email_input"
                )

                show_reg_pwd = st.checkbox("Show password", key="chk_show_reg_pwd")
                reg_password = st.text_input(
                    "Password (min 6 characters)",
                    type="default" if show_reg_pwd else "password",
                    placeholder="Create a secure password",
                    key="signup_pwd_input"
                )
                reg_confirm = st.text_input(
                    "Confirm Password",
                    type="default" if show_reg_pwd else "password",
                    placeholder="Re-enter your password",
                    key="signup_confirm_input"
                )

                pwd_val = reg_password or ""
                has_len = len(pwd_val) >= 6
                has_upper = any(c.isupper() for c in pwd_val)
                has_digit = any(c.isdigit() for c in pwd_val)
                
                score = 0
                if len(pwd_val) >= 6: score += 1
                if len(pwd_val) >= 8: score += 1
                if has_upper: score += 1
                if has_digit: score += 1
                
                if score <= 1:
                    strength_label, strength_color, strength_pct = "Basic", "#ef4444", 25
                elif score <= 2:
                    strength_label, strength_color, strength_pct = "Moderate", "#f59e0b", 60
                else:
                    strength_label, strength_color, strength_pct = "Strong", "#10b981", 100

                if pwd_val:
                    st.markdown(f"""
                    <div class="auth-strength-container">
                        <div style="display: flex; justify-content: space-between; font-size: 0.74rem; color: #94a3b8; font-weight: 600;">
                            <span>Password Strength</span>
                            <span style="color: {strength_color};">{strength_label}</span>
                        </div>
                        <div class="auth-strength-bar">
                            <div class="auth-strength-fill" style="width: {strength_pct}%; background-color: {strength_color};"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="auth-checklist">
                    <div class="auth-check-item {'valid' if has_len else ''}">
                        {'✓' if has_len else '○'} At least 6 characters
                    </div>
                    <div class="auth-check-item {'valid' if has_upper else ''}">
                        {'✓' if has_upper else '○'} Uppercase letter (recommended)
                    </div>
                    <div class="auth-check-item {'valid' if has_digit else ''}">
                        {'✓' if has_digit else '○'} Number (recommended)
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                submit_signup = st.form_submit_button("Create Account ➔", type="primary", use_container_width=True)

                if submit_signup:
                    u_clean = reg_username.strip()
                    e_clean = reg_email.strip().lower()
                    p_clean = reg_password

                    if not u_clean or not e_clean or not p_clean:
                        st.error("Please fill in all required fields.")
                    elif len(u_clean) < 3:
                        st.error("Username or name must be at least 3 characters long.")
                    elif "@" not in e_clean or "." not in e_clean:
                        st.error("Please provide a valid email address.")
                    elif len(p_clean) < 6:
                        st.error("Password must be at least 6 characters long.")
                    elif p_clean != reg_confirm:
                        st.error("Passwords do not match yet. Please verify and try again.")
                    else:
                        with st.spinner("Creating account..."):
                            success, message, user = tracker.register_user(u_clean, e_clean, p_clean)
                            if success and user:
                                st.session_state.current_user = user
                                st.session_state.profile_loaded = False
                                st.session_state.current_page = "profile"
                                st.toast("Account created! Let's set up your profile and upload your CV.", icon="🎉")
                                st.rerun()
                            else:
                                st.error(message)

            st.markdown('<div class="auth-switch-link">Already have an account?</div>', unsafe_allow_html=True)
            if st.button("Sign in to your account →", key="switch_to_signin_btn", use_container_width=True):
                st.session_state.auth_mode = "signin"
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
