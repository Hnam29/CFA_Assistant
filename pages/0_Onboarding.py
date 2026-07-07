"""
pages/0_Onboarding.py — Multi-step onboarding wizard for new CFA candidates.

Collects: full name, age, gender, phone, city, CFA level, exam window & year.
Saves to user_profiles with subscription hooks ready for future payment integration.
"""

import sys
from pathlib import Path
from datetime import date, datetime
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from database.db import init_db, create_user_profile, get_user_profile, is_onboarding_done
from utils.auth import is_logged_in, get_current_user, render_auth_page
from utils.cfa_topics import CFA_EXAM_WINDOWS
from utils.i18n import t

st.set_page_config(
    page_title="Welcome · CFA Assistant",
    page_icon="🎓",
    layout="centered",
)

init_db()
if not is_logged_in():
    st.session_state["show_auth"] = "login"
    st.switch_page("app.py")
    st.stop()

user = get_current_user()
uid  = user["id"]

from utils.sidebar import render_sidebar
render_sidebar()

# Show the welcome email sent notification if the user just registered
if "show_welcome_noti" in st.session_state:
    email_sent_to = st.session_state.pop("show_welcome_noti")
    st.success(t("welcome_email_sent_noti", email=email_sent_to))


# ── Pre-fill profile for existing candidates ──────────────────────────────────
if "ob_initialized" not in st.session_state:
    if is_onboarding_done(uid):
        prof = get_user_profile(uid)
        if prof:
            st.session_state.ob_full_name = prof.get("full_name", "")
            st.session_state.ob_age = prof.get("age", 25)
            st.session_state.ob_gender = prof.get("gender", "Male")
            st.session_state.ob_phone = prof.get("phone", "")
            st.session_state.ob_city = prof.get("city", "")
            st.session_state.ob_cfa_level = prof.get("cfa_level", 1)
            st.session_state.ob_exam_window = prof.get("exam_window", None)
            st.session_state.ob_exam_year = prof.get("exam_year", date.today().year)
    st.session_state.ob_initialized = True

# ── Session state ──────────────────────────────────────────────────────────────
if "ob_step" not in st.session_state:
    st.session_state.ob_step = 1

TOTAL_STEPS = 3

# ── Shared CSS ─────────────────────────────────────────────────────────────────
css_path = Path(__file__).parent.parent / "assets" / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
/* Onboarding specific styles */
.ob-hero { text-align:center; padding: 2rem 0 1.5rem; }
.ob-hero h1 {
    font-size: 2.4rem; font-weight: 900;
    background: linear-gradient(135deg, #6366f1, #06b6d4, #10b981);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0;
}
.ob-hero p { color: #64748b; font-size: 1rem; margin-top: 0.5rem; }

/* Step progress bar */
.ob-steps {
    display: flex; align-items: center; justify-content: center;
    gap: 0; margin: 1.5rem auto 2.5rem; max-width: 420px;
}
.ob-step-node {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 0.85rem; flex-shrink: 0;
    transition: all 0.3s ease;
}
.ob-step-node.done   { background: #6366f1; color: white; }
.ob-step-node.active { background: linear-gradient(135deg,#6366f1,#06b6d4); color: white;
                        box-shadow: 0 0 16px #6366f180; }
.ob-step-node.todo   { background: #1e293b; color: #475569; border: 1px solid #334155; }
.ob-step-line { flex: 1; height: 2px; background: #334155; min-width: 32px; }
.ob-step-line.done { background: linear-gradient(90deg, #6366f1, #06b6d4); }

.ob-step-label { text-align:center; color:#64748b; font-size:0.72rem; margin-top:0.3rem; }

.ob-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 2rem 2.5rem 2.5rem;
    margin: 0 auto;
    max-width: 560px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.4);
}
.ob-card h2 { color: #f1f5f9; font-size: 1.35rem; font-weight: 700; margin: 0 0 0.25rem; }
.ob-card .sub { color: #64748b; font-size: 0.88rem; margin-bottom: 1.8rem; }

.exam-window-card {
    background: #0f172a;
    border: 2px solid #334155;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    cursor: pointer;
    transition: all 0.2s;
    margin-bottom: 0.5rem;
}
.exam-window-card.selected {
    border-color: #6366f1;
    background: #1e1b4b;
    box-shadow: 0 0 16px #6366f140;
}
.exam-window-card:hover { border-color: #6366f1; }

.countdown-badge {
    background: linear-gradient(135deg, #1e1b4b, #0c4a6e);
    border: 1px solid #6366f1;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    margin: 1rem 0;
}

.feature-pill {
    display: inline-block;
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 999px;
    padding: 0.3rem 0.8rem;
    font-size: 0.78rem;
    color: #94a3b8;
    margin: 0.2rem;
}
</style>
""", unsafe_allow_html=True)


# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="ob-hero">
    <div style="font-size:2.5rem;">🎓</div>
    <h1>Welcome to CFA Assistant</h1>
    <p>Let's set up your personalized learning path — takes about 60 seconds.</p>
</div>
""", unsafe_allow_html=True)


# ── Progress indicator ─────────────────────────────────────────────────────────
step = st.session_state.ob_step
labels = ["Personal Info", "Exam Details", "All Set!"]

nodes_html = ""
for i in range(1, TOTAL_STEPS + 1):
    if i < step:
        cls = "done"
        icon = "✓"
    elif i == step:
        cls = "active"
        icon = str(i)
    else:
        cls = "todo"
        icon = str(i)
    nodes_html += f'<div class="ob-step-node {cls}">{icon}</div>'
    if i < TOTAL_STEPS:
        line_cls = "done" if i < step else ""
        nodes_html += f'<div class="ob-step-line {line_cls}"></div>'

st.markdown(f"""
<div class="ob-steps">{nodes_html}</div>
<div style="display:flex;justify-content:space-between;max-width:420px;margin:-2rem auto 2rem;">
    {''.join(f'<div class="ob-step-label" style="flex:1;{"font-weight:700;color:#818cf8;" if i+1==step else ""}">{l}</div>' for i,l in enumerate(labels))}
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# STEP 1 — Personal Information
# ─────────────────────────────────────────────────────────────────
if step == 1:
    st.markdown('<div class="ob-card">', unsafe_allow_html=True)
    st.markdown('<h2>👤 Personal Information</h2>', unsafe_allow_html=True)
    st.markdown('<p class="sub">We use this to personalize your study experience and stay in touch.</p>', unsafe_allow_html=True)

    full_name = st.text_input(
        "Full Name *",
        value=st.session_state.get("ob_full_name", ""),
        placeholder="e.g. Nguyen Van Anh",
        key="ob_full_name_input",
    )

    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input(
            "Age *",
            min_value=18, max_value=65,
            value=st.session_state.get("ob_age", 25),
            key="ob_age_input",
        )
    with col2:
        gender = st.selectbox(
            "Gender *",
            ["Male", "Female", "Prefer not to say"],
            index=["Male", "Female", "Prefer not to say"].index(
                st.session_state.get("ob_gender", "Male")
            ),
            key="ob_gender_input",
        )

    col3, col4 = st.columns(2)
    with col3:
        phone = st.text_input(
            "Phone Number",
            value=st.session_state.get("ob_phone", ""),
            placeholder="+84 9xx xxx xxx",
            key="ob_phone_input",
        )
    with col4:
        city = st.text_input(
            "City / Province *",
            value=st.session_state.get("ob_city", ""),
            placeholder="e.g. Ho Chi Minh City",
            key="ob_city_input",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns([1, 2])
    with col_btn2:
        if st.button("Continue →", use_container_width=True, type="primary", key="ob_next_1"):
            errors = []
            if not full_name.strip():
                errors.append("Please enter your full name.")
            if not city.strip():
                errors.append("Please enter your city or province.")
            if errors:
                for e in errors:
                    st.error(e)
            else:
                st.session_state.ob_full_name = full_name.strip()
                st.session_state.ob_age       = int(age)
                st.session_state.ob_gender    = gender
                st.session_state.ob_phone     = phone.strip()
                st.session_state.ob_city      = city.strip()
                st.session_state.ob_step      = 2
                st.rerun()


# ─────────────────────────────────────────────────────────────────
# STEP 2 — CFA Exam Details
# ─────────────────────────────────────────────────────────────────
elif step == 2:
    current_year = date.today().year

    st.markdown('<div class="ob-card">', unsafe_allow_html=True)
    st.markdown('<h2>📅 Your CFA Exam Details</h2>', unsafe_allow_html=True)
    st.markdown('<p class="sub">This lets us build your learning path, set a countdown timer, and apply the right weights for your specific exam cycle.</p>', unsafe_allow_html=True)

    cfa_level = st.radio(
        "CFA Level *",
        options=[1, 2, 3],
        format_func=lambda x: f"Level {x}",
        horizontal=True,
        index=st.session_state.get("ob_cfa_level", 1) - 1,
        key="ob_level_radio",
    )

    st.markdown("---")
    st.markdown("**Exam Window** — CFA exams are offered 4 times per year:")

    # Year selection
    exam_year = st.selectbox(
        "Exam Year *",
        options=[current_year, current_year + 1],
        index=0 if st.session_state.get("ob_exam_year", current_year) == current_year else 1,
        key="ob_year_select",
    )

    # Window selection via friendly cards
    windows = list(CFA_EXAM_WINDOWS.keys())
    window_cols = st.columns(4)
    current_window = st.session_state.get("ob_exam_window", None)

    for i, (window_name, winfo) in enumerate(CFA_EXAM_WINDOWS.items()):
        exam_dt = date(int(exam_year), winfo["month"], winfo["day"])
        is_past = exam_dt < date.today()
        with window_cols[i]:
            selected_class = "selected" if current_window == window_name else ""
            disabled_note  = " ⛔" if is_past else ""
            st.markdown(f"""
            <div class="exam-window-card {selected_class}" id="win_{window_name}">
                <div style="font-size:1.4rem; text-align:center;">
                    {"❄️" if window_name == "February" else "🌸" if window_name == "May" else "☀️" if window_name == "August" else "🍂"}
                </div>
                <div style="font-weight:700;color:#f1f5f9;text-align:center;margin-top:0.3rem;">{window_name}{disabled_note}</div>
                <div style="color:#64748b;font-size:0.72rem;text-align:center;">~{winfo['day']:02d} {window_name[:3]} {exam_year}</div>
            </div>
            """, unsafe_allow_html=True)
            btn_label = "✓ Selected" if current_window == window_name else f"Select {window_name[:3]}"
            if st.button(btn_label, key=f"win_btn_{window_name}", use_container_width=True,
                         type="primary" if current_window == window_name else "secondary",
                         disabled=is_past):
                st.session_state.ob_exam_window = window_name
                current_window = window_name
                st.rerun()

    # Show computed exam date
    if current_window:
        winfo    = CFA_EXAM_WINDOWS[current_window]
        exam_dt  = date(int(exam_year), winfo["month"], winfo["day"])
        days_left = (exam_dt - date.today()).days
        color    = "#10b981" if days_left > 90 else "#f59e0b" if days_left > 30 else "#ef4444"
        st.markdown(f"""
        <div class="countdown-badge">
            <div style="color:#64748b;font-size:0.8rem;">Your exam target</div>
            <div style="font-size:1.3rem;font-weight:800;color:#f1f5f9;margin:0.3rem 0;">
                📅 CFA Level {cfa_level} · {current_window} {exam_year}
            </div>
            <div style="font-size:2rem;font-weight:900;color:{color};">{max(0,days_left)}</div>
            <div style="color:#94a3b8;font-size:0.85rem;">days remaining</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_b1, col_b2, col_b3 = st.columns([1, 1, 1])
    with col_b1:
        if st.button("← Back", use_container_width=True, key="ob_back_2"):
            st.session_state.ob_step = 1
            st.rerun()
    with col_b3:
        if st.button("Continue →", use_container_width=True, type="primary", key="ob_next_2"):
            if not current_window:
                st.error("Please select an exam window.")
            else:
                st.session_state.ob_cfa_level   = int(cfa_level)
                st.session_state.ob_exam_window  = current_window
                st.session_state.ob_exam_year    = int(exam_year)
                st.session_state.ob_step         = 3
                st.rerun()


# ─────────────────────────────────────────────────────────────────
# STEP 3 — Confirmation & Save
# ─────────────────────────────────────────────────────────────────
elif step == 3:
    # Compute final exam date
    exam_window = st.session_state.get("ob_exam_window", "May")
    exam_year   = st.session_state.get("ob_exam_year", date.today().year)
    cfa_level   = st.session_state.get("ob_cfa_level", 1)
    winfo       = CFA_EXAM_WINDOWS.get(exam_window, list(CFA_EXAM_WINDOWS.values())[0])
    exam_date   = date(exam_year, winfo["month"], winfo["day"])
    days_left   = (exam_date - date.today()).days
    color       = "#10b981" if days_left > 90 else "#f59e0b" if days_left > 30 else "#ef4444"

    st.markdown('<div class="ob-card">', unsafe_allow_html=True)
    st.markdown('<h2>🎉 You\'re All Set!</h2>', unsafe_allow_html=True)
    st.markdown('<p class="sub">Here\'s your personalized learning profile. Everything is ready to go.</p>', unsafe_allow_html=True)

    # Profile summary
    st.markdown(f"""
    <div style="background:#0f172a; border:1px solid #334155; border-radius:12px; padding:1.2rem; margin-bottom:1.5rem;">
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.75rem;">
            <div>
                <div style="color:#64748b;font-size:0.72rem;">NAME</div>
                <div style="color:#f1f5f9;font-weight:600;">{st.session_state.get("ob_full_name","")}</div>
            </div>
            <div>
                <div style="color:#64748b;font-size:0.72rem;">LOCATION</div>
                <div style="color:#f1f5f9;font-weight:600;">{st.session_state.get("ob_city","")}</div>
            </div>
            <div>
                <div style="color:#64748b;font-size:0.72rem;">CFA LEVEL</div>
                <div style="color:#f1f5f9;font-weight:600;">Level {cfa_level}</div>
            </div>
            <div>
                <div style="color:#64748b;font-size:0.72rem;">EXAM TARGET</div>
                <div style="color:#f1f5f9;font-weight:600;">{exam_window} {exam_year}</div>
            </div>
        </div>
    </div>

    <div class="countdown-badge" style="margin-bottom:1.5rem;">
        <div style="color:#64748b;font-size:0.78rem;">TIME UNTIL YOUR EXAM</div>
        <div style="font-size:3rem;font-weight:900;color:{color};line-height:1.1;">{max(0,days_left)}</div>
        <div style="color:#94a3b8;font-size:0.85rem;">days</div>
        <div style="color:#64748b;font-size:0.78rem;margin-top:0.4rem;">📅 ~{exam_date.strftime("%d %B %Y")}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Your learning path includes:**")
    st.markdown("""
    <div style="display:flex;flex-wrap:wrap;gap:0.3rem;margin-bottom:1rem;">
        <span class="feature-pill">🎯 Adaptive Practice Questions</span>
        <span class="feature-pill">📝 Timed Mock Exams</span>
        <span class="feature-pill">🤖 AI Tutor Chatbot</span>
        <span class="feature-pill">📅 Smart Study Scheduler</span>
        <span class="feature-pill">📊 Progress Analytics</span>
        <span class="feature-pill">📁 Custom Question Bank</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
    with col_c1:
        if st.button("← Back", use_container_width=True, key="ob_back_3"):
            st.session_state.ob_step = 2
            st.rerun()
    with col_c3:
        if st.button("🚀 Start Learning!", use_container_width=True, type="primary", key="ob_finish"):
            try:
                create_user_profile(
                    user_id     = uid,
                    full_name   = st.session_state.get("ob_full_name", ""),
                    age         = st.session_state.get("ob_age", 25),
                    gender      = st.session_state.get("ob_gender", "Prefer not to say"),
                    phone       = st.session_state.get("ob_phone", ""),
                    city        = st.session_state.get("ob_city", ""),
                    cfa_level   = st.session_state.get("ob_cfa_level", 1),
                    exam_window = exam_window,
                    exam_year   = exam_year,
                    exam_date   = exam_date.isoformat(),
                )
                # Clear onboarding state keys
                for k in ["ob_step","ob_full_name","ob_age","ob_gender","ob_phone","ob_city",
                          "ob_cfa_level","ob_exam_window","ob_exam_year","ob_initialized"]:
                    st.session_state.pop(k, None)
                st.success("Profile saved! Redirecting to your dashboard...")
                st.balloons()
                import time; time.sleep(1.5)
                st.switch_page("pages/1_Dashboard.py")
            except Exception as e:
                st.error(f"Could not save profile: {e}")
