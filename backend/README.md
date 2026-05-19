# AI Interview Coach — Backend

FastAPI backend for the AI Interview Coach. Ingests resumes and job descriptions, stores sessions in PostgreSQL, and indexes chunked text in ChromaDB for semantic retrieval.

## Stack

- **Framework:** FastAPI (async)
- **Database:** PostgreSQL via SQLAlchemy (async) + asyncpg
- **Vector Store:** ChromaDB (HTTP client)
- **PDF Parsing:** PyPDF2

## Project Structure

```
backend/
├── main.py              # FastAPI app, routes, lifespan
├── schemas.py           # Pydantic request/response models
├── requirements.txt     # Python dependencies
├── .env.example         # Env var template
├── db/
│   ├── database.py      # Async engine & session factory
│   ├── models.py        # SQLAlchemy ORM models (Session, Question, Answer)
│   └── init_db.py       # Table creation on startup
├── rag/
│   ├── embedder.py      # ChromaDB collections, chunking, embedding
│   └── retriever.py     # Semantic search against ChromaDB
└── utils/
    └── pdf_parser.py    # PDF text extraction
```

## Prerequisites

- Python 3.11+
- Docker (for PostgreSQL and ChromaDB)

## Setup

```bash
# 1. Start infrastructure
docker compose up -d

# 2. Create virtual environment
python -m venv myenv
myenv\Scripts\activate      # Windows
# source myenv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env      # Windows
# cp .env.example .env       # Linux/Mac
```

Edit `.env` with your values:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (e.g. `postgresql://coach:coach@localhost:5433/interviewdb`) |
| `CHROMA_HOST` | ChromaDB host (e.g. `localhost`) |
| `CHROMA_PORT` | ChromaDB port (e.g. `8001`) |
| `GEMINI_API_KEY` | Google Gemini API key |
| `GROQ_API_KEY` | Groq API key |

## Run

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server starts at `http://localhost:8000`.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `GET` | `/health/db` | Database connectivity check |
| `POST` | `/upload` | Upload resume + JD PDFs, creates a session and embeds chunks |
| `POST` | `/debug/retrieve` | Retrieve relevant chunks for a query (debug) |
| `GET` | `/debug/session/{session_id}` | Get session metadata from PostgreSQL |

### POST /upload

Multipart form-data:

- `role` — target role (string)
- `resume_file` — PDF file
- `jd_file` — PDF file

Returns `session_id` and chunk counts.

## Database Models

- **Session** — id, created_at, role, jd_summary, status
- **Question** — id, session_id, text, order_index, source
- **Answer** — id, question_id, session_id, text, score, feedback, weak_topics, is_probe, created_at
