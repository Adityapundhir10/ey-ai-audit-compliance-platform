from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


@dataclass
class WorkflowNode:
    name: str
    callable_path: str
    next_nodes: list[str]
    condition: str | None = None
    retries: int = 0


class YAMLWorkflowEngine:
    """Small YAML-driven workflow engine for demo and testing.

    It supports named nodes, Python callable paths, retry counts, and simple
    conditional transitions based on keys in workflow state.
    """

    def __init__(self, workflow_path: Path):
        self.workflow_path = workflow_path
        self.nodes = self._load(workflow_path)

    def run(self, initial_state: dict[str, Any]) -> dict[str, Any]:
        state = initial_state
        current = self.nodes["start"].next_nodes[0]
        visited = 0
        while current != "end":
            visited += 1
            if visited > 100:
                raise RuntimeError("Workflow exceeded max node visits")
            node = self.nodes[current]
            fn = self._resolve(node.callable_path)
            attempts = node.retries + 1
            last_error: Exception | None = None
            for _ in range(attempts):
                try:
                    state = fn(state)
                    last_error = None
                    break
                except Exception as exc:  # pragma: no cover
                    last_error = exc
            if last_error:
                raise last_error
            current = self._choose_next(node, state)
        return state

    def _choose_next(self, node: WorkflowNode, state: dict[str, Any]) -> str:
        if not node.next_nodes:
            return "end"
        if len(node.next_nodes) == 1:
            return node.next_nodes[0]
        if node.condition:
            key = node.condition.replace("state.", "")
            value = bool(state.get(key))
            return node.next_nodes[0] if value else node.next_nodes[1]
        return node.next_nodes[0]

    def _resolve(self, path: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
        module_name, attr = path.rsplit(":", 1)
        module = importlib.import_module(module_name)
        obj = getattr(module, attr)
        if isinstance(obj, type):
            obj = obj()
        if hasattr(obj, "run"):
            return obj.run
        return obj

    def _load(self, workflow_path: Path) -> dict[str, WorkflowNode]:
        if yaml is None:
            raise RuntimeError("PyYAML is required for YAML workflow loading")
        payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        nodes: dict[str, WorkflowNode] = {
            "start": WorkflowNode(name="start", callable_path="", next_nodes=[payload["start_at"]]),
            "end": WorkflowNode(name="end", callable_path="", next_nodes=[]),
        }
        for name, raw in payload["nodes"].items():
            nodes[name] = WorkflowNode(
                name=name,
                callable_path=raw["callable"],
                next_nodes=raw.get("next", ["end"]),
                condition=raw.get("condition"),
                retries=int(raw.get("retries", 0)),
            )
        return nodes
