"""
Database handler for AI Interview Evaluator.

Canonical functions (new schema):
    init_db, register_candidate, login_candidate, save_interview,
    get_candidate_interviews, get_interview_details, get_all_candidates,
    get_leaderboard, get_domain_statistics, get_candidate_performance_trend

Backward-compatible aliases (keep the existing UI working):
    create_tables, register_user, login_user, get_user_interviews,
    get_interview_by_id, get_all_users, get_global_stats,
    get_domain_distribution, delete_user
"""

import hashlib
import secrets
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker

from config import DB_PATH
from .models import Base, Candidate, Interview, InterviewQuestion

log = logging.getLogger(__name__)

_engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)
_SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


# ── Session context manager ───────────────────────────────────────────────────

@contextmanager
def _session():
    db = _SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Password helpers ──────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """Returns 'salt:sha256hex' string."""
    salt = secrets.token_hex(16)
    digest = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{digest}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split(":", 1)
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == digest
    except (ValueError, AttributeError):
        return False


# ── Grade helpers ─────────────────────────────────────────────────────────────

def _letter_grade(pct: float) -> str:
    if pct >= 90: return "A+"
    if pct >= 80: return "A"
    if pct >= 72: return "B+"
    if pct >= 64: return "B"
    if pct >= 56: return "C+"
    if pct >= 48: return "C"
    if pct >= 35: return "D"
    return "F"


def _question_grade(score: int) -> str:
    if score >= 9: return "Excellent"
    if score >= 7: return "Good"
    if score >= 5: return "Average"
    if score >= 3: return "Below Average"
    return "Poor"


def _verdict(pct: float, domain: str) -> str:
    if pct >= 85:
        return (
            f"Outstanding performance in {domain}. "
            "Demonstrates expert-level mastery — highly recommended."
        )
    if pct >= 70:
        return (
            f"Strong performance in {domain}. "
            "Solid competency demonstrated; ready for most roles in this domain."
        )
    if pct >= 55:
        return (
            f"Satisfactory performance in {domain}. "
            "Core concepts understood; targeted preparation will bridge remaining gaps."
        )
    if pct >= 40:
        return (
            f"Below expectations in {domain}. "
            "Significant gaps identified — focused study required before re-attempting."
        )
    return (
        f"Insufficient performance in {domain}. "
        "Fundamental concepts need review; consider structured preparation."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 1. init_db
# ═══════════════════════════════════════════════════════════════════════════════

def init_db() -> None:
    """
    Create all tables (if they don't exist) and seed default accounts.
    Safe to call multiple times — idempotent.
    """
    Base.metadata.create_all(bind=_engine)
    _seed_admin()
    _seed_demo_user()


def _seed_admin() -> None:
    """Create admin@ai.com / admin123 if it doesn't exist yet."""
    try:
        with _session() as db:
            exists = db.query(Candidate).filter_by(email="admin@ai.com").first()
            if not exists:
                db.add(Candidate(
                    name="Administrator",
                    email="admin@ai.com",
                    password_hash=_hash_password("admin123"),
                    is_admin=True,
                ))
    except Exception as exc:
        log.warning("Admin seed skipped: %s", exc)


def _seed_demo_user() -> None:
    """Create demo@test.com / demo123 if it doesn't exist yet."""
    try:
        with _session() as db:
            exists = db.query(Candidate).filter_by(email="demo@test.com").first()
            if not exists:
                db.add(Candidate(
                    name="Demo User",
                    email="demo@test.com",
                    password_hash=_hash_password("demo123"),
                    is_admin=False,
                ))
    except Exception as exc:
        log.warning("Demo user seed skipped: %s", exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. register_candidate
# ═══════════════════════════════════════════════════════════════════════════════

def register_candidate(name: str, email: str, password: str) -> dict:
    """
    Create a new candidate account.

    Returns:
        {"success": True, "id": int, "name": str, "email": str}
        {"success": False, "error": str}
    """
    name = (name or "").strip()
    email = (email or "").strip().lower()
    if not name:
        return {"success": False, "error": "Name is required."}
    if not email or "@" not in email:
        return {"success": False, "error": "A valid email address is required."}
    if not password or len(password) < 6:
        return {"success": False, "error": "Password must be at least 6 characters."}
    try:
        with _session() as db:
            if db.query(Candidate).filter_by(email=email).first():
                return {"success": False, "error": "Email is already registered."}
            candidate = Candidate(
                name=name,
                email=email,
                password_hash=_hash_password(password),
            )
            db.add(candidate)
            db.flush()
            return {
                "success": True,
                "id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
            }
    except Exception as exc:
        log.error("register_candidate failed: %s", exc)
        return {"success": False, "error": "Registration failed. Please try again."}


# ═══════════════════════════════════════════════════════════════════════════════
# 3. login_candidate
# ═══════════════════════════════════════════════════════════════════════════════

def login_candidate(email: str, password: str) -> Optional[dict]:
    """
    Verify credentials and return a candidate dict, or None on failure.

    Returns:
        {
          "id": int, "name": str, "email": str,
          "is_admin": bool, "created_at": datetime
        }
        or None
    """
    email = (email or "").strip().lower()
    try:
        with _session() as db:
            candidate = db.query(Candidate).filter_by(email=email).first()
            if not candidate or not _verify_password(password, candidate.password_hash):
                return None
            return {
                "id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "is_admin": candidate.is_admin,
                "created_at": candidate.created_at,
            }
    except Exception as exc:
        log.error("login_candidate failed: %s", exc)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 4. save_interview
# ═══════════════════════════════════════════════════════════════════════════════

def save_interview(
    candidate_id: int = None,
    domain: str = "",
    difficulty: str = "",
    questions_data: list[dict] = None,
    scores: list[dict] = None,
    start_time: datetime = None,
    end_time: datetime = None,
    *,
    # ── Legacy keyword args (keep old UI working) ──────────────────────────
    user_id: int = None,
    responses: list[dict] = None,
) -> int:
    """
    Persist a completed interview and all per-question results.

    **New-style call:**
        save_interview(
            candidate_id=1, domain="...", difficulty="...",
            questions_data=[{"question_number":1, "question_text":"...",
                             "difficulty":"Easy", "topic":"OOP",
                             "candidate_answer":"...", "ideal_answer_hint":"...",
                             "time_taken_seconds":90}],
            scores=[{"score":7, "grade":"Good",
                     "strengths":"...", "improvements":"..."}],
            start_time=datetime(...), end_time=datetime(...),
        )

    **Legacy call (backward compatible):**
        save_interview(
            user_id=1, domain="...", difficulty="...",
            responses=[{"question_number":1, "question_text":"...",
                        "user_answer":"...", "ai_score":7.5,
                        "ai_feedback":"...", "model_answer":"..."}],
        )

    Returns: new interview id (int)
    """
    # ── Resolve legacy args ────────────────────────────────────────────────
    if candidate_id is None and user_id is not None:
        candidate_id = user_id

    if responses is not None and questions_data is None:
        questions_data, scores = _convert_legacy_responses(responses, difficulty)

    if not questions_data:
        raise ValueError("questions_data (or responses) must not be empty.")
    if candidate_id is None:
        raise ValueError("candidate_id is required.")

    now = datetime.utcnow()
    start_time = start_time or now
    end_time = end_time or now
    duration = max(0.0, (end_time - start_time).total_seconds() / 60)

    total = len(questions_data)
    raw_scores = [s.get("score", 0) for s in scores]
    overall_score = float(sum(raw_scores))
    max_possible = float(total * 10)
    percentage = round((overall_score / max_possible * 100) if max_possible else 0.0, 2)
    lg = _letter_grade(percentage)
    vd = _verdict(percentage, domain or "this domain")

    try:
        with _session() as db:
            interview = Interview(
                candidate_id=candidate_id,
                domain=domain,
                difficulty=difficulty,
                total_questions=total,
                overall_score=overall_score,
                percentage=percentage,
                letter_grade=lg,
                verdict=vd,
                started_at=start_time,
                completed_at=end_time,
                duration_minutes=round(duration, 2),
                status="completed",
            )
            db.add(interview)
            db.flush()

            for qd, sc in zip(questions_data, scores):
                db.add(InterviewQuestion(
                    interview_id=interview.id,
                    question_number=qd.get("question_number", 0),
                    question_text=qd.get("question_text", ""),
                    difficulty=qd.get("difficulty", difficulty),
                    topic=qd.get("topic", "General"),
                    candidate_answer=qd.get("candidate_answer", ""),
                    score=int(sc.get("score", 0)),
                    grade=sc.get("grade", _question_grade(int(sc.get("score", 0)))),
                    strengths=sc.get("strengths", ""),
                    improvements=sc.get("improvements", ""),
                    ideal_answer_hint=qd.get("ideal_answer_hint", ""),
                    time_taken_seconds=int(qd.get("time_taken_seconds", 0)),
                ))

            return interview.id
    except Exception as exc:
        log.error("save_interview failed: %s", exc)
        raise


def _convert_legacy_responses(
    responses: list[dict], interview_difficulty: str
) -> tuple[list[dict], list[dict]]:
    """Convert old-format response dicts to (questions_data, scores) pair."""
    questions_data = []
    scores = []
    for r in responses:
        raw_score = r.get("ai_score", 0.0)
        int_score = max(0, min(10, round(raw_score)))
        questions_data.append({
            "question_number": r.get("question_number", 0),
            "question_text": r.get("question_text", ""),
            "difficulty": interview_difficulty,
            "topic": "General",
            "candidate_answer": r.get("user_answer", ""),
            "ideal_answer_hint": r.get("model_answer", ""),
            "time_taken_seconds": 0,
        })
        scores.append({
            "score": int_score,
            "grade": _question_grade(int_score),
            "strengths": "Response submitted.",
            "improvements": r.get("ai_feedback", ""),
        })
    return questions_data, scores


# ═══════════════════════════════════════════════════════════════════════════════
# 5. get_candidate_interviews
# ═══════════════════════════════════════════════════════════════════════════════

def get_candidate_interviews(candidate_id: int) -> list[dict]:
    """
    Return all interviews for a candidate, most-recent first.

    Each dict:
        id, candidate_id, domain, difficulty, total_questions,
        overall_score, percentage, letter_grade, verdict,
        started_at, completed_at, duration_minutes, status
    """
    try:
        with _session() as db:
            rows = (
                db.query(Interview)
                .filter_by(candidate_id=candidate_id)
                .order_by(desc(Interview.completed_at))
                .all()
            )
            return [_interview_to_dict(i) for i in rows]
    except Exception as exc:
        log.error("get_candidate_interviews failed: %s", exc)
        return []


def _interview_to_dict(i: Interview) -> dict:
    return {
        "id": i.id,
        "candidate_id": i.candidate_id,
        "domain": i.domain,
        "difficulty": i.difficulty,
        "total_questions": i.total_questions,
        "overall_score": i.overall_score,
        "percentage": i.percentage,
        "letter_grade": i.letter_grade,
        "verdict": i.verdict,
        "started_at": i.started_at,
        "completed_at": i.completed_at,
        "duration_minutes": i.duration_minutes,
        "status": i.status,
        # ── Backward-compat aliases so old UI keeps working ────────────────
        "score": i.overall_score,
        "max_score": float((i.total_questions or 0) * 10),
        "grade": i.letter_grade,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 6. get_interview_details
# ═══════════════════════════════════════════════════════════════════════════════

def get_interview_details(interview_id: int) -> Optional[dict]:
    """
    Return the full interview record including all per-question data.

    Returns None if not found.
    """
    try:
        with _session() as db:
            interview = db.query(Interview).filter_by(id=interview_id).first()
            if not interview:
                return None
            questions = (
                db.query(InterviewQuestion)
                .filter_by(interview_id=interview_id)
                .order_by(InterviewQuestion.question_number)
                .all()
            )
            result = _interview_to_dict(interview)
            result["questions"] = [_question_to_dict(q) for q in questions]
            # Legacy key used by results_page.py
            result["responses"] = [_question_to_legacy_response(q) for q in questions]
            return result
    except Exception as exc:
        log.error("get_interview_details failed: %s", exc)
        return None


def _question_to_dict(q: InterviewQuestion) -> dict:
    return {
        "id": q.id,
        "interview_id": q.interview_id,
        "question_number": q.question_number,
        "question_text": q.question_text,
        "difficulty": q.difficulty,
        "topic": q.topic,
        "candidate_answer": q.candidate_answer,
        "score": q.score,
        "grade": q.grade,
        "strengths": q.strengths,
        "improvements": q.improvements,
        "ideal_answer_hint": q.ideal_answer_hint,
        "time_taken_seconds": q.time_taken_seconds,
    }


def _question_to_legacy_response(q: InterviewQuestion) -> dict:
    """Map new question fields → old response keys for backward compatibility."""
    return {
        "question_number": q.question_number,
        "question_text": q.question_text,
        "user_answer": q.candidate_answer,
        "ai_score": float(q.score or 0),
        "ai_feedback": q.improvements or "",
        "model_answer": q.ideal_answer_hint or "",
        # New keys also available
        "candidate_answer": q.candidate_answer,
        "score": q.score,
        "grade": q.grade,
        "strengths": q.strengths,
        "improvements": q.improvements,
        "ideal_answer_hint": q.ideal_answer_hint,
        "topic": q.topic,
        "difficulty": q.difficulty,
        "time_taken_seconds": q.time_taken_seconds,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 7. get_all_candidates
# ═══════════════════════════════════════════════════════════════════════════════

def get_all_candidates() -> list[dict]:
    """
    Return all registered candidates with aggregate interview stats.
    Intended for admin use.
    """
    try:
        with _session() as db:
            rows = db.query(Candidate).order_by(desc(Candidate.created_at)).all()
            result = []
            for c in rows:
                interview_count = (
                    db.query(func.count(Interview.id))
                    .filter_by(candidate_id=c.id)
                    .scalar()
                ) or 0
                avg_pct = (
                    db.query(func.avg(Interview.percentage))
                    .filter_by(candidate_id=c.id)
                    .scalar()
                ) or 0.0
                result.append({
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "is_admin": c.is_admin,
                    "created_at": c.created_at,
                    "interview_count": interview_count,
                    "avg_percentage": round(float(avg_pct), 1),
                    # Backward-compat alias
                    "username": c.name,
                    "is_active": True,
                })
            return result
    except Exception as exc:
        log.error("get_all_candidates failed: %s", exc)
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# 8. get_leaderboard
# ═══════════════════════════════════════════════════════════════════════════════

def get_leaderboard(domain: str = None, limit: int = 10) -> list[dict]:
    """
    Return the top-N ranked candidates by best percentage score.

    If `domain` is specified, rank only within that domain.
    Each dict: rank, id, name, best_score, avg_score, interview_count, last_completed.
    """
    try:
        with _session() as db:
            query = (
                db.query(
                    Candidate.id,
                    Candidate.name,
                    func.max(Interview.percentage).label("best_score"),
                    func.avg(Interview.percentage).label("avg_score"),
                    func.count(Interview.id).label("interview_count"),
                    func.max(Interview.completed_at).label("last_completed"),
                )
                .join(Interview, Interview.candidate_id == Candidate.id)
                .filter(Interview.status == "completed")
            )
            if domain:
                query = query.filter(Interview.domain == domain)
            rows = (
                query
                .group_by(Candidate.id, Candidate.name)
                .order_by(desc("best_score"), desc("avg_score"))
                .limit(limit)
                .all()
            )
            return [
                {
                    "rank": idx + 1,
                    "id": r.id,
                    "name": r.name,
                    "best_score": round(float(r.best_score or 0), 1),
                    "avg_score": round(float(r.avg_score or 0), 1),
                    "interview_count": r.interview_count,
                    "last_completed": r.last_completed,
                    "domain_filter": domain,
                }
                for idx, r in enumerate(rows)
            ]
    except Exception as exc:
        log.error("get_leaderboard failed: %s", exc)
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# 9. get_domain_statistics
# ═══════════════════════════════════════════════════════════════════════════════

def get_domain_statistics() -> list[dict]:
    """
    Return aggregate statistics per domain, sorted by total interview count desc.

    Each dict:
        domain, total_interviews, avg_percentage, max_percentage,
        min_percentage, avg_overall_score, grade_A_count, grade_F_count
    """
    try:
        with _session() as db:
            rows = (
                db.query(
                    Interview.domain,
                    func.count(Interview.id).label("total_interviews"),
                    func.avg(Interview.percentage).label("avg_percentage"),
                    func.max(Interview.percentage).label("max_percentage"),
                    func.min(Interview.percentage).label("min_percentage"),
                    func.avg(Interview.overall_score).label("avg_overall_score"),
                )
                .filter(Interview.status == "completed")
                .group_by(Interview.domain)
                .order_by(desc("total_interviews"))
                .all()
            )
            stats = []
            for r in rows:
                # Count A-grade and F-grade interviews for this domain
                grade_a = (
                    db.query(func.count(Interview.id))
                    .filter(
                        Interview.domain == r.domain,
                        Interview.letter_grade.in_(["A+", "A"]),
                        Interview.status == "completed",
                    )
                    .scalar()
                ) or 0
                grade_f = (
                    db.query(func.count(Interview.id))
                    .filter(
                        Interview.domain == r.domain,
                        Interview.letter_grade == "F",
                        Interview.status == "completed",
                    )
                    .scalar()
                ) or 0
                pass_count = (
                    db.query(func.count(Interview.id))
                    .filter(
                        Interview.domain == r.domain,
                        Interview.percentage >= 60,
                        Interview.status == "completed",
                    )
                    .scalar()
                ) or 0
                total = int(r.total_interviews) or 1
                stats.append({
                    "domain": r.domain,
                    "total_interviews": r.total_interviews,
                    "avg_percentage": round(float(r.avg_percentage or 0), 1),
                    "max_percentage": round(float(r.max_percentage or 0), 1),
                    "min_percentage": round(float(r.min_percentage or 0), 1),
                    "avg_overall_score": round(float(r.avg_overall_score or 0), 2),
                    "grade_A_count": grade_a,
                    "grade_F_count": grade_f,
                    "pass_count": pass_count,
                    "pass_rate": round(pass_count / total * 100, 1),
                    # Backward-compat key for admin_page.py
                    "count": r.total_interviews,
                    "avg_pct": round(float(r.avg_percentage or 0), 1),
                })
            return stats
    except Exception as exc:
        log.error("get_domain_statistics failed: %s", exc)
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# 10. get_candidate_performance_trend
# ═══════════════════════════════════════════════════════════════════════════════

def get_candidate_performance_trend(candidate_id: int) -> list[dict]:
    """
    Return chronological interview results for one candidate.

    Useful for plotting score improvement over time.
    Each dict: interview_id, sequence, domain, difficulty,
                percentage, letter_grade, overall_score, completed_at.
    """
    try:
        with _session() as db:
            rows = (
                db.query(Interview)
                .filter_by(candidate_id=candidate_id, status="completed")
                .order_by(Interview.completed_at.asc())
                .all()
            )
            return [
                {
                    "interview_id": i.id,
                    "sequence": idx + 1,
                    "domain": i.domain,
                    "difficulty": i.difficulty,
                    "percentage": i.percentage,
                    "letter_grade": i.letter_grade,
                    "overall_score": i.overall_score,
                    "completed_at": i.completed_at,
                }
                for idx, i in enumerate(rows)
            ]
    except Exception as exc:
        log.error("get_candidate_performance_trend failed: %s", exc)
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# Backward-compatible wrappers — keep existing UI pages working
# ═══════════════════════════════════════════════════════════════════════════════

def create_tables() -> None:
    """Alias for init_db() — creates all tables."""
    init_db()


def register_user(username: str, email: str, password: str) -> dict:
    """
    Legacy wrapper for register_candidate.
    Maps `username` → `name` in the new schema.
    Returns {"success": True, "user_id": int, "username": str} on success.
    """
    result = register_candidate(name=username, email=email, password=password)
    if result["success"]:
        return {
            "success": True,
            "user_id": result["id"],
            "username": result["name"],
        }
    return {"success": False, "message": result.get("error", "Registration failed.")}


def login_user(username: str, password: str) -> dict:
    """
    Legacy wrapper for login_candidate.
    `username` is treated as the candidate's email address.
    Returns {"success": True, "user_id": int, "username": str} on success.
    """
    candidate = login_candidate(email=username, password=password)
    if candidate:
        return {
            "success": True,
            "user_id": candidate["id"],
            "username": candidate["name"],
        }
    return {"success": False, "message": "Invalid email or password."}


def get_user_interviews(user_id: int) -> list[dict]:
    """Legacy wrapper — delegates to get_candidate_interviews."""
    return get_candidate_interviews(user_id)


def get_interview_by_id(interview_id: int) -> Optional[dict]:
    """Legacy wrapper — delegates to get_interview_details."""
    return get_interview_details(interview_id)


def get_all_users() -> list[dict]:
    """Legacy wrapper — delegates to get_all_candidates."""
    return get_all_candidates()


def get_global_stats() -> dict:
    """
    Platform-wide aggregate statistics for the admin dashboard.

    Returns:
        total_users, total_interviews, avg_percentage, grade_distribution
    """
    try:
        with _session() as db:
            total_users = db.query(func.count(Candidate.id)).scalar() or 0
            total_interviews = (
                db.query(func.count(Interview.id))
                .filter_by(status="completed")
                .scalar()
            ) or 0
            avg_pct = (
                db.query(func.avg(Interview.percentage))
                .filter_by(status="completed")
                .scalar()
            ) or 0.0
            grade_rows = (
                db.query(Interview.letter_grade, func.count(Interview.id))
                .filter_by(status="completed")
                .group_by(Interview.letter_grade)
                .all()
            )
            return {
                "total_users": total_users,
                "total_interviews": total_interviews,
                "avg_percentage": round(float(avg_pct), 1),
                "grade_distribution": {g: c for g, c in grade_rows},
            }
    except Exception as exc:
        log.error("get_global_stats failed: %s", exc)
        return {
            "total_users": 0,
            "total_interviews": 0,
            "avg_percentage": 0.0,
            "grade_distribution": {},
        }


def get_domain_distribution() -> list[dict]:
    """
    Legacy wrapper — returns per-domain count + avg percentage.
    Compatible with admin_page.py's plotly chart.
    """
    stats = get_domain_statistics()
    return [
        {
            "domain": s["domain"],
            "count": s["total_interviews"],
            "avg_percentage": s["avg_percentage"],
        }
        for s in stats
    ]


def delete_user(user_id: int) -> bool:
    """Delete a candidate and all their interview data (cascade)."""
    try:
        with _session() as db:
            candidate = db.query(Candidate).filter_by(id=user_id).first()
            if not candidate:
                return False
            db.delete(candidate)
            return True
    except Exception as exc:
        log.error("delete_user failed: %s", exc)
        return False


def get_recent_activity(limit: int = 20) -> list[dict]:
    """
    Return the most recently completed interviews across all candidates.

    Each dict: interview_id, candidate_id, candidate_name, domain, difficulty,
               percentage, letter_grade, completed_at, total_questions.
    """
    try:
        with _session() as db:
            rows = (
                db.query(Interview, Candidate.name)
                .join(Candidate, Interview.candidate_id == Candidate.id)
                .filter(Interview.status == "completed")
                .order_by(desc(Interview.completed_at))
                .limit(limit)
                .all()
            )
            return [
                {
                    "interview_id":   iv.id,
                    "candidate_id":   iv.candidate_id,
                    "candidate_name": cname,
                    "domain":         iv.domain,
                    "difficulty":     iv.difficulty,
                    "percentage":     round(float(iv.percentage or 0), 1),
                    "letter_grade":   iv.letter_grade or "—",
                    "completed_at":   iv.completed_at,
                    "total_questions": iv.total_questions or 0,
                }
                for iv, cname in rows
            ]
    except Exception as exc:
        log.error("get_recent_activity failed: %s", exc)
        return []


def get_candidates_best_domains() -> dict:
    """
    Return {candidate_id: domain} mapping where domain is the most-interviewed
    domain for each candidate. Computed in one query.
    """
    try:
        with _session() as db:
            rows = (
                db.query(
                    Interview.candidate_id,
                    Interview.domain,
                    func.count(Interview.id).label("cnt"),
                )
                .filter(Interview.status == "completed")
                .group_by(Interview.candidate_id, Interview.domain)
                .all()
            )
        # Group by candidate in Python
        from collections import defaultdict
        acc: dict = defaultdict(dict)
        for cid, domain, cnt in rows:
            acc[cid][domain] = cnt
        return {cid: max(domains, key=domains.get) for cid, domains in acc.items()}
    except Exception as exc:
        log.error("get_candidates_best_domains failed: %s", exc)
        return {}
