from pathlib import Path
from ey_audit_ai.rag import PolicyChunker, HybridPolicyRetriever


def test_policy_retrieval_finds_duplicate_invoice_policy():
    chunks = PolicyChunker().chunk_directory(Path("data/policies"))
    retriever = HybridPolicyRetriever(chunks)
    hits = retriever.retrieve("duplicate invoice vendor amount po", top_k=2)
    assert hits
    assert any("Duplicate" in hit.chunk.title or "duplicate" in hit.chunk.text.lower() for hit in hits)
