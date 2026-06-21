from app.services.ai import complete

def format_context(results):
    return "\n".join(f"[doc:{r['document_id']} chunk:{r['chunk_id']}] {r['text']}" for r in results)

async def generate_cards(results, difficulty="Medium"):
    ctx=format_context(results)
    return await complete(f"Create 10 {difficulty} flashcards as Q/A bullets.", ctx)
async def generate_quiz(results, difficulty="Adaptive"):
    return await complete(f"Create a {difficulty} quiz with MCQ, true/false, fill blank, short and long answer questions.", format_context(results))
async def generate_mindmap(results):
    return await complete("Create a hierarchical mind map with topics, subtopics, and relationships.", format_context(results))
