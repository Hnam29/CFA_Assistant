"""
pages/2_Practice.py — Adaptive AI-generated practice questions.
"""

import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from database.db import (
    init_db, create_session, complete_session,
    save_question, save_answer, upsert_topic_performance,
    get_topic_performance, get_bank_questions, get_bank_stats,
    delete_bank_questions,
)
try:
    from database.db import save_session_state
except ImportError:
    def save_session_state(sid, data): pass
from utils.auth import is_logged_in, get_current_user, render_auth_page
from utils.cfa_topics import TOPIC_NAMES, get_subtopics, DIFFICULTY_LEVELS, normalize_topic_name
from utils.sidebar import render_sidebar
from core.question_engine import generate_questions

st.set_page_config(page_title="Practice · CFA Assistant", page_icon="🎯", layout="wide")

css = Path(__file__).parent.parent / "assets" / "styles.css"
if css.exists():
    st.markdown(f"<style>{css.read_text()}</style>", unsafe_allow_html=True)

init_db()
if not is_logged_in():
    render_auth_page()
    st.stop()

user = get_current_user()
uid = user["id"]

render_sidebar()

# ── State init ────────────────────────────────────────────────────
if "practice_questions" not in st.session_state:
    st.session_state.practice_questions = []
if "practice_answers" not in st.session_state:
    st.session_state.practice_answers = {}
if "practice_submitted" not in st.session_state:
    st.session_state.practice_submitted = False
if "practice_session_id" not in st.session_state:
    st.session_state.practice_session_id = None
if "practice_start_time" not in st.session_state:
    st.session_state.practice_start_time = None
if "practice_current_idx" not in st.session_state:
    st.session_state.practice_current_idx = 0
if "practice_flags" not in st.session_state:
    st.session_state.practice_flags = set()
if "practice_confirm_submit" not in st.session_state:
    st.session_state.practice_confirm_submit = False
if "practice_timer_secs" not in st.session_state:
    st.session_state.practice_timer_secs = 0
if "practice_radio_versions" not in st.session_state:
    st.session_state.practice_radio_versions = {}

# ── Header ────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="margin-bottom:2rem;">
        <h1 style="font-size:1.9rem; font-weight:800; color:#f1f5f9; margin:0;">
            🎯 Adaptive Practice
        </h1>
        <p style="color:#64748b; margin-top:0.3rem;">
            AI-generated questions customized to your learning needs
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────
# SETUP PANEL (shown when no active session)
# ─────────────────────────────────────────────────────────────────
if not st.session_state.practice_questions:
    tab_setup, tab_manage = st.tabs(["🎯 Start Practice", "📁 Manage Question Bank"])
    
    with tab_setup:
        with st.container():
            col_setup, col_info = st.columns([1.2, 1])

            with col_setup:
                st.markdown(
                    """<div class="cfa-card">
                        <div class="section-header">⚙️ Configure Your Practice Session</div>
                    """,
                    unsafe_allow_html=True,
                )

                practice_mode = st.radio(
                    "Practice Mode",
                    ["🔌 Question Bank (Offline)", "🤖 AI-Generated (Online)"],
                    horizontal=True,
                    key="prac_mode"
                )
                use_bank_only = (practice_mode == "🔌 Question Bank (Offline)")

                topic = st.selectbox("📚 Topic", TOPIC_NAMES, key="prac_topic")
                subtopics_available = get_subtopics(topic)
                selected_subtopics = st.multiselect(
                    "🔍 Subtopics (optional — leave blank for all)",
                    subtopics_available,
                    key="prac_subtopics",
                )
                difficulty = st.select_slider(
                    "⚡ Difficulty",
                    options=DIFFICULTY_LEVELS,
                    value="Medium",
                    key="prac_difficulty",
                )
                num_questions = st.slider("📝 Number of Questions", min_value=3, max_value=15, value=5, key="prac_num")

                st.markdown("</div>", unsafe_allow_html=True)

                # Check bank availability for offline mode
                stats = get_bank_stats()
                topic_count = stats.get(topic, 0)

                if use_bank_only and topic_count == 0:
                    st.warning(f"⚠️ Your local question bank is empty for **{topic}**.")
                    st.info("Please click the **📁 Manage Question Bank** tab at the top to upload some custom questions first!")

                if not (use_bank_only and topic_count == 0):
                    if st.button("🚀 Generate Questions", use_container_width=True, type="primary", key="gen_btn"):
                        spinner_msg = (
                            f"📦 Loading {num_questions} questions from your local bank..."
                            if use_bank_only
                            else f"🤖 AI is crafting {num_questions} {difficulty} questions on **{topic}**..."
                        )
                        with st.spinner(spinner_msg):
                            try:
                                questions = generate_questions(
                                    topic=topic,
                                    subtopics=selected_subtopics or None,
                                    difficulty=difficulty,
                                    count=num_questions,
                                    use_bank_only=use_bank_only,
                                )
                                if questions:
                                    session_id = create_session(uid, topic, "practice")
                                    st.session_state.practice_questions = questions
                                    st.session_state.practice_answers = {}
                                    st.session_state.practice_submitted = False
                                    st.session_state.practice_session_id = session_id
                                    st.session_state.practice_start_time = time.time()
                                    st.session_state.practice_current_idx = 0
                                    st.session_state.practice_flags = set()
                                    st.session_state.practice_confirm_submit = False
                                    st.session_state.practice_timer_secs = len(questions) * 90
                                    st.session_state.practice_radio_versions = {}
                                    st.rerun()
                                else:
                                    st.error("Failed to generate questions. Check if your question bank has questions for this topic.")
                            except Exception as e:
                                st.error(f"Error: {e}")

            with col_info:
                st.markdown(
                    """
                    <div class="cfa-card" style="height:100%;">
                        <div class="section-header">💡 How Practice Modes Work</div>
                        <strong style="color:#f1f5f9; display:block; margin-top:0.8rem;">🔌 Question Bank (Offline)</strong>
                        <ul style="color:#94a3b8; font-size:0.85rem; line-height:1.6; padding-left:1.2rem; margin-top:0.3rem;">
                            <li>Runs completely offline using the pre-loaded 720-question bank</li>
                            <li>Bypasses AI API usage and keys entirely</li>
                            <li>Great for standard prep and mock simulation</li>
                        </ul>
                        <strong style="color:#f1f5f9;">🤖 AI-Generated (Online)</strong>
                        <ul style="color:#94a3b8; font-size:0.85rem; line-height:1.6; padding-left:1.2rem; margin-top:0.3rem;">
                            <li>AI prioritizes weak areas based on your study history</li>
                            <li>Fresh questions crafted for each session</li>
                            <li>Integrates uploaded question examples for structure</li>
                        </ul>
                        <hr style="border-color:#334155; margin:0.8rem 0 !important;">
                        <div style="color:#64748b; font-size:0.8rem;">
                            🔑 <strong style="color:#94a3b8;">Tip:</strong> The 720Q question bank is pre-loaded by default. You can also upload your own questions to expand it!
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with tab_manage:
        col_u1, col_u2 = st.columns([1.2, 1])
        with col_u1:
            st.markdown(
                """<div class="cfa-card">
                    <div class="section-header">📥 Import Questions</div>
                """,
                unsafe_allow_html=True,
            )
            st.write("Upload an Excel (`.xlsx`) or CSV (`.csv`) file to add more custom questions. By default, the system is pre-loaded with the 720-question bank.")
            
            # Built-in template Excel download button
            template_data = {
                "Topic": ["Ethical and Professional Standards"],
                "Subtopic": ["Professional Standards of Practice"],
                "Difficulty": ["Medium"],
                "Question": ["Which of the following is most likely a violation of the CFA Institute Code of Ethics?"],
                "Option A": ["Disclosing confidential information about a client to the SEC upon query."],
                "Option B": ["Accepting a luxury gift from a client without informing the employer."],
                "Option C": ["Using trading algorithms based on public market information."],
                "Correct Answer": ["B"],
                "Explanation": ["Standard I(B) Independence and Objectivity states that gifts must be disclosed and approved. Accepting them without informing the employer violates duty to employer."]
            }
            template_df = pd.DataFrame(template_data)
            
            from io import BytesIO
            excel_buffer = BytesIO()
            excel_ready = False
            try:
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    template_df.to_excel(writer, index=False, sheet_name='Template')
                excel_data = excel_buffer.getvalue()
                excel_ready = True
            except Exception:
                template_csv = (
                    "Topic,Subtopic,Difficulty,Question,Option A,Option B,Option C,Correct Answer,Explanation\n"
                    "Ethical and Professional Standards,Professional Standards of Practice,Medium,Which of the following is most likely a violation of the CFA Institute Code of Ethics?,Disclosing confidential information about a client to the SEC upon query.,Accepting a luxury gift from a client without informing the employer.,Using trading algorithms based on public market information.,B,Standard I(B) Independence and Objectivity states that gifts must be disclosed and approved. Accepting them without informing the employer violates duty to employer."
                )
                excel_data = template_csv
                excel_ready = False

            if excel_ready:
                st.download_button(
                    label="📥 Download Excel Template (.xlsx)",
                    data=excel_data,
                    file_name="cfa_question_bank_template.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Download an Excel sheet with pre-configured headers and a sample question. Fill it out and upload it below.",
                    use_container_width=True
                )
            else:
                st.download_button(
                    label="📥 Download CSV Template (.csv)",
                    data=excel_data,
                    file_name="cfa_question_bank_template.csv",
                    mime="text/csv",
                    help="Download a CSV template with pre-configured headers. (Excel engine openpyxl is missing).",
                    use_container_width=True
                )
            
            st.markdown("<br>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "Select Excel or CSV File",
                type=["xlsx", "csv"],
                key="bank_file_uploader"
            )
            
            if "import_success" in st.session_state:
                st.success(st.session_state.pop("import_success"))

            if uploaded_file is not None:
                st.info(f"📄 File loaded: **{uploaded_file.name}**")
                if st.button("🚀 Confirm and Import Questions", key="confirm_import_btn", type="primary", use_container_width=True):
                    try:
                        # Read the file
                        if uploaded_file.name.endswith(".csv"):
                            df = pd.read_csv(uploaded_file)
                        else:
                            try:
                                df = pd.read_excel(uploaded_file)
                            except ImportError:
                                st.error("❌ Excel engine not available. Please install 'openpyxl' (e.g. run `pip install openpyxl`) or upload the file as a CSV (`.csv`) instead.")
                                st.stop()
                        
                        # Normalize columns to lowercase and strip whitespace/underscores for flexible matching
                        norm_cols = {c.lower().replace(" ", "").replace("_", ""): c for c in df.columns}
                        
                        # Required fields
                        required_fields = {
                            "topic": ["topic"],
                            "subtopic": ["subtopic"],
                            "difficulty": ["difficulty"],
                            "question": ["question", "questiontext", "text"],
                            "optiona": ["optiona", "a"],
                            "optionb": ["optionb", "b"],
                            "optionc": ["optionc", "c"],
                            "correctanswer": ["correctanswer", "correct"],
                            "explanation": ["explanation", "explain"]
                        }
                        
                        # Find mapped columns
                        mapped_cols = {}
                        missing_fields = []
                        for key, aliases in required_fields.items():
                            found_col = None
                            for alias in aliases:
                                if alias in norm_cols:
                                    found_col = norm_cols[alias]
                                    break
                            if found_col is not None:
                                mapped_cols[key] = found_col
                            elif key != "subtopic":  # Subtopic is optional
                                missing_fields.append(key)
                        
                        if missing_fields:
                            st.error(f"❌ Missing required columns: {', '.join(missing_fields)}. Please structure your file correctly.")
                        else:
                            import_count = 0
                            # Validate values and insert
                            for index, row in df.iterrows():
                                # Extract fields
                                topic_val = normalize_topic_name(str(row[mapped_cols["topic"]]).strip())
                                subtopic_val = str(row[mapped_cols["subtopic"]]).strip() if "subtopic" in mapped_cols else ""
                                diff_val = str(row[mapped_cols["difficulty"]]).strip().capitalize()
                                q_val = str(row[mapped_cols["question"]]).strip()
                                oa_val = str(row[mapped_cols["optiona"]]).strip()
                                ob_val = str(row[mapped_cols["optionb"]]).strip()
                                oc_val = str(row[mapped_cols["optionc"]]).strip()
                                ans_val = str(row[mapped_cols["correctanswer"]]).strip().upper()
                                exp_val = str(row[mapped_cols["explanation"]]).strip()
                                
                                # Clean/Validate Correct Answer
                                if ans_val not in ["A", "B", "C"]:
                                    continue
                                if diff_val not in ["Easy", "Medium", "Hard"]:
                                    diff_val = "Medium"
                                    
                                save_question(
                                    topic=topic_val,
                                    subtopic=subtopic_val,
                                    difficulty=diff_val,
                                    question_text=q_val,
                                    option_a=oa_val,
                                    option_b=ob_val,
                                    option_c=oc_val,
                                    correct_answer=ans_val,
                                    explanation=exp_val,
                                    source="bank"
                                )
                                import_count += 1
                                
                            st.session_state["import_success"] = f"🎉 Successfully imported {import_count} questions into the local bank!"
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error parsing file: {e}")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_u2:
            st.markdown(
                """<div class="cfa-card">
                    <div class="section-header">📊 Question Bank Status</div>
                """,
                unsafe_allow_html=True,
            )
            stats = get_bank_stats()
            if stats:
                for t, count in stats.items():
                    st.markdown(f"- **{t}**: {count} questions")
                
                st.markdown("---")
                if st.button("🗑️ Clear Local Question Bank", type="secondary", use_container_width=True, key="clear_bank_btn"):
                    delete_bank_questions()
                    st.success("Successfully cleared all questions in the bank.")
                    st.rerun()
            else:
                st.info("Your local question bank is currently empty.")
            
            st.markdown(
                """
                <div style="background:#1e293b; border:1px solid #334155; border-radius:8px; padding:0.75rem; margin-top:1rem; font-size:0.8rem; color:#94a3b8;">
                    <strong>ℹ️ File Template Columns:</strong><br>
                    <code>Topic</code>, <code>Subtopic</code>, <code>Difficulty</code> (Easy/Medium/Hard), <code>Question</code>, <code>Option A</code>, <code>Option B</code>, <code>Option C</code>, <code>Correct Answer</code> (A/B/C), <code>Explanation</code>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# ACTIVE PRACTICE SESSION (CFA CBT Real Exam UI Simulation)
# ─────────────────────────────────────────────────────────────────
elif not st.session_state.practice_submitted:
    questions = st.session_state.practice_questions
    answers   = st.session_state.practice_answers
    flags     = st.session_state.get("practice_flags", set())
    curr_idx  = st.session_state.get("practice_current_idx", 0)
    total     = len(questions)

    # ── Timer ─────────────────────────────────────────────────────
    if st.session_state.practice_start_time is None:
        st.session_state.practice_start_time = time.time()
    elapsed_secs = time.time() - st.session_state.practice_start_time
    timer_total  = st.session_state.get("practice_timer_secs", total * 90)
    remaining    = max(0, timer_total - elapsed_secs)
    t_mins, t_secs = divmod(int(remaining), 60)
    timer_class  = "timer-danger" if remaining < 90 else "timer-warning" if remaining < 270 else ""

    # Auto-submit when time runs out
    if remaining <= 0:
        st.session_state.practice_submitted = True
        st.rerun()

    if curr_idx >= total:
        curr_idx = total - 1
    if curr_idx < 0:
        curr_idx = 0
    st.session_state.practice_current_idx = curr_idx
    q = questions[curr_idx]
    
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
        # Static info row
        st.markdown(
            f"""<div class="cbt-top-bar">
                <div><strong>Question: {curr_idx + 1}</strong> of {total} &nbsp;|&nbsp; &#9201;
                    <strong><span id="prac-timer-display">{t_mins:02d}:{t_secs:02d}</span></strong>
                </div>
                <div>Candidate: <strong>{display_name}</strong></div>
            </div>""",
            unsafe_allow_html=True,
        )
        # Hidden auto-submit button to avoid page reload on timeout
        st.markdown('<div style="position:absolute; left:-9999px; opacity:0; height:0; width:0; overflow:hidden;">', unsafe_allow_html=True)
        if st.button("Auto Submit", key="prac_auto_submit_trigger"):
            st.session_state.practice_submitted = True
            st.session_state.practice_confirm_submit = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Live JS countdown — one epoch per session, synced from Python server time
        # The key includes the start_time so the component is only re-created on new sessions.
        start_t = st.session_state.practice_start_time or time.time()
        epoch_key = int(start_t)
        deadline_epoch = int(start_t) + int(timer_total)
        components.html(
            f"""<script>
(function() {{
  // Use wall-clock deadline so reruns never reset the JS counter
  var deadline = {deadline_epoch} * 1000;  // ms
  function pad(n) {{ return (n < 10 ? '0' : '') + n; }}
  function tick() {{
    var rem = Math.max(0, Math.floor((deadline - Date.now()) / 1000));
    var m = Math.floor(rem / 60);
    var s = rem % 60;
    try {{
      var el = window.parent.document.querySelector('#prac-timer-display');
      if (el) {{ el.textContent = pad(m) + ':' + pad(s); }}
      el.style.color = rem < 90 ? '#ef4444' : rem < 270 ? '#f59e0b' : '#f1f5f9';
    }} catch(e) {{}}

    // Hide the Auto Submit button wrapper in parent document
    try {{
      var btns = window.parent.document.querySelectorAll('button');
      for (var i = 0; i < btns.length; i++) {{
        if (btns[i].textContent.trim() === 'Auto Submit') {{
          var p = btns[i].closest('.element-container');
          if (p) p.style.display = 'none';
        }}
      }}
    }} catch(e) {{}}

    if (rem <= 0) {{
      try {{
        var btns = window.parent.document.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {{
          if (btns[i].textContent.trim() === 'Auto Submit') {{
            btns[i].click(); return;
          }}
        }}
      }} catch(e) {{}}
      window.parent.location.reload();
      return;
    }}
    setTimeout(tick, 500);
  }}
  tick();
}})();
</script>""",
            height=0,
        )
    with top_col2:
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("⏸️ Pause", key="cbt_pause_top", use_container_width=True, help="Save progress and return to dashboard"):
                elapsed_s = time.time() - st.session_state.practice_start_time
                state_data = {
                    "questions": questions,
                    "answers": answers,
                    "current_idx": curr_idx,
                    "flags": list(flags),
                    "elapsed_secs": elapsed_s,
                    "practice_timer_secs": timer_total,
                }
                save_session_state(st.session_state.practice_session_id, state_data)
                
                # Clear session state keys
                for k in ["practice_questions", "practice_answers", "practice_submitted", "practice_session_id", "practice_start_time", "practice_current_idx", "practice_flags", "practice_timer_secs", "practice_radio_versions"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.toast("Progress saved!")
                st.switch_page("pages/1_Dashboard.py")
                st.rerun()

        with btn_c2:
            if st.button("Finish", key="cbt_finish_top", use_container_width=True, type="primary"):
                unanswered = total - len(answers)
                if unanswered > 0 and not st.session_state.practice_confirm_submit:
                    st.session_state.practice_confirm_submit = True
                    st.rerun()
                else:
                    st.session_state.practice_submitted = True
                    st.session_state.practice_confirm_submit = False
                    st.rerun()

    if st.session_state.practice_confirm_submit:
        unanswered = total - len(answers)
        st.warning(f"⚠️ You still have **{unanswered}** unanswered question(s). Unanswered questions will be marked as incorrect. Do you want to finish anyway?")
        conf_c1, conf_c2 = st.columns([1.5, 8.5])
        with conf_c1:
            if st.button("✅ Yes, finish now", key="prac_confirm_yes", type="primary"):
                st.session_state.practice_submitted = True
                st.session_state.practice_confirm_submit = False
                st.rerun()

    # 2. CBT Green Sub-bar
    st.markdown(
        f"""<div class="cbt-subbar">
            <div>Topic: {q.get('topic', '')} · {q.get('subtopic', '')}</div>
            <div>Difficulty: {q.get('difficulty', 'Medium')}</div>
        </div>""",
        unsafe_allow_html=True,
    )

    # 3. CBT Body Area with Left Navigation Palette and Right Question Window
    body_col_left, body_col_right = st.columns([1.2, 8.8])

    with body_col_left:
        st.markdown("<p style='text-align: center; font-weight: bold; margin-bottom: 0.5rem;'>Questions</p>", unsafe_allow_html=True)
        with st.container(height=480):
            for idx in range(total):
                is_ans = str(idx) in answers
                is_act = (idx == curr_idx)
                is_flg = idx in flags

                lbl = f"Q{idx+1}"
                if is_flg:
                    lbl += " 🚩"
                elif is_ans:
                    lbl += " ✓"

                btn_type = "primary" if is_act else "secondary"
                if st.button(lbl, key=f"cbt_nav_{idx}", use_container_width=True, type=btn_type):
                    st.session_state.practice_current_idx = idx
                    st.session_state.practice_confirm_submit = False
                    st.rerun()

    with body_col_right:
        # Stem
        st.markdown(f'<div class="cbt-stem-box">{q["question"]}</div>', unsafe_allow_html=True)
        
        is_answered = str(curr_idx) in answers
        user_choice = answers[str(curr_idx)]["selected"] if is_answered else None
        idx_map = {"A": 0, "B": 1, "C": 2}
        radio_ver = st.session_state.practice_radio_versions.get(curr_idx, 0)

        selected = st.radio(
            f"Select option for Q{curr_idx+1}",
            ["A", "B", "C"],
            index=idx_map[user_choice] if user_choice in idx_map else None,
            format_func=lambda x, q=q: f"{x}.  {q[f'option_{x.lower()}']}",
            key=f"cbt_radio_{curr_idx}_v{radio_ver}",
            label_visibility="collapsed",
            disabled=is_answered,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if not is_answered:
            btn_col1, btn_col2 = st.columns([1.4, 1])
            with btn_col1:
                if st.button("Submit Answer", key=f"cbt_confirm_{curr_idx}", type="primary", disabled=selected is None):
                    answers[str(curr_idx)] = {"selected": selected, "time": time.time()}
                    st.session_state.practice_answers = answers
                    st.rerun()
            with btn_col2:
                # Clear Selection — resets radio to unselected by bumping the widget key version
                if selected is not None:
                    if st.button("❌ Clear Selection", key=f"cbt_clear_{curr_idx}"):
                        vers = st.session_state.practice_radio_versions
                        vers[curr_idx] = vers.get(curr_idx, 0) + 1
                        st.session_state.practice_radio_versions = vers
                        st.rerun()
        else:
            user_ans = answers[str(curr_idx)]["selected"]
            correct = q["correct_answer"]
            is_ok = user_ans == correct
            result_class = "answer-correct" if is_ok else "answer-wrong"
            icon = "✅" if is_ok else "❌"
            st.markdown(
                f"""<div class="{result_class}">
                    <strong>{icon} {'Correct!' if is_ok else f'Incorrect. Correct answer is {correct}'}</strong>
                    <div style="margin-top:0.5rem; color:#94a3b8; font-size:0.9rem; line-height:1.6;">
                        <strong style="color:#f1f5f9;">Explanation:</strong> {q['explanation']}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

        pass

    # 4. CBT Bottom Controls Bar
    st.markdown('<div class="cbt-footer-bar">', unsafe_allow_html=True)
    btm_c1, btm_c2, btm_c3 = st.columns([1.5, 1, 1])
    with btm_c1:
        is_flg = curr_idx in flags
        flag_lbl = "🚩 Unflag" if is_flg else "🏳️ Flag Question"
        if st.button(flag_lbl, key=f"cbt_flag_btn_{curr_idx}", use_container_width=True):
            if is_flg:
                flags.remove(curr_idx)
            else:
                flags.add(curr_idx)
            st.session_state.practice_flags = flags
            st.rerun()
    with btm_c2:
        if st.button("< Back", key=f"cbt_back_btn_{curr_idx}", use_container_width=True, disabled=curr_idx == 0):
            st.session_state.practice_current_idx = curr_idx - 1
            st.session_state.practice_confirm_submit = False
            st.rerun()
    with btm_c3:
        if st.button("Next >", key=f"cbt_next_btn_{curr_idx}", use_container_width=True, disabled=curr_idx == total - 1):
            st.session_state.practice_current_idx = curr_idx + 1
            st.session_state.practice_confirm_submit = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────────────────────────
else:
    questions = st.session_state.practice_questions
    answers   = st.session_state.practice_answers
    session_id = st.session_state.practice_session_id
    elapsed = (time.time() - st.session_state.practice_start_time) / 60

    correct_count = sum(
        1 for i, q in enumerate(questions)
        if str(i) in answers and answers[str(i)]["selected"] == q["correct_answer"]
    )
    score = (correct_count / len(questions)) * 100
    topic = questions[0]["topic"] if questions else ""

    # Save results
    if session_id:
        try:
            complete_session(session_id, score, len(questions), correct_count, elapsed)
            upsert_topic_performance(uid, topic, score)
            for i, q in enumerate(questions):
                if str(i) in answers:
                    qid = save_question(
                        q["topic"], q.get("subtopic",""), q["difficulty"],
                        q["question"], q["option_a"], q["option_b"], q["option_c"],
                        q["correct_answer"], q["explanation"],
                    )
                    save_answer(
                        uid, qid, session_id,
                        answers[str(i)]["selected"],
                        answers[str(i)]["selected"] == q["correct_answer"],
                        0.0,
                    )
        except Exception:
            pass
        st.session_state.practice_session_id = None  # prevent double-save

    # Results header
    color = "#10b981" if score >= 70 else "#f59e0b" if score >= 50 else "#ef4444"
    msg   = "Excellent!" if score >= 70 else "Good effort!" if score >= 50 else "Keep studying!"

    st.markdown(
        f"""
        <div style="text-align:center; padding:2rem 0 1rem;">
            <div style="font-size:4rem; font-weight:900; color:{color};">{score:.0f}%</div>
            <div style="font-size:1.5rem; font-weight:700; color:#f1f5f9;">{msg}</div>
            <div style="color:#64748b; margin-top:0.5rem;">
                {correct_count}/{len(questions)} correct · {elapsed:.1f} min
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Per-question review
    st.markdown("### 📋 Answer Review")
    for i, q in enumerate(questions):
        ans_data = answers.get(str(i), {})
        user_ans = ans_data.get("selected", "?")
        correct  = q["correct_answer"]
        is_ok    = user_ans == correct
        icon = "✅" if is_ok else "❌"

        with st.expander(f"{icon} Q{i+1}: {q['question'][:80]}..."):
            st.markdown(f"**Your answer:** {user_ans}. {q[f'option_{user_ans.lower()}']}" if user_ans != "?" else "Not answered")
            st.markdown(f"**Correct answer:** {correct}. {q[f'option_{correct.lower()}']}")
            st.markdown("---")
            st.markdown(f"**Explanation:** {q['explanation']}")

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("🔄 Practice Again", use_container_width=True, type="primary", key="again_btn"):
            st.session_state.practice_questions = []
            st.session_state.practice_answers = {}
            st.session_state.practice_submitted = False
            st.rerun()
    with col_r2:
        if st.button("🤖 Ask AI Tutor about this topic", use_container_width=True, key="go_chat"):
            st.session_state["chatbot_context"] = f"I just completed a {topic} practice session and scored {score:.0f}%."
            st.switch_page("pages/4_Chatbot.py")
