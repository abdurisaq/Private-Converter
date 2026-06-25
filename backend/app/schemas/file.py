from pydantic import BaseModel
from typing import Optional


class UploadResponse(BaseModel):
    filename: str
    size: Optional[int]
 