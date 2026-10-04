import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

# Type alias for UUID primary key that falls back cleanly to String/UUID
UUID_ID = UUID(as_uuid=True)


class Parent(Base):
    __tablename__ = "parents"

    id: Mapped[uuid.UUID] = mapped_column(UUID_ID, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    children: Mapped[List["Child"]] = relationship("Child", back_populates="parent", cascade="all, delete-orphan")
    push_tokens: Mapped[List["PushToken"]] = relationship("PushToken", back_populates="parent", cascade="all, delete-orphan")
    consents: Mapped[List["Consent"]] = relationship("Consent", back_populates="parent", cascade="all, delete-orphan")


class PushToken(Base):
    __tablename__ = "push_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID_ID, primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID] = mapped_column(UUID_ID, ForeignKey("parents.id", ondelete="CASCADE"), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    parent: Mapped["Parent"] = relationship("Parent", back_populates="push_tokens")


class Child(Base):
    __tablename__ = "children"

    id: Mapped[uuid.UUID] = mapped_column(UUID_ID, primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID] = mapped_column(UUID_ID, ForeignKey("parents.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    grade: Mapped[str] = mapped_column(String(100), nullable=False)
    curriculum: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="English")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    parent: Mapped["Parent"] = relationship("Parent", back_populates="children")
    consents: Mapped[List["Consent"]] = relationship("Consent", back_populates="child", cascade="all, delete-orphan")
    devices: Mapped[List["Device"]] = relationship("Device", back_populates="child", cascade="all, delete-orphan")
    control: Mapped[Optional["Control"]] = relationship("Control", back_populates="child", uselist=False, cascade="all, delete-orphan")
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="child", cascade="all, delete-orphan")
    mastery_records: Mapped[List["Mastery"]] = relationship("Mastery", back_populates="child", cascade="all, delete-orphan")
    misconceptions: Mapped[List["Misconception"]] = relationship("Misconception", back_populates="child", cascade="all, delete-orphan")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="child", cascade="all, delete-orphan")


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[uuid.UUID] = mapped_column(UUID_ID, primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID] = mapped_column(UUID_ID, ForeignKey("parents.id", ondelete="CASCADE"), nullable=False, index=True)
    child_id: Mapped[uuid.UUID] = mapped_column(UUID_ID, ForeignKey("children.id", ondelete="CASCADE"), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(100), nullable=False)
    consented_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    voice: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expression: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    store_reasoning: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    model_improvement: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    parent: Mapped["Parent"] = relationship("Parent", back_populates="consents")
    child: Mapped["Child"] = relationship("Child", back_populates="consents")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID_ID, primary_key=True, default=uuid.uuid4)
    child_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID_ID, ForeignKey("children.id", ondelete="CASCADE"), nullable=True, index=True)
    pairing_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="offline", nullable=False)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    child: Mapped[Optional["Child"]] = relationship("Child", back_populates="devices")
    control_acks: Mapped[List["ControlAck"]] = relationship("ControlAck", back_populates="device", cascade="all, delete-orphan")


class Control(Base):
    __tablename__ = "controls"
    __table_args__ = (
        CheckConstraint("tries_before_reveal >= 1 AND tries_before_reveal <= 3", name="check_tries_before_reveal_range"),
        CheckConstraint("probe_mode IN ('voice', 'tap', 'both')", name="check_probe_mode_values"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_ID, primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(UUID_ID, ForeignKey("children.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    daily_limit_minutes: Mapped[int] = mapped_column(Integer, default=45, nullable=False)
    schedule: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    paused: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    subjects_allowed: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    content_level: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tries_before_reveal: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    probe_mode: Mapped[str] = mapped_column(String(50), default="both", nullable=False)
    frustration_guard: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    child: Mapped["Child"] = relationship("Child", back_populates="control")


class ControlAck(Base):
    __tablename__ = "control_acks"

    id: Mapped[uuid.UUID] = mapped_column(UUID_ID, primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID_ID, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    control_version: Mapped[int] = mapped_column(Integer, nullable=False)
    acked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    device: Mapped["Device"] = relationship("Device", back_populates="control_acks")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID_ID, primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(UUID_ID, ForeignKey("children.id", ondelete="CASCADE"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    action_mix: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    child: Mapped["Child"] = relationship("Child", back_populates="sessions")
    attempts: Mapped[List["QuestionAttempt"]] = relationship("QuestionAttempt", back_populates="session", cascade="all, delete-orphan")


class QuestionAttempt(Base):
    __tablename__ = "question_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID_ID, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID_ID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    option_picked: Mapped[str] = mapped_column(String(255), nullable=False)
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    tries_to_correct: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    self_corrected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped["Session"] = relationship("Session", back_populates="attempts")
    probe_responses: Mapped[List["ProbeResponse"]] = relationship("ProbeResponse", back_populates="attempt", cascade="all, delete-orphan")


class ProbeResponse(Base):
    __tablename__ = "probe_responses"

    id: Mapped[uuid.UUID] = mapped_column(UUID_ID, primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(UUID_ID, ForeignKey("question_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    reason_text: Mapped[str] = mapped_column(Text, nullable=False)
    input_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    attempt: Mapped["QuestionAttempt"] = relationship("QuestionAttempt", back_populates="probe_responses")


class Mastery(Base):
    __tablename__ = "mastery"
    __table_args__ = (
        CheckConstraint("score >= 0.0 AND score <= 1.0", name="check_mastery_score_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_ID, primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(UUID_ID, ForeignKey("children.id", ondelete="CASCADE"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    child: Mapped["Child"] = relationship("Child", back_populates="mastery_records")


class Misconception(Base):
    __tablename__ = "misconceptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID_ID, primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(UUID_ID, ForeignKey("children.id", ondelete="CASCADE"), nullable=False, index=True)
    concept: Mapped[str] = mapped_column(String(255), nullable=False)
    child_reason: Mapped[str] = mapped_column(Text, nullable=False)
    parent_tip: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    child: Mapped["Child"] = relationship("Child", back_populates="misconceptions")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID_ID, primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(UUID_ID, ForeignKey("children.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    child: Mapped["Child"] = relationship("Child", back_populates="alerts")
