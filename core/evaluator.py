"""
AI evaluation engine for AI Interview Evaluator.

Provides domain-specific rubric-based scoring via Google Gemini.
Automatically falls back to mock_evaluate on any API failure so the
app never crashes due to an unavailable model or missing key.
"""

import json
import logging
import os
import random
import time
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types

from config import GEMINI_MODEL

# ── Module-level setup ────────────────────────────────────────────────────────

load_dotenv()

log = logging.getLogger(__name__)

_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
_client: Optional[genai.Client] = (
    genai.Client(api_key=_API_KEY) if _API_KEY else None
)

if not _API_KEY:
    log.warning(
        "GEMINI_API_KEY is not set. All evaluations will use mock mode."
    )


# ── Domain-specific evaluation rubrics ───────────────────────────────────────
# Weights per domain must sum to 100.

RUBRICS: dict[str, dict[str, int]] = {
    "Software Engineering": {
        "technical_accuracy": 35,
        "depth_of_knowledge": 25,
        "practical_application": 20,
        "clarity_of_explanation": 20,
    },
    "HR / Behavioral": {
        "situation_action_result": 30,
        "self_awareness": 25,
        "communication_clarity": 25,
        "relevance_to_question": 20,
    },
    "System Design": {
        "scalability_thinking": 30,
        "component_identification": 25,
        "trade_off_analysis": 25,
        "clarity_and_structure": 20,
    },
    "Data Science & ML": {
        "conceptual_correctness": 35,
        "practical_knowledge": 25,
        "mathematical_understanding": 20,
        "real_world_application": 20,
    },
    "Product Management": {
        "structured_thinking": 30,
        "customer_empathy": 25,
        "data_driven_approach": 25,
        "business_awareness": 20,
    },
}

# Fallback rubric when the domain is not in RUBRICS.
_DEFAULT_RUBRIC = {
    "accuracy": 40,
    "depth": 30,
    "clarity": 30,
}

# ── Grade / verdict helpers ───────────────────────────────────────────────────


def _letter_grade(percentage: float) -> str:
    if percentage >= 90: return "A+"
    if percentage >= 80: return "A"
    if percentage >= 72: return "B+"
    if percentage >= 64: return "B"
    if percentage >= 56: return "C+"
    if percentage >= 48: return "C"
    if percentage >= 35: return "D"
    return "F"


def _word_grade(score: float) -> str:
    """Map a 1-10 score to a word grade label."""
    if score >= 9: return "Excellent"
    if score >= 7: return "Good"
    if score >= 5: return "Average"
    if score >= 3: return "Poor"
    return "Poor"


def _verdict_text(percentage: float) -> str:
    if percentage >= 85:
        return "Outstanding — demonstrates expert-level mastery. Highly recommended."
    if percentage >= 70:
        return "Strong — solid competency demonstrated; ready for most roles in this domain."
    if percentage >= 55:
        return "Satisfactory — core concepts understood; targeted preparation will close remaining gaps."
    if percentage >= 40:
        return "Below expectations — significant gaps identified; focused study required."
    return "Insufficient — fundamental concepts need review before re-attempting."


def _is_mock_mode() -> bool:
    return os.getenv("USE_MOCK", "false").lower() in ("true", "1", "yes")


# ── Mock evaluator ────────────────────────────────────────────────────────────

def mock_evaluate(
    question: str,
    answer: str,
    domain: str,
    difficulty: str,
    expected_keywords: list[str],
) -> dict:
    """
    Return realistic dummy evaluation data without calling Gemini.
    Used when USE_MOCK=true or as fallback on API failure.
    """
    rubric = RUBRICS.get(domain, _DEFAULT_RUBRIC)

    # Score heuristic: answer length + keyword coverage + noise
    base = _mock_base_score(answer, difficulty, expected_keywords)

    # Per-criterion scores with controlled variance
    criteria_scores: dict[str, int] = {}
    for criterion in rubric:
        raw = base + random.uniform(-1.5, 1.5)
        criteria_scores[criterion] = max(1, min(10, round(raw)))

    # Weighted score (authoritative — always computed here)
    weighted_score = sum(
        criteria_scores[c] * w / 100
        for c, w in rubric.items()
    )
    # In mock mode clamp to 4–9 for real answers so demo looks realistic
    stripped_ans = (answer or "").strip().lower()
    is_skipped = not stripped_ans or stripped_ans in (
        "skipped — no answer provided.", "[skipped]", "i don't know", "n/a", "-",
    )
    if not is_skipped:
        weighted_score = max(4.0, min(9.0, weighted_score))
    weighted_score = round(weighted_score, 2)
    final_score = max(1, min(10, round(weighted_score)))
    grade = _word_grade(weighted_score)

    # Keyword coverage
    answer_lower = (answer or "").lower()
    covered = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    keyword_coverage = (
        round(covered / len(expected_keywords) * 100) if expected_keywords else 50
    )

    strengths = (
        f"[MOCK] The response demonstrates familiarity with {domain} concepts "
        f"at the {difficulty} level and addresses the core question. "
        f"The answer shows practical awareness of the subject area."
    )
    improvements = (
        f"[MOCK] The answer could be strengthened by including concrete examples "
        f"and discussing edge cases or trade-offs. "
        f"For a {difficulty} question, deeper technical insight is expected."
    )
    ideal_answer_hint = (
        f"[MOCK] An ideal {difficulty} {domain} answer would: "
        f"(1) clearly define the core concept, "
        f"(2) enumerate key components with real-world examples, "
        f"(3) discuss trade-offs and constraints, "
        f"and (4) tie the answer to practical scenarios."
    )
    follow_up_question = (
        f"[MOCK] Can you describe a real-world scenario where you applied "
        f"this concept and what challenges you faced?"
    )

    return _build_result(
        criteria_scores=criteria_scores,
        weighted_score=weighted_score,
        final_score=final_score,
        grade=grade,
        strengths=strengths,
        improvements=improvements,
        ideal_answer_hint=ideal_answer_hint,
        follow_up_question=follow_up_question,
        keyword_coverage=keyword_coverage,
    )


def _mock_base_score(
    answer: str, difficulty: str, expected_keywords: list[str]
) -> float:
    """Heuristic base score for mock mode. Always returns 4–9 for real answers."""
    stripped = (answer or "").strip().lower()

    if not stripped or stripped in ("i don't know", "[skipped]", "n/a", "-",
                                    "skipped — no answer provided."):
        return 2.0

    words = stripped.split()
    if len(words) < 10:
        base = 4.5
    elif len(words) < 30:
        base = 5.5
    elif len(words) < 80:
        base = 7.0
    else:
        base = 8.0

    # Keyword bonus (up to +1 point)
    if expected_keywords:
        covered = sum(1 for kw in expected_keywords if kw.lower() in stripped)
        base += (covered / len(expected_keywords)) * 1.0

    # Difficulty adjustment
    if difficulty == "Hard":
        base -= 0.5
    elif difficulty == "Easy":
        base += 0.3

    return max(4.0, min(9.5, base))


# ── Prompt construction ───────────────────────────────────────────────────────

def _build_evaluation_prompt(
    question: str,
    answer: str,
    domain: str,
    difficulty: str,
    expected_keywords: list[str],
) -> str:
    rubric = RUBRICS.get(domain, _DEFAULT_RUBRIC)

    # Human-readable rubric block
    rubric_lines = "\n".join(
        f"  - {criterion.replace('_', ' ').title()}: {weight}% weight"
        for criterion, weight in rubric.items()
    )

    # Criteria names for the JSON template in the prompt
    criteria_json_lines = "\n".join(
        f'    "{criterion}": <int 1-10>'
        for criterion in rubric
    )

    keywords_str = ", ".join(expected_keywords) if expected_keywords else "None specified"

    return f"""You are a senior {domain} interviewer with 15+ years of experience at top tech companies.

EVALUATION CONTEXT:
- Domain: {domain}
- Question Difficulty: {difficulty}
- Question: {question}
- Candidate's Answer: {answer}
- Expected Key Concepts: {keywords_str}

EVALUATION RUBRIC for {domain}:
{rubric_lines}

Evaluate this answer strictly and professionally. Consider the difficulty level.
For an Easy question, basic understanding is sufficient for a high score.
For Hard questions, expect deep technical insight.

If the answer is blank or "I don't know", give a score of 1 with appropriate feedback.

Respond ONLY in this exact JSON format with no other text:
{{
  "criteria_scores": {{
{criteria_json_lines}
  }},
  "weighted_score": <float 1-10, calculated from criteria and weights>,
  "final_score": <int 1-10, rounded from weighted_score>,
  "grade": <"Excellent" | "Good" | "Average" | "Poor">,
  "strengths": "<2 sentences about what was good in the answer>",
  "improvements": "<2 sentences about what was missing or weak>",
  "ideal_answer_hint": "<3-4 lines giving the key points of an ideal answer>",
  "follow_up_question": "<a natural follow-up question based on their answer>",
  "keyword_coverage": <int 0-100, percentage of expected keywords covered>
}}"""


def _build_summary_prompt(all_qa_data: list[dict], domain: str) -> str:
    qa_lines = []
    for i, item in enumerate(all_qa_data, 1):
        qa_lines.append(
            f"Q{i} [{item.get('topic', 'General')}] ({item.get('difficulty', '')}): "
            f"{item.get('question', '')}\n"
            f"  Score: {item.get('score', 'N/A')}/10 | Grade: {item.get('grade', '')}\n"
            f"  Strengths: {item.get('strengths', '')}\n"
            f"  Gaps:      {item.get('improvements', '')}"
        )
    qa_summary = "\n\n".join(qa_lines)

    return f"""You are a senior {domain} interviewer. A candidate just completed a {domain} interview.

Here is a summary of each question and their performance:

{qa_summary}

Write a 3-paragraph professional interview debrief:
Paragraph 1: Overall assessment — what consistent strengths emerged across the interview.
Paragraph 2: Main areas for improvement — specific knowledge gaps or skills that need work.
Paragraph 3: Actionable recommendations — concrete next steps the candidate should take.

Keep each paragraph to 3-4 sentences. Be specific, constructive, and professional.
Respond with only the 3 paragraphs, separated by blank lines. No headings, no bullet points."""


# ── Response parsing ──────────────────────────────────────────────────────────

def _strip_markdown(text: str) -> str:
    """Remove optional ```json ... ``` fences Gemini sometimes adds."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop opening fence line
        lines = lines[1:] if lines[0].startswith("```") else lines
        # Drop closing fence line
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _parse_and_validate(
    raw: str, domain: str
) -> dict:
    """Parse Gemini's JSON response, validate, and recalculate weighted_score."""
    data = json.loads(_strip_markdown(raw))
    rubric = RUBRICS.get(domain, _DEFAULT_RUBRIC)

    # Validate/clamp criteria_scores
    criteria_scores: dict[str, int] = {}
    raw_criteria = data.get("criteria_scores", {})
    for criterion in rubric:
        val = raw_criteria.get(criterion, 5)
        criteria_scores[criterion] = max(1, min(10, int(round(float(val)))))

    # Always recompute weighted_score from our rubric — don't trust Gemini's calc
    weighted_score = sum(
        criteria_scores[c] * w / 100
        for c, w in rubric.items()
    )
    weighted_score = round(weighted_score, 2)
    final_score = max(1, min(10, round(weighted_score)))

    grade = data.get("grade", _word_grade(weighted_score))
    if grade not in ("Excellent", "Good", "Average", "Poor"):
        grade = _word_grade(weighted_score)

    keyword_coverage = max(0, min(100, int(data.get("keyword_coverage", 0))))

    return _build_result(
        criteria_scores=criteria_scores,
        weighted_score=weighted_score,
        final_score=final_score,
        grade=grade,
        strengths=str(data.get("strengths", "")).strip(),
        improvements=str(data.get("improvements", "")).strip(),
        ideal_answer_hint=str(data.get("ideal_answer_hint", "")).strip(),
        follow_up_question=str(data.get("follow_up_question", "")).strip(),
        keyword_coverage=keyword_coverage,
    )


def _build_result(
    *,
    criteria_scores: dict,
    weighted_score: float,
    final_score: int,
    grade: str,
    strengths: str,
    improvements: str,
    ideal_answer_hint: str,
    follow_up_question: str,
    keyword_coverage: int,
) -> dict:
    """Assemble the canonical result dict, including backward-compat keys."""
    return {
        # ── New fields ────────────────────────────────────────────────────
        "criteria_scores": criteria_scores,
        "weighted_score": weighted_score,
        "final_score": final_score,
        "grade": grade,
        "strengths": strengths,
        "improvements": improvements,
        "ideal_answer_hint": ideal_answer_hint,
        "follow_up_question": follow_up_question,
        "keyword_coverage": keyword_coverage,
        # ── Backward-compat aliases ───────────────────────────────────────
        "score": float(weighted_score),
        "feedback": improvements,
        "model_answer": ideal_answer_hint,
        "ai_score": float(weighted_score),
        "ai_feedback": improvements,
    }


# ── Gemini call helper ────────────────────────────────────────────────────────

def _call_gemini(prompt: str, max_tokens: int = 1024) -> str:
    """
    Call the Gemini API and return the raw text response.
    Raises on failure — caller handles retry / fallback.
    """
    if _client is None:
        raise RuntimeError("Gemini client is not initialised (missing API key).")

    response = _client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=max_tokens,
            # Disable "thinking" so the full token budget goes to the actual
            # response. Gemini 2.5 models otherwise spend tokens on internal
            # reasoning, which can truncate the JSON output mid-string.
            thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
        ),
    )
    return response.text


# ═════════════════════════════════════════════════════════════════════════════
# Primary public function
# ═════════════════════════════════════════════════════════════════════════════

def evaluate_answer(
    question: str,
    answer: str,
    domain: str,
    difficulty: str,
    expected_keywords: Optional[list[str]] = None,
) -> dict:
    """
    Evaluate a single interview answer using Gemini with domain-specific rubrics.

    Args:
        question:          The interview question text.
        answer:            The candidate's answer.
        domain:            One of the five supported domains.
        difficulty:        "Easy", "Medium", or "Hard".
        expected_keywords: Optional list of keywords the ideal answer should cover.

    Returns:
        A dict with both the new rich fields (criteria_scores, grade, strengths, …)
        and backward-compatible aliases (score, feedback, model_answer).
        Always returns a valid dict — never raises.
    """
    expected_keywords = expected_keywords or []

    # ── Mock / offline mode ───────────────────────────────────────────────
    if _is_mock_mode():
        time.sleep(0.25)
        return mock_evaluate(question, answer, domain, difficulty, expected_keywords)

    # ── Blank / skip detection ────────────────────────────────────────────
    stripped = (answer or "").strip()
    if not stripped or stripped.lower() in ("i don't know", "[skipped]", "-", "n/a"):
        rubric = RUBRICS.get(domain, _DEFAULT_RUBRIC)
        return _build_result(
            criteria_scores={c: 1 for c in rubric},
            weighted_score=1.0,
            final_score=1,
            grade="Poor",
            strengths="No answer was provided.",
            improvements=(
                "The question was skipped. Attempt every question to receive "
                "meaningful feedback and a representative score."
            ),
            ideal_answer_hint="Please review the topic and attempt the question.",
            follow_up_question="What concepts in this area are you least confident about?",
            keyword_coverage=0,
        )

    # ── Live Gemini evaluation with retry ─────────────────────────────────
    prompt = _build_evaluation_prompt(
        question=question,
        answer=stripped,
        domain=domain,
        difficulty=difficulty,
        expected_keywords=expected_keywords,
    )

    last_exc: Exception = RuntimeError("Unknown error")
    for attempt in range(3):
        try:
            raw = _call_gemini(prompt, max_tokens=1024)
            result = _parse_and_validate(raw, domain)
            log.debug(
                "evaluate_answer: domain=%s difficulty=%s "
                "weighted=%.2f grade=%s keywords=%d%%",
                domain, difficulty,
                result["weighted_score"], result["grade"],
                result["keyword_coverage"],
            )
            return result

        except json.JSONDecodeError as exc:
            last_exc = exc
            log.warning(
                "evaluate_answer: JSON parse error on attempt %d: %s",
                attempt + 1, exc,
            )
            time.sleep(1)

        except Exception as exc:
            last_exc = exc
            log.warning(
                "evaluate_answer: Gemini call failed on attempt %d: %s",
                attempt + 1, exc,
            )
            time.sleep(2 ** attempt)   # exponential back-off: 1s, 2s, 4s

    # ── Fallback to mock on total failure ─────────────────────────────────
    log.error(
        "evaluate_answer: all 3 Gemini attempts failed (%s). "
        "Falling back to mock_evaluate.",
        last_exc,
    )
    result = mock_evaluate(question, answer, domain, difficulty, expected_keywords)
    # Mark fallback results so the UI can flag them
    result["_fallback"] = True
    return result


# ═════════════════════════════════════════════════════════════════════════════
# calculate_final_result
# ═════════════════════════════════════════════════════════════════════════════

def calculate_final_result(scores_list: list[dict]) -> dict:
    """
    Aggregate per-question evaluation results into an overall interview score.

    Args:
        scores_list: List of dicts returned by evaluate_answer, each optionally
                     augmented with "topic" and "difficulty" keys for analysis.

    Returns::
        {
            "overall_score":  float,  # mean weighted score (1-10)
            "percentage":     float,  # overall_score × 10 (0-100)
            "letter_grade":   str,    # A+/A/B+/B/C+/C/D/F
            "verdict":        str,    # one-sentence narrative
            "topic_analysis": {       # per-topic breakdown
                "<topic>": {
                    "count":      int,
                    "avg_score":  float,
                    "avg_pct":    float,
                    "letter":     str,
                }
            }
        }
    """
    if not scores_list:
        return {
            "overall_score": 0.0,
            "percentage": 0.0,
            "letter_grade": "F",
            "verdict": "No questions were attempted.",
            "topic_analysis": {},
        }

    # Prefer weighted_score; fall back to final_score or score
    def _ws(s: dict) -> float:
        return float(
            s.get("weighted_score")
            or s.get("final_score")
            or s.get("score")
            or s.get("ai_score")
            or 0
        )

    n = len(scores_list)
    total = sum(_ws(s) for s in scores_list)
    overall_score = round(total / n, 2)
    percentage = round(overall_score * 10, 1)
    letter_grade = _letter_grade(percentage)
    verdict = _verdict_text(percentage)

    # ── Topic breakdown ───────────────────────────────────────────────────
    topic_buckets: dict[str, list[float]] = {}
    for s in scores_list:
        topic = (s.get("topic") or "General").strip()
        topic_buckets.setdefault(topic, []).append(_ws(s))

    topic_analysis: dict[str, dict] = {}
    for topic, bucket in topic_buckets.items():
        avg = round(sum(bucket) / len(bucket), 2)
        avg_pct = round(avg * 10, 1)
        topic_analysis[topic] = {
            "count": len(bucket),
            "avg_score": avg,
            "avg_pct": avg_pct,
            "letter": _letter_grade(avg_pct),
        }

    return {
        "overall_score": overall_score,
        "percentage": percentage,
        "letter_grade": letter_grade,
        "verdict": verdict,
        "topic_analysis": topic_analysis,
    }


# ═════════════════════════════════════════════════════════════════════════════
# get_interview_summary_feedback
# ═════════════════════════════════════════════════════════════════════════════

def get_interview_summary_feedback(
    all_qa_data: list[dict],
    domain: str,
) -> str:
    """
    Generate a 3-paragraph holistic performance summary via a single Gemini call.

    Args:
        all_qa_data: List of dicts, each with:
            question, answer, score, grade, strengths, improvements, topic, difficulty
        domain: Domain name for context.

    Returns:
        A string with three paragraphs (blank-line separated).
        Falls back to a structured template if Gemini is unavailable.
    """
    if not all_qa_data:
        return "No interview data available to summarise."

    if _is_mock_mode() or _client is None:
        return _mock_summary(all_qa_data, domain)

    prompt = _build_summary_prompt(all_qa_data, domain)

    for attempt in range(2):
        try:
            summary = _call_gemini(prompt, max_tokens=600)
            return summary.strip()
        except Exception as exc:
            log.warning(
                "get_interview_summary_feedback: attempt %d failed: %s",
                attempt + 1, exc,
            )
            time.sleep(2)

    log.error("get_interview_summary_feedback: Gemini unavailable; using template.")
    return _mock_summary(all_qa_data, domain)


def _mock_summary(all_qa_data: list[dict], domain: str) -> str:
    """Structured template fallback for the summary feedback."""
    n = len(all_qa_data)
    scores = [
        float(
            d.get("weighted_score")
            or d.get("score")
            or d.get("ai_score")
            or 0
        )
        for d in all_qa_data
    ]
    avg = round(sum(scores) / n, 1) if n else 0
    pct = round(avg * 10, 1)
    grade = _letter_grade(pct)

    strong = [d for d in all_qa_data if (d.get("weighted_score") or d.get("score") or 0) >= 7]
    weak = [d for d in all_qa_data if (d.get("weighted_score") or d.get("score") or 0) < 5]
    strong_topics = ", ".join({d.get("topic", "General") for d in strong}) or "several areas"
    weak_topics = ", ".join({d.get("topic", "General") for d in weak}) or "some areas"

    p1 = (
        f"The candidate completed a {n}-question {domain} interview and achieved "
        f"an overall score of {avg:.1f}/10 ({pct}%, letter grade {grade}). "
        f"They demonstrated relative strength in {strong_topics}, "
        f"showing a solid grasp of core concepts in those areas."
    )
    p2 = (
        f"The main areas requiring attention were {weak_topics}, "
        f"where answers lacked the depth and specificity expected at this difficulty level. "
        f"More concrete examples, trade-off discussions, and edge-case awareness would "
        f"significantly strengthen performance in these topics."
    )
    p3 = (
        f"To improve, the candidate should focus structured study sessions on {weak_topics}, "
        f"practice articulating answers using the STAR or component-breakdown frameworks, "
        f"and review real-world case studies relevant to {domain}. "
        f"Re-attempting this interview after targeted preparation is strongly recommended."
    )
    return f"{p1}\n\n{p2}\n\n{p3}"


# ═════════════════════════════════════════════════════════════════════════════
# Backward-compatible batch helper
# ═════════════════════════════════════════════════════════════════════════════

def batch_evaluate(
    questions: list[dict],
    answers: list[str],
    domain: str,
    difficulty: str,
) -> list[dict]:
    """
    Evaluate a list of questions/answers and return per-question result dicts
    compatible with both the old DB response format and the new rich format.
    """
    results = []
    for q, a in zip(questions, answers):
        result = evaluate_answer(
            question=q.get("question", ""),
            answer=a,
            domain=domain,
            difficulty=difficulty,
            expected_keywords=q.get("expected_keywords", []),
        )
        results.append({
            # Legacy keys
            "question_number": q.get("question_number", 0),
            "question_text": q.get("question", ""),
            "user_answer": a,
            "candidate_answer": a,
            "ai_score": result["weighted_score"],
            "ai_feedback": result["improvements"],
            "model_answer": result["ideal_answer_hint"],
            # New rich keys
            "topic": q.get("topic", "General"),
            "difficulty": q.get("difficulty", difficulty),
            **{k: v for k, v in result.items()
               if k not in ("score", "feedback", "model_answer",
                            "ai_score", "ai_feedback")},
        })
    return results
