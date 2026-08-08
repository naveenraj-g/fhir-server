import math
import os

# Must be set before any app module is imported so pydantic-settings reads them.
os.environ.setdefault("FHIR_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("IAM_ISSUER", "https://test.example.com")
os.environ.setdefault("IAM_JWKS_URL", "https://test.example.com/.well-known/jwks.json")

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import pytest
from fastapi import Request
from httpx import AsyncClient, ASGITransport
from sqlalchemy import BigInteger, Sequence as SASequence, event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.core.database import FHIRBase
from app.main import app, container, mount_routers  # triggers all model & router imports
from app.auth.dependencies import get_current_user
from app.middleware.rate_limit import RateLimitMiddleware

# Router mounting now happens inside app.main's lifespan (at real ASGI
# startup), not at module-import time — but httpx's ASGITransport (used by
# every test client fixture below) never triggers the ASGI lifespan
# protocol. Mount routes once here instead, synchronously, before any test
# runs — mount_routers() has no async/DB/Redis side effects, only route
# registration, so this is safe to call directly.
mount_routers(app)

# ── SQLite fallback for Postgres-only column types ────────────────────────────
# TSVECTOR (app/models/terminology/terminology.py) and ARRAY
# (app/models/practitioner_role/practitioner_role.py) have no SQLite
# equivalent — create_all() builds every table in FHIRBase.metadata at once,
# so without these shims every test in the suite errors during fixture setup,
# not just those two resources'.

from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR
from sqlalchemy.ext.compiler import compiles


@compiles(TSVECTOR, "sqlite")
def _tsvector_as_text(element, compiler, **kw):
    return "TEXT"


@compiles(ARRAY, "sqlite")
def _array_as_text(element, compiler, **kw):
    return "TEXT"


@compiles(JSONB, "sqlite")
def _jsonb_as_text(element, compiler, **kw):
    return "JSON"

# ── Disable rate limiting for tests ───────────────────────────────────────────
# The in-process sliding-window limiter accumulates across tests when Redis is
# unavailable, causing 429s.  We bypass dispatch entirely in the test process.


async def _no_rate_limit(self, request, call_next):
    return await call_next(request)


RateLimitMiddleware.dispatch = _no_rate_limit

# ── Sequence simulation ────────────────────────────────────────────────────────
# PostgreSQL sequences are not supported by SQLite.  We strip the server_default
# (which would emit nextval() DDL) and use an in-process counter in the ORM
# before_insert event instead.

_seq_counters: dict[str, int] = {}
_defaults_stripped = False


def _strip_server_defaults() -> None:
    """Remove nextval() server_defaults from all columns once before create_all().

    SQLite doesn't support sequences so we strip DefaultClause(next_value(...))
    from every sequence column.  func.now() server_defaults (created_at etc.) are
    left intact — SQLite compiles those to CURRENT_TIMESTAMP.
    """
    global _defaults_stripped
    if _defaults_stripped:
        return
    for table in FHIRBase.metadata.tables.values():
        for col in table.columns:
            sd = col.server_default
            if sd is None:
                continue
            arg = getattr(sd, "arg", None)
            if arg is not None and type(arg).__name__ == "next_value":
                col.server_default = None
    _defaults_stripped = True


@event.listens_for(FHIRBase, "before_insert", propagate=True)
def _simulate_sequence(mapper, connection, target) -> None:
    """Assign sequence-based IDs using a per-sequence Python counter.

    In SQLAlchemy, when a Sequence is passed as a positional Column arg it is
    stored directly as col.default (a Sequence instance, NOT wrapped in
    ColumnDefault).  We check isinstance(col.default, SASequence) to detect it.
    """
    for col in mapper.local_table.columns:
        if isinstance(col.default, SASequence):
            if getattr(target, col.name, None) is None:
                seq: SASequence = col.default
                key = seq.name
                if key not in _seq_counters:
                    _seq_counters[key] = seq.start or 1
                else:
                    _seq_counters[key] += seq.increment or 1
                setattr(target, col.name, _seq_counters[key])


_pk_counters: dict[str, int] = {}


@event.listens_for(FHIRBase, "before_insert", propagate=True)
def _simulate_bigint_pk(mapper, connection, target) -> None:
    """SQLite's implicit rowid-alias autoincrement only kicks in for a
    primary key column whose DDL literally reads INTEGER PRIMARY KEY —
    BigInteger compiles to BIGINT, which doesn't get that treatment, so it's
    left NULL on insert (NOT NULL constraint failure) unless simulated here
    the same way Sequence-based columns are above. Every resource's `id` and
    every sub-resource table's `id` is BigInteger, so this covers the whole
    schema."""
    pk_cols = list(mapper.local_table.primary_key.columns)
    if len(pk_cols) != 1:
        return
    col = pk_cols[0]
    if not isinstance(col.type, BigInteger):
        return
    if getattr(target, col.name, None) is not None:
        return
    key = mapper.local_table.name
    _pk_counters[key] = _pk_counters.get(key, 0) + 1
    setattr(target, col.name, _pk_counters[key])


# ── TestDatabase ───────────────────────────────────────────────────────────────

class TestDatabase:
    """Drop-in replacement for app.core.database.Database using a pre-built engine."""

    def __init__(self, engine):
        self.engine = engine
        self.session_maker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def disconnect(self) -> None:
        pass  # lifecycle is managed by the fixture

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        session: AsyncSession = self.session_maker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Auth helpers ───────────────────────────────────────────────────────────────

def make_test_user(
    sub: str = "u-test",
    org_id: str = "org-test",
    permissions: list[str] | None = None,
):
    """Factory that returns a get_current_user override for tests."""
    if permissions is None:
        permissions = [
            "patient:create",
            "patient:read",
            "patient:update",
            "patient:delete",
        ]

    async def _dep(request: Request) -> None:
        request.state.user = {
            "sub": sub,
            "activeOrganizationId": org_id,
            "permissions": permissions,
        }

    return _dep


# ── SQLite math functions ─────────────────────────────────────────────────────
# Location's `near` search parameter computes a great-circle distance in SQL
# (see app/repository/location/core.py). Postgres has these built in; SQLite
# ships none of them unless compiled with SQLITE_ENABLE_MATH_FUNCTIONS, so
# register them per-connection or every `near` query errors under test while
# working fine in production — exactly the gap that hides a broken filter.

_SQLITE_MATH_FUNCS = {
    "radians": math.radians,
    "acos": math.acos,
    "sin": math.sin,
    "cos": math.cos,
}


def _register_sqlite_math(dbapi_conn, _connection_record) -> None:
    for name, fn in _SQLITE_MATH_FUNCS.items():
        dbapi_conn.create_function(name, 1, fn)
    # least/greatest are Postgres-only spellings of SQLite's min/max.
    dbapi_conn.create_function("least", 2, min)
    dbapi_conn.create_function("greatest", 2, max)


# ── Shared engine fixture ──────────────────────────────────────────────────────

@pytest.fixture
async def _engine():
    """Single in-memory SQLite engine per test (StaticPool → one connection)."""
    _strip_server_defaults()
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    event.listen(eng.sync_engine, "connect", _register_sqlite_math)
    async with eng.begin() as conn:
        await conn.run_sync(FHIRBase.metadata.create_all)
    yield eng
    await eng.dispose()


# ── Primary test client ────────────────────────────────────────────────────────

@pytest.fixture
async def client(_engine):
    """AsyncClient authenticated as u-test / org-test with full patient permissions."""
    test_db = TestDatabase(_engine)
    container.core.database.override(test_db)
    app.dependency_overrides[get_current_user] = make_test_user()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.pop(get_current_user, None)
    container.core.database.reset_override()


# ── Alternate-org client (same database, different identity) ───────────────────

@pytest.fixture
async def other_client(_engine):
    """AsyncClient authenticated as u-other / org-other, sharing the same database."""
    test_db = TestDatabase(_engine)
    container.core.database.override(test_db)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other",
        org_id="org-other",
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.pop(get_current_user, None)
    container.core.database.reset_override()
