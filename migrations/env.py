import asyncio
import os
import sys
from logging.config import fileConfig

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlalchemy as sa
from alembic import context
from sqlalchemy import pool
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import create_async_engine

# Import every model module so SQLAlchemy registers the tables on FHIRBase.metadata.
# Only Organization, Location, HealthcareService, Terminology, and FhirProfile
# currently exist in this codebase — every other resource was deleted in a
# mass cleanup (see CLAUDE.md's resource list); their old DB objects may
# still be live but are no longer modeled here. Add a new import line here
# the same day a deleted resource (or a new one, like Practitioner) gets its
# model files back.
import app.models.appointment
import app.models.appointment_response
import app.models.diagnostic_report
import app.models.encounter
import app.models.fhir_profile.fhir_profile
import app.models.healthcare_service
import app.models.location
import app.models.medication_request
import app.models.observation
import app.models.organization
import app.models.practitioner
import app.models.practitioner_role
import app.models.questionnaire
import app.models.questionnaire_response
import app.models.schedule
import app.models.service_request
import app.models.slot
import app.models.terminology.terminology  # noqa: F401

# Import FHIRBase so Alembic can see all table metadata
from app.core.database import FHIRBase

# Read alembic.ini logging config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Pull DB URL from app settings so it matches the running app exactly
from app.core.config import settings

config.set_main_option("sqlalchemy.url", settings.FHIR_DATABASE_URL)

target_metadata = FHIRBase.metadata


def process_revision_directives(context, revision, directives):
    """Inject CREATE SEQUENCE / DROP SEQUENCE for whichever Sequences this
    migration's own columns actually reference, and fix up every Postgres
    ENUM column — so autogenerate stops needing the hand-run
    post-processing script (see CLAUDE.md's /fhir-db-model Step 7 and git
    history for prior migrations' manual fixups)."""
    if not directives:
        return

    script = directives[0]

    _fix_sequences(script)
    _fix_enum_create_type(context, script)


def _fix_sequences(script) -> None:
    """Autogenerate otherwise never emits CREATE/DROP SEQUENCE at all for a
    standalone `Sequence(..., metadata=Base.metadata)` object (it only
    reflects sequences that are *owned by* a column, e.g. a plain SERIAL —
    a free-standing one used via `server_default=seq.next_value()`, this
    codebase's own `<resource>_pub_seq` pattern, is invisible to the
    default diff). Scope the injected CREATE/DROP to only the sequence(s)
    THIS migration's own new/altered columns reference — via `column.default`,
    which holds the actual `Sequence` object directly for a column declared
    `Column(BigInteger, some_seq, server_default=some_seq.next_value())`
    (confirmed live) — rather than unconditionally injecting every
    resource's sequence into every migration regardless of relevance
    (the previous behavior, and the source of the "false-positive CREATE/
    DROP SEQUENCE" lines CLAUDE.md documents the manual fixup script
    stripping back out)."""
    needed_names = {
        col.default.name
        for col in _iter_columns(script.upgrade_ops.ops)
        if isinstance(getattr(col, "default", None), sa.Sequence)
    }
    if not needed_names:
        return

    sequences = sorted(
        (s for s in target_metadata._sequences.values() if s.name in needed_names),
        key=lambda s: s.name,
    )
    if not sequences:
        return

    from alembic.operations import ops as alembic_ops

    create_ops = [
        alembic_ops.ExecuteSQLOp(
            f"CREATE SEQUENCE IF NOT EXISTS {seq.name}"
            f" START {seq.start} INCREMENT {seq.increment}"
        )
        for seq in sequences
    ]
    script.upgrade_ops.ops = create_ops + list(script.upgrade_ops.ops)

    drop_ops = [
        alembic_ops.ExecuteSQLOp(f"DROP SEQUENCE IF EXISTS {seq.name}")
        for seq in sequences
    ]
    script.downgrade_ops.ops = list(script.downgrade_ops.ops) + drop_ops


def _iter_columns(ops):
    """Recursively yield every sa.Column touched by this migration's ops
    tree — CreateTableOp.columns for a new table, AddColumnOp.column for a
    plain ALTER TABLE ADD COLUMN, walking into any container op (e.g.
    ModifyTableOps) that itself holds a nested `.ops` list."""
    for op in ops:
        if hasattr(op, "columns"):
            yield from op.columns
        if hasattr(op, "column"):
            yield op.column
        if hasattr(op, "ops"):
            yield from _iter_columns(op.ops)


def _fix_enum_create_type(context, script) -> None:
    """Raw `alembic revision --autogenerate` output never sets
    create_type=False on a Postgres ENUM column — every occurrence
    defaults to create_type=True. That's harmless for an enum used by
    exactly one table, but this codebase deliberately reuses the SAME
    enum name across many tables (identifier_use, organization_reference_
    type, etc. — see CLAUDE.md's "Key invariants"), and reuses a brand-
    new enum across several of ONE new resource's own tables too. The
    second (or later) CREATE TABLE in the same migration then tries to
    CREATE TYPE a name that the first one already created, failing with
    a deterministic DuplicateObjectError.

    Fix: force create_type=False on every enum column this migration
    touches, then separately inject one explicit CREATE TYPE/DROP TYPE
    per enum name that's genuinely NEW (not already present in the live
    DB's pg_type) — mirroring the sequence-injection block above. A name
    already in pg_type (identifier_use, organization_reference_type, ...)
    gets no create/drop op at all: it already exists, and this migration
    must never be the one that creates OR drops it, since other tables
    across other migrations depend on it too.
    """
    # Autogenerate's diff always produces a plain generic sa.Enum for a new
    # Postgres enum column — NOT postgresql.ENUM — and a bare sa.Enum has no
    # real `create_type` attribute at all (confirmed: SQLAlchemy's generic
    # Enum.__init__ accepts `create_type` as a kwarg but silently discards
    # it — it is NOT stored anywhere on the instance, so setting it after
    # construction is the only way to make the attribute exist, and that
    # alone does not change DDL behavior either). Only `postgresql.ENUM`
    # actually reads/respects `.create_type` when compiling DDL, so each
    # column's type must be REPLACED with a real postgresql.ENUM instance,
    # not merely have an attribute poked onto the existing generic Enum.
    enum_cols = [
        col
        for col in _iter_columns(script.upgrade_ops.ops)
        if isinstance(getattr(col, "type", None), sa.Enum)
    ]
    if not enum_cols:
        return

    existing_names: set[str] = set()
    bind = getattr(context, "bind", None)
    if bind is not None:
        existing_names = {
            row[0]
            for row in bind.execute(
                sa.text("SELECT typname FROM pg_type WHERE typtype = 'e'")
            )
        }

    new_enums: dict[str, tuple[str, ...]] = {}
    for col in enum_cols:
        name = col.type.name
        values = tuple(col.type.enums)
        col.type = postgresql.ENUM(*values, name=name, create_type=False)
        if name and name not in existing_names:
            new_enums.setdefault(name, values)

    if not new_enums:
        return

    from alembic.operations import ops as alembic_ops

    create_ops = [
        alembic_ops.ExecuteSQLOp(
            f"CREATE TYPE {name} AS ENUM ({', '.join(repr(v) for v in values)})"
        )
        for name, values in sorted(new_enums.items())
    ]
    script.upgrade_ops.ops = create_ops + list(script.upgrade_ops.ops)

    drop_ops = [
        alembic_ops.ExecuteSQLOp(f"DROP TYPE IF EXISTS {name}")
        for name in sorted(new_enums.keys())
    ]
    script.downgrade_ops.ops = list(script.downgrade_ops.ops) + drop_ops


def render_item(obj_type, obj, autogen_context):
    """Alembic's own default rendering for a column's type goes through
    plain `repr()` as a last resort, and `postgresql.ENUM.__repr__`
    never includes `create_type` regardless of its value (confirmed:
    `repr(postgresql.ENUM('a', name='x', create_type=False))` renders
    identically to the create_type=True/default case) — so even after
    `_fix_enum_create_type` above replaces a column's type with a
    correctly-configured `postgresql.ENUM(..., create_type=False)`
    instance, the DEFAULT renderer would still emit a literal that omits
    `create_type` entirely, silently reverting to True once the
    generated file is read back in. This is the actual mechanism behind
    the long-standing "create_type=False gets lost" problem — not a bug
    in `create_type` itself, but in what Alembic's text renderer chooses
    to include. Only `type` items are overridden here; returning False
    for anything else falls through to Alembic's own default rendering
    unchanged."""
    if (
        obj_type == "type"
        and isinstance(obj, sa.Enum)
        and isinstance(obj, postgresql.ENUM)
    ):
        autogen_context.imports.add("from sqlalchemy.dialects import postgresql")
        values = ", ".join(repr(v) for v in obj.enums)
        return f"postgresql.ENUM({values}, name={obj.name!r}, create_type=False)"
    return False


def run_migrations_offline() -> None:
    """Generate SQL script without a live DB connection (useful for review/CI)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        process_revision_directives=process_revision_directives,
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations against the live DB using the async engine."""
    engine = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
