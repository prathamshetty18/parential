import asyncio
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session as SqlSession

from app.auth import get_current_parent
from app.db import get_db
from app.models.models import Child, Control, ControlAck, Device, Parent
from app.schemas.control import ControlResponse, ControlUpdate
from app.websocket_manager import device_ws_manager

router = APIRouter(prefix="/children", tags=["controls"])


def _calculate_sync_status(db: SqlSession, child_id: uuid.UUID, control_version: int) -> str:
    device = db.execute(
        select(Device).where(Device.child_id == child_id, Device.status == "paired")
    ).scalar_one_or_none()

    if not device:
        return "no_device"

    max_ack = db.execute(
        select(func.max(ControlAck.control_version)).where(ControlAck.device_id == device.id)
    ).scalar()

    if max_ack is not None and max_ack >= control_version:
        return "applied"
    return "pending"


@router.get("/{child_id}/controls", response_model=ControlResponse)
def get_child_controls(
    child_id: uuid.UUID,
    current_parent: Parent = Depends(get_current_parent),
    db: SqlSession = Depends(get_db),
):
    child = db.execute(
        select(Child).where(Child.id == child_id, Child.parent_id == current_parent.id)
    ).scalar_one_or_none()
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found",
        )

    # Get or create default control row in one transaction
    control = db.execute(
        select(Control).where(Control.child_id == child_id)
    ).scalar_one_or_none()

    if not control:
        control = Control(
            id=uuid.uuid4(),
            child_id=child_id,
            version=1,
            daily_limit_minutes=45,
            tries_before_reveal=2,
            probe_mode="both",
            frustration_guard=True,
        )
        db.add(control)
        db.commit()
        db.refresh(control)

    sync_status = _calculate_sync_status(db, child_id, control.version)

    return {
        "id": control.id,
        "child_id": control.child_id,
        "version": control.version,
        "daily_limit_minutes": control.daily_limit_minutes,
        "schedule": control.schedule,
        "paused": control.paused,
        "subjects_allowed": control.subjects_allowed,
        "content_level": control.content_level,
        "tries_before_reveal": control.tries_before_reveal,
        "probe_mode": control.probe_mode,
        "frustration_guard": control.frustration_guard,
        "sync_status": sync_status,
        "created_at": control.created_at,
    }


@router.patch("/{child_id}/controls", response_model=ControlResponse)
async def update_child_controls(
    child_id: uuid.UUID,
    payload: ControlUpdate,
    current_parent: Parent = Depends(get_current_parent),
    db: SqlSession = Depends(get_db),
):
    child = db.execute(
        select(Child).where(Child.id == child_id, Child.parent_id == current_parent.id)
    ).scalar_one_or_none()
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found",
        )

    # Lock controls row (SELECT ... FOR UPDATE)
    db.execute(
        select(Control).where(Control.child_id == child_id).with_for_update()
    )

    control = db.execute(
        select(Control).where(Control.child_id == child_id)
    ).scalar_one_or_none()

    if not control:
        control = Control(
            id=uuid.uuid4(),
            child_id=child_id,
            version=1,
            daily_limit_minutes=45,
            tries_before_reveal=2,
            probe_mode="both",
            frustration_guard=True,
        )
        db.add(control)
        db.flush()

    update_data = payload.model_dump(exclude_unset=True, mode="json")

    # An empty PATCH changes nothing and does not bump version
    if not update_data:
        sync_status = _calculate_sync_status(db, child_id, control.version)
        return {
            "id": control.id,
            "child_id": control.child_id,
            "version": control.version,
            "daily_limit_minutes": control.daily_limit_minutes,
            "schedule": control.schedule,
            "paused": control.paused,
            "subjects_allowed": control.subjects_allowed,
            "content_level": control.content_level,
            "tries_before_reveal": control.tries_before_reveal,
            "probe_mode": control.probe_mode,
            "frustration_guard": control.frustration_guard,
            "sync_status": sync_status,
            "created_at": control.created_at,
        }

    # Perform atomic update and version increment
    db.execute(
        update(Control)
        .where(Control.id == control.id)
        .values(
            version=Control.version + 1,
            **update_data
        )
    )
    db.commit()
    db.refresh(control)

    # Push to WebSocket ONLY after transaction commits
    device = db.execute(
        select(Device).where(Device.child_id == child_id, Device.status == "paired")
    ).scalar_one_or_none()

    if device:
        push_payload = {
            "event": "controls_update",
            "version": control.version,
            "daily_limit_minutes": control.daily_limit_minutes,
            "schedule": control.schedule,
            "paused": control.paused,
            "subjects_allowed": control.subjects_allowed,
            "content_level": control.content_level,
            "tries_before_reveal": control.tries_before_reveal,
            "probe_mode": control.probe_mode,
            "frustration_guard": control.frustration_guard,
        }
        await device_ws_manager.send_controls(device.id, push_payload)

    sync_status = _calculate_sync_status(db, child_id, control.version)

    return {
        "id": control.id,
        "child_id": control.child_id,
        "version": control.version,
        "daily_limit_minutes": control.daily_limit_minutes,
        "schedule": control.schedule,
        "paused": control.paused,
        "subjects_allowed": control.subjects_allowed,
        "content_level": control.content_level,
        "tries_before_reveal": control.tries_before_reveal,
        "probe_mode": control.probe_mode,
        "frustration_guard": control.frustration_guard,
        "sync_status": sync_status,
        "created_at": control.created_at,
    }
