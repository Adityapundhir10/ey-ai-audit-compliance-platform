from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class InvoiceRecord(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    vendor_id: Mapped[str] = mapped_column(String(64), index=True)
    vendor_name: Mapped[str] = mapped_column(String(255))
    po_number: Mapped[str] = mapped_column(String(64), index=True)
    invoice_date: Mapped[str] = mapped_column(String(32))
    due_date: Mapped[str] = mapped_column(String(32))
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    subtotal: Mapped[float] = mapped_column(Float, default=0.0)
    tax: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(64), default="received")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    compliance_score: Mapped[float] = mapped_column(Float, default=1.0)
    extraction_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    structured_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    audit_events: Mapped[list["AuditEvent"]] = relationship("AuditEvent", back_populates="invoice")


class PurchaseOrderRecord(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    po_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    vendor_id: Mapped[str] = mapped_column(String(64), index=True)
    vendor_name: Mapped[str] = mapped_column(String(255))
    department: Mapped[str] = mapped_column(String(128))
    approved_amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    approved_by: Mapped[str] = mapped_column(String(128))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class VendorRiskRecord(Base):
    __tablename__ = "vendor_risk"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vendor_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(64), default="IN")
    risk_tier: Mapped[str] = mapped_column(String(32), default="low")
    duplicate_rate: Mapped[float] = mapped_column(Float, default=0.0)
    late_submission_rate: Mapped[float] = mapped_column(Float, default=0.0)
    historical_exception_rate: Mapped[float] = mapped_column(Float, default=0.0)
    average_invoice_amount: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class WorkflowStateRecord(Base):
    __tablename__ = "workflow_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workflow_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    invoice_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(64), default="created")
    current_agent: Mapped[str] = mapped_column(String(128), default="intake")
    state_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_pk: Mapped[int | None] = mapped_column(ForeignKey("invoices.id"), nullable=True)
    invoice_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(128), index=True)
    actor: Mapped[str] = mapped_column(String(128), default="system")
    decision: Mapped[str] = mapped_column(String(128), default="observed")
    reason: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    invoice: Mapped[InvoiceRecord] = relationship("InvoiceRecord", back_populates="audit_events")


class PolicyChunkRecord(Base):
    __tablename__ = "policy_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doc_id: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(255))
    section: Mapped[str] = mapped_column(String(128), default="general")
    text: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    embedding_hint: Mapped[str] = mapped_column(Text, default="")
