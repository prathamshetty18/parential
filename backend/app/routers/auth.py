from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as SqlSession

from app.auth import create_access_token, get_current_parent, get_password_hash, verify_password
from app.db import get_db
from app.models.models import Parent
from app.schemas.auth import (
    ParentLoginRequest,
    ParentRegisterRequest,
    ParentResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=ParentResponse, status_code=status.HTTP_201_CREATED)
def register_parent(payload: ParentRegisterRequest, db: SqlSession = Depends(get_db)):
    clean_email = payload.email.strip().lower()

    existing = db.query(Parent).filter(Parent.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    hashed = get_password_hash(payload.password)
    parent = Parent(email=clean_email, password_hash=hashed)
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent


@router.post("/login", response_model=TokenResponse)
def login_parent(payload: ParentLoginRequest, db: SqlSession = Depends(get_db)):
    clean_email = payload.email.strip().lower()

    parent = db.query(Parent).filter(Parent.email == clean_email).first()
    if not parent or not verify_password(payload.password, parent.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(parent.id)})
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=ParentResponse)
def get_me(current_parent: Parent = Depends(get_current_parent)):
    return current_parent
