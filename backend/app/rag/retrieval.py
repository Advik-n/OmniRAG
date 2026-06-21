import json
from sqlmodel import Session, select
from app.models.entities import Chunk
from app.rag.embeddings import embed, cosine

def search(session: Session, workspace_id: int, query: str, top_k: int = 5):
    q=embed(query); terms=set(query.lower().split()); scored=[]
    for ch in session.exec(select(Chunk).where(Chunk.workspace_id==workspace_id)).all():
        v=json.loads(ch.embedding); keyword=sum(1 for t in terms if t in ch.text.lower())/(len(terms) or 1)
        score=0.75*cosine(q,v)+0.25*keyword
        scored.append((score,ch))
    scored.sort(key=lambda x:x[0], reverse=True)
    return [{"score":round(s,4),"chunk_id":c.id,"document_id":c.document_id,"text":c.text,"metadata":json.loads(c.metadata_json)} for s,c in scored[:top_k]]
