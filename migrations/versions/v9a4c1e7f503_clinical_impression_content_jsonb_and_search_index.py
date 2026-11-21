"""clinical_impression: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: v9a4c1e7f503
Revises: u8f3b0d6e492
Create Date: 2026-12-08 10:00:00.000000

Medplum-style storage for ClinicalImpression (see ClinicalImpressionModel's docstring), same as
the other resources already moved (Organization 5b1969c2ec19, Location 8c41d2e7a9b3,
Practitioner a7d3f19c2b64, HealthcareService c9f5b2d7e813, Endpoint d1a6c3e8f924,
PractitionerRole e2b7d4f9a035, Schedule f3c8e5a1b947, Slot g4d9f6b2c058, Patient h5e0a7c3d169,
Appointment i6f1b8d4e27a, AppointmentResponse j7a2c9e5f381, Encounter k8b3d0f6a492,
RelatedPerson l9c4e1a7b503, AllergyIntolerance m0d5f2b8c614, Condition n1e6a3c9d725, Procedure
o2f7b4d0e836, DiagnosticReport p3a8c5e1f947, Immunization q4b9d6f2a058,
ImmunizationRecommendation r5c0e7a3b169, ImmunizationEvaluation s6d1f8b4c270,
FamilyMemberHistory t7e2a9c5d381, RiskAssessment u8f3b0d6e492). The whole FHIR resource moves
into `clinical_impression.content`; every column/table that survives is a search index for one
of the FHIR R4 ClinicalImpression search parameters (or `_id` / `_lastUpdated`), derived from
`content`:

  clinical_impression: status (the Postgres enum already held the real FHIR codes, so it stays;
      now nullable), date_start/_end (`date`, the range it covers) and the subject_*,
      encounter_*, assessor_* and previous_* reference columns (`*_type` becomes a plain
      string); the public id gets its sequence as a server default; new: content.
  clinical_impression_identifier: rebuilt as an index table
  clinical_impression_token: new - finding-code (finding.itemCodeableConcept of every finding)
  clinical_impression_reference: new - problem, investigation (investigation.item), finding-ref
      (finding.itemReference) and supporting-info (supportingInfo)
  dropped: every old child table (identifier coding, status reason / code codings, problem,
      investigation + its code codings and items, protocol, finding + item codings, prognosis
      concepts + codings and references, supporting info, note), every main-table column with no
      search parameter (concept texts, description, effective[x], summary, extension and the
      display / logical-identifier details of every reference) and the six per-field
      `clinical_impression_*_reference_type` enums (the shared `subject_reference_type` /
      `encounter_reference_type` stay).

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_clinical_impression() logic (but keeping a reference's raw string, so an
absolute URL is not lost), so this migration never depends on application code that has since
changed; (2) drops the old child tables/columns and creates the index tables; (3) rebuilds the
index from `content`.

downgrade: not supported. Everything the old schema held is preserved in `content`, but rebuilding
the old normalized tables from it is not implemented - restore from a backup taken before
upgrading.
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
revision: str = 'v9a4c1e7f503'
down_revision: Union[str, None] = 'u8f3b0d6e492'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "clinical_impression"


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

# The shared / per-field reference-type enums hold FHIR type names or their member names; map
# either to the FHIR type name when building a reference from a resolved type + id.
_TYPE_NAMES = {t.upper(): t for t in (
    "Patient", "Group", "Encounter", "Condition", "AllergyIntolerance", "Practitioner", "PractitionerRole",
    "RelatedPerson", "Organization", "ClinicalImpression", "RiskAssessment", "FamilyMemberHistory",
    "DiagnosticReport", "Observation", "QuestionnaireResponse", "ImagingStudy", "Media")}


def _coding(c):
    return {"system": c["system"], "version": c["version"], "code": c["code"],
            "display": c["display"], "userSelected": c["user_selected"]}


def _concept(codings, text):
    return {"coding": [_coding(c) for c in codings], "text": text}


def _fallback_identifier(row, prefix):
    p = f"{prefix}_use"
    return {
        "use": row[p],
        "type": {
            "coding": [{
                "system": row[f"{prefix}_type_system"], "version": row[f"{prefix}_type_version"],
                "code": row[f"{prefix}_type_code"], "display": row[f"{prefix}_type_display"],
                "userSelected": row[f"{prefix}_type_user_selected"],
            }],
            "text": row[f"{prefix}_type_text"],
        },
        "system": row[f"{prefix}_system"],
        "value": row[f"{prefix}_value"],
        "period": _period(row[f"{prefix}_period_start"], row[f"{prefix}_period_end"]),
    }


def _old_ref(row, ref, typ, id_, display, ident):
    """A Reference from the old columns: `ref`/`typ`/`id_`/`display` are the four column names and
    `ident` the prefix of the eleven logical-identifier columns."""
    raw = row[ref]
    if not raw and row[typ] and row[id_]:
        ref_type = str(row[typ])
        raw = f"{_TYPE_NAMES.get(ref_type.upper(), ref_type)}/{row[id_]}"
    return {"reference": raw, "display": row[display], "identifier": _fallback_identifier(row, ident)}


def _main_ref(row, prefix):
    return _old_ref(row, f"{prefix}_reference", f"{prefix}_type", f"{prefix}_id", f"{prefix}_display",
                    f"{prefix}_identifier")


def _plain_ref(row):
    """The bare `reference` / `reference_type` / `reference_id` / `display` / `identifier_*` shape of
    prognosis_reference and supporting_info."""
    return _old_ref(row, "reference", "reference_type", "reference_id", "display", "identifier")


def _rows_of(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


def _note(n):
    note = {"time": _iso(n["time"]), "text": n["text"]}
    author = _prune(_main_ref(n, "author"))
    if author:
        note["authorReference"] = author
    elif n["author_string"]:
        note["authorString"] = n["author_string"]
    return note


def _investigation(bind, i):
    return {
        "code": _concept(_rows_of(bind, f"{P}_investigation_code_coding", f"{P}_investigation_id", i["id"]),
                         i["code_text"]),
        "item": [_main_ref(x, "item")
                 for x in _rows_of(bind, f"{P}_investigation_item", f"{P}_investigation_id", i["id"])],
    }


def _finding(bind, f):
    return {
        "itemCodeableConcept": _concept(
            _rows_of(bind, f"{P}_finding_item_coding", f"{P}_finding_id", f["id"]), f["item_codeable_concept_text"]),
        "itemReference": _old_ref(f, "item_reference", "item_reference_type", "item_reference_id",
                                  "item_reference_display", "item_reference_identifier"),
        "basis": f["basis"],
    }


def _build_content(bind, r):
    pk = r["id"]
    identifiers = []
    for i in _rows_of(bind, f"{P}_identifier", f"{P}_pk", pk):
        identifiers.append({
            "use": i["use"],
            "type": _concept(_rows_of(bind, f"{P}_identifier_coding", f"{P}_identifier_id", i["id"]), i["type_text"]),
            "system": i["system"], "value": i["value"],
            "period": _period(i["period_start"], i["period_end"]),
            "assigner": _main_ref(i, "assigner"),
        })
    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": identifiers,
        "status": r["status_text"],
        "statusReason": _concept(_rows_of(bind, f"{P}_status_reason_coding", f"{P}_pk", pk), r["status_reason_text"]),
        "code": _concept(_rows_of(bind, f"{P}_code_coding", f"{P}_pk", pk), r["code_text"]),
        "description": r["description"],
        "subject": _main_ref(r, "subject"),
        "encounter": _main_ref(r, "encounter"),
        "date": _iso(r["date"]),
        "assessor": _main_ref(r, "assessor"),
        "previous": _main_ref(r, "previous"),
        "problem": [_main_ref(x, "problem") for x in _rows_of(bind, f"{P}_problem", f"{P}_pk", pk)],
        "investigation": [_investigation(bind, i) for i in _rows_of(bind, f"{P}_investigation", f"{P}_pk", pk)],
        "protocol": [x["uri"] for x in _rows_of(bind, f"{P}_protocol", f"{P}_pk", pk)],
        "summary": r["summary"],
        "finding": [_finding(bind, f) for f in _rows_of(bind, f"{P}_finding", f"{P}_pk", pk)],
        "prognosisCodeableConcept": [
            _concept(_rows_of(bind, f"{P}_prognosis_coding", f"{P}_prognosis_id", x["id"]), x["text"])
            for x in _rows_of(bind, f"{P}_prognosis_codeable_concept", f"{P}_pk", pk)
        ],
        "prognosisReference": [_plain_ref(x) for x in _rows_of(bind, f"{P}_prognosis_reference", f"{P}_pk", pk)],
        "supportingInfo": [_plain_ref(x) for x in _rows_of(bind, f"{P}_supporting_info", f"{P}_pk", pk)],
        "note": [_note(n) for n in _rows_of(bind, f"{P}_note", f"{P}_pk", pk)],
    }
    if r["effective_date_time"]:
        content["effectiveDateTime"] = _iso(r["effective_date_time"])
    elif r["effective_period_start"] or r["effective_period_end"]:
        content["effectivePeriod"] = _period(r["effective_period_start"], r["effective_period_end"])
    return _prune(content)


def _backfill_content(bind):
    # `status` is an enum: cast it to text so the driver returns the label.
    for r in _rows(bind, f"SELECT *, status::text AS status_text FROM {P}"):
        bind.execute(
            sa.text(f"UPDATE {P} SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, dict(r)), default=str), "id": r["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_STATUSES = ("in-progress", "completed", "entered-in-error")
_SUBJECT_TYPES = ("Patient", "Group")
_ASSESSOR_TYPES = ("Practitioner", "PractitionerRole")
_PROBLEM_TYPES = ("Condition", "AllergyIntolerance")
_INVESTIGATION_TYPES = ("RiskAssessment", "FamilyMemberHistory", "Observation", "Media", "DiagnosticReport",
                        "ImagingStudy", "QuestionnaireResponse")
_FINDING_TYPES = ("Condition", "Observation", "Media")


def _typed(reference, allowed):
    match = _REF.match(reference or "")
    return (match["type"], int(match["id"])) if match and (allowed is None or match["type"] in allowed) else (None, None)


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
            f"INSERT INTO {P}_token ({P}_pk, param, system, code, display_norm, text_norm) "
            "VALUES (:pk, :param, :s, :c, :d, :t)"),
            {"pk": pk, "param": param, "s": c.get("system"), "c": c.get("code"), "d": _norm(c.get("display")),
             "t": text})


def _insert_reference(bind, pk, param, ref, allowed):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return
    rtype, rid = _typed(reference, allowed)
    bind.execute(sa.text(
        f"INSERT INTO {P}_reference ({P}_pk, param, reference_reference, reference_type, reference_id, "
        "reference_identifier_system, reference_identifier_value) VALUES (:pk, :param, :r, :t, :i, :s, :v)"),
        {"pk": pk, "param": param, "r": reference, "t": rtype, "i": rid, "s": identifier.get("system"),
         "v": identifier.get("value")})


def _rebuild_index(bind):
    for row in _rows(bind, f"SELECT id, content FROM {P}"):
        pk, doc = row["id"], _json(row["content"])

        start, end = _bounds(doc.get("date"))
        status = doc.get("status")
        columns = {
            "date_start": start, "date_end": end,
            **_ref_params("subject", doc.get("subject"), _SUBJECT_TYPES),
            **_ref_params("encounter", doc.get("encounter"), ("Encounter",)),
            **_ref_params("assessor", doc.get("assessor"), _ASSESSOR_TYPES),
            **_ref_params("previous", doc.get("previous"), ("ClinicalImpression",)),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(sa.text(f"UPDATE {P} SET status = CAST(:status AS clinical_impression_status), {sets} "
                             "WHERE id = :pk"),
                     {**columns, "status": status if status in _STATUSES else None, "pk": pk})

        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    f"INSERT INTO {P}_identifier ({P}_pk, system, value, type_system, type_code, type_text_norm, "
                    "type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})

        for finding in doc.get("finding") or []:
            finding = finding or {}
            _insert_token(bind, pk, "finding-code", finding.get("itemCodeableConcept"))
            _insert_reference(bind, pk, "finding-ref", finding.get("itemReference"), _FINDING_TYPES)
        for ref in doc.get("problem") or []:
            _insert_reference(bind, pk, "problem", ref, _PROBLEM_TYPES)
        for investigation in doc.get("investigation") or []:
            for ref in (investigation or {}).get("item") or []:
                _insert_reference(bind, pk, "investigation", ref, _INVESTIGATION_TYPES)
        for ref in doc.get("supportingInfo") or []:
            _insert_reference(bind, pk, "supporting-info", ref, None)


# The per-field enums of the old schema (the shared `subject_reference_type` /
# `encounter_reference_type` stay: other tables use them, and `clinical_impression_status` stays).
_OLD_ENUMS = (
    f"{P}_assessor_reference_type", f"{P}_previous_reference_type", f"{P}_problem_reference_type",
    f"{P}_finding_reference_type", f"{P}_prognosis_reference_type", f"{P}_note_author_reference_type",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns, `status` and the
# index columns of the four kept references (their reference-type enums become plain strings).
_KEEP = {
    "id", "clinical_impression_id", "tenant_id", "created_by", "updated_by", "created_at", "updated_at",
    "content", "status",
    *(f"{prefix}_{part}" for prefix in ("subject", "encounter", "assessor", "previous")
      for part in ("reference", "type", "id", "identifier_system", "identifier_value")),
}


def _fk():
    return sa.Column(f"{P}_pk", sa.BigInteger(), sa.ForeignKey(f"{P}.id"), nullable=False)


def _index(table, *columns):
    op.create_index(op.f("ix_" + table + "_" + columns[0]), table, list(columns))


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(P, sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are rebuilt from it
    # below. The new index tables do not exist yet, so every `clinical_impression_*` table is old.
    old_tables = [r[0] for r in bind.execute(sa.text(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema() "
        "AND table_name LIKE 'clinical\\_impression\\_%'"))]
    for table in old_tables:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
    existing = [r[0] for r in bind.execute(sa.text(
        f"SELECT column_name FROM information_schema.columns WHERE table_name = '{P}' "
        "AND table_schema = current_schema()"))]
    for column in existing:
        if column not in _KEEP:
            op.drop_column(P, column)

    # The reference types were enums; they are plain strings now, and the references are optional.
    for prefix in ('subject', 'encounter', 'assessor', 'previous'):
        op.alter_column(P, f'{prefix}_type', type_=sa.String(), nullable=True, postgresql_using=f'{prefix}_type::text')
    op.alter_column(P, 'subject_reference', nullable=True)
    op.alter_column(P, 'subject_id', nullable=True)
    op.alter_column(P, 'status', nullable=True)
    for name in _OLD_ENUMS:
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # The public id's sequence is now its server default.
    op.execute(f"ALTER TABLE {P} ALTER COLUMN clinical_impression_id SET DEFAULT nextval('clinical_impression_pub_seq')")

    op.add_column(P, sa.Column('date_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column(P, sa.Column('date_end', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_clinical_impression_date', P, ['date_start', 'date_end'])

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
    _index(f'{P}_identifier', f'{P}_pk')
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
    _index(f'{P}_token', f'{P}_pk')
    op.create_index('ix_clinical_impression_token_param_code', f'{P}_token', ['param', 'code'])

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
    _index(f'{P}_reference', f'{P}_pk')
    op.create_index('ix_clinical_impression_reference_param_type_id', f'{P}_reference',
                    ['param', 'reference_type', 'reference_id'])

    _rebuild_index(bind)
    for column in ('id', 'subject_id', 'encounter_id', 'assessor_id', 'previous_id', 'status'):
        op.create_index(f'ix_{P}_{column}', P, [column], if_not_exists=True)
    op.alter_column(P, 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "clinical_impression content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
