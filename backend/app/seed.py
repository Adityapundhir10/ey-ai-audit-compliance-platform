import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import SessionLocal, init_db
from app.models import InvoiceRecord, PurchaseOrderRecord, VendorRiskRecord, WorkflowStateRecord, AuditEvent
from app.services.rag import load_policy_documents


def seed_database(db: Session, reset: bool = False) -> None:
    settings = get_settings()
    if reset:
        db.query(AuditEvent).delete()
        db.query(WorkflowStateRecord).delete()
        db.query(InvoiceRecord).delete()
        db.query(PurchaseOrderRecord).delete()
        db.query(VendorRiskRecord).delete()
        db.commit()

    data_dir = settings.data_dir
    po_path = data_dir / "purchase_orders.json"
    vendors_path = data_dir / "vendors.json"
    invoices_path = data_dir / "sample_structured_invoices.json"

    if db.query(PurchaseOrderRecord).count() == 0 and po_path.exists():
        for row in json.loads(po_path.read_text(encoding="utf-8")):
            db.add(PurchaseOrderRecord(**row))

    if db.query(VendorRiskRecord).count() == 0 and vendors_path.exists():
        for row in json.loads(vendors_path.read_text(encoding="utf-8")):
            db.add(VendorRiskRecord(**row))

    if db.query(InvoiceRecord).count() == 0 and invoices_path.exists():
        for row in json.loads(invoices_path.read_text(encoding="utf-8")):
            db.add(InvoiceRecord(**row))

    db.commit()
    load_policy_documents(db)


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed_database(db, reset=False)
        print("Database seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
