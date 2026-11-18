"""slot: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: g4d9f6b2c058
Revises: f3c8e5a1b947
Create Date: 2026-11-23 10:00:00.000000

Medplum-style storage for Slot (see SlotModel's docstring), same as the other
resources already moved (Organization 5b1969c2ec19, Location 8c41d2e7a9b3,
Practitioner a7d3f19c2b64, HealthcareService c9f5b2d7e813, Endpoint
d1a6c3e8f924, PractitionerRole e2b7d4f9a035, Schedule f3c8e5a1b947). The whole
FHIR resource moves into `slot.content`; every column/table that survives is a
search index for one of the FHIR R4 Slot search parameters (or
`_id`/`_lastUpdated`), derived from `content`:

  slot: start, schedule_reference/_type/_id/_identifier_system/_value (kept; they
      feed `start` and `schedule` / `schedule:identifier`), `status` (rebuilt as a
      Postgres enum holding the real FHIR codes, see below); new: content
  slot_identifier: one row per identifier x type.coding
  slot_token (new): one row per coding for `service-category`, `service-type`,
      `specialty` and `appointment-type`
  dropped: slot_service_category / _service_type / _specialty /
      _appointment_type_coding (and every *_coding), slot_identifier_type_coding,
      and the main-table columns with no search parameter (end, overbooked,
      comment, extension, appointment_type_text, and the schedule display /
      identifier-detail columns)

`slot.status`: the old `slot_status` enum stored Python member names
(`busy_unavailable`, `entered_in_error`), not the FHIR codes. It is dropped and
recreated with the real codes (`busy-unavailable`, `entered-in-error`, ...), and
every row's status is rebuilt from `content` (where the migration writes the
real FHIR code). `schedule_id` becomes nullable (R4 requires a schedule, but
that is the validator's rule, not the database's), and the single-column
`ix_slot_schedule_id` is replaced by a composite (schedule_id, start) index.

upgrade: (1) builds `content` for every existing row from the old columns and
tables — a frozen copy of the old to_fhir_slot() logic (but keeping a
reference's raw string, so an absolute URL is not lost), so this migration never
depends on application code that has since changed; (2) drops the old child
tables and recreates the index tables; (3) rebuilds the index from `content`.

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
revision: str = 'g4d9f6b2c058'
down_revision: Union[str, None] = 'f3c8e5a1b947'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUS = ('busy', 'free', 'busy-unavailable', 'busy-tentative', 'entered-in-error')


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


def _concepts(bind, table, coding_table, fk, slot_pk):
    """A 0..* CodeableConcept list held as parent rows (text) + coding rows."""
    out = []
    for r in _rows(bind, f"SELECT * FROM {table} WHERE slot_pk = :pk ORDER BY id", pk=slot_pk):
        codings = _rows(bind, f"SELECT * FROM {coding_table} WHERE {fk} = :id ORDER BY id", id=r["id"])
        out.append({"coding": [_coding(c) for c in codings], "text": r["text"]})
    return out


def _identifier(bind, i):
    codings = _rows(bind, "SELECT * FROM slot_identifier_type_coding "
                          "WHERE slot_identifier_id = :id ORDER BY id", id=i["id"])
    return {
        "use": i["use"],
        "type": {"coding": [_coding(c) for c in codings], "text": i["type_text"]},
        "system": i["system"], "value": i["value"],
        "period": _period(i["period_start"], i["period_end"]),
        "assigner": _old_reference(i, "assigner"),
    }


def _fhir_status(old):
    """The old enum stored member names (`busy_unavailable`); FHIR codes are hyphenated."""
    return old.replace("_", "-") if old else None


def _build_content(bind, slot):
    pk = slot["id"]
    identifiers = [_identifier(bind, i) for i in _rows(
        bind, "SELECT * FROM slot_identifier WHERE slot_pk = :pk ORDER BY id", pk=pk)]
    appointment_codings = _rows(
        bind, "SELECT * FROM slot_appointment_type_coding WHERE slot_pk = :pk ORDER BY id", pk=pk)
    return _prune({
        "extension": _json(slot["extension"]),
        "identifier": identifiers,
        "serviceCategory": _concepts(bind, "slot_service_category", "slot_service_category_coding",
                                     "slot_service_category_id", pk),
        "serviceType": _concepts(bind, "slot_service_type", "slot_service_type_coding",
                                 "slot_service_type_id", pk),
        "specialty": _concepts(bind, "slot_specialty", "slot_specialty_coding", "slot_specialty_id", pk),
        "appointmentType": {"coding": [_coding(c) for c in appointment_codings],
                            "text": slot["appointment_type_text"]},
        "schedule": _old_reference(slot, "schedule"),
        "status": _fhir_status(str(slot["status"]) if slot["status"] is not None else None),
        "start": _iso(slot["start"]),
        "end": _iso(slot["end"]),
        "overbooked": slot["overbooked"],
        "comment": slot["comment"],
    })


def _backfill_content(bind):
    for slot in _rows(bind, "SELECT * FROM slot"):
        bind.execute(
            sa.text("UPDATE slot SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, slot)), "id": slot["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

TOKEN_PARAMS = {"service-category": "serviceCategory", "service-type": "serviceType",
                "specialty": "specialty", "appointment-type": "appointmentType"}


def _relative(ref, resource_type):
    return ref if ref and ref.startswith(f"{resource_type}/") else None


def _concept_list(value):
    """`appointmentType` is a single CodeableConcept (0..1); the others are lists."""
    if isinstance(value, dict):
        return [value]
    return list(value or [])


def _rebuild_index(bind):
    for row in _rows(bind, "SELECT id, content FROM slot"):
        pk, doc = row["id"], _json(row["content"])
        status = doc.get("status")
        start = _range(str(doc["start"])) if doc.get("start") else None
        schedule = doc.get("schedule") or {}
        local = _relative(schedule.get("reference"), "Schedule")
        tail = local.split("/", 1)[1] if local else ""
        sident = schedule.get("identifier") or {}
        bind.execute(sa.text(
            "UPDATE slot SET status = CAST(:st AS slot_status), start = :start, schedule_reference = :sr, "
            "schedule_type = CAST(:sty AS schedule_reference_type), schedule_id = :si, "
            "schedule_identifier_system = :sis, schedule_identifier_value = :siv WHERE id = :pk"),
            {"st": status if status in _STATUS else None, "start": start[0] if start else None,
             "sr": schedule.get("reference"), "sty": "Schedule" if local and tail.isdigit() else None,
             "si": int(tail) if tail.isdigit() else None, "sis": sident.get("system"),
             "siv": sident.get("value"), "pk": pk})
        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO slot_identifier (slot_pk, system, value, type_system, type_code, "
                    "type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})
        for param, element in TOKEN_PARAMS.items():
            for cc in _concept_list(doc.get(element)):
                text = _norm(cc.get("text"))
                codings = [c for c in cc.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
                for c in codings or ([{}] if text else []):
                    bind.execute(sa.text(
                        "INSERT INTO slot_token (slot_pk, param, system, code, display_norm, text_norm) "
                        "VALUES (:pk, :p, :s, :c, :d, :t)"),
                        {"pk": pk, "p": param, "s": c.get("system"), "c": c.get("code"),
                         "d": _norm(c.get("display")), "t": text})


# Children first.
_OLD_CHILD_TABLES = (
    "slot_identifier_type_coding", "slot_identifier",
    "slot_service_category_coding", "slot_service_category",
    "slot_service_type_coding", "slot_service_type",
    "slot_specialty_coding", "slot_specialty",
    "slot_appointment_type_coding",
)

_OLD_MAIN_COLUMNS = (
    "end", "overbooked", "comment", "extension", "appointment_type_text", "schedule_display",
    "schedule_identifier_use", "schedule_identifier_type_system", "schedule_identifier_type_version",
    "schedule_identifier_type_code", "schedule_identifier_type_display", "schedule_identifier_type_text",
    "schedule_identifier_type_user_selected", "schedule_identifier_period_start",
    "schedule_identifier_period_end",
)


def _fk():
    return sa.Column("slot_pk", sa.BigInteger(), sa.ForeignKey("slot.id"), nullable=False)


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('slot', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are
    # rebuilt from it below.
    for table in _OLD_CHILD_TABLES:
        op.drop_table(table)
    for column in _OLD_MAIN_COLUMNS:
        op.drop_column('slot', column)

    # status: the old enum held Python member names; recreate it with the FHIR codes.
    op.drop_column('slot', 'status')
    op.execute("DROP TYPE IF EXISTS slot_status")
    postgresql.ENUM(*_STATUS, name='slot_status').create(bind, checkfirst=True)
    op.add_column('slot', sa.Column('status', postgresql.ENUM(*_STATUS, name='slot_status', create_type=False), nullable=True))

    op.alter_column('slot', 'start', nullable=True)
    op.alter_column('slot', 'schedule_id', nullable=True)
    op.alter_column('slot', 'schedule_type', nullable=True)  # an absolute-URL Schedule has no resolved type
    op.execute("DROP INDEX IF EXISTS ix_slot_schedule_id")
    op.create_index(op.f('ix_slot_start'), 'slot', ['start'], unique=False)
    op.create_index('ix_slot_schedule_start', 'slot', ['schedule_id', 'start'], unique=False)

    op.create_table(
        'slot_identifier',
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
    op.create_index(op.f('ix_slot_identifier_slot_pk'), 'slot_identifier', ['slot_pk'], unique=False)
    op.create_index(op.f('ix_slot_identifier_value'), 'slot_identifier', ['value'], unique=False)

    op.create_table(
        'slot_token',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('param', sa.String(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_slot_token_slot_pk'), 'slot_token', ['slot_pk'], unique=False)
    op.create_index('ix_slot_token_param_code', 'slot_token', ['param', 'code'], unique=False)

    _rebuild_index(bind)
    op.alter_column('slot', 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "slot content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
