import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    role: Mapped[str] = mapped_column(String)
    jd_summary: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="active")

    questions: Mapped[list["Question"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id")
    )
    text: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(String)
    difficulty: Mapped[str | None] = mapped_column(String, nullable=True)
    expected_themes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String)

    session: Mapped["Session"] = relationship(back_populates="questions")
    answers: Mapped[list["Answer"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id")
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id")
    )
    text: Mapped[str] = mapped_column(Text)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    weak_topics: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    is_probe: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    question: Mapped["Question"] = relationship(back_populates="answers")


class EvalLog(Base):
    """One row per LLM call made through a graph node (question gen, probe, eval, summary)."""

    __tablename__ = "eval_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id")
    )
    question_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True
    )
    question_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer)
    model_used: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
