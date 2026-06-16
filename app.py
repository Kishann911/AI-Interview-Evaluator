import os
import time
from collections import Counter
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

# Load .env before any module that reads env vars (evaluator, db_handler)
load_dotenv()

from config import (
    APP_NAME, VERSION,
    DOMAINS, DIFFICULTY_LEVELS, QUESTION_COUNT_OPTIONS,
    DOMAIN_ICONS, DIFFICULTY_COLORS, GRADE_COLORS,
)
from database import db_handler
from database.db_handler import get_user_interviews, get_leaderboard
from core.questions import get_questions
from ui.auth_page import init_session_state, show_auth_page
from ui.interview_page import show_interview_page
from ui.results_page import show_results_page
from ui.history_page import show_history_page
from ui.admin_page import show_admin_page


# ── Nav configuration ─────────────────────────────────────────────────────────

_NAV = [
    ("🏠", "Home Dashboard",   "home"),
    ("🎤", "Start Interview",  "interview"),
    ("📊", "My Results",       "results"),
    ("📜", "Interview History","history"),
    ("🏆", "Leaderboard",      "leaderboard"),
]
_ADMIN_NAV = ("⚙️", "Admin Panel", "admin")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _inject_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as fh:
            st.markdown(f"<style>{fh.read()}</style>", unsafe_allow_html=True)
    # Sidebar: make the active-page button visually distinct
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] button[data-testid="baseButton-primary"] {
            background: rgba(255,255,255,0.22) !important;
            border: 1.5px solid rgba(255,255,255,0.45) !important;
            font-weight: 700 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _initials(name: str) -> str:
    parts = (name or "?").strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if len(name) >= 2 else (name or "?")[0].upper()


def _pct_color(pct: float) -> str:
    if pct >= 80: return "#059669"
    if pct >= 60: return "#3b82f6"
    if pct >= 40: return "#f59e0b"
    return "#ef4444"


def _medal(rank: int) -> str:
    return {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")


# ── Sidebar ───────────────────────────────────────────────────────────────────

def _render_sidebar():
    candidate = st.session_state.get("candidate") or {}
    name    = candidate.get("name")  or st.session_state.get("username", "User")
    email   = candidate.get("email") or ""
    is_admin = st.session_state.get("is_admin", False)
    current  = st.session_state.get("current_page", "home")

    with st.sidebar:
        # ── Avatar + identity ──────────────────────────────────────────────
        st.markdown(
            f"""
            <div style="padding:1.2rem 0 0.8rem; text-align:center;">
                <div style="
                    width:58px; height:58px;
                    background:linear-gradient(135deg, #60a5fa 0%, #818cf8 100%);
                    border-radius:50%;
                    display:inline-flex; align-items:center; justify-content:center;
                    font-size:1.35rem; font-weight:800; color:white;
                    box-shadow:0 4px 14px rgba(0,0,0,0.35);
                    margin-bottom:0.65rem;">
                    {_initials(name)}
                </div>
                <div style="font-weight:700; font-size:0.98rem; letter-spacing:0.2px;">
                    {name}
                </div>
                <div style="font-size:0.76rem; opacity:0.55; margin-top:3px;">
                    {email}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        # ── Navigation ─────────────────────────────────────────────────────
        nav_items = _NAV + ([_ADMIN_NAV] if is_admin else [])
        for icon, label, page_key in nav_items:
            is_active = current == page_key
            btn_label = f"{icon}  {label}"
            btn_type  = "primary" if is_active else "secondary"
            if st.button(
                btn_label,
                use_container_width=True,
                key=f"nav_{page_key}",
                type=btn_type,
            ):
                st.session_state.current_page = page_key
                if page_key == "results":
                    st.session_state.viewing_interview_id = None
                st.rerun()

        st.divider()

        # ── Version label + Logout ─────────────────────────────────────────
        st.markdown(
            f'<div style="font-size:0.72rem; opacity:0.35; text-align:center; '
            f'padding:0 0 0.6rem;">{APP_NAME} v{VERSION}</div>',
            unsafe_allow_html=True,
        )
        if st.button("🚪  Logout", use_container_width=True, key="nav_logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ── Home Dashboard ────────────────────────────────────────────────────────────

def _show_home():
    candidate = st.session_state.get("candidate") or {}
    name     = candidate.get("name") or st.session_state.get("username", "User")
    user_id  = st.session_state.get("user_id")
    today    = date.today().strftime("%A, %B %d, %Y")

    # ── Welcome banner ─────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            border-radius: 16px; padding: 2rem 2.5rem; color: white; margin-bottom: 1.5rem;">
            <div style="font-size:0.88rem; opacity:0.75; font-weight:500;">{today}</div>
            <div style="font-size:2rem; font-weight:800; margin-top:0.3rem;">
                Welcome back, {name}! 👋
            </div>
            <div style="opacity:0.8; margin-top:0.4rem; font-size:0.95rem;">
                Ready for your next interview session?
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Load interviews ────────────────────────────────────────────────────
    interviews = get_user_interviews(user_id) if user_id else []

    # ── Stats row ──────────────────────────────────────────────────────────
    total    = len(interviews)
    avg_pct  = round(sum(i["percentage"] for i in interviews) / total, 1) if total else 0.0
    best_pct = round(max(i["percentage"] for i in interviews), 1)         if total else 0.0

    fav_domain = "—"
    if interviews:
        counts = Counter(i["domain"] for i in interviews)
        top = counts.most_common(1)[0][0]
        fav_domain = f"{DOMAIN_ICONS.get(top, '')} {top}"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Interviews", total)
    c2.metric("Average Score",    f"{avg_pct:.1f}%")
    c3.metric("Best Score",       f"{best_pct:.1f}%")
    c4.metric("Favourite Domain", fav_domain)

    st.divider()

    # ── Quick Start ────────────────────────────────────────────────────────
    st.subheader("🚀 Quick Start Interview")

    qs_col1, qs_col2, qs_col3, qs_col4 = st.columns([3, 2, 2, 2])
    with qs_col1:
        qs_domain = st.selectbox(
            "Domain",
            DOMAINS,
            format_func=lambda d: f"{DOMAIN_ICONS.get(d, '')} {d}",
            key="qs_domain",
        )
    with qs_col2:
        qs_diff = st.radio(
            "Difficulty",
            DIFFICULTY_LEVELS,
            horizontal=True,
            key="qs_diff",
        )
    with qs_col3:
        qs_count = st.select_slider(
            "Questions",
            options=QUESTION_COUNT_OPTIONS,
            value=QUESTION_COUNT_OPTIONS[0],
            key="qs_count",
        )
    with qs_col4:
        st.write("")  # vertical alignment nudge
        st.write("")
        if st.button("Start Interview  →", type="primary", use_container_width=True):
            questions = get_questions(qs_domain, qs_count, qs_diff)
            if questions:
                n   = len(questions)
                now = time.time()
                st.session_state.questions_list         = questions
                st.session_state.answers_given          = [""] * n
                st.session_state.time_taken_list        = [0] * n
                st.session_state.evaluations            = []
                st.session_state.current_question_index = 0
                st.session_state.interview_domain       = qs_domain
                st.session_state.interview_difficulty   = qs_diff
                st.session_state.interview_start_time   = now
                st.session_state.question_start_time    = now
                st.session_state.interview_state        = "in_progress"
                st.session_state.current_page           = "interview"
                st.rerun()
            else:
                st.error(f"No questions found for {qs_domain} / {qs_diff}. Try another combination.")

    st.divider()

    # ── Recent Interviews ──────────────────────────────────────────────────
    st.subheader("🕐 Recent Interviews")

    if not interviews:
        st.info("No interviews yet — use Quick Start above to begin!")
    else:
        recent = interviews[:3]
        rows = []
        for iv in recent:
            pct  = iv.get("percentage", 0.0)
            grade = iv.get("grade") or iv.get("letter_grade", "—")
            domain_icon = DOMAIN_ICONS.get(iv["domain"], "")
            completed = (
                iv["completed_at"].strftime("%b %d, %Y  %H:%M")
                if iv.get("completed_at") else "—"
            )
            rows.append({
                "Domain":     f"{domain_icon} {iv['domain']}",
                "Difficulty": iv.get("difficulty", ""),
                "Score":      f"{pct:.1f}%",
                "Grade":      grade,
                "Date":       completed,
            })

        df_recent = pd.DataFrame(rows)
        st.dataframe(
            df_recent,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Score": st.column_config.TextColumn("Score"),
                "Grade": st.column_config.TextColumn("Grade"),
            },
        )

        if st.button("📜 View Full History", key="home_history_btn"):
            st.session_state.current_page = "history"
            st.rerun()

    # ── Performance trend chart ────────────────────────────────────────────
    if len(interviews) >= 2:
        st.divider()
        st.subheader("📈 Performance Over Time")

        last_10 = list(reversed(interviews[:10]))   # oldest → newest
        df_trend = pd.DataFrame([
            {
                "Interview #": idx + 1,
                "Score (%)":   round(iv["percentage"], 1),
                "Domain":      iv["domain"],
                "Difficulty":  iv.get("difficulty", ""),
                "Grade":       iv.get("grade") or iv.get("letter_grade", ""),
                "Date": (
                    iv["completed_at"].strftime("%b %d")
                    if iv.get("completed_at") else ""
                ),
            }
            for idx, iv in enumerate(last_10)
        ])

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_trend["Interview #"],
            y=df_trend["Score (%)"],
            mode="lines+markers",
            line=dict(color="#3b82f6", width=2.5),
            marker=dict(
                size=9,
                color=df_trend["Score (%)"],
                colorscale=[[0, "#ef4444"], [0.5, "#f59e0b"], [1, "#059669"]],
                cmin=0, cmax=100,
                line=dict(width=2, color="white"),
            ),
            hovertemplate=(
                "<b>Interview %{x}</b><br>"
                "Score: %{y:.1f}%<br>"
                "Domain: %{customdata[0]}<br>"
                "Date: %{customdata[1]}<extra></extra>"
            ),
            customdata=df_trend[["Domain", "Date"]].values,
        ))
        # Fill under the line
        fig.add_trace(go.Scatter(
            x=df_trend["Interview #"],
            y=df_trend["Score (%)"],
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.08)",
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False,
            hoverinfo="skip",
        ))
        fig.add_hline(
            y=60,
            line_dash="dot",
            line_color="#ef4444",
            annotation_text="Pass threshold (60%)",
            annotation_position="top right",
        )
        fig.update_layout(
            yaxis=dict(range=[0, 105], title="Score (%)", gridcolor="#f1f5f9"),
            xaxis=dict(
                title="Interview (oldest → latest)",
                tickmode="linear",
                tick0=1,
                dtick=1,
                gridcolor="#f1f5f9",
            ),
            height=300,
            margin=dict(t=10, b=30, l=10, r=10),
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)


# ── Leaderboard ───────────────────────────────────────────────────────────────

def _show_leaderboard():
    st.title("🏆 Leaderboard")
    st.markdown("Top performers ranked by their best interview score.")

    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        domain_opts = ["All Domains"] + DOMAINS
        domain_sel  = st.selectbox("Filter by Domain", domain_opts, key="lb_domain")
    with col_f2:
        limit = st.select_slider("Show top", options=[5, 10, 20, 50], value=10, key="lb_limit")

    domain_arg = None if domain_sel == "All Domains" else domain_sel
    rows = get_leaderboard(domain=domain_arg, limit=limit)

    if not rows:
        st.info("No completed interviews yet. Be the first on the board!")
        return

    current_id = st.session_state.get("user_id")

    st.divider()
    st.markdown(
        f"**{'All Domains' if not domain_arg else domain_arg}** — "
        f"showing top {len(rows)} candidates",
    )

    for entry in rows:
        rank          = entry["rank"]
        is_me         = entry["id"] == current_id
        highlight     = "background:#eff6ff; border-color:#3b82f6;" if is_me else ""
        medal         = _medal(rank)
        best_color    = _pct_color(entry["best_score"])
        last_active   = (
            entry["last_completed"].strftime("%b %d, %Y")
            if entry.get("last_completed") else "—"
        )
        name_tag = f"{entry['name']} {'<span style=\"background:#3b82f6;color:white;border-radius:4px;padding:1px 7px;font-size:0.75rem;\">You</span>' if is_me else ''}"

        st.markdown(
            f"""
            <div style="
                border:1px solid #e2e8f0; border-radius:12px;
                padding:1rem 1.4rem; margin-bottom:0.5rem;
                display:flex; align-items:center; justify-content:space-between;
                background:white; box-shadow:0 1px 4px rgba(0,0,0,0.05);
                {highlight}
            ">
                <div style="display:flex; align-items:center; gap:1rem;">
                    <div style="font-size:1.6rem; min-width:2rem; text-align:center;">{medal}</div>
                    <div>
                        <div style="font-weight:700; font-size:1rem;">{name_tag}</div>
                        <div style="font-size:0.8rem; color:#64748b; margin-top:2px;">
                            {entry['interview_count']} interview{'s' if entry['interview_count'] != 1 else ''}
                            &nbsp;·&nbsp; last active {last_active}
                        </div>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.5rem; font-weight:800; color:{best_color};">
                        {entry['best_score']:.1f}%
                    </div>
                    <div style="font-size:0.78rem; color:#64748b; margin-top:1px;">
                        avg {entry['avg_score']:.1f}%
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Page router ───────────────────────────────────────────────────────────────

def _render_page():
    page = st.session_state.get("current_page", "home")

    if page == "home":
        _show_home()
    elif page == "interview":
        show_interview_page()
    elif page == "results":
        show_results_page()
    elif page == "history":
        show_history_page()
    elif page == "leaderboard":
        _show_leaderboard()
    elif page == "admin":
        show_admin_page()
    else:
        _show_home()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title=APP_NAME,
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _inject_css()

    # Initialise DB (creates tables + seeds admin account idempotently)
    db_handler.init_db()

    # Initialise all session-state defaults (idempotent — safe to call every run)
    init_session_state()
    # Admin gate key not covered by auth_page
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    # ── Auth gate ──────────────────────────────────────────────────────────
    if not st.session_state.get("logged_in", False):
        show_auth_page()
        return

    # ── Authenticated: sidebar + page content ──────────────────────────────
    _render_sidebar()
    _render_page()


if __name__ == "__main__":
    main()
