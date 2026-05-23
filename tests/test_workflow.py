import json
from pathlib import Path

from ey_audit_ai.agents import MultiAgentInvoiceAuditGraph


def test_demo_workflow_runs(tmp_path, monkeypatch):
    payload = json.loads(Path("data/demo_payloads/invoice_workflow_request.json").read_text())
    graph = MultiAgentInvoiceAuditGraph()
    result = graph.run(payload)
    assert result["invoice"]["invoice_id"] == "INV-2025-1042"
    assert result["risk_score"] >= 0.5
    assert result["approval"]["required"] is True
    assert Path(result["evidence_path"]).exists()
