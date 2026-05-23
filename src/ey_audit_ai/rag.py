from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class DocumentChunk:
    doc_id: str
    title: str
    text: str
    metadata: dict[str, str]


@dataclass
class RetrievalHit:
    chunk: DocumentChunk
    score: float
    match_terms: list[str]


class PolicyChunker:
    def chunk_directory(self, directory: Path) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        if not directory.exists():
            return chunks
        for path in sorted(directory.glob("*.md")):
            chunks.extend(self.chunk_file(path))
        return chunks

    def chunk_file(self, path: Path) -> list[DocumentChunk]:
        text = path.read_text(encoding="utf-8")
        title = path.stem.replace("_", " ").title()
        sections = re.split(r"\n(?=##\s+)", text)
        chunks: list[DocumentChunk] = []
        for i, section in enumerate(sections):
            clean = section.strip()
            if not clean:
                continue
            heading = clean.splitlines()[0].lstrip("# ").strip()[:80]
            chunks.append(
                DocumentChunk(
                    doc_id=f"{path.stem}:{i}",
                    title=heading or title,
                    text=clean,
                    metadata={"source": str(path), "policy_family": path.stem},
                )
            )
        return chunks


class HybridPolicyRetriever:
    """Small no-service hybrid retriever with lexical + semantic-like scoring.

    The semantic score uses character/word n-gram overlap so the demo works without
    a vector database. A Weaviate or pgvector adapter can replace this class.
    """

    def __init__(self, chunks: Iterable[DocumentChunk]):
        self.chunks = list(chunks)
        self.doc_freq = self._compute_doc_freq(self.chunks)
        self.num_docs = max(len(self.chunks), 1)

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalHit]:
        query_tokens = self._tokens(query)
        hits: list[RetrievalHit] = []
        for chunk in self.chunks:
            tokens = self._tokens(chunk.text)
            lexical = self._bm25_like(query_tokens, tokens)
            semantic = self._jaccard(self._ngrams(query.lower()), self._ngrams(chunk.text.lower()))
            score = (0.70 * lexical) + (0.30 * semantic)
            matches = sorted(set(query_tokens) & set(tokens))[:12]
            if score > 0:
                hits.append(RetrievalHit(chunk=chunk, score=round(score, 4), match_terms=matches))
        hits.sort(key=lambda h: h.score, reverse=True)
        return self._rerank(query_tokens, hits[: max(top_k * 3, top_k)])[:top_k]

    def _rerank(self, query_tokens: list[str], hits: list[RetrievalHit]) -> list[RetrievalHit]:
        important = {"duplicate", "approval", "sanction", "watchlist", "tax", "po", "threshold", "evidence", "invoice"}
        for hit in hits:
            boost = len(set(query_tokens) & important & set(hit.match_terms)) * 0.08
            hit.score = round(hit.score + boost, 4)
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits

    def _tokens(self, text: str) -> list[str]:
        stop = {"the", "and", "or", "of", "to", "a", "for", "with", "in", "on", "by", "is", "are", "be"}
        return [t for t in re.findall(r"[a-zA-Z0-9_]+", text.lower()) if t not in stop and len(t) > 1]

    def _compute_doc_freq(self, chunks: list[DocumentChunk]) -> dict[str, int]:
        df: dict[str, int] = {}
        for chunk in chunks:
            for token in set(self._tokens(chunk.text)):
                df[token] = df.get(token, 0) + 1
        return df

    def _bm25_like(self, query_tokens: list[str], doc_tokens: list[str]) -> float:
        if not query_tokens or not doc_tokens:
            return 0.0
        score = 0.0
        length_norm = 1.0 / math.sqrt(len(doc_tokens))
        for token in query_tokens:
            tf = doc_tokens.count(token)
            if tf == 0:
                continue
            idf = math.log((self.num_docs + 1) / (1 + self.doc_freq.get(token, 0))) + 1
            score += (tf * idf) * length_norm
        return score

    def _ngrams(self, text: str, n: int = 3) -> set[str]:
        compact = re.sub(r"\s+", " ", text)
        if len(compact) <= n:
            return {compact}
        return {compact[i : i + n] for i in range(len(compact) - n + 1)}

    def _jaccard(self, a: set[str], b: set[str]) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)
