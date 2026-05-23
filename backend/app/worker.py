import asyncio
from app.db.session import SessionLocal, init_db
from app.schemas import WorkflowRunRequest
from app.services.queues import RedisQueue
from app.services.workflow import InvoiceWorkflowEngine


async def main():
    init_db()
    queue = RedisQueue()
    engine = InvoiceWorkflowEngine()
    print("Worker started. Waiting for invoice workflow jobs...")
    while True:
        payload = queue.pop(timeout=2)
        if not payload:
            await asyncio.sleep(1)
            continue
        db = SessionLocal()
        try:
            result = await engine.run(db, WorkflowRunRequest(**payload))
            print({"status": "processed", "workflow_id": result.workflow_id, "invoice_id": result.invoice_id})
        except Exception as exc:
            print({"status": "failed", "error": str(exc)})
        finally:
            db.close()


if __name__ == "__main__":
    asyncio.run(main())
