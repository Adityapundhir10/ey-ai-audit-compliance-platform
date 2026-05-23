from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable


class TaskState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class WorkflowTask:
    task_id: str
    state: TaskState
    payload: dict[str, Any]
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    result: dict[str, Any] | None = None
    error: str | None = None


class InMemoryWorkflowQueue:
    """Async queue for local demo mode.

    Production deployments can replace this with Redis Queue, Celery, Kafka, or
    a managed workflow service. The API surface intentionally mirrors those
    systems: submit, mark running, mark success, mark failure, inspect task.
    """

    def __init__(self):
        self.tasks: dict[str, WorkflowTask] = {}
        self.queue: asyncio.Queue[str] = asyncio.Queue()

    async def submit(self, payload: dict[str, Any]) -> WorkflowTask:
        task = WorkflowTask(task_id=f"task-{uuid.uuid4().hex[:12]}", state=TaskState.QUEUED, payload=payload)
        self.tasks[task.task_id] = task
        await self.queue.put(task.task_id)
        return task

    def submit_sync(self, payload: dict[str, Any]) -> WorkflowTask:
        task = WorkflowTask(task_id=f"task-{uuid.uuid4().hex[:12]}", state=TaskState.QUEUED, payload=payload)
        self.tasks[task.task_id] = task
        return task

    def mark_running(self, task_id: str) -> None:
        task = self._get(task_id)
        task.state = TaskState.RUNNING
        task.updated_at = time.time()

    def mark_success(self, task_id: str, result: dict[str, Any]) -> None:
        task = self._get(task_id)
        task.state = TaskState.SUCCEEDED
        task.result = result
        task.updated_at = time.time()

    def mark_failed(self, task_id: str, error: str) -> None:
        task = self._get(task_id)
        task.state = TaskState.FAILED
        task.error = error
        task.updated_at = time.time()

    def get(self, task_id: str) -> WorkflowTask:
        return self._get(task_id)

    def serialize(self, task_id: str) -> dict[str, Any]:
        task = self._get(task_id)
        return {
            "task_id": task.task_id,
            "state": task.state.value,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "result": task.result,
            "error": task.error,
        }

    async def worker_loop(self, handler: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]) -> None:
        while True:
            task_id = await self.queue.get()
            self.mark_running(task_id)
            try:
                result = await handler(self.tasks[task_id].payload)
                self.mark_success(task_id, result)
            except Exception as exc:  # pragma: no cover
                self.mark_failed(task_id, str(exc))
            finally:
                self.queue.task_done()

    def _get(self, task_id: str) -> WorkflowTask:
        if task_id not in self.tasks:
            raise KeyError(f"Unknown task_id: {task_id}")
        return self.tasks[task_id]


class RedisQueueAdapter:
    """Boundary for Redis/Celery/RQ integration.

    The implementation is intentionally lightweight so the repository runs
    without Redis in local mode. In production, wrap RQ, Celery, Dramatiq, or
    Arq here and preserve the same submit/get contract.
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url

    def submit(self, topic: str, payload: dict[str, Any]) -> str:
        raise NotImplementedError("Connect redis/rq/celery here for production async execution.")
