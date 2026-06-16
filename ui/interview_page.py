"""
Interactive interview experience for AI Interview Evaluator.

State machine:
    not_started  ──Begin──►  in_progress  ──Submit/Skip──►  evaluating
                                  ▲                               │
                                  └────────Next Question──────────┘
                                                  │ (after last question)
                                                  ▼
                                             completed  ──save──►  results page
"""

import time
import traceback
from datetime import datetime, timezone

import streamlit as st

from config import (
    DOMAINS, DIFFICULTY_LEVELS, QUESTION_COUNT_OPTIONS,
    DOMAIN_ICONS, DIFFICULTY_COLORS,
)
from core.evaluator import evaluate_answer
from core.questions import get_questions
from database.db_handler import save_interview


# ── Colour helpers ─────────────────────────────────────────────────────────────

_GRADE_COLORS = {
    "Excellent": "#059669",
    "Good":      "#3b82f6",
    "Average":   "#f59e0b",
    "Poor":      "#ef4444",
}

def _score_color(score: float) -> str:
    if score >= 8: return "#059669"
    if score >= 6: return "#3b82f6"
    if score >= 4: return "#f59e0b"
    return "#ef4444"


# ── Interview rules ────────────────────────────────────────────────────────────

_RULES = [
    ("📌", "Answer each question as completely as you can."),
    ("⏱️",  "There is no strict time limit — take as long as you need."),
    ("🔍", "Be specific. Use real-world examples from your experience."),
    ("⏭️",  "You can skip a question, but try your best first."),
    ("🤖", "Each answer is evaluated by AI immediately after submission."),
]


# ── Session-state management ───────────────────────────────────────────────────

def _ensure_state():
    """Initialise every interview-related session-state key idempotently."""
    defaults: dict = {
        "interview_state":        "not_started",
        "current_question_index": 0,
        "questions_list":         [],
        "answers_given":          [],
        "time_taken_list":        [],
        "evaluations":            [],
        "interview_start_time":   None,   # float (Unix timestamp)
        "question_start_time":    None,   # float (Unix timestamp)
        "interview_domain":       None,
        "interview_difficulty":   None,
        "interview_id":           None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # Normalise legacy state values written by auth_page / old code
    if st.session_state.interview_state in ("setup", "complete"):
        st.session_state.interview_state = "not_started"

    # Migrate old key names set by app.py Quick Start (before this rewrite)
    if st.session_state.interview_state == "in_progress":
        _migrate_legacy_keys()


def _migrate_legacy_keys():
    """Transparently migrate old interview key names → new ones."""
    if st.session_state.questions_list:
        return  # already using new keys
    old_qs = st.session_state.get("interview_questions", [])
    if not old_qs:
        return
    n = len(old_qs)
    st.session_state.questions_list         = old_qs
    st.session_state.answers_given          = [""] * n
    st.session_state.time_taken_list        = [0] * n
    st.session_state.evaluations            = []
    st.session_state.current_question_index = int(st.session_state.get("interview_current", 0))
    now = time.time()
    st.session_state.interview_start_time   = now
    st.session_state.question_start_time    = now


def _reset():
    """Wipe all interview-specific session state."""
    wipe = [
        "interview_state", "current_question_index", "questions_list",
        "answers_given", "time_taken_list", "evaluations",
        "interview_start_time", "question_start_time",
        "interview_domain", "interview_difficulty", "interview_id",
        # legacy keys
        "interview_questions", "interview_answers", "interview_current",
        "interview_results",
    ]
    for k in wipe:
        st.session_state.pop(k, None)
    # Clear per-question text_area widget keys
    for k in list(st.session_state.keys()):
        if k.startswith("_qa_"):
            del st.session_state[k]


# ════════════════════════════════════════════════════════════════════════════════
# Entry point
# ════════════════════════════════════════════════════════════════════════════════

def show_interview_page():
    try:
        _ensure_state()
        state = st.session_state.interview_state

        if state == "not_started":
            _show_not_started()
        elif state == "in_progress":
            _show_in_progress()
        elif state == "evaluating":
            _show_evaluating()
        elif state == "completed":
            _finish_interview()
        else:
            _reset()
            st.rerun()
    except Exception:
        print(traceback.format_exc())
        st.error("Something went wrong on the interview page. Please try again.")


# ════════════════════════════════════════════════════════════════════════════════
# State: not_started
# ════════════════════════════════════════════════════════════════════════════════

def _show_not_started():
    # ── Hero header ───────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center; padding:1.5rem 0 1rem;">
            <div style="font-size:3rem; filter:drop-shadow(0 4px 8px rgba(30,58,138,.2));">🎯</div>
            <h1 style="color:#1e3a8a; font-size:2rem; font-weight:800; margin:0.5rem 0 0.2rem;">
                Ready to Begin?
            </h1>
            <p style="color:#64748b; font-size:1rem; margin:0;">
                Configure your session, review the rules, then start.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    left, right = st.columns([1, 1], gap="large")

    # ── Left: configuration ───────────────────────────────────────────────────
    with left:
        st.markdown("#### ⚙️ Interview Settings")

        prev_domain = st.session_state.get("interview_domain")
        domain_idx  = DOMAINS.index(prev_domain) if prev_domain in DOMAINS else 0
        domain = st.selectbox(
            "Domain",
            DOMAINS,
            index=domain_idx,
            format_func=lambda d: f"{DOMAIN_ICONS.get(d, '')}  {d}",
            key="_ns_domain",
        )

        prev_diff = st.session_state.get("interview_difficulty")
        diff_idx  = DIFFICULTY_LEVELS.index(prev_diff) if prev_diff in DIFFICULTY_LEVELS else 0
        difficulty = st.radio(
            "Difficulty Level",
            DIFFICULTY_LEVELS,
            index=diff_idx,
            horizontal=True,
            key="_ns_diff",
        )

        question_count = st.select_slider(
            "Number of Questions",
            options=QUESTION_COUNT_OPTIONS,
            value=QUESTION_COUNT_OPTIONS[0],
            key="_ns_count",
        )

        # Live preview card
        d_color = DIFFICULTY_COLORS.get(difficulty, "#6c757d")
        st.markdown(
            f"""
            <div style="
                background:linear-gradient(135deg,#1e3a8a 0%,#3b82f6 100%);
                border-radius:14px; padding:1.4rem 1.6rem; color:white; margin-top:1rem;">
                <div style="font-size:2rem;">{DOMAIN_ICONS.get(domain,'📝')}</div>
                <div style="font-size:1.15rem; font-weight:800; margin-top:0.4rem;">{domain}</div>
                <div style="margin-top:0.6rem;">
                    <span style="background:{d_color};padding:3px 12px;border-radius:20px;
                          font-size:0.8rem;font-weight:700;">{difficulty}</span>
                    <span style="margin-left:0.6rem;font-size:0.9rem;opacity:0.9;">
                        {question_count} question{'s' if question_count != 1 else ''}
                    </span>
                </div>
                <div style="margin-top:0.7rem;font-size:0.82rem;opacity:0.75;">
                    ⏱️ Estimated time: {question_count * 3}–{question_count * 5} min
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Right: rules ──────────────────────────────────────────────────────────
    with right:
        st.markdown("#### 📋 Interview Rules")
        for icon, rule in _RULES:
            st.markdown(
                f"""
                <div style="
                    display:flex; align-items:flex-start; gap:0.7rem;
                    background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px;
                    padding:0.7rem 0.9rem; margin-bottom:0.5rem;">
                    <span style="font-size:1.1rem;">{icon}</span>
                    <span style="color:#334155; font-size:0.9rem; line-height:1.5;">{rule}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            <div style="
                background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px;
                padding:0.8rem 1rem; margin-top:0.8rem;">
                <span style="color:#1e40af; font-size:0.88rem; font-weight:600;">
                    💡 Tip: Longer, more detailed answers score higher across all domains.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Begin button ──────────────────────────────────────────────────────────
    st.divider()
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        if st.button("🚀  Begin Interview", type="primary", use_container_width=True):
            questions = get_questions(domain, question_count, difficulty)
            if not questions:
                st.error(
                    f"No questions available for **{domain}** / **{difficulty}**. "
                    "Please try another combination."
                )
                return
            n = len(questions)
            now = time.time()
            st.session_state.interview_domain        = domain
            st.session_state.interview_difficulty    = difficulty
            st.session_state.questions_list          = questions
            st.session_state.answers_given           = [""] * n
            st.session_state.time_taken_list         = [0] * n
            st.session_state.evaluations             = []
            st.session_state.current_question_index  = 0
            st.session_state.interview_start_time    = now
            st.session_state.question_start_time     = now
            st.session_state.interview_state         = "in_progress"
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# State: in_progress
# ════════════════════════════════════════════════════════════════════════════════

def _show_in_progress():
    questions  = st.session_state.questions_list
    idx        = st.session_state.current_question_index
    total      = len(questions)

    # Safety guard
    if idx >= total:
        st.session_state.interview_state = "completed"
        st.rerun()
        return

    question   = questions[idx]
    domain     = st.session_state.interview_domain
    difficulty = st.session_state.interview_difficulty
    q_diff     = question.get("difficulty", difficulty)
    topic      = question.get("topic", "")
    d_color    = DIFFICULTY_COLORS.get(q_diff, "#6c757d")

    # ── Progress bar ──────────────────────────────────────────────────────────
    pct = idx / total
    st.progress(pct, text=f"Question {idx + 1} of {total}  ·  {int(pct * 100)}% complete")

    # ── Header row ────────────────────────────────────────────────────────────
    h_col1, h_col2, h_col3 = st.columns([5, 2, 2])
    with h_col1:
        st.markdown(
            f"<span style='font-size:1.05rem;font-weight:700;color:#1e3a8a;'>"
            f"{DOMAIN_ICONS.get(domain,'')}  {domain}</span>",
            unsafe_allow_html=True,
        )
    with h_col2:
        st.markdown(
            f"<span style='background:{d_color};color:white;padding:4px 12px;"
            f"border-radius:14px;font-size:0.82rem;font-weight:700;'>{q_diff}</span>",
            unsafe_allow_html=True,
        )
    with h_col3:
        elapsed = int(time.time() - (st.session_state.question_start_time or time.time()))
        mins, secs = divmod(elapsed, 60)
        st.markdown(
            f"<div style='text-align:right;color:#64748b;font-size:0.9rem;'>⏱️ "
            f"<b>{mins:02d}:{secs:02d}</b></div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Question card ─────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="
            background:#eff6ff; border-left:5px solid #1e3a8a;
            border-radius:0 12px 12px 0; padding:1.4rem 1.6rem; margin-bottom:0.9rem;">
            <div style="color:#64748b;font-size:0.76rem;font-weight:700;
                 text-transform:uppercase;letter-spacing:1.2px;">
                Question {idx + 1}
            </div>
            <div style="font-size:1.15rem;font-weight:600;color:#0f172a;
                 margin-top:0.5rem;line-height:1.65;">
                {question['question']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Topic tag
    if topic:
        st.markdown(
            f"<span style='background:#f1f5f9;color:#475569;padding:3px 10px;"
            f"border-radius:12px;font-size:0.8rem;font-weight:500;'>🏷️  {topic}</span>",
            unsafe_allow_html=True,
        )
        st.markdown("")

    # ── Answer input ──────────────────────────────────────────────────────────
    answer_key = f"_qa_{idx}"
    answer = st.text_area(
        "Your Answer",
        key=answer_key,
        height=200,
        placeholder=(
            "Type your answer here… Be thorough and specific. "
            "Use real-world examples where possible."
        ),
    )

    word_count = len(answer.split()) if answer.strip() else 0
    col_wc, _ = st.columns([1, 3])
    with col_wc:
        color = "#059669" if word_count >= 50 else "#f59e0b" if word_count >= 20 else "#94a3b8"
        st.markdown(
            f"<span style='font-size:0.82rem;color:{color};'>💬  {word_count} word{'s' if word_count!=1 else ''}</span>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Action buttons ────────────────────────────────────────────────────────
    skip_col, submit_col = st.columns([1, 1])
    with skip_col:
        if st.button("⏭️  Skip Question", use_container_width=True, key=f"_skip_{idx}"):
            _submit_answer(idx, "Skipped — No answer provided.")
    with submit_col:
        if st.button(
            "Submit Answer  →",
            type="primary",
            use_container_width=True,
            key=f"_submit_{idx}",
        ):
            if not answer.strip():
                st.error("Please write an answer before submitting, or use **Skip Question**.")
            else:
                _submit_answer(idx, answer.strip())


def _submit_answer(idx: int, answer: str):
    """Record the answer, compute time taken, transition to evaluating."""
    taken = max(0, int(time.time() - (st.session_state.question_start_time or time.time())))

    answers = st.session_state.answers_given
    while len(answers) <= idx:
        answers.append("")
    answers[idx] = answer

    timings = st.session_state.time_taken_list
    while len(timings) <= idx:
        timings.append(0)
    timings[idx] = taken

    st.session_state.answers_given    = answers
    st.session_state.time_taken_list  = timings
    st.session_state.interview_state  = "evaluating"
    st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# State: evaluating
# ════════════════════════════════════════════════════════════════════════════════

def _show_evaluating():
    idx         = st.session_state.current_question_index
    questions   = st.session_state.questions_list
    evaluations = st.session_state.evaluations
    domain      = st.session_state.interview_domain
    difficulty  = st.session_state.interview_difficulty
    total       = len(questions)

    # ── Phase 1: run evaluation (shows spinner while blocked) ─────────────────
    if len(evaluations) <= idx:
        answer   = st.session_state.answers_given[idx] if idx < len(st.session_state.answers_given) else ""
        question = questions[idx]

        st.markdown(
            """
            <div style="text-align:center; padding:2rem 0 1rem;">
                <div style="font-size:2.5rem; margin-bottom:0.6rem;">🤖</div>
                <div style="font-size:1.2rem; font-weight:700; color:#1e3a8a;">
                    AI is evaluating your answer…
                </div>
                <div style="color:#64748b; font-size:0.9rem; margin-top:0.4rem;">
                    Analysing against domain rubric and expected keywords
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.spinner("Running evaluation — this may take a few seconds…"):
            result = evaluate_answer(
                question=question["question"],
                answer=answer,
                domain=domain,
                difficulty=question.get("difficulty", difficulty),
                expected_keywords=question.get("expected_keywords", []),
            )

        st.session_state.evaluations.append(result)
        st.rerun()
        return

    # ── Phase 2: show result card ─────────────────────────────────────────────
    result   = evaluations[idx]
    question = questions[idx]
    answer   = st.session_state.answers_given[idx] if idx < len(st.session_state.answers_given) else ""
    is_last  = idx == total - 1

    _show_result_card(result, question, answer, idx, total, is_last)


def _show_result_card(
    result: dict, question: dict, answer: str,
    idx: int, total: int, is_last: bool,
):
    score      = float(result.get("weighted_score") or result.get("score") or 0)
    grade      = result.get("grade", "Average")
    strengths  = result.get("strengths", "")
    imps       = result.get("improvements", "") or result.get("ai_feedback", "")
    hint       = result.get("ideal_answer_hint", "") or result.get("model_answer", "")
    follow_up  = result.get("follow_up_question", "")
    kw_cov     = int(result.get("keyword_coverage", 0))
    fallback   = result.get("_fallback", False)

    sc         = _score_color(score)
    gc         = _GRADE_COLORS.get(grade, "#6c757d")
    domain     = st.session_state.interview_domain

    # ── Progress tracker ──────────────────────────────────────────────────────
    eval_done = len(st.session_state.evaluations)
    st.progress(eval_done / total, text=f"Question {eval_done} of {total} evaluated")

    if fallback:
        st.warning(
            "⚠️ Gemini API was unavailable — this result uses mock evaluation.",
            icon=None,
        )

    # ── Score hero banner ─────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="
            background:linear-gradient(135deg, {sc}18 0%, {sc}08 100%);
            border:2px solid {sc}40; border-radius:16px;
            padding:1.6rem 2rem; margin-bottom:1.2rem;
            display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:1rem;">

            <div>
                <div style="font-size:0.8rem;font-weight:700;color:#64748b;
                     text-transform:uppercase;letter-spacing:1px;margin-bottom:0.3rem;">
                    Question {idx + 1} Result · {DOMAIN_ICONS.get(domain,'')} {domain}
                </div>
                <div style="font-size:0.9rem;color:#334155;max-width:460px;font-style:italic;">
                    {question['question'][:120]}{'…' if len(question['question'])>120 else ''}
                </div>
            </div>

            <div style="text-align:center;">
                <div style="font-size:3.8rem;font-weight:900;line-height:1;color:{sc};">
                    {score:.1f}
                    <span style="font-size:1.4rem;color:#94a3b8;">/10</span>
                </div>
                <div style="margin-top:0.4rem;">
                    <span style="background:{gc};color:white;padding:4px 16px;
                          border-radius:20px;font-size:0.88rem;font-weight:700;">
                        {grade}
                    </span>
                </div>
                <div style="font-size:0.78rem;color:#64748b;margin-top:0.4rem;">
                    Keyword coverage: {kw_cov}%
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Your answer (collapsed) ───────────────────────────────────────────────
    with st.expander("📝 Your Answer", expanded=False):
        if answer in ("Skipped — No answer provided.", "[Skipped]"):
            st.warning("This question was skipped.")
        else:
            st.text_area("", value=answer, height=120, disabled=True, key=f"_ra_{idx}")

    # ── Strengths ─────────────────────────────────────────────────────────────
    if strengths:
        st.markdown(
            f"""
            <div style="border-left:4px solid #059669;background:#f0fdf4;
                 border-radius:0 10px 10px 0;padding:1rem 1.2rem;margin-bottom:0.7rem;">
                <div style="font-weight:700;color:#059669;font-size:0.9rem;margin-bottom:0.4rem;">
                    ✅  Strengths
                </div>
                <div style="color:#1e293b;font-size:0.92rem;line-height:1.6;">
                    {strengths}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Improvements ─────────────────────────────────────────────────────────
    if imps:
        st.markdown(
            f"""
            <div style="border-left:4px solid #f59e0b;background:#fffbeb;
                 border-radius:0 10px 10px 0;padding:1rem 1.2rem;margin-bottom:0.7rem;">
                <div style="font-weight:700;color:#b45309;font-size:0.9rem;margin-bottom:0.4rem;">
                    ⚠️  Areas for Improvement
                </div>
                <div style="color:#1e293b;font-size:0.92rem;line-height:1.6;">
                    {imps}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Ideal answer hint (expandable) ────────────────────────────────────────
    if hint:
        with st.expander("💡 Ideal Answer Hint", expanded=False):
            st.markdown(
                f"""
                <div style="background:#f0f9ff;border:1px solid #bae6fd;
                     border-radius:8px;padding:1rem;font-size:0.9rem;
                     color:#0c4a6e;line-height:1.7;">
                    {hint}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Follow-up teaser ──────────────────────────────────────────────────────
    if follow_up:
        st.markdown(
            f"""
            <div style="margin-top:0.6rem;padding:0.8rem 1rem;
                 background:#fafafa;border-radius:8px;border:1px solid #e2e8f0;">
                <span style="color:#94a3b8;font-size:0.8rem;font-weight:600;
                      text-transform:uppercase;letter-spacing:0.8px;">
                    Follow-up question
                </span><br>
                <span style="color:#475569;font-style:italic;font-size:0.9rem;">
                    "{follow_up}"
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Navigation button ─────────────────────────────────────────────────────
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        if is_last:
            if st.button(
                "🏁  View Final Results  →",
                type="primary",
                use_container_width=True,
                key="_finish_btn",
            ):
                st.session_state.interview_state = "completed"
                st.rerun()
        else:
            remaining = total - idx - 1
            if st.button(
                f"Next Question  →   ({remaining} remaining)",
                type="primary",
                use_container_width=True,
                key=f"_next_{idx}",
            ):
                st.session_state.current_question_index = idx + 1
                st.session_state.question_start_time    = time.time()
                st.session_state.interview_state        = "in_progress"
                st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# State: completed — save and redirect
# ════════════════════════════════════════════════════════════════════════════════

def _finish_interview():
    # Guard: if already saved this session, go straight to results
    if st.session_state.get("interview_id"):
        st.session_state.viewing_interview_id = st.session_state.interview_id
        st.session_state.current_page = "results"
        _reset()
        st.rerun()
        return

    questions  = st.session_state.questions_list
    answers    = st.session_state.answers_given
    timings    = st.session_state.time_taken_list
    evaluations = st.session_state.evaluations
    domain     = st.session_state.interview_domain or ""
    difficulty = st.session_state.interview_difficulty or ""

    start_ts = st.session_state.get("interview_start_time") or time.time()
    start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
    end_dt   = datetime.now(timezone.utc)

    # Build payload
    questions_data = []
    scores_data    = []

    for i, q in enumerate(questions):
        ans  = answers[i]  if i < len(answers)    else ""
        ev   = evaluations[i] if i < len(evaluations) else {}
        secs = timings[i]  if i < len(timings)    else 0

        questions_data.append({
            "question_number":  q.get("question_number", i + 1),
            "question_text":    q["question"],
            "difficulty":       q.get("difficulty", difficulty),
            "topic":            q.get("topic", "General"),
            "candidate_answer": ans,
            "ideal_answer_hint": ev.get("ideal_answer_hint") or ev.get("model_answer", ""),
            "time_taken_seconds": secs,
        })
        scores_data.append({
            "score":        max(1, min(10, round(float(ev.get("weighted_score") or ev.get("score") or 1)))),
            "grade":        ev.get("grade", "Poor"),
            "strengths":    ev.get("strengths", ""),
            "improvements": ev.get("improvements") or ev.get("ai_feedback", ""),
        })

    # Show brief saving screen
    st.markdown(
        """
        <div style="text-align:center; padding:3rem 1rem;">
            <div style="font-size:2.5rem; margin-bottom:0.8rem;">💾</div>
            <div style="font-size:1.2rem; font-weight:700; color:#1e3a8a;">
                Saving your results…
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.spinner("Saving interview to database…"):
        interview_id = save_interview(
            candidate_id=st.session_state.get("user_id"),
            domain=domain,
            difficulty=difficulty,
            questions_data=questions_data,
            scores=scores_data,
            start_time=start_dt,
            end_time=end_dt,
        )

    st.session_state.interview_id          = interview_id
    st.session_state.viewing_interview_id  = interview_id
    st.session_state.current_page          = "results"
    _reset()
    st.rerun()
