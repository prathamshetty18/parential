import hashlib
import secrets
from typing import List
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as SqlSession

from app.auth import get_current_parent
from app.config import settings
from app.db import get_db
from app.models.models import Child, Device, Parent
from app.schemas.device import (
    DevicePairRequest,
    DeviceRegisterResponse,
    DeviceResponse,
)

router = APIRouter(tags=["devices"])


@router.post("/devices/register", response_model=DeviceRegisterResponse, status_code=status.HTTP_201_CREATED)
def register_device(
    x_provisioning_key: str = Header(..., alias="X-Provisioning-Key"),
    db: SqlSession = Depends(get_db),
):
    if not secrets.compare_digest(x_provisioning_key, settings.PROVISIONING_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid provisioning key",
        )

    device_id = uuid.uuid4()
    pairing_token = f"WINI-{secrets.token_hex(6).upper()}"
    raw_secret = secrets.token_urlsafe(32)
    secret_hash = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()

    device = Device(
        id=device_id,
        child_id=None,
        pairing_token=pairing_token,
        device_secret_hash=secret_hash,
        status="unpaired",
        last_seen=None,
    )
    db.add(device)
    db.commit()

    return DeviceRegisterResponse(
        device_id=device_id,
        pairing_token=pairing_token,
        device_secret=raw_secret,
    )


@router.post("/devices/pair", response_model=DeviceResponse)
def pair_device(
    payload: DevicePairRequest,
    current_parent: Parent = Depends(get_current_parent),
    db: SqlSession = Depends(get_db),
):
    # Verify child belongs to current parent
    child = db.execute(
        select(Child).where(Child.id == payload.child_id, Child.parent_id == current_parent.id)
    ).scalar_one_or_none()
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found",
        )

    # Check if child already has a device
    existing_child_device = db.execute(
        select(Device).where(Device.child_id == payload.child_id)
    ).scalar_one_or_none()
    if existing_child_device:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Child already has a paired device",
        )

    # Find device by pairing token
    device = db.execute(
        select(Device).where(Device.pairing_token == payload.pairing_token)
    ).scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or unknown pairing token",
        )

    if device.status == "paired" or device.child_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pairing token already used",
        )

    # Pair device and invalidate pairing token
    device.status = "paired"
    device.child_id = payload.child_id
    device.last_seen = None
    device.pairing_token = f"USED_{uuid.uuid4()}"

    db.commit()
    db.refresh(device)
    return device


@router.get("/children/{child_id}/devices", response_model=List[DeviceResponse])
def get_child_devices(
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

    devices = db.execute(
        select(Device).where(Device.child_id == child_id)
    ).scalars().all()
    return devices


@router.delete("/devices/{device_id}", status_code=status.HTTP_200_OK)
def unpair_device(
    device_id: uuid.UUID,
    current_parent: Parent = Depends(get_current_parent),
    db: SqlSession = Depends(get_db),
):
    device = db.execute(
        select(Device).where(Device.id == device_id)
    ).scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    if device.child_id:
        child = db.execute(
            select(Child).where(Child.id == device.child_id, Child.parent_id == current_parent.id)
        ).scalar_one_or_none()
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

    device.status = "unpaired"
    device.child_id = None
    db.commit()
    return {"message": "Device unpaired successfully"}
