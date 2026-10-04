import hashlib
import secrets
from typing import Tuple
import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as SqlSession

from app.db import get_db
from app.models.models import Device


def get_authenticated_device(
    x_device_id: str = Header(..., alias="X-Device-Id"),
    x_device_secret: str = Header(..., alias="X-Device-Secret"),
    db: SqlSession = Depends(get_db),
) -> Tuple[Device, uuid.UUID]:
    try:
        device_uuid = uuid.UUID(x_device_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device ID format",
        )

    device = db.execute(
        select(Device).where(Device.id == device_uuid)
    ).scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device authentication failed",
        )

    provided_hash = hashlib.sha256(x_device_secret.encode("utf-8")).hexdigest()
    if not secrets.compare_digest(provided_hash, device.device_secret_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device authentication failed",
        )

    if device.status != "paired" or device.child_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device is not paired to any child",
        )

    return device, device.child_id
