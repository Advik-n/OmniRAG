import json
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import Session, delete, select

from app.core.catalog import DEFAULT_SYSTEM_PROMPT, ROLES, THEMES
from app.core.config import get_settings
from app.db.session import get_session
from app.models.entities import Chunk, Document, Interaction, Workspace
from app.rag.chunking import chunk_text
from app.rag.embeddings import embed
from app.rag.parser import parse_file
from app.rag.retrieval import search as rag_search
from app.services.ai import complete
from app.services.generation import format_context

router = APIRouter()

class ChatSettings(BaseModel):
    role: str = "General Assistant"
    theme: str = "Nebula"
    system_prompt: str = ""

class PromptIn(BaseModel):
    prompt: str = "Summarize the uploaded documents"
    top_k: int | None = None

class ExportIn(BaseModel):
    content: str
    format: str = "markdown"
    title: str = "OmniRAG Export"


def _default_workspace(session: Session) -> Workspace:
    workspace = session.exec(select(Workspace).order_by(Workspace.created_at)).first()
    if workspace:
        return workspace
    workspace = Workspace(name="OmniRAG Chat", description="Default document chat", role="General Assistant", theme="Nebula")
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace




def _all_results(session: Session, workspace_id: int, limit: int = 80) -> list[dict]:
    chunks = session.exec(select(Chunk).where(Chunk.workspace_id == workspace_id).order_by(Chunk.id).limit(limit)).all()
    return [
        {
            "score": 1.0,
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "text": chunk.text,
            "metadata": json.loads(chunk.metadata_json),
        }
        for chunk in chunks
    ]

def _source_metadata(results: list[dict]) -> list[dict]:
    sources = []
    for result in results:
        metadata = result.get("metadata", {})
        sources.append({
            "document_id": result["document_id"],
            "chunk_id": result["chunk_id"],
            "filename": metadata.get("filename", "document"),
            "page": metadata.get("page"),
            "slide": metadata.get("slide"),
            "sheet": metadata.get("sheet"),
            "score": result["score"],
            "preview": result["text"][:240],
        })
    return sources


@router.get("/health")
def health():
    return {"status": "ok", "name": "OmniRAG AI"}


@router.get("/config")
def config(session: Session = Depends(get_session)):
    settings = get_settings()
    workspace = _default_workspace(session)
    return {
        "roles": ROLES,
        "themes": THEMES,
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "workspace": workspace,
        "defaults": {
            "chunk_size": settings.default_chunk_size,
            "overlap": settings.default_chunk_overlap,
            "top_k": settings.default_top_k,
            "embedding_model": settings.embedding_model,
        },
    }


@router.put("/settings")
def update_settings(data: ChatSettings, session: Session = Depends(get_session)):
    workspace = _default_workspace(session)
    workspace.role = data.role if data.role in ROLES else "General Assistant"
    workspace.theme = data.theme if data.theme in THEMES else "Nebula"
    workspace.system_prompt = data.system_prompt
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


@router.get("/documents")
def list_documents(session: Session = Depends(get_session)):
    workspace = _default_workspace(session)
    return session.exec(select(Document).where(Document.workspace_id == workspace.id).order_by(Document.created_at.desc())).all()


@router.delete("/documents/{document_id}")
def delete_document(document_id: int, session: Session = Depends(get_session)):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(404, "document not found")
    session.exec(delete(Chunk).where(Chunk.document_id == document_id))
    session.delete(document)
    session.commit()
    if document.path:
        Path(document.path).unlink(missing_ok=True)
    return {"deleted": document_id}


@router.post("/documents")
def upload_documents(files: list[UploadFile] = File(...), session: Session = Depends(get_session)):
    workspace = _default_workspace(session)
    base = Path(get_settings().storage_dir) / "chat"
    base.mkdir(parents=True, exist_ok=True)
    processed = []
    for uploaded in files:
        safe_name = Path(uploaded.filename or "document").name
        file_path = base / safe_name
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(uploaded.file, buffer)
        document = Document(workspace_id=workspace.id, filename=safe_name, content_type=uploaded.content_type or "", path=str(file_path))
        session.add(document)
        session.commit()
        session.refresh(document)
        try:
            parsed = parse_file(str(file_path))
            chunk_count = 0
            for page in parsed["pages"]:
                for text in chunk_text(page["text"], get_settings().default_chunk_size, get_settings().default_chunk_overlap):
                    metadata = {key: value for key, value in page.items() if key != "text"} | {"filename": safe_name}
                    session.add(Chunk(workspace_id=workspace.id, document_id=document.id, text=text, embedding=json.dumps(embed(text)), metadata_json=json.dumps(metadata)))
                    chunk_count += 1
            if chunk_count == 0:
                raise ValueError("No readable text was found in this file.")
            document.status = "ready"
            document.pages = len(parsed["pages"])
            document.chunks = chunk_count
        except Exception as exc:
            document.status = f"failed: {exc}"
        session.add(document)
        session.commit()
        session.refresh(document)
        processed.append(document)
    return processed


@router.post("/chat")
async def chat(data: PromptIn, session: Session = Depends(get_session)):
    workspace = _default_workspace(session)
    results = rag_search(session, workspace.id, data.prompt, data.top_k or 12)
    prompt = f"Role: {workspace.role}\n{workspace.system_prompt or DEFAULT_SYSTEM_PROMPT}\n\nUser request: {data.prompt}"
    answer = await complete(prompt, format_context(results))
    sources = _source_metadata(results)
    interaction = Interaction(workspace_id=workspace.id, kind="chat", prompt=data.prompt, response=answer, metadata_json=json.dumps({"sources": sources}))
    session.add(interaction)
    session.commit()
    session.refresh(interaction)
    return {"id": interaction.id, "answer": answer, "sources": sources}


@router.post("/summarize")
async def summarize(data: PromptIn, session: Session = Depends(get_session)):
    workspace = _default_workspace(session)
    query = data.prompt or "Create a complete structured summary of all uploaded documents"
    results = _all_results(session, workspace.id, data.top_k or 80)
    if not results:
        results = rag_search(session, workspace.id, query, data.top_k or 20)
    answer = await complete(f"Create a neatly formatted structured summary. {query}", format_context(results))
    sources = _source_metadata(results)
    interaction = Interaction(workspace_id=workspace.id, kind="summary", prompt=query, response=answer, metadata_json=json.dumps({"sources": sources}))
    session.add(interaction)
    session.commit()
    session.refresh(interaction)
    return {"id": interaction.id, "summary": answer, "sources": sources}


@router.post("/answer-questions")
async def answer_questions(data: PromptIn, session: Session = Depends(get_session)):
    workspace = _default_workspace(session)
    results = _all_results(session, workspace.id, data.top_k or 120)
    if not results:
        results = rag_search(session, workspace.id, data.prompt or "answer all questions", data.top_k or 30)
    answer = await complete(f"Answer every question clearly from the uploaded content. {data.prompt}", format_context(results))
    sources = _source_metadata(results)
    interaction = Interaction(workspace_id=workspace.id, kind="answers", prompt=data.prompt, response=answer, metadata_json=json.dumps({"sources": sources}))
    session.add(interaction)
    session.commit()
    session.refresh(interaction)
    return {"id": interaction.id, "answer": answer, "sources": sources}


@router.get("/history")
def history(session: Session = Depends(get_session)):
    workspace = _default_workspace(session)
    return session.exec(select(Interaction).where(Interaction.workspace_id == workspace.id).order_by(Interaction.created_at.desc())).all()


@router.delete("/history/{interaction_id}")
def delete_history_item(interaction_id: int, session: Session = Depends(get_session)):
    interaction = session.get(Interaction, interaction_id)
    if not interaction:
        raise HTTPException(404, "history item not found")
    session.delete(interaction)
    session.commit()
    return {"deleted": interaction_id}


@router.delete("/history")
def clear_history(session: Session = Depends(get_session)):
    workspace = _default_workspace(session)
    session.exec(delete(Interaction).where(Interaction.workspace_id == workspace.id))
    session.commit()
    return {"deleted": "all"}
