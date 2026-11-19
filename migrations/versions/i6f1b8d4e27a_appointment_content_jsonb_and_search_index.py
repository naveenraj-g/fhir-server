"""appointment: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: i6f1b8d4e27a
Revises: h5e0a7c3d169
Create Date: 2026-11-24 10:00:00.000000

Medplum-style storage for Appointment (see AppointmentModel's docstring), same
as the other resources already moved (Organization 5b1969c2ec19, Location
8c41d2e7a9b3, Practitioner a7d3f19c2b64, HealthcareService c9f5b2d7e813,
Endpoint d1a6c3e8f924, PractitionerRole e2b7d4f9a035, Schedule f3c8e5a1b947,
Slot g4d9f6b2c058, Patient h5e0a7c3d169). The whole FHIR resource moves into
`appointment.content`; every column/table that survives is a search index for
one of the FHIR R4 Appointment search parameters (or `_id`/`_lastUpdated`),
derived from `content`:

  appointment: status (rebuilt as a Postgres enum holding the real FHIR codes,
      see below), start (kept; feeds `date`); new: content
  appointment_identifier: one row per identifier x type.coding
  appointment_token (new): one row per coding for `service-category`,
      `service-type`, `specialty`, `appointment-type` and `reason-code`
  appointment_reference (new): one row per Reference for `based-on`,
      `reason-reference`, `slot` and `supporting-info`
  appointment_participant: one row per participant for `actor`, `patient`,
      `practitioner`, `location` and `part-status`
  dropped: every other old child table (service_category/_service_type/
      _specialty/_reason_code and their *_coding, reason_reference,
      supporting_information, slot, based_on, requested_period,
      participant_type(_coding), identifier_type_coding, cancelation_reason_coding,
      appointment_type_coding), the main-table columns with no search parameter
      (end, minutes_duration, created, priority, description, comment,
      patient_instruction, cancelation_reason_text, appointment_type_text,
      extension), and the six enums that only the old tables used.

`appointment.status`: the old `appointment_status` enum stored Python member
names (`entered_in_error`, `checked_in`), not the FHIR codes. It is dropped and
recreated with the real codes (`entered-in-error`, `checked-in`, ...), and every
row's status is rebuilt from `content` (where the migration writes the real FHIR
code). `appointment_participant` and `appointment_identifier` keep their table
names but get the index shape (the old tables are dropped first).

upgrade: (1) builds `content` for every existing row from the old columns and
tables — a frozen copy of the old to_fhir_appointment() logic (but keeping a
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
revision: str = 'i6f1b8d4e27a'
down_revision: Union[str, None] = 'h5e0a7c3d169'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUS = ('proposed', 'pending', 'booked', 'arrived', 'fulfilled', 'cancelled', 'noshow',
           'entered-in-error', 'checked-in', 'waitlist')


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
    """Frozen copy of the lower bound of app.fhir.search.values.parse_date for a
    bare FHIR date / dateTime: (first instant it denotes in UTC, None). None if
    it doesn't parse (only `start` is read, so the upper bound is not needed)."""
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
    return low.astimezone(UTC), None


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


def _concepts(bind, table, coding_table, fk, appointment_pk):
    """A 0..* CodeableConcept list held as parent rows (text) + coding rows."""
    out = []
    for r in _rows(bind, f"SELECT * FROM {table} WHERE appointment_pk = :pk ORDER BY id", pk=appointment_pk):
        codings = _rows(bind, f"SELECT * FROM {coding_table} WHERE {fk} = :id ORDER BY id", id=r["id"])
        out.append({"coding": [_coding(c) for c in codings], "text": r["text"]})
    return out


def _references(bind, table, appointment_pk):
    return [_old_reference(r, "reference") for r in _rows(
        bind, f"SELECT * FROM {table} WHERE appointment_pk = :pk ORDER BY id", pk=appointment_pk)]


def _identifier(bind, i):
    codings = _rows(bind, "SELECT * FROM appointment_identifier_type_coding "
                          "WHERE appointment_identifier_id = :id ORDER BY id", id=i["id"])
    return {
        "use": i["use"],
        "type": {"coding": [_coding(c) for c in codings], "text": i["type_text"]},
        "system": i["system"], "value": i["value"],
        "period": _period(i["period_start"], i["period_end"]),
        "assigner": _old_reference(i, "assigner"),
    }


def _hyphenate(old):
    """The old enums stored member names (`entered_in_error`); FHIR codes are hyphenated."""
    return str(old).replace("_", "-") if old is not None else None


def _participant(bind, p):
    types = []
    for t in _rows(bind, "SELECT * FROM appointment_participant_type "
                         "WHERE appointment_participant_id = :id ORDER BY id", id=p["id"]):
        codings = _rows(bind, "SELECT * FROM appointment_participant_type_coding "
                              "WHERE appointment_participant_type_id = :id ORDER BY id", id=t["id"])
        types.append({"coding": [_coding(c) for c in codings], "text": t["text"]})
    return {
        "type": types,
        "actor": _old_reference(p, "actor"),
        "required": _hyphenate(p["required"]),
        "status": _hyphenate(p["status"]),
        "period": _period(p["period_start"], p["period_end"]),
    }


def _build_content(bind, a):
    pk = a["id"]
    identifiers = [_identifier(bind, i) for i in _rows(
        bind, "SELECT * FROM appointment_identifier WHERE appointment_pk = :pk ORDER BY id", pk=pk)]
    cancelation = _rows(
        bind, "SELECT * FROM appointment_cancelation_reason_coding WHERE appointment_pk = :pk ORDER BY id", pk=pk)
    appointment_type = _rows(
        bind, "SELECT * FROM appointment_appointment_type_coding WHERE appointment_pk = :pk ORDER BY id", pk=pk)
    participants = [_participant(bind, p) for p in _rows(
        bind, "SELECT * FROM appointment_participant WHERE appointment_pk = :pk ORDER BY id", pk=pk)]
    requested = [_period(r["start"], r["end"]) for r in _rows(
        bind, "SELECT * FROM appointment_requested_period WHERE appointment_pk = :pk ORDER BY id", pk=pk)]
    return _prune({
        "extension": _json(a["extension"]),
        "identifier": identifiers,
        "status": _hyphenate(a["status"]),
        "cancelationReason": {"coding": [_coding(c) for c in cancelation], "text": a["cancelation_reason_text"]},
        "serviceCategory": _concepts(bind, "appointment_service_category", "appointment_service_category_coding",
                                     "appointment_service_category_id", pk),
        "serviceType": _concepts(bind, "appointment_service_type", "appointment_service_type_coding",
                                 "appointment_service_type_id", pk),
        "specialty": _concepts(bind, "appointment_specialty", "appointment_specialty_coding",
                               "appointment_specialty_id", pk),
        "appointmentType": {"coding": [_coding(c) for c in appointment_type],
                            "text": a["appointment_type_text"]},
        "reasonCode": _concepts(bind, "appointment_reason_code", "appointment_reason_code_coding",
                                "appointment_reason_code_id", pk),
        "reasonReference": _references(bind, "appointment_reason_reference", pk),
        "priority": a["priority"],
        "description": a["description"],
        "supportingInformation": _references(bind, "appointment_supporting_information", pk),
        "start": _iso(a["start"]),
        "end": _iso(a["end"]),
        "minutesDuration": a["minutes_duration"],
        "slot": _references(bind, "appointment_slot", pk),
        "created": _iso(a["created"]),
        "comment": a["comment"],
        "patientInstruction": a["patient_instruction"],
        "basedOn": _references(bind, "appointment_based_on", pk),
        "participant": participants,
        "requestedPeriod": requested,
    })


def _backfill_content(bind):
    for appointment in _rows(bind, "SELECT * FROM appointment"):
        bind.execute(
            sa.text("UPDATE appointment SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, appointment)), "id": appointment["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

TOKEN_PARAMS = {"service-category": "serviceCategory", "service-type": "serviceType",
                "specialty": "specialty", "appointment-type": "appointmentType", "reason-code": "reasonCode"}
REFERENCE_PARAMS = {"based-on": ("basedOn", ("ServiceRequest",)),
                    "reason-reference": ("reasonReference",
                                         ("Condition", "Procedure", "Observation", "ImmunizationRecommendation")),
                    "slot": ("slot", ("Slot",)),
                    "supporting-info": ("supportingInformation", None)}
ACTOR_TYPES = ("Patient", "Practitioner", "PractitionerRole", "RelatedPerson", "Device", "HealthcareService",
               "Location")

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")


def _split(reference, allowed):
    """('Slot', 220001) for a relative Type/<id> of an allowed type (None = any)."""
    match = _REF.match(reference or "")
    if match and (allowed is None or match["type"] in allowed):
        return match["type"], int(match["id"])
    return None


def _concept_list(value):
    """`appointmentType` is a single CodeableConcept (0..1); the others are lists."""
    if isinstance(value, dict):
        return [value]
    return list(value or [])


def _rebuild_index(bind):
    for row in _rows(bind, "SELECT id, content FROM appointment"):
        pk, doc = row["id"], _json(row["content"])
        status = doc.get("status")
        start = _range(str(doc["start"])) if doc.get("start") else None
        bind.execute(sa.text(
            "UPDATE appointment SET status = CAST(:st AS appointment_status), start = :start WHERE id = :pk"),
            {"st": status if status in _STATUS else None, "start": start[0] if start else None, "pk": pk})
        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO appointment_identifier (appointment_pk, system, value, type_system, type_code, "
                    "type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})
        for param, element in TOKEN_PARAMS.items():
            for cc in _concept_list(doc.get(element)):
                text = _norm(cc.get("text"))
                codings = [c for c in cc.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
                for c in codings or ([{}] if text else []):
                    bind.execute(sa.text(
                        "INSERT INTO appointment_token (appointment_pk, param, system, code, display_norm, text_norm) "
                        "VALUES (:pk, :p, :s, :c, :d, :t)"),
                        {"pk": pk, "p": param, "s": c.get("system"), "c": c.get("code"),
                         "d": _norm(c.get("display")), "t": text})
        for param, (element, allowed) in REFERENCE_PARAMS.items():
            for ref in doc.get(element) or []:
                reference = ref.get("reference")
                ident = ref.get("identifier") or {}
                if not (reference or ident.get("value")):
                    continue
                parsed = _split(reference, allowed)
                bind.execute(sa.text(
                    "INSERT INTO appointment_reference (appointment_pk, param, reference_reference, reference_type, "
                    "reference_id, reference_identifier_system, reference_identifier_value) "
                    "VALUES (:pk, :p, :r, :t, :i, :isys, :ival)"),
                    {"pk": pk, "p": param, "r": reference, "t": parsed[0] if parsed else None,
                     "i": parsed[1] if parsed else None, "isys": ident.get("system"), "ival": ident.get("value")})
        for participant in doc.get("participant") or []:
            actor = participant.get("actor") or {}
            reference = actor.get("reference")
            ident = actor.get("identifier") or {}
            parsed = _split(reference, ACTOR_TYPES)
            bind.execute(sa.text(
                "INSERT INTO appointment_participant (appointment_pk, reference_reference, reference_type, "
                "reference_id, reference_identifier_system, reference_identifier_value, status) "
                "VALUES (:pk, :r, :t, :i, :isys, :ival, :st)"),
                {"pk": pk, "r": reference, "t": parsed[0] if parsed else None,
                 "i": parsed[1] if parsed else None, "isys": ident.get("system"), "ival": ident.get("value"),
                 "st": participant.get("status")})


# Children first (grandchildren before their parents).
_OLD_CHILD_TABLES = (
    "appointment_participant_type_coding", "appointment_participant_type", "appointment_participant",
    "appointment_identifier_type_coding", "appointment_identifier",
    "appointment_service_category_coding", "appointment_service_category",
    "appointment_service_type_coding", "appointment_service_type",
    "appointment_specialty_coding", "appointment_specialty",
    "appointment_reason_code_coding", "appointment_reason_code",
    "appointment_reason_reference", "appointment_supporting_information",
    "appointment_slot", "appointment_based_on", "appointment_requested_period",
    "appointment_cancelation_reason_coding", "appointment_appointment_type_coding",
)

_OLD_MAIN_COLUMNS = (
    "end", "minutes_duration", "created", "priority", "description", "comment", "patient_instruction",
    "cancelation_reason_text", "appointment_type_text", "extension",
)

# Enums only the old child tables used (appointment_reference_type is shared
# with appointment_response and stays).
_OLD_ENUMS = (
    "appointment_based_on_reference_type", "appointment_participant_actor_reference_type",
    "appointment_participant_required", "appointment_participation_status",
    "appointment_reason_reference_type", "appointment_slot_reference_type",
)


def _fk():
    return sa.Column("appointment_pk", sa.BigInteger(), sa.ForeignKey("appointment.id"), nullable=False)


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('appointment', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are
    # rebuilt from it below.
    for table in _OLD_CHILD_TABLES:
        op.drop_table(table)
    for column in _OLD_MAIN_COLUMNS:
        op.drop_column('appointment', column)
    for enum in _OLD_ENUMS:
        op.execute(f"DROP TYPE IF EXISTS {enum}")

    # status: the old enum held Python member names; recreate it with the FHIR codes.
    op.drop_column('appointment', 'status')
    op.execute("DROP TYPE IF EXISTS appointment_status")
    postgresql.ENUM(*_STATUS, name='appointment_status').create(bind, checkfirst=True)
    op.add_column('appointment', sa.Column(
        'status', postgresql.ENUM(*_STATUS, name='appointment_status', create_type=False), nullable=True))
    op.create_index(op.f('ix_appointment_start'), 'appointment', ['start'], unique=False)

    op.create_table(
        'appointment_identifier',
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
    op.create_index(op.f('ix_appointment_identifier_appointment_pk'), 'appointment_identifier', ['appointment_pk'])
    op.create_index(op.f('ix_appointment_identifier_value'), 'appointment_identifier', ['value'])

    op.create_table(
        'appointment_token',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('param', sa.String(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_appointment_token_appointment_pk'), 'appointment_token', ['appointment_pk'])
    op.create_index('ix_appointment_token_param_code', 'appointment_token', ['param', 'code'])

    op.create_table(
        'appointment_reference',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('param', sa.String(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_identifier_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_value', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_appointment_reference_appointment_pk'), 'appointment_reference', ['appointment_pk'])
    op.create_index('ix_appointment_reference_param_type_id', 'appointment_reference',
                    ['param', 'reference_type', 'reference_id'])

    op.create_table(
        'appointment_participant',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_identifier_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_value', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_appointment_participant_appointment_pk'), 'appointment_participant', ['appointment_pk'])
    op.create_index('ix_appointment_participant_type_id', 'appointment_participant',
                    ['reference_type', 'reference_id'])

    _rebuild_index(bind)
    op.alter_column('appointment', 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "appointment content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
