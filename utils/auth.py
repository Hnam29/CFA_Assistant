"""
utils/auth.py — Simple username/password auth backed by SQLite + bcrypt.
"""

import re
import bcrypt
import streamlit as st
from database.db import get_user_by_username, create_user
from utils.i18n import t
from utils.email_sender import send_welcome_email


import os

def get_admin_credentials():
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")
    try:
        if "ADMIN_USERNAME" in st.secrets:
            username = st.secrets["ADMIN_USERNAME"]
        if "ADMIN_PASSWORD" in st.secrets:
            password = st.secrets["ADMIN_PASSWORD"]
    except Exception:
        pass
    if not username or not password:
        raise RuntimeError(
            "ADMIN_USERNAME / ADMIN_PASSWORD not configured. "
            "Set them via environment variables or Streamlit secrets."
        )
    return username, password


# ── Password helpers ─────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ── Email Validation with Typo Rules ──────────────────────────────

def validate_email_typos(email: str) -> str | None:
    """
    Validate email format and check for common typos.
    Returns error message if invalid/typo, else None.
    """
    email = email.strip().lower()
    if not email:
        return t("email_required")
    
    # Basic email format validation
    email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(email_regex, email):
        return "Invalid email format (e.g. user@domain.com) / Định dạng email không hợp lệ."
        
    # Popular email typo rules
    domain_typos = {
        "gamil.com": "gmail.com",
        "gmal.com": "gmail.com",
        "gamil.co": "gmail.com",
        "gmail.con": "gmail.com",
        "gmail.co": "gmail.com",
        "yaho.com": "yahoo.com",
        "yahoo.co": "yahoo.com",
        "hotamil.com": "hotmail.com",
        "hotmial.com": "hotmail.com",
        "outlook.con": "outlook.com",
        "outlook.co": "outlook.com",
    }
    
    domain = email.split("@")[-1]
    if domain in domain_typos:
        return f"Did you mean '@{domain_typos[domain]}' instead of '@{domain}'? / Bạn có ý định gõ '@{domain_typos[domain]}' thay vì '@{domain}' không?"
        
    return None


# ── Session state (DB-backed token via st.query_params) ──────────

def _create_session_token(user_id: int) -> str:
    """Create a login token in the DB and return it."""
    import uuid
    from database.db import get_connection
    token = uuid.uuid4().hex
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO login_tokens (token, user_id) VALUES (?, ?)",
            (token, user_id),
        )
    return token


def _validate_session_token(token: str) -> dict | None:
    """Look up a token in the DB and return the user dict if valid with retries."""
    import time
    from database.db import get_connection, get_user_by_id
    last_err = None
    for attempt in range(3):
        try:
            with get_connection() as conn:
                row = conn.execute(
                    "SELECT user_id FROM login_tokens WHERE token = ?",
                    (token,),
                ).fetchone()
            if row:
                return get_user_by_id(row["user_id"])
            return None
        except Exception as e:
            last_err = e
            time.sleep(0.2)
    if last_err:
        raise last_err
    return None


def _delete_session_token(token: str) -> None:
    """Remove a token from the DB."""
    from database.db import get_connection
    with get_connection() as conn:
        conn.execute("DELETE FROM login_tokens WHERE token = ?", (token,))


def is_logged_in() -> bool:
    if st.session_state.get("logged_in", False):
        # Re-inject token into URL if a page switch cleared the query params.
        # This ensures the token is always in the URL so a browser reload works.
        token = st.session_state.get("session_token")
        if token and st.query_params.get("sid") != token:
            try:
                st.query_params["sid"] = token
            except Exception:
                pass
        return True

    # Check if this is a fresh reload. Streamlit sometimes runs the script
    # once before query params are synced from the client. We do one fast
    # rerun to ensure query params are populated.
    if "run_count" not in st.session_state:
        st.session_state["run_count"] = 1
        if not st.query_params.get("sid"):
            try:
                st.rerun()
            except Exception:
                pass

    # Try restoring session from URL token (handles reloads)
    try:
        token = st.query_params.get("sid")
        if token:
            user = _validate_session_token(token)
            if user:
                st.session_state["logged_in"] = True
                st.session_state["current_user"] = user
                st.session_state["session_token"] = token
                return True
            else:
                # Invalid/expired token — clean it from URL
                try:
                    del st.query_params["sid"]
                except Exception:
                    pass
    except Exception:
        pass
    return False


def get_current_user() -> dict | None:
    current = st.session_state.get("current_user", None)
    imp_uid = st.session_state.get("impersonate_uid")
    if imp_uid and current:
        try:
            admin_user, _ = get_admin_credentials()
            if current.get("username") == admin_user:
                from database.db import get_user_by_id
                imp_user = get_user_by_id(imp_uid)
                if imp_user:
                    return imp_user
        except Exception:
            pass
    return current


def login_user(user: dict) -> None:
    st.session_state["logged_in"] = True
    st.session_state["current_user"] = user
    token = _create_session_token(user["id"])
    # Store in session_state so page switches (which clear query_params) don't lose it
    st.session_state["session_token"] = token
    st.query_params["sid"] = token


def logout_user() -> None:
    # Delete the DB token
    try:
        token = st.session_state.get("session_token") or st.query_params.get("sid")
        if token:
            _delete_session_token(token)
        try:
            del st.query_params["sid"]
        except Exception:
            pass
    except Exception:
        pass
    for key in ["logged_in", "current_user", "session_token", "impersonate_uid", "impersonate_name"]:
        st.session_state.pop(key, None)




# ── Login / Register UI ──────────────────────────────────────────

def render_auth_page() -> bool:
    """
    Renders the login/register UI. Returns True if user is now logged in.
    """
    st.markdown(
        """
        <div style="text-align:center; padding: 2rem 0 1rem;">
            <h1 style="font-size:2.5rem; font-weight:800; background: linear-gradient(135deg,#6366f1,#06b6d4);
                       -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                CFA Learning Assistant
            </h1>
            <p style="color:#94a3b8; font-size:1.05rem;">AI-powered study platform for CFA candidates</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(["🔐 " + t("sign_in"), "📝 " + t("sign_up")])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input(t("username"), value="", placeholder=t("enter_username"))
            password = st.text_input(t("password"), value="", type="password", placeholder=t("enter_password"))
            submitted = st.form_submit_button(t("sign_in"), use_container_width=True, type="primary")

            if submitted:
                if not username or not password:
                    st.error(t("fill_both_fields"))
                else:
                    try:
                        admin_user, admin_pass = get_admin_credentials()
                    except RuntimeError:
                        admin_user, admin_pass = None, None
                    if admin_user and username == admin_user and password == admin_pass:
                        user = get_user_by_username(username)
                        if not user:
                            hashed = hash_password(password)
                            create_user(username, hashed, "admin@cfa-assistant.com", 3, "")
                            user = get_user_by_username(username)
                        login_user(user)
                        st.success(f"Welcome Admin, {username}! 🎓")
                        st.rerun()
                    else:
                        user = get_user_by_username(username)
                        if user and verify_password(password, user["password"]):
                            login_user(user)
                            st.success(f"Welcome back, {username}! 🎓")
                            st.rerun()
                        else:
                            st.error(t("invalid_credentials"))

    with tab_register:
        with st.form("register_form"):
            new_username = st.text_input(t("username"), placeholder=t("enter_username"), key="reg_user")
            new_email = st.text_input(t("email_required"), placeholder="your@email.com", key="reg_email")
            new_phone = st.text_input(t("phone_optional"), placeholder="e.g. +84901234567", key="reg_phone")
            new_password = st.text_input(t("password"), type="password", placeholder=t("min_6_chars"), key="reg_pass")
            confirm_password = st.text_input(t("confirm_password"), type="password", key="reg_confirm")
            cfa_level = st.selectbox(t("cfa_level_focus"), [1, 2, 3], key="reg_level")
            submitted = st.form_submit_button(t("create_account"), use_container_width=True, type="primary")

            if submitted:
                email_err = validate_email_typos(new_email)
                if not new_username or not new_password:
                    st.error(t("username_required"))
                elif email_err:
                    st.error(email_err)
                elif len(new_password) < 6:
                    st.error(t("password_min"))
                elif new_password != confirm_password:
                    st.error(t("passwords_no_match"))
                else:
                    hashed = hash_password(new_password)
                    user_id = create_user(new_username, hashed, new_email, cfa_level, new_phone)
                    if user_id:
                        user = get_user_by_username(new_username)
                        
                        # Send auto email in the background/inline
                        success_mail, mail_msg = send_welcome_email(new_email, new_username)
                        
                        login_user(user)
                        
                        # Save success notification message in session state so we can display it below the form
                        st.session_state["show_welcome_noti"] = new_email
                        
                        st.rerun()
                    else:
                        st.error(t("username_taken"))
        
        # Display the email notification message directly below the form
        if "show_welcome_noti" in st.session_state:
            email_sent_to = st.session_state["show_welcome_noti"]
            st.success(t("welcome_email_sent_noti", email=email_sent_to))

    return is_logged_in()
