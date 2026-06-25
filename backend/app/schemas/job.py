from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime


class JobBase(BaseModel):
    input_filename: str
    output_filename: str
    input_format: str
    output_format: str


class JobCreate(JobBase):
    file_size: Optional[int] = 0


class JobRead(JobBase):
    id: uuid.UUID
    status: str
    progress: int
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    tool_used: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobUpdate(BaseModel):
    status: Optional[str]
    progress: Optional[int]
