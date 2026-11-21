"""immunization_recommendation: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: r5c0e7a3b169
Revises: q4b9d6f2a058
Create Date: 2026-12-04 10:00:00.000000

Medplum-style storage for ImmunizationRecommendation (see ImmunizationRecommendationModel's
docstring), same as the other resources already moved (Organization 5b1969c2ec19, Location
8c41d2e7a9b3, Practitioner a7d3f19c2b64, HealthcareService c9f5b2d7e813, Endpoint
d1a6c3e8f924, PractitionerRole e2b7d4f9a035, Schedule f3c8e5a1b947, Slot g4d9f6b2c058,
Patient h5e0a7c3d169, Appointment i6f1b8d4e27a, AppointmentResponse j7a2c9e5f381,
Encounter k8b3d0f6a492, RelatedPerson l9c4e1a7b503, AllergyIntolerance m0d5f2b8c614,
Condition n1e6a3c9d725, Procedure o2f7b4d0e836, DiagnosticReport p3a8c5e1f947,
Immunization q4b9d6f2a058). The whole FHIR resource moves into
`immunization_recommendation.content`; every column/table that survives is a search index
for one of the FHIR R4 ImmunizationRecommendation search parameters (or `_id` /
`_lastUpdated`), derived from `content`:

  immunization_recommendation: date_start/_end (the dateTime, the range it covers) and the
      patient_* reference columns (`patient_type` becomes a plain string, `patient_reference`
      becomes nullable); the public id gets its sequence as a server default; new: content
  immunization_recommendation_identifier: rebuilt as an index table
  immunization_recommendation_token: new - status, target-disease, vaccine-type
  immunization_recommendation_reference: new - support, information
  dropped: every old child table (identifier type, recommendation and its vaccine code,
      contraindicated code, forecast status / reason, target disease, date criterion and
      supporting immunization / patient information tables), every main-table column with no
      search parameter (date, authority, extension and the display / logical-identifier
      details of the patient reference) and the four per-field
      `immunization_recommendation_*_reference_type` enums.

upgrade: (1) builds `content` for every existing row from the old columns and tables - a
frozen copy of the old to_fhir_immunization_recommendation() logic (but keeping a reference's
raw string, so an absolute URL is not lost), so this migration never depends on application
code that has since changed; (2) drops the old child tables/columns and creates the index
tables; (3) rebuilds the index from `content`.

downgrade: not supported. Everything the old schema held is preserved in `content`, but
rebuilding the old normalized tables from it is not implemented - restore from a backup
taken before upgrading.
"""
import json
import re
import unicodedata
from datetime import UTC, date, datetime, timedelta, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'r5c0e7a3b169'
down_revision: Union[str, None] = 'q4b9d6f2a058'
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
    if isinstance(value, (datetime, date)):
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
    r"^(?P<y>\d{4})(?:-(?P<m>\d{2})(?:-(?P<d>\d{2})(?:T(?P<H>\d{2}):(?P<M>\d{2})"
    r"(?::(?P<S>\d{2})(?P<f>\.\d+)?)?(?P<tz>Z|[+-]\d{2}:\d{2})?)?)?)?$"
)


def _bounds(value):
    """(start, end) instants of a FHIR date/dateTime at its written
    precision — the half-open range it covers (frozen copy of
    app.fhir.search.values.parse_date / period_bounds). (None, None) if absent
    or unparseable."""
    if not value:
        return None, None
    g = _DATE_RE.match(str(value))
    if not g:
        return None, None
    g = g.groupdict()
    tz = UTC
    if g["tz"] and g["tz"] != "Z":
        sign = 1 if g["tz"][0] == "+" else -1
        tz = timezone(sign * timedelta(hours=int(g["tz"][1:3]), minutes=int(g["tz"][4:6])))
    try:
        low = datetime(int(g["y"]), int(g["m"] or 1), int(g["d"] or 1), int(g["H"] or 0), int(g["M"] or 0),
                       int(g["S"] or 0), int(((g["f"] or ".0")[1:] + "000000")[:6]), tzinfo=tz)
    except ValueError:
        return None, None
    if g["f"]:
        high = low + timedelta(microseconds=1)
    elif g["S"]:
        high = low + timedelta(seconds=1)
    elif g["M"]:
        high = low + timedelta(minutes=1)
    elif g["d"]:
        high = low + timedelta(days=1)
    elif g["m"]:
        high = low.replace(year=low.year + (low.month // 12), month=low.month % 12 + 1)
    else:
        high = low.replace(year=low.year + 1)
    return low.astimezone(UTC), high.astimezone(UTC)


# ── upgrade: old columns/tables -> content (frozen copy of the old mapper) ───

def _coding(c):
    return {"system": c["system"], "version": c["version"], "code": c["code"],
            "display": c["display"], "userSelected": c["user_selected"]}


def _concept(codings, text):
    return {"coding": [_coding(c) for c in codings], "text": text}


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
    raw = row[f"{prefix}_reference"]
    if not raw and row[f"{prefix}_type"] and row[f"{prefix}_id"]:
        raw = f"{row[prefix + '_type']}/{row[prefix + '_id']}"
    return {
        "reference": raw,
        "display": row[f"{prefix}_display"],
        "identifier": _fallback_identifier(row, prefix),
    }


def _rows_of(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


def _concept_list(bind, table, coding_table, coding_fk, rec_id):
    return [
        _concept(_rows_of(bind, coding_table, coding_fk, c["id"]), c["text"])
        for c in _rows_of(bind, table, "recommendation_id", rec_id)
    ]


def _build_recommendation(bind, r):
    rid = r["id"]
    p = "immunization_recommendation"
    entry = {
        "vaccineCode": _concept_list(bind, f"{p}_vaccine_code", f"{p}_vaccine_code_coding", "vaccine_code_id", rid),
        "targetDisease": _concept(_rows_of(bind, f"{p}_target_disease_coding", "recommendation_id", rid),
                                  r["target_disease_text"]),
        "contraindicatedVaccineCode": _concept_list(
            bind, f"{p}_contraindicated_code", f"{p}_contraindicated_coding", "contraindicated_code_id", rid),
        "forecastStatus": _concept(_rows_of(bind, f"{p}_forecast_status_coding", "recommendation_id", rid),
                                   r["forecast_status_text"]),
        "forecastReason": _concept_list(
            bind, f"{p}_forecast_reason", f"{p}_forecast_reason_coding", "forecast_reason_id", rid),
        "dateCriterion": [
            {"code": _concept(_rows_of(bind, f"{p}_date_criterion_coding", "date_criterion_id", dc["id"]),
                              dc["code_text"]),
             "value": _iso(dc["value"])}
            for dc in _rows_of(bind, f"{p}_date_criterion", "recommendation_id", rid)
        ],
        "description": r["description"],
        "series": r["series"],
        "supportingImmunization": [_old_reference(x, "reference")
                                   for x in _rows_of(bind, f"{p}_supporting_immunization", "recommendation_id", rid)],
        "supportingPatientInformation": [
            _old_reference(x, "reference")
            for x in _rows_of(bind, f"{p}_supporting_patient_info", "recommendation_id", rid)],
    }
    if r["dose_number_positive_int"] is not None:
        entry["doseNumberPositiveInt"] = r["dose_number_positive_int"]
    elif r["dose_number_string"]:
        entry["doseNumberString"] = r["dose_number_string"]
    if r["series_doses_positive_int"] is not None:
        entry["seriesDosesPositiveInt"] = r["series_doses_positive_int"]
    elif r["series_doses_string"]:
        entry["seriesDosesString"] = r["series_doses_string"]
    return entry


def _build_content(bind, r):
    pk = r["id"]
    identifiers = []
    for i in _rows_of(bind, "immunization_recommendation_identifier", "immunization_recommendation_pk", pk):
        identifiers.append({
            "use": i["use"],
            "type": _concept(
                _rows_of(bind, "immunization_recommendation_identifier_type_coding", "identifier_id", i["id"]),
                i["type_text"]),
            "system": i["system"], "value": i["value"],
            "period": _period(i["period_start"], i["period_end"]),
            "assigner": _old_reference(i, "assigner"),
        })
    authority = _old_reference(r, "authority") if (r["authority_reference"] or r["authority_id"]) else None
    return _prune({
        "extension": list(_json(r["extension"]) or []),
        "identifier": identifiers,
        "patient": _old_reference(r, "patient"),
        "date": _iso(r["date"]),
        "authority": authority,
        "recommendation": [
            _build_recommendation(bind, x)
            for x in _rows_of(bind, "immunization_recommendation_recommendation", "immunization_recommendation_pk", pk)
        ],
    })


def _backfill_content(bind):
    for r in _rows(bind, "SELECT * FROM immunization_recommendation"):
        bind.execute(
            sa.text("UPDATE immunization_recommendation SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, r), default=str), "id": r["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_SUPPORT_TYPES = ("Immunization", "ImmunizationEvaluation")


def _typed(reference, allowed):
    match = _REF.match(reference or "")
    return (match["type"], int(match["id"])) if match and match["type"] in allowed else (None, None)


def _any_typed(reference):
    match = _REF.match(reference or "")
    return (match["type"], int(match["id"])) if match else (None, None)


def _ref_params(prefix, ref, allowed):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    rtype, rid = _typed(reference, allowed)
    return {f"{prefix}_reference": reference, f"{prefix}_type": rtype, f"{prefix}_id": rid,
            f"{prefix}_identifier_system": identifier.get("system"),
            f"{prefix}_identifier_value": identifier.get("value")}


def _insert_token(bind, pk, param, concept):
    if not concept:
        return
    text = _norm(concept.get("text"))
    codings = [c for c in concept.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
    for c in codings or ([{}] if text else []):
        bind.execute(sa.text(
            "INSERT INTO immunization_recommendation_token (immunization_recommendation_pk, param, system, code, "
            "display_norm, text_norm) VALUES (:pk, :param, :s, :c, :d, :t)"),
            {"pk": pk, "param": param, "s": c.get("system"), "c": c.get("code"), "d": _norm(c.get("display")),
             "t": text})


def _insert_reference(bind, pk, param, ref):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return
    rtype, rid = _any_typed(reference) if param == "information" else _typed(reference, _SUPPORT_TYPES)
    bind.execute(sa.text(
        "INSERT INTO immunization_recommendation_reference (immunization_recommendation_pk, param, "
        "reference_reference, reference_type, reference_id, reference_identifier_system, "
        "reference_identifier_value) VALUES (:pk, :p, :r, :t, :i, :s, :v)"),
        {"pk": pk, "p": param, "r": reference, "t": rtype, "i": rid, "s": identifier.get("system"),
         "v": identifier.get("value")})


def _rebuild_index(bind):
    for row in _rows(bind, "SELECT id, content FROM immunization_recommendation"):
        pk, doc = row["id"], _json(row["content"])

        start, end = _bounds(doc.get("date"))
        columns = {"date_start": start, "date_end": end, **_ref_params("patient", doc.get("patient"), ("Patient",))}
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(sa.text(f"UPDATE immunization_recommendation SET {sets} WHERE id = :pk"), {**columns, "pk": pk})

        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO immunization_recommendation_identifier (immunization_recommendation_pk, system, "
                    "value, type_system, type_code, type_text_norm, type_display_norm) "
                    "VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})

        for rec in doc.get("recommendation") or []:
            rec = rec or {}
            _insert_token(bind, pk, "status", rec.get("forecastStatus"))
            _insert_token(bind, pk, "target-disease", rec.get("targetDisease"))
            for concept in rec.get("vaccineCode") or []:
                _insert_token(bind, pk, "vaccine-type", concept)
            for ref in rec.get("supportingImmunization") or []:
                _insert_reference(bind, pk, "support", ref)
            for ref in rec.get("supportingPatientInformation") or []:
                _insert_reference(bind, pk, "information", ref)


P = "immunization_recommendation"
# Children first (grandchildren before their parents).
_OLD_CHILD_TABLES = (
    f"{P}_identifier_type_coding", f"{P}_identifier",
    f"{P}_vaccine_code_coding", f"{P}_vaccine_code",
    f"{P}_contraindicated_coding", f"{P}_contraindicated_code",
    f"{P}_forecast_reason_coding", f"{P}_forecast_reason",
    f"{P}_date_criterion_coding", f"{P}_date_criterion",
    f"{P}_forecast_status_coding", f"{P}_target_disease_coding",
    f"{P}_supporting_immunization", f"{P}_supporting_patient_info",
    f"{P}_recommendation",
)

# The per-field reference-type enums of the old schema (the last two names are as Postgres
# truncated them to 63 characters).
_OLD_ENUMS = (
    f"{P}_patient_reference_type", f"{P}_authority_reference_type",
    f"{P}_supporting_immunization_reference_t", f"{P}_supporting_patient_info_reference_t",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns and the index
# columns of `patient` (its reference-type enum becomes a plain string).
_KEEP = {
    "id", "immunization_recommendation_id", "tenant_id", "created_by", "updated_by", "created_at", "updated_at",
    "content",
    *(f"patient_{part}" for part in ("reference", "type", "id", "identifier_system", "identifier_value")),
}


def _fk():
    return sa.Column("immunization_recommendation_pk", sa.BigInteger(),
                     sa.ForeignKey("immunization_recommendation.id"), nullable=False)


def _index(table, *columns):
    op.create_index(op.f("ix_" + table + "_" + columns[0]), table, list(columns))


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(P, sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are
    # rebuilt from it below.
    for table in _OLD_CHILD_TABLES:
        op.drop_table(table)
    existing = [r[0] for r in bind.execute(sa.text(
        f"SELECT column_name FROM information_schema.columns WHERE table_name = '{P}' "
        "AND table_schema = current_schema()"))]
    for column in existing:
        if column not in _KEEP:
            op.drop_column(P, column)

    # The patient reference type was an enum; it is a plain string now.
    op.alter_column(P, 'patient_type', type_=sa.String(), nullable=True, postgresql_using='patient_type::text')
    op.alter_column(P, 'patient_reference', nullable=True)
    for name in _OLD_ENUMS:
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # The public id's sequence is now its server default.
    op.execute(f"ALTER TABLE {P} ALTER COLUMN immunization_recommendation_id "
               "SET DEFAULT nextval('immunization_recommendation_pub_seq')")

    op.add_column(P, sa.Column('date_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column(P, sa.Column('date_end', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_immunization_recommendation_date', P, ['date_start', 'date_end'])

    op.create_table(
        f'{P}_identifier',
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
    _index(f'{P}_identifier', 'immunization_recommendation_pk')
    _index(f'{P}_identifier', 'value')

    op.create_table(
        f'{P}_token',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('param', sa.String(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index(f'{P}_token', 'immunization_recommendation_pk')
    op.create_index('ix_immunization_recommendation_token_param_code', f'{P}_token', ['param', 'code'])

    op.create_table(
        f'{P}_reference',
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
    _index(f'{P}_reference', 'immunization_recommendation_pk')
    op.create_index('ix_immunization_recommendation_reference_param_type_id', f'{P}_reference',
                    ['param', 'reference_type', 'reference_id'])

    _rebuild_index(bind)
    op.create_index(f'ix_{P}_patient_id', P, ['patient_id'], if_not_exists=True)
    op.alter_column(P, 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "immunization_recommendation content/index migration is one-way: its old normalized tables are "
        "not rebuilt from `content`. Restore from a backup taken before upgrading."
    )
