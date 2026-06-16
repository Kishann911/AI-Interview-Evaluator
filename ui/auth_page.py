import re
import streamlit as st

from config import APP_NAME, DOMAINS
from database.db_handler import login_candidate, register_user


# ── Session state ──────────────────────────────────────────────────────────────

def init_session_state():
    defaults = {
        # Auth
        "logged_in": False,
        "candidate": None,
        "page": "home",
        "current_interview": None,
        # Legacy keys used by other UI pages
        "user_id": None,
        "username": None,
        "is_admin": False,
        "current_page": "interview",
        "viewing_interview_id": None,
        # Interview flow — new keys (used by interview_page.py)
        "interview_state":        "not_started",
        "current_question_index": 0,
        "questions_list":         [],
        "answers_given":          [],
        "time_taken_list":        [],
        "evaluations":            [],
        "interview_start_time":   None,
        "question_start_time":    None,
        "interview_domain":       None,
        "interview_difficulty":   None,
        "interview_id":           None,
        # Legacy interview keys (kept for backward compat / migration)
        "interview_questions": [],
        "interview_answers":   [],
        "interview_current":   0,
        "interview_results":   None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ── Page styling ───────────────────────────────────────────────────────────────

_PAGE_CSS = """
<style>
/* Gradient page background */
.stApp {
    background: linear-gradient(145deg, #eef2ff 0%, #e8f0fe 40%, #f3e8ff 100%);
    min-height: 100vh;
}

/* Auth card */
.auth-card {
    background: #ffffff;
    border-radius: 20px;
    padding: 2.5rem 2.8rem;
    box-shadow: 0 8px 40px rgba(30, 58, 138, 0.12),
                0 2px 8px rgba(0, 0, 0, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.9);
    margin: 0.5rem 0 1.5rem 0;
}

/* Logo section */
.auth-logo-wrap {
    text-align: center;
    padding: 1.8rem 0 1.4rem;
}
.auth-logo-emoji {
    font-size: 3.6rem;
    line-height: 1;
    filter: drop-shadow(0 4px 8px rgba(30,58,138,0.2));
}
.auth-app-name {
    font-size: 2rem;
    font-weight: 800;
    color: #1e3a8a;
    margin: 0.5rem 0 0 0;
    letter-spacing: -0.5px;
}
.auth-subtitle {
    font-size: 0.92rem;
    font-weight: 500;
    background: linear-gradient(90deg, #4f46e5, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-top: 0.3rem;
}

/* Divider below logo */
.auth-divider {
    height: 2px;
    background: linear-gradient(90deg, transparent, #c7d2fe, transparent);
    margin: 1rem 0 0 0;
    border: none;
}

/* Demo credentials box */
.demo-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-top: 1.2rem;
    text-align: center;
}
.demo-label {
    font-size: 0.78rem;
    color: #94a3b8;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
.demo-creds {
    font-size: 0.88rem;
    color: #475569;
    font-family: monospace;
    margin-top: 0.3rem;
    font-weight: 600;
}

/* Register success note */
.success-banner {
    background: linear-gradient(135deg, #d1fae5, #a7f3d0);
    border: 1px solid #6ee7b7;
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    text-align: center;
    color: #065f46;
    font-weight: 600;
    font-size: 0.95rem;
    margin-top: 0.8rem;
}

/* Streamlit tab overrides */
div[data-testid="stTabs"] button[role="tab"] {
    font-weight: 600;
    font-size: 0.95rem;
    padding: 0.6rem 1.4rem;
    border-radius: 8px 8px 0 0;
}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    background: #eff6ff;
    color: #1e3a8a;
    border-bottom: 2px solid #1e3a8a;
}

/* Input label styles */
div[data-testid="stTextInput"] label,
div[data-testid="stSelectbox"] label {
    font-weight: 600;
    color: #334155;
    font-size: 0.9rem;
}

/* Form submit button */
div[data-testid="stForm"] button[kind="primaryFormSubmit"] {
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
    border: none;
    border-radius: 10px;
    font-weight: 700;
    font-size: 1rem;
    padding: 0.65rem 1rem;
    letter-spacing: 0.3px;
    transition: opacity 0.2s;
}
div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {
    opacity: 0.9;
}
</style>
"""

_LOGO_HTML = f"""
<div class="auth-logo-wrap">
    <div class="auth-logo-emoji">🎯</div>
    <div class="auth-app-name">{APP_NAME}</div>
    <div class="auth-subtitle">✨ Powered by Google Gemini</div>
    <hr class="auth-divider">
</div>
"""

_DEMO_BOX_HTML = """
<div class="demo-box">
    <div class="demo-label">Demo credentials</div>
    <div class="demo-creds">demo@test.com &nbsp;/&nbsp; demo123</div>
</div>
"""


# ── Helpers ────────────────────────────────────────────────────────────────────

def _valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()))


def _apply_login(candidate: dict):
    """Populate all session-state keys after a successful authentication."""
    st.session_state.logged_in = True
    st.session_state.candidate = candidate
    st.session_state.page = "home"
    # Legacy keys for other UI pages
    st.session_state.user_id = candidate["id"]
    st.session_state.username = candidate["name"]
    st.session_state.is_admin = candidate.get("is_admin", False)
    st.session_state.current_page = "interview"


# ── Tab: Login ─────────────────────────────────────────────────────────────────

def _show_login():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown(_LOGO_HTML, unsafe_allow_html=True)

    st.markdown("#### Welcome back")

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input(
            "Email address",
            placeholder="you@example.com",
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
        )
        col_a, col_b = st.columns([3, 1])
        with col_a:
            submitted = st.form_submit_button(
                "Login",
                use_container_width=True,
                type="primary",
            )

    if submitted:
        if not email.strip() or not password:
            st.error("Please fill in both fields.")
        elif not _valid_email(email):
            st.error("Please enter a valid email address.")
        else:
            candidate = login_candidate(email=email.strip(), password=password)
            if candidate:
                _apply_login(candidate)
                st.success(f"Welcome back, {candidate['name']}!")
                st.rerun()
            else:
                st.error("Invalid email or password.")

    st.markdown(_DEMO_BOX_HTML, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ── Tab: Register ──────────────────────────────────────────────────────────────

def _show_register():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown(_LOGO_HTML, unsafe_allow_html=True)

    st.markdown("#### Create your account")

    with st.form("register_form", clear_on_submit=True):
        full_name = st.text_input(
            "Full Name",
            placeholder="e.g. Jane Smith",
        )
        email = st.text_input(
            "Email address",
            placeholder="you@example.com",
        )
        domain_interest = st.selectbox(
            "Domain of Interest",
            options=DOMAINS,
            help="Pick the area you want to practice most — you can change this later.",
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Minimum 6 characters",
        )
        confirm = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Repeat your password",
        )
        submitted = st.form_submit_button(
            "Create Account",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        errors = _validate_registration(full_name, email, password, confirm)
        if errors:
            for e in errors:
                st.error(e)
        else:
            result = register_user(
                username=full_name.strip(),
                email=email.strip().lower(),
                password=password,
            )
            if result["success"]:
                # Auto-login the newly registered user
                candidate = login_candidate(
                    email=email.strip().lower(),
                    password=password,
                )
                if candidate:
                    _apply_login(candidate)
                    st.markdown(
                        '<div class="success-banner">'
                        "Account created! Welcome aboard 🎉"
                        "</div>",
                        unsafe_allow_html=True,
                    )
                    st.rerun()
                else:
                    st.success(
                        "Account created! Switch to the Login tab to sign in."
                    )
            else:
                st.error(result.get("message", "Registration failed. Please try again."))

    st.markdown("</div>", unsafe_allow_html=True)


def _validate_registration(
    name: str, email: str, password: str, confirm: str
) -> list[str]:
    errors = []
    if not name or len(name.strip()) < 2:
        errors.append("Full name must be at least 2 characters.")
    if not email or not _valid_email(email):
        errors.append("Please enter a valid email address.")
    if not password or len(password) < 6:
        errors.append("Password must be at least 6 characters.")
    if password != confirm:
        errors.append("Passwords do not match.")
    return errors


# ── Main entry point ───────────────────────────────────────────────────────────

def show_auth_page():
    init_session_state()

    st.markdown(_PAGE_CSS, unsafe_allow_html=True)

    # Outer centering columns
    _, center, _ = st.columns([1, 2, 1])

    with center:
        tab_login, tab_register = st.tabs(["🔑  Login", "✨  Register"])

        with tab_login:
            _show_login()

        with tab_register:
            _show_register()
