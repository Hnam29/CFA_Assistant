"""
pages/6_Admin.py — Admin dashboard with 4 sections:
  👥 Users · 📊 User Analytics · 📈 Platform · 🛠️ Actions
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database.db import (
    init_db, get_all_users, get_user_summary_stats,
    get_user_sessions, get_user_profile, get_topic_performance,
    grant_premium_access, revoke_premium_access, delete_user,
    # Analytics
    get_user_activity_heatmap, get_user_score_trend,
    get_user_topic_coverage, get_user_session_completion_rate,
    get_retention_funnel,
    # Actions
    send_admin_notification, export_user_data, reset_user_progress,
    get_user_notifications,
)
from utils.auth import is_logged_in, get_current_user, render_auth_page, get_admin_credentials
from utils.sidebar import render_sidebar
from utils.cfa_topics import TOPIC_NAMES

st.set_page_config(page_title="Admin Dashboard · CFA Assistant", page_icon="🔑", layout="wide")

css = Path(__file__).parent.parent / "assets" / "styles.css"
if css.exists():
    st.markdown(f"<style>{css.read_text()}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
.user-card {
    background: linear-gradient(145deg, #0f172a, #1e293b);
    border: 1px solid #334155; border-radius: 14px;
    padding: 1.1rem 1.2rem; height: 100%;
    transition: border-color 0.2s, transform 0.15s, box-shadow 0.2s;
    position: relative; overflow: hidden;
}
.user-card:hover { border-color: #6366f1; transform: translateY(-2px); box-shadow: 0 8px 24px rgba(99,102,241,0.15); }
.user-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #6366f1, #06b6d4); border-radius: 14px 14px 0 0;
}
.user-avatar {
    width: 42px; height: 42px; border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #06b6d4);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; font-weight: 800; color: white; margin-bottom: 0.6rem;
}
.user-name { font-weight: 800; font-size: 0.95rem; color: #f1f5f9; }
.user-username { font-size: 0.75rem; color: #64748b; }
.user-meta { font-size: 0.75rem; color: #94a3b8; margin-top: 0.5rem; line-height: 1.8; }
.stat-chip {
    display: inline-flex; align-items: center; gap: 4px;
    background: #0f172a; border: 1px solid #1e293b;
    border-radius: 6px; padding: 3px 8px;
    font-size: 0.72rem; color: #94a3b8; margin: 2px 2px 0 0;
}
.stat-chip strong { color: #f1f5f9; }
.admin-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid #334155; border-radius: 16px;
    padding: 1.5rem 2rem; margin-bottom: 1.5rem;
    display: flex; justify-content: space-between; align-items: center;
}
.heatmap-cell {
    display: inline-block; width: 12px; height: 12px;
    border-radius: 2px; margin: 1px;
}
.funnel-bar {
    height: 44px; border-radius: 8px;
    display: flex; align-items: center; padding: 0 1rem;
    font-weight: 700; font-size: 0.85rem; color: white;
    margin-bottom: 6px;
}
.coverage-pill {
    display: inline-block; padding: 4px 12px;
    border-radius: 20px; font-size: 0.75rem; font-weight: 600;
    margin: 3px; white-space: nowrap;
}
</style>
""", unsafe_allow_html=True)

# ── Auth & access control ─────────────────────────────────────────
init_db()
if not is_logged_in():
    render_auth_page()
    st.stop()

user = get_current_user()
admin_user, _ = get_admin_credentials()

if user["username"] != admin_user:
    st.error("🔒 Access denied. Administrator privileges required.")
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
            <h1 style="font-size:1.9rem; font-weight:800; color:#f1f5f9; margin:0;">🔑 Admin Dashboard</h1>
            <p style="color:#64748b; margin-top:0.3rem; margin-bottom:0;">Monitor, evaluate and manage every user</p>
        </div>
        <div style="display:flex; gap:2rem; text-align:center;">
            <div><div style="font-size:2rem;font-weight:900;color:#6366f1;">{total_users}</div><div style="font-size:0.75rem;color:#64748b;">Total Users</div></div>
            <div><div style="font-size:2rem;font-weight:900;color:#10b981;">{onboarded}</div><div style="font-size:0.75rem;color:#64748b;">Onboarded</div></div>
            <div><div style="font-size:2rem;font-weight:900;color:#f59e0b;">{total_users - onboarded}</div><div style="font-size:0.75rem;color:#64748b;">New (No Profile)</div></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Custom tab navigation ─────────────────────────────────────────
if "admin_tab" not in st.session_state:
    st.session_state.admin_tab = "users"

TABS = [
    ("users",     "👥 Users"),
    ("analytics", "📊 User Analytics"),
    ("platform",  "📈 Platform"),
    ("actions",   "🛠️ Actions"),
]

tab_cols = st.columns(len(TABS))
for i, (key, label) in enumerate(TABS):
    with tab_cols[i]:
        btn_type = "primary" if st.session_state.admin_tab == key else "secondary"
        if st.button(label, key=f"adminnav_{key}", use_container_width=True, type=btn_type):
            st.session_state.admin_tab = key
            st.rerun()

st.markdown("<hr style='margin:0.4rem 0 1.5rem 0; border-color:#334155;'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAB 1: USERS
# ══════════════════════════════════════════════════════════════════
if st.session_state.admin_tab == "users":

    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("🔍 Search", placeholder="Name or email…", label_visibility="collapsed", key="usr_search")
    with col_filter:
        filter_onboarding = st.selectbox("Filter", ["All users", "Onboarded only", "Not onboarded"], label_visibility="collapsed", key="usr_filter")

    filtered = all_users
    if search_query:
        q = search_query.lower()
        filtered = [u for u in filtered if
                    q in (u.get("username") or "").lower() or
                    q in (u.get("email") or "").lower() or
                    q in (u.get("full_name") or "").lower()]
    if filter_onboarding == "Onboarded only":
        filtered = [u for u in filtered if u.get("onboarding_done")]
    elif filter_onboarding == "Not onboarded":
        filtered = [u for u in filtered if not u.get("onboarding_done")]

    st.markdown(f"<p style='color:#64748b;font-size:0.8rem;margin-bottom:1rem;'>Showing {len(filtered)} of {total_users} users</p>", unsafe_allow_html=True)

    if not filtered:
        st.info("No users match your search criteria.")
    else:
        CARDS_PER_ROW = 3
        for row_start in range(0, len(filtered), CARDS_PER_ROW):
            row_users = filtered[row_start:row_start + CARDS_PER_ROW]
            cols = st.columns(CARDS_PER_ROW)
            for col_idx, u in enumerate(row_users):
                with cols[col_idx]:
                    uid_u      = u["id"]
                    full_name  = u.get("full_name") or u["username"]
                    username   = u["username"]
                    email      = u.get("email") or "—"
                    cfa_level  = u.get("cfa_level") or 1
                    exam_window= u.get("exam_window") or "—"
                    exam_year  = u.get("exam_year") or "—"
                    city       = u.get("city") or "—"
                    is_onboarded = bool(u.get("onboarding_done"))
                    plan       = u.get("subscription_plan") or "free"
                    created_raw= u.get("created_at") or ""
                    created    = created_raw.isoformat()[:10] if hasattr(created_raw, "isoformat") else str(created_raw)[:10]
                    initials   = "".join(w[0].upper() for w in full_name.split()[:2]) or "?"
                    status_dot = "#10b981" if is_onboarded else "#f59e0b"

                    stats         = get_user_summary_stats(uid_u)
                    avg_score     = stats.get("avg_score") or 0
                    total_sessions= stats.get("total_sessions") or 0
                    total_chats   = stats.get("total_chats") or 0
                    weak_topics   = stats.get("weak_topics") or []
                    score_color   = "#10b981" if avg_score >= 70 else "#f59e0b" if avg_score >= 50 else "#ef4444"
                    plan_color    = "#818cf8" if plan == "pro" else "#64748b"

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
                                    <span style="width:8px;height:8px;border-radius:50%;background:{status_dot};display:inline-block;"
                                          title="{'Onboarded' if is_onboarded else 'Not onboarded'}"></span>
                                </div>
                            </div>
                            <div class="user-meta">
                                📧 {email}<br>🏙️ {city} &nbsp;·&nbsp; 📅 Joined {created}<br>
                                🎓 CFA Level {cfa_level} &nbsp;·&nbsp; {exam_window} {exam_year}
                            </div>
                            <div style="margin-top:0.6rem;display:flex;flex-wrap:wrap;">
                                <div class="stat-chip">📊 <strong>{total_sessions}</strong> Sessions</div>
                                <div class="stat-chip" style="color:{score_color};">🏆 <strong style="color:{score_color};">{avg_score:.0f}%</strong> Avg</div>
                                <div class="stat-chip">💬 <strong>{total_chats}</strong> Chats</div>
                                <div class="stat-chip" style="color:{plan_color};">⭐ <strong style="color:{plan_color};">{plan.upper()}</strong></div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    btn_row = st.columns([1, 1, 1])
                    detail_key = f"show_detail_{uid_u}"
                    btn_label = "🔽 Hide" if st.session_state.get(detail_key) else "👁 Details"
                    if btn_row[0].button(btn_label, key=f"btn_detail_{uid_u}", use_container_width=True):
                        st.session_state[detail_key] = not st.session_state.get(detail_key, False)
                        st.rerun()

                    if plan in ("premium", "pro", "admin"):
                        if btn_row[1].button("🔓 Revoke", key=f"btn_revoke_{uid_u}", use_container_width=True):
                            revoke_premium_access(uid_u)
                            st.success(f"Revoked premium for {username}")
                            st.rerun()
                    else:
                        if btn_row[1].button("⭐ Grant", key=f"btn_grant_{uid_u}", use_container_width=True, type="primary"):
                            grant_premium_access(uid_u)
                            st.success(f"Granted premium to {username}")
                            st.rerun()

                    # View Analytics shortcut
                    if btn_row[2].button("📊 Analyze", key=f"btn_analyze_{uid_u}", use_container_width=True):
                        st.session_state["analytics_user_id"] = uid_u
                        st.session_state.admin_tab = "analytics"
                        st.rerun()

                    confirm_key = f"confirm_del_{uid_u}"
                    if st.session_state.get(confirm_key):
                        st.warning(f"Delete **{username}** permanently?")
                        yes_col, no_col = st.columns(2)
                        if yes_col.button("✅ Yes, delete", key=f"yes_del_{uid_u}", use_container_width=True, type="primary"):
                            delete_user(uid_u)
                            st.session_state.pop(confirm_key, None)
                            st.success(f"Deleted user {username}")
                            st.rerun()
                        if no_col.button("❌ Cancel", key=f"no_del_{uid_u}", use_container_width=True):
                            st.session_state.pop(confirm_key, None)
                            st.rerun()
                    else:
                        if st.button("🗑 Delete", key=f"btn_del_{uid_u}", use_container_width=True):
                            st.session_state[confirm_key] = True
                            st.rerun()

                    if st.session_state.get(detail_key):
                        recent_sessions = get_user_sessions(uid_u, limit=5)
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
                                    raw_dt = s.get("started_at") or ""
                                    started_str = raw_dt.isoformat()[:10] if hasattr(raw_dt, "isoformat") else str(raw_dt)[:10]
                                    st.markdown(
                                        f"""<div style="display:flex;justify-content:space-between;padding:4px 0;
                                                        border-bottom:1px solid #1e293b;font-size:0.78rem;">
                                            <span style="color:#94a3b8;">{started_str} · {s.get('topic','')} ({s.get('session_type','')})</span>
                                            <strong style="color:{s_color};">{score_val:.0f}%</strong>
                                        </div>""",
                                        unsafe_allow_html=True,
                                    )
                            else:
                                st.caption("No sessions completed yet.")

            st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# TAB 2: USER ANALYTICS
# ══════════════════════════════════════════════════════════════════
elif st.session_state.admin_tab == "analytics":
    user_options = {f"{u.get('full_name') or u['username']} (@{u['username']})": u["id"] for u in all_users}
    
    # Pre-select if navigated from Users tab
    pre_uid = st.session_state.get("analytics_user_id")
    default_idx = 0
    if pre_uid:
        ids = list(user_options.values())
        if pre_uid in ids:
            default_idx = ids.index(pre_uid)

    selected_label = st.selectbox("👤 Select User", list(user_options.keys()), index=default_idx, key="analytics_user_sel")
    sel_uid = user_options[selected_label]
    st.session_state["analytics_user_id"] = sel_uid

    st.markdown("<hr style='border-color:#1e293b; margin:0.5rem 0 1.5rem 0;'>", unsafe_allow_html=True)

    # ── Activity Heatmap ──────────────────────────────────────────
    st.markdown("### 🗓️ Activity Heatmap (Last 12 Months)")
    heatmap_data = get_user_activity_heatmap(sel_uid)

    today = date.today()
    # Start from the Monday of 52 weeks ago
    start = today - timedelta(days=365)
    start -= timedelta(days=start.weekday())  # align to Monday

    max_count = max(heatmap_data.values(), default=1)
    
    # Build 52-week × 7-day grid
    weeks = []
    cur = start
    while cur <= today:
        week = []
        for _ in range(7):
            week.append(cur)
            cur += timedelta(days=1)
        weeks.append(week)

    def heat_color(cnt: int) -> str:
        if cnt == 0: return "#1e293b"
        ratio = cnt / max(max_count, 1)
        if ratio < 0.25: return "#166534"
        if ratio < 0.5:  return "#16a34a"
        if ratio < 0.75: return "#22c55e"
        return "#4ade80"

    months_html = ""
    last_month = None
    month_positions = []
    for wi, week in enumerate(weeks):
        month_of_week = week[0].month
        if month_of_week != last_month:
            month_positions.append((wi, week[0].strftime("%b")))
            last_month = month_of_week

    # Month labels
    month_label_html = '<div style="display:flex;gap:0px;margin-bottom:4px;padding-left:24px;">'
    prev_wi = 0
    for wi, lbl in month_positions:
        spacer = wi - prev_wi
        month_label_html += f'<span style="width:{spacer*14}px;font-size:0.65rem;color:#64748b;display:inline-block;overflow:hidden;">{lbl}</span>'
        prev_wi = wi
    month_label_html += "</div>"

    # Day labels + grid
    day_labels = ["Mon", "", "Wed", "", "Fri", "", "Sun"]
    grid_html = '<div style="display:flex;gap:0;">'
    grid_html += '<div style="display:flex;flex-direction:column;gap:1px;margin-right:4px;">'
    for dl in day_labels:
        grid_html += f'<span style="height:13px;font-size:0.6rem;color:#64748b;line-height:13px;">{dl}</span>'
    grid_html += "</div>"

    for week in weeks:
        grid_html += '<div style="display:flex;flex-direction:column;gap:1px;">'
        for d in week:
            ds = d.isoformat()
            cnt = heatmap_data.get(ds, 0)
            color = heat_color(cnt)
            tip = f"{cnt} session{'s' if cnt != 1 else ''} on {ds}"
            grid_html += f'<div class="heatmap-cell" style="background:{color};" title="{tip}"></div>'
        grid_html += "</div>"
    grid_html += "</div>"

    total_active_days = len(heatmap_data)
    total_heatmap_sessions = sum(heatmap_data.values())

    st.markdown(
        f"""<div class="cfa-card">
            {month_label_html}
            {grid_html}
            <div style="margin-top:0.8rem;font-size:0.75rem;color:#64748b;">
                🟩 <strong style="color:#f1f5f9;">{total_active_days}</strong> active days &nbsp;·&nbsp;
                📊 <strong style="color:#f1f5f9;">{total_heatmap_sessions}</strong> total sessions in last year
                &nbsp;·&nbsp; Less <span style="background:#1e293b;padding:2px 6px;border-radius:3px;">░</span>
                <span style="background:#166534;padding:2px 6px;border-radius:3px;"> </span>
                <span style="background:#22c55e;padding:2px 6px;border-radius:3px;"> </span>
                <span style="background:#4ade80;padding:2px 6px;border-radius:3px;"> </span> More
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col_trend, col_completion = st.columns([1.5, 1])

    # ── Score Trend ───────────────────────────────────────────────
    with col_trend:
        st.markdown("### 📈 Score Trend Over Time")
        score_trend = get_user_score_trend(sel_uid)
        if score_trend:
            df_trend = pd.DataFrame(score_trend)
            df_trend["date"] = pd.to_datetime(df_trend["date"])
            df_trend = df_trend.set_index("date")[["score"]]
            st.line_chart(df_trend, color="#6366f1", use_container_width=True)
            st.caption(f"Based on {len(score_trend)} completed session(s).")
        else:
            st.markdown("""<div class="cfa-card" style="text-align:center;color:#64748b;padding:2rem;">
                No completed sessions yet.</div>""", unsafe_allow_html=True)

    # ── Session Completion Rate ───────────────────────────────────
    with col_completion:
        st.markdown("### ✅ Session Completion Rate")
        comp_data = get_user_session_completion_rate(sel_uid)
        completed = comp_data["completed"]
        abandoned = comp_data["abandoned"]
        total_s   = comp_data["total"]
        rate = (completed / total_s * 100) if total_s > 0 else 0

        rate_color = "#10b981" if rate >= 70 else "#f59e0b" if rate >= 40 else "#ef4444"

        st.markdown(
            f"""<div class="cfa-card" style="text-align:center;">
                <div style="font-size:3.5rem;font-weight:900;color:{rate_color};line-height:1;">{rate:.0f}%</div>
                <div style="color:#64748b;font-size:0.8rem;margin-top:0.3rem;">Completion Rate</div>
                <div style="margin:1.2rem 0;height:10px;background:#1e293b;border-radius:99px;overflow:hidden;">
                    <div style="width:{rate:.0f}%;height:100%;background:{rate_color};border-radius:99px;transition:width 0.5s;"></div>
                </div>
                <div style="display:flex;justify-content:space-around;margin-top:0.8rem;">
                    <div>
                        <div style="font-size:1.6rem;font-weight:800;color:#10b981;">{completed}</div>
                        <div style="font-size:0.72rem;color:#64748b;">Completed</div>
                    </div>
                    <div>
                        <div style="font-size:1.6rem;font-weight:800;color:#ef4444;">{abandoned}</div>
                        <div style="font-size:0.72rem;color:#64748b;">Abandoned</div>
                    </div>
                    <div>
                        <div style="font-size:1.6rem;font-weight:800;color:#f1f5f9;">{total_s}</div>
                        <div style="font-size:0.72rem;color:#64748b;">Total</div>
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Topic Coverage Map ────────────────────────────────────────
    st.markdown("### 🗺️ Topic Coverage Map")
    coverage = get_user_topic_coverage(sel_uid)
    covered   = sum(1 for t in TOPIC_NAMES if t in coverage)
    uncovered = len(TOPIC_NAMES) - covered

    st.markdown(
        f"<p style='color:#64748b;font-size:0.85rem;margin-bottom:0.8rem;'>"
        f"<strong style='color:#10b981;'>{covered}</strong> of {len(TOPIC_NAMES)} topics practiced &nbsp;·&nbsp; "
        f"<strong style='color:#ef4444;'>{uncovered}</strong> never touched</p>",
        unsafe_allow_html=True,
    )

    pills_html = '<div style="display:flex;flex-wrap:wrap;gap:4px;">'
    for topic in TOPIC_NAMES:
        cnt = coverage.get(topic, 0)
        if cnt > 0:
            pills_html += (
                f'<span class="coverage-pill" style="background:rgba(16,185,129,0.15);'
                f'color:#10b981;border:1px solid rgba(16,185,129,0.3);" title="{cnt} session(s)">'
                f'✓ {topic} ({cnt})</span>'
            )
        else:
            pills_html += (
                f'<span class="coverage-pill" style="background:#1e293b;'
                f'color:#475569;border:1px solid #334155;">○ {topic}</span>'
            )
    pills_html += "</div>"
    st.markdown(
        f'<div class="cfa-card">{pills_html}</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════
# TAB 3: PLATFORM ANALYTICS
# ══════════════════════════════════════════════════════════════════
elif st.session_state.admin_tab == "platform":
    st.markdown("### 🔄 User Retention Funnel")
    st.markdown("<p style='color:#64748b;font-size:0.85rem;'>Tracks how users progress through key engagement milestones.</p>", unsafe_allow_html=True)

    funnel = get_retention_funnel()

    stages = [
        ("registered",   "📋 Registered",          "#6366f1"),
        ("onboarded",    "✅ Completed Onboarding", "#8b5cf6"),
        ("had_session",  "🎯 Completed 1+ Session", "#06b6d4"),
        ("active_5plus", "🏃 Completed 5+ Sessions","#10b981"),
        ("active_7days", "🔥 Active (Last 7 Days)", "#f59e0b"),
    ]

    base = funnel.get("registered", 1) or 1

    st.markdown("<div style='max-width:700px;'>", unsafe_allow_html=True)
    for key, label, color in stages:
        count = funnel.get(key, 0)
        pct   = count / base * 100
        width = max(pct, 5)
        st.markdown(
            f"""<div style="margin-bottom:0.6rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;">
                    <span style="font-size:0.82rem;color:#94a3b8;">{label}</span>
                    <span style="font-size:0.82rem;font-weight:700;color:{color};">{count} ({pct:.1f}%)</span>
                </div>
                <div style="height:36px;background:#1e293b;border-radius:8px;overflow:hidden;">
                    <div style="height:36px;width:{width:.1f}%;background:linear-gradient(90deg,{color},{color}88);
                                border-radius:8px;display:flex;align-items:center;padding:0 0.8rem;
                                font-weight:700;font-size:0.8rem;color:white;white-space:nowrap;
                                transition:width 0.5s;">{count}</div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Drop-off between stages
        keys = [k for k, _, _ in stages]
        idx = keys.index(key)
        if idx < len(stages) - 1:
            next_count = funnel.get(keys[idx + 1], 0)
            drop = count - next_count
            if drop > 0 and count > 0:
                drop_pct = drop / count * 100
                st.markdown(
                    f'<div style="font-size:0.7rem;color:#ef4444;padding-left:0.5rem;margin-bottom:0.4rem;">'
                    f'▼ {drop} dropped off ({drop_pct:.0f}%)</div>',
                    unsafe_allow_html=True,
                )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Summary metrics ───────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    mc1, mc2, mc3 = st.columns(3)
    onboard_rate = (funnel.get("onboarded", 0) / base * 100) if base else 0
    session_rate = (funnel.get("had_session", 0) / base * 100) if base else 0
    retention_7d = (funnel.get("active_7days", 0) / base * 100) if base else 0

    for col, val, label, color in [
        (mc1, f"{onboard_rate:.0f}%", "Onboarding Rate", "#8b5cf6"),
        (mc2, f"{session_rate:.0f}%", "Activation Rate", "#06b6d4"),
        (mc3, f"{retention_7d:.0f}%", "7-Day Retention", "#f59e0b"),
    ]:
        with col:
            col.markdown(
                f"""<div class="cfa-card" style="text-align:center;">
                    <div style="font-size:2.2rem;font-weight:900;color:{color};">{val}</div>
                    <div style="font-size:0.78rem;color:#64748b;margin-top:0.3rem;">{label}</div>
                </div>""",
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════
# TAB 4: ADMIN ACTIONS
# ══════════════════════════════════════════════════════════════════
elif st.session_state.admin_tab == "actions":

    user_options = {f"{u.get('full_name') or u['username']} (@{u['username']})": u for u in all_users}
    user_names   = list(user_options.keys())

    action_col1, action_col2 = st.columns(2)

    # ── Send Notification ─────────────────────────────────────────
    with action_col1:
        st.markdown(
            """<div class="cfa-card">
                <div class="section-header">📬 Send Notification</div>
            """, unsafe_allow_html=True)

        with st.form("send_notif_form", clear_on_submit=True):
            notif_target = st.selectbox("Target User", user_names, key="notif_target")
            notif_msg    = st.text_area("Message", placeholder="Write your message to the user…", height=120, key="notif_msg")
            submitted    = st.form_submit_button("📤 Send Notification", type="primary", use_container_width=True)

            if submitted:
                if not notif_msg.strip():
                    st.error("Please enter a message.")
                else:
                    target_user = user_options[notif_target]
                    send_admin_notification(target_user["id"], notif_msg.strip(), sender=admin_user)
                    st.success(f"✅ Notification sent to **{notif_target}**!")
                    # Force rerun to show the new message in the history log below
                    st.rerun()

        # Display history of sent messages to this user
        target_user = user_options[notif_target]
        notifs = get_user_notifications(target_user["id"])
        if notifs:
            st.markdown("<div style='font-size:0.85rem; font-weight:700; color:#94a3b8; margin-top:1rem; margin-bottom:0.4rem;'>📜 Sent Message History:</div>", unsafe_allow_html=True)
            for n in notifs[:5]:
                created_raw = n.get("created_at") or ""
                created = created_raw.isoformat()[:16].replace("T", " ") if hasattr(created_raw, "isoformat") else str(created_raw)[:16]
                read_status = "🟢 Read" if n.get("is_read") else "⚪ Unread"
                st.markdown(
                    f"""<div style="background:#0f172a; padding:0.5rem 0.7rem; border-radius:8px; border:1px solid #1e293b; margin-bottom:0.4rem; font-size:0.75rem;">
                        <div style="display:flex; justify-content:space-between; color:#64748b; font-size:0.7rem; margin-bottom:3px;">
                            <span>🕒 {created}</span>
                            <span>{read_status}</span>
                        </div>
                        <div style="color:#cbd5e1; line-height:1.4;">{n['message']}</div>
                    </div>""",
                    unsafe_allow_html=True
                )

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Export User Data ──────────────────────────────────────────
    with action_col2:
        st.markdown(
            """<div class="cfa-card">
                <div class="section-header">📥 Export User Data (CSV)</div>
            """, unsafe_allow_html=True)

        export_target = st.selectbox("Select User", user_names, key="export_target")
        export_all    = st.checkbox("Export ALL users", key="export_all_chk")

        if st.button("🔄 Prepare Export", use_container_width=True, key="prep_export_btn"):
            if export_all:
                all_rows = []
                for u in all_users:
                    rows = export_user_data(u["id"])
                    for r in rows:
                        r["username"] = u["username"]
                    all_rows.extend(rows)
                df_export = pd.DataFrame(all_rows)
                filename = "cfa_all_users_export.csv"
            else:
                target_user = user_options[export_target]
                rows = export_user_data(target_user["id"])
                df_export = pd.DataFrame(rows)
                uname = target_user["username"]
                filename = f"cfa_{uname}_sessions.csv"

            if df_export.empty:
                st.warning("No data found for export.")
            else:
                st.download_button(
                    label=f"⬇️ Download {filename}",
                    data=df_export.to_csv(index=False).encode("utf-8"),
                    file_name=filename,
                    mime="text/csv",
                    use_container_width=True,
                )
                st.success(f"Ready: {len(df_export)} rows")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    action_col3, action_col4 = st.columns(2)

    # ── Reset User Progress ───────────────────────────────────────
    with action_col3:
        st.markdown(
            """<div class="cfa-card">
                <div class="section-header">🔄 Reset User Progress</div>
            """, unsafe_allow_html=True)

        reset_target = st.selectbox("Select User", user_names, key="reset_target")
        st.markdown(
            "<p style='color:#f59e0b;font-size:0.8rem;'>⚠️ This clears all sessions, answers, and scheduled sessions but keeps the account.</p>",
            unsafe_allow_html=True,
        )

        confirm_reset_key = f"confirm_reset_{reset_target}"
        if st.session_state.get(confirm_reset_key):
            st.warning(f"Reset all progress for **{reset_target}**? This cannot be undone.")
            yr, nr = st.columns(2)
            if yr.button("✅ Confirm Reset", key="yes_reset_btn", use_container_width=True, type="primary"):
                target_user = user_options[reset_target]
                reset_user_progress(target_user["id"])
                st.session_state.pop(confirm_reset_key, None)
                st.success(f"✅ Progress reset for **{reset_target}**.")
                st.rerun()
            if nr.button("❌ Cancel", key="no_reset_btn", use_container_width=True):
                st.session_state.pop(confirm_reset_key, None)
                st.rerun()
        else:
            if st.button("🔄 Reset Progress", use_container_width=True, key="reset_btn"):
                st.session_state[confirm_reset_key] = True
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Impersonate User ──────────────────────────────────────────
    with action_col4:
        st.markdown(
            """<div class="cfa-card">
                <div class="section-header">👤 Impersonate User</div>
            """, unsafe_allow_html=True)

        impersonate_target = st.selectbox("Select User", user_names, key="impersonate_target")
        st.markdown(
            "<p style='color:#94a3b8;font-size:0.8rem;'>View the app as this user. Your admin session remains active — click 'Exit' to return.</p>",
            unsafe_allow_html=True,
        )

        if st.session_state.get("impersonate_uid"):
            imp_uid  = st.session_state["impersonate_uid"]
            imp_name = st.session_state.get("impersonate_name", "user")
            st.markdown(
                f"<div style='background:rgba(99,102,241,0.15);border:1px solid #6366f1;border-radius:8px;"
                f"padding:0.6rem 1rem;margin-bottom:0.8rem;font-size:0.83rem;color:#818cf8;'>"
                f"👤 Currently viewing as <strong>{imp_name}</strong></div>",
                unsafe_allow_html=True,
            )
            if st.button("🚪 Exit Impersonate", use_container_width=True, key="exit_impersonate"):
                st.session_state.pop("impersonate_uid", None)
                st.session_state.pop("impersonate_name", None)
                st.rerun()
        else:
            if st.button("👤 Start Impersonating", type="primary", use_container_width=True, key="start_impersonate"):
                target_user = user_options[impersonate_target]
                st.session_state["impersonate_uid"]  = target_user["id"]
                st.session_state["impersonate_name"] = impersonate_target
                st.success(f"Now impersonating {impersonate_target}. Go to Dashboard to see their view.")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
