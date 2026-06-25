from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import CurrentActiveSuperuser, SessionDep, CurrentUser, get_current_active_superuser
from app.models import User
from app.schemas.user import UserRead

router = APIRouter()


@router.get("/me", response_model=UserRead)
def read_me(current_user: CurrentUser):
    return current_user


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: str, session: Session = Depends(SessionDep)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/", response_model=list[UserRead])
def list_users(*, session: SessionDep, admin_user: CurrentActiveSuperuser):
    statement = select(User)
    return session.exec(statement).all()


@router.patch("/{user_id}/promote", response_model=UserRead)
def promote_user(*, user_id: str, session: SessionDep, admin_user: CurrentActiveSuperuser):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_superuser = True
    user.role = "admin"
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(*, user_id: str, session: SessionDep, admin_user: CurrentActiveSuperuser):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"status": "deleted"}
