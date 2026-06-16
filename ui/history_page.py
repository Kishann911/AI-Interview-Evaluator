"""
History page — two tabs:
  📜 Interview History  — filtered cards + trend chart
  🏆 Leaderboard       — ranked table with privacy masking
"""

import traceback
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import DIFFICULTY_COLORS, DOMAIN_ICONS, DOMAINS
from database.db_handler import (
    get_candidate_performance_trend,
    get_leaderboard,
    get_user_interviews,
)


# ── Constants ──────────────────────────────────────────────────────────────────

_DOMAIN_COLORS: dict[str, str] = {
    "Software Engineering": "#3b82f6",
    "HR / Behavioral":      "#10b981",
    "System Design":        "#f59e0b",
    "Data Science & ML":    "#8b5cf6",
    "Product Management":   "#ef4444",
}

_LETTER_COLORS: dict[str, str] = {
    "A+": "#059669", "A": "#10b981",
    "B+": "#3b82f6", "B": "#6366f1",
    "C+": "#f59e0b", "C": "#f97316",
    "D":  "#ef4444", "F": "#dc2626",
}

# Grade filter groups: selectbox label → set of matching letter grades
_GRADE_GROUPS: dict[str, set[str]] = {
    "A": {"A+", "A"},
    "B": {"B+", "B"},
    "C": {"C+", "C"},
    "D": {"D"},
    "F": {"F"},
}

_DATE_RANGES = ["Last 7 Days", "Last 30 Days", "All Time"]


# ── Utility helpers ────────────────────────────────────────────────────────────

def _lcolor(grade: str) -> str:
    return _LETTER_COLORS.get(grade, "#6c757d")


def _pct_color(pct: float) -> str:
    if pct >= 80: return "#059669"
    if pct >= 60: return "#3b82f6"
    if pct >= 40: return "#f59e0b"
    return "#ef4444"


def _aware(dt: datetime | None) -> datetime | None:
    """Normalise a possibly-naive datetime to UTC-aware."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _fmt_date(dt: datetime | None) -> str:
    if not dt:
        return "—"
    return dt.strftime("%d %b %Y, %I:%M %p")


def _fmt_duration(minutes: float | None) -> str:
    if not minutes:
        return "—"
    total_s = int(minutes * 60)
    m, s = divmod(total_s, 60)
    return f"{m}m {s}s" if m else f"{s}s"


def _mask_name(name: str) -> str:
    """Privacy mask: show first 3 chars of first word + '*****'."""
    first = (name or "?").strip().split()[0]
    visible = first[:3] if len(first) > 3 else first
    return visible + "*****"


def _medal(rank: int) -> str:
    return {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")


def _grade_matches(grade: str, grade_filter: str) -> bool:
    if grade_filter == "All":
        return True
    return grade in _GRADE_GROUPS.get(grade_filter, set())


def _improvement_trend(interviews_chrono: list) -> str:
    """Return trend arrow based on first-half vs second-half avg percentage."""
    n = len(interviews_chrono)
    if n < 4:
        return "—"
    mid   = n // 2
    first = sum(i["percentage"] for i in interviews_chrono[:mid]) / mid
    last  = sum(i["percentage"] for i in interviews_chrono[-mid:]) / mid
    delta = last - first
    if delta >= 3:
        return f"📈 +{delta:.1f}%"
    if delta <= -3:
        return f"📉 {delta:.1f}%"
    return f"➡️ Stable"


# ════════════════════════════════════════════════════════════════════════════════
# Entry point
# ════════════════════════════════════════════════════════════════════════════════

def show_history_page():
    try:
        tab_history, tab_lb = st.tabs(["📜  Interview History", "🏆  Leaderboard"])

        with tab_history:
            _show_history()

        with tab_lb:
            _show_leaderboard()
    except Exception:
        print(traceback.format_exc())
        st.error("Something went wrong loading your history. Please try again.")


# ════════════════════════════════════════════════════════════════════════════════
# Tab 1 — Interview History
# ════════════════════════════════════════════════════════════════════════════════

def _show_history():
    st.title("📜 Your Interview History")

    uid        = st.session_state.get("user_id")
    interviews = get_user_interviews(uid)   # newest first

    if not interviews:
        _empty_state()
        return

    # ── Trend chart (always uses all data, oldest → newest) ───────────────────
    trend_rows = get_candidate_performance_trend(uid)
    _render_trend_chart(trend_rows)

    st.divider()

    # ── Filters ───────────────────────────────────────────────────────────────
    st.subheader("🔍 Filter Interviews")
    f1, f2, f3 = st.columns([2, 1, 2])

    with f1:
        domain_opts   = ["All Domains"] + sorted({iv["domain"] for iv in interviews})
        domain_filter = st.selectbox("Domain", domain_opts, key="hist_domain")

    with f2:
        grade_opts   = ["All", "A", "B", "C", "D", "F"]
        grade_filter = st.selectbox("Grade", grade_opts, key="hist_grade")

    with f3:
        date_range = st.radio(
            "Date Range",
            _DATE_RANGES,
            index=2,
            horizontal=True,
            key="hist_date",
        )

    # ── Apply filters ─────────────────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    cutoffs = {"Last 7 Days": now - timedelta(days=7),
               "Last 30 Days": now - timedelta(days=30),
               "All Time": None}
    cutoff = cutoffs[date_range]

    filtered = []
    for iv in interviews:
        if domain_filter != "All Domains" and iv["domain"] != domain_filter:
            continue
        if not _grade_matches(iv.get("grade", ""), grade_filter):
            continue
        if cutoff and (_aware(iv.get("completed_at")) or now) < cutoff:
            continue
        filtered.append(iv)

    # ── Summary stats ─────────────────────────────────────────────────────────
    _render_summary_stats(filtered, list(reversed(interviews)))

    st.divider()

    # ── Interview cards ───────────────────────────────────────────────────────
    st.subheader(f"📋 Interviews  ({len(filtered)} found)")
    if not filtered:
        st.info("No interviews match the selected filters. Try broadening the filters above.")
        return

    for iv in filtered:
        _render_interview_card(iv)


# ── Trend chart ───────────────────────────────────────────────────────────────

def _render_trend_chart(trend_rows: list):
    if len(trend_rows) < 2:
        return

    rows = []
    for t in trend_rows:
        dt = _aware(t.get("completed_at"))
        if not dt:
            continue
        rows.append({
            "Date":       dt,
            "Score (%)":  round(float(t["percentage"]), 1),
            "Domain":     t["domain"],
            "Grade":      t.get("letter_grade", ""),
            "Difficulty": t.get("difficulty", ""),
            "Sequence":   t["sequence"],
        })

    if len(rows) < 2:
        return

    df = pd.DataFrame(rows).sort_values("Date")

    st.subheader("📈 Performance Trend")

    # Build discrete color map covering only domains that appear in data
    present_domains = df["Domain"].unique().tolist()
    color_map = {d: _DOMAIN_COLORS.get(d, "#6c757d") for d in present_domains}

    fig = px.line(
        df,
        x="Date",
        y="Score (%)",
        color="Domain",
        markers=True,
        color_discrete_map=color_map,
        custom_data=["Domain", "Grade", "Difficulty"],
    )
    fig.update_traces(
        line_width=2.5,
        marker_size=9,
        marker_line_width=2,
        marker_line_color="white",
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Score: %{y:.1f}%<br>"
            "Grade: %{customdata[1]}<br>"
            "Difficulty: %{customdata[2]}<br>"
            "Date: %{x|%d %b %Y}<extra></extra>"
        ),
    )
    fig.add_hline(
        y=60, line_dash="dot", line_color="#ef4444", line_width=1.5,
        annotation_text="Pass threshold (60%)",
        annotation_font=dict(size=10, color="#ef4444"),
        annotation_position="top right",
    )
    fig.update_layout(
        yaxis=dict(range=[0, 105], title="Score (%)", gridcolor="#f1f5f9"),
        xaxis=dict(title="Date", gridcolor="#f1f5f9"),
        height=300,
        margin=dict(t=10, b=30, l=10, r=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.35,
                    xanchor="center", x=0.5, font=dict(size=11)),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Summary stats row ─────────────────────────────────────────────────────────

def _render_summary_stats(filtered: list, chrono_all: list):
    n = len(filtered)
    if n == 0:
        return

    avg_pct = sum(iv["percentage"] for iv in filtered) / n

    # Best domain (by avg percentage over all history, not just filtered)
    domain_scores: dict[str, list] = defaultdict(list)
    for iv in chrono_all:
        domain_scores[iv["domain"]].append(iv["percentage"])
    best_domain = max(
        domain_scores,
        key=lambda d: sum(domain_scores[d]) / len(domain_scores[d]),
        default="—",
    )
    best_domain_icon = DOMAIN_ICONS.get(best_domain, "")

    # Average letter grade from filtered
    from collections import Counter
    grade_cnt = Counter(iv.get("grade", "") for iv in filtered if iv.get("grade"))
    avg_grade  = grade_cnt.most_common(1)[0][0] if grade_cnt else "—"

    # Improvement trend (chronological all-time data)
    trend_str = _improvement_trend(chrono_all)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Interviews",  n)
    c2.metric("Best Domain",       f"{best_domain_icon} {best_domain}" if best_domain != "—" else "—")
    c3.metric("Most Common Grade", avg_grade)
    c4.metric("Improvement Trend", trend_str)


# ── Interview card ─────────────────────────────────────────────────────────────

def _render_interview_card(iv: dict):
    grade      = iv.get("grade") or iv.get("letter_grade", "—")
    pct        = float(iv.get("percentage", 0))
    domain     = iv.get("domain", "")
    difficulty = iv.get("difficulty", "")
    verdict    = iv.get("verdict", "")
    d_icon     = DOMAIN_ICONS.get(domain, "📝")
    d_color    = DIFFICULTY_COLORS.get(difficulty, "#6c757d")
    g_color    = _lcolor(grade)
    p_color    = _pct_color(pct)
    date_str   = _fmt_date(_aware(iv.get("completed_at")))
    duration   = _fmt_duration(iv.get("duration_minutes"))
    total_q    = iv.get("total_questions", "?")
    verdict_short = (verdict[:90] + "…") if len(verdict) > 90 else verdict

    st.markdown(
        f"""
        <div style="
            background:white; border:1px solid #e2e8f0;
            border-radius:14px; padding:1.2rem 1.5rem;
            box-shadow:0 1px 6px rgba(0,0,0,0.06); margin-bottom:0.7rem;
            border-left:5px solid {g_color};
        ">
            <div style="display:flex; justify-content:space-between;
                        align-items:flex-start; flex-wrap:wrap; gap:0.8rem;">

                <!-- Left column -->
                <div style="flex:1; min-width:240px;">
                    <div style="display:flex; align-items:center; gap:0.5rem;
                                flex-wrap:wrap; margin-bottom:0.4rem;">
                        <span style="font-size:1.05rem; font-weight:700; color:#0f172a;">
                            {d_icon}  {domain}
                        </span>
                        <span style="background:{d_color}; color:white; padding:2px 10px;
                              border-radius:12px; font-size:0.77rem; font-weight:700;">
                            {difficulty}
                        </span>
                        <span style="background:#f1f5f9; color:#475569; padding:2px 9px;
                              border-radius:12px; font-size:0.76rem;">
                            {total_q} questions
                        </span>
                    </div>
                    <div style="font-size:0.82rem; color:#64748b; margin-bottom:0.4rem;">
                        🗓️ {date_str}  ·  ⏱️ {duration}
                    </div>
                    <div style="font-size:0.85rem; color:#475569; font-style:italic;
                                max-width:480px;">
                        {verdict_short}
                    </div>
                </div>

                <!-- Right column: score -->
                <div style="text-align:center; min-width:100px;">
                    <div style="font-size:2.2rem; font-weight:900; color:{p_color};
                                line-height:1;">
                        {pct:.0f}<span style="font-size:1rem; color:#94a3b8;">%</span>
                    </div>
                    <div style="margin-top:0.3rem;">
                        <span style="background:{g_color}; color:white; padding:3px 14px;
                              border-radius:16px; font-size:0.9rem; font-weight:800;">
                            {grade}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Button rendered outside the HTML block (Streamlit requirement)
    _, btn_col = st.columns([5, 1])
    with btn_col:
        if st.button("View Details →", key=f"hist_view_{iv['id']}",
                     use_container_width=True):
            st.session_state.viewing_interview_id = iv["id"]
            st.session_state.current_page         = "results"
            st.rerun()

    st.markdown("<div style='margin-bottom:-0.5rem;'></div>", unsafe_allow_html=True)


# ── Empty state ────────────────────────────────────────────────────────────────

def _empty_state():
    st.markdown(
        """
        <div style="text-align:center; padding:3rem 1rem;">
            <div style="font-size:3.5rem; margin-bottom:0.8rem;">🚀</div>
            <h3 style="color:#1e3a8a; font-weight:800; margin-bottom:0.5rem;">
                No interviews yet
            </h3>
            <p style="color:#64748b; font-size:1rem; max-width:380px; margin:0 auto;">
                Complete your first interview to start building your history and tracking
                your improvement over time.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _, c, _ = st.columns([1, 2, 1])
    with c:
        if st.button("🎤  Start Your First Interview", type="primary",
                     use_container_width=True):
            st.session_state.interview_state = "not_started"
            st.session_state.current_page    = "interview"
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# Tab 2 — Leaderboard
# ════════════════════════════════════════════════════════════════════════════════

def _show_leaderboard():
    st.title("🏆 Leaderboard")
    st.markdown(
        "Rankings are based on **best single-interview score** in each domain. "
        "Names are partially masked for privacy."
    )

    uid = st.session_state.get("user_id")

    # ── Controls ──────────────────────────────────────────────────────────────
    ctrl_left, ctrl_right = st.columns([2, 1])
    with ctrl_left:
        domain_opts    = ["All Domains"] + DOMAINS
        selected       = st.selectbox("Domain", domain_opts, key="lb2_domain")
        domain_arg     = None if selected == "All Domains" else selected
    with ctrl_right:
        limit_display  = st.select_slider("Show Top", options=[5, 10, 20], value=10, key="lb2_limit")

    # ── Fetch data ────────────────────────────────────────────────────────────
    lb_all  = get_leaderboard(domain=domain_arg, limit=200)   # for rank finding
    lb_show = lb_all[:limit_display]

    # ── "Your rank" callout ───────────────────────────────────────────────────
    _render_rank_callout(lb_all, uid, selected)

    if not lb_show:
        st.markdown(
            """
            <div style="text-align:center; padding:2.5rem 1rem;">
                <div style="font-size:2.5rem; margin-bottom:0.6rem;">🏅</div>
                <div style="color:#64748b; font-size:0.95rem;">
                    No data yet for this domain. Complete an interview to appear here!
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ── Column headers ────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:1rem;
                    padding:0.5rem 1rem; margin-bottom:0.2rem;
                    font-size:0.75rem; font-weight:700; color:#94a3b8;
                    text-transform:uppercase; letter-spacing:0.8px;">
            <div style="width:48px; text-align:center;">Rank</div>
            <div style="flex:1;">Candidate</div>
            <div style="width:110px; text-align:center;">Best Score</div>
            <div style="width:95px; text-align:center;">Avg Score</div>
            <div style="width:80px; text-align:center;">Sessions</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Leaderboard rows ──────────────────────────────────────────────────────
    for entry in lb_show:
        _render_lb_row(entry, uid)

    # ── Domain summary (if filtered) ──────────────────────────────────────────
    if domain_arg and lb_show:
        best  = lb_show[0]
        avg_t = round(sum(e["avg_score"] for e in lb_show) / len(lb_show), 1)
        st.markdown(
            f"""
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px;
                 padding:0.8rem 1.2rem; margin-top:1rem; font-size:0.85rem; color:#475569;">
                <b>{domain_arg}</b>  ·  Top score: <b>{best['best_score']:.1f}%</b>
                  ·  Field average: <b>{avg_t:.1f}%</b>
                  ·  {len(lb_all)} candidate{'s' if len(lb_all)!=1 else ''} ranked
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_rank_callout(lb_all: list, uid: int | None, domain_label: str):
    """Show the current user's rank in a highlighted callout card."""
    if not uid or not lb_all:
        return

    user_entry = next((e for e in lb_all if e["id"] == uid), None)

    if user_entry:
        rank        = user_entry["rank"]
        best_score  = user_entry["best_score"]
        total_count = len(lb_all)
        rank_pct    = round(rank / total_count * 100) if total_count else 0
        medal       = _medal(rank)

        st.markdown(
            f"""
            <div style="
                background:linear-gradient(135deg,#1e3a8a 0%,#3b82f6 100%);
                border-radius:14px; padding:1.2rem 1.8rem; margin-bottom:1.2rem;
                display:flex; align-items:center; justify-content:space-between;
                flex-wrap:wrap; gap:1rem; color:white;">
                <div>
                    <div style="font-size:0.78rem; opacity:0.7; text-transform:uppercase;
                         letter-spacing:0.8px; font-weight:600;">Your Ranking</div>
                    <div style="font-size:1.6rem; font-weight:900; margin-top:0.2rem;">
                        {medal}  Rank #{rank}
                        <span style="font-size:0.95rem; opacity:0.8; font-weight:500;">
                            in {domain_label}
                        </span>
                    </div>
                    <div style="font-size:0.85rem; opacity:0.75; margin-top:0.3rem;">
                        Top {rank_pct}% of {total_count} candidate{'s' if total_count!=1 else ''}
                    </div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:2rem; font-weight:900; line-height:1;">
                        {best_score:.1f}<span style="font-size:1rem; opacity:0.65;">%</span>
                    </div>
                    <div style="font-size:0.78rem; opacity:0.65; margin-top:2px;">
                        Personal best
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # User hasn't interviewed in this domain / isn't ranked
        st.markdown(
            f"""
            <div style="background:#f8fafc; border:1px dashed #cbd5e1;
                 border-radius:12px; padding:1rem 1.4rem; margin-bottom:1rem;
                 text-align:center; color:#64748b;">
                You're not yet ranked in <b>{domain_label}</b>.
                Complete an interview to claim your spot!
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_lb_row(entry: dict, current_uid: int | None):
    rank       = entry["rank"]
    is_me      = (entry["id"] == current_uid)
    medal_text = _medal(rank)
    sc_color   = _pct_color(entry["best_score"])

    name_display = (
        f"<b>{entry['name']}</b> "
        f"<span style='background:#3b82f6;color:white;padding:1px 7px;"
        f"border-radius:4px;font-size:0.72rem;margin-left:4px;'>You</span>"
        if is_me
        else _mask_name(entry["name"])
    )

    bg        = "#eff6ff" if is_me else "white"
    border    = "2px solid #3b82f6" if is_me else "1px solid #f1f5f9"
    font_w    = "700" if is_me else "500"
    last_active = (
        entry["last_completed"].strftime("%d %b %Y")
        if entry.get("last_completed") else "—"
    )

    st.markdown(
        f"""
        <div style="
            background:{bg}; border:{border}; border-radius:10px;
            padding:0.85rem 1rem; margin-bottom:0.4rem;
            display:flex; align-items:center; gap:1rem;
            transition:box-shadow .15s;">
            <div style="width:48px; text-align:center; font-size:{'1.4rem' if rank<=3 else '0.95rem'};
                 font-weight:700; color:#334155;">
                {medal_text}
            </div>
            <div style="flex:1; min-width:120px;">
                <div style="font-weight:{font_w}; color:#0f172a; font-size:0.95rem;">
                    {name_display}
                </div>
                <div style="font-size:0.75rem; color:#94a3b8; margin-top:2px;">
                    Last active {last_active}
                </div>
            </div>
            <div style="width:110px; text-align:center;">
                <span style="font-size:1.15rem; font-weight:800; color:{sc_color};">
                    {entry['best_score']:.1f}%
                </span>
            </div>
            <div style="width:95px; text-align:center;
                 font-size:0.9rem; color:#64748b; font-weight:500;">
                {entry['avg_score']:.1f}%
            </div>
            <div style="width:80px; text-align:center; font-size:0.88rem; color:#94a3b8;">
                {entry['interview_count']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
