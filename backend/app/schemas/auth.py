from pydantic import BaseModel
from typing import Optional
import uuid


class LoginRequest(BaseModel):
    email: str
    password: str


class UserInfo(BaseModel):
    id: str
    email: str
    username: str
    role: str


class Token(BaseModel):
    access: str
    refresh: str
    user: UserInfo


