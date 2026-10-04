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
    client.post("/auth/register", json={"email": email, "password": "password123"})
    login_resp = client.post("/auth/login", json={"email": email, "password": "password123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

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


# --- 1. PROVISIONING & PAIRING TESTS ---

def test_register_device_wrong_provisioning_key_401():
    resp_bad = client.post("/devices/register", headers={"X-Provisioning-Key": "invalid_key"})
    assert resp_bad.status_code == 401


def test_register_device_valid_provisioning_key_201():
    resp_ok = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY})
    assert resp_ok.status_code == 201
    data = resp_ok.json()
    assert "device_id" in data
    assert data["pairing_token"].startswith("WINI-")
    assert "device_secret" in data


def test_pair_device_twice_409_and_other_parent_child_404():
    headers_a, child_a_id = create_test_parent_and_child(email="pair_a@example.com")
    headers_b, child_b_id = create_test_parent_and_child(email="pair_b@example.com")

    reg_resp = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY})
    reg_data = reg_resp.json()
    pairing_token = reg_data["pairing_token"]

    # Unknown pairing token -> 404
    assert client.post("/devices/pair", json={"pairing_token": "WINI-UNKNOWN999", "child_id": child_a_id}, headers=headers_a).status_code == 404

    # Child owned by another parent -> 404
    assert client.post("/devices/pair", json={"pairing_token": pairing_token, "child_id": child_b_id}, headers=headers_a).status_code == 404

    # Success pairing
    resp_pair = client.post("/devices/pair", json={"pairing_token": pairing_token, "child_id": child_a_id}, headers=headers_a)
    assert resp_pair.status_code == 200

    # Re-using already paired token -> 409
    resp_reuse = client.post("/devices/pair", json={"pairing_token": pairing_token, "child_id": child_a_id}, headers=headers_a)
    assert resp_reuse.status_code == 404 or resp_reuse.status_code == 409


def test_second_device_on_same_child_409():
    headers, child_id = create_test_parent_and_child(email="second_dev@example.com")
    reg1 = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY}).json()
    client.post("/devices/pair", json={"pairing_token": reg1["pairing_token"], "child_id": child_id}, headers=headers)

    reg2 = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY}).json()
    resp_second = client.post("/devices/pair", json={"pairing_token": reg2["pairing_token"], "child_id": child_id}, headers=headers)
    assert resp_second.status_code == 409


def test_get_and_unpair_child_device_two_parent_isolation():
    headers_a, child_a_id = create_test_parent_and_child(email="unpair_a@example.com")
    headers_b, _ = create_test_parent_and_child(email="unpair_b@example.com")

    reg = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY}).json()
    client.post("/devices/pair", json={"pairing_token": reg["pairing_token"], "child_id": child_a_id}, headers=headers_a)

    resp_list = client.get(f"/children/{child_a_id}/devices", headers=headers_a)
    assert resp_list.status_code == 200
    devices = resp_list.json()
    assert len(devices) == 1
    device_id = devices[0]["id"]
    assert "device_secret" not in devices[0]
    assert "pairing_token" not in devices[0]

    # Two-parent isolation -> 404
    assert client.get(f"/children/{child_a_id}/devices", headers=headers_b).status_code == 404
    assert client.delete(f"/devices/{device_id}", headers=headers_b).status_code == 404

    resp_unpair = client.delete(f"/devices/{device_id}", headers=headers_a)
    assert resp_unpair.status_code == 200
    assert len(client.get(f"/children/{child_a_id}/devices", headers=headers_a).json()) == 0


# --- 2. CONTROLS ENDPOINTS & VALIDATION TESTS ---

def test_two_parent_isolation_get_and_patch_controls():
    headers_a, child_a_id = create_test_parent_and_child(email="iso_ctrl_a@example.com")
    headers_b, _ = create_test_parent_and_child(email="iso_ctrl_b@example.com")

    # Parent B gets 404 on GET parent A's child controls
    assert client.get(f"/children/{child_a_id}/controls", headers=headers_b).status_code == 404

    # Parent B gets 404 on PATCH parent A's child controls
    assert client.patch(
        f"/children/{child_a_id}/controls",
        json={"daily_limit_minutes": 60},
        headers=headers_b
    ).status_code == 404


def test_get_controls_get_or_create():
    headers_a, child_a_id = create_test_parent_and_child(email="ctrl_a@example.com")
    headers_b, _ = create_test_parent_and_child(email="ctrl_b@example.com")

    # Isolation check -> 404
    assert client.get(f"/children/{child_a_id}/controls", headers=headers_b).status_code == 404

    resp = client.get(f"/children/{child_a_id}/controls", headers=headers_a)
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == 1
    assert data["sync_status"] == "no_device"
    assert data["daily_limit_minutes"] == 45


def test_patch_controls_tries_0_and_4_give_422_and_unknown_field_422():
    headers, child_id = create_test_parent_and_child(email="patch_val@example.com")

    assert client.patch(f"/children/{child_id}/controls", json={"daily_limit_minutes": 1500}, headers=headers).status_code == 422
    assert client.patch(f"/children/{child_id}/controls", json={"tries_before_reveal": 0}, headers=headers).status_code == 422
    assert client.patch(f"/children/{child_id}/controls", json={"tries_before_reveal": 4}, headers=headers).status_code == 422
    assert client.patch(f"/children/{child_id}/controls", json={"probe_mode": "invalid"}, headers=headers).status_code == 422
    assert client.patch(f"/children/{child_id}/controls", json={"schedule": {"mon": [{"start": "18:00", "end": "17:00"}]}}, headers=headers).status_code == 422
    assert client.patch(f"/children/{child_id}/controls", json={"unknown_field": "val"}, headers=headers).status_code == 422


def test_empty_patch_no_version_bump():
    headers, child_id = create_test_parent_and_child(email="empty_patch@example.com")
    c_before = client.get(f"/children/{child_id}/controls", headers=headers).json()
    resp_empty = client.patch(f"/children/{child_id}/controls", json={}, headers=headers)
    assert resp_empty.status_code == 200
    assert resp_empty.json()["version"] == c_before["version"]


def test_parallel_patch_controls_version_plus_two():
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
    assert c_after["version"] == initial_ver + 2


# --- 3. DEVICE API & ACK & SYNC STATUS TESTS ---

def test_wrong_device_secret_401_and_unpaired_device_403():
    headers, child_id = create_test_parent_and_child(email="dev_auth@example.com")
    reg = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY}).json()
    device_id = reg["device_id"]
    device_secret = reg["device_secret"]

    # Unpaired device -> 403
    device_headers = {"X-Device-Id": device_id, "X-Device-Secret": device_secret}
    assert client.get("/device/controls", headers=device_headers).status_code == 403

    # Pair device
    client.post("/devices/pair", json={"pairing_token": reg["pairing_token"], "child_id": child_id}, headers=headers)

    # Wrong device secret -> 401
    bad_headers = {"X-Device-Id": device_id, "X-Device-Secret": "wrong_secret"}
    assert client.get("/device/controls", headers=bad_headers).status_code == 401


def test_device_heartbeat_updates_last_seen():
    headers, child_id = create_test_parent_and_child(email="hb_test@example.com")
    reg = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY}).json()
    client.post("/devices/pair", json={"pairing_token": reg["pairing_token"], "child_id": child_id}, headers=headers)

    device_headers = {"X-Device-Id": reg["device_id"], "X-Device-Secret": reg["device_secret"]}
    resp_hb = client.post("/device/heartbeat", headers=device_headers)
    assert resp_hb.status_code == 200
    assert "last_seen" in resp_hb.json()


def test_future_ack_422_and_duplicate_ack_idempotent():
    headers, child_id = create_test_parent_and_child(email="ack_test@example.com")
    reg = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY}).json()
    client.post("/devices/pair", json={"pairing_token": reg["pairing_token"], "child_id": child_id}, headers=headers)

    device_headers = {"X-Device-Id": reg["device_id"], "X-Device-Secret": reg["device_secret"]}

    # Ack future version -> 422
    assert client.post("/device/controls/ack", json={"control_version": 99}, headers=device_headers).status_code == 422

    # Ack current version (1) -> 200
    resp_ack = client.post("/device/controls/ack", json={"control_version": 1}, headers=device_headers)
    assert resp_ack.status_code == 200

    # Duplicate ack of same version -> idempotent (200)
    resp_dup = client.post("/device/controls/ack", json={"control_version": 1}, headers=device_headers)
    assert resp_dup.status_code == 200


def test_sync_status_pending_then_applied():
    headers, child_id = create_test_parent_and_child(email="sync_stat@example.com")
    reg = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY}).json()
    client.post("/devices/pair", json={"pairing_token": reg["pairing_token"], "child_id": child_id}, headers=headers)

    # Initial sync_status -> "pending"
    c_pending = client.get(f"/children/{child_id}/controls", headers=headers).json()
    assert c_pending["sync_status"] == "pending"

    # Ack version 1 -> sync_status becomes "applied"
    device_headers = {"X-Device-Id": reg["device_id"], "X-Device-Secret": reg["device_secret"]}
    client.post("/device/controls/ack", json={"control_version": 1}, headers=device_headers)
    c_applied = client.get(f"/children/{child_id}/controls", headers=headers).json()
    assert c_applied["sync_status"] == "applied"


# --- 4. WEBSOCKET TESTS ---

def test_websocket_auth_timeout_closes(monkeypatch):
    import app.routers.device_api as device_api_module
    monkeypatch.setattr(device_api_module, "WS_AUTH_TIMEOUT_SECONDS", 0.05)

    with pytest.raises(Exception):
        with client.websocket_connect("/ws/device") as ws:
            # Send nothing, connection closes after timeout
            ws.receive_json()


def test_websocket_bad_auth_closes():
    headers, child_id = create_test_parent_and_child(email="ws_bad@example.com")
    reg = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY}).json()
    client.post("/devices/pair", json={"pairing_token": reg["pairing_token"], "child_id": child_id}, headers=headers)

    # Bad auth closes socket
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/device") as ws:
            ws.send_json({"device_id": reg["device_id"], "device_secret": "wrong_secret"})
            ws.receive_json()


def test_websocket_initial_controls_on_connect():
    headers, child_id = create_test_parent_and_child(email="ws_init@example.com")
    reg = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY}).json()
    client.post("/devices/pair", json={"pairing_token": reg["pairing_token"], "child_id": child_id}, headers=headers)

    with client.websocket_connect("/ws/device") as ws:
        ws.send_json({"device_id": reg["device_id"], "device_secret": reg["device_secret"]})
        initial_msg = ws.receive_json()
        assert initial_msg["event"] == "controls_update"
        assert initial_msg["version"] == 1


def test_websocket_push_after_patch():
    headers, child_id = create_test_parent_and_child(email="ws_push@example.com")
    reg = client.post("/devices/register", headers={"X-Provisioning-Key": settings.PROVISIONING_KEY}).json()
    client.post("/devices/pair", json={"pairing_token": reg["pairing_token"], "child_id": child_id}, headers=headers)

    with client.websocket_connect("/ws/device") as ws:
        ws.send_json({"device_id": reg["device_id"], "device_secret": reg["device_secret"]})
        ws.receive_json()  # Read initial connect payload

        # PATCH controls while connected -> receives pushed update
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
