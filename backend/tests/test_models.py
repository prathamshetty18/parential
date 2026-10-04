import socket
import uuid
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session as SqlSession, sessionmaker
import pytest

from app.config import settings
from app.db import Base
from app.models import (
    Alert,
    Child,
    Consent,
    Control,
    ControlAck,
    Device,
    Mastery,
    Misconception,
    Parent,
    ProbeResponse,
    PushToken,
    QuestionAttempt,
    Session,
)

EXPECTED_TABLES = {
    "parents",
    "push_tokens",
    "children",
    "consents",
    "devices",
    "controls",
    "control_acks",
    "sessions",
    "question_attempts",
    "probe_responses",
    "mastery",
    "misconceptions",
    "alerts",
}


def get_test_db_url():
    url = settings.DATABASE_URL
    if "@db:" in url or "@db/" in url:
        try:
            socket.gethostbyname("db")
        except socket.gaierror:
            url = url.replace("@db:", "@localhost:").replace("@db/", "@localhost/")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


@pytest.fixture(scope="module")
def db_engine():
    assert "postgresql" in settings.DATABASE_URL, f"Database URL must be PostgreSQL, got: {settings.DATABASE_URL}"
    url = get_test_db_url()
    try:
        engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            pass
    except Exception:
        pytest.skip(f"PostgreSQL server is not reachable at {url}")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    SessionMaker = sessionmaker(bind=db_engine)
    session = SessionMaker()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_thirteen_tables_exist(db_engine):
    inspector = inspect(db_engine)
    existing_tables = set(inspector.get_table_names())
    assert EXPECTED_TABLES.issubset(existing_tables), f"Missing tables: {EXPECTED_TABLES - existing_tables}"
    assert len(existing_tables.intersection(EXPECTED_TABLES)) == 13


def test_child_delete_cascade_removes_all_child_owned_rows(db_session: SqlSession):
    # 1. Create Parent
    parent = Parent(
        id=uuid.uuid4(),
        email=f"cascade_test_{uuid.uuid4()}@example.com",
        password_hash="hashed_secret"
    )
    db_session.add(parent)
    db_session.commit()

    # 2. Create Child
    child = Child(
        id=uuid.uuid4(),
        parent_id=parent.id,
        name="Leo",
        age=8,
        grade="3rd Grade",
        curriculum="STEM",
        language="English"
    )
    db_session.add(child)
    db_session.commit()

    # 3. Create Child-owned records: Device, Control, Session, Mastery, Misconception, Alert, Consent
    device = Device(
        id=uuid.uuid4(),
        child_id=child.id,
        pairing_token=f"TOKEN_{uuid.uuid4()}",
        status="online"
    )
    control = Control(
        id=uuid.uuid4(),
        child_id=child.id,
        version=1,
        daily_limit_minutes=45,
        tries_before_reveal=2,
        probe_mode="both",
        frustration_guard=True
    )
    consent = Consent(
        id=uuid.uuid4(),
        parent_id=parent.id,
        child_id=child.id,
        method="DPDP_VERIFIED",
        voice=True,
        expression=False,
        store_reasoning=True,
        model_improvement=False
    )
    session_record = Session(
        id=uuid.uuid4(),
        child_id=child.id,
        subject="Science"
    )
    mastery = Mastery(
        id=uuid.uuid4(),
        child_id=child.id,
        subject="Science",
        topic="Gravity",
        score=0.85
    )
    misconception = Misconception(
        id=uuid.uuid4(),
        child_id=child.id,
        concept="Gravity underwater",
        child_reason="Thought gravity turns off in pool",
        parent_tip="Explain buoyancy force"
    )
    alert = Alert(
        id=uuid.uuid4(),
        child_id=child.id,
        type="DAILY_LIMIT",
        message="Daily limit reached"
    )

    db_session.add_all([device, control, consent, session_record, mastery, misconception, alert])
    db_session.commit()

    # 4. Create Session -> QuestionAttempt -> ProbeResponse
    attempt = QuestionAttempt(
        id=uuid.uuid4(),
        session_id=session_record.id,
        question_text="Why do heavy ships float?",
        option_picked="Option B",
        correct=False,
        tries_to_correct=1,
        self_corrected=False
    )
    db_session.add(attempt)
    db_session.commit()

    probe_resp = ProbeResponse(
        id=uuid.uuid4(),
        attempt_id=attempt.id,
        reason_text="Weightless in water",
        input_mode="voice"
    )
    db_session.add(probe_resp)
    db_session.commit()

    child_id = child.id
    session_id = session_record.id
    attempt_id = attempt.id

    # Verify rows exist before delete
    assert db_session.execute(select(Session).where(Session.child_id == child_id)).scalar_one_or_none() is not None
    assert db_session.execute(select(QuestionAttempt).where(QuestionAttempt.session_id == session_id)).scalar_one_or_none() is not None
    assert db_session.execute(select(ProbeResponse).where(ProbeResponse.attempt_id == attempt_id)).scalar_one_or_none() is not None
    assert db_session.execute(select(Mastery).where(Mastery.child_id == child_id)).scalar_one_or_none() is not None
    assert db_session.execute(select(Misconception).where(Misconception.child_id == child_id)).scalar_one_or_none() is not None
    assert db_session.execute(select(Alert).where(Alert.child_id == child_id)).scalar_one_or_none() is not None
    assert db_session.execute(select(Control).where(Control.child_id == child_id)).scalar_one_or_none() is not None
    assert db_session.execute(select(Device).where(Device.child_id == child_id)).scalar_one_or_none() is not None

    # 5. Delete Child row
    db_session.delete(child)
    db_session.commit()

    # 6. Assert ON DELETE CASCADE removed all child-owned rows
    assert db_session.execute(select(Session).where(Session.child_id == child_id)).scalar_one_or_none() is None
    assert db_session.execute(select(QuestionAttempt).where(QuestionAttempt.session_id == session_id)).scalar_one_or_none() is None
    assert db_session.execute(select(ProbeResponse).where(ProbeResponse.attempt_id == attempt_id)).scalar_one_or_none() is None
    assert db_session.execute(select(Mastery).where(Mastery.child_id == child_id)).scalar_one_or_none() is None
    assert db_session.execute(select(Misconception).where(Misconception.child_id == child_id)).scalar_one_or_none() is None
    assert db_session.execute(select(Alert).where(Alert.child_id == child_id)).scalar_one_or_none() is None
    assert db_session.execute(select(Control).where(Control.child_id == child_id)).scalar_one_or_none() is None
    assert db_session.execute(select(Device).where(Device.child_id == child_id)).scalar_one_or_none() is None
