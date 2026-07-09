"""/auth — register, login, refresh, me. JWT access+refresh, bcrypt-hashed passwords.

Google OAuth is wired as an optional route that only activates when GOOGLE_CLIENT_ID/SECRET
are set (brief §4 "one OAuth provider"); without them the password flow is fully functional.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from app.db.database import get_db
from app.deps import get_current_user
from app.services.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest, db=Depends(get_db)) -> TokenResponse:
    from app.db.models import User

    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=req.email, password_hash=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return _tokens_for(user.id)


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)) -> TokenResponse:
    # OAuth2PasswordRequestForm uses `username`; we treat it as the email.
    from app.db.models import User

    user = db.query(User).filter(User.email == form.username).first()
    if not user or not user.password_hash or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return _tokens_for(user.id)


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest) -> TokenResponse:
    try:
        payload = decode_token(req.refresh_token, expected_type="refresh")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return _tokens_for(int(payload["sub"]))


@router.get("/me")
def me(user=Depends(get_current_user)) -> dict:
    return {"id": user.id, "email": user.email, "created_at": user.created_at.isoformat()}


def _tokens_for(user_id: int) -> TokenResponse:
    sub = str(user_id)
    return TokenResponse(access_token=create_access_token(sub), refresh_token=create_refresh_token(sub))
