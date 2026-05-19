"""
Async SQLAlchemy engine + session factory for the Interview Coach backend.

The DATABASE_URL in .env uses the standard postgresql:// scheme (Supabase /
pgbouncer style).  asyncpg requires the postgresql+asyncpg:// scheme, so we
swap the prefix here automatically.
"""

import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── Load env ──────────────────────────────────────────────────────────────────
load_dotenv()

_raw_url: str | None = os.getenv("DATABASE_URL")
if not _raw_url:
    raise RuntimeError("DATABASE_URL is not set in the environment / .env file")

# Ensure asyncpg driver is specified
if _raw_url.startswith("postgresql://"):
    DATABASE_URL = _raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _raw_url.startswith("postgres://"):
    DATABASE_URL = _raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = _raw_url  # already has the correct scheme

# pgBouncer (Supabase pooler) doesn't support prepared statements
_connect_args: dict = {"statement_cache_size": 0} if "pgbouncer=true" in DATABASE_URL else {}

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── FastAPI dependency ────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session; close it when the request finishes."""
    async with AsyncSessionLocal() as session:
        yield session
