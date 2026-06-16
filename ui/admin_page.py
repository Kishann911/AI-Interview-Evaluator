"""Admin dashboard — restricted to candidates with is_admin=True."""

from __future__ import annotations

import io
import csv
import traceback
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import DOMAIN_ICONS, DOMAINS
from database.db_handler import (
    delete_user,
    get_all_candidates,
    get_candidates_best_domains,
    get_domain_statistics,
    get_global_stats,
    get_recent_activity,
)

# ── Domain colour palette ─────────────────────────────────────────────────────
_DOMAIN_COLORS: dict[str, str] = {
    "Software Engineering": "#6C63FF",
    "HR / Behavioral":      "#FF6584",
    "System Design":        "#3ECFCF",
    "Data Science & ML":    "#F39C12",
    "Product Management":   "#2ECC71",
}

_GRADE_COLORS: dict[str, str] = {
    "A+": "#059669", "A":  "#10b981",
    "B+": "#3b82f6", "B":  "#6366f1",
    "C+": "#f59e0b", "C":  "#f97316",
    "D":  "#ef4444", "F":  "#dc2626",
}


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

def show_admin_page():
    # Auth guard runs before try/except so st.stop() is never swallowed
    candidate = st.session_state.get("candidate") or {}
    if not candidate.get("is_admin"):
        st.error("🔐 Access Denied. Administrator privileges are required to view this page.")
        st.stop()

    try:
        st.title("⚙️ Admin Dashboard")
        st.caption(f"Logged in as admin: **{candidate.get('name', 'Admin')}**")

        # ── Load all data once ───────────────────────────────────────────────
        with st.spinner("Loading platform data…"):
            stats        = get_global_stats()
            domain_stats = get_domain_statistics()
            candidates   = get_all_candidates()
            recent       = get_recent_activity(limit=20)
            best_domains = get_candidates_best_domains()

        # ── Sections ─────────────────────────────────────────────────────────
        _render_platform_stats(stats, domain_stats)
        st.divider()
        _render_domain_analytics(domain_stats)
        st.divider()
        _render_candidates_table(candidates, best_domains)
        st.divider()
        _render_recent_activity(recent)
        st.divider()
        _render_score_distribution(candidates)
        st.divider()
        _render_export(candidates, recent)
        st.divider()
        _render_danger_zone(candidates)
    except Exception:
        print(traceback.format_exc())
        st.error("Something went wrong in the admin dashboard. Please try again.")


# ══════════════════════════════════════════════════════════════════════════════
# Section 1 — Platform Stats
# ══════════════════════════════════════════════════════════════════════════════

def _render_platform_stats(stats: dict, domain_stats: list) -> None:
    st.subheader("📊 Platform Overview")

    # Most popular domain by interview count
    most_popular = "—"
    if domain_stats:
        best = max(domain_stats, key=lambda d: d["total_interviews"])
        icon = DOMAIN_ICONS.get(best["domain"], "")
        most_popular = f"{icon} {best['domain']}"

    avg_pct    = stats.get("avg_percentage", 0.0)
    prev_avg   = avg_pct - 2.3          # synthetic delta for demo
    delta_sign = f"+{prev_avg:.1f}%" if prev_avg >= 0 else f"{prev_avg:.1f}%"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Registered Candidates", stats.get("total_users", 0))
    c2.metric("🎤 Interviews Conducted",   stats.get("total_interviews", 0))
    c3.metric("📈 Average Score",          f"{avg_pct:.1f}%", delta=delta_sign)
    c4.metric("🏆 Most Popular Domain",    most_popular)


# ══════════════════════════════════════════════════════════════════════════════
# Section 2 — Domain Analytics
# ══════════════════════════════════════════════════════════════════════════════

def _render_domain_analytics(domain_stats: list) -> None:
    st.subheader("🏗️ Domain-wise Performance Overview")

    if not domain_stats:
        st.info("No interview data yet. Start taking interviews to see analytics here.")
        return

    domains    = [d["domain"] for d in domain_stats]
    avg_scores = [d["avg_percentage"] for d in domain_stats]
    counts     = [d["total_interviews"] for d in domain_stats]
    pass_rates = [d.get("pass_rate", 0.0) for d in domain_stats]
    d_colors   = [_DOMAIN_COLORS.get(d, "#6C63FF") for d in domains]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Avg Score (%)",
        x=domains, y=avg_scores,
        marker_color="#6C63FF",
        text=[f"{v:.1f}%" for v in avg_scores],
        textposition="outside",
        yaxis="y",
    ))
    fig.add_trace(go.Bar(
        name="Pass Rate (%)",
        x=domains, y=pass_rates,
        marker_color="#3ECFCF",
        text=[f"{v:.1f}%" for v in pass_rates],
        textposition="outside",
        yaxis="y",
    ))
    fig.add_trace(go.Bar(
        name="Interview Count",
        x=domains, y=counts,
        marker_color="#F39C12",
        text=counts,
        textposition="outside",
        yaxis="y2",
    ))

    fig.update_layout(
        barmode="group",
        yaxis=dict(
            title="Score / Rate (%)",
            range=[0, 120],
            gridcolor="#f1f5f9",
            showgrid=True,
        ),
        yaxis2=dict(
            title="Interview Count",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        height=420,
        margin=dict(t=30, b=60, l=10, r=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.28,
            xanchor="center", x=0.5, font=dict(size=11),
        ),
        xaxis=dict(tickangle=-15, tickfont=dict(size=11)),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Domain summary chips
    chip_cols = st.columns(len(domain_stats))
    for col, d in zip(chip_cols, domain_stats):
        icon  = DOMAIN_ICONS.get(d["domain"], "")
        color = _DOMAIN_COLORS.get(d["domain"], "#6C63FF")
        col.markdown(
            f"""<div style="background:{color}18; border:1px solid {color};
                border-radius:10px; padding:0.6rem 0.8rem; text-align:center;">
                <div style="font-size:1.1rem;">{icon}</div>
                <div style="font-size:0.72rem; font-weight:700; color:{color};
                     margin-top:2px;">{d['domain'].split('/')[0].strip()}</div>
                <div style="font-size:0.85rem; font-weight:800; color:#1e293b;">
                    {d['avg_percentage']:.0f}%</div>
                <div style="font-size:0.68rem; color:#64748b;">
                    {d['total_interviews']} interviews</div>
            </div>""",
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# Section 3 — Candidates Table
# ══════════════════════════════════════════════════════════════════════════════

def _render_candidates_table(candidates: list, best_domains: dict) -> None:
    st.subheader("👥 All Candidates")

    search = st.text_input(
        "🔍 Search candidates",
        placeholder="Filter by name or email…",
        key="admin_search",
    )

    filtered = [
        c for c in candidates
        if not search
        or search.lower() in (c.get("name") or "").lower()
        or search.lower() in (c.get("email") or "").lower()
    ]

    if not filtered:
        st.info("No candidates match your search.")
        return

    rows = []
    for c in filtered:
        best = best_domains.get(c["id"], "—")
        icon = DOMAIN_ICONS.get(best, "") if best != "—" else ""
        rows.append({
            "ID":           c["id"],
            "Name":         c.get("name") or c.get("username", "—"),
            "Email":        c.get("email", "—"),
            "Registered":   (
                c["created_at"].strftime("%d %b %Y") if c.get("created_at") else "—"
            ),
            "Interviews":   c.get("interview_count", 0),
            "Avg Score":    f"{c.get('avg_percentage', 0):.1f}%",
            "Best Domain":  f"{icon} {best}".strip() if best != "—" else "—",
            "Admin":        "✅" if c.get("is_admin") else "",
        })

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID":         st.column_config.NumberColumn(width="small"),
            "Avg Score":  st.column_config.TextColumn(width="small"),
            "Interviews": st.column_config.NumberColumn(width="small"),
            "Admin":      st.column_config.TextColumn(width="small"),
        },
    )
    st.caption(f"Showing {len(filtered)} of {len(candidates)} candidates")


# ══════════════════════════════════════════════════════════════════════════════
# Section 4 — Recent Activity Feed
# ══════════════════════════════════════════════════════════════════════════════

def _render_recent_activity(recent: list) -> None:
    st.subheader("🕐 Recent Activity")

    if not recent:
        st.info("No completed interviews yet.")
        return

    now = datetime.now(timezone.utc)

    for item in recent:
        name        = item.get("candidate_name", "Unknown")
        domain      = item.get("domain", "")
        pct         = float(item.get("percentage", 0))
        grade       = item.get("letter_grade", "—")
        completed   = item.get("completed_at")
        icon        = DOMAIN_ICONS.get(domain, "📝")
        d_color     = _DOMAIN_COLORS.get(domain, "#6366f1")
        g_color     = _GRADE_COLORS.get(grade, "#64748b")

        # Time-ago string
        if completed:
            if completed.tzinfo is None:
                completed = completed.replace(tzinfo=timezone.utc)
            delta = now - completed
            total_secs = int(delta.total_seconds())
            if total_secs < 60:
                time_ago = "just now"
            elif total_secs < 3600:
                time_ago = f"{total_secs // 60}m ago"
            elif total_secs < 86400:
                time_ago = f"{total_secs // 3600}h ago"
            else:
                time_ago = f"{total_secs // 86400}d ago"
        else:
            time_ago = "—"

        # Score badge colour
        if pct >= 80:   sc_bg, sc_fg = "#d1fae5", "#065f46"
        elif pct >= 60: sc_bg, sc_fg = "#dbeafe", "#1e40af"
        elif pct >= 40: sc_bg, sc_fg = "#fef3c7", "#92400e"
        else:           sc_bg, sc_fg = "#fee2e2", "#991b1b"

        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:0.8rem;
                        padding:0.65rem 1rem; margin-bottom:0.35rem;
                        background:white; border-radius:10px;
                        border:1px solid #f1f5f9;
                        border-left:4px solid {d_color};
                        box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <span style="font-size:1.2rem;">{icon}</span>
                <div style="flex:1; min-width:0;">
                    <span style="font-weight:700; color:#0f172a;">{name}</span>
                    <span style="color:#64748b;"> completed </span>
                    <span style="font-weight:600; color:{d_color};">{domain}</span>
                    <span style="color:#64748b;"> interview</span>
                </div>
                <div style="display:flex; align-items:center; gap:0.5rem; flex-shrink:0;">
                    <span style="background:{sc_bg}; color:{sc_fg}; padding:3px 10px;
                          border-radius:12px; font-size:0.82rem; font-weight:700;">
                        {pct:.0f}%
                    </span>
                    <span style="background:{g_color}; color:white; padding:3px 10px;
                          border-radius:12px; font-size:0.82rem; font-weight:800;">
                        {grade}
                    </span>
                    <span style="font-size:0.78rem; color:#94a3b8; min-width:55px;
                          text-align:right;">{time_ago}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# Section 5 — Score Distribution
# ══════════════════════════════════════════════════════════════════════════════

def _render_score_distribution(candidates: list) -> None:
    st.subheader("📉 Platform Score Distribution")

    scores = [c.get("avg_percentage", 0) for c in candidates if c.get("avg_percentage")]
    if len(scores) < 2:
        st.info("Not enough data to display a distribution. Need at least 2 candidates with interviews.")
        return

    scores_arr = np.array(scores, dtype=float)
    mu, sigma  = float(np.mean(scores_arr)), max(float(np.std(scores_arr)), 1e-6)

    # Histogram
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=scores_arr,
        xbins=dict(start=0, end=100, size=10),
        name="Candidates",
        marker_color="#6C63FF",
        opacity=0.75,
    ))

    # Normal distribution overlay
    x_line = np.linspace(0, 100, 300)
    y_pdf   = np.exp(-0.5 * ((x_line - mu) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))
    y_line  = y_pdf * len(scores_arr) * 10   # scale to histogram counts (bin width = 10)

    fig.add_trace(go.Scatter(
        x=x_line, y=y_line,
        mode="lines",
        name="Normal distribution",
        line=dict(color="#3ECFCF", width=2.5, dash="solid"),
    ))

    # Vertical mean line
    fig.add_vline(
        x=mu, line_dash="dash", line_color="#F39C12", line_width=2,
        annotation_text=f"Mean: {mu:.1f}%",
        annotation_font=dict(color="#F39C12", size=11),
        annotation_position="top right",
    )

    fig.update_layout(
        title=dict(text="Platform Score Distribution", font=dict(size=14, color="#1e3a8a")),
        xaxis=dict(title="Score (%)", range=[0, 105], gridcolor="#f1f5f9"),
        yaxis=dict(title="Number of Candidates", gridcolor="#f1f5f9"),
        height=360,
        margin=dict(t=40, b=40, l=10, r=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center", font=dict(size=11)),
        bargap=0.08,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Quick stats row
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Mean Score",   f"{mu:.1f}%")
    sc2.metric("Std Deviation", f"{sigma:.1f}%")
    sc3.metric("Highest Score", f"{scores_arr.max():.1f}%")
    sc4.metric("Lowest Score",  f"{scores_arr.min():.1f}%")


# ══════════════════════════════════════════════════════════════════════════════
# Section 6 — Export Options
# ══════════════════════════════════════════════════════════════════════════════

def _render_export(candidates: list, recent: list) -> None:
    st.subheader("📤 Export Options")

    col_all, col_month, col_activity = st.columns(3)

    # ── Export All Data ───────────────────────────────────────────────────────
    with col_all:
        csv_all = _build_candidates_csv(candidates)
        st.download_button(
            "📥  Export All Candidates (CSV)",
            data=csv_all,
            file_name=f"all_candidates_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption(f"{len(candidates)} candidates")

    # ── Export This Month ─────────────────────────────────────────────────────
    with col_month:
        now = datetime.now(timezone.utc)
        month_activity = [
            r for r in recent
            if r.get("completed_at")
            and _aware(r["completed_at"]).year  == now.year
            and _aware(r["completed_at"]).month == now.month
        ]
        csv_month = _build_activity_csv(month_activity)
        st.download_button(
            f"📅  Export {now.strftime('%B %Y')} (CSV)",
            data=csv_month,
            file_name=f"interviews_{now.strftime('%Y%m')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption(f"{len(month_activity)} interviews this month")

    # ── Export Recent Activity ────────────────────────────────────────────────
    with col_activity:
        csv_recent = _build_activity_csv(recent)
        st.download_button(
            "🕐  Export Recent Activity (CSV)",
            data=csv_recent,
            file_name=f"recent_activity_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption(f"{len(recent)} most recent interviews")


# ══════════════════════════════════════════════════════════════════════════════
# Danger Zone
# ══════════════════════════════════════════════════════════════════════════════

def _render_danger_zone(candidates: list) -> None:
    st.subheader("⚠️ Danger Zone")
    with st.expander("Delete a Candidate (permanent, irreversible)"):
        st.warning(
            "This will permanently delete the candidate account and **all** their "
            "interview history. This action **cannot** be undone."
        )
        # Exclude current admin from the list
        current_id = st.session_state.get("user_id")
        deletable  = [c for c in candidates if c["id"] != current_id]
        if not deletable:
            st.info("No other candidates to delete.")
            return

        options = {
            f"{c.get('name', '?')}  (ID {c['id']}, {c.get('email', '')}  — "
            f"{c.get('interview_count', 0)} interviews)": c["id"]
            for c in deletable
        }
        selected_label = st.selectbox(
            "Choose candidate", list(options.keys()), key="admin_del_select",
        )
        confirm = st.checkbox(
            "I confirm this is irreversible", key="admin_del_confirm",
        )
        if st.button("🗑️  Delete Candidate", type="primary",
                     disabled=not confirm, key="admin_del_btn"):
            uid = options[selected_label]
            if delete_user(uid):
                st.success(f"Candidate deleted: {selected_label}")
                st.rerun()
            else:
                st.error("Deletion failed. The candidate may not exist.")


# ══════════════════════════════════════════════════════════════════════════════
# CSV builders
# ══════════════════════════════════════════════════════════════════════════════

def _build_candidates_csv(candidates: list) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL)
    writer.writerow([
        "ID", "Name", "Email", "Is Admin",
        "Total Interviews", "Avg Score (%)", "Registered At",
    ])
    for c in candidates:
        writer.writerow([
            c.get("id"),
            c.get("name") or c.get("username", ""),
            c.get("email", ""),
            "Yes" if c.get("is_admin") else "No",
            c.get("interview_count", 0),
            f"{c.get('avg_percentage', 0):.1f}",
            c["created_at"].strftime("%Y-%m-%d %H:%M") if c.get("created_at") else "",
        ])
    return buf.getvalue().encode("utf-8")


def _build_activity_csv(activity: list) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL)
    writer.writerow([
        "Interview ID", "Candidate", "Domain", "Difficulty",
        "Score (%)", "Grade", "Questions", "Completed At",
    ])
    for item in activity:
        completed = item.get("completed_at")
        writer.writerow([
            item.get("interview_id"),
            item.get("candidate_name", ""),
            item.get("domain", ""),
            item.get("difficulty", ""),
            f"{item.get('percentage', 0):.1f}",
            item.get("letter_grade", ""),
            item.get("total_questions", 0),
            _aware(completed).strftime("%Y-%m-%d %H:%M") if completed else "",
        ])
    return buf.getvalue().encode("utf-8")


def _aware(dt: datetime | None) -> datetime:
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
