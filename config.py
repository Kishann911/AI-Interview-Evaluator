APP_NAME = "AI Interview Evaluator"
VERSION = "1.0.0"
DB_PATH = "database/interview_evaluator.db"

DOMAINS = [
    "Software Engineering",
    "HR / Behavioral",
    "System Design",
    "Data Science & ML",
    "Product Management",
]

DIFFICULTY_LEVELS = ["Easy", "Medium", "Hard"]

QUESTION_COUNT_OPTIONS = [5, 7, 10]

SCORE_THRESHOLDS = {
    "Excellent": 8,
    "Good": 6,
    "Average": 4,
    "Poor": 0,
}

GEMINI_MODEL = "gemini-2.5-flash"

DOMAIN_ICONS = {
    "Software Engineering": "💻",
    "HR / Behavioral": "🤝",
    "System Design": "🏗️",
    "Data Science & ML": "🤖",
    "Product Management": "📦",
}

DIFFICULTY_COLORS = {
    "Easy": "#28a745",
    "Medium": "#ffc107",
    "Hard": "#dc3545",
}

GRADE_COLORS = {
    "Excellent": "#28a745",
    "Good": "#17a2b8",
    "Average": "#ffc107",
    "Poor": "#dc3545",
}

MAX_ANSWER_WORDS = 500
EVALUATION_TIMEOUT = 30
