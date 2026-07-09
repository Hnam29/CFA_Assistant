"""
pages/5_Schedule.py — Kanban-style learning scheduler with spaced repetition.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import textwrap
from datetime import date, timedelta, datetime
from database.db import (
    init_db, get_topic_performance, get_user_sessions,
    get_upcoming_sessions, save_scheduled_sessions, mark_session_done,
    add_manual_session, delete_scheduled_session,
    get_all_scheduled_sessions_by_status,
)
from utils.auth import is_logged_in, get_current_user, render_auth_page
from utils.cfa_topics import TOPIC_NAMES, get_subtopics
from utils.i18n import t
from core.scheduler_engine import generate_schedule, get_study_insights, generate_rule_based_schedule

st.set_page_config(page_title="Schedule · CFA Assistant", page_icon="📅", layout="wide")

css = Path(__file__).parent.parent / "assets" / "styles.css"
if css.exists():
    st.markdown(f"<style>{css.read_text()}</style>", unsafe_allow_html=True)

def draw_html_calendar(pending_sessions):
    import calendar
    from datetime import date
    
    today = date.today()
    yr, mo = today.year, today.month
    
    # Group pending sessions by date
    sessions_by_date = {}
    for s in pending_sessions:
        raw_d = s.get("scheduled_date", "")
        d_str = raw_d.isoformat() if hasattr(raw_d, "isoformat") else str(raw_d)[:10]
        if d_str not in sessions_by_date:
            sessions_by_date[d_str] = []
        sessions_by_date[d_str].append(s)
        
    cal = calendar.Calendar(firstweekday=6) # Sunday start
    month_days = cal.monthdayscalendar(yr, mo)
    month_name = today.strftime("%B %Y")
    
    html = f"""
    <style>
    .cal-day-box {{
        position: relative;
        cursor: pointer;
    }}
    .cal-tooltip {{
        position: absolute;
        bottom: 105%;
        left: 50%;
        transform: translateX(-50%) translateY(5px);
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 0.5rem 0.7rem;
        width: 200px;
        color: #f1f5f9;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        z-index: 9999;
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
        transition: opacity 0.15s ease, transform 0.15s ease;
    }}
    .cal-day-box:hover .cal-tooltip {{
        opacity: 1;
        visibility: visible;
        transform: translateX(-50%) translateY(0);
    }}
    .cal-tooltip-title {{
        font-weight: 700;
        font-size: 0.7rem;
        border-bottom: 1px solid #334155;
        padding-bottom: 4px;
        margin-bottom: 5px;
        color: #94a3b8;
        text-align: left;
    }}
    .cal-tooltip-item {{
        font-size: 0.7rem;
        margin-bottom: 4px;
        line-height: 1.3;
        display: flex;
        align-items: flex-start;
        gap: 5px;
        text-align: left;
    }}
    </style>
    <div style="background:#0f172a; border:1px solid #1e293b; border-radius:14px; padding:1rem; margin:0 auto 1.5rem auto; max-width:640px; box-shadow:0 4px 20px rgba(0,0,0,0.15); overflow:visible;">
        <h4 style="color:#f1f5f9; margin:0 0 0.75rem 0; font-size:0.95rem; display:flex; align-items:center; gap:0.4rem; font-weight:700;">
            {t("sch_cal", month=month_name)}
        </h4>
        <div style="display:grid; grid-template-columns: repeat(7, 1fr); gap:4px; text-align:center; font-size:0.75rem; font-weight:600; color:#64748b; margin-bottom:4px;">
            <div>Sun</div><div>Mon</div><div>Tue</div><div>Wed</div><div>Thu</div><div>Fri</div><div>Sat</div>
        </div>
        <div style="display:grid; gap:4px;">
    """
    
    for week in month_days:
        html += '<div style="display:grid; grid-template-columns: repeat(7, 1fr); gap:4px;">'
        for day in week:
            if day == 0:
                html += '<div style="background:transparent; min-height:42px;"></div>'
            else:
                curr_date_str = f"{yr}-{mo:02d}-{day:02d}"
                day_sessions = sessions_by_date.get(curr_date_str, [])
                
                # Check if it's today
                is_today = (day == today.day)
                bg = "rgba(99,102,241,0.1)" if is_today else "#1e293b"
                border = "1px solid #6366f1" if is_today else "1px solid #334155"
                
                dots_html = ""
                tooltip_items_html = ""
                for s in day_sessions:
                    stype = s.get("session_type", "Practice")
                    # Color code: Practice = yellow (#f59e0b), Mock Exam = purple/blue (#a855f7), Review = green (#10b981)
                    color = "#f59e0b"
                    icon = "🎯"
                    if stype == "Mock Exam":
                        color = "#a855f7"
                        icon = "📝"
                    elif stype == "Review":
                        color = "#10b981"
                        icon = "📖"
                    dots_html += f'<div style="background:{color}; width:5px; height:5px; border-radius:50%; display:inline-block; margin:1px;"></div>'
                    tooltip_items_html += f'<div class="cal-tooltip-item"><span style="color:{color};">{icon}</span><span><strong>{s.get("topic")}</strong><br/><span style="color:#64748b; font-size:0.65rem;">{stype}</span></span></div>'
                
                tooltip_html = ""
                if day_sessions:
                    d_obj = date(yr, mo, day)
                    date_label = d_obj.strftime("%a, %b %d")
                    tooltip_html = f"""
                    <div class="cal-tooltip">
                        <div class="cal-tooltip-title">📅 Plans for {date_label}</div>
                        {tooltip_items_html}
                    </div>
                    """
                
                html += f"""
                <div class="cal-day-box" style="background:{bg}; border:{border}; border-radius:6px; min-height:42px; padding:2px; display:flex; flex-direction:column; justify-content:space-between; align-items:center;">
                    <span style="font-weight:700; color:{'#6366f1' if is_today else '#f1f5f9'}; font-size:0.75rem;">{day}</span>
                    <div style="display:flex; flex-wrap:wrap; justify-content:center; gap:1px; max-width:100%; overflow:hidden; padding-bottom:1px;">
                        {dots_html}
                    </div>
                    {tooltip_html}
                </div>
                """
        html += '</div>'
        
    html += """
        </div>
        <div style="display:flex; gap:1rem; font-size:0.7rem; color:#94a3b8; margin-top:0.6rem; justify-content:center; border-top:1px solid #1e293b; padding-top:0.6rem;">
            <div style="display:flex; align-items:center; gap:4px;"><div style="background:#f59e0b; width:6px; height:6px; border-radius:50%;"></div> Practice</div>
            <div style="display:flex; align-items:center; gap:4px;"><div style="background:#a855f7; width:6px; height:6px; border-radius:50%;"></div> Mock Exam</div>
            <div style="display:flex; align-items:center; gap:4px;"><div style="background:#10b981; width:6px; height:6px; border-radius:50%;"></div> Review</div>
        </div>
    </div>
    """
    # Sanitize newlines and redundant spaces to prevent Streamlit from wrapping in code blocks
    cleaned_html = " ".join([line.strip() for line in html.splitlines()])
    return cleaned_html

# Kanban CSS
st.markdown("""
<style>
.kanban-board { display:flex; gap:1rem; overflow-x:auto; padding-bottom:1rem; }
.kanban-col {
    flex: 0 0 280px;
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 0.85rem;
    max-height: 72vh;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: #334155 #0f172a;
}
.kanban-col-header {
    font-size: 0.78rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.7rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.kanban-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 0.75rem 0.85rem;
    margin-bottom: 0.55rem;
    transition: border-color 0.2s, transform 0.15s;
    position: relative;
}
.kanban-card:hover { border-color: #6366f1; transform: translateY(-1px); }
.kcard-topic { font-weight: 700; font-size: 0.85rem; color: #f1f5f9; }
.kcard-sub { font-size: 0.75rem; color: #64748b; margin-top: 1px; }
.kcard-date { font-size: 0.7rem; color: #475569; margin-top: 0.35rem; }
.kcard-reason { font-size: 0.72rem; color: #94a3b8; margin-top: 0.4rem; font-style: italic; line-height: 1.45; }
.kcard-badge {
    display: inline-block;
    padding: 1px 8px;
    border-radius: 99px;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    margin-top: 0.4rem;
}
.badge-high { background: #7f1d1d; color: #fca5a5; }
.badge-medium { background: #78350f; color: #fcd34d; }
.badge-low { background: #14532d; color: #86efac; }
.settings-panel {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

init_db()
if not is_logged_in():
    st.session_state["show_auth"] = "login"
    st.switch_page("app.py")
    st.stop()

user = get_current_user()
uid  = user["id"]

from utils.sidebar import render_sidebar
render_sidebar()

# ── Header ────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="margin-bottom:1.5rem;">
        <h1 style="font-size:1.9rem; font-weight:800; color:#f1f5f9; margin:0;">
            {t("sch_title")}
        </h1>
        <p style="color:#64748b; margin-top:0.3rem;">
            Kanban-style study planning with AI-powered spaced repetition
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Data fetch ────────────────────────────────────────────────────
topic_perf  = get_topic_performance(uid)
sessions    = get_user_sessions(uid, limit=20)
all_by_status = get_all_scheduled_sessions_by_status(uid)

# ─────────────────────────────────────────────────────────────────
# OPTION SETTINGS PANEL (above Kanban)
# ─────────────────────────────────────────────────────────────────
with st.expander(t("sch_plan_gen"), expanded=False):
    tab_system, tab_manual, tab_insights = st.tabs([t("sch_auto"), t("sch_manual"), t("sch_insights")])

    with tab_system:
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            engine_mode = st.radio(
                "Schedule Engine",
                ["🔌 Rule-Based (Spaced Repetition)", "🤖 AI-Powered (Online)"],
                key="sys_engine_mode"
            )
            subject_filter = st.selectbox(
                "📚 Subject Filter",
                ["All Topics"] + TOPIC_NAMES,
                key="sys_subject_filter",
            )
        with col_b:
            days_ahead = st.slider("Planning horizon (days)", min_value=7, max_value=30, value=14, step=7, key="sys_days_ahead")
            exam_date_toggle = st.checkbox("Target exam date", key="sys_exam_toggle")
            exam_date_str = None
            if exam_date_toggle:
                exam_date = st.date_input("Exam Date", min_value=date.today() + timedelta(days=7), key="sys_exam_date")
                exam_date_str = exam_date.isoformat()
        with col_c:
            free_slots = st.multiselect(
                "📆 Availability",
                ["Weekday mornings", "Weekday evenings", "Weekday lunch",
                 "Saturday mornings", "Saturday afternoons",
                 "Sunday mornings", "Sunday afternoons", "Weekends"],
                default=["Weekday evenings", "Saturday mornings"],
                key="sys_free_slots",
            )

        if st.button(t("sch_auto_btn"), use_container_width=True, type="primary", key="gen_sys_plan"):
            spinner_msg = (
                "🧠 Running spaced repetition algorithm..."
                if engine_mode == "🔌 Rule-Based (Spaced Repetition)"
                else "🧠 AI is building your personalized schedule..."
            )
            with st.spinner(spinner_msg):
                try:
                    if engine_mode == "🤖 AI-Powered (Online)":
                        raw_sessions = generate_schedule(
                            topic_performance=topic_perf,
                            completed_sessions=sessions,
                            free_slots=free_slots or None,
                            days_ahead=days_ahead,
                            exam_date=exam_date_str,
                        )
                        if subject_filter != "All Topics":
                            raw_sessions = [s for s in raw_sessions if s["topic"] == subject_filter]
                    else:
                        raw_sessions = generate_rule_based_schedule(
                            topic_performance=topic_perf,
                            completed_sessions=sessions,
                            days_ahead=days_ahead,
                            exam_date=exam_date_str,
                            subject_filter=None if subject_filter == "All Topics" else subject_filter,
                            free_slots=free_slots or None,
                        )

                    if raw_sessions:
                        save_scheduled_sessions(uid, raw_sessions, creator="system")
                        st.success(f"✅ Generated {len(raw_sessions)} sessions! Refresh the Kanban board below.")
                        st.rerun()
                    else:
                        st.error("No sessions generated. Adjust availability/subject filters.")
                except Exception as e:
                    st.error(f"Error: {e}")

    with tab_manual:
        st.markdown(f"**{t('sch_manual')}**")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            manual_date = st.date_input(t("sch_date"), min_value=date.today(), key="man_date")
            manual_topic = st.selectbox(t("sch_topic"), TOPIC_NAMES, key="man_topic")
            manual_subtopic = st.selectbox(
                t("sch_subtopic"),
                ["(none)"] + get_subtopics(st.session_state.get("man_topic", TOPIC_NAMES[0])),
                key="man_subtopic"
            )
        with col_m2:
            manual_type = st.selectbox(t("sch_type"), ["Practice", "Mock Exam", "Review"], key="man_type")
            manual_priority = st.selectbox(t("sch_priority"), ["high", "medium", "low"], index=1, key="man_priority")
            manual_reason = st.text_input("Reason / Note", placeholder="e.g. Cover Reading 15 & do 25 Qs", key="man_reason")
        if st.button("✍️ Add to Planner", type="primary", key="add_man_btn"):
            try:
                subtopic_val = manual_subtopic if manual_subtopic != "(none)" else ""
                add_manual_session(
                    user_id=uid,
                    scheduled_date=manual_date.isoformat(),
                    topic=manual_topic,
                    session_type=manual_type,
                    priority=manual_priority,
                    reason=f"[{subtopic_val}] {manual_reason}".strip(" []") if subtopic_val else manual_reason
                )
                st.success("✅ Session added to your Kanban board!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with tab_insights:
        st.caption("Get an AI analysis of your learning patterns and study priorities.")
        if st.button("💡 Get Personalized Insights", type="primary", key="get_insights"):
            with st.spinner("Analyzing your learning patterns..."):
                try:
                    insights = get_study_insights(topic_perf, sessions)
                    st.session_state["ai_insights"] = insights
                except Exception as e:
                    st.error(f"Error: {e}")
        if "ai_insights" in st.session_state:
            st.markdown(st.session_state["ai_insights"])


# ─────────────────────────────────────────────────────────────────
# CALENDAR
# ─────────────────────────────────────────────────────────────────
st.markdown(draw_html_calendar(all_by_status.get("pending", [])), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# KANBAN BOARD
# ─────────────────────────────────────────────────────────────────
today_str = date.today().isoformat()

# Auto-mark overdue pending sessions as 'skipped'
for s in all_by_status["pending"]:
    # scheduled_date may be a date object (Postgres) or string (SQLite)
    raw_date = s.get("scheduled_date", today_str)
    session_date_str = raw_date.isoformat() if hasattr(raw_date, "isoformat") else str(raw_date)[:10]
    if session_date_str < today_str:
        try:
            from database.db import get_connection
            with get_connection() as conn:
                conn.execute(
                    "UPDATE scheduled_sessions SET status='skipped' WHERE id=?",
                    (s["id"],)
                )
        except Exception:
            pass

# Re-fetch after any auto-updates
all_by_status = get_all_scheduled_sessions_by_status(uid)

COLUMNS = [
    {
        "key": "pending",
        "label": t("sch_pending"),
        "color": "#6366f1",
        "border_color": "#6366f1",
        "empty_msg": "No pending sessions. Generate a plan above!",
        "count_color": "#818cf8",
    },
    {
        "key": "done",
        "label": t("sch_done"),
        "color": "#10b981",
        "border_color": "#10b981",
        "empty_msg": "Complete a session to see it here.",
        "count_color": "#34d399",
    },
    {
        "key": "skipped",
        "label": t("sch_skipped"),
        "color": "#f59e0b",
        "border_color": "#f59e0b",
        "empty_msg": "No skipped sessions.",
        "count_color": "#fbbf24",
    },
]

# Render each column side-by-side using Streamlit columns
kanban_cols = st.columns(len(COLUMNS))

for col_idx, col_def in enumerate(COLUMNS):
    items = all_by_status.get(col_def["key"], [])

    with kanban_cols[col_idx]:
        # Column header - single line HTML construction
        header_html = f'<div class="kanban-col-header" style="color:{col_def["color"]};border-color:{col_def["border_color"]};">{col_def["label"]}<span style="background:{col_def["border_color"]}22;color:{col_def["count_color"]};padding:1px 8px;border-radius:99px;font-size:0.7rem;margin-left:0.5rem;">{len(items)}</span></div>'
        st.markdown(header_html, unsafe_allow_html=True)

        if not items:
            empty_html = f'<div style="text-align:center;padding:2rem 0.5rem;color:#475569;font-size:0.8rem;">{col_def["empty_msg"]}</div>'
            st.markdown(empty_html, unsafe_allow_html=True)
        else:
            for s in items:
                priority = s.get("priority", "medium")
                session_type = s.get("session_type", "Practice")
                type_icons = {"Practice": "🎯", "Mock Exam": "📝", "Review": "📖"}
                icon = type_icons.get(session_type, "📚")
                subtopic = s.get("subtopic", "") or ""
                reason = s.get("reason", "") or ""

                try:
                    raw_d = s.get("scheduled_date", "")
                    date_str = raw_d.isoformat() if hasattr(raw_d, "isoformat") else str(raw_d)[:10]
                    d = datetime.strptime(date_str, "%Y-%m-%d")
                    is_today = date_str == today_str
                    date_label = ("🔥 Today" if is_today else d.strftime("%a, %b %d"))
                except Exception:
                    date_label = s.get("scheduled_date", "")

                # Construct single-line card HTML to avoid any Markdown indentation bugs
                card_html = f'<div class="kanban-card">'
                card_html += f'<div class="kcard-topic">{icon} {s["topic"]}</div>'
                if subtopic:
                    card_html += f'<div class="kcard-sub">📌 {subtopic}</div>'
                card_html += f'<div class="kcard-date">📅 {date_label} · {session_type}</div>'
                if reason:
                    card_html += f'<div class="kcard-reason">{reason}</div>'
                card_html += f'<div><span class="kcard-badge badge-{priority}">{priority}</span></div>'
                card_html += '</div>'

                st.markdown(card_html, unsafe_allow_html=True)

                # Action buttons below each card
                if col_def["key"] == "pending":
                    if st.button(t("sch_start_test"), key=f"start_{s['id']}", type="primary", use_container_width=True):
                        st.session_state["schedule_launch"] = {
                            "topic": s["topic"],
                            "session_type": s["session_type"],
                        }
                        if s["session_type"].strip() == "Mock Exam":
                            st.switch_page("pages/3_Mock_Exam.py")
                        else:
                            st.switch_page("pages/2_Practice.py")
                            
                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if st.button(t("sch_mark_done"), key=f"done_{s['id']}", use_container_width=True):
                            mark_session_done(s["id"])
                            st.rerun()
                    with btn_c2:
                        if st.button(t("sch_delete"), key=f"del_{s['id']}", use_container_width=True):
                            delete_scheduled_session(s["id"])
                            st.rerun()
                elif col_def["key"] == "skipped":
                    if st.button("↩️ Restore", key=f"restore_{s['id']}", use_container_width=True):
                        try:
                            from database.db import get_connection
                            with get_connection() as conn:
                                conn.execute(
                                    "UPDATE scheduled_sessions SET status='pending' WHERE id=?",
                                    (s["id"],)
                                )
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Error: {ex}")
