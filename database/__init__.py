# ── New canonical API ─────────────────────────────────────────────────────────
from .db_handler import (
    init_db,
    register_candidate,
    login_candidate,
    save_interview,
    get_candidate_interviews,
    get_interview_details,
    get_all_candidates,
    get_leaderboard,
    get_domain_statistics,
    get_candidate_performance_trend,
)

# ── Backward-compatible aliases (keep existing UI pages working) ───────────────
from .db_handler import (
    create_tables,
    register_user,
    login_user,
    get_user_interviews,
    get_interview_by_id,
    get_all_users,
    get_global_stats,
    get_domain_distribution,
    delete_user,
    get_recent_activity,
    get_candidates_best_domains,
)

__all__ = [
    # Canonical
    "init_db",
    "register_candidate",
    "login_candidate",
    "save_interview",
    "get_candidate_interviews",
    "get_interview_details",
    "get_all_candidates",
    "get_leaderboard",
    "get_domain_statistics",
    "get_candidate_performance_trend",
    # Legacy aliases
    "create_tables",
    "register_user",
    "login_user",
    "get_user_interviews",
    "get_interview_by_id",
    "get_all_users",
    "get_global_stats",
    "get_domain_distribution",
    "delete_user",
    "get_recent_activity",
    "get_candidates_best_domains",
]
