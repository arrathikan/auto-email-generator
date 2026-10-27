"""
Theme and CSS tokens for CareerLens platform.
Includes responsive layout, dark canvas, glassmorphic cards, and micro-animations.
"""
import streamlit as st

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    letter-spacing: -0.01em;
}

h1, h2, h3, .career-title, .card-title {
    font-family: 'Outfit', 'Plus Jakarta Sans', sans-serif !important;
}

/* Neutral Deep Slate Canvas */
.stApp {
    background-color: #0b0f19;
    background-image: 
        radial-gradient(at 15% 15%, rgba(79, 70, 229, 0.07) 0px, transparent 50%),
        radial-gradient(at 85% 85%, rgba(14, 165, 233, 0.05) 0px, transparent 50%);
    color: #e2e8f0;
}

/* Smooth Micro-Animations (150-250ms) */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulseDot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(0.9); }
}

.animate-fade-in {
    animation: fadeIn 0.22s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

/* Career Platform Cards */
.career-card {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.35);
    transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
    animation: fadeIn 0.25s ease-out;
}

.career-card:hover {
    border-color: rgba(99, 102, 241, 0.3);
    box-shadow: 0 8px 25px -4px rgba(0, 0, 0, 0.45);
}

.card-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 0.85rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Welcome Hero Box */
.welcome-banner {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 18px;
    padding: 2rem 2.25rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}

.welcome-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #4f46e5, #06b6d4, #10b981);
}

.welcome-title {
    font-size: 1.95rem;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: -0.03em;
    margin-bottom: 0.35rem;
}

.welcome-desc {
    color: #94a3b8;
    font-size: 1rem;
    line-height: 1.55;
    max-width: 780px;
}

/* Real Status Overview Tiles (No Fake Stats) */
.status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
    margin-top: 1.25rem;
}

.status-tile {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    padding: 1rem 1.15rem;
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.status-tile:hover {
    border-color: rgba(99, 102, 241, 0.35);
    transform: translateY(-1.5px);
}

.tile-label {
    font-size: 0.76rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.3rem;
}

.tile-value {
    font-size: 1.05rem;
    font-weight: 700;
    color: #f1f5f9;
}

.tile-sub {
    font-size: 0.8rem;
    color: #94a3b8;
    margin-top: 0.2rem;
}

/* Workflow Step Indicator */
.workflow-stepper {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    margin: 1.25rem 0;
    padding: 0.85rem 1.15rem;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    align-items: center;
}

.step-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.84rem;
    font-weight: 600;
    color: #94a3b8;
}

.step-item.active {
    color: #818cf8;
}

.step-item.completed {
    color: #10b981;
}

.step-badge {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.72rem;
    font-weight: 700;
    background: rgba(255, 255, 255, 0.08);
    color: #94a3b8;
}

.step-item.active .step-badge {
    background: #4f46e5;
    color: #ffffff;
}

.step-item.completed .step-badge {
    background: #10b981;
    color: #ffffff;
}

.step-arrow {
    color: #475569;
    font-size: 0.8rem;
}

/* Accessible Skill Chips */
.skill-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.75rem;
    border-radius: 8px;
    font-size: 0.84rem;
    font-weight: 600;
    margin: 0.25rem;
    transition: transform 0.15s ease, background 0.15s ease;
}

.skill-chip:hover {
    transform: translateY(-1px);
}

.skill-chip.matched {
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #a7f3d0;
}

.skill-chip.partial {
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.35);
    color: #fde68a;
}

.skill-chip.gap {
    background: rgba(100, 116, 139, 0.15);
    border: 1px solid rgba(100, 116, 139, 0.35);
    color: #cbd5e1;
}

/* Match Score Visualization */
.score-hero-card {
    background: #0f172a;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.score-display {
    font-size: 3.2rem;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.04em;
}

.score-label-badge {
    display: inline-block;
    padding: 0.25rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.84rem;
    font-weight: 700;
    margin-top: 0.5rem;
}

/* Requirement Audit Comparison Rows */
.audit-row {
    background: rgba(15, 23, 42, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 0.85rem 1.15rem;
    margin-bottom: 0.65rem;
    transition: border-color 0.15s ease;
}

.audit-row:hover {
    border-color: rgba(255, 255, 255, 0.14);
}

/* Clean Professional Email Composer Window */
.email-composer-frame {
    background: #080c16;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    overflow: hidden;
    margin: 1rem 0 1.5rem 0;
    box-shadow: 0 16px 36px -8px rgba(0, 0, 0, 0.5);
}

.composer-toolbar {
    background: #0f172a;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding: 0.65rem 1.25rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.composer-dots {
    display: flex;
    gap: 0.4rem;
}

.composer-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
}

.composer-dot.red { background: #ef4444; }
.composer-dot.yellow { background: #f59e0b; }
.composer-dot.green { background: #10b981; }

.composer-headers {
    background: rgba(15, 23, 42, 0.4);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    padding: 0.85rem 1.35rem;
}

.composer-row {
    display: flex;
    gap: 0.65rem;
    font-size: 0.88rem;
    line-height: 1.8;
}

.composer-field-label {
    width: 60px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    font-size: 0.74rem;
}

.composer-field-value {
    color: #f1f5f9;
    font-weight: 500;
}

.composer-body {
    padding: 1.6rem 1.8rem;
    font-size: 1rem;
    line-height: 1.8;
    color: #f8fafc;
    white-space: pre-wrap;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

/* Polished Dark Form Controls */
div[data-baseweb="input"] {
    background-color: #0f172a !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
}

div[data-baseweb="input"]:focus-within {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
}

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    color: #ffffff !important;
    background-color: transparent !important;
    font-size: 0.96rem !important;
}

div.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
    padding: 0.6rem 1.4rem !important;
    transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
}

div.stButton > button:hover {
    transform: translateY(-1.5px) !important;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.35) !important;
}

div.stButton > button:active {
    transform: translateY(0) scale(0.99) !important;
}

div.stButton > button[kind="primary"] {
    background: #4f46e5 !important;
    color: #ffffff !important;
    border-color: #6366f1 !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35) !important;
}

div.stButton > button[kind="primary"]:hover {
    background: #4338ca !important;
    border-color: #818cf8 !important;
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.5) !important;
}

/* -----------------------------------------
   Auth Split-Screen System (Login & Register)
-------------------------------------------- */
.auth-split-container {
    max-width: 1180px;
    margin: 1.5rem auto 2.5rem auto;
}

.auth-visual-panel {
    background: linear-gradient(145deg, rgba(17, 24, 39, 0.95) 0%, rgba(11, 15, 25, 0.98) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 2.2rem 2rem;
    box-shadow: 0 12px 36px -8px rgba(0, 0, 0, 0.5);
    animation: fadeIn 0.25s ease-out;
}

.auth-workflow-card {
    background: #0d1322;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.65rem;
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.auth-workflow-card:hover {
    border-color: rgba(99, 102, 241, 0.35);
    transform: translateY(-1.5px);
}

.auth-node-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.4rem;
}

.auth-node-title {
    font-size: 0.92rem;
    font-weight: 700;
    color: #f1f5f9;
}

.auth-node-badge {
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.15rem 0.55rem;
    border-radius: 6px;
    background: rgba(99, 102, 241, 0.15);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.3);
}

.auth-connector {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: -0.15rem 0 0.5rem 0;
}

.auth-connector-line {
    width: 2px;
    height: 14px;
    background: linear-gradient(180deg, #4f46e5 0%, rgba(99, 102, 241, 0.25) 100%);
}

.auth-form-card {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 20px;
    padding: 2.25rem 2.2rem;
    box-shadow: 0 16px 40px -10px rgba(0, 0, 0, 0.55);
    animation: fadeIn 0.25s ease-out;
}

.auth-brand-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.85rem;
    background: rgba(79, 70, 229, 0.12);
    border: 1px solid rgba(79, 70, 229, 0.25);
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 700;
    color: #818cf8;
    margin-bottom: 0.85rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.auth-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.85rem;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: -0.03em;
    line-height: 1.2;
    margin-bottom: 0.35rem;
}

.auth-subtitle {
    font-size: 0.94rem;
    color: #94a3b8;
    margin-bottom: 1.5rem;
    line-height: 1.5;
}

.auth-strength-container {
    margin: 0.35rem 0 0.65rem 0;
}

.auth-strength-bar {
    height: 4px;
    border-radius: 2px;
    background: rgba(255, 255, 255, 0.08);
    overflow: hidden;
    margin-top: 0.35rem;
}

.auth-strength-fill {
    height: 100%;
    transition: width 0.25s ease, background-color 0.25s ease;
}

.auth-checklist {
    font-size: 0.8rem;
    color: #94a3b8;
    margin: 0.5rem 0 0.85rem 0;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.auth-check-item {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    transition: color 0.18s ease;
}

.auth-check-item.valid {
    color: #10b981;
    font-weight: 600;
}

.auth-switch-link {
    text-align: center;
    margin-top: 1.25rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    color: #94a3b8;
    font-size: 0.88rem;
}

@media (max-width: 880px) {
    .auth-visual-panel {
        padding: 1.25rem;
        margin-bottom: 1.25rem;
    }
    .auth-form-card {
        padding: 1.5rem 1.25rem;
    }
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #070a13;
    border-right: 1px solid rgba(255, 255, 255, 0.07);
}

/* Respect user accessibility motion settings */
@media (prefers-reduced-motion: reduce) {
    * {
        animation: none !important;
        transition: none !important;
    }
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""

def apply_custom_theme():
    """Injects the custom CSS into the Streamlit app."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
