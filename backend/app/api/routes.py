import json, os, shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from app.core.config import get_settings
from app.core.catalog import DEFAULT_SYSTEM_PROMPT, ROLES, THEMES, SUMMARY_MODES
from app.db.session import get_session
from app.models.entities import Workspace, Document, Chunk, Interaction
from app.rag.parser import parse_file
from app.rag.chunking import chunk_text
from app.rag.embeddings import embed
from app.rag.retrieval import search as rag_search
from app.services.ai import complete
from app.services.generation import format_context, generate_cards, generate_quiz, generate_mindmap

router=APIRouter()
class WorkspaceIn(BaseModel):
    name:str="Untitled Workspace"; description:str=""; role:str="General Assistant"; theme:str="Nebula"; system_prompt:str=""
class PromptIn(BaseModel):
    prompt:str; top_k:int|None=None; mode:str|None=None; difficulty:str|None=None
class ExportIn(BaseModel):
    content:str; format:str="markdown"; title:str="OmniRAG Export"

@router.get('/health')
def health(): return {"status":"ok","name":"OmniRAG AI"}
@router.get('/config')
def config():
    s=get_settings(); return {"roles":ROLES,"themes":THEMES,"summary_modes":SUMMARY_MODES,"system_prompt":DEFAULT_SYSTEM_PROMPT,"defaults":{"chunk_size":s.default_chunk_size,"overlap":s.default_chunk_overlap,"top_k":s.default_top_k,"embedding_model":s.embedding_model}}
@router.post('/workspaces')
def create_workspace(data:WorkspaceIn, session:Session=Depends(get_session)):
    ws=Workspace(**data.model_dump()); session.add(ws); session.commit(); session.refresh(ws); return ws
@router.get('/workspaces')
def list_workspaces(session:Session=Depends(get_session)): return session.exec(select(Workspace).order_by(Workspace.created_at.desc())).all()
@router.post('/workspaces/{workspace_id}/documents')
def upload_documents(workspace_id:int, files:list[UploadFile]=File(...), session:Session=Depends(get_session)):
    if not session.get(Workspace, workspace_id): raise HTTPException(404,"workspace not found")
    base=Path(get_settings().storage_dir)/str(workspace_id); base.mkdir(parents=True, exist_ok=True); out=[]
    for f in files:
        path=base/f.filename
        with path.open('wb') as buffer: shutil.copyfileobj(f.file, buffer)
        doc=Document(workspace_id=workspace_id, filename=f.filename, content_type=f.content_type or '', path=str(path)); session.add(doc); session.commit(); session.refresh(doc)
        parsed=parse_file(str(path)); count=0
        for page in parsed['pages']:
            for text in chunk_text(page['text'], get_settings().default_chunk_size, get_settings().default_chunk_overlap):
                meta={k:v for k,v in page.items() if k!='text'} | {"filename":f.filename}
                session.add(Chunk(workspace_id=workspace_id, document_id=doc.id, text=text, embedding=json.dumps(embed(text)), metadata_json=json.dumps(meta))); count+=1
        doc.status='ready'; doc.pages=len(parsed['pages']); doc.chunks=count; session.add(doc); session.commit(); session.refresh(doc); out.append(doc)
    return out
@router.get('/workspaces/{workspace_id}/documents')
def docs(workspace_id:int, session:Session=Depends(get_session)): return session.exec(select(Document).where(Document.workspace_id==workspace_id)).all()
@router.post('/workspaces/{workspace_id}/search')
def search(workspace_id:int, data:PromptIn, session:Session=Depends(get_session)): return {"results":rag_search(session, workspace_id, data.prompt, data.top_k or get_settings().default_top_k)}
@router.post('/workspaces/{workspace_id}/chat')
async def chat(workspace_id:int, data:PromptIn, session:Session=Depends(get_session)):
    results=rag_search(session, workspace_id, data.prompt, data.top_k or get_settings().default_top_k); answer=await complete(data.prompt, format_context(results)); session.add(Interaction(workspace_id=workspace_id, kind='chat', prompt=data.prompt, response=answer, metadata_json=json.dumps({"sources":results}))); session.commit(); return {"answer":answer,"sources":results}
@router.post('/workspaces/{workspace_id}/summaries')
async def summary(workspace_id:int, data:PromptIn, session:Session=Depends(get_session)):
    results=rag_search(session, workspace_id, data.prompt or 'summarize all documents', data.top_k or 12); answer=await complete(f"Generate a {data.mode or 'Detailed Notes'} summary using the universal summary format.", format_context(results)); session.add(Interaction(workspace_id=workspace_id, kind='summary', prompt=data.prompt, response=answer)); session.commit(); return {"summary":answer,"sources":results}
@router.post('/workspaces/{workspace_id}/flashcards')
async def flashcards(workspace_id:int, data:PromptIn, session:Session=Depends(get_session)): return {"flashcards":await generate_cards(rag_search(session, workspace_id, data.prompt or 'key facts', data.top_k or 10), data.difficulty or 'Medium')}
@router.post('/workspaces/{workspace_id}/quiz')
async def quiz(workspace_id:int, data:PromptIn, session:Session=Depends(get_session)): return {"quiz":await generate_quiz(rag_search(session, workspace_id, data.prompt or 'quiz topics', data.top_k or 10), data.difficulty or 'Adaptive')}
@router.post('/workspaces/{workspace_id}/mindmap')
async def mindmap(workspace_id:int, data:PromptIn, session:Session=Depends(get_session)): return {"mindmap":await generate_mindmap(rag_search(session, workspace_id, data.prompt or 'main topics', data.top_k or 10))}
@router.get('/workspaces/{workspace_id}/history')
def history(workspace_id:int, session:Session=Depends(get_session)): return session.exec(select(Interaction).where(Interaction.workspace_id==workspace_id).order_by(Interaction.created_at.desc())).all()
@router.post('/workspaces/{workspace_id}/export')
def export(workspace_id:int, data:ExportIn): return {"filename":f"{data.title}.{data.format}","content":data.content,"format":data.format}
