"""healthcare_service: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: c9f5b2d7e813
Revises: b8e4a1c6d902
Create Date: 2026-11-19 10:00:00.000000

Medplum-style storage for HealthcareService (see HealthcareServiceModel's
docstring), same as Organization (5b1969c2ec19), Location (8c41d2e7a9b3) and
Practitioner (a7d3f19c2b64). The whole FHIR resource moves into
`healthcare_service.content`; every column/table that survives is a search
index for one of the FHIR R4 HealthcareService search parameters (or
`_id`/`_lastUpdated`), derived from `content`:

  healthcare_service: active, name, provided_by_reference/_type/_id,
      provided_by_identifier_system/_value (kept; they feed `organization` and
      `organization:identifier`); new: content, name_norm
  healthcare_service_identifier: one row per identifier x type.coding
      (system, value, type_system, type_code, type_text_norm, type_display_norm)
  healthcare_service_token (new): one row per coding for `service-category`,
      `service-type`, `specialty`, `program`, `characteristic` (`param` says which)
  healthcare_service_reference (new): one row per Reference for `location`,
      `coverage-area`, `endpoint` (`param` says which)
  dropped: every other child table (category, type, specialty, location,
      telecom, coverage_area, service_provision_code, eligibility, program,
      characteristic, communication, referral_method, available_time,
      not_available, endpoint and every *_coding) and the main-table columns
      that have no search parameter (extension, comment, extra_details,
      photo_*, appointment_required, availability_exceptions, and the
      providedBy display / identifier detail columns), plus the now-unused
      Postgres enum types.

upgrade: (1) builds `content` for every existing row from the old columns and
tables — a frozen copy of the old to_fhir_healthcare_service() logic (but
keeping a reference's raw string, so an absolute URL is not lost), so this
migration never depends on application code that has since changed;
(2) drops the old child tables and creates the index tables; (3) rebuilds the
index from `content`.

downgrade: not supported. Everything the old schema held is preserved in
`content`, but rebuilding the sixteen old normalized tables from it is not
implemented — restore from a backup taken before upgrading.
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
revision: str = 'c9f5b2d7e813'
down_revision: Union[str, None] = 'b8e4a1c6d902'
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


def _concepts(bind, table, coding_table, fk, hs_pk):
    """A 0..* CodeableConcept list held as parent rows (text) + coding rows."""
    out = []
    for r in _rows(bind, f"SELECT * FROM {table} WHERE healthcare_service_pk = :pk ORDER BY id", pk=hs_pk):
        codings = _rows(bind, f"SELECT * FROM {coding_table} WHERE {fk} = :id ORDER BY id", id=r["id"])
        out.append({"coding": [_coding(c) for c in codings], "text": r["text"]})
    return out


def _identifier(bind, i):
    codings = _rows(bind, "SELECT * FROM healthcare_service_identifier_type_coding "
                          "WHERE healthcare_service_identifier_id = :id ORDER BY id", id=i["id"])
    return {
        "use": i["use"],
        "type": {"coding": [_coding(c) for c in codings], "text": i["type_text"]},
        "system": i["system"], "value": i["value"],
        "period": _period(i["period_start"], i["period_end"]),
        "assigner": _old_reference(i, "assigner"),
    }


def _build_content(bind, hs):
    pk = hs["id"]
    identifiers = [_identifier(bind, i) for i in _rows(
        bind, "SELECT * FROM healthcare_service_identifier WHERE healthcare_service_pk = :pk ORDER BY id", pk=pk)]
    telecoms = [{
        "system": t["system"], "value": t["value"], "use": t["use"], "rank": t["rank"],
        "period": _period(t["period_start"], t["period_end"]),
    } for t in _rows(bind, "SELECT * FROM healthcare_service_telecom WHERE healthcare_service_pk = :pk ORDER BY id", pk=pk)]
    locations = [_old_reference(r, "reference") for r in _rows(
        bind, "SELECT * FROM healthcare_service_location WHERE healthcare_service_pk = :pk ORDER BY id", pk=pk)]
    coverage = [_old_reference(r, "reference") for r in _rows(
        bind, "SELECT * FROM healthcare_service_coverage_area WHERE healthcare_service_pk = :pk ORDER BY id", pk=pk)]
    endpoints = [_old_reference(r, "reference") for r in _rows(
        bind, "SELECT * FROM healthcare_service_endpoint WHERE healthcare_service_pk = :pk ORDER BY id", pk=pk)]
    eligibility = []
    for e in _rows(bind, "SELECT * FROM healthcare_service_eligibility WHERE healthcare_service_pk = :pk ORDER BY id", pk=pk):
        codings = _rows(bind, "SELECT * FROM healthcare_service_eligibility_code_coding "
                              "WHERE healthcare_service_eligibility_id = :id ORDER BY id", id=e["id"])
        eligibility.append({"code": {"coding": [_coding(c) for c in codings], "text": e["code_text"]},
                            "comment": e["comment"]})
    available = [{
        "daysOfWeek": [str(d) for d in a["days_of_week"]] if a["days_of_week"] else None,
        "allDay": a["all_day"],
        "availableStartTime": _iso(a["available_start_time"]),
        "availableEndTime": _iso(a["available_end_time"]),
    } for a in _rows(bind, "SELECT * FROM healthcare_service_available_time WHERE healthcare_service_pk = :pk ORDER BY id", pk=pk)]
    not_available = [{
        "description": n["description"], "during": _period(n["during_start"], n["during_end"]),
    } for n in _rows(bind, "SELECT * FROM healthcare_service_not_available WHERE healthcare_service_pk = :pk ORDER BY id", pk=pk)]
    photo = {
        "contentType": hs["photo_content_type"], "language": hs["photo_language"], "data": hs["photo_data"],
        "url": hs["photo_url"], "size": hs["photo_size"], "hash": hs["photo_hash"], "title": hs["photo_title"],
        "creation": _iso(hs["photo_creation"]),
    }
    return _prune({
        "extension": _json(hs["extension"]),
        "identifier": identifiers,
        "active": hs["active"],
        "providedBy": _old_reference(hs, "provided_by"),
        "category": _concepts(bind, "healthcare_service_category", "healthcare_service_category_coding",
                              "healthcare_service_category_id", pk),
        "type": _concepts(bind, "healthcare_service_type", "healthcare_service_type_coding",
                          "healthcare_service_type_id", pk),
        "specialty": _concepts(bind, "healthcare_service_specialty", "healthcare_service_specialty_coding",
                               "healthcare_service_specialty_id", pk),
        "location": locations,
        "name": hs["name"],
        "comment": hs["comment"],
        "extraDetails": hs["extra_details"],
        "photo": photo,
        "telecom": telecoms,
        "coverageArea": coverage,
        "serviceProvisionCode": _concepts(
            bind, "healthcare_service_service_provision_code", "healthcare_service_service_provision_code_coding",
            "healthcare_service_service_provision_code_id", pk),
        "eligibility": eligibility,
        "program": _concepts(bind, "healthcare_service_program", "healthcare_service_program_coding",
                             "healthcare_service_program_id", pk),
        "characteristic": _concepts(bind, "healthcare_service_characteristic", "healthcare_service_characteristic_coding",
                                    "healthcare_service_characteristic_id", pk),
        "communication": _concepts(bind, "healthcare_service_communication", "healthcare_service_communication_coding",
                                   "healthcare_service_communication_id", pk),
        "referralMethod": _concepts(bind, "healthcare_service_referral_method", "healthcare_service_referral_method_coding",
                                    "healthcare_service_referral_method_id", pk),
        "appointmentRequired": hs["appointment_required"],
        "availableTime": available,
        "notAvailable": not_available,
        "availabilityExceptions": hs["availability_exceptions"],
        "endpoint": endpoints,
    })


def _backfill_content(bind):
    for hs in _rows(bind, "SELECT * FROM healthcare_service"):
        bind.execute(
            sa.text("UPDATE healthcare_service SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, hs)), "id": hs["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

TOKEN_PARAMS = {"service-category": "category", "service-type": "type", "specialty": "specialty",
                "program": "program", "characteristic": "characteristic"}
REFERENCE_PARAMS = {"location": ("location", "Location"), "coverage-area": ("coverageArea", "Location"),
                    "endpoint": ("endpoint", "Endpoint")}


def _relative(ref, resource_type):
    return ref if ref and ref.startswith(f"{resource_type}/") else None


def _rebuild_index(bind):
    for row in _rows(bind, "SELECT id, content FROM healthcare_service"):
        pk, doc = row["id"], _json(row["content"])
        provided = doc.get("providedBy") or {}
        local = _relative(provided.get("reference"), "Organization")
        pident = provided.get("identifier") or {}
        bind.execute(sa.text(
            "UPDATE healthcare_service SET name_norm = :nn, provided_by_reference = :pr, "
            "provided_by_type = CAST(:t AS organization_reference_type), provided_by_id = :i, "
            "provided_by_identifier_system = :pis, provided_by_identifier_value = :piv WHERE id = :pk"),
            {"nn": _norm(doc.get("name")), "pr": provided.get("reference"),
             "t": "Organization" if local else None,
             "i": int(local.split("/", 1)[1]) if local and local.split("/", 1)[1].isdigit() else None,
             "pis": pident.get("system"), "piv": pident.get("value"), "pk": pk})
        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO healthcare_service_identifier (healthcare_service_pk, system, value, type_system, "
                    "type_code, type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})
        for param, element in TOKEN_PARAMS.items():
            for cc in doc.get(element) or []:
                text = _norm(cc.get("text"))
                codings = [c for c in cc.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
                for c in codings or ([{}] if text else []):
                    bind.execute(sa.text(
                        "INSERT INTO healthcare_service_token (healthcare_service_pk, param, system, code, "
                        "display_norm, text_norm) VALUES (:pk, :p, :s, :c, :d, :t)"),
                        {"pk": pk, "p": param, "s": c.get("system"), "c": c.get("code"),
                         "d": _norm(c.get("display")), "t": text})
        for param, (element, rtype) in REFERENCE_PARAMS.items():
            for ref in doc.get(element) or []:
                reference = ref.get("reference")
                ident = ref.get("identifier") or {}
                if not (reference or ident.get("value")):
                    continue
                loc = _relative(reference, rtype)
                tail = loc.split("/", 1)[1] if loc else ""
                ref_id = int(tail) if tail.isdigit() else None
                bind.execute(sa.text(
                    "INSERT INTO healthcare_service_reference (healthcare_service_pk, param, reference_reference, "
                    "reference_type, reference_id, reference_identifier_system, reference_identifier_value) "
                    "VALUES (:pk, :p, :r, :t, :i, :is_, :iv)"),
                    {"pk": pk, "p": param, "r": reference, "t": rtype if ref_id is not None else None,
                     "i": ref_id, "is_": ident.get("system"), "iv": ident.get("value")})


# Children first.
_OLD_CHILD_TABLES = (
    "healthcare_service_identifier_type_coding", "healthcare_service_identifier",
    "healthcare_service_category_coding", "healthcare_service_category",
    "healthcare_service_type_coding", "healthcare_service_type",
    "healthcare_service_specialty_coding", "healthcare_service_specialty",
    "healthcare_service_service_provision_code_coding", "healthcare_service_service_provision_code",
    "healthcare_service_eligibility_code_coding", "healthcare_service_eligibility",
    "healthcare_service_program_coding", "healthcare_service_program",
    "healthcare_service_characteristic_coding", "healthcare_service_characteristic",
    "healthcare_service_communication_coding", "healthcare_service_communication",
    "healthcare_service_referral_method_coding", "healthcare_service_referral_method",
    "healthcare_service_available_time", "healthcare_service_not_available",
    "healthcare_service_location", "healthcare_service_coverage_area", "healthcare_service_endpoint",
    "healthcare_service_telecom",
)

_OLD_MAIN_COLUMNS = (
    "extension", "comment", "extra_details", "appointment_required", "availability_exceptions",
    "photo_content_type", "photo_language", "photo_data", "photo_url", "photo_size", "photo_hash",
    "photo_title", "photo_creation",
    "provided_by_display", "provided_by_identifier_use", "provided_by_identifier_type_system",
    "provided_by_identifier_type_version", "provided_by_identifier_type_code",
    "provided_by_identifier_type_display", "provided_by_identifier_type_text",
    "provided_by_identifier_type_user_selected", "provided_by_identifier_period_start",
    "provided_by_identifier_period_end",
)

_OLD_ENUM_TYPES = (
    "healthcare_service_location_reference_type", "healthcare_service_coverage_area_reference_type",
    "healthcare_service_endpoint_reference_type", "healthcare_service_day_of_week",
)


def _fk():
    return sa.Column("healthcare_service_pk", sa.BigInteger(), sa.ForeignKey("healthcare_service.id"), nullable=False)


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('healthcare_service', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are
    # rebuilt from it below.
    for table in _OLD_CHILD_TABLES:
        op.drop_table(table)
    op.execute("DROP INDEX IF EXISTS ix_healthcare_service_name")
    for column in _OLD_MAIN_COLUMNS:
        op.drop_column('healthcare_service', column)
    op.add_column('healthcare_service', sa.Column('name_norm', sa.String(), nullable=True))
    op.create_index('ix_healthcare_service_name_norm', 'healthcare_service', ['name_norm'], unique=False,
                    postgresql_ops={'name_norm': 'text_pattern_ops'})

    op.create_table(
        'healthcare_service_identifier',
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
    op.create_index(op.f('ix_healthcare_service_identifier_healthcare_service_pk'), 'healthcare_service_identifier', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_identifier_value'), 'healthcare_service_identifier', ['value'], unique=False)

    op.create_table(
        'healthcare_service_token',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('param', sa.String(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_token_healthcare_service_pk'), 'healthcare_service_token', ['healthcare_service_pk'], unique=False)
    op.create_index('ix_healthcare_service_token_param_code', 'healthcare_service_token', ['param', 'code'], unique=False)

    op.create_table(
        'healthcare_service_reference',
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
    op.create_index(op.f('ix_healthcare_service_reference_healthcare_service_pk'), 'healthcare_service_reference', ['healthcare_service_pk'], unique=False)
    op.create_index('ix_healthcare_service_reference_param_id', 'healthcare_service_reference', ['param', 'reference_id'], unique=False)

    _rebuild_index(bind)
    op.alter_column('healthcare_service', 'content', nullable=False)

    # The reference/day-of-week enum types belonged only to the dropped tables.
    for type_name in _OLD_ENUM_TYPES:
        op.execute(f"DROP TYPE IF EXISTS {type_name}")


def downgrade() -> None:
    raise NotImplementedError(
        "healthcare_service content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
