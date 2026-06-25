from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy import BigInteger
from app.core.database import Base

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import uuid
from datetime import datetime


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    username: str = Field(index=True)
    email: str = Field(index=True)
    hashed_password: str
    role: str = Field(default="user", max_length=10)
    is_active: bool = Field(default=True)
    storage_quota: int = Field(default=10737418240)  # 10GB
    storage_used: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    is_superuser: bool = Field(default=False)

    # relationships
    jobs: List["Job"] = Relationship(back_populates="user")

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<User {self.email} ({self.role})>"