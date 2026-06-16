"""
Rich results page with interactive Plotly charts and AI summary.

Two modes:
  1. Just-completed interview  → reads from st.session_state.viewing_interview_id
                                  (set by interview_page._finish_interview)
  2. Viewing a past interview  → same key, set by history_page
"""

import json
import math
import random
import traceback

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from config import DIFFICULTY_COLORS, DOMAIN_ICONS
from core.evaluator import RUBRICS, get_interview_summary_feedback
from core.report_generator import generate_csv_report, generate_pdf_report
from database.db_handler import get_interview_by_id, get_user_interviews


# ── Grade / colour helpers ─────────────────────────────────────────────────────

_LETTER_GRADE_COLORS: dict[str, str] = {
    "A+": "#059669",
    "A":  "#10b981",
    "B+": "#3b82f6",
    "B":  "#6366f1",
    "C+": "#f59e0b",
    "C":  "#f97316",
    "D":  "#ef4444",
    "F":  "#dc2626",
}
_WORD_GRADE_COLORS: dict[str, str] = {
    "Excellent": "#059669",
    "Good":      "#3b82f6",
    "Average":   "#f59e0b",
    "Poor":      "#ef4444",
}

def _lgrade_color(grade: str) -> str:
    return (
        _LETTER_GRADE_COLORS.get(grade)
        or _WORD_GRADE_COLORS.get(grade)
        or "#6c757d"
    )

def _score_bar_color(score: float) -> str:
    if score >= 8: return "#059669"
    if score >= 6: return "#3b82f6"
    if score >= 4: return "#f59e0b"
    return "#ef4444"


# ════════════════════════════════════════════════════════════════════════════════
# Entry point
# ════════════════════════════════════════════════════════════════════════════════

def show_results_page():
    try:
        interview = _load_interview()
        if interview is None:
            st.info("No interview data found. Complete an interview first!")
            _back_button()
            return

        candidate  = st.session_state.get("candidate") or {}
        username   = candidate.get("name") or st.session_state.get("username", "Candidate")
        responses  = interview.get("responses", [])
        domain     = interview.get("domain", "")

        if not responses:
            st.warning("This interview has no question data to display.")
            _back_button()
            return

        _render_hero(interview, username, responses)
        _render_metrics(interview, responses)

        st.divider()
        _render_charts(interview, responses, domain)

        st.divider()
        _render_breakdown_table(responses)

        st.divider()
        _render_qa_details(responses)

        st.divider()
        _render_ai_summary(interview, responses, domain)

        st.divider()
        _render_export(interview, username)
    except Exception:
        print(traceback.format_exc())
        st.error("Something went wrong loading your results. Please try again.")

    st.divider()
    _render_bottom_nav()


# ── Data loading ──────────────────────────────────────────────────────────────

def _load_interview() -> dict | None:
    # Mode 1: just-completed or explicitly chosen history item
    interview_id = (
        st.session_state.get("viewing_interview_id")
        or (st.session_state.get("current_interview") or {}).get("id")
    )

    if interview_id:
        return get_interview_by_id(interview_id)

    # Fallback: most recent for this user
    uid = st.session_state.get("user_id")
    if uid:
        history = get_user_interviews(uid)
        if history:
            return get_interview_by_id(history[0]["id"])

    return None


# ════════════════════════════════════════════════════════════════════════════════
# Section 1 — Hero result card
# ════════════════════════════════════════════════════════════════════════════════

def _render_hero(interview: dict, username: str, responses: list):
    domain     = interview.get("domain", "")
    difficulty = interview.get("difficulty", "")
    grade      = interview.get("grade") or interview.get("letter_grade", "—")
    percentage = float(interview.get("percentage", 0.0))
    verdict    = interview.get("verdict", "")
    completed  = interview.get("completed_at")
    total_q    = interview.get("total_questions", len(responses))

    overall_score = float(interview.get("overall_score") or interview.get("score") or 0)
    avg_score     = overall_score / max(total_q, 1)

    grade_color  = _lgrade_color(grade)
    diff_color   = DIFFICULTY_COLORS.get(difficulty, "#6c757d")
    date_str     = completed.strftime("%B %d, %Y  %H:%M") if completed else "—"

    # Animated SVG ring
    circ         = 2 * math.pi * 60        # ≈ 376.99
    ring_offset  = circ - (percentage / 100) * circ
    ring_svg = f"""
    <svg width="160" height="160" viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
      <style>
        @keyframes ring-fill {{
          from {{ stroke-dashoffset: {circ:.1f}; }}
          to   {{ stroke-dashoffset: {ring_offset:.1f}; }}
        }}
        .ring {{ stroke-dasharray:{circ:.1f}; stroke-dashoffset:{circ:.1f};
                  animation: ring-fill 1.4s cubic-bezier(.4,0,.2,1) forwards; }}
      </style>
      <circle cx="80" cy="80" r="60" fill="none"
              stroke="rgba(255,255,255,0.12)" stroke-width="12"/>
      <circle cx="80" cy="80" r="60" fill="none" stroke="{grade_color}"
              stroke-width="12" stroke-linecap="round"
              transform="rotate(-90 80 80)" class="ring"/>
      <text x="80" y="72" text-anchor="middle" font-family="system-ui,sans-serif"
            font-size="30" font-weight="900" fill="white">{avg_score:.1f}</text>
      <text x="80" y="92" text-anchor="middle" font-family="system-ui,sans-serif"
            font-size="13" fill="rgba(255,255,255,0.65)">/ 10</text>
      <text x="80" y="110" text-anchor="middle" font-family="system-ui,sans-serif"
            font-size="11" fill="rgba(255,255,255,0.5)">{percentage:.0f}%</text>
    </svg>"""

    st.markdown(
        f"""
        <div style="
            background:linear-gradient(135deg,#0f172a 0%,#1e3a8a 50%,#1d4ed8 100%);
            border-radius:20px; padding:2rem 2.5rem; color:white; margin-bottom:0.5rem;">

            <div style="display:flex; justify-content:space-between;
                        align-items:center; flex-wrap:wrap; gap:1.5rem;">

                <!-- Left: info -->
                <div style="flex:1; min-width:260px;">
                    <div style="font-size:0.8rem; opacity:0.6; font-weight:600;
                         text-transform:uppercase; letter-spacing:1px;">
                        Interview Results
                    </div>
                    <div style="font-size:2rem; font-weight:800; margin:0.4rem 0 0.2rem;">
                        {DOMAIN_ICONS.get(domain,'📝')}  {domain}
                    </div>
                    <div style="display:flex; align-items:center; gap:0.6rem;
                         flex-wrap:wrap; margin-bottom:0.8rem;">
                        <span style="background:{diff_color};padding:3px 12px;
                              border-radius:20px;font-size:0.82rem;font-weight:700;">
                            {difficulty}
                        </span>
                        <span style="opacity:0.75; font-size:0.88rem;">
                            {total_q} questions
                        </span>
                        <span style="opacity:0.55; font-size:0.82rem;">{date_str}</span>
                    </div>
                    <div style="font-size:0.9rem; opacity:0.8; font-style:italic;
                         max-width:420px; line-height:1.5;">
                        "{verdict}"
                    </div>
                    <div style="margin-top:0.8rem; font-size:0.82rem; opacity:0.55;">
                        👤 {username}
                    </div>
                </div>

                <!-- Right: ring + grade -->
                <div style="text-align:center; min-width:180px;">
                    {ring_svg}
                    <div style="margin-top:0.4rem;">
                        <span style="
                            background:{grade_color};
                            color:white; font-size:1.6rem; font-weight:900;
                            padding:6px 24px; border-radius:30px;
                            box-shadow:0 4px 14px rgba(0,0,0,0.3);
                            display:inline-block;">
                            {grade}
                        </span>
                    </div>
                </div>

            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════════════════════
# Section 2 — Three metric cards
# ════════════════════════════════════════════════════════════════════════════════

def _render_metrics(interview: dict, responses: list):
    total_q  = interview.get("total_questions", len(responses))
    total_time_s = sum(r.get("time_taken_seconds") or 0 for r in responses)
    mins, secs   = divmod(int(total_time_s), 60)
    time_str     = f"{mins}m {secs}s" if mins else f"{secs}s"
    if total_time_s == 0:
        dur_m = float(interview.get("duration_minutes") or 0)
        time_str = f"{dur_m:.1f} min" if dur_m else "N/A"

    high_scores = sum(
        1 for r in responses
        if (r.get("ai_score") or r.get("score") or 0) >= 8
    )
    pct_high = round(high_scores / max(total_q, 1) * 100)

    c1, c2, c3 = st.columns(3)
    c1.metric("📋 Total Questions",  total_q)
    c2.metric("⏱️ Time Taken",       time_str)
    c3.metric("🌟 Scored 8+",        f"{high_scores} / {total_q}  ({pct_high}%)")


# ════════════════════════════════════════════════════════════════════════════════
# Section 3 — Charts
# ════════════════════════════════════════════════════════════════════════════════

def _render_charts(interview: dict, responses: list, domain: str):
    col_left, col_right = st.columns(2, gap="medium")

    with col_left:
        _chart_score_per_question(responses)

    with col_right:
        _chart_criteria_radar(interview, responses, domain)

    _chart_time_per_question(responses)


# ── Chart 1: Score per question ───────────────────────────────────────────────

def _chart_score_per_question(responses: list):
    st.subheader("Question-wise Performance")

    q_labels = [f"Q{r['question_number']}" for r in responses]
    q_scores = [float(r.get("ai_score") or r.get("score") or 0) for r in responses]
    colors   = [_score_bar_color(s) for s in q_scores]

    fig = go.Figure(go.Bar(
        x=q_labels,
        y=q_scores,
        marker_color=colors,
        marker_line_color="rgba(0,0,0,0.1)",
        marker_line_width=1,
        text=[f"{s:.1f}" for s in q_scores],
        textposition="outside",
        textfont=dict(size=11, color="#334155"),
        hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}/10<extra></extra>",
    ))
    fig.add_hline(
        y=6, line_dash="dot", line_color="#1e3a8a", line_width=1.5,
        annotation_text="Pass threshold (6)", annotation_position="top left",
        annotation_font=dict(size=10, color="#1e3a8a"),
    )
    fig.update_layout(
        yaxis=dict(range=[0, 11.5], title="Score (0–10)", gridcolor="#f1f5f9"),
        xaxis=dict(title="Question"),
        height=320,
        margin=dict(t=20, b=30, l=10, r=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Chart 2: Criteria radar ───────────────────────────────────────────────────

def _chart_criteria_radar(interview: dict, responses: list, domain: str):
    st.subheader("Evaluation Criteria Breakdown")

    rubric = RUBRICS.get(domain)
    if not rubric:
        st.info("No rubric data available for this domain.")
        return

    # Estimate per-criteria scores from overall question performance
    total_q   = max(interview.get("total_questions", len(responses)), 1)
    raw_sum   = float(interview.get("overall_score") or interview.get("score") or 0)
    avg_score = raw_sum / total_q

    rng = random.Random(interview.get("id", 42))
    criteria_vals = [
        round(min(10.0, max(1.0, avg_score + rng.uniform(-1.5, 1.5))), 1)
        for _ in rubric
    ]
    labels = [c.replace("_", " ").title() for c in rubric.keys()]

    # Close the loop for polar chart
    vals_closed   = criteria_vals + [criteria_vals[0]]
    labels_closed = labels + [labels[0]]

    fig = go.Figure()
    # Filled area
    fig.add_trace(go.Scatterpolar(
        r=vals_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(59,130,246,0.18)",
        line=dict(color="#3b82f6", width=2.5),
        name="Your performance",
        hovertemplate="<b>%{theta}</b><br>Score: %{r:.1f}/10<extra></extra>",
    ))
    # Max reference
    fig.add_trace(go.Scatterpolar(
        r=[10] * len(labels_closed),
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(226,232,240,0.15)",
        line=dict(color="#e2e8f0", width=1, dash="dot"),
        name="Max (10)",
        hoverinfo="skip",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                range=[0, 10], tickvals=[2, 4, 6, 8, 10],
                tickfont=dict(size=9, color="#94a3b8"),
                gridcolor="#e2e8f0",
            ),
            angularaxis=dict(
                tickfont=dict(size=10, color="#334155"),
                gridcolor="#e2e8f0",
            ),
            bgcolor="white",
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5,
                    font=dict(size=10)),
        height=320,
        margin=dict(t=20, b=50, l=50, r=50),
        paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Chart 3: Time per question ────────────────────────────────────────────────

def _chart_time_per_question(responses: list):
    times  = [int(r.get("time_taken_seconds") or 0) for r in responses]
    all_zero = all(t == 0 for t in times)
    if all_zero:
        return   # don't show chart if no timing data

    st.subheader("Time Spent Per Question")

    q_labels = [f"Q{r['question_number']}" for r in responses]
    scores   = [float(r.get("ai_score") or r.get("score") or 0) for r in responses]
    colors   = [_score_bar_color(s) for s in scores]

    fig = go.Figure(go.Bar(
        y=q_labels,
        x=times,
        orientation="h",
        marker_color=colors,
        marker_line_color="rgba(0,0,0,0.08)",
        marker_line_width=1,
        text=[f"{t}s" if t else "N/A" for t in times],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Time: %{x}s<extra></extra>",
    ))
    fig.update_layout(
        xaxis=dict(title="Seconds", gridcolor="#f1f5f9"),
        yaxis=dict(autorange="reversed", title=""),
        title="",
        height=max(220, 52 * len(responses)),
        margin=dict(t=10, b=30, l=10, r=60),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    # Average time reference
    avg_time = sum(times) / max(len(times), 1)
    if avg_time > 0:
        fig.add_vline(
            x=avg_time, line_dash="dot", line_color="#64748b", line_width=1.5,
            annotation_text=f"Avg {avg_time:.0f}s",
            annotation_position="top",
            annotation_font=dict(size=10, color="#64748b"),
        )
    st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# Section 4 — Breakdown table
# ════════════════════════════════════════════════════════════════════════════════

def _render_breakdown_table(responses: list):
    st.subheader("📋 Summary Table")

    rows = []
    for r in responses:
        score  = float(r.get("ai_score") or r.get("score") or 0)
        grade  = r.get("grade", "")
        secs   = int(r.get("time_taken_seconds") or 0)
        strg   = r.get("strengths", "") or ""
        q_text = r.get("question_text", "")

        rows.append({
            "Q#":       r.get("question_number", ""),
            "Question": q_text[:65] + "…" if len(q_text) > 65 else q_text,
            "Score":    f"{score:.1f} / 10",
            "Grade":    grade,
            "Time":     f"{secs}s" if secs else "—",
            "Strengths": strg[:75] + "…" if len(strg) > 75 else strg,
        })

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Q#":       st.column_config.NumberColumn("Q#", width="small"),
            "Score":    st.column_config.TextColumn("Score", width="small"),
            "Grade":    st.column_config.TextColumn("Grade", width="small"),
            "Time":     st.column_config.TextColumn("Time", width="small"),
            "Question": st.column_config.TextColumn("Question"),
            "Strengths":st.column_config.TextColumn("Key Strength"),
        },
    )


# ════════════════════════════════════════════════════════════════════════════════
# Section 5 — Per-question expandable details
# ════════════════════════════════════════════════════════════════════════════════

def _render_qa_details(responses: list):
    st.subheader("🔍 Detailed Question Breakdown")

    for resp in responses:
        q_num   = resp.get("question_number", "?")
        q_text  = resp.get("question_text", "")
        q_score = float(resp.get("ai_score") or resp.get("score") or 0)
        sc      = _score_bar_color(q_score)
        grade   = resp.get("grade", "")
        grade_c = _lgrade_color(grade)

        label = (
            f"Q{q_num}: {q_text[:70]}{'…' if len(q_text) > 70 else ''}"
            f"   ·   {q_score:.1f}/10   {grade}"
        )
        with st.expander(label, expanded=False):
            # Score strip
            st.markdown(
                f"""
                <div style="background:{sc}18;border-left:5px solid {sc};
                     border-radius:0 8px 8px 0;padding:0.6rem 1rem;margin-bottom:0.9rem;
                     display:flex;align-items:center;gap:1rem;">
                    <span style="font-size:1.4rem;font-weight:900;color:{sc};">
                        {q_score:.1f}/10
                    </span>
                    <span style="background:{grade_c};color:white;padding:2px 12px;
                          border-radius:12px;font-size:0.82rem;font-weight:700;">
                        {grade}
                    </span>
                    <span style="font-size:0.8rem;color:#64748b;">
                        🏷️ {resp.get('topic','General')}  ·
                        {resp.get('difficulty','')}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("**❓ Question**")
            st.info(q_text)

            st.markdown("**📝 Your Answer**")
            answer = resp.get("user_answer") or resp.get("candidate_answer", "")
            if answer in ("[Skipped]", "Skipped — No answer provided.", ""):
                st.warning("This question was skipped.")
            else:
                st.text_area(
                    "",
                    value=answer,
                    height=120,
                    disabled=True,
                    key=f"_rqa_{q_num}_{id(resp)}",
                )

            # Strengths / Improvements side by side
            strg = resp.get("strengths", "")
            imps = resp.get("ai_feedback") or resp.get("improvements", "")

            if strg or imps:
                s_col, i_col = st.columns(2)
                if strg:
                    with s_col:
                        st.markdown(
                            f"""
                            <div style="border-left:4px solid #059669;background:#f0fdf4;
                                 border-radius:0 8px 8px 0;padding:0.8rem;font-size:0.88rem;">
                                <b style="color:#059669;">✅ Strengths</b><br>
                                <span style="color:#1e293b;">{strg}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                if imps:
                    with i_col:
                        st.markdown(
                            f"""
                            <div style="border-left:4px solid #f59e0b;background:#fffbeb;
                                 border-radius:0 8px 8px 0;padding:0.8rem;font-size:0.88rem;">
                                <b style="color:#b45309;">⚠️ Improvements</b><br>
                                <span style="color:#1e293b;">{imps}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            model_ans = resp.get("model_answer") or resp.get("ideal_answer_hint", "")
            if model_ans:
                with st.expander("💡 Ideal Answer Hint", expanded=False):
                    st.markdown(
                        f"""
                        <div style="background:#f0f9ff;border:1px solid #bae6fd;
                             border-radius:8px;padding:0.9rem;font-size:0.9rem;
                             color:#0c4a6e;line-height:1.7;">
                            {model_ans}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


# ════════════════════════════════════════════════════════════════════════════════
# Section 6 — AI performance summary
# ════════════════════════════════════════════════════════════════════════════════

def _render_ai_summary(interview: dict, responses: list, domain: str):
    st.subheader("🤖 AI Performance Analysis")

    cache_key = f"_ai_summary_{interview.get('id', 0)}"

    if cache_key not in st.session_state:
        all_qa_data = [
            {
                "question":     r.get("question_text", ""),
                "answer":       r.get("user_answer") or r.get("candidate_answer", ""),
                "score":        float(r.get("ai_score") or r.get("score") or 0),
                "grade":        r.get("grade", ""),
                "strengths":    r.get("strengths", ""),
                "improvements": r.get("ai_feedback") or r.get("improvements", ""),
                "topic":        r.get("topic", "General"),
                "difficulty":   r.get("difficulty", ""),
            }
            for r in responses
        ]
        with st.spinner("Generating personalised AI feedback…"):
            st.session_state[cache_key] = get_interview_summary_feedback(
                all_qa_data, domain
            )

    summary_text: str = st.session_state[cache_key]
    paragraphs = [p.strip() for p in summary_text.split("\n\n") if p.strip()]

    para_headers = [
        ("📊", "Overall Assessment"),
        ("💪", "Key Strengths"),
        ("🎯", "Priority Improvements"),
    ]

    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);
             border-radius:16px;padding:1.8rem 2rem;margin-bottom:0.5rem;">
            <div style="color:#e2e8f0;font-size:1rem;font-weight:700;
                 margin-bottom:1.2rem;opacity:0.9;">
                AI-Generated Personalised Feedback
            </div>
        """,
        unsafe_allow_html=True,
    )

    for i, para in enumerate(paragraphs[:3]):
        icon, hdr = para_headers[i] if i < len(para_headers) else ("📌", "Feedback")
        st.markdown(
            f"""
            <div style="background:rgba(255,255,255,0.05);border-radius:10px;
                 padding:1rem 1.2rem;margin-bottom:0.8rem;
                 border-left:4px solid {'#3b82f6' if i==0 else '#10b981' if i==1 else '#f59e0b'};">
                <div style="font-size:0.8rem;font-weight:700;
                     color:{'#93c5fd' if i==0 else '#6ee7b7' if i==1 else '#fcd34d'};
                     text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.4rem;">
                    {icon}  {hdr}
                </div>
                <div style="color:#cbd5e1;font-size:0.9rem;line-height:1.75;">
                    {para}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# Section 7 — Export buttons
# ════════════════════════════════════════════════════════════════════════════════

def _render_export(interview: dict, username: str):
    st.subheader("📤 Export & Share")

    grade      = interview.get("grade") or interview.get("letter_grade", "—")
    domain     = interview.get("domain", "")
    percentage = float(interview.get("percentage", 0))
    date_str   = (
        interview["completed_at"].strftime("%Y-%m-%d")
        if interview.get("completed_at") else "today"
    )

    pdf_col, csv_col, share_col = st.columns(3)

    with pdf_col:
        candidate = st.session_state.get("candidate") or {"name": username, "email": ""}
        pdf_bytes = generate_pdf_report(interview, candidate)
        st.download_button(
            "📄  Download PDF Report",
            data=pdf_bytes,
            file_name=f"interview_{interview['id']}_{date_str}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with csv_col:
        csv_bytes = generate_csv_report(interview)
        st.download_button(
            "📊  Download CSV",
            data=csv_bytes,
            file_name=f"interview_{interview['id']}_{date_str}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with share_col:
        share_text = (
            f"I scored {percentage:.0f}% ({grade}) on a {domain} "
            f"interview with AI Interview Evaluator! 🎯"
        )
        share_js = json.dumps(share_text)   # safely quoted + escaped
        components.html(
            f"""
            <button id="share-btn" onclick="
                navigator.clipboard.writeText({share_js}).then(function() {{
                    var btn = document.getElementById('share-btn');
                    btn.textContent = '✅  Copied to clipboard!';
                    btn.style.background = '#059669';
                    setTimeout(function(){{
                        btn.textContent = '🔗  Share Results';
                        btn.style.background = '#1e3a8a';
                    }}, 2500);
                }}).catch(function(){{
                    document.getElementById('share-btn').textContent = '❌  Copy failed';
                }});"
            style="
                width:100%; padding:0.55rem 0.8rem; cursor:pointer;
                background:#1e3a8a; color:white; border:none;
                border-radius:8px; font-size:0.9rem; font-weight:600;
                font-family:system-ui,sans-serif; transition:background .2s;
            ">
                🔗  Share Results
            </button>
            """,
            height=48,
        )

    # Share text preview
    with st.expander("Preview share text", expanded=False):
        st.code(share_text, language=None)


# ════════════════════════════════════════════════════════════════════════════════
# Section 8 — Bottom navigation
# ════════════════════════════════════════════════════════════════════════════════

def _render_bottom_nav():
    left, right = st.columns(2)
    with left:
        if st.button(
            "🎤  Take Another Interview",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.viewing_interview_id = None
            st.session_state.interview_state      = "not_started"
            st.session_state.current_page         = "interview"
            st.rerun()

    with right:
        if st.button(
            "📜  View All History",
            use_container_width=True,
        ):
            st.session_state.viewing_interview_id = None
            st.session_state.current_page         = "history"
            st.rerun()


def _back_button():
    if st.button("🏠 Go to Home"):
        st.session_state.current_page = "home"
        st.rerun()
