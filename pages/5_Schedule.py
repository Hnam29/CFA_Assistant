"""
pages/5_Schedule.py — AI-powered learning scheduler with spaced repetition.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()
import streamlit as st
from datetime import date, timedelta
from database.db import (
    init_db, get_topic_performance, get_user_sessions,
    get_upcoming_sessions, save_scheduled_sessions, mark_session_done,
    add_manual_session, delete_scheduled_session,
)
from utils.auth import is_logged_in, get_current_user, render_auth_page
from utils.cfa_topics import TOPIC_NAMES
from core.scheduler_engine import generate_schedule, get_study_insights, generate_rule_based_schedule

st.set_page_config(page_title="Schedule · CFA Assistant", page_icon="📅", layout="wide")

css = Path(__file__).parent.parent / "assets" / "styles.css"
if css.exists():
    st.markdown(f"<style>{css.read_text()}</style>", unsafe_allow_html=True)

init_db()
if not is_logged_in():
    render_auth_page()
    st.stop()

user = get_current_user()
uid  = user["id"]

from utils.sidebar import render_sidebar
render_sidebar()

# ── Header ────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="margin-bottom:2rem;">
        <h1 style="font-size:1.9rem; font-weight:800; color:#f1f5f9; margin:0;">
            📅 Learning Scheduler
        </h1>
        <p style="color:#64748b; margin-top:0.3rem;">
            Personalize your study plan with AI or rule-based scheduling, or design your own plan
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Data fetch ────────────────────────────────────────────────────
topic_perf  = get_topic_performance(uid)
sessions    = get_user_sessions(uid, limit=20)

# Helper function to render a list of sessions
def render_upcoming_list(upcoming_sessions, show_delete=False):
    if not upcoming_sessions:
        st.markdown(
            """
            <div class="cfa-card" style="text-align:center; padding:3rem; color:#64748b; margin-bottom:1rem;">
                <div style="font-size:2.5rem; margin-bottom:1rem;">📅</div>
                <div style="font-size:1rem; font-weight:600; color:#94a3b8; margin-bottom:0.5rem;">
                    No sessions scheduled yet
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Group by date
    from collections import defaultdict
    by_date = defaultdict(list)
    for s in upcoming_sessions:
        by_date[s["scheduled_date"]].append(s)

    today_str = date.today().isoformat()
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()

    for day, day_sessions in sorted(by_date.items()):
        if day == today_str:
            day_label = "🔥 Today"
            header_color = "#6366f1"
        elif day == tomorrow_str:
            day_label = "⏰ Tomorrow"
            header_color = "#06b6d4"
        else:
            from datetime import datetime
            try:
                d = datetime.strptime(day, "%Y-%m-%d")
                day_label = d.strftime("%A, %b %d")
            except Exception:
                day_label = day
            header_color = "#475569"

        st.markdown(
            f"""
            <div style="font-size:0.85rem; font-weight:700; color:{header_color};
                        text-transform:uppercase; letter-spacing:0.08em;
                        margin: 1.2rem 0 0.5rem; padding-bottom:0.3rem;
                        border-bottom:1px solid #334155;">
                {day_label}
            </div>
            """,
            unsafe_allow_html=True,
        )

        for s in day_sessions:
            priority     = s.get("priority", "medium")
            badge_class  = f"badge-{priority}"
            session_type = s.get("session_type", "Practice")
            type_icons   = {"Practice": "🎯", "Mock Exam": "📝", "Review": "📖"}
            type_icon    = type_icons.get(session_type, "📚")

            col_card, col_action = st.columns([5, 1.2])
            with col_card:
                st.markdown(
                    f"""
                    <div class="cfa-card cfa-card-accent" style="padding:0.9rem 1rem; margin-bottom:0.4rem;">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                            <div>
                                <div style="font-weight:600; color:#f1f5f9; font-size:0.9rem;">
                                    {type_icon} {s['topic']}
                                </div>
                                <div style="color:#64748b; font-size:0.78rem; margin-top:2px;">
                                    {session_type}
                                </div>
                            </div>
                            <span class="badge {badge_class}">{priority}</span>
                        </div>
                        {f'<div style="color:#94a3b8; font-size:0.78rem; margin-top:0.5rem; font-style:italic; line-height:1.4;">{s["reason"]}</div>' if s.get("reason") else ""}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_action:
                st.write("")
                if st.button("✓", key=f"done_{s['id']}", help="Mark as done", use_container_width=True):
                    mark_session_done(s["id"])
                    st.rerun()
                if show_delete:
                    if st.button("🗑️", key=f"del_{s['id']}", help="Delete session", use_container_width=True):
                        delete_scheduled_session(s["id"])
                        st.rerun()

# ── Split UI into 2 parts using tabs ────────────────────────────────
tab_system, tab_user = st.tabs(["📅 System Plan", "✍️ My Planner"])

# ─────────────────────────────────────────────────────────────────
# TAB 1 — System Plan
# ─────────────────────────────────────────────────────────────────
with tab_system:
    col_left, col_right = st.columns([1, 1.4])
    
    with col_left:
        st.markdown("#### ⚙️ System Schedule Generator")

        engine_mode = st.radio(
            "Schedule Engine",
            ["🔌 Rule-Based (Spaced Repetition)", "🤖 AI-Powered (Online)"],
            key="sys_engine_mode"
        )

        subject_filter = st.selectbox(
            "📚 Subject Filter",
            ["All Topics"] + TOPIC_NAMES,
            key="sys_subject_filter",
            help="Focus the generated schedule on one topic, or plan for all topics."
        )

        days_ahead = st.slider("Planning horizon (days)", min_value=7, max_value=30, value=14, step=7, key="sys_days_ahead")

        exam_date_toggle = st.checkbox("I have a target exam date", key="sys_exam_toggle")
        exam_date_str = None
        if exam_date_toggle:
            exam_date = st.date_input("Exam Date", min_value=date.today() + timedelta(days=7), key="sys_exam_date")
            exam_date_str = exam_date.isoformat()

        st.markdown("**Your availability (optional)**")
        free_slots = st.multiselect(
            "When are you free to study?",
            [
                "Weekday mornings", "Weekday evenings", "Weekday lunch",
                "Saturday mornings", "Saturday afternoons",
                "Sunday mornings", "Sunday afternoons", "Weekends",
            ],
            default=["Weekday evenings", "Saturday mornings"],
            key="sys_free_slots",
        )

        if st.button("🚀 Generate System Study Plan", use_container_width=True, type="primary", key="gen_sys_plan"):
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
                        # Post-filter AI sessions if a specific subject was selected
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
                        st.success(f"✅ Generated {len(raw_sessions)} system study sessions!")
                        st.rerun()
                    else:
                        st.error("No sessions generated. Adjust availability/subject filters.")
                except Exception as e:
                    st.error(f"Error: {e}")

        # AI Insights Section
        st.markdown("---")
        st.markdown("#### 🧠 AI Study Insights")
        st.caption("Get an AI-generated analysis of your learning patterns, weakest areas, and study priorities.")

        if st.button("💡 Get Personalized Insights", use_container_width=True, type="primary", key="get_insights"):
            with st.spinner("Analyzing your learning patterns..."):
                try:
                    insights = get_study_insights(topic_perf, sessions)
                    st.session_state["ai_insights"] = insights
                except Exception as e:
                    st.error(f"Error: {e}")

        if "ai_insights" in st.session_state:
            st.markdown(st.session_state["ai_insights"])

    with col_right:
        st.markdown("#### 📆 System-Designed Study Plan")
        system_upcoming = get_upcoming_sessions(uid, creator="system")
        render_upcoming_list(system_upcoming, show_delete=False)

# ─────────────────────────────────────────────────────────────────
# TAB 2 — My Planner
# ─────────────────────────────────────────────────────────────────
with tab_user:
    col_left_user, col_right_user = st.columns([1, 1.4])
    
    with col_left_user:
        st.markdown("#### ✍️ Add Custom Study Session")

        manual_date = st.date_input("Date", min_value=date.today(), key="man_date")
        manual_topic = st.selectbox("📚 Topic", TOPIC_NAMES, key="man_topic")
        manual_type = st.selectbox("📝 Session Type", ["Practice", "Mock Exam", "Review"], key="man_type")
        manual_priority = st.selectbox("⚡ Priority", ["high", "medium", "low"], index=1, key="man_priority")
        manual_reason = st.text_input("Reason / Note", placeholder="e.g. Cover Reading 15 & do 25 Qs", key="man_reason")
        
        if st.button("✍️ Add to My Planner", type="primary", use_container_width=True, key="add_man_btn"):
            try:
                add_manual_session(
                    user_id=uid,
                    scheduled_date=manual_date.isoformat(),
                    topic=manual_topic,
                    session_type=manual_type,
                    priority=manual_priority,
                    reason=manual_reason
                )
                st.success("✅ Successfully added custom session to your planner!")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding session: {e}")
                
    with col_right_user:
        st.markdown("#### 📆 My Personal Study Planner")
        user_upcoming = get_upcoming_sessions(uid, creator="user")
        render_upcoming_list(user_upcoming, show_delete=True)

# Current Performance Summary removed — see Dashboard → Score by Topic chart for a
# full breakdown with radar, bar chart, and Topics Needing Attention details.
