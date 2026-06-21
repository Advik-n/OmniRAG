# OmniRAG AI

Universal Document Intelligence Platform for ingesting documents, indexing them with retrieval augmented generation, and generating chats, summaries, flashcards, quizzes, mind maps, timelines, and exports.

## Features

- **Workspace-first UX**: create isolated workspaces with document collections and interaction history.
- **Universal ingestion**: PDF, DOCX, PPTX, XLSX, CSV, TXT, and Markdown parsing with extensible parser registry.
- **RAG pipeline**: cleaning, token-aware chunking, metadata extraction, embeddings, FAISS-like vector search, keyword search, and reranking hooks.
- **Provider-independent LLM layer**: OpenAI-compatible, Ollama/local, custom endpoint, and deterministic offline fallback.
- **Document intelligence tools**: chat with citations, multiple summary modes, flashcards, quizzes, mind maps, semantic search, history, and exports.
- **Configurable roles and prompts**: built-in roles plus custom system prompts without code changes.
- **Themeable workspace**: Nebula, Aurora, Midnight, Cyberpunk, Sakura, Solar, Ocean, and Matrix themes.

## Tech Stack

### Frontend
- React 18
- Vite
- TypeScript
- Tailwind CSS
- Framer Motion
- Zustand
- React Router
- Lucide React icons

### Backend
- FastAPI
- SQLModel / SQLite by default
- Pydantic settings
- BackgroundTasks for local worker execution
- Pluggable parsers: PyMuPDF, python-docx, python-pptx, openpyxl, pandas
- Local deterministic embeddings with optional sentence-transformers integration
- Optional FAISS support with pure Python fallback

### Production Integrations
- Redis and Celery-ready worker module
- PostgreSQL-ready database URL configuration
- Docker Compose for frontend, backend, Redis, and Postgres

## Repository Structure

```text
OmniRAG/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/          # REST routers
│   │   ├── core/         # settings, roles, themes, prompts
│   │   ├── db/           # SQLModel database setup
│   │   ├── models/       # database models
│   │   ├── rag/          # parsing, chunking, embeddings, retrieval
│   │   └── services/     # workspace, AI, export, generation services
│   ├── tests/
│   └── requirements.txt
├── frontend/             # React AI workspace
│   ├── src/
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at `http://localhost:8000` and OpenAPI docs at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

The web app is available at `http://localhost:5173`.

### 3. Docker Compose

```bash
docker compose up --build
```

Frontend: `http://localhost:5173`  
Backend: `http://localhost:8000`

## Configuration

Copy the example environment file and edit it as needed:

```bash
cp backend/.env.example backend/.env
```

Important settings:

| Variable | Default | Description |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./omnirag.db` | SQLite or PostgreSQL database URL. |
| `STORAGE_DIR` | `./storage` | Uploaded files and generated exports. |
| `EMBEDDING_MODEL` | `BAAI/bge-base-en` | Logical embedding model name. |
| `LLM_PROVIDER` | `offline` | `offline`, `openai`, `ollama`, or `custom`. |
| `OPENAI_API_KEY` | empty | Used when `LLM_PROVIDER=openai`. |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI chat model. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint. |
| `CUSTOM_LLM_ENDPOINT` | empty | OpenAI-compatible custom endpoint. |
| `DEFAULT_CHUNK_SIZE` | `800` | Chunk size in approximate tokens. |
| `DEFAULT_CHUNK_OVERLAP` | `150` | Chunk overlap in approximate tokens. |
| `DEFAULT_TOP_K` | `5` | Retrieval result count. |

## API Overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Health check. |
| `GET` | `/api/config` | Roles, themes, providers, summary modes, defaults. |
| `POST` | `/api/workspaces` | Create workspace. |
| `GET` | `/api/workspaces` | List workspaces. |
| `POST` | `/api/workspaces/{id}/documents` | Upload and process documents. |
| `GET` | `/api/workspaces/{id}/documents` | List documents. |
| `POST` | `/api/workspaces/{id}/chat` | Ask document-aware questions. |
| `POST` | `/api/workspaces/{id}/summaries` | Generate citation-backed summaries. |
| `POST` | `/api/workspaces/{id}/search` | Hybrid semantic and keyword search. |
| `POST` | `/api/workspaces/{id}/flashcards` | Generate flashcards. |
| `POST` | `/api/workspaces/{id}/quiz` | Generate quizzes. |
| `POST` | `/api/workspaces/{id}/mindmap` | Generate hierarchical mind maps. |
| `GET` | `/api/workspaces/{id}/history` | Persistent interaction history. |
| `POST` | `/api/workspaces/{id}/export` | Export content as Markdown, HTML, JSON, CSV, DOCX, or PDF-like text. |

## Usage Flow

1. Create a workspace.
2. Upload one or more supported documents.
3. OmniRAG detects file types, parses content, chunks text, extracts metadata, generates embeddings, and stores searchable chunks.
4. Use Chat, Summary, Search, Flashcards, Quiz, Mind Maps, and History from the sidebar.
5. Export generated artifacts in your preferred format.

## Notes on Production Deployment

- Use PostgreSQL by setting `DATABASE_URL=postgresql+psycopg://...`.
- Use Redis/Celery for distributed processing when ingestion volume grows.
- Replace the deterministic embedding fallback with sentence-transformers or an external embedding API.
- Configure API keys through environment variables or a managed secret store.
- Put the backend behind TLS and configure CORS with your production frontend origin.
- Enable persistent volumes for `STORAGE_DIR` and database data.

## Development Commands

```bash
# Backend tests
cd backend && pytest

# Frontend type-check and build
cd frontend && npm run build

# Docker
 docker compose up --build
```
