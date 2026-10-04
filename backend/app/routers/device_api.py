import asyncio
import hashlib
import secrets
from typing import Tuple
import uuid

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as SqlSession

from app.db import SessionLocal, get_db
from app.device_auth import get_authenticated_device
from app.models.models import Control, ControlAck, Device
from app.schemas.control import ControlResponse
from app.schemas.device import ControlAckRequest, ControlAckResponse
from app.websocket_manager import device_ws_manager

router = APIRouter(tags=["device_api"])


@router.get("/device/controls")
def get_device_controls(
    auth_data: Tuple[Device, uuid.UUID] = Depends(get_authenticated_device),
    db: SqlSession = Depends(get_db),
):
    device, child_id = auth_data

    # Update last_seen
    device.last_seen = func.now()
    db.commit()

    control = db.execute(
        select(Control).where(Control.child_id == child_id)
    ).scalar_one_or_none()

    if not control:
        # Create default controls if missing
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

    return {
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


@router.post("/device/controls/ack", response_model=ControlAckResponse)
def ack_device_controls(
    payload: ControlAckRequest,
    auth_data: Tuple[Device, uuid.UUID] = Depends(get_authenticated_device),
    db: SqlSession = Depends(get_db),
):
    device, child_id = auth_data

    control = db.execute(
        select(Control).where(Control.child_id == child_id)
    ).scalar_one_or_none()

    current_version = control.version if control else 1
    if payload.control_version > current_version:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot ack future control version {payload.control_version} (current version is {current_version})",
        )

    # Check for existing duplicate ack (idempotent)
    existing_ack = db.execute(
        select(ControlAck).where(
            ControlAck.device_id == device.id,
            ControlAck.control_version == payload.control_version,
        )
    ).scalar_one_or_none()

    if existing_ack:
        device.last_seen = func.now()
        db.commit()
        return existing_ack

    ack = ControlAck(
        id=uuid.uuid4(),
        device_id=device.id,
        control_version=payload.control_version,
    )
    device.last_seen = func.now()
    db.add(ack)
    db.commit()
    db.refresh(ack)
    return ack


@router.post("/device/heartbeat")
def device_heartbeat(
    auth_data: Tuple[Device, uuid.UUID] = Depends(get_authenticated_device),
    db: SqlSession = Depends(get_db),
):
    device, _ = auth_data
    device.last_seen = func.now()
    db.commit()
    return {"status": "ok", "last_seen": device.last_seen}


WS_AUTH_TIMEOUT_SECONDS = 10.0


@router.websocket("/ws/device")
async def websocket_device_endpoint(websocket: WebSocket):
    await websocket.accept()

    # 10 second authentication timeout (configurable via WS_AUTH_TIMEOUT_SECONDS)
    try:
        auth_payload = await asyncio.wait_for(websocket.receive_json(), timeout=WS_AUTH_TIMEOUT_SECONDS)
    except Exception:
        await websocket.close(code=1008)  # Policy violation / timeout
        return

    device_id_str = auth_payload.get("device_id")
    device_secret = auth_payload.get("device_secret")

    if not device_id_str or not device_secret:
        await websocket.close(code=1008)
        return

    try:
        device_uuid = uuid.UUID(device_id_str)
    except ValueError:
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    try:
        device = db.execute(
            select(Device).where(Device.id == device_uuid)
        ).scalar_one_or_none()

        if not device or not device.device_secret_hash:
            await websocket.close(code=1008)
            return

        provided_hash = hashlib.sha256(device_secret.encode("utf-8")).hexdigest()
        if not secrets.compare_digest(provided_hash, device.device_secret_hash):
            await websocket.close(code=1008)
            return

        if device.status != "paired" or device.child_id is None:
            await websocket.close(code=1008)
            return

        child_id = device.child_id
        device.last_seen = func.now()
        db.commit()

        await device_ws_manager.connect(device.id, websocket)

        # Send initial controls immediately on connect so offline device catches up
        control = db.execute(
            select(Control).where(Control.child_id == child_id)
        ).scalar_one_or_none()

        initial_controls_payload = {
            "event": "controls_update",
            "version": control.version if control else 1,
            "daily_limit_minutes": control.daily_limit_minutes if control else 45,
            "schedule": control.schedule if control else None,
            "paused": control.paused if control else False,
            "subjects_allowed": control.subjects_allowed if control else None,
            "content_level": control.content_level if control else None,
            "tries_before_reveal": control.tries_before_reveal if control else 2,
            "probe_mode": control.probe_mode if control else "both",
            "frustration_guard": control.frustration_guard if control else True,
        }
        await websocket.send_json(initial_controls_payload)

        # Keep connection open and receive messages
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        device_ws_manager.disconnect(device_uuid)
    except Exception:
        device_ws_manager.disconnect(device_uuid)
        try:
            await websocket.close(code=1008)
        except Exception:
            pass
    finally:
        db.close()
