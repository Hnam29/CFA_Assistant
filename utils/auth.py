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
    """Load admin credentials from env variables or Streamlit secrets."""
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")
    try:
        import streamlit as st
        if "ADMIN_USERNAME" in st.secrets:
            username = st.secrets["ADMIN_USERNAME"]
        if "ADMIN_PASSWORD" in st.secrets:
            password = st.secrets["ADMIN_PASSWORD"]
    except Exception:
        pass
    return username or "hnamvu29", password or "admin123"


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


# ── Session state ────────────────────────────────────────────────

def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)


def get_current_user() -> dict | None:
    return st.session_state.get("current_user", None)


def login_user(user: dict) -> None:
    st.session_state["logged_in"] = True
    st.session_state["current_user"] = user


def logout_user() -> None:
    for key in ["logged_in", "current_user"]:
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
        admin_mode = st.toggle("🔒 Admin Sign In", key="login_admin_mode")
        admin_user, admin_pass = get_admin_credentials()
        
        default_user = admin_user if admin_mode else ""
        default_pass = admin_pass if admin_mode else ""
        
        with st.form("login_form"):
            username = st.text_input(t("username"), value=default_user, placeholder=t("enter_username"))
            password = st.text_input(t("password"), value=default_pass, type="password", placeholder=t("enter_password"))
            submitted = st.form_submit_button(t("sign_in"), use_container_width=True, type="primary")

            if submitted:
                if not username or not password:
                    st.error(t("fill_both_fields"))
                else:
                    # Check for direct admin match first
                    if username == admin_user and password == admin_pass:
                        user = get_user_by_username(username)
                        if not user:
                            # Auto-provision the admin account if missing from database
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
