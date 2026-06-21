def chunk_text(text: str, size: int = 800, overlap: int = 150):
    words = text.split(); chunks=[]; start=0
    if not words: return []
    while start < len(words):
        end = min(len(words), start + size)
        chunks.append(" ".join(words[start:end]))
        if end == len(words): break
        start = max(0, end - overlap)
    return chunks
