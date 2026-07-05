"""
pages/3_Mock_Exam.py — Timed CFA mock exam with weighted topic coverage.
"""

import sys, time, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from database.db import (
    init_db, create_session, complete_session,
    save_question, save_answer, upsert_topic_performance,
    get_topic_performance, get_curriculum_weights,
)
from utils.auth import is_logged_in, get_current_user, render_auth_page
from utils.cfa_topics import TOPIC_NAMES, TOPIC_WEIGHTS, CFA_TOPICS
from utils.charts import topic_bar_chart
from core.question_engine import generate_questions

st.set_page_config(page_title="Mock Exam · CFA Assistant", page_icon="📝", layout="wide")

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

# ── State init ────────────────────────────────────────────────────
for key, default in [
    ("exam_questions", []),
    ("exam_answers", {}),
    ("exam_started", False),
    ("exam_submitted", False),
    ("exam_start_time", None),
    ("exam_duration_mins", 30),
    ("exam_session_id", None),
    ("exam_current_idx", 0),
    ("exam_flags", set()),
    ("exam_confirm_submit", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Header ────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="margin-bottom:2rem;">
        <h1 style="font-size:1.9rem; font-weight:800; color:#f1f5f9; margin:0;">📝 Mock Exam</h1>
        <p style="color:#64748b; margin-top:0.3rem;">
            Timed CFA-style exam with AI-generated questions weighted by your weak areas
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────────────────────────
if not st.session_state.exam_started:
    col_l, col_r = st.columns([1.2, 1])

    with col_l:
        st.markdown('<div class="cfa-card">', unsafe_allow_html=True)
        st.markdown("#### ⚙️ Exam Configuration")

        exam_mode = st.radio(
            "Exam Mode",
            ["Session 1 (90 Q · 135 min)", "Session 2 (90 Q · 135 min)"],
            key="exam_mode",
            horizontal=True,
        )
        # Both sessions: 90 questions, 135 minutes (matches real CFA Level I)
        num_q, duration = 90, 135

        exam_source = st.radio(
            "Exam Source",
            ["🔌 Question Bank (Offline)", "🤖 AI-Generated (Online)"],
            key="exam_source",
            horizontal=True,
        )
        use_bank_only = (exam_source == "🔌 Question Bank (Offline)")

        weighting = st.radio(
            "Question Weighting",
            ["Adaptive (focus on weak areas)", "Official CFA weights"],
            key="exam_weight",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("🚀 Start Mock Exam", use_container_width=True, type="primary", key="start_exam"):
            # Build topic weights
            topic_perf = get_topic_performance(uid)
            perf_map = {p["topic"]: p["avg_score"] for p in topic_perf}
            db_weights = get_curriculum_weights()

            if weighting == "Adaptive (focus on weak areas)" and topic_perf:
                # Inverse score weighting — lower score = more questions
                inverse = {t: max(0, 100 - perf_map.get(t, 50)) for t in TOPIC_NAMES}
                total_inv = sum(inverse.values()) or 1
                weights = {t: v / total_inv for t, v in inverse.items()}
            else:
                # Official CFA weights
                total_w = sum(db_weights.values())
                weights = {t: db_weights[t] / total_w for t in TOPIC_NAMES}

            # Generate questions per-topic (sample a few per topic)
            spinner_msg = (
                f"📦 Loading {num_q} questions from your offline question bank..."
                if use_bank_only
                else f"🤖 Generating {num_q} exam questions — this may take ~30s..."
            )
            with st.spinner(spinner_msg):
                all_qs = []
                for topic, weight in weights.items():
                    n = max(1, round(num_q * weight))
                    try:
                        qs = generate_questions(
                            topic=topic,
                            difficulty="Medium",
                            count=n,
                            use_bank_only=use_bank_only
                        )
                        all_qs.extend(qs)
                    except Exception:
                        continue
                    if len(all_qs) >= num_q:
                        break

            if not all_qs:
                st.error("Failed to generate exam questions. Check your question bank or API key.")
            else:
                random.shuffle(all_qs)
                all_qs = all_qs[:num_q]
                session_id = create_session(uid, "Mixed", "mock")
                st.session_state.exam_questions    = all_qs
                st.session_state.exam_answers      = {}
                st.session_state.exam_started      = True
                st.session_state.exam_submitted    = False
                st.session_state.exam_start_time   = time.time()
                st.session_state.exam_duration_mins = duration
                st.session_state.exam_session_id   = session_id
                st.session_state.exam_current_idx  = 0
                st.session_state.exam_flags        = set()
                st.session_state.exam_confirm_submit = False
                st.rerun()

    with col_r:
        st.markdown(
            """
            <div class="cfa-card" style="height:100%;">
                <div class="section-header">📌 Exam Guidelines</div>
                <ul style="color:#94a3b8; font-size:0.88rem; line-height:2; padding-left:1.2rem;">
                    <li>All questions are 3-option MCQ (A, B, C)</li>
                    <li>90 questions per session · 135 minutes (matches real CFA Level I)</li>
                    <li>Timer counts down — auto-submits on expiry</li>
                    <li>You can skip and return to questions</li>
                    <li>Offline mode uses the pre-loaded question bank</li>
                    <li>Adaptive mode focuses on your weakest topics</li>
                    <li>Detailed score breakdown after submission</li>
                </ul>
                <hr style="border-color:#334155;">
                <div style="color:#64748b; font-size:0.8rem;">
                    ⏱️ <strong style="color:#94a3b8;">Tip:</strong>
                    90 seconds per question = 135 min per session.<br>
                    Complete both sessions to simulate the full exam.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────────
# ACTIVE EXAM (CFA CBT Real Exam UI Simulation)
# ─────────────────────────────────────────────────────────────────
elif st.session_state.exam_started and not st.session_state.exam_submitted:
    questions = st.session_state.exam_questions
    answers   = st.session_state.exam_answers
    flags     = st.session_state.get("exam_flags", set())
    curr_idx  = st.session_state.get("exam_current_idx", 0)
    duration_secs = st.session_state.exam_duration_mins * 60
    elapsed = time.time() - st.session_state.exam_start_time
    remaining = max(0, duration_secs - elapsed)
    total     = len(questions)

    if curr_idx >= total:
        curr_idx = total - 1
    if curr_idx < 0:
        curr_idx = 0
    st.session_state.exam_current_idx = curr_idx
    q = questions[curr_idx]

    mins, secs = divmod(int(remaining), 60)
    timer_class = "timer-danger" if remaining < 120 else "timer-warning" if remaining < 300 else ""

    # Auto-submit on timeout
    if remaining <= 0:
        st.session_state.exam_submitted = True
        st.rerun()

    # Candidate name
    display_name = user["username"]
    try:
        from database.db import get_user_profile
        prof = get_user_profile(uid)
        if prof and prof.get("full_name"):
            display_name = prof["full_name"]
    except Exception:
        pass

    # CBT Outer Window Container
    st.markdown('<div class="cbt-window">', unsafe_allow_html=True)

    # 1. CBT Top Header with Live JS Timer
    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        st.markdown(
            f"""<div class="cbt-top-bar">
                <div><strong>Question: {curr_idx + 1}</strong> of {total} &nbsp;|&nbsp; &#9201;
                    <strong><span id="exam-timer-display">{mins:02d}:{secs:02d}</span></strong>
                </div>
                <div>Candidate: <strong>{display_name}</strong></div>
            </div>""",
            unsafe_allow_html=True,
        )
        # Hidden auto-submit button to avoid page reload on timeout
        st.markdown('<div style="position:absolute; left:-9999px; opacity:0; height:0; width:0; overflow:hidden;">', unsafe_allow_html=True)
        if st.button("Auto Submit", key="exam_auto_submit_trigger"):
            st.session_state.exam_submitted = True
            st.session_state.exam_confirm_submit = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Live JS countdown — updates every second without a Python rerun
        import streamlit.components.v1 as components
        components.html(
            f"""<script>
(function() {{
  var rem = {int(remaining)};
  function pad(n) {{ return (n < 10 ? '0' : '') + n; }}
  function tick() {{
    var m = Math.floor(rem / 60);
    var s = rem % 60;
    try {{
      var el = window.parent.document.getElementById('exam-timer-display');
      if (el) {{
        el.textContent = pad(m) + ':' + pad(s);
        el.style.color = rem < 120 ? '#ef4444' : rem < 300 ? '#f59e0b' : '#f1f5f9';
      }}
    }} catch(e) {{}}
    if (rem <= 0) {{
      try {{
        var btns = window.parent.document.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {{
          if (btns[i].textContent.trim() === 'Auto Submit') {{
            btns[i].click();
            return;
          }}
        }}
      }} catch(e) {{}}
      // Fallback if click fails
      window.parent.location.reload();
      return;
    }}
    rem--;
    setTimeout(tick, 1000);
  }}
  tick();
}})();
</script>""",
            height=0,
        )
    with top_col2:
        if st.button("Finish Test", key="cbt_exam_finish_top", use_container_width=True, type="primary"):
            unanswered = total - len(answers)
            if unanswered > 0 and not st.session_state.exam_confirm_submit:
                st.session_state.exam_confirm_submit = True
                st.rerun()
            else:
                st.session_state.exam_submitted = True
                st.session_state.exam_confirm_submit = False
                st.rerun()

    # Confirmation warning (shown when user clicked Finish/Submit with unanswered questions)
    if st.session_state.exam_confirm_submit:
        unanswered = total - len(answers)
        st.warning(f"⚠️ You still have **{unanswered}** unanswered question(s). Unanswered questions will be marked as incorrect. Do you want to submit anyway?")
        conf_c1, conf_c2, conf_c3 = st.columns([1.5, 1.5, 5])
        with conf_c1:
            if st.button("✅ Yes, submit now", key="exam_confirm_yes", type="primary"):
                st.session_state.exam_submitted = True
                st.session_state.exam_confirm_submit = False
                st.rerun()
        with conf_c2:
            if st.button("↩️ Continue", key="exam_confirm_no"):
                st.session_state.exam_confirm_submit = False
                st.rerun()

    # 2. CBT Green Sub-bar
    st.markdown(
        f"""<div class="cbt-subbar">
            <div>Topic: {q.get('topic', '')} · {q.get('subtopic', '')}</div>
            <div>Mode: CBT Mock Exam ({len(answers)}/{total} answered)</div>
        </div>""",
        unsafe_allow_html=True,
    )

    # 3. CBT Body Area with Left Navigation Palette and Right Question Window
    body_col_left, body_col_right = st.columns([1.4, 8.6])

    with body_col_left:
        # Build the JS-clickable palette HTML — one box per question
        palette_html_items = []
        for idx in range(total):
            ans_key = str(idx)
            is_ans = ans_key in answers
            is_act = (idx == curr_idx)
            is_flg = idx in flags
            q_num = idx + 1

            if is_act:
                bg = "#6366f1"
                border = "#818cf8"
                color = "#fff"
            elif is_ans:
                bg = "#10b981"
                border = "#34d399"
                color = "#fff"
            elif is_flg:
                bg = "#f59e0b"
                border = "#fbbf24"
                color = "#fff"
            else:
                bg = "#1e293b"
                border = "#334155"
                color = "#94a3b8"

            palette_html_items.append(
                f'<div title="Q{q_num}{" 🚩" if is_flg else ""}" '
                f'style="width:36px;height:36px;display:flex;align-items:center;justify-content:center;'
                f'background:{bg};border:1.5px solid {border};border-radius:6px;'
                f'font-size:0.72rem;font-weight:700;color:{color};cursor:pointer;'
                f'flex-shrink:0;transition:transform 0.1s;" '
                f'onclick="window._cfaNav({idx})">{q_num}</div>'
            )

        palette_html = "".join(palette_html_items)

        st.markdown(
            f"""
            <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:0.6rem;
                        height:calc(100vh - 220px);overflow-y:auto;
                        scrollbar-width:thin;scrollbar-color:#334155 #0f172a;">
              <div style="font-size:0.7rem;font-weight:700;color:#475569;text-transform:uppercase;
                          letter-spacing:0.07em;margin-bottom:0.6rem;padding:0 2px;">
                Questions
              </div>
              <div style="display:flex;flex-wrap:wrap;gap:5px;">
                {palette_html}
              </div>
              <div style="margin-top:0.8rem;border-top:1px solid #1e293b;padding-top:0.6rem;">
                <div style="font-size:0.65rem;color:#475569;line-height:1.8;">
                  <span style="display:inline-block;width:10px;height:10px;background:#10b981;border-radius:2px;margin-right:4px;vertical-align:middle;"></span>Answered<br>
                  <span style="display:inline-block;width:10px;height:10px;background:#6366f1;border-radius:2px;margin-right:4px;vertical-align:middle;"></span>Current<br>
                  <span style="display:inline-block;width:10px;height:10px;background:#f59e0b;border-radius:2px;margin-right:4px;vertical-align:middle;"></span>Flagged<br>
                  <span style="display:inline-block;width:10px;height:10px;background:#1e293b;border:1px solid #334155;border-radius:2px;margin-right:4px;vertical-align:middle;"></span>Unanswered
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Hidden nav buttons used by the JS palette click handler
        st.markdown('<div style="display:none">', unsafe_allow_html=True)
        for idx in range(total):
            if st.button(f"__nav_{idx}", key=f"cbt_mock_nav_{idx}"):
                st.session_state.exam_current_idx = idx
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # JS: wire palette clicks to the hidden buttons
        import streamlit.components.v1 as components_nav
        components_nav.html(
            """
            <script>
            window._cfaNav = function(idx) {
              try {
                var btns = window.parent.document.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {
                  if (btns[i].textContent.trim() === '__nav_' + idx) {
                    btns[i].click(); return;
                  }
                }
              } catch(e) {}
            };
            </script>
            """,
            height=0,
        )


    with body_col_right:
        st.markdown('<div class="cbt-body">', unsafe_allow_html=True)

        # Stem
        st.markdown(f'<div class="cbt-stem-box">{q["question"]}</div>', unsafe_allow_html=True)

        ans_key = str(curr_idx)
        current_ans = answers.get(ans_key)
        idx_map = {"A": 0, "B": 1, "C": 2}

        selected = st.radio(
            f"Select option for Q{curr_idx+1}",
            ["A", "B", "C"],
            index=idx_map.get(current_ans) if current_ans in idx_map else None,
            format_func=lambda x, q=q: f"{x}.  {q[f'option_{x.lower()}']}",
            key=f"cbt_mock_radio_{curr_idx}_{st.session_state.exam_session_id}",
            label_visibility="collapsed",
        )

        if selected is not None and answers.get(ans_key) != selected:
            answers[ans_key] = selected
            st.session_state.exam_answers = answers

        # Clear Answer button — lets user unselect their choice
        if ans_key in answers:
            if st.button("❌ Clear Answer", key=f"cbt_mock_clear_{curr_idx}"):
                answers.pop(ans_key, None)
                st.session_state.exam_answers = answers
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # 4. CBT Bottom Controls Bar
    st.markdown('<div class="cbt-footer-bar">', unsafe_allow_html=True)
    btm_c1, btm_c2, btm_c3, btm_c4 = st.columns([1.2, 1, 1, 1.2])
    with btm_c1:
        is_flg = curr_idx in flags
        flag_lbl = "🚩 Unflag" if is_flg else "🏳️ Flag Question"
        if st.button(flag_lbl, key=f"cbt_mock_flag_btn_{curr_idx}", use_container_width=True):
            if is_flg:
                flags.remove(curr_idx)
            else:
                flags.add(curr_idx)
            st.session_state.exam_flags = flags
            st.rerun()
    with btm_c2:
        if st.button("< Back", key=f"cbt_mock_back_{curr_idx}", use_container_width=True, disabled=curr_idx == 0):
            st.session_state.exam_current_idx = curr_idx - 1
            st.rerun()
    with btm_c3:
        if st.button("Next >", key=f"cbt_mock_next_{curr_idx}", use_container_width=True, disabled=curr_idx == total - 1):
            st.session_state.exam_current_idx = curr_idx + 1
            st.rerun()
    with btm_c4:
        if st.button("📊 Submit Exam", key="cbt_mock_submit_btn", use_container_width=True, type="primary"):
            unanswered = total - len(answers)
            if unanswered > 0 and not st.session_state.exam_confirm_submit:
                st.session_state.exam_confirm_submit = True
                st.rerun()
            else:
                st.session_state.exam_submitted = True
                st.session_state.exam_confirm_submit = False
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────────────────────────
else:
    questions  = st.session_state.exam_questions
    answers    = st.session_state.exam_answers
    session_id = st.session_state.exam_session_id
    elapsed_mins = (time.time() - st.session_state.exam_start_time) / 60

    correct_count = sum(
        1 for i, q in enumerate(questions)
        if answers.get(str(i)) == q["correct_answer"]
    )
    score = (correct_count / len(questions)) * 100 if questions else 0

    # Score by topic
    topic_scores: dict[str, list] = {}
    for i, q in enumerate(questions):
        t = q["topic"]
        if t not in topic_scores:
            topic_scores[t] = []
        is_ok = answers.get(str(i)) == q["correct_answer"]
        topic_scores[t].append(1 if is_ok else 0)

    topic_avg = {t: (sum(vs) / len(vs)) * 100 for t, vs in topic_scores.items()}

    # Save
    if session_id:
        try:
            complete_session(session_id, score, len(questions), correct_count, elapsed_mins)
            for t, avg in topic_avg.items():
                upsert_topic_performance(uid, t, avg)
            for i, q in enumerate(questions):
                qid = save_question(
                    q["topic"], q.get("subtopic",""), q["difficulty"],
                    q["question"], q["option_a"], q["option_b"], q["option_c"],
                    q["correct_answer"], q["explanation"],
                )
                save_answer(
                    uid, qid, session_id,
                    answers.get(str(i), ""),
                    answers.get(str(i)) == q["correct_answer"],
                    0.0,
                )
        except Exception:
            pass
        st.session_state.exam_session_id = None

    # Render results
    color = "#10b981" if score >= 70 else "#f59e0b" if score >= 50 else "#ef4444"
    st.markdown(
        f"""
        <div style="text-align:center; padding:2rem 0;">
            <div style="font-size:4.5rem; font-weight:900; color:{color}; line-height:1;">{score:.0f}%</div>
            <div style="font-size:1.4rem; font-weight:700; color:#f1f5f9; margin-top:0.5rem;">
                {'Passed! 🎉' if score >= 70 else 'Below passing threshold'}
            </div>
            <div style="color:#64748b; margin-top:0.4rem;">
                {correct_count}/{len(questions)} correct · {elapsed_mins:.0f} min
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_res1, col_res2 = st.columns([1.2, 1])
    with col_res1:
        st.markdown("### 📊 Score by Topic")
        if topic_avg:
            st.plotly_chart(topic_bar_chart(topic_avg), use_container_width=True, key="exam_topic_bar")

    with col_res2:
        st.markdown("### 📋 Quick Summary")
        for t, avg in sorted(topic_avg.items(), key=lambda x: x[1]):
            icon = "🟢" if avg >= 70 else "🟡" if avg >= 50 else "🔴"
            st.markdown(
                f"""<div style="display:flex;justify-content:space-between;
                               padding:0.4rem 0; border-bottom:1px solid #1e293b;">
                    <span style="color:#94a3b8; font-size:0.85rem;">{icon} {t}</span>
                    <span style="font-weight:600; color:#f1f5f9; font-size:0.85rem;">{avg:.0f}%</span>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("### 📝 Detailed Review")
    for i, q in enumerate(questions):
        user_ans = answers.get(str(i), "?")
        correct  = q["correct_answer"]
        is_ok    = user_ans == correct
        icon = "✅" if is_ok else "❌"
        with st.expander(f"{icon} Q{i+1} — {q.get('topic','')} — {q['question'][:70]}..."):
            st.markdown(f"**Your answer:** {user_ans}. {q.get(f'option_{user_ans.lower()}', 'N/A')}")
            st.markdown(f"**Correct:** {correct}. {q[f'option_{correct.lower()}']}")
            st.markdown(f"**Explanation:** {q['explanation']}")

    col_eb1, col_eb2 = st.columns(2)
    with col_eb1:
        if st.button("🔄 New Exam", use_container_width=True, type="primary", key="new_exam"):
            for k in ["exam_questions","exam_answers","exam_started","exam_submitted","exam_start_time","exam_session_id"]:
                st.session_state.pop(k, None)
            st.rerun()
    with col_eb2:
        if st.button("📅 Update Schedule Based on Results", use_container_width=True, key="go_sched"):
            st.switch_page("pages/5_Schedule.py")
