"""
Match radar, criteria comparison breakdown, and scoring audit view for CareerLens.
"""
import streamlit as st

def render_audit_view():
    if not st.session_state.get("fit_analysis_result"):
        st.markdown('<div class="career-card" style="text-align: center; padding: 3rem 2rem;">', unsafe_allow_html=True)
        st.markdown("### No Job Analyzed Yet")
        st.markdown("Paste a job description to view your verified match score, skill breakdown, and gap analysis.")
        if st.button("Go to Job Analysis ➔", type="primary"):
            st.session_state.current_page = "analyze"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        res = st.session_state.fit_analysis_result["analysis"]
        target_job = st.session_state.fit_analysis_result["job"]
        score = res.get("match_score", 75)
        fit_level = res.get("fit_level", "Strong Match")
        strengths = res.get("matched_strengths", [])
        gaps = res.get("skill_gaps", [])
        advice = res.get("strategic_advice", "")
        evidence_breakdown = res.get("evidence_breakdown", [])
        audit_meta = res.get("audit_meta", {})

        score_color = "#10b981" if score >= 80 else ("#f59e0b" if score >= 65 else "#64748b")

        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        col_res1, col_res2 = st.columns([1, 2.2])

        with col_res1:
            st.markdown(f"""
            <div class="score-hero-card">
                <div class="score-display" style="color: {score_color};">{score}%</div>
                <div class="score-label-badge" style="background: {score_color}1a; color: {score_color}; border: 1px solid {score_color}40;">
                    {fit_level}
                </div>
                <div style="font-size: 0.78rem; color: #64748b; margin-top: 0.5rem;">Weighted Evidence Alignment</div>
            </div>
            """, unsafe_allow_html=True)

        with col_res2:
            st.markdown(f"## {target_job.get('role', 'Target Role')}")
            st.markdown(f"**Company:** {target_job.get('company', 'Target Company')}")
            domain_val = target_job.get("domain", "Technology")
            focus_items = target_job.get("key_focus_areas", [])
            focus_str = " • ".join(focus_items) if focus_items else "Core Engineering"
            
            st.markdown(f"""
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem;">
                <span class="skill-chip matched">🏷️ {domain_val}</span>
                <span class="skill-chip partial">🎯 Focus: {focus_str}</span>
            </div>
            """, unsafe_allow_html=True)

            if st.button("✉️ Draft Application Email for this Role ➔", type="primary"):
                st.session_state.current_page = "email"
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="career-card">', unsafe_allow_html=True)
        col_sk1, col_sk2 = st.columns(2)

        with col_sk1:
            st.markdown("#### ✓ Matched Skills")
            st.caption("Requirements verified with concrete evidence in your profile/CV.")
            if strengths:
                for s in strengths:
                    st.markdown(f'<span class="skill-chip matched">✓ {s}</span>', unsafe_allow_html=True)
            else:
                st.info("Found foundational alignment.")

        with col_sk2:
            st.markdown("#### ○ Skills to Develop")
            st.caption("Important requirements not found in your current profile.")
            if gaps:
                for g in gaps:
                    st.markdown(f'<span class="skill-chip gap">○ {g}</span>', unsafe_allow_html=True)
            else:
                st.success("No critical gaps identified for this role.")

        partial_items = [e for e in evidence_breakdown if "PARTIAL" in str(e.get("status", "")).upper()]
        if partial_items:
            st.markdown("<hr style='margin: 1.25rem 0; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
            st.markdown("#### ◐ Partial Matches & Scope Differences")
            st.caption("Related foundation found, but lacking specific production scale or depth demanded by this posting.")
            for p in partial_items:
                req_title = p.get("requirement", "")
                expl = p.get("explanation", "")
                st.markdown(f'<span class="skill-chip partial">◐ {req_title}</span> <span style="font-size: 0.85rem; color: #94a3b8; margin-left: 0.5rem;">— {expl}</span>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        if evidence_breakdown:
            st.markdown('<div class="career-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">📋 Requirement Comparison Breakdown</div>', unsafe_allow_html=True)
            st.caption("Item-by-item verification showing exact evidence extracted from your CV.")

            for ev in evidence_breakdown:
                req = ev.get("requirement", "")
                imp = ev.get("importance", "Core requirement")
                status = str(ev.get("status", "MISSING")).upper()
                cand_ev = ev.get("candidate_evidence", "")

                is_match = "MATCHED" in status and "PARTIAL" not in status
                is_part = "PARTIAL" in status
                is_noise = "NOT RELEVANT" in status

                stat_badge = "✓ Matched" if is_match else ("◐ Partial" if is_part else ("— Excluded Noise" if is_noise else "○ Not Found"))
                badge_class = "matched" if is_match else ("partial" if is_part else "gap")

                st.markdown(f"""
                <div class="audit-row">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                        <span style="font-weight: 700; color: #f8fafc; font-size: 0.94rem;">{req}</span>
                        <span class="skill-chip {badge_class}" style="margin: 0; padding: 0.2rem 0.6rem; font-size: 0.76rem;">{stat_badge} ({imp})</span>
                    </div>
                    <div style="font-size: 0.84rem; color: #94a3b8;">
                        <b style="color: #cbd5e1;">Profile Evidence:</b> {cand_ev if cand_ev else "No direct evidence found in uploaded resume"}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        if audit_meta:
            with st.expander("Why this match score?", expanded=False):
                c_acc = audit_meta.get("critical_accuracy", {})
                p_acc = audit_meta.get("preferred_accuracy", {})
                s_acc = audit_meta.get("soft_accuracy", {})
                formula_str = audit_meta.get("formula", "")

                st.markdown(f"""
                <div style="padding: 0.5rem 0;">
                    <p style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.6;">
                        Your match score is calculated using weighted mathematical scoring based on verified evidence in your profile:
                    </p>
                    <ul style="font-size: 0.86rem; color: #94a3b8; line-height: 1.8;">
                        <li><b>Critical Core Requirements (65% Weight):</b> {c_acc.get('percentage', 0)}% satisfied ({c_acc.get('matched', 0)} of {c_acc.get('total', 0)} verified)</li>
                        <li><b>Preferred Requirements (25% Weight):</b> {p_acc.get('percentage', 0)}% satisfied ({p_acc.get('matched', 0)} of {p_acc.get('total', 0)} verified)</li>
                        <li><b>Soft / Collaborative Skills (10% Weight):</b> {s_acc.get('percentage', 0)}% satisfied ({s_acc.get('matched', 0)} of {s_acc.get('total', 0)} verified)</li>
                    </ul>
                    <div style="font-family: monospace; font-size: 0.8rem; background: rgba(0,0,0,0.3); padding: 0.5rem 0.85rem; border-radius: 8px; color: #818cf8;">
                        Audit Calculation: {formula_str} = {score}%
                    </div>
                </div>
                """, unsafe_allow_html=True)

        if advice:
            st.markdown(f"""
            <div class="career-card" style="border-left: 4px solid #4f46e5;">
                <div style="font-weight: 700; color: #f8fafc; font-size: 0.95rem; margin-bottom: 0.35rem;">💡 Application & Interview Advice</div>
                <div style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.6;">{advice}</div>
            </div>
            """, unsafe_allow_html=True)
