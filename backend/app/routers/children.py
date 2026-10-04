from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as SqlSession

from app.auth import get_current_parent
from app.db import get_db
from app.models.models import Child, Consent, Parent
from app.schemas.child import ChildCreate, ChildResponse, ChildUpdate
from app.schemas.consent import ConsentResponse, ConsentUpdate

router = APIRouter(prefix="/children", tags=["children"])


@router.post("", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
def create_child(
    payload: ChildCreate,
    current_parent: Parent = Depends(get_current_parent),
    db: SqlSession = Depends(get_db),
):
    # Lock parent row to prevent race conditions on 5th child creation
    db.execute(
        select(Parent).where(Parent.id == current_parent.id).with_for_update()
    )

    child_count = db.query(Child).filter(Child.parent_id == current_parent.id).count()
    if child_count >= 4:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Maximum limit of 4 children per parent reached",
        )

    # Create Child and Consent rows in ONE transaction
    new_child = Child(
        id=uuid.uuid4(),
        parent_id=current_parent.id,
        name=payload.name,
        age=payload.age,
        grade=payload.grade,
        curriculum=payload.curriculum,
        language=payload.language,
    )
    db.add(new_child)
    db.flush()  # Ensures new_child.id is generated for FK

    consent_data = payload.consent
    new_consent = Consent(
        id=uuid.uuid4(),
        parent_id=current_parent.id,
        child_id=new_child.id,
        method=consent_data.method,
        voice=consent_data.voice,
        expression=consent_data.expression,
        store_reasoning=consent_data.store_reasoning,
        model_improvement=consent_data.model_improvement,
    )
    db.add(new_consent)

    db.commit()
    db.refresh(new_child)
    return new_child


@router.get("", response_model=List[ChildResponse])
def get_children(
    current_parent: Parent = Depends(get_current_parent),
    db: SqlSession = Depends(get_db),
):
    children = db.query(Child).filter(Child.parent_id == current_parent.id).all()
    return children


@router.get("/{child_id}", response_model=ChildResponse)
def get_child_by_id(
    child_id: uuid.UUID,
    current_parent: Parent = Depends(get_current_parent),
    db: SqlSession = Depends(get_db),
):
    child = (
        db.query(Child)
        .filter(Child.id == child_id, Child.parent_id == current_parent.id)
        .first()
    )
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found",
        )
    return child


@router.put("/{child_id}", response_model=ChildResponse)
def update_child(
    child_id: uuid.UUID,
    payload: ChildUpdate,
    current_parent: Parent = Depends(get_current_parent),
    db: SqlSession = Depends(get_db),
):
    child = (
        db.query(Child)
        .filter(Child.id == child_id, Child.parent_id == current_parent.id)
        .first()
    )
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(child, field, val)

    db.commit()
    db.refresh(child)
    return child


@router.put("/{child_id}/consent", response_model=ConsentResponse)
def update_child_consent(
    child_id: uuid.UUID,
    payload: ConsentUpdate,
    current_parent: Parent = Depends(get_current_parent),
    db: SqlSession = Depends(get_db),
):
    # Ensure child belongs to current parent, else 404
    child = (
        db.query(Child)
        .filter(Child.id == child_id, Child.parent_id == current_parent.id)
        .first()
    )
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found",
        )

    consent = db.query(Consent).filter(Consent.child_id == child_id).first()
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent record not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(consent, field, val)

    consent.consented_at = func.now()
    db.commit()
    db.refresh(consent)
    return consent
