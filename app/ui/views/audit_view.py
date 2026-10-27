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
            st.markdown('<div class="card-title">📋 Structured Requirement Breakdown & Evidence Audit</div>', unsafe_allow_html=True)
            st.caption("Item-by-item verification comparing job requirements against uploaded CV evidence with technical normalization.")

            # Filter or group by Category
            categories = [
                "All Categories",
                "Critical Technical Skill",
                "Preferred Technical Skill",
                "Experience Requirement",
                "Educational Qualification",
                "Soft Skill"
            ]
            selected_cat = st.selectbox("Filter Requirements by Category:", categories, index=0)

            filtered_evidence = [
                e for e in evidence_breakdown 
                if selected_cat == "All Categories" or str(e.get("category", "")).strip().lower() == selected_cat.lower()
            ]

            for idx, ev in enumerate(filtered_evidence):
                req = ev.get("requirement", "")
                cat = ev.get("category", "General Requirement")
                imp = ev.get("importance", "Core requirement")
                status = str(ev.get("status", "MISSING")).upper()
                exact_passage = ev.get("supporting_evidence", "")
                cand_ev = ev.get("candidate_evidence", "")
                explanation = ev.get("explanation", "")
                confidence = ev.get("confidence", "Medium")
                uncertainty = ev.get("uncertainty", 0.15)
                uncertainty_pct = int(round(float(uncertainty) * 100)) if uncertainty is not None else 15

                is_match = "MATCHED" in status and "PARTIAL" not in status
                is_part = "PARTIAL" in status
                is_noise = "NOT RELEVANT" in status

                stat_badge = "✓ Matched" if is_match else ("◐ Partially Matched" if is_part else ("— Excluded Noise" if is_noise else "○ Missing"))
                badge_class = "matched" if is_match else ("partial" if is_part else "gap")
                conf_color = "#10b981" if confidence.lower() == "high" else ("#f59e0b" if confidence.lower() == "medium" else "#ef4444")

                st.markdown(f"""
                <div class="audit-row" style="margin-bottom: 0.75rem; border-left: 3px solid {conf_color};">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.4rem;">
                        <div>
                            <span style="font-weight: 700; color: #f8fafc; font-size: 1rem;">{req}</span>
                            <span style="font-size: 0.75rem; color: #94a3b8; margin-left: 0.5rem; background: rgba(255,255,255,0.06); padding: 0.15rem 0.5rem; border-radius: 4px;">{cat}</span>
                        </div>
                        <div style="display: flex; gap: 0.4rem; align-items: center;">
                            <span class="skill-chip {badge_class}" style="margin: 0; padding: 0.2rem 0.65rem; font-size: 0.78rem;">{stat_badge}</span>
                            <span style="font-size: 0.72rem; color: {conf_color}; background: {conf_color}18; padding: 0.18rem 0.5rem; border-radius: 4px; border: 1px solid {conf_color}33;">
                                {confidence} Conf (±{uncertainty_pct}%)
                            </span>
                        </div>
                    </div>
                    <div style="font-size: 0.85rem; color: #cbd5e1; margin-bottom: 0.25rem;">
                        <b>Assessment:</b> {explanation if explanation else cand_ev}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Expandable Evidence View
                with st.expander(f"🔍 Supporting CV Passage & Verification Details — {req}", expanded=False):
                    col_ev1, col_ev2 = st.columns([1.5, 1])
                    with col_ev1:
                        st.markdown("**Exact Supporting CV Passage:**")
                        if exact_passage:
                            st.markdown(f"""
                            <div style="background: rgba(15, 23, 42, 0.7); border-left: 3px solid #6366f1; padding: 0.65rem 0.9rem; border-radius: 6px; font-size: 0.84rem; color: #e2e8f0; font-family: monospace; white-space: pre-wrap;">
{exact_passage}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="background: rgba(15, 23, 42, 0.4); border-left: 3px solid #64748b; padding: 0.5rem 0.8rem; border-radius: 6px; font-size: 0.82rem; color: #94a3b8; font-style: italic;">
                                No exact supporting CV passage identified in candidate profile.
                            </div>
                            """, unsafe_allow_html=True)

                    with col_ev2:
                        st.markdown("**Audit Metadata:**")
                        st.markdown(f"""
                        <ul style="font-size: 0.8rem; color: #94a3b8; line-height: 1.7; padding-left: 1.2rem; margin: 0;">
                            <li><b>Requirement:</b> {req}</li>
                            <li><b>Category:</b> {cat}</li>
                            <li><b>Importance:</b> {imp}</li>
                            <li><b>Match Status:</b> <span style="color: {'#10b981' if is_match else ('#f59e0b' if is_part else '#ef4444')};">{status}</span></li>
                            <li><b>Model Confidence:</b> {confidence}</li>
                            <li><b>Uncertainty Metric:</b> ±{uncertainty_pct}%</li>
                        </ul>
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
                        <li><b>Critical Core Requirements (65% Weight):</b> {c_acc.get('percentage', 0)}% satisfied ({c_acc.get('matched', 0)} of {c_acc.get('total', 0)} verified) — includes Critical Technical Skills, Experience Requirements, and Educational Qualifications</li>
                        <li><b>Preferred Requirements (25% Weight):</b> {p_acc.get('percentage', 0)}% satisfied ({p_acc.get('matched', 0)} of {p_acc.get('total', 0)} verified) — includes Preferred Technical Skills</li>
                        <li><b>Soft / Collaborative Skills (10% Weight):</b> {s_acc.get('percentage', 0)}% satisfied ({s_acc.get('matched', 0)} of {s_acc.get('total', 0)} verified) — includes Teamwork & Interpersonal Competencies</li>
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
