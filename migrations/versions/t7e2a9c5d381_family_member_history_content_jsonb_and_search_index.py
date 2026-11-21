"""family_member_history: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: t7e2a9c5d381
Revises: s6d1f8b4c270
Create Date: 2026-12-06 10:00:00.000000

Medplum-style storage for FamilyMemberHistory (see FamilyMemberHistoryModel's docstring),
same as the other resources already moved (Organization 5b1969c2ec19, Location
8c41d2e7a9b3, Practitioner a7d3f19c2b64, HealthcareService c9f5b2d7e813, Endpoint
d1a6c3e8f924, PractitionerRole e2b7d4f9a035, Schedule f3c8e5a1b947, Slot g4d9f6b2c058,
Patient h5e0a7c3d169, Appointment i6f1b8d4e27a, AppointmentResponse j7a2c9e5f381,
Encounter k8b3d0f6a492, RelatedPerson l9c4e1a7b503, AllergyIntolerance m0d5f2b8c614,
Condition n1e6a3c9d725, Procedure o2f7b4d0e836, DiagnosticReport p3a8c5e1f947,
Immunization q4b9d6f2a058, ImmunizationRecommendation r5c0e7a3b169, ImmunizationEvaluation
s6d1f8b4c270). The whole FHIR resource moves into `family_member_history.content`; every
column/table that survives is a search index for one of the FHIR R4 FamilyMemberHistory
search parameters (or `_id` / `_lastUpdated`), derived from `content`:

  family_member_history: status (the Postgres enum already held the real FHIR codes, so it
      stays; only its NOT NULL goes), date_start/_end (the dateTime, the range it covers)
      and the patient_* reference columns (`patient_type` becomes a plain string,
      `patient_reference` becomes nullable); the public id keeps its sequence as a server
      default; new: content
  family_member_history_identifier: rebuilt as an index table
  family_member_history_token: new - code (condition.code), relationship, sex
  family_member_history_reference: new - instantiates-canonical
  family_member_history_instantiates_uri: new - instantiates-uri
  dropped: every old child table (identifier type, data absent reason, relationship, sex,
      reason code / reference, note and condition codings / notes tables), every main-table
      column with no search parameter (the canonical / uri arrays, name, born / age /
      deceased elements, estimated age, extension, the text of every concept and the display
      / logical-identifier details of the patient reference) and the four per-field
      `family_member_history_*` reference-type / comparator enums.

upgrade: (1) builds `content` for every existing row from the old columns and tables - a
frozen copy of the old to_fhir_family_member_history() logic (but keeping a reference's raw
string, so an absolute URL is not lost), so this migration never depends on application code
that has since changed; (2) drops the old child tables/columns and creates the index tables;
(3) rebuilds the index from `content`.

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
revision: str = 't7e2a9c5d381'
down_revision: Union[str, None] = 's6d1f8b4c270'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUS = ('partial', 'completed', 'entered-in-error', 'health-unknown')
P = "family_member_history"


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

_COMPARATOR_SYMBOLS = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}


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


def _quantity(row, prefix):
    value = row[f"{prefix}_value"]
    if value is None:
        return None
    comparator = row.get(f"{prefix}_comparator")
    return {"value": float(value), "comparator": _COMPARATOR_SYMBOLS.get(comparator) if comparator else None,
            "unit": row[f"{prefix}_unit"], "system": row[f"{prefix}_system"], "code": row[f"{prefix}_code"]}


def _range(row, prefix):
    out = {}
    for side in ("low", "high"):
        value = row[f"{prefix}_{side}_value"]
        if value is not None:
            out[side] = {"value": float(value), "unit": row[f"{prefix}_{side}_unit"],
                         "system": row[f"{prefix}_{side}_system"], "code": row[f"{prefix}_{side}_code"]}
    return out or None


def _rows_of(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


def _note(n):
    note = {"time": _iso(n["time"]), "text": n["text"]}
    author = _prune(_old_reference(n, "author"))
    if author:
        note["authorReference"] = author
    elif n["author_string"]:
        note["authorString"] = n["author_string"]
    return note


def _condition(bind, c):
    cid = c["id"]
    entry = {
        "code": _concept(_rows_of(bind, f"{P}_condition_code_coding", f"{P}_condition_id", cid), c["code_text"]),
        "outcome": _concept(_rows_of(bind, f"{P}_condition_outcome_coding", f"{P}_condition_id", cid),
                            c["outcome_text"]),
        "contributedToDeath": c["contributed_to_death"],
        "note": [_note(n) for n in _rows_of(bind, f"{P}_condition_note", f"{P}_condition_id", cid)],
    }
    if c["onset_age_value"] is not None:
        entry["onsetAge"] = _quantity(c, "onset_age")
    elif c["onset_range_low_value"] is not None or c["onset_range_high_value"] is not None:
        entry["onsetRange"] = _range(c, "onset_range")
    elif c["onset_period_start"] or c["onset_period_end"]:
        entry["onsetPeriod"] = _period(c["onset_period_start"], c["onset_period_end"])
    elif c["onset_string"]:
        entry["onsetString"] = c["onset_string"]
    return entry


def _build_content(bind, r):
    pk = r["id"]
    identifiers = []
    for i in _rows_of(bind, f"{P}_identifier", f"{P}_pk", pk):
        identifiers.append({
            "use": i["use"],
            "type": _concept(_rows_of(bind, f"{P}_identifier_type_coding", f"{P}_identifier_id", i["id"]),
                             i["type_text"]),
            "system": i["system"], "value": i["value"],
            "period": _period(i["period_start"], i["period_end"]),
            "assigner": _old_reference(i, "assigner"),
        })
    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": identifiers,
        "instantiatesCanonical": list(r["instantiates_canonical"] or []),
        "instantiatesUri": list(r["instantiates_uri"] or []),
        "status": r["status_text"],
        "dataAbsentReason": _concept(_rows_of(bind, f"{P}_data_absent_reason_coding", f"{P}_pk", pk),
                                     r["data_absent_reason_text"]),
        "patient": _old_reference(r, "patient"),
        "date": _iso(r["date"]),
        "name": r["name"],
        "relationship": _concept(_rows_of(bind, f"{P}_relationship_coding", f"{P}_pk", pk), r["relationship_text"]),
        "sex": _concept(_rows_of(bind, f"{P}_sex_coding", f"{P}_pk", pk), r["sex_text"]),
        "estimatedAge": r["estimated_age"],
        "reasonCode": [
            _concept(_rows_of(bind, f"{P}_reason_code_coding", f"{P}_reason_code_id", x["id"]), x["text"])
            for x in _rows_of(bind, f"{P}_reason_code", f"{P}_pk", pk)
        ],
        "reasonReference": [_old_reference(x, "reference")
                            for x in _rows_of(bind, f"{P}_reason_reference", f"{P}_pk", pk)],
        "note": [_note(n) for n in _rows_of(bind, f"{P}_note", f"{P}_pk", pk)],
        "condition": [_condition(bind, c) for c in _rows_of(bind, f"{P}_condition", f"{P}_pk", pk)],
    }
    # born[x]
    if r["born_period_start"] or r["born_period_end"]:
        content["bornPeriod"] = _period(r["born_period_start"], r["born_period_end"])
    elif r["born_date"]:
        content["bornDate"] = _iso(r["born_date"])
    elif r["born_string"]:
        content["bornString"] = r["born_string"]
    # age[x]
    if r["age_age_value"] is not None:
        content["ageAge"] = _quantity(r, "age_age")
    elif r["age_range_low_value"] is not None or r["age_range_high_value"] is not None:
        content["ageRange"] = _range(r, "age_range")
    elif r["age_string"]:
        content["ageString"] = r["age_string"]
    # deceased[x]
    if r["deceased_boolean"] is not None:
        content["deceasedBoolean"] = r["deceased_boolean"]
    elif r["deceased_age_value"] is not None:
        content["deceasedAge"] = _quantity(r, "deceased_age")
    elif r["deceased_range_low_value"] is not None or r["deceased_range_high_value"] is not None:
        content["deceasedRange"] = _range(r, "deceased_range")
    elif r["deceased_date"]:
        content["deceasedDate"] = _iso(r["deceased_date"])
    elif r["deceased_string"]:
        content["deceasedString"] = r["deceased_string"]
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
_CANONICAL_TYPES = ("PlanDefinition", "Questionnaire", "ActivityDefinition", "Measure", "OperationDefinition")


def _typed(reference, allowed):
    match = _REF.match(reference or "")
    return (match["type"], int(match["id"])) if match and match["type"] in allowed else (None, None)


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


def _rebuild_index(bind):
    for row in _rows(bind, f"SELECT id, content FROM {P}"):
        pk, doc = row["id"], _json(row["content"])

        start, end = _bounds(doc.get("date"))
        status = doc.get("status")
        patient = doc.get("patient") or {}
        reference = patient.get("reference")
        identifier = patient.get("identifier") or {}
        ptype, pid = _typed(reference, ("Patient",))
        bind.execute(
            sa.text(f"UPDATE {P} SET status = CAST(:status AS family_member_history_status), date_start = :ds, "
                    "date_end = :de, patient_reference = :pr, patient_type = :pt, patient_id = :pi, "
                    "patient_identifier_system = :isys, patient_identifier_value = :ival WHERE id = :pk"),
            {"status": status if status in _STATUS else None, "ds": start, "de": end, "pr": reference,
             "pt": ptype, "pi": pid, "isys": identifier.get("system"), "ival": identifier.get("value"), "pk": pk})

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

        for condition in doc.get("condition") or []:
            _insert_token(bind, pk, "code", (condition or {}).get("code"))
        _insert_token(bind, pk, "relationship", doc.get("relationship"))
        _insert_token(bind, pk, "sex", doc.get("sex"))

        for canonical in doc.get("instantiatesCanonical") or []:
            if not canonical:
                continue
            rtype, rid = _typed(canonical, _CANONICAL_TYPES)
            bind.execute(sa.text(
                f"INSERT INTO {P}_reference ({P}_pk, param, reference_reference, reference_type, reference_id) "
                "VALUES (:pk, 'instantiates-canonical', :r, :t, :i)"),
                {"pk": pk, "r": canonical, "t": rtype, "i": rid})
        for uri in doc.get("instantiatesUri") or []:
            if uri:
                bind.execute(sa.text(f"INSERT INTO {P}_instantiates_uri ({P}_pk, uri) VALUES (:pk, :u)"),
                             {"pk": pk, "u": uri})


# Children first (grandchildren before their parents).
_OLD_CHILD_TABLES = (
    f"{P}_condition_note", f"{P}_condition_code_coding", f"{P}_condition_outcome_coding", f"{P}_condition",
    f"{P}_note", f"{P}_reason_reference", f"{P}_reason_code_coding", f"{P}_reason_code",
    f"{P}_sex_coding", f"{P}_relationship_coding", f"{P}_data_absent_reason_coding",
    f"{P}_identifier_type_coding", f"{P}_identifier",
)

# The per-field reference-type and comparator enums of the old schema (`family_member_history_status`
# stays).
_OLD_ENUMS = (
    f"{P}_patient_reference_type", f"{P}_reason_reference_type", f"{P}_note_author_reference_type",
    f"{P}_quantity_comparator",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns, `status` and the
# index columns of `patient` (its reference-type enum becomes a plain string).
_KEEP = {
    "id", "family_member_history_id", "tenant_id", "created_by", "updated_by", "created_at", "updated_at",
    "content", "status",
    *(f"patient_{part}" for part in ("reference", "type", "id", "identifier_system", "identifier_value")),
}


def _fk():
    return sa.Column(f"{P}_pk", sa.BigInteger(), sa.ForeignKey(f"{P}.id"), nullable=False)


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
    op.alter_column(P, 'status', nullable=True)
    for name in _OLD_ENUMS:
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # The public id's sequence is its server default (as it already was).
    op.execute(f"ALTER TABLE {P} ALTER COLUMN family_member_history_id "
               "SET DEFAULT nextval('family_member_history_pub_seq')")

    op.add_column(P, sa.Column('date_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column(P, sa.Column('date_end', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_family_member_history_date', P, ['date_start', 'date_end'])

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
    op.create_index('ix_family_member_history_token_param_code', f'{P}_token', ['param', 'code'])

    op.create_table(
        f'{P}_reference',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('param', sa.String(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index(f'{P}_reference', f'{P}_pk')
    op.create_index('ix_family_member_history_reference_param_type_id', f'{P}_reference',
                    ['param', 'reference_type', 'reference_id'])

    op.create_table(
        f'{P}_instantiates_uri',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('uri', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    _index(f'{P}_instantiates_uri', f'{P}_pk')
    _index(f'{P}_instantiates_uri', 'uri')

    _rebuild_index(bind)
    op.create_index(f'ix_{P}_patient_id', P, ['patient_id'], if_not_exists=True)
    op.alter_column(P, 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "family_member_history content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
