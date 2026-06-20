# 🏗️ System Architecture — AI Interview Evaluator

> Layered, loosely-coupled architecture. Each layer can be replaced independently.
> Render this on GitHub (auto-renders) or paste into https://mermaid.live

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontFamily": "Inter, Segoe UI, sans-serif",
    "fontSize": "14px",
    "lineColor": "#94a3b8",
    "primaryColor": "#EEF2FF",
    "primaryTextColor": "#1e293b",
    "primaryBorderColor": "#6C63FF"
  }
}}%%
flowchart TB

    %% ===================== CLIENT =====================
    subgraph CLIENT["🌐 CLIENT LAYER"]
        direction LR
        USER["👤 Candidate / Admin<br/><i>Web Browser · localhost:8501</i>"]
    end

    %% ===================== PRESENTATION =====================
    subgraph UI["🎨 PRESENTATION LAYER · Streamlit"]
        direction TB
        APP["🏠 <b>app.py</b><br/>Router + Home Dashboard + Auth Gate"]
        subgraph PAGES[" "]
            direction LR
            AUTH["🔑 auth_page<br/>Login / Register"]
            INT["🎤 interview_page<br/>Q&A State Machine"]
            RES["📊 results_page<br/>Scores + Charts"]
            HIST["📜 history_page<br/>History + Leaderboard"]
            ADM["⚙️ admin_page<br/>Admin Dashboard"]
        end
        APP --> PAGES
    end

    %% ===================== BUSINESS LOGIC =====================
    subgraph CORE["🧠 BUSINESS LOGIC LAYER · core/"]
        direction LR
        EVAL["🤖 <b>evaluator.py</b><br/>Rubric-based AI Scoring<br/>Retry + Mock Fallback"]
        QST["📚 questions.py<br/>Question Bank<br/>5 Domains × 3 Levels"]
        REP["📄 report_generator.py<br/>PDF + CSV Export"]
        MOCK["🛟 mock_evaluate<br/><i>offline fallback</i>"]
    end

    %% ===================== DATA ACCESS =====================
    subgraph DATA["🗄️ DATA ACCESS LAYER · database/"]
        direction LR
        DBH["🔧 <b>db_handler.py</b><br/>CRUD · Auth · Stats · Leaderboard"]
        MODEL["🧩 models.py<br/>SQLAlchemy ORM"]
    end

    %% ===================== EXTERNAL =====================
    subgraph EXT["☁️ EXTERNAL AI SERVICE"]
        GEMINI["✨ <b>Google Gemini 2.5 Flash</b><br/>generateContent REST API"]
    end

    %% ===================== STORAGE =====================
    subgraph STORE["💾 PERSISTENT STORAGE"]
        direction LR
        SQLITE[("🛢️ SQLite<br/>interview_evaluator.db")]
        T1["👥 candidates"]
        T2["📋 interviews"]
        T3["❓ interview_questions"]
    end

    %% ===================== FLOWS =====================
    USER <==>|"HTTP"| APP

    INT -->|"get questions"| QST
    INT -->|"evaluate answer"| EVAL
    RES -->|"export"| REP
    RES -->|"summary"| EVAL

    EVAL <==>|"prompt → JSON<br/>3× retry · backoff"| GEMINI
    EVAL -.->|"on failure"| MOCK

    AUTH --> DBH
    INT --> DBH
    RES --> DBH
    HIST --> DBH
    ADM --> DBH

    DBH --> MODEL
    MODEL --> SQLITE
    SQLITE --- T1
    SQLITE --- T2
    SQLITE --- T3

    %% ===================== STYLING =====================
    classDef clientL  fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0c4a6e;
    classDef uiL      fill:#eef2ff,stroke:#6C63FF,stroke-width:2px,color:#312e81;
    classDef coreL    fill:#ecfdf5,stroke:#10b981,stroke-width:2px,color:#064e3b;
    classDef dataL    fill:#fff7ed,stroke:#f59e0b,stroke-width:2px,color:#7c2d12;
    classDef extL     fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#831843;
    classDef storeL   fill:#f1f5f9,stroke:#475569,stroke-width:2px,color:#0f172a;
    classDef tableL   fill:#ffffff,stroke:#94a3b8,stroke-width:1px,color:#334155;

    class USER clientL;
    class APP,AUTH,INT,RES,HIST,ADM uiL;
    class EVAL,QST,REP,MOCK coreL;
    class DBH,MODEL dataL;
    class GEMINI extL;
    class SQLITE storeL;
    class T1,T2,T3 tableL;
```

## Layer Responsibilities

| Layer | Files | Responsibility |
|---|---|---|
| 🌐 **Client** | Browser | Candidate & admin interact via web UI |
| 🎨 **Presentation** | `app.py`, `ui/*` | Streamlit pages, routing, session state |
| 🧠 **Business Logic** | `core/*` | AI scoring, question bank, report generation |
| 🗄️ **Data Access** | `database/*` | CRUD, auth, stats via SQLAlchemy ORM |
| ☁️ **External** | Gemini API | AI evaluation of answers (with retry + fallback) |
| 💾 **Storage** | SQLite | `candidates`, `interviews`, `interview_questions` |

**Key resilience flow:** `evaluator.py` → Gemini (3× retry, exponential backoff) → on total failure → `mock_evaluate` → app never crashes.
