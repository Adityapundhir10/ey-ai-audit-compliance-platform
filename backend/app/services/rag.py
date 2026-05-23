import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models import PolicyChunkRecord

TOKEN_RE = re.compile(r"[a-zA-Z0-9_/-]+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


@dataclass
class RetrievedChunk:
    doc_id: str
    title: str
    section: str
    text: str
    score: float
    metadata: dict


class LocalHybridRetriever:
    """Lightweight hybrid retrieval.

    It uses lexical TF-IDF style scoring plus metadata boosts. A production system
    can switch to Weaviate, Azure AI Search, or pgvector without changing callers.
    """

    def __init__(self, db: Session):
        self.db = db

    def search(self, query: str, top_k: int = 5, filters: Dict[str, Any] | None = None) -> List[RetrievedChunk]:
        filters = filters or {}
        rows = self.db.query(PolicyChunkRecord).all()
        query_tokens = tokenize(query)
        scored: list[RetrievedChunk] = []
        for row in rows:
            if filters:
                skip = False
                for k, v in filters.items():
                    if row.metadata_json.get(k) != v:
                        skip = True
                        break
                if skip:
                    continue
            text_tokens = tokenize(row.text + " " + row.title + " " + row.section)
            score = self._score(query_tokens, text_tokens)
            if query.lower() in row.text.lower():
                score += 0.2
            if any(tok in row.section.lower() for tok in query_tokens):
                score += 0.1
            scored.append(
                RetrievedChunk(
                    doc_id=row.doc_id,
                    title=row.title,
                    section=row.section,
                    text=row.text,
                    score=round(score, 4),
                    metadata=row.metadata_json or {},
                )
            )
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]

    def _score(self, query_tokens: list[str], text_tokens: list[str]) -> float:
        if not query_tokens or not text_tokens:
            return 0.0
        text_counts = Counter(text_tokens)
        text_len = len(text_tokens)
        score = 0.0
        for tok in query_tokens:
            tf = text_counts[tok] / text_len
            if tf > 0:
                score += 0.5 + math.log1p(tf * 100)
        overlap = len(set(query_tokens) & set(text_tokens)) / max(len(set(query_tokens)), 1)
        return score + overlap


class ComplianceRAGService:
    def __init__(self, db: Session):
        self.retriever = LocalHybridRetriever(db)

    def answer(self, query: str, top_k: int = 5, filters: Dict[str, Any] | None = None) -> dict:
        chunks = self.retriever.search(query, top_k=top_k, filters=filters)
        if not chunks:
            return {"answer": "No relevant policy evidence found.", "citations": [], "confidence": 0.0}
        top = chunks[0]
        answer = f"Most relevant policy: {top.title} / {top.section}. {self._compress(top.text)}"
        citations = [
            {
                "doc_id": c.doc_id,
                "title": c.title,
                "section": c.section,
                "score": c.score,
                "snippet": self._compress(c.text, max_chars=240),
                "metadata": c.metadata,
            }
            for c in chunks
        ]
        confidence = min(0.95, 0.35 + sum(c.score for c in chunks[:3]) / 10)
        return {"answer": answer, "citations": citations, "confidence": round(confidence, 3)}

    def _compress(self, text: str, max_chars: int = 320) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        return text if len(text) <= max_chars else text[: max_chars - 3] + "..."


def chunk_policy_text(doc_id: str, title: str, text: str) -> list[dict]:
    sections = []
    current_title = "general"
    buffer: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if buffer:
                sections.append({"section": current_title, "text": "\n".join(buffer).strip()})
                buffer = []
            current_title = line.replace("## ", "").strip().lower().replace(" ", "-")
        else:
            buffer.append(line)
    if buffer:
        sections.append({"section": current_title, "text": "\n".join(buffer).strip()})

    chunks = []
    for idx, sec in enumerate(sections):
        words = sec["text"].split()
        if not words:
            continue
        for start in range(0, len(words), 120):
            piece = " ".join(words[start : start + 160])
            chunks.append(
                {
                    "doc_id": f"{doc_id}-{idx}-{start}",
                    "title": title,
                    "section": sec["section"],
                    "text": piece,
                    "metadata": {"source_doc": doc_id, "chunk_index": idx, "domain": "finance_compliance"},
                    "embedding_hint": " ".join(tokenize(title + " " + sec["section"]))[:512],
                }
            )
    return chunks


def load_policy_documents(db: Session, policy_dir: Path | None = None) -> int:
    settings = get_settings()
    policy_dir = policy_dir or settings.data_dir / "policies"
    count = 0
    db.query(PolicyChunkRecord).delete()
    for path in policy_dir.glob("*.md"):
        title = path.stem.replace("_", " ").title()
        text = path.read_text(encoding="utf-8")
        for chunk in chunk_policy_text(path.stem, title, text):
            db.add(PolicyChunkRecord(**chunk))
            count += 1
    db.commit()
    return count
