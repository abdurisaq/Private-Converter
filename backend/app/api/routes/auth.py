from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta
from sqlmodel import Session

from app.api.deps import get_db, CurrentUser
from app.schemas.auth import LoginRequest, Token
from app.core.security import authenticate_user, create_access_token, create_refresh_token
from app.core.config import settings

router = APIRouter()


@router.post("/login", response_model=Token)
def login(form_data: LoginRequest, db: Session = Depends(get_db)):
    # Frontend sends email and password
    user = authenticate_user(db, form_data.email, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token({"sub": str(user.id)}, expires_delta=access_token_expires)
    refresh = create_refresh_token({"sub": str(user.id)})
    # return format expected by frontend: { access, refresh, user }
    return {"access": token, "refresh": refresh, "user": {"id": str(user.id), "email": user.email, "username": user.username, "role": getattr(user, 'role', 'user')} }


@router.post("/register", response_model=dict)
def register(form_data: LoginRequest, db: Session = Depends(get_db)):
    """Register a new user. Uses username as email if an email isn't supplied.

    This checks both username and email for duplicates and creates a new user on success.
    """
    from app.crud import get_user_by_email, get_user_by_username, create_user

    # check duplicate username or email
    if get_user_by_username(db, form_data.email):
        raise HTTPException(status_code=400, detail="Username already registered")
    # allow user to use email as username (common pattern)
    if get_user_by_email(db, form_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = create_user(db, username=form_data.email.split('@')[0], email=form_data.email, password=form_data.password)
    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})
    return {"access": access, "refresh": refresh, "user": {"id": str(user.id), "email": user.email, "username": user.username, "role": getattr(user, 'role', 'user')}}



@router.get('/me', response_model=dict)
def me(current_user: CurrentUser):  # Remove "= Depends()"
    return {"id": str(current_user.id), "username": current_user.username, "email": current_user.email, "role": getattr(current_user, 'role', 'user')}
