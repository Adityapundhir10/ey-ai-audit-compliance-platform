from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class AuditRepository:
    def __init__(self, sqlite_path: Path):
        self.sqlite_path = sqlite_path
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id TEXT NOT NULL,
                    evidence_id TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    approval_route TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def save_run(self, invoice_id: str, evidence_id: str, risk_score: float, approval_route: str, payload: dict[str, Any]) -> None:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute(
                "INSERT INTO workflow_runs(invoice_id, evidence_id, risk_score, approval_route, payload_json) VALUES (?, ?, ?, ?, ?)",
                (invoice_id, evidence_id, risk_score, approval_route, json.dumps(payload, default=str)),
            )

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        with sqlite3.connect(self.sqlite_path) as conn:
            rows = conn.execute(
                "SELECT invoice_id, evidence_id, risk_score, approval_route, created_at FROM workflow_runs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "invoice_id": row[0],
                "evidence_id": row[1],
                "risk_score": row[2],
                "approval_route": row[3],
                "created_at": row[4],
            }
            for row in rows
        ]
