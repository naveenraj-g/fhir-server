"""practitioner_role: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: e2b7d4f9a035
Revises: d1a6c3e8f924
Create Date: 2026-11-21 10:00:00.000000

Medplum-style storage for PractitionerRole (see PractitionerRoleModel's
docstring), same as Organization (5b1969c2ec19), Location (8c41d2e7a9b3),
Practitioner (a7d3f19c2b64), HealthcareService (c9f5b2d7e813) and Endpoint
(d1a6c3e8f924). The whole FHIR resource moves into
`practitioner_role.content`; every column/table that survives is a search index
for one of the FHIR R4 PractitionerRole search parameters (or
`_id`/`_lastUpdated`), derived from `content`:

  practitioner_role: active, period_start/period_end (kept; they feed `date`,
      now as the half-open [start, end) range — see the upgrade note below),
      practitioner_reference/_type/_id/_identifier_system/_value and
      organization_reference/_type/_id/_identifier_system/_value (kept; they
      feed `practitioner` / `organization` and their `:identifier`); new: content
  practitioner_role_identifier: one row per identifier x type.coding
  practitioner_role_telecom: system, value, use (for telecom / phone / email)
  practitioner_role_token (new): one row per coding for `role` and `specialty`
  practitioner_role_reference (new): one row per Reference for `location`,
      `service` (healthcareService) and `endpoint`
  dropped: every other child table (code, specialty, location,
      healthcare_service, endpoint, available_time, not_available and every
      *_coding) and the main-table columns with no search parameter (extension,
      availability_exceptions, and the practitioner / organization display and
      identifier-detail columns), plus the now-unused Postgres enum types.
      (`practitioner_reference_type` is shared with other tables and is kept.)

upgrade: (1) builds `content` for every existing row from the old columns and
tables — a frozen copy of the old to_fhir_practitioner_role() logic (but keeping
a reference's raw string, so an absolute URL is not lost), so this migration
never depends on application code that has since changed; (2) drops the old
child tables and creates the index tables; (3) rebuilds the index from
`content` — including `period_end`, which used to hold Period.end as written and
now holds the first instant *after* it (so a Period matches `date` searches as a
range at its written precision).

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
revision: str = 'e2b7d4f9a035'
down_revision: Union[str, None] = 'd1a6c3e8f924'
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


def _concepts(bind, table, coding_table, fk, role_pk):
    """A 0..* CodeableConcept list held as parent rows (text) + coding rows."""
    out = []
    for r in _rows(bind, f"SELECT * FROM {table} WHERE practitioner_role_pk = :pk ORDER BY id", pk=role_pk):
        codings = _rows(bind, f"SELECT * FROM {coding_table} WHERE {fk} = :id ORDER BY id", id=r["id"])
        out.append({"coding": [_coding(c) for c in codings], "text": r["text"]})
    return out


def _identifier(bind, i):
    codings = _rows(bind, "SELECT * FROM practitioner_role_identifier_type_coding "
                          "WHERE practitioner_role_identifier_id = :id ORDER BY id", id=i["id"])
    return {
        "use": i["use"],
        "type": {"coding": [_coding(c) for c in codings], "text": i["type_text"]},
        "system": i["system"], "value": i["value"],
        "period": _period(i["period_start"], i["period_end"]),
        "assigner": _old_reference(i, "assigner"),
    }


def _references(bind, table, role_pk):
    return [_old_reference(r, "reference") for r in _rows(
        bind, f"SELECT * FROM {table} WHERE practitioner_role_pk = :pk ORDER BY id", pk=role_pk)]


def _build_content(bind, role):
    pk = role["id"]
    identifiers = [_identifier(bind, i) for i in _rows(
        bind, "SELECT * FROM practitioner_role_identifier WHERE practitioner_role_pk = :pk ORDER BY id", pk=pk)]
    telecoms = [{
        "system": t["system"], "value": t["value"], "use": t["use"], "rank": t["rank"],
        "period": _period(t["period_start"], t["period_end"]),
    } for t in _rows(bind, "SELECT * FROM practitioner_role_telecom WHERE practitioner_role_pk = :pk ORDER BY id", pk=pk)]
    available = [{
        "daysOfWeek": [str(d) for d in a["days_of_week"]] if a["days_of_week"] else None,
        "allDay": a["all_day"],
        "availableStartTime": _iso(a["available_start_time"]),
        "availableEndTime": _iso(a["available_end_time"]),
    } for a in _rows(bind, "SELECT * FROM practitioner_role_available_time WHERE practitioner_role_pk = :pk ORDER BY id", pk=pk)]
    not_available = [{
        "description": n["description"], "during": _period(n["during_start"], n["during_end"]),
    } for n in _rows(bind, "SELECT * FROM practitioner_role_not_available WHERE practitioner_role_pk = :pk ORDER BY id", pk=pk)]
    return _prune({
        "extension": _json(role["extension"]),
        "identifier": identifiers,
        "active": role["active"],
        "period": _period(role["period_start"], role["period_end"]),
        "practitioner": _old_reference(role, "practitioner"),
        "organization": _old_reference(role, "organization"),
        "code": _concepts(bind, "practitioner_role_code", "practitioner_role_code_coding",
                          "practitioner_role_code_id", pk),
        "specialty": _concepts(bind, "practitioner_role_specialty", "practitioner_role_specialty_coding",
                               "practitioner_role_specialty_id", pk),
        "location": _references(bind, "practitioner_role_location", pk),
        "healthcareService": _references(bind, "practitioner_role_healthcare_service", pk),
        "telecom": telecoms,
        "availableTime": available,
        "notAvailable": not_available,
        "availabilityExceptions": role["availability_exceptions"],
        "endpoint": _references(bind, "practitioner_role_endpoint", pk),
    })


def _backfill_content(bind):
    for role in _rows(bind, "SELECT * FROM practitioner_role"):
        bind.execute(
            sa.text("UPDATE practitioner_role SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, role)), "id": role["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

TOKEN_PARAMS = {"role": "code", "specialty": "specialty"}
REFERENCE_PARAMS = {"location": ("location", "Location"), "service": ("healthcareService", "HealthcareService"),
                    "endpoint": ("endpoint", "Endpoint")}


def _relative(ref, resource_type):
    return ref if ref and ref.startswith(f"{resource_type}/") else None


def _ref_columns(ref, resource_type):
    ref = ref or {}
    local = _relative(ref.get("reference"), resource_type)
    tail = local.split("/", 1)[1] if local else ""
    ident = ref.get("identifier") or {}
    return {
        "r": ref.get("reference"),
        "t": resource_type if local and tail.isdigit() else None,
        "i": int(tail) if tail.isdigit() else None,
        "is_": ident.get("system"),
        "iv": ident.get("value"),
    }


def _rebuild_index(bind):
    for row in _rows(bind, "SELECT id, content FROM practitioner_role"):
        pk, doc = row["id"], _json(row["content"])
        start, end = _period_bounds(doc.get("period"))
        prac = _ref_columns(doc.get("practitioner"), "Practitioner")
        org = _ref_columns(doc.get("organization"), "Organization")
        bind.execute(sa.text(
            "UPDATE practitioner_role SET period_start = :ps, period_end = :pe, "
            "practitioner_reference = :pr, practitioner_type = CAST(:pt AS practitioner_reference_type), "
            "practitioner_id = :pi, practitioner_identifier_system = :pis, practitioner_identifier_value = :piv, "
            "organization_reference = :or_, organization_type = CAST(:ot AS organization_reference_type), "
            "organization_id = :oi, organization_identifier_system = :ois, organization_identifier_value = :oiv "
            "WHERE id = :pk"),
            {"ps": start, "pe": end, "pr": prac["r"], "pt": prac["t"], "pi": prac["i"], "pis": prac["is_"],
             "piv": prac["iv"], "or_": org["r"], "ot": org["t"], "oi": org["i"], "ois": org["is_"],
             "oiv": org["iv"], "pk": pk})
        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO practitioner_role_identifier (practitioner_role_pk, system, value, type_system, "
                    "type_code, type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})
        for t in doc.get("telecom") or []:
            if not t.get("value"):
                continue
            bind.execute(sa.text(
                "INSERT INTO practitioner_role_telecom (practitioner_role_pk, system, value, use) "
                "VALUES (:pk, :s, :v, :u)"),
                {"pk": pk, "s": t.get("system"), "v": t["value"], "u": t.get("use")})
        for param, element in TOKEN_PARAMS.items():
            for cc in doc.get(element) or []:
                text = _norm(cc.get("text"))
                codings = [c for c in cc.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
                for c in codings or ([{}] if text else []):
                    bind.execute(sa.text(
                        "INSERT INTO practitioner_role_token (practitioner_role_pk, param, system, code, "
                        "display_norm, text_norm) VALUES (:pk, :p, :s, :c, :d, :t)"),
                        {"pk": pk, "p": param, "s": c.get("system"), "c": c.get("code"),
                         "d": _norm(c.get("display")), "t": text})
        for param, (element, rtype) in REFERENCE_PARAMS.items():
            for ref in doc.get(element) or []:
                cols = _ref_columns(ref, rtype)
                if not (cols["r"] or cols["iv"]):
                    continue
                bind.execute(sa.text(
                    "INSERT INTO practitioner_role_reference (practitioner_role_pk, param, reference_reference, "
                    "reference_type, reference_id, reference_identifier_system, reference_identifier_value) "
                    "VALUES (:pk, :p, :r, :t, :i, :is_, :iv)"),
                    {"pk": pk, "p": param, **cols})


# Children first.
_OLD_CHILD_TABLES = (
    "practitioner_role_identifier_type_coding", "practitioner_role_identifier",
    "practitioner_role_code_coding", "practitioner_role_code",
    "practitioner_role_specialty_coding", "practitioner_role_specialty",
    "practitioner_role_available_time", "practitioner_role_not_available",
    "practitioner_role_location", "practitioner_role_healthcare_service", "practitioner_role_endpoint",
    "practitioner_role_telecom",
)

_OLD_MAIN_COLUMNS = (
    "extension", "availability_exceptions",
    "practitioner_display", "practitioner_identifier_use", "practitioner_identifier_type_system",
    "practitioner_identifier_type_version", "practitioner_identifier_type_code",
    "practitioner_identifier_type_display", "practitioner_identifier_type_text",
    "practitioner_identifier_type_user_selected", "practitioner_identifier_period_start",
    "practitioner_identifier_period_end",
    "organization_display", "organization_identifier_use", "organization_identifier_type_system",
    "organization_identifier_type_version", "organization_identifier_type_code",
    "organization_identifier_type_display", "organization_identifier_type_text",
    "organization_identifier_type_user_selected", "organization_identifier_period_start",
    "organization_identifier_period_end",
)

_OLD_ENUM_TYPES = (
    "practitioner_role_location_reference_type", "practitioner_role_healthcare_service_reference_type",
    "practitioner_role_endpoint_reference_type", "practitioner_role_day_of_week",
)


def _fk():
    return sa.Column("practitioner_role_pk", sa.BigInteger(), sa.ForeignKey("practitioner_role.id"), nullable=False)


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('practitioner_role', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are
    # rebuilt from it below.
    for table in _OLD_CHILD_TABLES:
        op.drop_table(table)
    for column in _OLD_MAIN_COLUMNS:
        op.drop_column('practitioner_role', column)
    op.create_index('ix_practitioner_role_period', 'practitioner_role', ['period_start', 'period_end'], unique=False)

    op.create_table(
        'practitioner_role_identifier',
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
    op.create_index(op.f('ix_practitioner_role_identifier_practitioner_role_pk'), 'practitioner_role_identifier', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_identifier_value'), 'practitioner_role_identifier', ['value'], unique=False)

    op.create_table(
        'practitioner_role_telecom',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('use', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practitioner_role_telecom_practitioner_role_pk'), 'practitioner_role_telecom', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_telecom_value'), 'practitioner_role_telecom', ['value'], unique=False)

    op.create_table(
        'practitioner_role_token',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('param', sa.String(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practitioner_role_token_practitioner_role_pk'), 'practitioner_role_token', ['practitioner_role_pk'], unique=False)
    op.create_index('ix_practitioner_role_token_param_code', 'practitioner_role_token', ['param', 'code'], unique=False)

    op.create_table(
        'practitioner_role_reference',
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
    op.create_index(op.f('ix_practitioner_role_reference_practitioner_role_pk'), 'practitioner_role_reference', ['practitioner_role_pk'], unique=False)
    op.create_index('ix_practitioner_role_reference_param_id', 'practitioner_role_reference', ['param', 'reference_id'], unique=False)

    _rebuild_index(bind)
    op.alter_column('practitioner_role', 'content', nullable=False)

    # These enum types belonged only to the dropped tables.
    for type_name in _OLD_ENUM_TYPES:
        op.execute(f"DROP TYPE IF EXISTS {type_name}")


def downgrade() -> None:
    raise NotImplementedError(
        "practitioner_role content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
