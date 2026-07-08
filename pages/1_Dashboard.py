"""
pages/1_Dashboard.py — Performance overview and upcoming sessions.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from database.db import (
    init_db, get_topic_performance, get_user_sessions,
    get_upcoming_sessions, is_onboarding_done, get_user_profile,
    get_subtopic_performance,
    get_user_streak, get_user_engagement_score,
    get_user_notifications, mark_notifications_read,
    get_user_activity_heatmap,
)
try:
    from database.db import get_pending_sessions, discard_session
except ImportError:
    def get_pending_sessions(uid): return []
    def discard_session(sid): pass
from utils.auth import is_logged_in, get_current_user, render_auth_page
from utils.cfa_topics import TOPIC_NAMES, CFA_TOPICS, TOPIC_WEIGHTS
from utils.charts import radar_chart, score_timeline, topic_bar_chart
from utils.i18n import t
from datetime import date, datetime, timedelta

def format_datetime_str(val):
    if not val:
        return ""
    if hasattr(val, "strftime"):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    val_str = str(val)
    if "." in val_str:
        val_str = val_str.split(".")[0]
    return val_str.replace("T", " ")

st.set_page_config(page_title="Dashboard · CFA Assistant", page_icon="📈", layout="wide")

# Load CSS
css = Path(__file__).parent.parent / "assets" / "styles.css"
if css.exists():
    st.markdown(f"<style>{css.read_text()}</style>", unsafe_allow_html=True)

init_db()

if not is_logged_in():
    st.session_state["show_auth"] = "login"
    st.switch_page("app.py")
    st.stop()

user = get_current_user()
uid = user["id"]

from utils.sidebar import render_sidebar
render_sidebar()

# Onboarding gate — redirect new users before they see the dashboard
if not is_onboarding_done(uid):
    st.switch_page("pages/0_Onboarding.py")
    st.stop()

profile = get_user_profile(uid)

# ── Data ──────────────────────────────────────────────────────────
topic_perf      = get_topic_performance(uid)
sessions        = get_user_sessions(uid, limit=30)
upcoming        = get_upcoming_sessions(uid)
subtopic_perf   = get_subtopic_performance(uid)

# Build score dict
topic_scores = {t_: 50.0 for t_ in TOPIC_NAMES}  # default 50 for radar display
for p in topic_perf:
    if p["topic"] in topic_scores:
        topic_scores[p["topic"]] = p["avg_score"]

# Build subtopic lookup: { topic: [ {subtopic, avg_score, total_answers}, ... ] }
subtopic_by_topic: dict = {}
for sp in subtopic_perf:
    topic_key = sp["topic"]
    if topic_key not in subtopic_by_topic:
        subtopic_by_topic[topic_key] = []
    subtopic_by_topic[topic_key].append(sp)

# ── Header ────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="margin-bottom:2rem;">
        <h1 style="font-size:1.9rem; font-weight:800; color:#f1f5f9; margin:0;">
            📈 {t('dashboard')}
        </h1>
        <p style="color:#64748b; margin-top:0.3rem;">
            {t('welcome_back')}, <strong style="color:#818cf8">{user['username']}</strong> ·
            CFA Level {profile['cfa_level'] if profile else 1} ·
            {date.today().strftime("%B %d, %Y")}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ══ Streak & Engagement Widget ═════════════════════════════════════
_streak   = get_user_streak(uid)
_engage   = get_user_engagement_score(uid)
_notifs   = get_user_notifications(uid)
_unread   = [n for n in _notifs if not n.get("is_read")]

cur_streak   = _streak["current_streak"]
longest_str  = _streak["longest_streak"]
last_active  = _streak.get("last_active_date") or "—"
eng_score    = _engage["score"]
eng_level    = _engage["level"]
eng_s30      = _engage["sessions_30d"]
eng_avg      = _engage["avg_score"]

# Level colors
level_colors = {
    "Elite":    ("#f59e0b", "rgba(245,158,11,0.15)"),
    "Advanced": ("#6366f1", "rgba(99,102,241,0.15)"),
    "Focused":  ("#06b6d4", "rgba(6,182,212,0.15)"),
    "Steady":   ("#10b981", "rgba(16,185,129,0.15)"),
    "Beginner": ("#64748b", "rgba(100,116,139,0.15)"),
}
lvl_color, lvl_bg = level_colors.get(eng_level, ("#64748b", "rgba(100,116,139,0.15)"))

# Streak flame emoji logic
if cur_streak >= 30:   flame = "🔥🔥🔥"
elif cur_streak >= 14: flame = "🔥🔥"
elif cur_streak >= 3:  flame = "🔥"
else:                  flame = "❄️"

# Last 14 days activity dots
from datetime import date as _d, timedelta as _td
_activity_hm = {}
try:
    _activity_hm = get_user_activity_heatmap(uid)
except Exception:
    pass

dots_html = ""
for i in range(13, -1, -1):
    d = (_d.today() - _td(days=i)).isoformat()
    has = _activity_hm.get(d, 0) > 0
    bg = "#22c55e" if has else "#1e293b"
    dots_html += f'<span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:{bg};margin:1px;"></span>'

# Notification banner
notif_html = ""
if _unread:
    mark_notifications_read(uid)
    msgs_preview = " &nbsp;|&nbsp; ".join(
        f'<em>{n["message"][:60]}{"..." if len(n["message"]) > 60 else ""}</em>' for n in _unread[:2]
    )
    notif_html = (
        f'<div style="background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.3);'
        f'border-radius:8px;padding:0.5rem 1rem;margin-top:0.7rem;font-size:0.8rem;color:#818cf8;">'
        f'📩 <strong>{len(_unread)} new message{"s" if len(_unread) > 1 else ""} from admin:</strong> {msgs_preview}'
        f'</div>'
    )

st.markdown(
    f"""
    <div style="background:linear-gradient(135deg,#0f172a,#1e293b);border:1px solid #334155;
                border-radius:16px;padding:1.2rem 1.5rem;margin-bottom:1.8rem;">
        <div style="display:flex;flex-wrap:wrap;gap:1.5rem;align-items:center;">
            <div style="text-align:center;min-width:80px;">
                <div style="font-size:2.4rem;line-height:1;">{flame}</div>
                <div style="font-size:1.9rem;font-weight:900;color:#f59e0b;line-height:1.1;">{cur_streak}</div>
                <div style="font-size:0.7rem;color:#64748b;margin-top:1px;">Day Streak</div>
            </div>
            <div style="width:1px;height:60px;background:#334155;"></div>
            <div style="text-align:center;min-width:80px;">
                <div style="font-size:1.6rem;font-weight:900;color:#94a3b8;">{longest_str}</div>
                <div style="font-size:0.7rem;color:#64748b;">Best Streak</div>
                <div style="font-size:0.65rem;color:#475569;margin-top:2px;">Last active: {last_active}</div>
            </div>
            <div style="width:1px;height:60px;background:#334155;"></div>
            <div style="text-align:center;min-width:100px;">
                <div style="font-size:1.8rem;font-weight:900;color:{lvl_color};">{eng_score}<span style="font-size:1rem;color:#64748b;">/100</span></div>
                <div style="background:{lvl_bg};color:{lvl_color};border:1px solid {lvl_color}44;
                            border-radius:20px;padding:1px 10px;font-size:0.72rem;font-weight:700;
                            display:inline-block;margin-top:2px;">{eng_level}</div>
                <div style="font-size:0.65rem;color:#475569;margin-top:3px;">Engagement Score</div>
            </div>
            <div style="width:1px;height:60px;background:#334155;"></div>
            <div style="flex:1;min-width:160px;">
                <div style="font-size:0.7rem;color:#64748b;margin-bottom:4px;">Last 14 days activity</div>
                <div>{dots_html}</div>
                <div style="font-size:0.7rem;color:#64748b;margin-top:6px;">
                    📊 {eng_s30} sessions this month &nbsp;·&nbsp; ∅ {eng_avg:.0f}% avg score
                </div>
            </div>
        </div>
        {notif_html}
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Pending / Saved Sessions ─────────────────────────────────────
try:
    import time
    pending_sessions = get_pending_sessions(uid)
except Exception:
    pending_sessions = []

if pending_sessions:
    st.markdown(
        """<div class="cfa-card" style="border-color:#3b82f6; background:rgba(59,130,246,0.05); margin-bottom:1.5rem; padding: 1.2rem;">
            <h4 style="color:#60a5fa; margin:0 0 0.5rem 0;">🔄 Saved Sessions In Progress</h4>
            <p style="color:#94a3b8; font-size:0.85rem; margin:0 0 1rem 0;">
                You have saved/paused sessions. You can resume them or discard them.
            </p>
        </div>""",
        unsafe_allow_html=True
    )
    for ps in pending_sessions:
        ps_id = ps["id"]
        ps_topic = ps["topic"]
        ps_type = ps["session_type"]
        started_time = format_datetime_str(ps["started_at"])

        display_type = "Practice" if ps_type.lower() in ("practice", "mixed") else "Mock Exam"

        col_ps_info, col_ps_actions = st.columns([7.5, 2.5])
        with col_ps_info:
            st.markdown(
                f"""<div style="font-size:0.95rem; color:#f1f5f9; padding-top: 0.3rem;">
                    <strong>{display_type}</strong> — Topic: <span style="color:#60a5fa; font-weight: 600;">{ps_topic}</span>
                    <span style="font-size:0.8rem; color:#64748b;">(Started: {started_time})</span>
                </div>""",
                unsafe_allow_html=True
            )
        with col_ps_actions:
            act_col1, act_col2 = st.columns(2)
            with act_col1:
                if st.button("▶️ Resume", key=f"resume_{ps_id}", use_container_width=True, type="primary"):
                    state = ps["state"]
                    if ps_type.lower() in ("practice", "mixed"):
                        st.session_state.practice_questions = state["questions"]
                        st.session_state.practice_answers = state["answers"]
                        st.session_state.practice_submitted = False
                        st.session_state.practice_session_id = ps_id
                        st.session_state.practice_start_time = time.time() - state.get("elapsed_secs", 0)
                        st.session_state.practice_current_idx = state.get("current_idx", 0)
                        st.session_state.practice_flags = set(state.get("flags", []))
                        st.session_state.practice_timer_secs = state.get("practice_timer_secs", len(state["questions"]) * 90)
                        st.session_state.practice_confirm_submit = False
                        st.session_state.practice_radio_versions = {}
                        st.switch_page("pages/2_Practice.py")
                    else:
                        st.session_state.exam_questions = state["questions"]
                        st.session_state.exam_answers = state["answers"]
                        st.session_state.exam_started = True
                        st.session_state.exam_submitted = False
                        st.session_state.exam_session_id = ps_id
                        st.session_state.exam_start_time = time.time() - state.get("elapsed_secs", 0)
                        st.session_state.exam_current_idx = state.get("current_idx", 0)
                        st.session_state.exam_flags = set(state.get("flags", []))
                        st.session_state.exam_duration_mins = state.get("exam_duration_mins", 30)
                        st.session_state.exam_confirm_submit = False
                        st.switch_page("pages/3_Mock_Exam.py")
            with act_col2:
                if st.button("🗑️ Discard", key=f"discard_{ps_id}", use_container_width=True):
                    try:
                        discard_session(ps_id)
                    except Exception:
                        pass
                    st.toast("Session discarded.")
                    st.rerun()
    st.markdown("<hr style='border-color:#334155; margin: 1.5rem 0;'>", unsafe_allow_html=True)

# ── KPI row ───────────────────────────────────────────────────────
total_sessions = len([s for s in sessions if s["completed"]])
avg_score = (
    sum(p["avg_score"] for p in topic_perf) / len(topic_perf)
    if topic_perf else 0
)
weak_topics = [p for p in topic_perf if p["avg_score"] < 60]
top_topic = max(topic_perf, key=lambda p: p["avg_score"]) if topic_perf else None

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(
        f"""<div class="metric-card">
            <div class="metric-value">{total_sessions}</div>
            <div class="metric-label">{t('sessions_completed')}</div>
        </div>""", unsafe_allow_html=True)
with col2:
    st.markdown(
        f"""<div class="metric-card">
            <div class="metric-value">{avg_score:.0f}%</div>
            <div class="metric-label">{t('overall_avg_score')}</div>
        </div>""", unsafe_allow_html=True)
with col3:
    st.markdown(
        f"""<div class="metric-card">
            <div class="metric-value">{len(weak_topics)}</div>
            <div class="metric-label">{t('topics_need_focus')}</div>
        </div>""", unsafe_allow_html=True)
with col4:
    st.markdown(
        f"""<div class="metric-card">
            <div class="metric-value">{len(upcoming)}</div>
            <div class="metric-label">{t('scheduled_sessions')}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Main content ──────────────────────────────────────────────────
col_left, col_right = st.columns([1.2, 1])

with col_left:
    with st.container(border=True):
        st.markdown(f"### {t('performance_radar')}")
        st.plotly_chart(radar_chart(topic_scores), use_container_width=True, key="radar")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f"### {t('score_history')}")
        if sessions:
            st.plotly_chart(score_timeline(sessions), use_container_width=True, key="timeline")
        else:
            st.markdown(
                f"""<div style="text-align:center; color:#64748b; padding:2rem;">
                    {t('no_sessions_yet')}
                </div>""", unsafe_allow_html=True)

with col_right:
    with st.container(border=True):
        st.markdown(f"### {t('score_by_topic')}")
        if topic_perf:
            perf_dict = {p["topic"]: p["avg_score"] for p in topic_perf}
            st.plotly_chart(topic_bar_chart(perf_dict), use_container_width=True, key="topicbar")
        else:
            st.markdown(
                f"""<div style="text-align:center; color:#64748b; padding:2rem;">
                    {t('complete_to_see_scores')}
                </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f"### {t('upcoming_sessions')}")
        if upcoming:
            today_str    = date.today().isoformat()
            tomorrow_str = (date.today() + timedelta(days=1)).isoformat()

            # Group by date
            from collections import defaultdict
            by_date: dict = defaultdict(list)
            for sess in upcoming:
                by_date[sess["scheduled_date"]].append(sess)

            # Build topic score lookup for context bars
            topic_score_lookup = {p["topic"]: p["avg_score"] for p in topic_perf}

            type_icons = {"Practice": "🎯", "Mock Exam": "📝", "Review": "📖"}
            priority_dots = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            priority_colors = {"high": "#ef4444", "medium": "#f59e0b", "low": "#10b981"}

            shown = 0
            for day in sorted(by_date.keys()):
                if shown >= 5:
                    break
                if day == today_str:
                    day_label = t("today")
                    header_color = "#6366f1"
                elif day == tomorrow_str:
                    day_label = t("tomorrow")
                    header_color = "#06b6d4"
                else:
                    try:
                        d = datetime.strptime(day, "%Y-%m-%d")
                        day_label = d.strftime("%A, %b %d")
                    except Exception:
                        day_label = day
                    header_color = "#475569"

                st.markdown(
                    f"""<div style="font-size:0.75rem; font-weight:700; color:{header_color};
                                    text-transform:uppercase; letter-spacing:0.08em;
                                    margin: 0.8rem 0 0.3rem; padding-bottom:0.2rem;
                                    border-bottom:1px solid #1e293b;">
                        {day_label}
                    </div>""",
                    unsafe_allow_html=True,
                )

                for s in by_date[day]:
                    if shown >= 5:
                        break
                    priority     = s.get("priority", "medium")
                    session_type = s.get("session_type", "Practice")
                    icon         = type_icons.get(session_type, "📚")
                    dot          = priority_dots.get(priority, "🟡")
                    pcolor       = priority_colors.get(priority, "#f59e0b")
                    topic_name   = s["topic"]
                    # Truncate long topic names
                    display_topic = topic_name if len(topic_name) <= 28 else topic_name[:25] + "\u2026"

                    # Context bar
                    tscore = topic_score_lookup.get(topic_name, None)
                    bar_section = ""
                    if tscore is not None:
                        bcolor = "#10b981" if tscore >= 70 else "#f59e0b" if tscore >= 50 else "#ef4444"
                        pct = int(min(tscore, 100))
                        sc  = int(tscore)
                        bar_section = (
                            '<div style="display:flex;align-items:center;gap:0.4rem;margin-top:0.25rem;">'
                            '<div style="flex:1;height:3px;background:#0f172a;border-radius:2px;overflow:hidden;">'
                            '<div style="width:' + str(pct) + '%;height:100%;background:' + bcolor + ';border-radius:2px;"></div>'
                            '</div>'
                            '<span style="font-size:0.65rem;color:' + bcolor + ';font-weight:700;min-width:2rem;">' + str(sc) + '%</span>'
                            '</div>'
                        )

                    card_html = (
                        '<div style="background:#1e293b;border:1px solid #334155;border-left:3px solid ' + pcolor + ';'
                        'border-radius:6px;padding:0.5rem 0.75rem;margin-bottom:0.3rem;">'
                        '<div style="display:flex;align-items:center;justify-content:space-between;gap:0.5rem;">'
                        '<div style="flex:1;min-width:0;">'
                        '<span style="font-size:0.82rem;font-weight:600;color:#f1f5f9;white-space:nowrap;'
                        'overflow:hidden;text-overflow:ellipsis;display:block;">' + icon + ' ' + display_topic + '</span>'
                        '<span style="font-size:0.7rem;color:#64748b;">' + session_type + '</span>'
                        '</div>'
                        '<span style="font-size:0.8rem;">' + dot + '</span>'
                        '</div>'
                        + bar_section +
                        '</div>'
                    )
                    st.markdown(card_html, unsafe_allow_html=True)
                    shown += 1

            # "View all" link if more than 5
            if len(upcoming) > 5:
                remaining = len(upcoming) - 5
                st.markdown(
                    f"""<div style="text-align:right; margin-top:0.2rem;">
                        <span style="font-size:0.75rem; color:#6366f1; cursor:pointer;">
                            +{remaining} more
                        </span>
                    </div>""",
                    unsafe_allow_html=True,
                )
            if st.button(t("view_all_sessions"), key="go_schedule_view", use_container_width=True):
                st.switch_page("pages/5_Schedule.py")
        else:
            st.markdown(
                f"""<div style="text-align:center; color:#64748b; padding:1.5rem;">
                    {t('no_sessions_scheduled')}
                </div>""", unsafe_allow_html=True)
            if st.button(t("generate_study_plan"), key="go_schedule"):
                st.switch_page("pages/5_Schedule.py")


# ── Feature 4: Topics Needing Attention — deep-dive ───────────────
st.markdown("---")
if weak_topics:
    st.markdown(f"### {t('topics_needing_attention')}")

    # Build priority index = (1 - accuracy/100) × exam_weight  — higher = more urgent
    def _priority_index(topic_name: str, score: float) -> float:
        weight = TOPIC_WEIGHTS.get(topic_name, 8)
        return round((1 - score / 100) * weight, 2)

    # Sort weak topics by priority index (descending)
    weak_sorted = sorted(
        weak_topics,
        key=lambda w: _priority_index(w["topic"], w["avg_score"]),
        reverse=True,
    )

    for w in weak_sorted:
        score      = w["avg_score"]
        topic_name = w["topic"]
        sessions_done = w["sessions_done"]
        last_studied  = w.get("last_studied") or ""
        exam_weight   = TOPIC_WEIGHTS.get(topic_name, 8)
        pindex        = _priority_index(topic_name, score)
        topic_color   = CFA_TOPICS.get(topic_name, {}).get("color", "#6366f1")

        # Score color
        score_color = "#ef4444" if score < 40 else "#f59e0b"

        # Days since last studied
        days_since_html = ""
        if last_studied:
            try:
                ls_date = datetime.fromisoformat(last_studied[:10]).date()
                days_ago = (date.today() - ls_date).days
                if days_ago > 7:
                    days_since_html = f'<span style="background:rgba(239,68,68,0.15); color:#fca5a5; border-radius:4px; padding:1px 6px; font-size:0.68rem; font-weight:600;">⚠️ {days_ago} {t("days_ago")}</span>'
                else:
                    days_since_html = f'<span style="color:#64748b; font-size:0.68rem;">{t("last_studied")}: {days_ago} {t("days_ago")}</span>'
            except Exception:
                days_since_html = f'<span style="color:#64748b; font-size:0.68rem;">{t("last_studied")}: —</span>'
        else:
            days_since_html = f'<span style="color:#64748b; font-size:0.68rem;">{t("last_studied")}: {t("never")}</span>'

        # Sub-topic data for this topic
        sub_data = sorted(
            subtopic_by_topic.get(topic_name, []),
            key=lambda x: x["avg_score"]
        )  # already sorted ASC (weakest first) from DB query

        with st.expander(
            f"{topic_name}  —  {score:.0f}%  ·  {sessions_done} {t('sessions')}  ·  {exam_weight}% {t('exam_weight')}",
            expanded=True,
        ):
            col_main, col_sub = st.columns([1, 1.4])

            with col_main:
                # Score gauge
                st.markdown(
                    f"""
                    <div style="background:#0f172a; border:1px solid {topic_color}30;
                                border-radius:10px; padding:1.2rem; text-align:center; margin-bottom:0.8rem;">
                        <div style="font-size:2.8rem; font-weight:900; color:{score_color};
                                    line-height:1;">{score:.0f}%</div>
                        <div style="color:#94a3b8; font-size:0.78rem; margin-top:0.3rem;">{topic_name}</div>
                        <div style="margin-top:0.6rem; height:6px; background:#1e293b; border-radius:3px; overflow:hidden;">
                            <div style="width:{min(score,100):.0f}%; height:100%;
                                        background: linear-gradient(90deg, {score_color}, {score_color}88);
                                        border-radius:3px;"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Meta badges row
                st.markdown(
                    f"""
                    <div style="display:flex; flex-wrap:wrap; gap:0.4rem; margin-bottom:0.8rem;">
                        <span style="background:{topic_color}22; color:{topic_color}; border:1px solid {topic_color}44;
                                     border-radius:5px; padding:2px 8px; font-size:0.7rem; font-weight:600;">
                            📊 {exam_weight}% {t('exam_weight')}
                        </span>
                        <span style="background:rgba(99,102,241,0.12); color:#818cf8; border:1px solid rgba(99,102,241,0.3);
                                     border-radius:5px; padding:2px 8px; font-size:0.7rem; font-weight:600;">
                            🎯 {t('priority_index')}: {pindex:.1f}
                        </span>
                        {days_since_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Practice Now button
                if st.button(
                    t("practice_now"),
                    key=f"practice_{topic_name}",
                    use_container_width=True,
                    type="primary",
                ):
                    st.session_state["prefill_topic"] = topic_name
                    st.switch_page("pages/2_Practice.py")

            with col_sub:
                st.markdown(
                    f"""<div style="font-size:0.78rem; font-weight:700; color:#94a3b8;
                                    text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.6rem;">
                        {t('subtopic_breakdown')}
                    </div>""",
                    unsafe_allow_html=True,
                )

                if sub_data:
                    for sp in sub_data[:5]:  # show top 5 weakest sub-topics
                        sp_score   = sp["avg_score"]
                        sp_answers = sp["total_answers"]
                        sp_name    = sp["subtopic"]
                        # Truncate long subtopic names
                        sp_display = sp_name if len(sp_name) <= 42 else sp_name[:39] + "…"
                        sp_color   = "#ef4444" if sp_score < 40 else "#f59e0b" if sp_score < 70 else "#10b981"
                        pct        = min(sp_score, 100)

                        st.markdown(
                            f"""
                            <div style="margin-bottom:0.55rem;">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2px;">
                                    <span style="font-size:0.75rem; color:#cbd5e1; max-width:75%;
                                                 overflow:hidden; text-overflow:ellipsis; white-space:nowrap;"
                                          title="{sp_name}">
                                        {sp_display}
                                    </span>
                                    <span style="font-size:0.72rem; font-weight:700; color:{sp_color}; min-width:2.5rem; text-align:right;">
                                        {sp_score:.0f}%
                                    </span>
                                </div>
                                <div style="height:4px; background:#1e293b; border-radius:2px; overflow:hidden;">
                                    <div style="width:{pct:.0f}%; height:100%;
                                                background: linear-gradient(90deg, {sp_color}, {sp_color}88);
                                                border-radius:2px;"></div>
                                </div>
                                <div style="font-size:0.62rem; color:#475569; margin-top:1px;">
                                    {sp_answers} {t('questions_answered')}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown(
                        f"""<div style="color:#64748b; font-size:0.8rem; font-style:italic; padding:1rem 0;">
                            {t('no_subtopic_data')}
                        </div>""",
                        unsafe_allow_html=True,
                    )

elif topic_perf:
    # Has data but no weak topics — all good
    st.markdown(
        f"""<div class="cfa-card" style="text-align:center; color:#10b981; padding:1.5rem; margin-top:1rem;">
            {t('all_looking_good')}
        </div>""",
        unsafe_allow_html=True,
    )
