from datetime import datetime, timedelta
from typing import Optional
import jwt as pyjwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.core.config import settings
from app.models.user import User

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(db: Session, identifier: str, password: str):
    # identifier may be username or email
    statement = select(User).where((User.username == identifier) | (User.email == identifier))
    user = db.exec(statement).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = pyjwt.encode(to_encode, settings.JWT_SECRET_KEY or settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    # pyjwt returns string in v2+
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    # For now refresh tokens are just a longer-lived access token using same secret
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_access_token(data, expires_delta=delta)