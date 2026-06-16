"""
Generate a high-resolution System Architecture Diagram for AI Interview Evaluator.
Run:  python3 generate_architecture_diagram.py
Output: System_Architecture_Diagram.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe

fig, ax = plt.subplots(figsize=(20, 14))
ax.set_xlim(0, 20)
ax.set_ylim(0, 14)
ax.axis("off")
fig.patch.set_facecolor("#F8FAFC")

# ── Color palette ──────────────────────────────────────────────────────────────
C_BROWSER   = "#1E3A8A"   # deep navy   – client
C_UI        = "#2563EB"   # blue        – UI / Streamlit
C_CORE      = "#7C3AED"   # purple      – Core / Business logic
C_DB        = "#065F46"   # dark green  – Data access
C_EXTERNAL  = "#B45309"   # amber-brown – External API
C_STORAGE   = "#1E293B"   # slate       – Persistent storage
C_ARROW     = "#64748B"   # muted grey  – arrows
C_BG_LAYER  = "#EFF6FF"   # pale blue   – layer bands

TITLE_FONT  = {"fontsize": 10, "fontweight": "bold", "color": "white",
               "ha": "center", "va": "center"}
LABEL_FONT  = {"fontsize": 8.5, "color": "#1E293B", "ha": "center", "va": "center"}
SUB_FONT    = {"fontsize": 7.5, "color": "#475569", "ha": "center", "va": "center"}

# ── Helper functions ───────────────────────────────────────────────────────────

def box(ax, x, y, w, h, color, label, sublabel="", radius=0.18):
    """Draw a rounded rectangle box with a coloured header and white body."""
    # White body
    body = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor="white",
        edgecolor=color,
        linewidth=1.8,
        zorder=3,
    )
    ax.add_patch(body)
    # Coloured header bar (top 30 % of box)
    header_h = h * 0.38
    header = FancyBboxPatch(
        (x, y + h - header_h), w, header_h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=color,
        edgecolor=color,
        linewidth=0,
        zorder=4,
    )
    ax.add_patch(header)
    # Clip the bottom corners of the header to look right
    clip_fix = mpatches.Rectangle(
        (x, y + h - header_h), w, header_h * 0.5,
        facecolor=color, edgecolor="none", zorder=4,
    )
    ax.add_patch(clip_fix)
    # Label in header
    ax.text(x + w / 2, y + h - header_h / 2, label, zorder=5, **TITLE_FONT)
    # Sub-label in body
    if sublabel:
        ax.text(x + w / 2, y + h * 0.22, sublabel, zorder=5, wrap=True,
                **SUB_FONT)


def layer_band(ax, y_bot, height, label, color, alpha=0.07):
    """Draw a horizontal tinted band for a layer."""
    rect = mpatches.Rectangle(
        (0.3, y_bot), 19.4, height,
        facecolor=color, alpha=alpha, edgecolor=color,
        linewidth=0.8, linestyle="--", zorder=1,
    )
    ax.add_patch(rect)
    ax.text(0.08, y_bot + height / 2, label, fontsize=7.5, color=color,
            fontweight="bold", ha="center", va="center", rotation=90, zorder=2)


def arrow(ax, x1, y1, x2, y2, label="", color=C_ARROW, bidirectional=False):
    """Draw a styled arrow between two points."""
    style = "<|-|>" if bidirectional else "-|>"
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle=style, color=color, lw=1.5,
            connectionstyle="arc3,rad=0.0",
        ),
        zorder=6,
    )
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.15, my, label, fontsize=6.5, color=color,
                ha="left", va="center", zorder=7,
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                          edgecolor=color, linewidth=0.6, alpha=0.85))


# ── Title ──────────────────────────────────────────────────────────────────────
ax.text(10, 13.5, "AI Interview Evaluator — System Architecture",
        fontsize=17, fontweight="bold", color="#1E3A8A",
        ha="center", va="center", zorder=10)
ax.text(10, 13.1,
        "Streamlit · Google Gemini 1.5 Flash · SQLAlchemy · SQLite · ReportLab",
        fontsize=9.5, color="#64748B", ha="center", va="center", zorder=10)

# ── Layer 1 — Client (y: 12.0 – 12.6) ────────────────────────────────────────
layer_band(ax, 11.85, 0.8, "CLIENT", C_BROWSER, alpha=0.09)
box(ax, 6.5, 11.92, 7, 0.6, C_BROWSER, "Web Browser", "User Interface (localhost:8501)")

# ── Layer 2 — Streamlit App / UI Pages (y: 9.5 – 11.5) ───────────────────────
layer_band(ax, 9.3, 2.3, "UI LAYER", C_UI, alpha=0.06)
ui_boxes = [
    (0.6,  "app.py",         "Entry point\n& Sidebar"),
    (3.2,  "auth_page.py",   "Login /\nRegister"),
    (5.8,  "interview_\npage.py", "Interview\nFlow"),
    (8.4,  "results_\npage.py",  "Results &\nCharts"),
    (11.0, "history_\npage.py",  "History &\nLeaderboard"),
    (13.6, "admin_\npage.py",    "Admin\nDashboard"),
    (16.2, "style.css",      "Custom CSS\nTheme"),
]
for x, lbl, sub in ui_boxes:
    box(ax, x, 9.42, 2.45, 1.7, C_UI, lbl, sub)

# ── Layer 3 — Core / Business Logic (y: 6.8 – 9.0) ───────────────────────────
layer_band(ax, 6.6, 2.5, "CORE LAYER", C_CORE, alpha=0.05)
core_boxes = [
    (2.5,  "evaluator.py",          "AI Evaluation Engine\n225 rubric criteria"),
    (7.3,  "questions.py",          "Question Bank\n225 questions · 5 domains · 3 diff."),
    (12.1, "report_generator.py",   "Report Generator\nPDF (ReportLab) · CSV"),
    (16.6, "config.py",             "Configuration\nConstants & Secrets"),
]
for x, lbl, sub in core_boxes:
    box(ax, x, 6.7, 3.5, 1.8, C_CORE, lbl, sub)

# ── Layer 4 — Data Access (y: 4.2 – 6.5) ─────────────────────────────────────
layer_band(ax, 4.0, 2.4, "DATA ACCESS", C_DB, alpha=0.05)
db_boxes = [
    (4.0,  "db_handler.py",         "DB Operations\nCRUD · Auth · Stats"),
    (9.5,  "models.py",             "ORM Models\nCandidate · Interview\nInterviewQuestion"),
    (15.0, "database/__init__.py",  "Public API\nExports & Aliases"),
]
for x, lbl, sub in db_boxes:
    box(ax, x, 4.1, 3.8, 1.8, C_DB, lbl, sub)

# ── Layer 5 — External + Storage (y: 1.0 – 3.8) ──────────────────────────────
layer_band(ax, 0.9, 2.8, "EXTERNAL &\nSTORAGE", C_EXTERNAL, alpha=0.05)
# Google Gemini
box(ax, 1.0, 1.0, 4.5, 2.5, C_EXTERNAL, "Google Gemini API",
    "gemini-1.5-flash\nAI Evaluation · JSON scoring\nMock fallback mode")
# SQLite
box(ax, 7.5, 1.0, 5.0, 2.5, C_STORAGE,  "SQLite Database",
    "interview_evaluator.db\nCandidates · Interviews\nInterview Questions")
# Reports output
box(ax, 14.5, 1.0, 4.5, 2.5, C_CORE,    "File Output",
    "reports/ directory\nPDF reports · CSV exports")

# ── Arrows — vertical layer flows ─────────────────────────────────────────────

# Browser ↔ Streamlit
arrow(ax, 10, 11.85, 10, 11.12, "HTTP requests\n(Streamlit)", C_BROWSER, bidirectional=True)

# UI → Core
arrow(ax, 5.0, 9.42, 4.25, 8.5, "evaluate()", C_UI)
arrow(ax, 8.0, 9.42, 9.05, 8.5, "get_questions()", C_UI)
arrow(ax, 11.0, 9.42, 13.85, 8.5, "generate_report()", C_UI)

# Core → Data Access
arrow(ax, 5.8, 6.7, 5.9, 5.9, "query / save", C_CORE)
arrow(ax, 11.5, 6.7, 11.4, 5.9, "ORM models", C_CORE)

# Data Access → Storage
arrow(ax, 10, 4.1, 10, 3.5, "SQL / ORM", C_DB)

# Evaluator ↔ Gemini
arrow(ax, 4.0, 6.7, 3.25, 3.5, "REST API call\n(JSON prompt)", C_EXTERNAL, bidirectional=True)

# Report generator → File Output
arrow(ax, 15.85, 6.7, 16.75, 3.5, "write PDF/CSV", C_CORE)

# DB → SQLite
arrow(ax, 11.5, 4.1, 11.0, 3.5, "SQLAlchemy", C_DB)

# ── Session State annotation ───────────────────────────────────────────────────
session_box = FancyBboxPatch(
    (16.8, 9.42), 2.9, 1.7,
    boxstyle="round,pad=0.1,rounding_size=0.15",
    facecolor="#FEF3C7", edgecolor="#D97706", linewidth=1.5, zorder=3,
)
ax.add_patch(session_box)
ax.text(18.25, 10.32, "Streamlit\nSession State",
        fontsize=7.8, color="#92400E", ha="center", va="center",
        fontweight="bold", zorder=5)
ax.text(18.25, 9.78, "logged_in · candidate\ninterview_state\nquestions_list · evaluations",
        fontsize=6.5, color="#78350F", ha="center", va="center", zorder=5)

# ── Legend ─────────────────────────────────────────────────────────────────────
legend_items = [
    (C_BROWSER,  "Client Layer"),
    (C_UI,       "UI / Presentation Layer"),
    (C_CORE,     "Core / Business Logic Layer"),
    (C_DB,       "Data Access Layer"),
    (C_EXTERNAL, "External Services"),
    (C_STORAGE,  "Persistent Storage"),
]
lx, ly = 0.5, 0.55
for i, (c, label) in enumerate(legend_items):
    rect = mpatches.Rectangle((lx + i * 3.2, ly), 0.4, 0.22,
                               facecolor=c, edgecolor="white", zorder=8)
    ax.add_patch(rect)
    ax.text(lx + i * 3.2 + 0.55, ly + 0.11, label,
            fontsize=7.5, color="#334155", va="center", zorder=8)

plt.tight_layout(pad=0.5)
plt.savefig(
    "System_Architecture_Diagram.png",
    dpi=180,
    bbox_inches="tight",
    facecolor=fig.get_facecolor(),
)
print("✅  Saved: System_Architecture_Diagram.png")
plt.close()
