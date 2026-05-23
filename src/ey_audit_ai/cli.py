from __future__ import annotations

import argparse
import json
from pathlib import Path
from pprint import pprint

from .agents import MultiAgentInvoiceAuditGraph
from .config import settings


def load_demo_payload() -> dict:
    path = Path("data/demo_payloads/invoice_workflow_request.json")
    return json.loads(path.read_text(encoding="utf-8"))


def run_demo(args: argparse.Namespace) -> None:
    if args.output:
        settings.evidence_output_dir.mkdir(parents=True, exist_ok=True)
    graph = MultiAgentInvoiceAuditGraph()
    result = graph.run(load_demo_payload())
    pprint(
        {
            "invoice_id": result["invoice"]["invoice_id"],
            "risk_score": result["risk_score"],
            "approval_route": result["approval"]["route"],
            "evidence_path": result["evidence_path"],
            "fraud_signals": [s["name"] for s in result["fraud_signals"]],
            "compliance_findings": [f["title"] for f in result["compliance_findings"]],
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="EY audit AI demo CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("run-demo")
    demo.add_argument("--output", default="outputs/evidence", help="Evidence output directory")
    demo.set_defaults(func=run_demo)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
