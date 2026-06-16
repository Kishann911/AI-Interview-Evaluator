"""
Generate the complete Project Documentation PDF for AI Interview Evaluator.
Run:  python3 generate_documentation.py
Output: Project_Documentation.pdf
"""

import io
import os
import sys
from datetime import datetime

# ── ReportLab imports ──────────────────────────────────────────────────────────
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import BalancedColumns

W, H = A4

# ── Color palette ──────────────────────────────────────────────────────────────
NAVY     = colors.HexColor("#1E3A8A")
BLUE     = colors.HexColor("#2563EB")
PURPLE   = colors.HexColor("#7C3AED")
TEAL     = colors.HexColor("#0D9488")
GREEN    = colors.HexColor("#065F46")
AMBER    = colors.HexColor("#B45309")
SLATE    = colors.HexColor("#334155")
LIGHT_BG = colors.HexColor("#EFF6FF")
PALE_GREY = colors.HexColor("#F1F5F9")
BORDER   = colors.HexColor("#CBD5E1")
WHITE    = colors.white
BLACK    = colors.HexColor("#0F172A")


# ── Styles ─────────────────────────────────────────────────────────────────────
def _make_styles():
    base = getSampleStyleSheet()
    styles = {}

    def S(name, **kw):
        styles[name] = ParagraphStyle(name, **kw)

    # Cover
    S("CoverTitle",  fontSize=32, fontName="Helvetica-Bold",
      textColor=WHITE, alignment=TA_CENTER, leading=40)
    S("CoverSub",    fontSize=14, fontName="Helvetica",
      textColor=colors.HexColor("#BFDBFE"), alignment=TA_CENTER, leading=22)
    S("CoverMeta",   fontSize=10, fontName="Helvetica",
      textColor=colors.HexColor("#E0E7FF"), alignment=TA_CENTER, leading=16)

    # Body
    S("H1",  fontSize=17, fontName="Helvetica-Bold", textColor=NAVY,
      spaceBefore=14, spaceAfter=6, leading=22)
    S("H2",  fontSize=13, fontName="Helvetica-Bold", textColor=BLUE,
      spaceBefore=10, spaceAfter=4, leading=17)
    S("H3",  fontSize=11, fontName="Helvetica-Bold", textColor=PURPLE,
      spaceBefore=8, spaceAfter=3, leading=15)
    S("Body", fontSize=10, fontName="Helvetica", textColor=BLACK,
      spaceAfter=5, leading=15, alignment=TA_JUSTIFY)
    S("Bullet", fontSize=10, fontName="Helvetica", textColor=SLATE,
      spaceAfter=3, leading=14, leftIndent=14, firstLineIndent=-10)
    S("Code",  fontSize=8.5, fontName="Courier", textColor=colors.HexColor("#1E293B"),
      spaceAfter=4, leading=13, leftIndent=12,
      backColor=PALE_GREY)
    S("Caption", fontSize=8, fontName="Helvetica-Oblique",
      textColor=SLATE, alignment=TA_CENTER, spaceAfter=4, leading=12)
    S("TableHeader", fontSize=9, fontName="Helvetica-Bold",
      textColor=WHITE, alignment=TA_CENTER)
    S("TableCell", fontSize=9, fontName="Helvetica",
      textColor=BLACK, alignment=TA_LEFT, leading=13)
    S("PageFooter", fontSize=8, fontName="Helvetica",
      textColor=SLATE, alignment=TA_CENTER)

    return styles


ST = _make_styles()


# ── Page templates ─────────────────────────────────────────────────────────────

def _draw_cover(canvas, doc):
    canvas.saveState()
    # Navy gradient upper block
    canvas.setFillColor(NAVY)
    canvas.rect(0, H * 0.52, W, H * 0.48, fill=1, stroke=0)
    # Accent stripe
    canvas.setFillColor(BLUE)
    canvas.rect(0, H * 0.52, W, 4, fill=1, stroke=0)
    # Lower block
    canvas.setFillColor(LIGHT_BG)
    canvas.rect(0, 0, W, H * 0.52, fill=1, stroke=0)
    # Decorative circle (top-right)
    canvas.setFillColor(colors.HexColor("#1E40AF"))
    canvas.circle(W - 30, H - 30, 80, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#1D4ED8"))
    canvas.circle(W - 30, H - 30, 55, fill=1, stroke=0)
    canvas.restoreState()


def _draw_content(canvas, doc):
    canvas.saveState()
    # Header stripe
    canvas.setFillColor(NAVY)
    canvas.rect(0, H - 14 * mm, W, 14 * mm, fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.rect(0, H - 14 * mm, W, 1.5, fill=1, stroke=0)
    # Header text
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(WHITE)
    canvas.drawString(20 * mm, H - 9 * mm, "AI Interview Evaluator")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#BFDBFE"))
    canvas.drawRightString(W - 20 * mm, H - 9 * mm, "System Design Final Project")
    # Footer
    canvas.setFillColor(PALE_GREY)
    canvas.rect(0, 0, W, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(BORDER)
    canvas.rect(0, 12 * mm, W, 0.6, fill=1, stroke=0)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(SLATE)
    canvas.drawCentredString(W / 2, 4 * mm, f"Page {doc.page}")
    canvas.drawString(20 * mm, 4 * mm, "Confidential — Academic Submission")
    canvas.drawRightString(W - 20 * mm, 4 * mm, datetime.now().strftime("%B %Y"))
    canvas.restoreState()


def _make_doc(filename):
    doc = BaseDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=22 * mm, bottomMargin=18 * mm,
    )
    cover_frame   = Frame(20 * mm, 20 * mm, W - 40 * mm, H - 40 * mm,
                          id="cover_frame")
    content_frame = Frame(20 * mm, 14 * mm, W - 40 * mm, H - 30 * mm,
                          id="content_frame")
    doc.addPageTemplates([
        PageTemplate(id="Cover",   frames=[cover_frame],   onPage=_draw_cover),
        PageTemplate(id="Content", frames=[content_frame], onPage=_draw_content),
    ])
    return doc


# ── Helpers ────────────────────────────────────────────────────────────────────

def hr():
    return HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=6)

def spacer(n=6):
    return Spacer(1, n)

def h1(text):
    return Paragraph(text, ST["H1"])

def h2(text):
    return Paragraph(text, ST["H2"])

def h3(text):
    return Paragraph(text, ST["H3"])

def body(text):
    return Paragraph(text, ST["Body"])

def bullet(text):
    return Paragraph(f"• &nbsp;{text}", ST["Bullet"])

def code(text):
    return Paragraph(text.replace("\n", "<br/>").replace(" ", "&nbsp;"),
                     ST["Code"])


def info_box(text, color=LIGHT_BG, border=BLUE):
    tbl = Table([[Paragraph(text, ST["Body"])]], colWidths=[W - 44 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("BOX",        (0, 0), (-1, -1), 1.2, border),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [4]),
    ]))
    return tbl


def styled_table(header_row, data_rows, col_widths=None, header_color=NAVY):
    all_rows = [header_row] + data_rows
    tbl = Table(all_rows, colWidths=col_widths, repeatRows=1)
    n = len(data_rows)
    style = [
        # Header
        ("BACKGROUND",   (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR",    (0, 0), (-1, 0), WHITE),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 9),
        ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
        ("ROWBACKGROUND",(0, 1), (-1, -1), [PALE_GREY, WHITE]),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 9),
        ("GRID",         (0, 0), (-1, -1), 0.4, BORDER),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]
    # Alternating row colour
    for i in range(1, n + 1):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), PALE_GREY))
        else:
            style.append(("BACKGROUND", (0, i), (-1, i), WHITE))
    tbl.setStyle(TableStyle(style))
    return tbl


# ── Section builders ───────────────────────────────────────────────────────────

def _cover_page():
    story = []
    story.append(spacer(H * 0.08))
    story.append(Paragraph("🎯 AI Interview Evaluator", ST["CoverTitle"]))
    story.append(spacer(8))
    story.append(Paragraph("Project Documentation", ST["CoverSub"]))
    story.append(spacer(4))
    story.append(Paragraph("System Design Final Project", ST["CoverSub"]))
    story.append(spacer(30))
    story.append(Paragraph("Powered by Google Gemini 1.5 Flash · Streamlit · SQLite", ST["CoverMeta"]))
    story.append(spacer(12))

    # Metadata table
    meta_data = [
        ["Project Title",  "AI-Based Interview Evaluator"],
        ["Technology",     "Python · Streamlit · Google Gemini AI"],
        ["Database",       "SQLite via SQLAlchemy 2.0"],
        ["Submission Date", "June 2026"],
    ]
    meta_tbl = Table(meta_data, colWidths=[55 * mm, 100 * mm])
    meta_tbl.setStyle(TableStyle([
        ("FONTNAME",     (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",     (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("TEXTCOLOR",    (0, 0), (-1, -1), colors.HexColor("#BFDBFE")),
        ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#1E3A8A")),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#2563EB")),
    ]))
    story.append(meta_tbl)
    story.append(spacer(H * 0.06))

    # Tagline in lower white area (switch template first)
    story.append(NextPageTemplate("Content"))
    return story


def _toc_page():
    story = [PageBreak()]
    story.append(h1("Table of Contents"))
    story.append(hr())
    toc = [
        ("1", "Problem Statement", "3"),
        ("2", "Proposed Solution", "4"),
        ("3", "System Architecture", "5"),
        ("4", "Module Description", "6"),
        ("5", "Database Design", "8"),
        ("6", "Technology Stack", "9"),
        ("7", "Implementation Details", "10"),
        ("8", "Evaluation Rubric & Scoring", "12"),
        ("9", "Screenshots", "13"),
        ("10","Future Scope", "14"),
    ]
    toc_tbl = Table(
        [[Paragraph(f"<b>{n}.</b>", ST["Body"]),
          Paragraph(title, ST["Body"]),
          Paragraph(f"<b>{pg}</b>", ST["Body"])]
         for n, title, pg in toc],
        colWidths=[12 * mm, 130 * mm, 18 * mm],
    )
    toc_tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("LINEBELOW",     (0, 0), (-1, -1), 0.4, BORDER),
        ("ALIGN",         (2, 0), (2, -1), "RIGHT"),
    ]))
    story.append(toc_tbl)
    return story


def _section_problem_statement():
    return [
        PageBreak(),
        h1("1. Problem Statement"),
        hr(),
        body(
            "The modern hiring process relies heavily on in-person or remote technical interviews to assess "
            "a candidate's knowledge, communication skills, and problem-solving abilities. However, "
            "candidates often lack access to structured, objective, and domain-specific practice tools. "
            "Existing resources are either too generic (basic quiz apps), too expensive (coaching services), "
            "or provide no actionable feedback beyond a simple right/wrong score."
        ),
        spacer(4),
        h2("Core Challenges Identified"),
        bullet("<b>Lack of structured practice environments</b> — candidates cannot simulate real interview pressure with immediate, personalised feedback."),
        bullet("<b>Subjectivity in self-assessment</b> — without expert evaluation, candidates cannot identify blind spots in their knowledge."),
        bullet("<b>Domain-specific gaps</b> — different interview types (system design, coding, behavioural) require different preparation approaches, rarely addressed by a single tool."),
        bullet("<b>No progress tracking</b> — most practice tools do not maintain a history of performance, making it impossible to measure improvement over time."),
        bullet("<b>Accessibility</b> — professional coaching or mock interview services can be prohibitively expensive for students and early-career professionals."),
        spacer(6),
        info_box(
            "<b>Problem Definition:</b> Design and implement a scalable, AI-powered web application that provides "
            "domain-specific mock interviews with automated, rubric-based evaluation, detailed performance analytics, "
            "progress tracking, and exportable reports — accessible to any user with a web browser.",
            color=LIGHT_BG, border=BLUE,
        ),
    ]


def _section_proposed_solution():
    return [
        PageBreak(),
        h1("2. Proposed Solution"),
        hr(),
        body(
            "The AI Interview Evaluator is a full-stack Python web application built with Streamlit as the "
            "presentation layer and Google Gemini 1.5 Flash as the evaluation engine. It provides a complete "
            "interview simulation pipeline from question selection to performance reporting."
        ),
        spacer(4),
        h2("Solution Highlights"),
        bullet("<b>225-question bank</b> spanning 5 domains (Software Engineering, System Design, Data Science &amp; ML, HR/Behavioural, Product Management) at 3 difficulty levels (Easy, Medium, Hard)."),
        bullet("<b>AI-powered per-question evaluation</b> using a structured JSON prompt sent to Gemini 1.5 Flash, which returns scores on 4 weighted rubric criteria, strengths, areas for improvement, and an ideal answer hint."),
        bullet("<b>Rubric-based weighted scoring</b> — each domain has unique weights (e.g., Software Engineering: Technical Accuracy 35%, Depth 25%, Communication 25%, Problem-Solving 15%) ensuring fair, objective scoring."),
        bullet("<b>SQLite persistence</b> via SQLAlchemy 2.0 ORM — all candidates, interviews, and per-question evaluations are stored in a relational database with cascade deletes."),
        bullet("<b>Rich analytics dashboard</b> using Plotly — score trend lines, radar charts, grade distribution histograms, and domain-wise performance comparisons."),
        bullet("<b>PDF and CSV export</b> via ReportLab and pandas — multi-page professional reports with cover page, performance summary, Q&amp;A analysis, and domain recommendations."),
        bullet("<b>Global leaderboard</b> with privacy masking (only first 3 characters of names shown) ranked by best percentage score per domain."),
        bullet("<b>Admin dashboard</b> for platform-wide analytics, candidate management, and data export."),
        bullet("<b>Offline/mock mode</b> — setting <font face='Courier'>USE_MOCK=true</font> runs the entire pipeline without any API calls, producing realistic scores (4–9) for demonstration and testing."),
        spacer(6),
        h2("Design Principles Followed"),
        bullet("<b>Separation of Concerns</b> — UI, business logic, and data access are cleanly separated into distinct Python packages."),
        bullet("<b>DRY (Don't Repeat Yourself)</b> — a single <font face='Courier'>_build_result()</font> function in evaluator.py produces evaluation dicts consumed by all UI pages."),
        bullet("<b>Backward Compatibility</b> — all legacy key names are aliased so no existing functionality breaks when internal keys are refactored."),
        bullet("<b>Idempotent Initialisation</b> — <font face='Courier'>init_db()</font> is safe to call on every Streamlit rerun; tables are created only if they don't exist."),
        bullet("<b>Graceful Degradation</b> — if the Gemini API call fails after 3 retries, the system automatically falls back to mock evaluation and flags the result."),
    ]


def _section_architecture():
    story = [
        PageBreak(),
        h1("3. System Architecture"),
        hr(),
        body(
            "The system follows a layered architecture with clear boundaries between presentation, "
            "business logic, data access, and external services. Streamlit's session state acts as "
            "an in-memory state machine that coordinates the interview flow across page reruns."
        ),
        spacer(6),
    ]

    # Embed the architecture diagram if it exists
    diagram_path = os.path.join(os.path.dirname(__file__),
                                "System_Architecture_Diagram.png")
    if os.path.exists(diagram_path):
        img = Image(diagram_path, width=W - 44 * mm, height=(W - 44 * mm) * 0.7)
        story.append(img)
        story.append(Paragraph(
            "Figure 1: System Architecture Diagram — 6 layers from browser client to SQLite storage",
            ST["Caption"]
        ))
        story.append(spacer(6))
    else:
        story.append(info_box("⚠️ Architecture diagram not found. Run: python3 generate_architecture_diagram.py", PALE_GREY, AMBER))

    story += [
        h2("Layer Description"),
        styled_table(
            ["Layer", "Components", "Responsibility"],
            [
                ["Client Layer",       "Web Browser",                              "User interface via HTTP on port 8501"],
                ["UI / Presentation",  "app.py, auth_page, interview_page,\nresults_page, history_page, admin_page",  "Page rendering, navigation, session state management"],
                ["Core / Logic",       "evaluator.py, questions.py,\nreport_generator.py, config.py",  "AI evaluation, question retrieval, report generation"],
                ["Data Access",        "db_handler.py, models.py,\ndatabase/__init__.py",  "ORM queries, CRUD operations, stats aggregation"],
                ["External Services",  "Google Gemini 1.5 Flash API",              "AI scoring, rubric evaluation, feedback generation"],
                ["Persistent Storage", "SQLite (interview_evaluator.db)",           "Candidate accounts, interview records, question scores"],
            ],
            col_widths=[35 * mm, 65 * mm, 65 * mm],
        ),
        spacer(8),
        h2("Interview State Machine"),
        body(
            "The interview flow is implemented as a state machine managed through Streamlit session state:"
        ),
        spacer(4),
        info_box(
            "<b>not_started</b>  →  (Begin button)  →  <b>in_progress</b>  →  (Submit / Skip)  →  <b>evaluating</b>"
            "  →  (AI call complete)  →  back to <b>in_progress</b> (next Q) or  →  <b>completed</b>  →  (save to DB)  →  Results page",
            color=colors.HexColor("#F0FDF4"),
            border=GREEN,
        ),
    ]
    return story


def _section_modules():
    return [
        PageBreak(),
        h1("4. Module Description"),
        hr(),
        h2("4.1 app.py — Application Entry Point"),
        body("The root Streamlit file. Responsibilities: load .env, call init_db() and init_session_state() on every run, inject custom CSS, render the sidebar navigation, and route to the appropriate page function based on current_page session key."),

        spacer(4), h2("4.2 config.py — Configuration Constants"),
        body("Centralised configuration: DOMAINS (5), DIFFICULTY_LEVELS (3), QUESTION_COUNT_OPTIONS ([5,7,10]), DOMAIN_ICONS, DIFFICULTY_COLORS, GRADE_COLORS, GEMINI_MODEL, DB_PATH, MAX_ANSWER_WORDS, EVALUATION_TIMEOUT."),

        spacer(4), h2("4.3 core/evaluator.py — AI Evaluation Engine"),
        body("Core module containing the Gemini integration. Key functions:"),
        bullet("<font face='Courier'>evaluate_answer(question, answer, domain, difficulty, expected_keywords)</font> — builds a structured prompt, calls Gemini with 3-attempt retry + exponential backoff, parses JSON, validates and recomputes weighted score from rubric."),
        bullet("<font face='Courier'>mock_evaluate()</font> — returns realistic scores (4–9) without API calls. Used when USE_MOCK=true or as automatic fallback after API failure."),
        bullet("<font face='Courier'>get_interview_summary_feedback()</font> — calls Gemini to generate an AI narrative summary of the full interview."),
        bullet("<font face='Courier'>RUBRICS dict</font> — 5 domains × 4 criteria with weights summing to 100. Used both for prompt construction and weighted score recomputation."),

        spacer(4), h2("4.4 core/questions.py — Question Bank"),
        body("Stores all 225 interview questions as a Python dictionary. Structure: QUESTIONS[domain] = list of dicts with fields: id, question, difficulty, topic, expected_keywords, follow_up. The get_questions(domain, count, difficulty) function filters and randomly samples the requested number of questions."),

        spacer(4), h2("4.5 core/report_generator.py — Report Generator"),
        body("Generates professional output using ReportLab Platypus. Two public functions:"),
        bullet("<font face='Courier'>generate_pdf_report(interview_data, candidate_data, evaluations=None) → bytes</font> — 4-page PDF: Cover, Performance Summary, Question Analysis (with matplotlib bar chart), Recommendations."),
        bullet("<font face='Courier'>generate_csv_report(interview_data, evaluations=None) → bytes</font> — 12-column CSV: Q#, Topic, Domain, Difficulty, Question, Answer, Score, Grade, Strengths, Improvements, Ideal Answer Hint, Time Taken."),

        spacer(4), h2("4.6 database/models.py — ORM Models"),
        body("Defines 3 SQLAlchemy models with cascade relationships:"),
        bullet("<b>Candidate</b> — id, name, email, password_hash (salt:sha256), created_at, is_admin."),
        bullet("<b>Interview</b> — id, candidate_id (FK), domain, difficulty, total_questions, overall_score, percentage, letter_grade, verdict, started_at, completed_at, duration_minutes, status."),
        bullet("<b>InterviewQuestion</b> — id, interview_id (FK), question_number, question_text, difficulty, topic, candidate_answer, score, grade, strengths, improvements, ideal_answer_hint, time_taken_seconds."),

        spacer(4), h2("4.7 database/db_handler.py — Data Access Layer"),
        body("All database operations in a single module. Uses a @contextmanager _session() that auto-commits on success and rolls back on exception. Key functions: init_db (idempotent, seeds admin + demo user), register_candidate, login_candidate (salted SHA-256 verify), save_interview, get_candidate_interviews, get_interview_details, get_leaderboard, get_domain_statistics, get_recent_activity, plus legacy aliases for backward compatibility."),

        spacer(4), h2("4.8 – 4.12 UI Pages"),
        styled_table(
            ["File", "Purpose", "Key Features"],
            [
                ["auth_page.py",      "Authentication",       "Login / Register forms, init_session_state() with 18 keys, auto-login after register"],
                ["interview_page.py", "Interview Flow",       "State machine, per-question answer input, word count indicator, AI evaluation spinner, result cards"],
                ["results_page.py",   "Results Display",      "Score hero, metric cards, Plotly charts (radar, bar, pie), Q&A breakdown, AI narrative summary, PDF/CSV export"],
                ["history_page.py",   "History + Leaderboard","Interview cards, domain/grade/date filters, trend chart, privacy-masked leaderboard with user highlight"],
                ["admin_page.py",     "Admin Dashboard",      "Platform stats, domain analytics, candidates table, activity feed, score histogram, export, danger zone"],
            ],
            col_widths=[38 * mm, 35 * mm, 92 * mm],
        ),
    ]


def _section_database():
    return [
        PageBreak(),
        h1("5. Database Design"),
        hr(),
        body(
            "The application uses SQLite as its persistent store, accessed through SQLAlchemy 2.0 ORM. "
            "The schema consists of 3 tables with a one-to-many cascade delete relationship chain."
        ),
        spacer(6),
        h2("Entity-Relationship Overview"),
        info_box(
            "<b>Candidate</b> (1) ──── (∞) <b>Interview</b> (1) ──── (∞) <b>InterviewQuestion</b><br/>"
            "On Candidate delete → cascade delete all Interviews → cascade delete all InterviewQuestions",
            color=colors.HexColor("#F0FDF4"), border=GREEN,
        ),
        spacer(8),

        h2("Table: candidates"),
        styled_table(
            ["Column", "Type", "Constraints", "Description"],
            [
                ["id",            "INTEGER", "PRIMARY KEY AUTOINCREMENT", "Unique candidate identifier"],
                ["name",          "VARCHAR(100)", "NOT NULL",             "Full display name"],
                ["email",         "VARCHAR(150)", "UNIQUE, NOT NULL",     "Login email address"],
                ["password_hash", "VARCHAR(256)", "NOT NULL",             "'salt:sha256hex' format"],
                ["created_at",    "DATETIME",     "DEFAULT utcnow",       "Account creation timestamp"],
                ["is_admin",      "BOOLEAN",      "DEFAULT False",        "Admin privilege flag"],
            ],
            col_widths=[32 * mm, 28 * mm, 50 * mm, 55 * mm],
        ),
        spacer(8),

        h2("Table: interviews"),
        styled_table(
            ["Column", "Type", "Description"],
            [
                ["id",               "INTEGER PK",  "Auto-incremented interview ID"],
                ["candidate_id",     "INTEGER FK",  "References candidates.id (cascade delete)"],
                ["domain",           "VARCHAR(100)", "Interview domain (e.g. Software Engineering)"],
                ["difficulty",       "VARCHAR(50)",  "Easy / Medium / Hard"],
                ["total_questions",  "INTEGER",      "Number of questions answered"],
                ["overall_score",    "FLOAT",        "Sum of individual question scores"],
                ["percentage",       "FLOAT",        "overall_score / (total_questions × 10) × 100"],
                ["letter_grade",     "VARCHAR(5)",   "A+ / A / B+ / B / C+ / C / D / F"],
                ["verdict",          "VARCHAR(200)", "AI-generated performance verdict text"],
                ["started_at",       "DATETIME",     "Interview start timestamp (UTC)"],
                ["completed_at",     "DATETIME",     "Interview end timestamp (UTC)"],
                ["duration_minutes", "FLOAT",        "Computed from start/end timestamps"],
                ["status",           "VARCHAR(20)",  "Always 'completed' for saved interviews"],
            ],
            col_widths=[40 * mm, 30 * mm, 95 * mm],
        ),
        spacer(8),

        h2("Table: interview_questions"),
        styled_table(
            ["Column", "Type", "Description"],
            [
                ["id",                 "INTEGER PK",   "Auto-incremented row ID"],
                ["interview_id",       "INTEGER FK",   "References interviews.id (cascade delete)"],
                ["question_number",    "INTEGER",      "Position within the interview (1-based)"],
                ["question_text",      "TEXT",         "Full question string"],
                ["difficulty",         "VARCHAR(50)",  "Per-question difficulty level"],
                ["topic",              "VARCHAR(100)", "Sub-topic tag (e.g. OOP, Recursion)"],
                ["candidate_answer",   "TEXT",         "Candidate's submitted answer text"],
                ["score",              "INTEGER",      "AI score 1–10"],
                ["grade",              "VARCHAR(50)",  "Excellent / Good / Average / Poor"],
                ["strengths",          "TEXT",         "AI-identified answer strengths"],
                ["improvements",       "TEXT",         "AI-suggested improvements"],
                ["ideal_answer_hint",  "TEXT",         "Model answer hint from AI"],
                ["time_taken_seconds", "INTEGER",      "Seconds spent on this question"],
            ],
            col_widths=[42 * mm, 28 * mm, 95 * mm],
        ),
    ]


def _section_tech_stack():
    return [
        PageBreak(),
        h1("6. Technology Stack"),
        hr(),
        styled_table(
            ["Layer", "Technology", "Version", "Role"],
            [
                ["Web Framework",     "Streamlit",                  "≥ 1.32",   "Single-page app routing, session state, widget rendering"],
                ["AI Engine",         "Google Gemini 1.5 Flash",    "via google-genai", "Rubric-based answer evaluation, narrative summaries"],
                ["Programming Language", "Python",                  "3.10+",    "All backend logic, data processing, scripting"],
                ["Database ORM",      "SQLAlchemy",                 "≥ 2.0",    "Model definition, query building, session management"],
                ["Database",          "SQLite",                     "Built-in", "Lightweight relational storage, zero-configuration"],
                ["Charting",          "Plotly",                     "≥ 5.20",   "Interactive line, bar, radar, pie charts in UI"],
                ["Diagram / Charts",  "Matplotlib",                 "≥ 3.8",    "Static bar chart in PDF, architecture diagram PNG"],
                ["PDF Generation",    "ReportLab (Platypus)",       "≥ 4.1",    "Multi-page professional PDF with custom templates"],
                ["Tabular Data",      "pandas",                     "≥ 2.2",    "DataFrame operations, CSV export"],
                ["Numerical",         "NumPy",                      "≥ 1.26",   "Stats computations in admin score histogram"],
                ["Environment",       "python-dotenv",              "≥ 1.0",    "Loads GEMINI_API_KEY and USE_MOCK from .env file"],
                ["Styling",           "Custom CSS",                 "—",        "Inter font, CSS variables, animations via style.css"],
            ],
            col_widths=[32 * mm, 40 * mm, 22 * mm, 71 * mm],
        ),
    ]


def _section_implementation():
    return [
        PageBreak(),
        h1("7. Implementation Details"),
        hr(),

        h2("7.1 AI Evaluation Pipeline"),
        body("Each submitted answer goes through the following pipeline:"),
        bullet("<b>Step 1 — Prompt Construction:</b> evaluator.py builds a structured prompt including the question, candidate answer, domain, difficulty, expected keywords, and the domain rubric with criteria weights."),
        bullet("<b>Step 2 — API Call with Retry:</b> The prompt is sent to Gemini 1.5 Flash with temperature=0.3 and max_output_tokens=1024. If the call fails, it retries up to 3 times with exponential backoff (1s, 2s, 4s)."),
        bullet("<b>Step 3 — JSON Parsing:</b> Gemini returns a JSON object. The parser extracts scores for each rubric criterion, validates them, and recomputes the weighted score using our rubric weights (not Gemini's calculation)."),
        bullet("<b>Step 4 — Result Building:</b> A standardised result dict is constructed with new keys (weighted_score, grade, strengths, improvements, ideal_answer_hint, follow_up_question, keyword_coverage) plus backward-compat aliases."),
        bullet("<b>Step 5 — Fallback:</b> If all 3 API attempts fail, mock_evaluate() is called and result['_fallback'] = True is set. A warning is shown to the user."),

        spacer(6),
        h2("7.2 Password Security"),
        body("Passwords are never stored in plaintext. The _hash_password() function generates a cryptographically random 16-byte salt using secrets.token_hex(16), then computes SHA-256(salt + password) and stores the result as 'salt:hexdigest'. Verification recomputes and compares using hmac-like comparison."),

        spacer(6),
        h2("7.3 Session State Management"),
        body("Streamlit re-executes the entire script on every user interaction. The init_session_state() function in auth_page.py initialises 18 session state keys with safe defaults on the first run, and is idempotent on subsequent runs. The interview state machine uses the 'interview_state' key as its current state."),

        spacer(6),
        h2("7.4 Mock Mode Architecture"),
        body("When USE_MOCK=true in .env, _is_mock_mode() returns True and evaluate_answer() delegates directly to mock_evaluate() without any API call. The mock evaluator:"),
        bullet("Computes a base score from answer length (4.5 for short, 5.5 for medium, 7.0 for longer, 8.0 for detailed answers)."),
        bullet("Applies keyword bonus (+1 point maximum for keyword coverage)."),
        bullet("Applies difficulty adjustment (±0.5)."),
        bullet("Clamps the final weighted score to [4.0, 9.0] for real answers and [1.0, 3.0] for skipped answers, ensuring realistic demo scores."),
        bullet("Returns identical structure to the real evaluator — zero code changes needed elsewhere."),

        spacer(6),
        h2("7.5 Report Generation"),
        body("The generate_pdf_report() function uses ReportLab's Platypus framework with two PageTemplate objects (Cover and Content). Each page has a custom background drawn via canvas.saveState()/restoreState(). The report includes:"),
        bullet("<b>Page 1 — Cover:</b> Navy gradient background, candidate name, domain, difficulty, grade, overall score, date."),
        bullet("<b>Page 2 — Performance Summary:</b> Score metrics table, matplotlib bar chart (embedded as RLImage), verdict box."),
        bullet("<b>Pages 3+ — Question Analysis:</b> Each question wrapped in KeepTogether([...]) with question box, answer box, score banner, strengths/improvements panels."),
        bullet("<b>Last Page — Recommendations:</b> Domain-specific study tips from the _DOMAIN_TIPS dict."),

        spacer(6),
        h2("7.6 Leaderboard Privacy"),
        body("The leaderboard masks all candidate names except the current user's own name. The _mask_name() function takes the first word of the name, keeps the first 3 characters visible, and appends '*****'. Example: 'Kishan Patel' → 'Kis*****'. The current user's row is highlighted in light blue with a 'You' badge."),

        spacer(6),
        h2("7.7 Database Seeding"),
        body("On every application startup, init_db() calls two seed functions: _seed_admin() creates admin@ai.com/admin123 with is_admin=True if it doesn't exist, and _seed_demo_user() creates demo@test.com/demo123 if it doesn't exist. Both functions are wrapped in try/except and log warnings on failure without crashing the app."),
    ]


def _section_rubric():
    return [
        PageBreak(),
        h1("8. Evaluation Rubric & Scoring"),
        hr(),
        body(
            "Each domain has a unique rubric with 4 criteria and weights summing to 100. "
            "The AI evaluates each criterion independently, and the final weighted score is "
            "computed deterministically from the rubric — never trusted directly from the AI."
        ),
        spacer(6),
        h2("Domain Rubrics"),
        styled_table(
            ["Domain", "Criterion 1", "Criterion 2", "Criterion 3", "Criterion 4"],
            [
                ["Software Engineering",  "Technical Accuracy (35%)",   "Depth & Completeness (25%)",  "Communication Clarity (25%)",     "Problem-Solving Approach (15%)"],
                ["System Design",         "Scalability (30%)",          "Architecture Depth (30%)",    "Trade-off Analysis (25%)",        "Communication Clarity (15%)"],
                ["Data Science & ML",     "Conceptual Accuracy (35%)",  "Mathematical Depth (25%)",    "Practical Application (25%)",     "Communication (15%)"],
                ["HR / Behavioral",       "Situation Clarity (25%)",    "Action & Reasoning (35%)",    "Outcome & Impact (25%)",          "Communication (15%)"],
                ["Product Management",    "Problem Definition (25%)",   "Strategic Thinking (30%)",    "Data-Driven Approach (25%)",      "Communication (20%)"],
            ],
            col_widths=[38 * mm, 35 * mm, 35 * mm, 35 * mm, 22 * mm],
        ),
        spacer(8),
        h2("Letter Grade Scale"),
        styled_table(
            ["Percentage", "Letter Grade", "Interpretation"],
            [
                ["≥ 90%", "A+", "Outstanding — Expert level, highly recommended"],
                ["≥ 80%", "A",  "Excellent — Strong competency demonstrated"],
                ["≥ 72%", "B+", "Good — Above average, minor gaps"],
                ["≥ 64%", "B",  "Good — Solid foundation with some areas to improve"],
                ["≥ 56%", "C+", "Satisfactory — Core concepts understood"],
                ["≥ 48%", "C",  "Average — Acceptable but needs focused preparation"],
                ["≥ 35%", "D",  "Below Average — Significant gaps identified"],
                ["< 35%", "F",  "Fail — Fundamental review required"],
            ],
            col_widths=[30 * mm, 30 * mm, 105 * mm],
        ),
    ]


def _section_screenshots():
    return [
        PageBreak(),
        h1("9. Screenshots"),
        hr(),
        body(
            "The following screens represent the primary user interface views of the application. "
            "Run the application locally and navigate through each page to see the live UI."
        ),
        spacer(6),
        styled_table(
            ["Screen", "Description", "How to Access"],
            [
                ["Login / Register",     "Auth page with two tabs, demo credentials box, gradient card", "Open app — shown before login"],
                ["Home Dashboard",       "Welcome banner, 4 metric cards, Quick Start panel, trend chart", "Login → Home (sidebar)"],
                ["Interview Setup",      "Domain/difficulty/count config, live preview card, rules panel", "Start Interview → Setup tab"],
                ["Interview Q&A",        "Progress bar, question card, text area, word count indicator", "During an active interview session"],
                ["Evaluation Result",    "Score hero, grade badge, strengths panel, improvements panel, hint expander", "After submitting each answer"],
                ["Results Page",         "Score hero, radar chart, bar chart, Q&A breakdown table, AI summary", "After completing interview"],
                ["PDF Report",           "Professional multi-page PDF with cover, charts, Q&A analysis", "Results → Download PDF"],
                ["Interview History",    "Filtered interview cards, trend line chart across sessions", "Sidebar → Interview History"],
                ["Leaderboard",          "Ranked table, masked names, You badge, domain filter", "History → Leaderboard tab"],
                ["Admin Dashboard",      "Platform stats, domain analytics, candidates table, danger zone", "Login as admin → Admin Panel"],
            ],
            col_widths=[40 * mm, 80 * mm, 45 * mm],
        ),
        spacer(8),
        info_box(
            "📸 To capture screenshots for your submission: launch the app with <font face='Courier'>streamlit run app.py</font>, "
            "navigate to each page, and use your OS screenshot tool (macOS: Cmd+Shift+4, Windows: Win+Shift+S). "
            "Insert the captured images here before final PDF submission.",
            color=colors.HexColor("#FEF3C7"), border=AMBER,
        ),
    ]


def _section_future_scope():
    return [
        PageBreak(),
        h1("10. Future Scope"),
        hr(),
        body(
            "The current implementation provides a strong foundation for a production-grade interview platform. "
            "The following enhancements are planned or proposed for future versions:"
        ),
        spacer(6),
        h2("10.1 AI & Evaluation Enhancements"),
        bullet("<b>Voice Input:</b> Integrate Web Speech API or Whisper to allow candidates to speak answers rather than type, mimicking real interview conditions."),
        bullet("<b>Code Execution Environment:</b> Embed a sandboxed Python/JavaScript REPL for coding questions, evaluating both correctness and code quality."),
        bullet("<b>Adaptive Difficulty:</b> Dynamically adjust question difficulty based on the candidate's running score — increase difficulty after correct answers, decrease after poor ones."),
        bullet("<b>Multi-Model Support:</b> Allow users to choose between Gemini, GPT-4, and Claude for evaluation, comparing scoring consistency across models."),

        spacer(4),
        h2("10.2 Platform Features"),
        bullet("<b>Interview Scheduling:</b> Calendar integration allowing candidates to schedule mock interviews and receive email/SMS reminders."),
        bullet("<b>Peer Review Mode:</b> Allow two users to evaluate each other's answers with a crowd-sourced score alongside the AI score."),
        bullet("<b>Company-Specific Question Banks:</b> Curated question sets modeled after FAANG, startup, and domain-specific company interviews."),
        bullet("<b>Interview Streaks &amp; Gamification:</b> Daily practice streaks, badges, XP points, and level progression to improve engagement."),

        spacer(4),
        h2("10.3 Technical Improvements"),
        bullet("<b>PostgreSQL Migration:</b> Replace SQLite with PostgreSQL for multi-user concurrent access in production deployments."),
        bullet("<b>Redis Caching:</b> Cache leaderboard queries and domain statistics with a 5-minute TTL to reduce DB load."),
        bullet("<b>REST API Layer:</b> Expose a FastAPI backend so the evaluation engine can serve mobile apps and third-party integrations."),
        bullet("<b>Docker + Kubernetes:</b> Containerise the application for one-command deployment and horizontal scaling."),
        bullet("<b>Automated Testing Suite:</b> Add pytest unit tests for evaluator.py, db_handler.py, and report_generator.py with CI/CD integration."),
        bullet("<b>OAuth 2.0 Authentication:</b> Replace email/password login with Google Sign-In and GitHub OAuth for simpler onboarding."),

        spacer(4),
        h2("10.4 Analytics & Reporting"),
        bullet("<b>Comparative Analytics:</b> Compare a candidate's scores against the anonymised cohort average for each domain and difficulty."),
        bullet("<b>AI-Generated Study Plan:</b> After each interview, Gemini generates a personalised 2-week study plan targeting identified weak areas."),
        bullet("<b>Employer Portal:</b> Allow companies to create accounts, set custom question banks, send interview links to candidates, and view scores in a shared dashboard."),

        spacer(8),
        hr(),
        info_box(
            "<b>Conclusion:</b> The AI Interview Evaluator successfully demonstrates the integration of modern AI capabilities "
            "(Google Gemini) with a full-stack Python web application (Streamlit + SQLAlchemy). "
            "It addresses a real-world problem in interview preparation by providing objective, rubric-based feedback "
            "at scale, with a robust architecture that supports future enhancements without requiring a ground-up rewrite.",
            color=LIGHT_BG, border=NAVY,
        ),
    ]


# ── Main document assembly ─────────────────────────────────────────────────────

def build_pdf(filename="Project_Documentation.pdf"):
    doc = _make_doc(filename)

    story = []
    story += _cover_page()
    story += _toc_page()
    story += _section_problem_statement()
    story += _section_proposed_solution()
    story += _section_architecture()
    story += _section_modules()
    story += _section_database()
    story += _section_tech_stack()
    story += _section_implementation()
    story += _section_rubric()
    story += _section_screenshots()
    story += _section_future_scope()

    doc.build(story)
    size_kb = os.path.getsize(filename) // 1024
    print(f"✅  Saved: {filename}  ({size_kb} KB,  {doc.page} pages)")


if __name__ == "__main__":
    build_pdf()
