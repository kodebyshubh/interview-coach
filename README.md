# AI Interview Coach

Upload your resume and a job description, get grilled by an AI, receive scored feedback on every answer, and walk away with a full performance report. No mock interviews, no fluff — just structured practice that surfaces where you're actually weak.

---

## How it works

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                             │
│  [Upload] ──▶ [Interview flow] ──▶ [Report] ──▶ [Analytics]     │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP (Next.js → FastAPI)
┌────────────────────────────▼────────────────────────────────────┐
│                  FASTAPI BACKEND (LangGraph)                     │
│                                                                 │
│  POST /upload                                                   │
│    PyPDF2 extracts text ──▶ chunked (400 chars / 50 overlap)    │
│    ──▶ ChromaDB collections: resume_chunks / jd_chunks          │
│    ──▶ PostgreSQL: Session row created                          │
│                                                                 │
│  POST /api/generate-questions          [Interviewer node]       │
│    ChromaDB retrieval (resume + JD context)                     │
│    Per question, 3 tiers: (1) Groq + MCP question-bank tool     │
│    bound — LLM genuinely chooses canned vs. fresh, (2) Gemini   │
│    primary / Groq fallback, (3) direct MCP bank call            │
│    8 questions: 3 behavioral · 3 technical · 1 situational      │
│                 1 resume deep-dive                              │
│    ──▶ PostgreSQL: Question rows + eval_logs rows                │
│                                                                 │
│  POST /api/submit-answer         [Evaluator → Interviewer node] │
│    Groq ─(fallback)─▶ Gemini ─(fallback)─▶ Ollama (local, last  │
│    resort — no external quota dependency)                       │
│    4-dim rubric: clarity · depth · relevance · examples         │
│    needs_probe computed in Python (overall_score < 6), never    │
│    trusted from the model's own JSON                            │
│    needs_probe ──▶ Gemini/Groq generates follow-up probe        │
│    is_probe=true circuit breaker prevents infinite loops        │
│    ──▶ PostgreSQL: Answer row + eval_logs rows                   │
│                                                                 │
│  POST /api/session/{id}/summarize          [Feedback node]      │
│    Gemini 2.0 Flash  ─(fallback)─▶  Groq                       │
│    Aggregated report: overall score · performance band          │
│    strengths · weaknesses + actions · resources · verdict       │
│    (probe answers excluded from scoring)                        │
│                                                                 │
│  GET /api/analytics/summary                                     │
│    eval_logs aggregations: score over time, latency by model,   │
│    score by question_type                                       │
└──────┬──────────────┬─────────────────┬──────────┬──────────────┘
       │              │                 │          │
┌──────▼─────┐ ┌──────▼──────┐  ┌───────▼───┐ ┌────▼─────┐
│ PostgreSQL │ │ ChromaDB    │  │  Groq /   │ │  Ollama  │
│   :5433    │ │  HTTP :8001 │  │  Gemini   │ │  (host)  │
│ sessions/  │ │ resume_chunks│  │ (hosted) │ │qwen2.5-  │
│ questions/ │ │ jd_chunks   │  │           │ │coder:7b  │
│ answers/   │ │             │  │           │ │          │
│ eval_logs  │ │             │  │           │ │          │
└────────────┘ └─────────────┘  └───────────┘ └──────────┘
```

Orchestrated by LangGraph (`backend/graph/`) — three nodes (Interviewer, Evaluator,
Feedback), state-machine routing by request stage, not inline route logic. One MCP
tool (`backend/mcp_tools/`) gives the Interviewer node a genuine choice between a
curated question bank and fresh LLM generation, using the real MCP protocol.

---

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 16, Tailwind CSS 4, framer-motion, Cormorant Garamond + Outfit fonts |
| Backend | Python 3.13, FastAPI (async), SQLAlchemy 2 + asyncpg |
| Orchestration | LangGraph — Interviewer / Evaluator / Feedback nodes |
| Tool calling | MCP (real protocol) — question-bank fetcher bound to Groq's `tools=` |
| Database | PostgreSQL 15 |
| Vector store | ChromaDB (HTTP client) |
| LLMs | Google Gemini 2.0 Flash · Groq / LLaMA-3.3-70B · Ollama / qwen2.5-coder:7b (local fallback) |
| PDF parsing | PyPDF2 |
| Tests | pytest-asyncio, httpx AsyncClient, SQLite in-memory — 60 tests, all offline |
| Infra | Docker Compose — Postgres, ChromaDB, backend, frontend all containerized |

---

## Local setup

### Option A — full stack via Docker (recommended)

```bash
cp backend/.env.example backend/.env   # fill in GEMINI_API_KEY, GROQ_API_KEY
docker-compose up -d --build
```

Builds and starts all four services: PostgreSQL (`:5433`), ChromaDB (`:8001`),
backend (`:8000`), frontend (`:3000`). Check `curl localhost:8000/health/llm` to
confirm the backend can reach Ollama on your host machine (see below).

### Option B — manual (local, non-Docker) dev

```bash
docker-compose up -d postgres chromadb   # just the data stores
```

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Fill in .env (see table below)

uvicorn main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev       # http://localhost:3000
```

### Ollama (required for the evaluator's local fallback tier)

Install [Ollama](https://ollama.com) and pull the model:
```bash
ollama pull qwen2.5-coder:7b
```
Ollama runs on your host machine, not as a Docker service. The containerized backend
reaches it via `host.docker.internal:11434` (set automatically in `docker-compose.yml`);
local (non-Docker) dev uses `localhost:11434` by default.

---

## Environment variables

Copy `backend/.env.example` → `backend/.env` and fill in:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string — e.g. `postgresql+asyncpg://coach:coach@localhost:5433/interviewdb` |
| `GEMINI_API_KEY` | ✅ | Google AI Studio key — question gen, probe gen, session summary |
| `GROQ_API_KEY` | ✅ | Groq key — answer evaluation (speed-critical path) |
| `CHROMA_HOST` | ✅ | ChromaDB host — `localhost` for local Docker |
| `CHROMA_PORT` | ✅ | ChromaDB port — `8001` for local Docker |
| `OLLAMA_HOST` | — | Ollama base URL — default `http://localhost:11434`; docker-compose overrides this to `http://host.docker.internal:11434` for the containerized backend |

Get keys:
- Gemini → [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- Groq → [console.groq.com/keys](https://console.groq.com/keys)

---

## API reference

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness |
| `GET` | `/health/db` | DB connectivity |
| `GET` | `/health/llm` | Ollama connectivity |
| `POST` | `/upload` | Upload resume + JD PDFs → returns `session_id` |
| `POST` | `/api/generate-questions` | Generate 8 LLM questions for session |
| `GET` | `/api/questions/{session_id}` | Fetch questions |
| `POST` | `/api/submit-answer` | Submit answer → evaluation + optional probe |
| `GET` | `/api/answers/{session_id}` | Fetch all evaluated answers |
| `POST` | `/api/session/{session_id}/summarize` | Full LLM report (call once at end) |
| `GET` | `/api/session/{session_id}/summary` | Score progress check (no LLM) |
| `GET` | `/api/analytics/summary` | eval_logs aggregations — score over time, latency by model, score by question_type |

---

## Running tests

```bash
cd backend
pip install -r requirements-test.txt
pytest tests/ -v
```

60 tests, ~2s. All LLM calls mocked, no network or subprocess dependency (the MCP tool
tests mock the Groq call and the MCP client functions rather than spawning a real
subprocess). SQLite in-memory replaces PostgreSQL.

---

## Project structure

```
interview-coach/
├── backend/
│   ├── agents/
│   │   ├── question_generator.py   # Gemini primary, Groq fallback; per-question call only
│   │   ├── evaluator.py            # Groq → Gemini → Ollama; needs_probe computed in Python
│   │   ├── probe_generator.py      # Gemini — follow-up for weak answers
│   │   └── summarizer.py           # Gemini primary, Groq fallback
│   ├── graph/
│   │   ├── state.py                 # InterviewState TypedDict
│   │   ├── nodes.py                 # Interviewer/Evaluator/Feedback nodes + MCP tool binding
│   │   └── build.py                 # Compiled LangGraph StateGraph
│   ├── mcp_tools/
│   │   ├── question_bank_server.py  # Real MCP server (FastMCP, stdio)
│   │   ├── question_bank_client.py  # Sync MCP client wrapper
│   │   └── question_bank.json       # Curated static question bank
│   ├── db/
│   │   ├── models.py               # Session, Question, Answer, EvalLog ORM models
│   │   ├── database.py             # Async engine + get_db dependency
│   │   └── init_db.py              # Table creation on startup
│   ├── rag/
│   │   ├── embedder.py             # Chunk + embed into ChromaDB
│   │   └── retriever.py            # Semantic search by session_id
│   ├── routes/
│   │   ├── questions.py
│   │   ├── answers.py
│   │   ├── summary.py
│   │   └── analytics.py            # eval_logs aggregations
│   ├── utils/pdf_parser.py
│   ├── tests/                      # pytest suite (60 tests)
│   ├── main.py
│   ├── Dockerfile
│   ├── next_steps.md               # Flagged, deliberately-unfixed follow-ups
│   └── requirements.txt            # fully pinned
├── frontend/
│   ├── app/
│   │   ├── page.tsx                # Upload / landing
│   │   ├── interview/[session_id]/ # Interview flow
│   │   ├── report/[session_id]/   # Final report
│   │   └── analytics/              # Eval-log analytics dashboard
│   ├── components/                 # EvaluationPanel, ScoreBar, ProbeCard
│   ├── lib/api.ts                  # All FastAPI calls
│   └── Dockerfile                  # Multi-stage, output: "standalone"
└── docker-compose.yml               # Postgres, ChromaDB, backend, frontend
```
