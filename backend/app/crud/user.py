from sqlmodel import Session, select
from app.models import User
from app.core.security import get_password_hash
from typing import Optional


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def get_user_by_username(session: Session, username: str) -> Optional[User]:
    statement = select(User).where(User.username == username)
    return session.exec(statement).first()


def create_user(session: Session, username: str, email: str, password: str, is_superuser: bool = False) -> User:
    # avoid creating duplicate users
    existing = get_user_by_email(session, email)
    if existing:
        return existing
    hashed = get_password_hash(password)
    user = User(username=username, email=email, hashed_password=hashed, is_superuser=is_superuser)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
