from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_rag_query_shape():
    client.post("/api/v1/demo/reset")
    res = client.post("/api/v1/rag/query", json={"query": "approval threshold for high value invoices", "top_k": 3})
    assert res.status_code == 200
    body = res.json()
    assert "answer" in body
    assert "citations" in body
