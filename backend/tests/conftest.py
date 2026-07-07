import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.database import get_db
from db.models import Answer, Base, Question
from db.models import Session as InterviewSession
from main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def engine():
    eng = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest.fixture
async def db(engine):
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
async def client(db):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def test_session(db):
    session = InterviewSession(
        id=uuid.uuid4(),
        role="Backend Engineer",
        jd_summary="Requires FastAPI, PostgreSQL, LLM experience",
        status="active",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@pytest.fixture
async def test_question(db, test_session):
    question = Question(
        id=uuid.uuid4(),
        session_id=test_session.id,
        text="Tell me about a time you reduced latency.",
        question_type="behavioral",
        difficulty="medium",
        expected_themes=["optimization", "async"],
        order_index=0,
        source="gemini",
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question


@pytest.fixture
async def test_answer(db, test_question, test_session):
    answer = Answer(
        id=uuid.uuid4(),
        question_id=test_question.id,
        session_id=test_session.id,
        text="At my previous role I reduced latency from 2s to 200ms by optimizing the DB query pipeline.",
        score=7,
        feedback="Good structure but could go deeper on trade-offs.",
        weak_topics=[],
        is_probe=False,
    )
    db.add(answer)
    await db.commit()
    await db.refresh(answer)
    return answer
