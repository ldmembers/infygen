# Context-Aware Personal Executive (CAPE)

A production-grade AI assistant that resolves **information fragmentation** by searching across Gmail, PDFs, CSV files, text notes, and personal memories — then synthesising a natural-language answer with a confidence score.

---

## Architecture

```
User Query
    │
    ▼
FastAPI Backend (main.py)
    │
    ├── Firebase JWT Auth  ────── every request verified
    │
    ├── Retrieval Service
    │      ├── Embed query (Ollama → nomic-embed-text)
    │      ├── Semantic Tool Router (cosine similarity vs tool descriptions)
    │      └── FAISS per-user index search
    │
    ├── Context Builder  ─────── formats retrieved chunks for LLM
    │
    ├── LLM Reasoning  ───────── OpenAI-compatible API (Qwen 2.5)
    │
    ├── Confidence Calculator  ── exp(-L2_distance) × 100
    │
    └── Timeline Builder  ──────── extracts and sorts date references
```

---

## Project Structure

```
backend/
├── main.py                    ← FastAPI app + lifespan
├── requirements.txt
├── .env.example               ← copy to .env and fill in
│
├── config/
│   ├── settings.py            ← typed Settings dataclass
│   └── env_loader.py          ← loads + validates .env vars
│
├── auth/
│   └── firebase_auth.py       ← Firebase JWT verification
│
├── api/
│   ├── routes_upload.py       ← POST /upload
│   ├── routes_query.py        ← POST /ask
│   ├── routes_memory.py       ← POST /remember
│   ├── routes_gmail.py        ← GET|POST /gmail/auth, POST /gmail/sync
│   └── routes_timeline.py     ← GET /timeline
│
├── ingestion/
│   ├── file_loader.py         ← orchestrates the full ingestion pipeline
│   ├── pdf_parser.py          ← pypdf text extraction
│   ├── csv_parser.py          ← row-to-text conversion
│   ├── text_parser.py         ← plain text loader
│   └── chunker.py             ← overlapping character chunks
│
├── embeddings/
│   └── embedding_service.py   ← Ollama nomic-embed-text HTTP client
│
├── vector_store/
│   └── faiss_index.py         ← per-user FAISS index + metadata
│
├── retrieval/
│   └── retrieval_service.py   ← full pipeline + confidence score
│
├── router/
│   └── semantic_tool_router.py ← embedding-based tool selection
│
├── reasoning/
│   ├── llm_service.py         ← OpenAI-compatible LLM call
│   └── context_builder.py     ← formats context for LLM + timestamp extraction
│
├── memory/
│   ├── memory_store.py        ← stores memory in FAISS + SQLite
│   └── memory_retrieval.py    ← retrieves memories
│
├── timeline/
│   └── timeline_builder.py    ← reconstructs chronological event timeline
│
├── gmail/
│   ├── gmail_auth.py          ← Google OAuth 2.0 flow + token storage
│   ├── gmail_fetcher.py       ← Gmail API message fetching
│   └── gmail_parser.py        ← extracts sender/subject/body/timestamp
│
├── storage/
│   └── object_storage.py      ← local filesystem object store
│
├── database/
│   ├── sqlite_db.py           ← SQLAlchemy engine + session factory
│   └── models.py              ← Document, Memory, GmailToken ORM models
│
├── utils/
│   ├── logger.py              ← centralised logging
│   ├── error_handlers.py      ← custom exceptions + FastAPI handlers
│   └── validators.py          ← file, query, memory validation
│
└── workers/
    └── ingestion_worker.py    ← background re-indexing worker
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10+ | `python --version` |
| Ollama        | [ollama.com](https://ollama.com) — local embeddings |
| Firebase project | [console.firebase.google.com](https://console.firebase.google.com) |
| LLM API key  | [OpenRouter](https://openrouter.ai) or any OpenAI-compatible provider |
| Google Cloud project | Only for Gmail integration |

---

## Setup

### 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start Ollama and pull the embedding model
```bash
ollama serve
ollama pull nomic-embed-text
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env — at minimum set LLM_API_KEY and FIREBASE_PROJECT_ID
```

### 4. Firebase setup
- Create a project at console.firebase.google.com
- Enable Authentication → Sign-in method → Email/Password (or Google)
- Project Settings → Service accounts → Generate new private key
- Save as `config/firebase_service_account.json`

### 5. (Optional) Gmail setup
- Go to console.cloud.google.com
- Enable the Gmail API
- Create OAuth 2.0 credentials (Desktop app)
- Download and save as `config/gmail_client_secret.json`

### 6. Start the server
```bash
uvicorn main:app --reload
# → http://localhost:8000
# → Docs: http://localhost:8000/docs
```

---

## API Reference

### Authentication
All endpoints require a Firebase ID token:
```
Authorization: Bearer <firebase_id_token>
```

### `POST /upload`
Upload PDF, CSV, or TXT files for indexing.
```bash
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer <token>" \
  -F "files=@report.pdf" \
  -F "files=@tasks.csv"
```

### `POST /ask`
Ask a natural-language question.
```json
// Request
{ "query": "What did we decide about event logistics?" }

// Response
{
  "answer": "Based on the emails and meeting notes, transport will use two buses...",
  "confidence": "87%",
  "sources": ["email", "pdf"],
  "result_count": 5
}
```

### `POST /remember`
Store a personal memory.
```json
{ "text": "The catering vendor is ABC Foods. Contact Sarah at 555-0101." }
```

### `GET /gmail/auth`
Get the Gmail OAuth URL.

### `POST /gmail/auth`
Exchange OAuth code for credentials.
```json
{ "code": "4/0AeaYS..." }
```

### `POST /gmail/sync`
Fetch and index Gmail messages.
```json
{ "max_emails": 50 }
```

### `GET /timeline?query=event+planning`
Return a chronological timeline for a topic.

### `GET /health`
Liveness check.

---

## Key Design Decisions

**Semantic Tool Routing** — Tools are described in natural language. The query and each description are embedded; tools with cosine similarity ≥ 0.35 are activated. This is more robust than keyword matching.

**Per-user FAISS shards** — Each user has their own `data/faiss/<user_id>/` directory. This prevents cross-user data leakage and allows independent index rebuilding.

**Exponential confidence scoring** — FAISS returns L2 distances. We convert with `exp(-distance)` to get [0,1] similarity, then average the top-3 and multiply by 100.

**SQLite + FAISS dual storage** — FAISS stores vectors for fast retrieval. SQLite stores structured metadata (user, source, timestamps) for queries, audit trails, and re-indexing.
