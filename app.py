"""
app.py — CFA Learning Assistant main entry point.
"""

import os
import sys
import base64
from pathlib import Path

# ── Path setup ──────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Load env before imports ─────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# ── Page config (must be first Streamlit call) ───────────────────
st.set_page_config(
    page_title="CFA Learning Assistant",
    page_icon=str(ROOT / "assets" / "logo.png"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Load custom CSS early (Must load early so browser parses sidebar rules immediately) ──
css_path = ROOT / "assets" / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ── Inject Landing Page Indicator for visitors ───────────────────
if not st.session_state.get("logged_in", False):
    st.markdown("<div class='landing-page-indicator'></div>", unsafe_allow_html=True)

# ── DB init ──────────────────────────────────────────────────────
from database.db import init_db
from database.seeder import auto_seed_default_bank
init_db()
auto_seed_default_bank()

# ── Auth ─────────────────────────────────────────────────────────
from utils.auth import is_logged_in, render_auth_page, logout_user, get_current_user
from database.db import is_onboarding_done, get_user_profile
from utils.i18n import t, get_lang, set_lang

# (No query-param handler needed — logo uses href="/" for a fresh-session navigation)


# ── Logo helper ───────────────────────────────────────────────────
def _logo_b64() -> str:
    """Return base64-encoded logo PNG for inline HTML embedding."""
    logo_path = ROOT / "assets" / "logo.png"
    if logo_path.exists():
        return base64.b64encode(logo_path.read_bytes()).decode()
    return ""

# ── Auto-redirect logged-in users ────────────────────────────────
# If the user is already logged in, skip the landing page entirely
# and send them to the correct page based on onboarding status.
if is_logged_in():
    user = get_current_user()
    if user:
        if not is_onboarding_done(user["id"]):
            st.switch_page("pages/0_Onboarding.py")
            st.stop()
        else:
            st.switch_page("pages/1_Dashboard.py")
            st.stop()

# ── Clear any stale auth overlay state (e.g. after logout) ────────
# Ensures landing page is shown cleanly, not a login/register form.
if st.session_state.get("show_auth") and not is_logged_in():
    pass  # show_auth will be read below from nav button clicks

# ── Top Navigation Bar ───────────────────────────────────────────────
# Layout: [Logo  (left)] ──────────── [🇬🇧] [🇻🇳]  |  [Sign In]  [Sign Up]
nav_col_logo, nav_col_right = st.columns([3.8, 2.8])

with nav_col_logo:
    _logo = _logo_b64()
    _logo_html = (
        f'<img src="data:image/png;base64,{_logo}" '
        f'style="height:36px; width:36px; object-fit:contain; border-radius:6px; vertical-align:middle;" />'
        if _logo else '<span style="font-size:1.6rem; vertical-align:middle;">📊</span>'
    )
    st.markdown(
        f"""
        <div style="padding: 0.4rem 0;">
            <a href="/" target="_self" style="text-decoration:none; display:inline-flex; align-items:center; gap:0.6rem;">
                {_logo_html}
                <span style="font-size:1.4rem; font-weight:800;
                             background: linear-gradient(135deg,#6366f1,#06b6d4);
                             -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                             line-height:1.2; display:inline-block; vertical-align:middle;">
                    CFA Assistant
                </span>
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

with nav_col_right:
    # 5-column micro-grid:  [🇬🇧] [🇻🇳] [gap] [Sign In] [Sign Up]
    _lang = get_lang()
    rc1, rc2, rc_gap, rc3, rc4 = st.columns([0.6, 0.6, 0.15, 1.0, 1.2])
    with rc1:
        _t_en = "primary" if _lang == "en" else "secondary"
        if st.button("🇬🇧", key="lang_en", use_container_width=True, type=_t_en, help="English"):
            set_lang("en")
            st.rerun()
    with rc2:
        _t_vi = "primary" if _lang == "vi" else "secondary"
        if st.button("🇻🇳", key="lang_vi", use_container_width=True, type=_t_vi, help="Tiếng Việt"):
            set_lang("vi")
            st.rerun()
    with rc3:
        if st.button(t("sign_in"), key="nav_signin", use_container_width=True):
            st.session_state["show_auth"] = "login"
            st.rerun()
    with rc4:
        if st.button(t("sign_up"), key="nav_signup", use_container_width=True, type="primary"):
            st.session_state["show_auth"] = "register"
            st.rerun()

st.markdown("---")

# ── Auth Overlay Mode ────────────────────────────────────────────────
show_auth = st.session_state.get("show_auth")

if show_auth == "login":
    col_l, col_center, col_r = st.columns([1, 1.5, 1])
    with col_center:
        st.markdown('<div class="cfa-card" style="margin-top:2rem; border-color:#6366f1;">', unsafe_allow_html=True)
        st.markdown("<h3 style='text-align:center; color:#f1f5f9;'>🔐 " + t("sign_in") + "</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:#64748b; font-size:0.85rem; margin-top:-0.5rem;'>{t('access_portal')}</p>", unsafe_allow_html=True)

        admin_mode = st.toggle("🔒 Admin Sign In", key="login_admin_mode_landing")

        with st.form("landing_login_form"):
            if admin_mode:
                st.markdown(
                    "<p style='color:#818cf8;font-size:0.82rem;'>🔑 Enter administrator credentials below</p>",
                    unsafe_allow_html=True,
                )
            username = st.text_input(t("username"), placeholder=t("enter_username"))
            password = st.text_input(t("password"), type="password", placeholder=t("enter_password"))
            submitted = st.form_submit_button(t("sign_in"), use_container_width=True, type="primary")

            if submitted:
                if not username or not password:
                    st.error(t("fill_both_fields"))
                else:
                    from utils.auth import (
                        get_admin_credentials, get_user_by_username,
                        verify_password, login_user, hash_password,
                    )
                    from database.db import create_user

                    try:
                        admin_user, admin_pass = get_admin_credentials()
                    except RuntimeError:
                        admin_user, admin_pass = None, None

                    if admin_user and username == admin_user and password == admin_pass:
                        user = get_user_by_username(username)
                        if not user:
                            hashed = hash_password(password)
                            create_user(username, hashed, "admin@cfa-assistant.com", 3, "")
                            user = get_user_by_username(username)
                        login_user(user)
                        st.session_state["show_auth"] = None
                        st.switch_page("pages/1_Dashboard.py")
                    else:
                        user = get_user_by_username(username)
                        if user and verify_password(password, user["password"]):
                            login_user(user)
                            st.session_state["show_auth"] = None
                            if is_onboarding_done(user["id"]):
                                st.switch_page("pages/1_Dashboard.py")
                            else:
                                st.switch_page("pages/0_Onboarding.py")
                        else:
                            st.error(t("invalid_credentials"))

        if st.button(t("cancel"), use_container_width=True, key="cancel_login"):
            st.session_state["show_auth"] = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

elif show_auth == "register":
    col_l, col_center, col_r = st.columns([1, 1.5, 1])
    with col_center:
        st.markdown('<div class="cfa-card" style="margin-top:1rem; border-color:#06b6d4;">', unsafe_allow_html=True)
        st.markdown("<h3 style='text-align:center; color:#f1f5f9;'>📝 " + t("create_account") + "</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:#64748b; font-size:0.85rem; margin-top:-0.5rem;'>{t('start_journey')}</p>", unsafe_allow_html=True)

        with st.form("landing_register_form"):
            new_username = st.text_input(t("username"), placeholder=t("enter_username"))
            new_email = st.text_input(t("email_required"), placeholder="your@email.com")
            new_phone = st.text_input(t("phone_optional"), placeholder="e.g. +84901234567")
            new_password = st.text_input(t("password"), type="password", placeholder=t("min_6_chars"))
            confirm_password = st.text_input(t("confirm_password"), type="password")
            cfa_level = st.selectbox(t("cfa_level_focus"), [1, 2, 3])
            submitted = st.form_submit_button(t("create_account"), use_container_width=True, type="primary")

            if submitted:
                from utils.auth import validate_email_typos
                email_err = validate_email_typos(new_email)
                if not new_username or not new_password:
                    st.error(t("username_required"))
                elif email_err:
                    st.error(email_err)
                elif len(new_password) < 6:
                    st.error(t("password_min"))
                elif new_password != confirm_password:
                    st.error(t("passwords_no_match"))
                else:
                    from utils.auth import hash_password
                    from database.db import create_user
                    from utils.email_sender import send_welcome_email
                    hashed = hash_password(new_password)
                    user_id = create_user(new_username, hashed, new_email, cfa_level, new_phone)
                    if user_id:
                        from utils.auth import get_user_by_username, login_user
                        user = get_user_by_username(new_username)
                        
                        # Send auto welcome email
                        send_welcome_email(new_email, new_username)
                        
                        login_user(user)
                        
                        # Set welcome notification message flag in session state
                        st.session_state["show_welcome_noti"] = new_email
                        
                        st.session_state["show_auth"] = None
                        # ── Feature 1: new users always go to Onboarding ──
                        st.switch_page("pages/0_Onboarding.py")
                    else:
                        st.error(t("username_taken"))

        if st.button(t("cancel"), use_container_width=True, key="cancel_register"):
            st.session_state["show_auth"] = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ── LANDING PAGE CONTENT (visitors only) ─────────────────────────────────────
st.markdown(
    f"""
    <div style="text-align:center; padding: 3rem 1rem 4rem;">
        <span class="badge badge-high" style="margin-bottom:1rem; padding: 4px 14px;">{t('hero_badge')}</span>
        <h1 style="font-size:3.5rem; font-weight:800; line-height:1.2;
                    background: linear-gradient(135deg,#f1f5f9,#94a3b8,#818cf8);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                    max-width:850px; margin: 0 auto 1.5rem;">
            {t('hero_title')}
        </h1>
        <p style="color:#94a3b8; font-size:1.15rem; max-width:680px; margin:0 auto 2.5rem; line-height:1.6;">
            {t('hero_subtitle')}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Hero CTA button
col_btn1, col_btn_c, col_btn2 = st.columns([2, 1.2, 2])
with col_btn_c:
    if st.button(t("get_started"), use_container_width=True, type="primary", key="hero_cta"):
        st.session_state["show_auth"] = "register"
        st.rerun()

st.markdown("<br><br><br>", unsafe_allow_html=True)

# ── Feature Grid ─────────────────────────────────────────────────────
st.markdown(f"<h3 style='text-align:center; color:#f1f5f9; margin-bottom:2rem;'>{t('features_title')}</h3>", unsafe_allow_html=True)
col_feat1, col_feat2, col_feat3 = st.columns(3)

with col_feat1:
    st.markdown(
        f"""
        <div class="cfa-card" style="height:100%; padding:2rem; border-color:#818cf8; text-align:center;">
            <div style="font-size:3rem; margin-bottom:1rem;">🎯</div>
            <h4 style="color:#f1f5f9; font-weight:700; margin-bottom:0.8rem;">{t('feat1_title')}</h4>
            <p style="color:#94a3b8; font-size:0.88rem; line-height:1.6;">
                {t('feat1_desc')}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_feat2:
    st.markdown(
        f"""
        <div class="cfa-card" style="height:100%; padding:2rem; border-color:#06b6d4; text-align:center;">
            <div style="font-size:3rem; margin-bottom:1rem;">🤖</div>
            <h4 style="color:#f1f5f9; font-weight:700; margin-bottom:0.8rem;">{t('feat2_title')}</h4>
            <p style="color:#94a3b8; font-size:0.88rem; line-height:1.6;">
                {t('feat2_desc')}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_feat3:
    st.markdown(
        f"""
        <div class="cfa-card" style="height:100%; padding:2rem; border-color:#10b981; text-align:center;">
            <div style="font-size:3rem; margin-bottom:1rem;">📅</div>
            <h4 style="color:#f1f5f9; font-weight:700; margin-bottom:0.8rem;">{t('feat3_title')}</h4>
            <p style="color:#94a3b8; font-size:0.88rem; line-height:1.6;">
                {t('feat3_desc')}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br><br><br><hr style='border-color:#334155;'><br>", unsafe_allow_html=True)

# ── Detailed Deep Dives ──────────────────────────────────────────────
st.markdown(f"<h3 style='text-align:center; color:#f1f5f9; margin-bottom:3rem;'>{t('inside_ecosystem')}</h3>", unsafe_allow_html=True)

# Row 1
col_r1_text, col_r1_vis = st.columns([1.2, 1])
with col_r1_text:
    st.markdown(
        f"""
        <div style="padding:1rem 0;">
            <span class="badge badge-medium" style="margin-bottom:0.8rem;">Adaptive Q-Bank</span>
            <h3 style="color:#f1f5f9; font-weight:700;">{t('land_deep_dive_title1')}</h3>
            <p style="color:#94a3b8; font-size:0.95rem; line-height:1.6; margin-top:1rem;">
                {t('land_deep_dive_desc1')}
            </p>
            <ul style="color:#64748b; font-size:0.85rem; padding-left:1.2rem; line-height:1.8; margin-top:1rem;">
                <li>{t('land_deep_dive_li1_1')}</li>
                <li>{t('land_deep_dive_li1_2')}</li>
                <li>{t('land_deep_dive_li1_3')}</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_r1_vis:
    st.markdown(
        f"""
        <div class="cfa-card" style="background:#1e293b; padding:1.5rem; border-color:#334155; margin-top:1.5rem;">
            <div style="font-size:0.8rem; text-transform:uppercase; color:#64748b; letter-spacing:0.05em; margin-bottom:0.8rem;">{t('land_map_perf_title')}</div>
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #334155; padding:0.5rem 0;">
                <span style="color:#f1f5f9; font-size:0.88rem;">📊 {t('land_map_fsa')}</span>
                <span class="badge badge-high">35% Avg</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #334155; padding:0.5rem 0;">
                <span style="color:#f1f5f9; font-size:0.88rem;">⚖️ {t('land_map_ethics')}</span>
                <span class="badge badge-medium" style="background:rgba(245,158,11,0.1); color:#fbbf24; border-color:#f59e0b;">58% Avg</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; padding:0.5rem 0; margin-bottom:1rem;">
                <span style="color:#f1f5f9; font-size:0.88rem;">📈 {t('land_map_quant')}</span>
                <span class="badge badge-low">82% Avg</span>
            </div>
            <div style="background:#0f172a; border-radius:8px; padding:0.8rem; text-align:center; font-size:0.75rem; color:#818cf8;">
                🎯 {t('land_map_next_rec')} <strong>{t('land_map_next_rec_topic')}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br><br>", unsafe_allow_html=True)

# Row 2
col_r2_vis, col_r2_text = st.columns([1, 1.2])
with col_r2_vis:
    st.markdown(
        f"""
        <div class="cfa-card" style="background:#1e293b; padding:1.5rem; border-color:#334155; margin-top:1.5rem;">
            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:1rem;">
                <span style="font-size:1rem;">👤</span>
                <div style="font-size:0.75rem; color:#94a3b8;"><strong style="color:#818cf8;">{t('land_chat_candidate')}</strong> "{t('land_chat_query')}"</div>
            </div>
            <div style="background:#0f172a; border-radius:8px; padding:1rem; border:1px solid #334155; margin-bottom:0.5rem;">
                <div style="font-size:0.8rem; font-weight:700; color:#06b6d4; margin-bottom:0.3rem;">🤖 {t('land_chat_tutor_title')}</div>
                <div style="font-size:0.78rem; color:#f1f5f9; line-height:1.5;">
                    {t('land_chat_tutor_text')}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_r2_text:
    st.markdown(
        f"""
        <div style="padding:1rem 0;">
            <span class="badge badge-low" style="margin-bottom:0.8rem; background:rgba(6,182,212,0.1); color:#06b6d4; border-color:rgba(6,182,212,0.3);">Context-Aware Tutor</span>
            <h3 style="color:#f1f5f9; font-weight:700;">{t('land_deep_dive_title2')}</h3>
            <p style="color:#94a3b8; font-size:0.95rem; line-height:1.6; margin-top:1rem;">
                {t('land_deep_dive_desc2')}
            </p>
            <ul style="color:#64748b; font-size:0.85rem; padding-left:1.2rem; line-height:1.8; margin-top:1rem;">
                <li>{t('land_deep_dive_li2_1')}</li>
                <li>{t('land_deep_dive_li2_2')}</li>
                <li>{t('land_deep_dive_li2_3')}</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br><br>", unsafe_allow_html=True)

# Row 3
col_r3_text, col_r3_vis = st.columns([1.2, 1])
with col_r3_text:
    st.markdown(
        f"""
        <div style="padding:1rem 0;">
            <span class="badge badge-medium" style="margin-bottom:0.8rem; background:rgba(16,185,129,0.1); color:#10b981; border-color:rgba(16,185,129,0.3);">Spaced Repetition Engine</span>
            <h3 style="color:#f1f5f9; font-weight:700;">{t('land_deep_dive_title3')}</h3>
            <p style="color:#94a3b8; font-size:0.95rem; line-height:1.6; margin-top:1rem;">
                {t('land_deep_dive_desc3')}
            </p>
            <ul style="color:#64748b; font-size:0.85rem; padding-left:1.2rem; line-height:1.8; margin-top:1rem;">
                <li>{t('land_deep_dive_li3_1')}</li>
                <li>{t('land_deep_dive_li3_2')}</li>
                <li>{t('land_deep_dive_li3_3')}</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_r3_vis:
    st.markdown(
        f"""
        <div class="cfa-card" style="background:#1e293b; padding:1.5rem; border-color:#334155; margin-top:1.5rem;">
            <div style="font-size:0.8rem; text-transform:uppercase; color:#64748b; letter-spacing:0.05em; margin-bottom:0.8rem;">{t('land_cal_title')}</div>
            <div style="background:#0f172a; border-radius:6px; padding:0.6rem; margin-bottom:0.5rem; display:flex; justify-content:space-between; align-items:center; border-left:3px solid #ef4444;">
                <div>
                    <div style="color:#f1f5f9; font-size:0.8rem; font-weight:600;">{t('land_cal_prac_fsa')}</div>
                    <div style="color:#64748b; font-size:0.7rem;">{t('land_cal_target_tomorrow')}</div>
                </div>
                <span class="badge badge-high" style="font-size:0.65rem;">High</span>
            </div>
            <div style="background:#0f172a; border-radius:6px; padding:0.6rem; margin-bottom:0.5rem; display:flex; justify-content:space-between; align-items:center; border-left:3px solid #f59e0b;">
                <div>
                    <div style="color:#f1f5f9; font-size:0.8rem; font-weight:600;">{t('land_cal_rev_ethics')}</div>
                    <div style="color:#64748b; font-size:0.7rem;">{t('land_cal_target_3days')}</div>
                </div>
                <span class="badge badge-medium" style="font-size:0.65rem;">Medium</span>
            </div>
            <div style="background:#0f172a; border-radius:6px; padding:0.6rem; display:flex; justify-content:space-between; align-items:center; border-left:3px solid #10b981;">
                <div>
                    <div style="color:#f1f5f9; font-size:0.8rem; font-weight:600;">{t('land_cal_mock_sess1')}</div>
                    <div style="color:#64748b; font-size:0.7rem;">{t('land_cal_target_weekend')}</div>
                </div>
                <span class="badge badge-low" style="font-size:0.65rem;">Low</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br><br><br><hr style='border-color:#334155;'><br>", unsafe_allow_html=True)

# ── Footer ───────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="text-align:center; padding: 2rem 0; color:#64748b; font-size:0.8rem;">
        <p>📊 CFA Learning Assistant</p>
        <p style="margin-top:0.4rem; color:#475569;">
            {t('footer_disclaimer')}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
