"""schedule: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: f3c8e5a1b947
Revises: e2b7d4f9a035
Create Date: 2026-11-22 10:00:00.000000

Medplum-style storage for Schedule (see ScheduleModel's docstring), same as
Organization (5b1969c2ec19), Location (8c41d2e7a9b3), Practitioner
(a7d3f19c2b64), HealthcareService (c9f5b2d7e813), Endpoint (d1a6c3e8f924) and
PractitionerRole (e2b7d4f9a035). The whole FHIR resource moves into
`schedule.content`; every column/table that survives is a search index for one
of the FHIR R4 Schedule search parameters (or `_id`/`_lastUpdated`), derived
from `content`:

  schedule: active, planning_horizon_start/planning_horizon_end (kept; they
      feed `date`, now as the half-open [start, end) range — see the upgrade
      note below); new: content
  schedule_identifier: one row per identifier x type.coding
  schedule_token (new): one row per coding for `service-category`,
      `service-type` and `specialty`
  schedule_actor: one row per actor Reference (reference_type/reference_id
      resolved for a relative `Type/<id>` naming one of the seven allowed types)
  dropped: schedule_service_category / _service_type / _specialty (and every
      *_coding), schedule_identifier_type_coding, and the main-table columns
      with no search parameter (comment, extension), plus the now-unused
      `schedule_actor_reference_type` Postgres enum.

upgrade: (1) builds `content` for every existing row from the old columns and
tables — a frozen copy of the old to_fhir_schedule() logic (but keeping a
reference's raw string, so an absolute URL is not lost), so this migration never
depends on application code that has since changed; (2) drops the old child
tables and recreates the index tables; (3) rebuilds the index from `content` —
including `planning_horizon_end`, which used to hold Period.end as written and
now holds the first instant *after* it (so the Period matches `date` searches as
a range at its written precision).

downgrade: not supported. Everything the old schema held is preserved in
`content`, but rebuilding the old normalized tables from it is not implemented —
restore from a backup taken before upgrading.
"""
import json
import re
import unicodedata
from datetime import UTC, date, datetime, time, timedelta, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f3c8e5a1b947'
down_revision: Union[str, None] = 'e2b7d4f9a035'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── shared helpers (frozen — never import application code here) ────────────

def _prune(value):
    if isinstance(value, dict):
        out = {k: _prune(v) for k, v in value.items()}
        return {k: v for k, v in out.items() if v is not None and v != [] and v != {}}
    if isinstance(value, list):
        out = [_prune(v) for v in value]
        return [v for v in out if v is not None and v != [] and v != {}]
    return value


def _iso(value):
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return value


def _period(start, end):
    return {"start": _iso(start), "end": _iso(end)}


def _json(value):
    """A raw text() query can hand JSONB back as a string."""
    return json.loads(value) if isinstance(value, str) else value


def _rows(bind, sql, **params):
    return bind.execute(sa.text(sql), params).mappings().all()


def _norm(text):
    """Frozen copy of app.fhir.search.values.normalize."""
    if text is None:
        return None
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


_DATE_RE = re.compile(
    r"^(?P<y>\d{4})(?:-(?P<m>\d{2})(?:-(?P<d>\d{2})(?:T(?P<H>\d{2}):(?P<M>\d{2})(?::(?P<S>\d{2})(?P<f>\.\d+)?)?"
    r"(?P<tz>Z|[+-]\d{2}:\d{2})?)?)?)?$"
)


def _range(value):
    """Frozen copy of app.fhir.search.values.parse_date for a bare FHIR date /
    dateTime: the half-open UTC range [low, high) it denotes at its written
    precision. None if it doesn't parse."""
    match = _DATE_RE.match(value or "")
    if not match:
        return None
    g = match.groupdict()
    tz = UTC
    if g["tz"] and g["tz"] != "Z":
        sign = 1 if g["tz"][0] == "+" else -1
        tz = timezone(sign * timedelta(hours=int(g["tz"][1:3]), minutes=int(g["tz"][4:6])))
    try:
        low = datetime(int(g["y"]), int(g["m"] or 1), int(g["d"] or 1), int(g["H"] or 0), int(g["M"] or 0),
                       int(g["S"] or 0), int(((g["f"] or ".0")[1:] + "000000")[:6]), tzinfo=tz)
    except ValueError:
        return None
    if g["S"]:
        high = low + (timedelta(seconds=1) if not g["f"] else timedelta(microseconds=10 ** (6 - min(len(g["f"]) - 1, 6))))
    elif g["M"]:
        high = low + timedelta(minutes=1)
    elif g["H"]:
        high = low + timedelta(hours=1)
    elif g["d"]:
        high = low + timedelta(days=1)
    elif g["m"]:
        month = low.month
        high = low.replace(year=low.year + (month // 12), month=month % 12 + 1)
    else:
        high = low.replace(year=low.year + 1)
    return low.astimezone(UTC), high.astimezone(UTC)


def _period_bounds(period):
    """(start, end) instants for the index columns: the first instant of
    Period.start and the first instant after Period.end; None = open."""
    period = period or {}
    start = _range(str(period["start"])) if period.get("start") else None
    end = _range(str(period["end"])) if period.get("end") else None
    return (start[0] if start else None), (end[1] if end else None)


# ── upgrade: old columns/tables -> content (frozen copy of the old mapper) ───

def _coding(c):
    return {"system": c["system"], "version": c["version"], "code": c["code"],
            "display": c["display"], "userSelected": c["user_selected"]}


def _fallback_identifier(row, prefix):
    p = f"{prefix}_identifier_"
    return {
        "use": row[p + "use"],
        "type": {
            "coding": [{
                "system": row[p + "type_system"], "version": row[p + "type_version"],
                "code": row[p + "type_code"], "display": row[p + "type_display"],
                "userSelected": row[p + "type_user_selected"],
            }],
            "text": row[p + "type_text"],
        },
        "system": row[p + "system"],
        "value": row[p + "value"],
        "period": _period(row[p + "period_start"], row[p + "period_end"]),
    }


def _old_reference(row, prefix):
    """Keeps the raw reference string when there is one (an absolute URL to
    another server lives only there), else Type/id from the resolved columns."""
    raw = row[f"{prefix}_reference"]
    if not raw and row[f"{prefix}_type"] and row[f"{prefix}_id"]:
        raw = f"{row[prefix + '_type']}/{row[prefix + '_id']}"
    return {
        "reference": raw,
        "display": row[f"{prefix}_display"],
        "identifier": _fallback_identifier(row, prefix),
    }


def _concepts(bind, table, coding_table, fk, schedule_pk):
    """A 0..* CodeableConcept list held as parent rows (text) + coding rows."""
    out = []
    for r in _rows(bind, f"SELECT * FROM {table} WHERE schedule_pk = :pk ORDER BY id", pk=schedule_pk):
        codings = _rows(bind, f"SELECT * FROM {coding_table} WHERE {fk} = :id ORDER BY id", id=r["id"])
        out.append({"coding": [_coding(c) for c in codings], "text": r["text"]})
    return out


def _identifier(bind, i):
    codings = _rows(bind, "SELECT * FROM schedule_identifier_type_coding "
                          "WHERE schedule_identifier_id = :id ORDER BY id", id=i["id"])
    return {
        "use": i["use"],
        "type": {"coding": [_coding(c) for c in codings], "text": i["type_text"]},
        "system": i["system"], "value": i["value"],
        "period": _period(i["period_start"], i["period_end"]),
        "assigner": _old_reference(i, "assigner"),
    }


def _build_content(bind, schedule):
    pk = schedule["id"]
    identifiers = [_identifier(bind, i) for i in _rows(
        bind, "SELECT * FROM schedule_identifier WHERE schedule_pk = :pk ORDER BY id", pk=pk)]
    actors = [_old_reference(a, "reference") for a in _rows(
        bind, "SELECT * FROM schedule_actor WHERE schedule_pk = :pk ORDER BY id", pk=pk)]
    return _prune({
        "extension": _json(schedule["extension"]),
        "identifier": identifiers,
        "active": schedule["active"],
        "serviceCategory": _concepts(bind, "schedule_service_category", "schedule_service_category_coding",
                                     "schedule_service_category_id", pk),
        "serviceType": _concepts(bind, "schedule_service_type", "schedule_service_type_coding",
                                 "schedule_service_type_id", pk),
        "specialty": _concepts(bind, "schedule_specialty", "schedule_specialty_coding",
                               "schedule_specialty_id", pk),
        "actor": actors,
        "planningHorizon": _period(schedule["planning_horizon_start"], schedule["planning_horizon_end"]),
        "comment": schedule["comment"],
    })


def _backfill_content(bind):
    for schedule in _rows(bind, "SELECT * FROM schedule"):
        bind.execute(
            sa.text("UPDATE schedule SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, schedule)), "id": schedule["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

TOKEN_PARAMS = {"service-category": "serviceCategory", "service-type": "serviceType", "specialty": "specialty"}
ACTOR_TYPES = ("Patient", "Practitioner", "PractitionerRole", "RelatedPerson", "Device", "HealthcareService", "Location")
_ACTOR_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")


def _rebuild_index(bind):
    for row in _rows(bind, "SELECT id, content FROM schedule"):
        pk, doc = row["id"], _json(row["content"])
        start, end = _period_bounds(doc.get("planningHorizon"))
        bind.execute(sa.text("UPDATE schedule SET planning_horizon_start = :s, planning_horizon_end = :e WHERE id = :pk"),
                     {"s": start, "e": end, "pk": pk})
        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO schedule_identifier (schedule_pk, system, value, type_system, type_code, "
                    "type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})
        for param, element in TOKEN_PARAMS.items():
            for cc in doc.get(element) or []:
                text = _norm(cc.get("text"))
                codings = [c for c in cc.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
                for c in codings or ([{}] if text else []):
                    bind.execute(sa.text(
                        "INSERT INTO schedule_token (schedule_pk, param, system, code, display_norm, text_norm) "
                        "VALUES (:pk, :p, :s, :c, :d, :t)"),
                        {"pk": pk, "p": param, "s": c.get("system"), "c": c.get("code"),
                         "d": _norm(c.get("display")), "t": text})
        for actor in doc.get("actor") or []:
            reference = actor.get("reference")
            ident = actor.get("identifier") or {}
            if not (reference or ident.get("value")):
                continue
            match = _ACTOR_REF.match(reference or "")
            typed = match and match["type"] in ACTOR_TYPES
            bind.execute(sa.text(
                "INSERT INTO schedule_actor (schedule_pk, reference_reference, reference_type, reference_id, "
                "reference_identifier_system, reference_identifier_value) VALUES (:pk, :r, :t, :i, :is_, :iv)"),
                {"pk": pk, "r": reference, "t": match["type"] if typed else None,
                 "i": int(match["id"]) if typed else None, "is_": ident.get("system"), "iv": ident.get("value")})


# Children first.
_OLD_CHILD_TABLES = (
    "schedule_identifier_type_coding", "schedule_identifier",
    "schedule_service_category_coding", "schedule_service_category",
    "schedule_service_type_coding", "schedule_service_type",
    "schedule_specialty_coding", "schedule_specialty",
    "schedule_actor",
)

_OLD_MAIN_COLUMNS = ("extension", "comment")


def _fk():
    return sa.Column("schedule_pk", sa.BigInteger(), sa.ForeignKey("schedule.id"), nullable=False)


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('schedule', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are
    # rebuilt from it below.
    for table in _OLD_CHILD_TABLES:
        op.drop_table(table)
    for column in _OLD_MAIN_COLUMNS:
        op.drop_column('schedule', column)
    op.create_index('ix_schedule_planning_horizon', 'schedule', ['planning_horizon_start', 'planning_horizon_end'], unique=False)

    op.create_table(
        'schedule_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_text_norm', sa.String(), nullable=True),
        sa.Column('type_display_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_schedule_identifier_schedule_pk'), 'schedule_identifier', ['schedule_pk'], unique=False)
    op.create_index(op.f('ix_schedule_identifier_value'), 'schedule_identifier', ['value'], unique=False)

    op.create_table(
        'schedule_token',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('param', sa.String(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_schedule_token_schedule_pk'), 'schedule_token', ['schedule_pk'], unique=False)
    op.create_index('ix_schedule_token_param_code', 'schedule_token', ['param', 'code'], unique=False)

    op.create_table(
        'schedule_actor',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_identifier_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_value', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_schedule_actor_schedule_pk'), 'schedule_actor', ['schedule_pk'], unique=False)
    op.create_index('ix_schedule_actor_type_id', 'schedule_actor', ['reference_type', 'reference_id'], unique=False)

    _rebuild_index(bind)
    op.alter_column('schedule', 'content', nullable=False)

    # This enum type belonged only to the dropped schedule_actor table.
    op.execute("DROP TYPE IF EXISTS schedule_actor_reference_type")


def downgrade() -> None:
    raise NotImplementedError(
        "schedule content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
