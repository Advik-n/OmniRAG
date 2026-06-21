# OmniRAG AI

OmniRAG is a focused document chat and summarization app. Upload your learning material, notes, PDFs, PPTX slides, DOCX files, spreadsheets, CSV, Markdown, or TXT files, then ask for a clean summary or ask it to answer questions from uploaded content.

The current product is intentionally simple: **Chat**, **History**, and **Settings**. There is no confusing workspace switching and no unused flashcard/quiz/mind-map UI.

## What It Does

- Upload and index documents in one chat-like space.
- Summarize uploaded content in structured Markdown.
- Answer questions using retrieved document passages.
- Upload a content document plus a question paper and ask OmniRAG to answer the questions.
- Keep chat history and delete individual old chats or clear all history.
- Change themes and assistant roles from Settings.
- Delete uploaded documents and their indexed chunks.
- Run locally with deterministic offline generation, or configure OpenAI for stronger responses.

## Supported Uploads

- PDF
- PPTX / PPT
- DOCX / DOC
- XLSX / XLS
- CSV
- TXT
- Markdown

PPTX parsing includes slide text, tables, notes where available, and an XML fallback for unusual slide decks.

## Tech Stack

### Backend

- FastAPI
- SQLModel + SQLite by default
- PyMuPDF for PDF text
- python-pptx for PowerPoint
- python-docx for Word documents
- openpyxl for spreadsheets
- Local deterministic embeddings
- Hybrid semantic/keyword retrieval
- OpenAI-compatible LLM path plus offline fallback

### Frontend

- React
- TypeScript
- Vite
- Lucide icons
- Plain CSS theme system

### DevOps

- Dockerfiles for frontend and backend
- Docker Compose with backend, frontend, Redis, and Postgres services
- `.env.example` for backend configuration

## Project Structure

```text
OmniRAG/
├── backend/
│   ├── app/
│   │   ├── api/routes.py       # REST API for upload, chat, summarize, history, settings
│   │   ├── core/               # settings, roles, themes, default prompt
│   │   ├── db/session.py       # SQLModel engine/session setup
│   │   ├── models/entities.py  # Workspace, Document, Chunk, Interaction tables
│   │   ├── rag/                # parsing, chunking, embeddings, retrieval
│   │   └── services/           # answer generation helpers
│   ├── tests/test_api.py       # health + PPTX upload/summarize/history regression tests
│   └── requirements.txt
├── frontend/
│   ├── src/App.tsx             # simplified Chat / History / Settings UI
│   └── src/style.css           # theme-aware app styling
├── docker-compose.yml
└── README.md
```

## Run Locally

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173`

### Docker

```bash
docker compose up --build
```

Frontend: `http://localhost:5173`  
Backend: `http://localhost:8000`

## Configuration

Copy the example environment file:

```bash
cp backend/.env.example backend/.env
```

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./omnirag.db` | Database connection string. |
| `STORAGE_DIR` | `./storage` | Uploaded file storage. |
| `EMBEDDING_MODEL` | `BAAI/bge-base-en` | Logical embedding model label. |
| `LLM_PROVIDER` | `offline` | Use `offline` or `openai`. |
| `OPENAI_API_KEY` | empty | Required when `LLM_PROVIDER=openai`. |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name. |
| `DEFAULT_CHUNK_SIZE` | `800` | Approximate words per chunk. |
| `DEFAULT_CHUNK_OVERLAP` | `150` | Approximate overlap between chunks. |
| `DEFAULT_TOP_K` | `5` | Default retrieval count. |

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Health check. |
| `GET` | `/api/config` | Current themes, roles, defaults, and active settings. |
| `PUT` | `/api/settings` | Save role, theme, and custom system prompt. |
| `GET` | `/api/documents` | List uploaded documents. |
| `POST` | `/api/documents` | Upload and index one or more files. |
| `DELETE` | `/api/documents/{id}` | Delete a document and its chunks. |
| `POST` | `/api/chat` | Ask a custom question. |
| `POST` | `/api/summarize` | Generate a structured summary. |
| `POST` | `/api/answer-questions` | Answer questions from uploaded content. |
| `GET` | `/api/history` | List previous chats/summaries/answers. |
| `DELETE` | `/api/history/{id}` | Delete one old chat. |
| `DELETE` | `/api/history` | Clear all history. |

The public API intentionally uses the simple document-chat endpoints above; no workspace routes are required by the frontend.

## Recommended Use

1. Start backend and frontend.
2. Upload your content document, such as lecture slides or notes.
3. Optional: upload a question PDF or TXT file.
4. Click **Summarize** for a structured overview.
5. Click **Answer Questions** or type a specific question and click **Ask**.
6. Use **History** to review, delete one chat, or clear all old chats.
7. Use **Settings** to change role and theme.

## Tests

```bash
cd backend && .venv/bin/python -m pytest tests -q
cd frontend && npm run build
```
