from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, Any
from sqlalchemy import Column, JSON
import uuid
from datetime import datetime


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional["User"] = Relationship()

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<AuditLog {self.action} - {self.user} ({self.created_at})>"
