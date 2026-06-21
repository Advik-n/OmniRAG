import re
from collections import Counter
from typing import Iterable

import httpx

from app.core.config import get_settings

STOPWORDS = {
    "the", "and", "for", "are", "that", "this", "with", "from", "have", "has", "was", "were",
    "you", "your", "will", "can", "not", "but", "all", "any", "into", "about", "what", "when",
    "where", "which", "while", "than", "then", "them", "they", "their", "there", "these", "those",
}


def _sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+|\n+", cleaned)
    return [p.strip(" •\t") for p in parts if len(p.strip()) > 35]


def _keywords(text: str, limit: int = 12) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text.lower())
    counts = Counter(w for w in words if w not in STOPWORDS)
    return [w for w, _ in counts.most_common(limit)]


def _rank_sentences(sentences: Iterable[str], query: str, limit: int = 8) -> list[str]:
    query_terms = set(_keywords(query, 20))
    corpus = " ".join(sentences)
    global_terms = set(_keywords(corpus, 30))
    scored: list[tuple[float, str]] = []
    for sentence in sentences:
        terms = set(_keywords(sentence, 30))
        score = len(terms & query_terms) * 3 + len(terms & global_terms) + min(len(sentence) / 220, 2)
        scored.append((score, sentence))
    return [s for _, s in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]]


def _extract_questions(text: str) -> list[str]:
    candidates = re.split(r"\n+|(?<=\?)\s+", text)
    questions = []
    for item in candidates:
        item = re.sub(r"^\s*(?:Q\.?\s*)?\d+[.)-]?\s*", "", item).strip()
        if item.endswith("?") or re.match(r"(?i)^(define|explain|describe|prove|show|find|list|state|compare|why|how|what|when|where|which)\b", item):
            if len(item) > 8:
                questions.append(item)
    return questions[:25]


def offline_answer(prompt: str, context: str) -> str:
    sentences = _sentences(context)
    if not sentences:
        return "## No document content found\n\nUpload a readable PDF, PPTX, DOCX, CSV, TXT, or Markdown file and try again."

    lower_prompt = prompt.lower()
    questions = _extract_questions(prompt)
    context_questions = _extract_questions(context) if "question" in lower_prompt or "answer all" in lower_prompt else []
    if questions or context_questions:
        selected_questions = questions or context_questions
        sections = ["## Answers"]
        for idx, question in enumerate(selected_questions, 1):
            support = _rank_sentences(sentences, question, 4)
            sections.append(f"### {idx}. {question}")
            sections.append("\n".join(f"- {line}" for line in support) if support else "- The uploaded content does not contain enough information to answer this confidently.")
        sections.append("\n## Source note\nAnswers are generated from the most relevant uploaded document passages available in the local index.")
        return "\n\n".join(sections)

    important = _rank_sentences(sentences, prompt, 10)
    key_terms = _keywords(context, 10)
    concise = important[:3]
    detailed = important[3:10]
    return "\n\n".join([
        "## Structured Summary",
        "### Executive Summary\n" + "\n".join(f"- {s}" for s in concise),
        "### Key Concepts\n" + "\n".join(f"- {term.title()}" for term in key_terms),
        "### Important Details\n" + ("\n".join(f"- {s}" for s in detailed) if detailed else "- No additional high-confidence details were found."),
        "### Revision Notes\n- Review the definitions, theorem statements, examples, and formulas in the uploaded file.\n- Ask a specific question to get a targeted answer from the same documents.",
    ])


async def complete(prompt: str, context: str = "") -> str:
    settings = get_settings()
    if settings.llm_provider == "openai" and settings.openai_api_key:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": settings.openai_model,
                    "messages": [
                        {"role": "system", "content": "Use the provided context. Return clean Markdown. Do not dump raw chunks."},
                        {"role": "user", "content": f"Context:\n{context}\n\nTask:\n{prompt}"},
                    ],
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    return offline_answer(prompt, context)
