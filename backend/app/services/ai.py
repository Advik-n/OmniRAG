import httpx
from app.core.config import get_settings

async def complete(prompt: str, context: str = "") -> str:
    s=get_settings()
    if s.llm_provider == "openai" and s.openai_api_key:
        async with httpx.AsyncClient(timeout=60) as client:
            r=await client.post("https://api.openai.com/v1/chat/completions",headers={"Authorization":f"Bearer {s.openai_api_key}"},json={"model":s.openai_model,"messages":[{"role":"system","content":"Answer with citations from context."},{"role":"user","content":f"Context:\n{context}\n\nTask:\n{prompt}"}]})
            r.raise_for_status(); return r.json()["choices"][0]["message"]["content"]
    if context:
        lines=context.splitlines()[:10]
        return "Offline grounded response:\n" + "\n".join(f"- {line[:300]}" for line in lines) + "\n\nCitations are listed below in the source panel."
    return "Offline response: upload documents or configure an LLM provider for richer generation."
