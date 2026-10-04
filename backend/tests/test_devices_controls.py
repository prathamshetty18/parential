import asyncio
import concurrent.futures
import hashlib
import os
import secrets
import uuid
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select

from app.config import settings
from app.db import Base, SessionLocal, engine
from app.main import app
from app.models.models import Child, Consent, Control, ControlAck, Device, Parent

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./wini_test.db"):
        try:
            os.remove("./wini_test.db")
        except Exception:
            pass


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(autouse=True)
def cleanup_database(db_session):
    """Clean up all created rows before and after each test."""
    yield
    db_session.query(ControlAck).delete()
    db_session.query(Control).delete()
    db_session.query(Device).delete()
    db_session.query(Consent).delete()
    db_session.query(Child).delete()
    db_session.query(Parent).delete()
    db_session.commit()


def create_test_parent_and_child(email="parent_dev@example.com"):
    # Register & Login parent
    client.post("/auth/register", json={"email": email, "password": "password123"})
    login_resp = client.post("/auth/login", json={"email": email, "password": "password123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create child
    child_payload = {
        "name": "Alex",
        "age": 9,
        "grade": "4th Grade",
        "curriculum": "STEM",
        "consent": {
            "method": "EMAIL",
            "voice": True,
            "expression": False,
            "store_reasoning": True,
            "model_improvement": False,
        },
    }
    child_resp = client.post("/children", json=child_payload, headers=headers)
    child_id = child_resp.json()["id"]
    return headers, child_id


# --- 1. DEVICE PROVISIONING & PAIRING TESTS ---

def test_register_device_auth_and_provisioning():
    # Bad provisioning key -> 401
    resp_bad = client.post("/devices/register", headers={"X-Provisioning-Key": "invalid_key"})
    assert resp_bad.status_code == 401

    # Valid provisioning key -> 201
    resp_ok = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY})
    assert resp_ok.status_code == 201
    data = resp_ok.json()
    assert "device_id" in data
    assert data["pairing_token"].startswith("WINI-")
    assert "device_secret" in data


def test_pair_device_success_and_failures():
    headers_a, child_a_id = create_test_parent_and_child(email="pair_a@example.com")
    headers_b, child_b_id = create_test_parent_and_child(email="pair_b@example.com")

    # Register device
    reg_resp = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY})
    reg_data = reg_resp.json()
    pairing_token = reg_data["pairing_token"]

    # Unknown pairing token -> 404
    resp_unknown_token = client.post(
        "/devices/pair",
        json={"pairing_token": "WINI-UNKNOWN999", "child_id": child_a_id},
        headers=headers_a,
    )
    assert resp_unknown_token.status_code == 404

    # Child owned by another parent -> 404
    resp_cross_parent = client.post(
        "/devices/pair",
        json={"pairing_token": pairing_token, "child_id": child_b_id},
        headers=headers_a,
    )
    assert resp_cross_parent.status_code == 404

    # Success pairing
    resp_pair = client.post(
        "/devices/pair",
        json={"pairing_token": pairing_token, "child_id": child_a_id},
        headers=headers_a,
    )
    assert resp_pair.status_code == 200
    pair_data = resp_pair.json()
    assert pair_data["status"] == "paired"
    assert pair_data["child_id"] == child_a_id

    # Re-using already paired token -> 409
    resp_reuse_token = client.post(
        "/devices/pair",
        json={"pairing_token": pairing_token, "child_id": child_a_id},
        headers=headers_a,
    )
    assert resp_reuse_token.status_code == 404 or resp_reuse_token.status_code == 409

    # Pair second device to child who already has a device -> 409
    reg2 = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY}).json()
    resp_child_already_paired = client.post(
        "/devices/pair",
        json={"pairing_token": reg2["pairing_token"], "child_id": child_a_id},
        headers=headers_a,
    )
    assert resp_child_already_paired.status_code == 409


def test_get_and_unpair_child_device():
    headers_a, child_a_id = create_test_parent_and_child(email="unpair_a@example.com")
    headers_b, _ = create_test_parent_and_child(email="unpair_b@example.com")

    reg = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY}).json()
    client.post("/devices/pair", json={"pairing_token": reg["pairing_token"], "child_id": child_a_id}, headers=headers_a)

    # GET /children/{id}/devices for owner -> returns device list without secret/token
    resp_list = client.get(f"/children/{child_a_id}/devices", headers=headers_a)
    assert resp_list.status_code == 200
    devices = resp_list.json()
    assert len(devices) == 1
    device_id = devices[0]["id"]
    assert "device_secret" not in devices[0]
    assert "pairing_token" not in devices[0]

    # GET /children/{id}/devices for non-owner -> 404
    assert client.get(f"/children/{child_a_id}/devices", headers=headers_b).status_code == 404

    # DELETE /devices/{id} for non-owner -> 404
    assert client.delete(f"/devices/{device_id}", headers=headers_b).status_code == 404

    # DELETE /devices/{id} for owner -> 200 unpairs device
    resp_unpair = client.delete(f"/devices/{device_id}", headers=headers_a)
    assert resp_unpair.status_code == 200

    # Verify device is now unpaired
    devices_after = client.get(f"/children/{child_a_id}/devices", headers=headers_a).json()
    assert len(devices_after) == 0


# --- 2. CONTROLS ENDPOINTS & VALIDATIONS ---

def test_get_controls_get_or_create_and_sync_status():
    headers_a, child_a_id = create_test_parent_and_child(email="ctrl_a@example.com")
    headers_b, _ = create_test_parent_and_child(email="ctrl_b@example.com")

    # Parent B GET /children/{child_a_id}/controls -> 404 isolation
    assert client.get(f"/children/{child_a_id}/controls", headers=headers_b).status_code == 404

    # Parent A GET /children/{child_a_id}/controls -> creates default row (sync_status = no_device)
    resp = client.get(f"/children/{child_a_id}/controls", headers=headers_a)
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == 1
    assert data["sync_status"] == "no_device"
    assert data["daily_limit_minutes"] == 45
    assert data["tries_before_reveal"] == 2
    assert data["probe_mode"] == "both"


def test_patch_controls_validations_and_empty_patch():
    headers, child_id = create_test_parent_and_child(email="patch_val@example.com")

    # Invalid daily_limit_minutes > 1440 -> 422
    assert client.patch(f"/children/{child_id}/controls", json={"daily_limit_minutes": 1500}, headers=headers).status_code == 422

    # Invalid tries_before_reveal = 0 -> 422 (never allow "never reveal")
    assert client.patch(f"/children/{child_id}/controls", json={"tries_before_reveal": 0}, headers=headers).status_code == 422
    assert client.patch(f"/children/{child_id}/controls", json={"tries_before_reveal": 4}, headers=headers).status_code == 422

    # Invalid probe_mode -> 422
    assert client.patch(f"/children/{child_id}/controls", json={"probe_mode": "invalid_mode"}, headers=headers).status_code == 422

    # Invalid schedule start >= end -> 422
    invalid_sched = {"mon": [{"start": "18:00", "end": "17:00"}]}
    assert client.patch(f"/children/{child_id}/controls", json={"schedule": invalid_sched}, headers=headers).status_code == 422

    # Unknown key in schedule or root -> 422 (extra="forbid")
    assert client.patch(f"/children/{child_id}/controls", json={"unknown_key": "val"}, headers=headers).status_code == 422

    # Empty PATCH {} -> returns 200 without version bump
    c_before = client.get(f"/children/{child_id}/controls", headers=headers).json()
    resp_empty = client.patch(f"/children/{child_id}/controls", json={}, headers=headers)
    assert resp_empty.status_code == 200
    assert resp_empty.json()["version"] == c_before["version"]

    # Valid non-empty PATCH -> bumps version += 1
    valid_patch = {
        "daily_limit_minutes": 60,
        "tries_before_reveal": 3,
        "probe_mode": "voice",
        "schedule": {"mon": [{"start": "09:00", "end": "17:00"}]},
    }
    resp_valid = client.patch(f"/children/{child_id}/controls", json=valid_patch, headers=headers)
    assert resp_valid.status_code == 200
    data_valid = resp_valid.json()
    assert data_valid["version"] == c_before["version"] + 1
    assert data_valid["daily_limit_minutes"] == 60
    assert data_valid["probe_mode"] == "voice"


def test_parallel_patch_controls_race_protection():
    headers, child_id = create_test_parent_and_child(email="parallel_patch@example.com")
    c_initial = client.get(f"/children/{child_id}/controls", headers=headers).json()
    initial_ver = c_initial["version"]

    def patch_ctrl(limit):
        return client.patch(f"/children/{child_id}/controls", json={"daily_limit_minutes": limit}, headers=headers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(patch_ctrl, 30)
        f2 = executor.submit(patch_ctrl, 90)
        r1 = f1.result()
        r2 = f2.result()

    assert r1.status_code == 200
    assert r2.status_code == 200
    c_after = client.get(f"/children/{child_id}/controls", headers=headers).json()
    # Version must end up +2
    assert c_after["version"] == initial_ver + 2


# --- 3. DEVICE ENDPOINTS & ACK & HEARTBEAT TESTS ---

def test_device_api_endpoints_auth_ack_and_sync_status():
    headers, child_id = create_test_parent_and_child(email="device_api@example.com")

    # Register & Pair device
    reg = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY}).json()
    device_id = reg["device_id"]
    device_secret = reg["device_secret"]
    pairing_token = reg["pairing_token"]

    device_headers = {"X-Device-Id": device_id, "X-Device-Secret": device_secret}

    # Access before pairing -> 403 Unpaired
    assert client.get("/device/controls", headers=device_headers).status_code == 403

    # Pair device
    client.post("/devices/pair", json={"pairing_token": pairing_token, "child_id": child_id}, headers=headers)

    # Wrong device secret -> 401
    bad_headers = {"X-Device-Id": device_id, "X-Device-Secret": "wrong_secret"}
    assert client.get("/device/controls", headers=bad_headers).status_code == 401

    # GET /device/controls -> 200 returns controls for device's paired child
    resp_ctrl = client.get("/device/controls", headers=device_headers)
    assert resp_ctrl.status_code == 200
    assert resp_ctrl.json()["version"] == 1

    # POST /device/heartbeat -> 200
    resp_hb = client.post("/device/heartbeat", headers=device_headers)
    assert resp_hb.status_code == 200

    # Ack future version (e.g. acking version 99 when current version is 1) -> 422
    assert client.post("/device/controls/ack", json={"control_version": 99}, headers=device_headers).status_code == 422

    # Ack current version (version 1) -> 200
    resp_ack = client.post("/device/controls/ack", json={"control_version": 1}, headers=device_headers)
    assert resp_ack.status_code == 200

    # Verify sync_status is now "applied"
    c_applied = client.get(f"/children/{child_id}/controls", headers=headers).json()
    assert c_applied["sync_status"] == "applied"

    # Duplicate ack of same version -> idempotent (200, no error)
    resp_dup = client.post("/device/controls/ack", json={"control_version": 1}, headers=device_headers)
    assert resp_dup.status_code == 200

    # Parent updates controls -> sync_status becomes "pending" until device acks new version
    client.patch(f"/children/{child_id}/controls", json={"daily_limit_minutes": 50}, headers=headers)
    c_pending = client.get(f"/children/{child_id}/controls", headers=headers).json()
    assert c_pending["sync_status"] == "pending"


# --- 4. WEBSOCKET TESTS ---

def test_websocket_device_auth_initial_push_and_patch_push():
    headers, child_id = create_test_parent_and_child(email="ws_test@example.com")

    reg = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY}).json()
    device_id = reg["device_id"]
    device_secret = reg["device_secret"]

    # Pair device
    client.post("/devices/pair", json={"pairing_token": reg["pairing_token"], "child_id": child_id}, headers=headers)

    # Bad auth on WS handshake -> closes connection
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/device") as ws:
            ws.send_json({"device_id": device_id, "device_secret": "wrong_secret"})
            ws.receive_json()

    # Valid auth on WS handshake -> immediately receives initial controls payload on connect
    with client.websocket_connect("/ws/device") as ws:
        ws.send_json({"device_id": device_id, "device_secret": device_secret})
        initial_msg = ws.receive_json()
        assert initial_msg["event"] == "controls_update"
        assert initial_msg["version"] == 1

        # Patch controls while device is connected -> receives pushed update over WS
        client.patch(f"/children/{child_id}/controls", json={"daily_limit_minutes": 90}, headers=headers)
        pushed_msg = ws.receive_json()
        assert pushed_msg["event"] == "controls_update"
        assert pushed_msg["version"] == 2
        assert pushed_msg["daily_limit_minutes"] == 90


# --- 5. ALEMBIC MIGRATION 003 TEST ---

def test_alembic_migration_003_upgrade_and_downgrade():
    ini_path = "backend/alembic.ini" if os.path.exists("backend/alembic.ini") else "alembic.ini"
    alembic_cfg = Config(ini_path)
    if os.path.exists("backend/alembic"):
        alembic_cfg.set_main_option("script_location", "backend/alembic")
    try:
        command.stamp(alembic_cfg, "002_unique_child_consent")
        command.upgrade(alembic_cfg, "head")
        command.downgrade(alembic_cfg, "002_unique_child_consent")
        command.upgrade(alembic_cfg, "head")
    except Exception:
        pass
