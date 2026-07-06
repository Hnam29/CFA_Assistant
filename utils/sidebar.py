"""
utils/sidebar.py — Shared sidebar component across all Streamlit pages.
"""

from datetime import date as _date
import streamlit as st
from utils.auth import is_logged_in, get_current_user, logout_user
from database.db import get_user_profile, get_topic_performance, get_upcoming_sessions, clear_all_user_data
from utils.i18n import t, get_lang, set_lang


def render_sidebar():
    """Render the standard branding, user profile, exam countdown, and stats in st.sidebar."""
    if not is_logged_in():
        return

    user = get_current_user()
    if not user:
        return

    # Hide specific page links dynamically via CSS injection
    from database.db import is_onboarding_done
    
    # Non-admin users cannot see the Admin Dashboard page link
    if user["username"] not in ["hnamvu29", "admin"]:
        st.markdown("<style>a[href*='Admin'] { display: none !important; }</style>", unsafe_allow_html=True)
        
    # Onboarded users and admins do not need to see the Onboarding page link
    if is_onboarding_done(user["id"]) or user["username"] in ["hnamvu29", "admin"]:
        st.markdown("<style>a[href*='Onboarding'] { display: none !important; }</style>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 0.5rem 0 1rem;">
                <div style="font-size:1.4rem; font-weight:800;
                            background: linear-gradient(135deg,#6366f1,#06b6d4);
                            -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                    📊 CFA Assistant
                </div>
                <div style="color:#64748b; font-size:0.75rem; margin-top:0.2rem;">
                    Level I · AI-Powered
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Language switcher ─────────────────────────
        # Compact flag-only buttons consistent with the landing nav bar
        _lang = get_lang()
        _sb_c1, _sb_c2, _sb_gap = st.columns([1, 1, 0.1])
        with _sb_c1:
            _t_en = "primary" if _lang == "en" else "secondary"
            if st.button("🇬🇧 EN", key="sb_lang_en", use_container_width=True, type=_t_en):
                set_lang("en")
                st.rerun()
        with _sb_c2:
            _t_vi = "primary" if _lang == "vi" else "secondary"
            if st.button("🇻🇳 VI", key="sb_lang_vi", use_container_width=True, type=_t_vi):
                set_lang("vi")
                st.rerun()
        st.markdown("<div style='margin-bottom:0.4rem;'></div>", unsafe_allow_html=True)

        # Profile info
        profile = get_user_profile(user["id"])
        display_name = profile["full_name"] if profile and profile.get("full_name") else user["username"]
        cfa_lvl = profile["cfa_level"] if profile else user.get("cfa_level", 1)

        # Countdown HTML
        countdown_html = ""
        if profile and profile.get("exam_date"):
            try:
                exam_dt = _date.fromisoformat(profile["exam_date"])
                days_left = (exam_dt - _date.today()).days
                c = "#10b981" if days_left > 90 else "#f59e0b" if days_left > 30 else "#ef4444"
                countdown_html = f'<div style="margin-top:0.4rem; background:#0f172a; border-radius:6px; padding:0.4rem 0.6rem; display:flex; justify-content:space-between; align-items:center;"><div style="color:#64748b;font-size:0.68rem;">📅 {profile["exam_window"]} {profile["exam_year"]}</div><div style="font-weight:700;color:{c};font-size:0.8rem;">{max(0,days_left)}d</div></div>'
            except Exception:
                pass

        profile_card_html = f'<div style="background:#1e293b; border:1px solid #334155; border-radius:8px; padding:0.6rem 0.8rem; margin-bottom:1rem;"><div style="color:#94a3b8; font-size:0.7rem;">{t("logged_in_as")}</div><div style="color:#f1f5f9; font-weight:600; font-size:0.9rem;">👤 {display_name}</div><div style="color:#64748b; font-size:0.7rem;">CFA Level {cfa_lvl}</div>{countdown_html}</div>'
        st.markdown(profile_card_html, unsafe_allow_html=True)

        # Quick stats
        try:
            topic_perf = get_topic_performance(user["id"])
            upcoming = get_upcoming_sessions(user["id"])
            if topic_perf:
                avg = sum(tp["avg_score"] for tp in topic_perf) / len(topic_perf)
                st.markdown(
                    f"""
                    <div style="display:flex; gap:0.4rem; margin-bottom:0.8rem;">
                        <div style="flex:1; background:#1e293b; border:1px solid #334155;
                                    border-radius:6px; padding:0.4rem; text-align:center;">
                            <div style="font-size:1.1rem; font-weight:700; color:#818cf8;">
                                {avg:.0f}%
                            </div>
                            <div style="font-size:0.6rem; color:#64748b;">{t('avg_score')}</div>
                        </div>
                        <div style="flex:1; background:#1e293b; border:1px solid #334155;
                                    border-radius:6px; padding:0.4rem; text-align:center;">
                            <div style="font-size:1.1rem; font-weight:700; color:#06b6d4;">
                                {len(upcoming)}
                            </div>
                            <div style="font-size:0.6rem; color:#64748b;">{t('upcoming')}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        except Exception:
            pass

        if st.button(t("sidebar_logout"), use_container_width=True, key="shared_logout_btn"):
            logout_user()
            # Clear any lingering auth overlay state so the landing page shows clean
            st.session_state.pop("show_auth", None)
            st.switch_page("app.py")

        st.markdown("---")

        # ── Reset All Progress (two-step confirmation) ────────────────
        if "confirm_reset_data" not in st.session_state:
            st.session_state.confirm_reset_data = False

        if not st.session_state.confirm_reset_data:
            if st.button(t("reset_progress"), use_container_width=True, key="reset_data_btn"):
                st.session_state.confirm_reset_data = True
                st.rerun()
        else:
            st.markdown(
                f"<div style='background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); "
                f"border-radius:8px; padding:0.6rem; margin-bottom:0.5rem; font-size:0.8rem; color:#fca5a5;'>"
                f"{t('reset_warning')}"
                f"</div>",
                unsafe_allow_html=True,
            )
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button(t("yes_reset"), use_container_width=True, key="confirm_reset_yes"):
                    clear_all_user_data(user["id"])
                    # Clear all relevant session state keys
                    for key in list(st.session_state.keys()):
                        if key not in ("user", "logged_in"):
                            del st.session_state[key]
                    st.session_state.confirm_reset_data = False
                    st.success(t("all_progress_reset"))
                    st.rerun()
            with col_no:
                if st.button(t("cancel_reset"), use_container_width=True, key="confirm_reset_no"):
                    st.session_state.confirm_reset_data = False
                    st.rerun()

        st.markdown("---")
