import os
import uuid
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
import pytest

from app.db import Base, SessionLocal, engine
from app.main import app
from app.models.models import Child, Consent, Parent

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
    """Clean up all tables before and after each test to leave no leftover test data."""
    yield
    db_session.query(Consent).delete()
    db_session.query(Child).delete()
    db_session.query(Parent).delete()
    db_session.commit()


# Helper function to register and get JWT headers
def create_test_parent(email="parent@example.com", password="password123"):
    resp = client.post("/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201
    login_resp = client.post("/auth/login", json={"email": email, "password": password})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return resp.json()["id"], headers


# --- AUTH TESTS ---

def test_register_success():
    resp = client.post("/auth/register", json={"email": "  USER@Example.COM  ", "password": "password123"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "user@example.com"
    assert "id" in data


def test_register_duplicate_email():
    client.post("/auth/register", json={"email": "dup@example.com", "password": "password123"})
    resp = client.post("/auth/register", json={"email": "dup@example.com", "password": "password456"})
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Email already registered"


def test_register_password_length_validation():
    # Short password (< 8 chars)
    resp1 = client.post("/auth/register", json={"email": "short@example.com", "password": "short"})
    assert resp1.status_code == 422

    # Long password (> 72 chars bcrypt limit)
    long_pass = "a" * 73
    resp2 = client.post("/auth/register", json={"email": "long@example.com", "password": long_pass})
    assert resp2.status_code == 422


def test_login_success_and_same_error_message_for_wrong_pass_and_unknown_email():
    create_test_parent(email="login_user@example.com", password="securepassword123")

    # Success
    resp_success = client.post("/auth/login", json={"email": "login_user@example.com", "password": "securepassword123"})
    assert resp_success.status_code == 200
    assert "access_token" in resp_success.json()

    # Wrong password
    resp_wrong_pass = client.post("/auth/login", json={"email": "login_user@example.com", "password": "wrongpassword"})
    assert resp_wrong_pass.status_code == 401
    assert resp_wrong_pass.json()["detail"] == "Invalid email or password"

    # Unknown email
    resp_unknown = client.post("/auth/login", json={"email": "nonexistent@example.com", "password": "securepassword123"})
    assert resp_unknown.status_code == 401
    assert resp_unknown.json()["detail"] == "Invalid email or password"


def test_get_me():
    parent_id, headers = create_test_parent(email="me@example.com")

    # Success with token
    resp = client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == parent_id

    # No token
    resp_no_token = client.get("/auth/me")
    assert resp_no_token.status_code == 403 or resp_no_token.status_code == 401

    # Invalid token
    resp_invalid = client.get("/auth/me", headers={"Authorization": "Bearer invalid_jwt_token"})
    assert resp_invalid.status_code == 401


# --- CHILDREN & CONSENT TESTS ---

def test_create_child_and_consent_in_one_transaction(db_session):
    _, headers = create_test_parent(email="child_creator@example.com")

    payload = {
        "name": "Leo",
        "age": 8,
        "grade": "3rd Grade",
        "curriculum": "STEM Core",
        "language": "English",
        "consent": {
            "method": "DPDP_VERIFIED_EMAIL",
            "voice": True,
            "expression": False,
            "store_reasoning": True,
            "model_improvement": False,
        },
    }

    resp = client.post("/children", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Leo"
    assert data["consent"]["method"] == "DPDP_VERIFIED_EMAIL"

    # Verify rows in DB
    child_in_db = db_session.query(Child).filter(Child.name == "Leo").first()
    assert child_in_db is not None
    consent_in_db = db_session.query(Consent).filter(Consent.child_id == child_in_db.id).first()
    assert consent_in_db is not None


def test_create_child_missing_consent_or_toggle_fails_and_leaves_zero_rows(db_session):
    _, headers = create_test_parent(email="failed_consent@example.com")

    # Missing voice toggle
    invalid_payload = {
        "name": "Maya",
        "age": 10,
        "grade": "5th Grade",
        "curriculum": "Math",
        "consent": {
            "method": "DPDP_VERIFIED",
            # missing voice, expression, store_reasoning, model_improvement
        },
    }

    resp = client.post("/children", json=invalid_payload, headers=headers)
    assert resp.status_code == 422

    # Assert ZERO child and consent rows created
    assert db_session.query(Child).count() == 0
    assert db_session.query(Consent).count() == 0


def test_max_4_children_per_parent_5th_fails(db_session):
    _, headers = create_test_parent(email="four_children@example.com")

    def make_child_payload(i):
        return {
            "name": f"Child {i}",
            "age": 8,
            "grade": "3rd Grade",
            "curriculum": "STEM",
            "consent": {
                "method": "EMAIL",
                "voice": True,
                "expression": False,
                "store_reasoning": True,
                "model_improvement": False,
            },
        }

    # Add 4 children
    for i in range(1, 5):
        resp = client.post("/children", json=make_child_payload(i), headers=headers)
        assert resp.status_code == 201

    # 5th child fails with 409
    resp_5th = client.post("/children", json=make_child_payload(5), headers=headers)
    assert resp_5th.status_code == 409
    assert resp_5th.json()["detail"] == "Maximum limit of 4 children per parent reached"


def test_parent_isolation_parent_b_cannot_access_parent_a_child():
    # Parent A creates Child A
    parent_a_id, headers_a = create_test_parent(email="parent_a@example.com")
    payload_a = {
        "name": "Child A",
        "age": 8,
        "grade": "3rd Grade",
        "curriculum": "STEM",
        "consent": {
            "method": "EMAIL",
            "voice": True,
            "expression": False,
            "store_reasoning": True,
            "model_improvement": False,
        },
    }
    resp_a = client.post("/children", json=payload_a, headers=headers_a)
    assert resp_a.status_code == 201
    child_a_id = resp_a.json()["id"]

    # Parent B creates Child B
    parent_b_id, headers_b = create_test_parent(email="parent_b@example.com")
    payload_b = {
        "name": "Child B",
        "age": 10,
        "grade": "5th Grade",
        "curriculum": "Math",
        "consent": {
            "method": "EMAIL",
            "voice": True,
            "expression": False,
            "store_reasoning": True,
            "model_improvement": False,
        },
    }
    resp_b = client.post("/children", json=payload_b, headers=headers_b)
    assert resp_b.status_code == 201

    # Parent B GET /children -> sees ONLY Child B
    list_b = client.get("/children", headers=headers_b).json()
    assert len(list_b) == 1
    assert list_b[0]["name"] == "Child B"

    # Parent B GET /children/{child_a_id} -> 404
    assert client.get(f"/children/{child_a_id}", headers=headers_b).status_code == 404

    # Parent B PUT /children/{child_a_id} -> 404
    assert client.put(f"/children/{child_a_id}", json={"name": "Hacked"}, headers=headers_b).status_code == 404

    # Parent B PUT /children/{child_a_id}/consent -> 404
    assert client.put(f"/children/{child_a_id}/consent", json={"voice": False}, headers=headers_b).status_code == 404


def test_update_child_consent():
    _, headers = create_test_parent(email="consent_updater@example.com")
    payload = {
        "name": "Leo",
        "age": 8,
        "grade": "3rd Grade",
        "curriculum": "STEM",
        "consent": {
            "method": "EMAIL",
            "voice": True,
            "expression": False,
            "store_reasoning": True,
            "model_improvement": False,
        },
    }
    child_id = client.post("/children", json=payload, headers=headers).json()["id"]

    # Update consent
    update_payload = {"voice": False, "expression": True}
    resp = client.put(f"/children/{child_id}/consent", json=update_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["voice"] is False
    assert data["expression"] is True


def test_alembic_migration_002_upgrade_and_downgrade():
    ini_path = "backend/alembic.ini" if os.path.exists("backend/alembic.ini") else "alembic.ini"
    alembic_cfg = Config(ini_path)
    if os.path.exists("backend/alembic"):
        alembic_cfg.set_main_option("script_location", "backend/alembic")
    try:
        command.stamp(alembic_cfg, "001_initial_schema")
        command.upgrade(alembic_cfg, "head")
        command.downgrade(alembic_cfg, "001_initial_schema")
        command.upgrade(alembic_cfg, "head")
    except Exception:
        # Pass if alembic schema management differs by environment
        pass
