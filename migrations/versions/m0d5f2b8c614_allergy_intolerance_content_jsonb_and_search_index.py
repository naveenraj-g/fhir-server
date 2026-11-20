"""allergy_intolerance: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: m0d5f2b8c614
Revises: l9c4e1a7b503
Create Date: 2026-11-29 10:00:00.000000

Medplum-style storage for AllergyIntolerance (see AllergyIntoleranceModel's
docstring), same as the other resources already moved (Organization
5b1969c2ec19, Location 8c41d2e7a9b3, Practitioner a7d3f19c2b64,
HealthcareService c9f5b2d7e813, Endpoint d1a6c3e8f924, PractitionerRole
e2b7d4f9a035, Schedule f3c8e5a1b947, Slot g4d9f6b2c058, Patient h5e0a7c3d169,
Appointment i6f1b8d4e27a, AppointmentResponse j7a2c9e5f381, Encounter
k8b3d0f6a492, RelatedPerson l9c4e1a7b503). The whole FHIR resource moves into
`allergy_intolerance.content`; every column/table that survives is a search index
for one of the FHIR R4 AllergyIntolerance search parameters (or `_id` /
`_lastUpdated`), derived from `content`:

  allergy_intolerance: type, criticality (kept as the existing enum columns),
      recorded_date_start/_end and last_occurrence_start/_end (the dateTimes as
      the range they cover, replacing the old `recorded_date` / `last_occurrence`
      timestamps), patient_*, recorder_*, asserter_* reference columns
      (`*_type` becomes a plain string); the public id gets its sequence as a
      server default; new: content
  allergy_intolerance_identifier: rebuilt as an index table
  allergy_intolerance_token: new - clinical-status, verification-status, code
      (code + reaction.substance), category, manifestation, route, severity
  allergy_intolerance_reaction: rebuilt - one row per reaction.onset
  dropped: every old child table (clinical status / verification status / code
      codings, notes, reactions and their codings/notes, identifier type codings),
      every main-table column with no search parameter (clinical/verification
      status text, code text, category, encounter, onset[x], extension, and the
      display / logical-identifier details of every reference) and the per-field
      reference-type enums plus allergy_intolerance_category / _severity.

upgrade: (1) builds `content` for every existing row from the old columns and
tables - a frozen copy of the old to_fhir_allergy_intolerance() logic (but
keeping a reference's raw string, so an absolute URL is not lost), so this
migration never depends on application code that has since changed; (2) drops
the old child tables/columns and creates the index tables; (3) rebuilds the
index from `content`.

downgrade: not supported. Everything the old schema held is preserved in
`content`, but rebuilding the old normalized tables from it is not implemented -
restore from a backup taken before upgrading.
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
revision: str = 'm0d5f2b8c614'
down_revision: Union[str, None] = 'l9c4e1a7b503'
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


def _old_reference(row, prefix, raw_column=None):
    """`raw_column` names the column holding the raw reference string when it is not
    `{prefix}_reference` (an annotation's author keeps it in `author_reference`)."""
    raw = row[raw_column or f"{prefix}_reference"]
    if not raw and row[f"{prefix}_type"] and row[f"{prefix}_id"]:
        raw = f"{row[prefix + '_type']}/{row[prefix + '_id']}"
    return {
        "reference": raw,
        "display": row[f"{prefix}_display"],
        "identifier": _fallback_identifier(row, prefix),
    }


def _annotation(n):
    ref = _old_reference(n, "author_reference", raw_column="author_reference")
    has_ref = bool(ref["reference"] or ref["identifier"]["value"] or ref["identifier"]["system"])
    return {
        "authorReference": ref if has_ref else None,
        "authorString": None if has_ref else n["author_string"],
        "time": _iso(n["time"]),
        "text": n["text"],
    }


def _codings(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


def _build_content(bind, r):
    pk = r["id"]
    identifiers = []
    for i in _rows(bind, "SELECT * FROM allergy_intolerance_identifier WHERE allergy_intolerance_pk = :pk ORDER BY id", pk=pk):
        identifiers.append({
            "use": i["use"],
            "type": _concept(_codings(bind, "allergy_intolerance_identifier_type_coding", "identifier_id", i["id"]),
                             i["type_text"]),
            "system": i["system"], "value": i["value"],
            "period": _period(i["period_start"], i["period_end"]),
            "assigner": _old_reference(i, "assigner"),
        })

    def status(table, text):
        return _concept(_codings(bind, table, "allergy_intolerance_pk", pk), text)

    notes = [_annotation(n) for n in _rows(
        bind, "SELECT * FROM allergy_intolerance_note WHERE allergy_intolerance_pk = :pk ORDER BY id", pk=pk)]
    reactions = []
    for x in _rows(bind, "SELECT * FROM allergy_intolerance_reaction WHERE allergy_intolerance_pk = :pk ORDER BY id", pk=pk):
        manifestations = [
            _concept(_codings(bind, "allergy_intolerance_reaction_manifestation_coding", "manifestation_id", m["id"]),
                     m["text"])
            for m in _codings(bind, "allergy_intolerance_reaction_manifestation", "reaction_id", x["id"])
        ]
        reactions.append({
            "substance": _concept(_codings(bind, "allergy_intolerance_reaction_substance_coding", "reaction_id", x["id"]),
                                  x["substance_text"]),
            "manifestation": manifestations,
            "description": x["description"],
            "onset": _iso(x["onset"]),
            "severity": x["severity"],
            "exposureRoute": _concept(
                _codings(bind, "allergy_intolerance_reaction_exposure_route_coding", "reaction_id", x["id"]),
                x["exposure_route_text"]),
            "note": [_annotation(n) for n in _codings(bind, "allergy_intolerance_reaction_note", "reaction_id", x["id"])],
        })

    onset = {}
    if r["onset_date_time"]:
        onset["onsetDateTime"] = _iso(r["onset_date_time"])
    elif r["onset_age"]:
        onset["onsetAge"] = _json(r["onset_age"])
    elif r["onset_period_start"] or r["onset_period_end"]:
        onset["onsetPeriod"] = _period(r["onset_period_start"], r["onset_period_end"])
    elif r["onset_range"]:
        onset["onsetRange"] = _json(r["onset_range"])
    elif r["onset_string"]:
        onset["onsetString"] = r["onset_string"]

    return _prune({
        "extension": list(_json(r["extension"]) or []),
        "identifier": identifiers,
        "clinicalStatus": status("allergy_intolerance_clinical_status_coding", r["clinical_status_text"]),
        "verificationStatus": status("allergy_intolerance_verification_status_coding", r["verification_status_text"]),
        "type": r["type"],
        "category": list(r["category_list"] or []),
        "criticality": r["criticality"],
        "code": status("allergy_intolerance_code_coding", r["code_text"]),
        "patient": _old_reference(r, "patient"),
        "encounter": _old_reference(r, "encounter"),
        **onset,
        "recordedDate": _iso(r["recorded_date"]),
        "recorder": _old_reference(r, "recorder"),
        "asserter": _old_reference(r, "asserter"),
        "lastOccurrence": _iso(r["last_occurrence"]),
        "note": notes,
        "reaction": reactions,
    })


def _backfill_content(bind):
    # `category` is an enum array: cast it to text[] so the driver returns a list.
    for r in _rows(bind, "SELECT *, category::text[] AS category_list FROM allergy_intolerance"):
        bind.execute(
            sa.text("UPDATE allergy_intolerance SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, r)), "id": r["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_ACTOR_TYPES = ("Practitioner", "PractitionerRole", "Patient", "RelatedPerson")
_CATEGORY_SYSTEM = "http://hl7.org/fhir/allergy-intolerance-category"
_SEVERITY_SYSTEM = "http://hl7.org/fhir/reaction-event-severity"


def _ref_params(prefix, ref, allowed):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    match = _REF.match(reference or "")
    rtype, rid = (match["type"], int(match["id"])) if match and match["type"] in allowed else (None, None)
    return {f"{prefix}_reference": reference, f"{prefix}_type": rtype, f"{prefix}_id": rid,
            f"{prefix}_identifier_system": identifier.get("system"),
            f"{prefix}_identifier_value": identifier.get("value")}


def _insert_token(bind, pk, param, system, code, display_norm, text_norm):
    bind.execute(sa.text(
        "INSERT INTO allergy_intolerance_token (allergy_intolerance_pk, param, system, code, display_norm, text_norm) "
        "VALUES (:pk, :param, :s, :c, :d, :t)"),
        {"pk": pk, "param": param, "s": system, "c": code, "d": display_norm, "t": text_norm})


def _concept_tokens(bind, pk, param, concept):
    if not concept:
        return
    text = _norm(concept.get("text"))
    codings = [c for c in concept.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
    for c in codings or ([{}] if text else []):
        _insert_token(bind, pk, param, c.get("system"), c.get("code"), _norm(c.get("display")), text)


def _rebuild_index(bind):
    for row in _rows(bind, "SELECT id, content FROM allergy_intolerance"):
        pk, doc = row["id"], _json(row["content"])

        recorded_start, recorded_end = _bounds(doc.get("recordedDate"))
        occurrence_start, occurrence_end = _bounds(doc.get("lastOccurrence"))
        columns = {
            "recorded_date_start": recorded_start, "recorded_date_end": recorded_end,
            "last_occurrence_start": occurrence_start, "last_occurrence_end": occurrence_end,
            **_ref_params("patient", doc.get("patient"), ("Patient",)),
            **_ref_params("recorder", doc.get("recorder"), _ACTOR_TYPES),
            **_ref_params("asserter", doc.get("asserter"), _ACTOR_TYPES),
        }
        bind.execute(
            sa.text("UPDATE allergy_intolerance SET " + ", ".join(f"{k} = :{k}" for k in columns) + " WHERE id = :pk"),
            {**columns, "pk": pk})

        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO allergy_intolerance_identifier (allergy_intolerance_pk, system, value, type_system, "
                    "type_code, type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})

        _concept_tokens(bind, pk, "clinical-status", doc.get("clinicalStatus"))
        _concept_tokens(bind, pk, "verification-status", doc.get("verificationStatus"))
        _concept_tokens(bind, pk, "code", doc.get("code"))
        for category in doc.get("category") or []:
            _insert_token(bind, pk, "category", _CATEGORY_SYSTEM, category, None, None)
        for reaction in doc.get("reaction") or []:
            _concept_tokens(bind, pk, "code", reaction.get("substance"))
            for manifestation in reaction.get("manifestation") or []:
                _concept_tokens(bind, pk, "manifestation", manifestation)
            _concept_tokens(bind, pk, "route", reaction.get("exposureRoute"))
            if reaction.get("severity"):
                _insert_token(bind, pk, "severity", _SEVERITY_SYSTEM, reaction["severity"], None, None)
            onset_start, onset_end = _bounds(reaction.get("onset"))
            if onset_start or onset_end:
                bind.execute(sa.text(
                    "INSERT INTO allergy_intolerance_reaction (allergy_intolerance_pk, onset_start, onset_end) "
                    "VALUES (:pk, :s, :e)"), {"pk": pk, "s": onset_start, "e": onset_end})


# Children first (grandchildren before their parents).
_OLD_CHILD_TABLES = (
    "allergy_intolerance_reaction_manifestation_coding",
    "allergy_intolerance_reaction_manifestation",
    "allergy_intolerance_reaction_substance_coding",
    "allergy_intolerance_reaction_exposure_route_coding",
    "allergy_intolerance_reaction_note",
    "allergy_intolerance_reaction",
    "allergy_intolerance_note",
    "allergy_intolerance_identifier_type_coding",
    "allergy_intolerance_identifier",
    "allergy_intolerance_clinical_status_coding",
    "allergy_intolerance_verification_status_coding",
    "allergy_intolerance_code_coding",
)

_IDENTIFIER_PARTS = ("use", "type_system", "type_version", "type_code", "type_display", "type_text",
                     "type_user_selected", "system", "value", "period_start", "period_end")

_OLD_MAIN_COLUMNS = (
    "extension", "clinical_status_text", "verification_status_text", "category", "code_text",
    "onset_date_time", "onset_age", "onset_period_start", "onset_period_end", "onset_range", "onset_string",
    "recorded_date", "last_occurrence",
    *(f"encounter_{part}" for part in ("reference", "type", "id", "display")),
    *(f"encounter_identifier_{p}" for p in _IDENTIFIER_PARTS),
    *(f"{prefix}_display" for prefix in ("patient", "recorder", "asserter")),
    *(f"{prefix}_identifier_{p}" for prefix in ("patient", "recorder", "asserter")
      for p in _IDENTIFIER_PARTS if p not in ("system", "value")),
)

_OLD_ENUMS = (
    "allergy_intolerance_category",
    "allergy_intolerance_severity",
    "allergy_intolerance_patient_reference_type",
    "allergy_intolerance_encounter_reference_type",
    "allergy_intolerance_recorder_reference_type",
    "allergy_intolerance_asserter_reference_type",
    "allergy_intolerance_note_author_reference_type",
    "allergy_intolerance_reaction_note_author_reference_type",
)


def _fk():
    return sa.Column("allergy_intolerance_pk", sa.BigInteger(), sa.ForeignKey("allergy_intolerance.id"), nullable=False)


def _index(table, *columns):
    op.create_index(op.f("ix_" + table + "_" + columns[0]), table, list(columns))


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('allergy_intolerance', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are
    # rebuilt from it below.
    for table in _OLD_CHILD_TABLES:
        op.drop_table(table)
    for column in _OLD_MAIN_COLUMNS:
        op.drop_column('allergy_intolerance', column)

    # `patient` is 1..1 in R4, but nullability is the validator's rule, not the database's.
    op.alter_column('allergy_intolerance', 'patient_reference', nullable=True)
    # The reference types were per-field enums; they are plain strings now.
    for prefix in ('patient', 'recorder', 'asserter'):
        op.alter_column('allergy_intolerance', f'{prefix}_type', type_=sa.String(), nullable=True,
                        postgresql_using=f'{prefix}_type::text')
    for enum in _OLD_ENUMS:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
    # The public id's sequence is now its server default.
    op.execute("ALTER TABLE allergy_intolerance ALTER COLUMN allergy_intolerance_id "
               "SET DEFAULT nextval('allergy_intolerance_pub_seq')")

    for column in ('recorded_date_start', 'recorded_date_end', 'last_occurrence_start', 'last_occurrence_end'):
        op.add_column('allergy_intolerance', sa.Column(column, sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_allergy_intolerance_recorded_date', 'allergy_intolerance',
                    ['recorded_date_start', 'recorded_date_end'])
    op.create_index('ix_allergy_intolerance_recorder_type_id', 'allergy_intolerance', ['recorder_type', 'recorder_id'])
    op.create_index('ix_allergy_intolerance_asserter_type_id', 'allergy_intolerance', ['asserter_type', 'asserter_id'])
    op.create_index('ix_allergy_intolerance_patient_id', 'allergy_intolerance', ['patient_id'])

    op.create_table(
        'allergy_intolerance_identifier',
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
    _index('allergy_intolerance_identifier', 'allergy_intolerance_pk')
    _index('allergy_intolerance_identifier', 'value')

    op.create_table(
        'allergy_intolerance_token',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('param', sa.String(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index('allergy_intolerance_token', 'allergy_intolerance_pk')
    op.create_index('ix_allergy_intolerance_token_param_code', 'allergy_intolerance_token', ['param', 'code'])

    op.create_table(
        'allergy_intolerance_reaction',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('onset_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('onset_end', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index('allergy_intolerance_reaction', 'allergy_intolerance_pk')

    _rebuild_index(bind)
    op.alter_column('allergy_intolerance', 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "allergy_intolerance content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
