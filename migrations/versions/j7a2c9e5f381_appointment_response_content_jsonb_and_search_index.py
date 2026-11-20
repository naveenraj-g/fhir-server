"""appointment_response: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: j7a2c9e5f381
Revises: i6f1b8d4e27a
Create Date: 2026-11-25 10:00:00.000000

Medplum-style storage for AppointmentResponse (see AppointmentResponseModel's
docstring), same as the other resources already moved (Organization
5b1969c2ec19, Location 8c41d2e7a9b3, Practitioner a7d3f19c2b64,
HealthcareService c9f5b2d7e813, Endpoint d1a6c3e8f924, PractitionerRole
e2b7d4f9a035, Schedule f3c8e5a1b947, Slot g4d9f6b2c058, Patient h5e0a7c3d169,
Appointment i6f1b8d4e27a). The whole FHIR resource moves into
`appointment_response.content`; every column/table that survives is a search
index for one of the FHIR R4 AppointmentResponse search parameters (or
`_id`/`_lastUpdated`), derived from `content`:

  appointment_response: participant_status (rebuilt as a Postgres enum holding
      the real FHIR codes, see below), appointment_reference/_type/_id/
      _identifier_system/_value and actor_reference/_type/_id/
      _identifier_system/_value (kept; `_type` becomes a plain string);
      new: content
  appointment_response_identifier: one row per identifier x type.coding
  dropped: the participant_type(_coding) and identifier_type_coding child
      tables, the main-table columns with no search parameter (start, end,
      comment, extension, appointment_display, actor_display) and the
      logical-reference columns no search reads (identifier use/type/period),
      and the two enums only the old table used.

`participant_status`: the old `appointment_response_participant_status` enum
stored Python member names (`needs_action`), not the FHIR code. It is dropped
and recreated with the real codes (`needs-action`, ...), and every row's status
is rebuilt from `content` (where the migration writes the real FHIR code).

upgrade: (1) builds `content` for every existing row from the old columns and
tables — a frozen copy of the old to_fhir_appointment_response() logic (but
keeping a reference's raw string, so an absolute URL is not lost), so this
migration never depends on application code that has since changed; (2) drops
the old child tables/columns and recreates the index table; (3) rebuilds the
index from `content`.

downgrade: not supported. Everything the old schema held is preserved in
`content`, but rebuilding the old normalized tables from it is not implemented —
restore from a backup taken before upgrading.
"""
import json
import re
import unicodedata
from datetime import date, datetime, time
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'j7a2c9e5f381'
down_revision: Union[str, None] = 'i6f1b8d4e27a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUS = ('accepted', 'declined', 'tentative', 'needs-action')


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


def _identifier(bind, i):
    codings = _rows(bind, "SELECT * FROM appointment_response_identifier_type_coding "
                          "WHERE appointment_response_identifier_id = :id ORDER BY id", id=i["id"])
    return {
        "use": i["use"],
        "type": {"coding": [_coding(c) for c in codings], "text": i["type_text"]},
        "system": i["system"], "value": i["value"],
        "period": _period(i["period_start"], i["period_end"]),
        "assigner": _old_reference(i, "assigner"),
    }


def _hyphenate(old):
    """The old enum stored member names (`needs_action`); FHIR codes are hyphenated."""
    return str(old).replace("_", "-") if old is not None else None


def _participant_types(bind, pk):
    out = []
    for t in _rows(bind, "SELECT * FROM appointment_response_participant_type "
                         "WHERE appointment_response_pk = :pk ORDER BY id", pk=pk):
        codings = _rows(bind, "SELECT * FROM appointment_response_participant_type_coding "
                              "WHERE appointment_response_participant_type_id = :id ORDER BY id", id=t["id"])
        out.append({"coding": [_coding(c) for c in codings], "text": t["text"]})
    return out


def _build_content(bind, r):
    pk = r["id"]
    identifiers = [_identifier(bind, i) for i in _rows(
        bind, "SELECT * FROM appointment_response_identifier WHERE appointment_response_pk = :pk ORDER BY id", pk=pk)]
    return _prune({
        "extension": _json(r["extension"]),
        "identifier": identifiers,
        "appointment": _old_reference(r, "appointment"),
        "start": _iso(r["start"]),
        "end": _iso(r["end"]),
        "participantType": _participant_types(bind, pk),
        "actor": _old_reference(r, "actor"),
        "participantStatus": _hyphenate(r["participant_status"]),
        "comment": r["comment"],
    })


def _backfill_content(bind):
    for row in _rows(bind, "SELECT * FROM appointment_response"):
        bind.execute(
            sa.text("UPDATE appointment_response SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, row)), "id": row["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

ACTOR_TYPES = ("Patient", "Practitioner", "PractitionerRole", "RelatedPerson", "Device", "HealthcareService",
               "Location")

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")


def _split(reference, allowed):
    """('Patient', 10001) for a relative Type/<id> of an allowed type."""
    match = _REF.match(reference or "")
    if match and match["type"] in allowed:
        return match["type"], int(match["id"])
    return None


def _rebuild_index(bind):
    for row in _rows(bind, "SELECT id, content FROM appointment_response"):
        pk, doc = row["id"], _json(row["content"])
        status = doc.get("participantStatus")
        appointment = doc.get("appointment") or {}
        actor = doc.get("actor") or {}
        a_ident = appointment.get("identifier") or {}
        x_ident = actor.get("identifier") or {}
        a_parsed = _split(appointment.get("reference"), ("Appointment",))
        x_parsed = _split(actor.get("reference"), ACTOR_TYPES)
        bind.execute(sa.text(
            "UPDATE appointment_response SET "
            "participant_status = CAST(:st AS appointment_response_participant_status), "
            "appointment_reference = :ar, appointment_type = :at, appointment_id = :ai, "
            "appointment_identifier_system = :asys, appointment_identifier_value = :aval, "
            "actor_reference = :xr, actor_type = :xt, actor_id = :xi, "
            "actor_identifier_system = :xsys, actor_identifier_value = :xval WHERE id = :pk"),
            {"st": status if status in _STATUS else None, "pk": pk,
             "ar": appointment.get("reference"), "at": a_parsed[0] if a_parsed else None,
             "ai": a_parsed[1] if a_parsed else None, "asys": a_ident.get("system"), "aval": a_ident.get("value"),
             "xr": actor.get("reference"), "xt": x_parsed[0] if x_parsed else None,
             "xi": x_parsed[1] if x_parsed else None, "xsys": x_ident.get("system"), "xval": x_ident.get("value")})
        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO appointment_response_identifier (appointment_response_pk, system, value, "
                    "type_system, type_code, type_text_norm, type_display_norm) "
                    "VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})


# Children first (grandchildren before their parents).
_OLD_CHILD_TABLES = (
    "appointment_response_participant_type_coding", "appointment_response_participant_type",
    "appointment_response_identifier_type_coding", "appointment_response_identifier",
)

_OLD_MAIN_COLUMNS = (
    "start", "end", "comment", "extension", "participant_status",
    "appointment_display", "appointment_identifier_use", "appointment_identifier_type_system",
    "appointment_identifier_type_version", "appointment_identifier_type_code",
    "appointment_identifier_type_display", "appointment_identifier_type_text",
    "appointment_identifier_type_user_selected", "appointment_identifier_period_start",
    "appointment_identifier_period_end",
    "actor_display", "actor_identifier_use", "actor_identifier_type_system", "actor_identifier_type_version",
    "actor_identifier_type_code", "actor_identifier_type_display", "actor_identifier_type_text",
    "actor_identifier_type_user_selected", "actor_identifier_period_start", "actor_identifier_period_end",
)


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('appointment_response',
                  sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are
    # rebuilt from it below.
    for table in _OLD_CHILD_TABLES:
        op.drop_table(table)
    for column in _OLD_MAIN_COLUMNS:
        op.drop_column('appointment_response', column)

    # The two reference-type columns were enums; they are plain strings now
    # (appointment_reference_type is shared with Encounter and stays).
    op.alter_column('appointment_response', 'appointment_type', type_=sa.String(), nullable=True,
                    postgresql_using='appointment_type::text')
    op.alter_column('appointment_response', 'actor_type', type_=sa.String(), nullable=True,
                    postgresql_using='actor_type::text')
    # appointment_id was NOT NULL; an absolute-URL appointment has no local id.
    op.alter_column('appointment_response', 'appointment_id', nullable=True)
    op.execute("DROP TYPE IF EXISTS appointment_response_actor_reference_type")
    op.execute("DROP INDEX IF EXISTS ix_appointment_response_actor_id")
    op.create_index('ix_appointment_response_actor_type_id', 'appointment_response', ['actor_type', 'actor_id'])

    # participant_status: the old enum held Python member names; recreate it with the FHIR codes.
    op.execute("DROP TYPE IF EXISTS appointment_response_participant_status")
    postgresql.ENUM(*_STATUS, name='appointment_response_participant_status').create(bind, checkfirst=True)
    op.add_column('appointment_response', sa.Column(
        'participant_status',
        postgresql.ENUM(*_STATUS, name='appointment_response_participant_status', create_type=False),
        nullable=True))

    op.create_table(
        'appointment_response_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('appointment_response_pk', sa.BigInteger(), sa.ForeignKey('appointment_response.id'),
                  nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_text_norm', sa.String(), nullable=True),
        sa.Column('type_display_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_appointment_response_identifier_appointment_response_pk'),
                    'appointment_response_identifier', ['appointment_response_pk'])
    op.create_index(op.f('ix_appointment_response_identifier_value'), 'appointment_response_identifier', ['value'])

    _rebuild_index(bind)
    op.alter_column('appointment_response', 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "appointment_response content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
