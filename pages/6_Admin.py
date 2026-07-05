"""
pages/6_Admin.py — Admin user dashboard (restricted to admin accounts).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from database.db import (
    init_db, get_all_users, get_user_summary_stats,
    get_user_sessions, get_user_profile, get_topic_performance,
)
from utils.auth import is_logged_in, get_current_user, render_auth_page
from utils.sidebar import render_sidebar

st.set_page_config(page_title="Admin Dashboard · CFA Assistant", page_icon="🔑", layout="wide")

css = Path(__file__).parent.parent / "assets" / "styles.css"
if css.exists():
    st.markdown(f"<style>{css.read_text()}</style>", unsafe_allow_html=True)

# Extra admin-specific CSS
st.markdown("""
<style>
.user-card {
    background: linear-gradient(145deg, #0f172a, #1e293b);
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 1.1rem 1.2rem;
    height: 100%;
    transition: border-color 0.2s, transform 0.15s, box-shadow 0.2s;
    position: relative;
    overflow: hidden;
}
.user-card:hover {
    border-color: #6366f1;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(99,102,241,0.15);
}
.user-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #6366f1, #06b6d4);
    border-radius: 14px 14px 0 0;
}
.user-avatar {
    width: 42px; height: 42px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #06b6d4);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; font-weight: 800; color: white;
    margin-bottom: 0.6rem;
}
.user-name { font-weight: 800; font-size: 0.95rem; color: #f1f5f9; }
.user-username { font-size: 0.75rem; color: #64748b; }
.user-meta { font-size: 0.75rem; color: #94a3b8; margin-top: 0.5rem; line-height: 1.8; }
.stat-chip {
    display: inline-flex; align-items: center; gap: 4px;
    background: #0f172a; border: 1px solid #1e293b;
    border-radius: 6px; padding: 3px 8px;
    font-size: 0.72rem; color: #94a3b8;
    margin: 2px 2px 0 0;
}
.stat-chip strong { color: #f1f5f9; }
.admin-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 2rem;
    display: flex; justify-content: space-between; align-items: center;
}
.detail-modal {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 1.5rem;
    margin-top: 1rem;
}
.weak-topic-bar {
    height: 6px; border-radius: 99px;
    background: linear-gradient(90deg, #ef4444, #f59e0b);
    margin-top: 3px; margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# ── Auth & access control ─────────────────────────────────────────
init_db()
if not is_logged_in():
    render_auth_page()
    st.stop()

user = get_current_user()
ADMIN_USERNAMES = ["hnamvu29", "admin"]  # Add your own username here

if user["username"] not in ADMIN_USERNAMES:
    st.error("🔒 Access denied. Administrator privileges required.")
    st.info("If you believe this is an error, please contact the system administrator.")
    st.stop()

render_sidebar()

# ── Header ────────────────────────────────────────────────────────
all_users = get_all_users()
total_users = len(all_users)
onboarded = sum(1 for u in all_users if u.get("onboarding_done"))

st.markdown(
    f"""
    <div class="admin-header">
        <div>
            <h1 style="font-size:1.9rem; font-weight:800; color:#f1f5f9; margin:0;">
                🔑 Admin Dashboard
            </h1>
            <p style="color:#64748b; margin-top:0.3rem; margin-bottom:0;">
                Monitor user activity, progress, and engagement
            </p>
        </div>
        <div style="display:flex; gap:2rem; text-align:center;">
            <div>
                <div style="font-size:2rem; font-weight:900; color:#6366f1;">{total_users}</div>
                <div style="font-size:0.75rem; color:#64748b;">Total Users</div>
            </div>
            <div>
                <div style="font-size:2rem; font-weight:900; color:#10b981;">{onboarded}</div>
                <div style="font-size:0.75rem; color:#64748b;">Onboarded</div>
            </div>
            <div>
                <div style="font-size:2rem; font-weight:900; color:#f59e0b;">{total_users - onboarded}</div>
                <div style="font-size:0.75rem; color:#64748b;">New (No Profile)</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Search / filter bar ───────────────────────────────────────────
col_search, col_filter = st.columns([2, 1])
with col_search:
    search_query = st.text_input("🔍 Search users by name or email", placeholder="Type a name...", label_visibility="collapsed")
with col_filter:
    filter_onboarding = st.selectbox("Filter", ["All users", "Onboarded only", "Not onboarded"], label_visibility="collapsed")

filtered_users = all_users
if search_query:
    q = search_query.lower()
    filtered_users = [u for u in filtered_users if q in (u.get("username") or "").lower()
                     or q in (u.get("email") or "").lower()
                     or q in (u.get("full_name") or "").lower()]
if filter_onboarding == "Onboarded only":
    filtered_users = [u for u in filtered_users if u.get("onboarding_done")]
elif filter_onboarding == "Not onboarded":
    filtered_users = [u for u in filtered_users if not u.get("onboarding_done")]

st.markdown(f"<p style='color:#64748b; font-size:0.8rem; margin-bottom:1rem;'>Showing {len(filtered_users)} of {total_users} users</p>", unsafe_allow_html=True)

# ── User Cards (3 per row) ────────────────────────────────────────
if not filtered_users:
    st.info("No users match your search criteria.")
else:
    CARDS_PER_ROW = 3

    for row_start in range(0, len(filtered_users), CARDS_PER_ROW):
        row_users = filtered_users[row_start:row_start + CARDS_PER_ROW]
        cols = st.columns(CARDS_PER_ROW)

        for col_idx, u in enumerate(row_users):
            with cols[col_idx]:
                uid_u = u["id"]
                full_name = u.get("full_name") or u["username"]
                username = u["username"]
                email = u.get("email") or "—"
                cfa_level = u.get("cfa_level") or 1
                exam_window = u.get("exam_window") or "—"
                exam_year = u.get("exam_year") or "—"
                city = u.get("city") or "—"
                is_onboarded = bool(u.get("onboarding_done"))
                plan = u.get("subscription_plan") or "free"
                created = (u.get("created_at") or "")[:10]

                # Avatar initials
                initials = "".join(w[0].upper() for w in full_name.split()[:2]) or "?"
                status_dot_color = "#10b981" if is_onboarded else "#f59e0b"

                stats = get_user_summary_stats(uid_u)
                avg_score = stats.get("avg_score") or 0
                total_sessions = stats.get("total_sessions") or 0
                total_chats = stats.get("total_chats") or 0
                weak_topics = stats.get("weak_topics") or []

                score_color = "#10b981" if avg_score >= 70 else "#f59e0b" if avg_score >= 50 else "#ef4444"
                plan_color = "#818cf8" if plan == "pro" else "#64748b"

                st.markdown(
                    f"""
                    <div class="user-card">
                        <div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:0.5rem;">
                            <div class="user-avatar">{initials}</div>
                            <div>
                                <div class="user-name">{full_name}</div>
                                <div class="user-username">@{username}</div>
                            </div>
                            <div style="margin-left:auto;">
                                <span style="width:8px;height:8px;border-radius:50%;background:{status_dot_color};
                                             display:inline-block;" title="{'Onboarded' if is_onboarded else 'Not onboarded'}"></span>
                            </div>
                        </div>
                        <div class="user-meta">
                            📧 {email}<br>
                            🏙️ {city} &nbsp;·&nbsp; 📅 Joined {created}<br>
                            🎓 CFA Level {cfa_level} &nbsp;·&nbsp; {exam_window} {exam_year}
                        </div>
                        <div style="margin-top:0.6rem; display:flex; flex-wrap:wrap;">
                            <div class="stat-chip">📊 <strong>{total_sessions}</strong> Sessions</div>
                            <div class="stat-chip" style="color:{score_color};">🏆 <strong style="color:{score_color};">{avg_score:.0f}%</strong> Avg</div>
                            <div class="stat-chip">💬 <strong>{total_chats}</strong> Chats</div>
                            <div class="stat-chip" style="color:{plan_color};">⭐ <strong style="color:{plan_color};">{plan.upper()}</strong></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Details button — uses session_state to track which user's detail is open
                detail_key = f"show_detail_{uid_u}"
                btn_label = "🔽 Hide Details" if st.session_state.get(detail_key) else "👁 View Details"
                if st.button(btn_label, key=f"btn_detail_{uid_u}", use_container_width=True):
                    st.session_state[detail_key] = not st.session_state.get(detail_key, False)
                    st.rerun()

                # Inline detail panel
                if st.session_state.get(detail_key):
                    recent_sessions = get_user_sessions(uid_u, limit=5)
                    topic_perf = get_topic_performance(uid_u)

                    with st.expander(f"📂 {full_name}'s Details", expanded=True):
                        if weak_topics:
                            st.markdown("**Weakest Topics:**")
                            for wt in weak_topics:
                                pct = wt.get("avg_score") or 0
                                bar_w = max(5, int(pct))
                                st.markdown(
                                    f"""<div style="font-size:0.78rem;color:#94a3b8;">{wt['topic']}
                                    <span style="float:right;color:#ef4444;font-weight:700;">{pct:.0f}%</span></div>
                                    <div style="height:5px;background:#1e293b;border-radius:99px;margin-bottom:6px;">
                                        <div style="height:5px;width:{bar_w}%;background:linear-gradient(90deg,#ef4444,#f59e0b);border-radius:99px;"></div>
                                    </div>""",
                                    unsafe_allow_html=True,
                                )

                        if recent_sessions:
                            st.markdown("**Recent Sessions:**")
                            for s in recent_sessions:
                                score_val = s.get("score") or 0
                                s_color = "#10b981" if score_val >= 70 else "#f59e0b" if score_val >= 50 else "#ef4444"
                                st.markdown(
                                    f"""<div style="display:flex;justify-content:space-between;
                                                    padding:4px 0;border-bottom:1px solid #1e293b;
                                                    font-size:0.78rem;">
                                        <span style="color:#94a3b8;">{(s.get('started_at') or '')[:10]} · {s.get('topic','')} ({s.get('session_type','')})</span>
                                        <strong style="color:{s_color};">{score_val:.0f}%</strong>
                                    </div>""",
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.caption("No sessions completed yet.")

        # Spacer between rows
        st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
