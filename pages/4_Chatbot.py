"""
pages/4_Chatbot.py — AI Tutor chatbot for CFA questions and explanations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from database.db import init_db, get_chat_history, save_chat_message, clear_chat_history, get_topic_performance
from utils.auth import is_logged_in, get_current_user, render_auth_page
from utils.cfa_topics import TOPIC_NAMES
from core.chatbot_engine import chat_with_tutor
from database.db import get_user_profile

st.set_page_config(page_title="AI Tutor · CFA Assistant", page_icon="🤖", layout="wide")

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
if "chat_messages" not in st.session_state:
    # Load from DB
    history = get_chat_history(uid, limit=40)
    st.session_state.chat_messages = history

# Inject context if coming from practice page
context = st.session_state.pop("chatbot_context", "")

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🤖 AI Tutor Settings")

    quick_topic = st.selectbox("Quick Topic Focus", ["All Topics"] + TOPIC_NAMES, key="chat_topic")

    st.markdown("---")
    st.markdown("**💬 Conversation Starters**")

    starters = [
        "Explain the differences between FIFO and LIFO inventory methods",
        "What is the Sharpe ratio and how is it calculated?",
        "Walk me through how duration measures bond price sensitivity",
    ]

    for starter in starters:
        if st.button(f"💬 {starter[:45]}...", key=f"starter_{hash(starter)}", use_container_width=True):
            st.session_state["pending_message"] = starter

    st.markdown("---")
    if st.button("🗑️ Clear Conversation", use_container_width=True, key="clear_chat"):
        clear_chat_history(uid)
        st.session_state.chat_messages = []
        st.rerun()

# ── Header ────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="margin-bottom:1.5rem;">
        <h1 style="font-size:1.9rem; font-weight:800; color:#f1f5f9; margin:0;">🤖 AI Tutor</h1>
        <p style="color:#64748b; margin-top:0.3rem;">
            Your personal CFA Level I expert — ask anything about concepts, formulas, or exam strategy
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Context banner ─────────────────────────────────────────────────
if context:
    st.info(f"📌 Context from your last session: *{context}*")

# ── Chat display ───────────────────────────────────────────────────
chat_container = st.container()
with chat_container:
    if not st.session_state.chat_messages:
        st.markdown(
            """
            <div style="text-align:center; padding:3rem 1rem; color:#64748b;">
                <div style="font-size:3rem; margin-bottom:1rem;">🎓</div>
                <div style="font-size:1.1rem; font-weight:600; color:#94a3b8; margin-bottom:0.5rem;">
                    Ask me anything about CFA Level I
                </div>
                <div style="font-size:0.88rem;">
                    Try: "Explain the Dividend Discount Model" or "What is WACC?"
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for msg in st.session_state.chat_messages:
            role    = msg["role"]
            content = msg["content"]

            if role == "user":
                st.markdown(
                    f"""
                    <div class="chat-message chat-user">
                        <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.4rem;">
                            <span style="font-size:1rem;">👤</span>
                            <span style="font-weight:600; color:#818cf8; font-size:0.85rem;">You</span>
                        </div>
                        <div style="color:#e2e8f0; font-size:0.93rem; line-height:1.6;">{content}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                with st.container():
                    st.markdown(
                        f"""
                        <div class="chat-message chat-assistant">
                            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.4rem;">
                                <span style="font-size:1rem;">🤖</span>
                                <span style="font-weight:600; color:#06b6d4; font-size:0.85rem;">CFA Tutor</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown(content)

# ── Input area ─────────────────────────────────────────────────────
pending = st.session_state.pop("pending_message", "")
# ── Build user context for AI personalisation ──────────────────────
_profile = get_user_profile(uid)
_perf    = get_topic_performance(uid)

_user_ctx_lines = []
if _profile:
    name = _profile.get("full_name") or user["username"]
    _user_ctx_lines.append(f"- Name: {name}")
    _user_ctx_lines.append(f"- CFA Level: {_profile.get('cfa_level', 1)}")
    if _profile.get("exam_date"):
        _user_ctx_lines.append(f"- Exam date: {_profile['exam_date']} ({_profile.get('exam_window','')} {_profile.get('exam_year','')})")

if _perf:
    _user_ctx_lines.append("- Topic performance (avg score):")
    for p in sorted(_perf, key=lambda x: x.get("avg_score") or 0):
        score = p.get("avg_score")
        score_str = f"{score:.0f}%" if score is not None else "no score"
        _user_ctx_lines.append(f"  • {p['topic']}: {score_str} ({p['sessions_done']} sessions)")

user_ctx = "\n".join(_user_ctx_lines) if _user_ctx_lines else ""

user_input = st.chat_input("Ask your CFA tutor anything... e.g. 'What is convexity and why does it matter?'")

# Handle send
if user_input or pending:
    msg = (user_input or pending).strip()

    # Add user message
    st.session_state.chat_messages.append({"role": "user", "content": msg})
    save_chat_message(uid, "user", msg)

    # Build context string
    ctx = context
    if quick_topic != "All Topics":
        ctx = f"Focus area: {quick_topic}. " + ctx

    # Get AI response
    history_for_api = st.session_state.chat_messages[:-1]  # all except the one we just added

    with st.spinner("🤖 Thinking..."):
        try:
            response = chat_with_tutor(
                messages=history_for_api,
                user_message=msg,
                context=ctx,
                user_context=user_ctx,
            )
        except Exception as e:
            response = f"⚠️ AI error: {e}\n\nPlease check your API key in `.env`."

    st.session_state.chat_messages.append({"role": "assistant", "content": response})
    save_chat_message(uid, "assistant", response)
    st.rerun()
