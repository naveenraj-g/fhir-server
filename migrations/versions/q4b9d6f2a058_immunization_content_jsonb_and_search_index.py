"""immunization: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: q4b9d6f2a058
Revises: p3a8c5e1f947
Create Date: 2026-12-03 10:00:00.000000

Medplum-style storage for Immunization (see ImmunizationModel's docstring), same as
the other resources already moved (Organization 5b1969c2ec19, Location 8c41d2e7a9b3,
Practitioner a7d3f19c2b64, HealthcareService c9f5b2d7e813, Endpoint d1a6c3e8f924,
PractitionerRole e2b7d4f9a035, Schedule f3c8e5a1b947, Slot g4d9f6b2c058, Patient
h5e0a7c3d169, Appointment i6f1b8d4e27a, AppointmentResponse j7a2c9e5f381, Encounter
k8b3d0f6a492, RelatedPerson l9c4e1a7b503, AllergyIntolerance m0d5f2b8c614, Condition
n1e6a3c9d725, Procedure o2f7b4d0e836, DiagnosticReport p3a8c5e1f947). The whole FHIR
resource moves into `immunization.content`; every column/table that survives is a
search index for one of the FHIR R4 Immunization search parameters (or `_id` /
`_lastUpdated`), derived from `content`:

  immunization: status (the Postgres enum already held the real FHIR codes, so it
      stays; only its NOT NULL goes), occurrence_date_start/_end (occurrenceDateTime,
      the range it covers), lot_number (kept) + lot_number_norm, and the patient_*,
      location_* and manufacturer_* reference columns (`*_type` becomes a plain
      string); the public id gets its sequence as a server default; new: content
  immunization_identifier: rebuilt as an index table
  immunization_token: new - reason-code, status-reason, target-disease, vaccine-code
  immunization_protocol: new - series
  immunization_reaction: new - reaction (detail) and reaction-date
  immunization_performer: rebuilt - one row per performer.actor
  immunization_reason_reference: rebuilt - one row per reasonReference
  dropped: every old child table (identifier type, status reason, vaccine, report
      origin, site, route, funding source codings, education, note, performer,
      program eligibility, protocol applied, reaction, reason code, reason
      reference and subpotent reason tables), every main-table column with no
      search parameter (encounter, recorded, primary source, expiration date,
      dose quantity, text of every concept, extension and the display /
      logical-identifier details of every reference) and the nine per-field
      `immunization_*_reference_type` enums.

upgrade: (1) builds `content` for every existing row from the old columns and
tables - a frozen copy of the old to_fhir_immunization() logic (but keeping a
reference's raw string, so an absolute URL is not lost), so this migration never
depends on application code that has since changed; (2) drops the old child
tables/columns and creates the index tables; (3) rebuilds the index from `content`.

downgrade: not supported. Everything the old schema held is preserved in
`content`, but rebuilding the old normalized tables from it is not implemented -
restore from a backup taken before upgrading.
"""
import json
import re
import unicodedata
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'q4b9d6f2a058'
down_revision: Union[str, None] = 'p3a8c5e1f947'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUS = ('completed', 'entered-in-error', 'not-done')


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


def _hyphenate(old):
    """The FHIR code for an old status label (a real code passes through)."""
    return old.replace("_", "-") if old else old


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


def _codings_of(bind, table, fk, value):
    return _rows_of(bind, table, fk, value)


def _concept_list(bind, table, coding_table, coding_fk, pk):
    return [
        _concept(_codings_of(bind, coding_table, coding_fk, c["id"]), c["text"])
        for c in _rows_of(bind, table, "immunization_pk", pk)
    ]


def _single_concept(bind, coding_table, pk, text):
    return _concept(_rows_of(bind, coding_table, "immunization_pk", pk), text)


def _build_content(bind, r):
    pk = r["id"]
    identifiers = []
    for i in _rows_of(bind, "immunization_identifier", "immunization_pk", pk):
        identifiers.append({
            "use": i["use"],
            "type": _concept(_rows_of(bind, "immunization_identifier_type_coding", "identifier_id", i["id"]),
                             i["type_text"]),
            "system": i["system"], "value": i["value"],
            "period": _period(i["period_start"], i["period_end"]),
            "assigner": _old_reference(i, "assigner"),
        })

    performers = []
    for p in _rows_of(bind, "immunization_performer", "immunization_pk", pk):
        performers.append({
            "function": _concept(_rows_of(bind, "immunization_performer_function_coding", "performer_id", p["id"]),
                                 p["function_text"]),
            "actor": _old_reference(p, "actor"),
        })

    notes = []
    for n in _rows_of(bind, "immunization_note", "immunization_pk", pk):
        note = {"text": n["text"], "time": _iso(n["time"])}
        if n["author_string"]:
            note["authorString"] = n["author_string"]
        else:
            note["authorReference"] = _old_reference(n, "author")
        notes.append(note)

    education = [
        {"documentType": e["document_type"], "reference": e["reference"],
         "publicationDate": _iso(e["publication_date"]), "presentationDate": _iso(e["presentation_date"])}
        for e in _rows_of(bind, "immunization_education", "immunization_pk", pk)
    ]

    reactions = [
        {"date": _iso(x["date"]), "detail": _old_reference(x, "detail"), "reported": x["reported"]}
        for x in _rows_of(bind, "immunization_reaction", "immunization_pk", pk)
    ]

    protocols = []
    for pa in _rows_of(bind, "immunization_protocol_applied", "immunization_pk", pk):
        entry = {
            "series": pa["series"],
            "authority": _old_reference(pa, "authority"),
            "targetDisease": [
                _concept(_rows_of(bind, "immunization_protocol_applied_target_disease_coding",
                                  "target_disease_id", td["id"]), td["text"])
                for td in _rows_of(bind, "immunization_protocol_applied_target_disease", "protocol_applied_id",
                                   pa["id"])
            ],
        }
        if pa["dose_number_positive_int"] is not None:
            entry["doseNumberPositiveInt"] = pa["dose_number_positive_int"]
        elif pa["dose_number_string"]:
            entry["doseNumberString"] = pa["dose_number_string"]
        if pa["series_doses_positive_int"] is not None:
            entry["seriesDosesPositiveInt"] = pa["series_doses_positive_int"]
        elif pa["series_doses_string"]:
            entry["seriesDosesString"] = pa["series_doses_string"]
        protocols.append(entry)

    dose = None
    if r["dose_quantity_value"] is not None:
        value = r["dose_quantity_value"]
        dose = {"value": float(value) if isinstance(value, Decimal) else value, "unit": r["dose_quantity_unit"],
                "system": r["dose_quantity_system"], "code": r["dose_quantity_code"]}

    occurrence = {}
    if r["occurrence_date_time"]:
        occurrence["occurrenceDateTime"] = _iso(r["occurrence_date_time"])
    elif r["occurrence_string"]:
        occurrence["occurrenceString"] = r["occurrence_string"]

    return _prune({
        "extension": list(_json(r["extension"]) or []),
        "identifier": identifiers,
        "status": _hyphenate(r["status_text"]),
        "statusReason": _single_concept(bind, "immunization_status_reason_coding", pk, r["status_reason_text"]),
        "vaccineCode": _single_concept(bind, "immunization_vaccine_coding", pk, r["vaccine_code_text"]),
        "patient": _old_reference(r, "patient"),
        "encounter": _old_reference(r, "encounter"),
        **occurrence,
        "recorded": _iso(r["recorded"]),
        "primarySource": r["primary_source"],
        "reportOrigin": _single_concept(bind, "immunization_report_origin_coding", pk, r["report_origin_text"]),
        "location": _old_reference(r, "location"),
        "manufacturer": _old_reference(r, "manufacturer"),
        "lotNumber": r["lot_number"],
        "expirationDate": _iso(r["expiration_date"]),
        "site": _single_concept(bind, "immunization_site_coding", pk, r["site_text"]),
        "route": _single_concept(bind, "immunization_route_coding", pk, r["route_text"]),
        "doseQuantity": dose,
        "performer": performers,
        "note": notes,
        "reasonCode": _concept_list(bind, "immunization_reason_code", "immunization_reason_code_coding",
                                    "reason_code_id", pk),
        "reasonReference": [_old_reference(x, "reference")
                            for x in _rows_of(bind, "immunization_reason_reference", "immunization_pk", pk)],
        "isSubpotent": r["is_subpotent"],
        "subpotentReason": _concept_list(bind, "immunization_subpotent_reason",
                                         "immunization_subpotent_reason_coding", "subpotent_reason_id", pk),
        "education": education,
        "programEligibility": _concept_list(bind, "immunization_program_eligibility",
                                            "immunization_program_eligibility_coding", "program_eligibility_id", pk),
        "fundingSource": _single_concept(bind, "immunization_funding_source_coding", pk, r["funding_source_text"]),
        "reaction": reactions,
        "protocolApplied": protocols,
    })


def _backfill_content(bind):
    # `status` is an enum: cast it to text so the driver returns the label.
    for r in _rows(bind, "SELECT *, status::text AS status_text FROM immunization"):
        bind.execute(
            sa.text("UPDATE immunization SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, r), default=str), "id": r["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_PERFORMER_TYPES = ("Practitioner", "PractitionerRole", "Organization")
_REASON_TYPES = ("Condition", "Observation", "DiagnosticReport")


def _typed(reference, allowed):
    match = _REF.match(reference or "")
    return (match["type"], int(match["id"])) if match and match["type"] in allowed else (None, None)


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
            "INSERT INTO immunization_token (immunization_pk, param, system, code, display_norm, text_norm) "
            "VALUES (:pk, :param, :s, :c, :d, :t)"),
            {"pk": pk, "param": param, "s": c.get("system"), "c": c.get("code"), "d": _norm(c.get("display")),
             "t": text})


def _insert_reference(bind, table, pk, ref, allowed):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return
    rtype, rid = _typed(reference, allowed)
    bind.execute(sa.text(
        f"INSERT INTO {table} (immunization_pk, reference_reference, reference_type, reference_id, "
        "reference_identifier_system, reference_identifier_value) VALUES (:pk, :r, :t, :i, :s, :v)"),
        {"pk": pk, "r": reference, "t": rtype, "i": rid, "s": identifier.get("system"),
         "v": identifier.get("value")})


def _rebuild_index(bind):
    for row in _rows(bind, "SELECT id, content FROM immunization"):
        pk, doc = row["id"], _json(row["content"])

        start, end = _bounds(doc.get("occurrenceDateTime"))
        lot = doc.get("lotNumber")
        status = doc.get("status")
        columns = {
            "occurrence_date_start": start, "occurrence_date_end": end,
            "lot_number_norm": _norm(lot) if lot else None,
            **_ref_params("patient", doc.get("patient"), ("Patient",)),
            **_ref_params("location", doc.get("location"), ("Location",)),
            **_ref_params("manufacturer", doc.get("manufacturer"), ("Organization",)),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(f"UPDATE immunization SET status = CAST(:status AS immunization_status), {sets} WHERE id = :pk"),
            {**columns, "status": status if status in _STATUS else None, "pk": pk})

        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO immunization_identifier (immunization_pk, system, value, type_system, "
                    "type_code, type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})

        for concept in doc.get("reasonCode") or []:
            _insert_token(bind, pk, "reason-code", concept)
        _insert_token(bind, pk, "status-reason", doc.get("statusReason"))
        for protocol in doc.get("protocolApplied") or []:
            for concept in (protocol or {}).get("targetDisease") or []:
                _insert_token(bind, pk, "target-disease", concept)
            if (protocol or {}).get("series"):
                bind.execute(sa.text(
                    "INSERT INTO immunization_protocol (immunization_pk, series, series_norm) VALUES (:pk, :s, :n)"),
                    {"pk": pk, "s": protocol["series"], "n": _norm(protocol["series"])})
        _insert_token(bind, pk, "vaccine-code", doc.get("vaccineCode"))

        for reaction in doc.get("reaction") or []:
            reaction = reaction or {}
            detail = reaction.get("detail") or {}
            reference = detail.get("reference")
            identifier = detail.get("identifier") or {}
            r_start, r_end = _bounds(reaction.get("date"))
            if not (reference or identifier.get("value") or r_start):
                continue
            rtype, rid = _typed(reference, ("Observation",))
            bind.execute(sa.text(
                "INSERT INTO immunization_reaction (immunization_pk, detail_reference, detail_type, detail_id, "
                "detail_identifier_system, detail_identifier_value, date_start, date_end) "
                "VALUES (:pk, :r, :t, :i, :s, :v, :ds, :de)"),
                {"pk": pk, "r": reference, "t": rtype, "i": rid, "s": identifier.get("system"),
                 "v": identifier.get("value"), "ds": r_start, "de": r_end})

        for performer in doc.get("performer") or []:
            _insert_reference(bind, "immunization_performer", pk, (performer or {}).get("actor"), _PERFORMER_TYPES)
        for ref in doc.get("reasonReference") or []:
            _insert_reference(bind, "immunization_reason_reference", pk, ref, _REASON_TYPES)


# Children first (grandchildren before their parents).
_OLD_CHILD_TABLES = (
    "immunization_identifier_type_coding", "immunization_identifier",
    "immunization_performer_function_coding", "immunization_performer",
    "immunization_program_eligibility_coding", "immunization_program_eligibility",
    "immunization_protocol_applied_target_disease_coding", "immunization_protocol_applied_target_disease",
    "immunization_protocol_applied",
    "immunization_reason_code_coding", "immunization_reason_code",
    "immunization_subpotent_reason_coding", "immunization_subpotent_reason",
    "immunization_education", "immunization_funding_source_coding", "immunization_note",
    "immunization_reaction", "immunization_reason_reference", "immunization_report_origin_coding",
    "immunization_route_coding", "immunization_site_coding", "immunization_status_reason_coding",
    "immunization_vaccine_coding",
)

# The per-field reference-type enums of the old schema (`immunization_status` stays).
_OLD_ENUMS = (
    "immunization_patient_reference_type", "immunization_encounter_reference_type",
    "immunization_location_reference_type", "immunization_manufacturer_reference_type",
    "immunization_performer_actor_reference_type", "immunization_note_author_reference_type",
    "immunization_reason_reference_type", "immunization_reaction_detail_reference_type",
    "immunization_protocol_applied_authority_reference_type",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns, `status`,
# `lot_number` and the index columns of the three kept references (the reference-type
# enums become plain strings).
_KEEP = {
    "id", "immunization_id", "tenant_id", "created_by", "updated_by", "created_at", "updated_at", "content",
    "status", "lot_number",
    *(f"{prefix}_{part}" for prefix in ("patient", "location", "manufacturer")
      for part in ("reference", "type", "id", "identifier_system", "identifier_value")),
}


def _fk():
    return sa.Column("immunization_pk", sa.BigInteger(), sa.ForeignKey("immunization.id"), nullable=False)


def _index(table, *columns):
    op.create_index(op.f("ix_" + table + "_" + columns[0]), table, list(columns))


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('immunization', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are
    # rebuilt from it below.
    for table in _OLD_CHILD_TABLES:
        op.drop_table(table)
    existing = [r[0] for r in bind.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'immunization' "
        "AND table_schema = current_schema()"))]
    for column in existing:
        if column not in _KEEP:
            op.drop_column('immunization', column)

    # The reference types were enums; they are plain strings now.
    for prefix in ('patient', 'location', 'manufacturer'):
        op.alter_column('immunization', f'{prefix}_type', type_=sa.String(), nullable=True,
                        postgresql_using=f'{prefix}_type::text')
    op.alter_column('immunization', 'patient_reference', nullable=True)
    op.alter_column('immunization', 'status', nullable=True)
    for name in _OLD_ENUMS:
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # The public id's sequence is now its server default.
    op.execute("ALTER TABLE immunization ALTER COLUMN immunization_id SET DEFAULT nextval('immunization_pub_seq')")

    op.add_column('immunization', sa.Column('occurrence_date_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('immunization', sa.Column('occurrence_date_end', sa.DateTime(timezone=True), nullable=True))
    op.add_column('immunization', sa.Column('lot_number_norm', sa.String(), nullable=True))
    op.create_index('ix_immunization_occurrence_date', 'immunization',
                    ['occurrence_date_start', 'occurrence_date_end'])
    op.create_index('ix_immunization_lot_number_norm', 'immunization', ['lot_number_norm'])

    op.create_table(
        'immunization_identifier',
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
    _index('immunization_identifier', 'immunization_pk')
    _index('immunization_identifier', 'value')

    op.create_table(
        'immunization_token',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('param', sa.String(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index('immunization_token', 'immunization_pk')
    op.create_index('ix_immunization_token_param_code', 'immunization_token', ['param', 'code'])

    op.create_table(
        'immunization_protocol',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('series', sa.String(), nullable=True),
        sa.Column('series_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index('immunization_protocol', 'immunization_pk')
    _index('immunization_protocol', 'series_norm')

    op.create_table(
        'immunization_reaction',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('detail_reference', sa.String(), nullable=True),
        sa.Column('detail_type', sa.String(), nullable=True),
        sa.Column('detail_id', sa.BigInteger(), nullable=True),
        sa.Column('detail_identifier_system', sa.String(), nullable=True),
        sa.Column('detail_identifier_value', sa.String(), nullable=True),
        sa.Column('date_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('date_end', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index('immunization_reaction', 'immunization_pk')
    op.create_index('ix_immunization_reaction_detail', 'immunization_reaction', ['detail_type', 'detail_id'])

    for table, index in (('immunization_performer', 'ix_immunization_performer_type_id'),
                         ('immunization_reason_reference', 'ix_immunization_reason_reference_type_id')):
        op.create_table(
            table,
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            _fk(),
            sa.Column('reference_reference', sa.String(), nullable=True),
            sa.Column('reference_type', sa.String(), nullable=True),
            sa.Column('reference_id', sa.BigInteger(), nullable=True),
            sa.Column('reference_identifier_system', sa.String(), nullable=True),
            sa.Column('reference_identifier_value', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        _index(table, 'immunization_pk')
        op.create_index(index, table, ['reference_type', 'reference_id'])

    _rebuild_index(bind)
    for column in ('patient_id', 'location_id', 'manufacturer_id'):
        op.create_index(f'ix_immunization_{column}', 'immunization', [column], if_not_exists=True)
    op.alter_column('immunization', 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "immunization content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
