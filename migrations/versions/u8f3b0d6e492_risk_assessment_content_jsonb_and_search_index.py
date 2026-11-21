"""risk_assessment: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: u8f3b0d6e492
Revises: t7e2a9c5d381
Create Date: 2026-12-07 10:00:00.000000

Medplum-style storage for RiskAssessment (see RiskAssessmentModel's docstring), same as the
other resources already moved (Organization 5b1969c2ec19, Location 8c41d2e7a9b3, Practitioner
a7d3f19c2b64, HealthcareService c9f5b2d7e813, Endpoint d1a6c3e8f924, PractitionerRole
e2b7d4f9a035, Schedule f3c8e5a1b947, Slot g4d9f6b2c058, Patient h5e0a7c3d169, Appointment
i6f1b8d4e27a, AppointmentResponse j7a2c9e5f381, Encounter k8b3d0f6a492, RelatedPerson
l9c4e1a7b503, AllergyIntolerance m0d5f2b8c614, Condition n1e6a3c9d725, Procedure
o2f7b4d0e836, DiagnosticReport p3a8c5e1f947, Immunization q4b9d6f2a058,
ImmunizationRecommendation r5c0e7a3b169, ImmunizationEvaluation s6d1f8b4c270,
FamilyMemberHistory t7e2a9c5d381). The whole FHIR resource moves into `risk_assessment.content`;
every column/table that survives is a search index for one of the FHIR R4 RiskAssessment search
parameters (or `_id` / `_lastUpdated`), derived from `content`:

  risk_assessment: date_start/_end (occurrenceDateTime, the range it covers) and the subject_*,
      encounter_*, condition_* and performer_* reference columns (`*_type` becomes a plain
      string); the public id gets its sequence as a server default; new: content. `status` has
      no search parameter on this resource, so its column and the `risk_assessment_status`
      enum go (the value is kept in `content`).
  risk_assessment_identifier: rebuilt as an index table
  risk_assessment_token: new - method, risk (prediction.qualitativeRisk)
  risk_assessment_prediction: rebuilt - one row per prediction with a probability (its lower
      and upper bound; a decimal is a point)
  dropped: every old child table (identifier coding, method / code codings, reason code /
      reference, basis, note, prediction outcome / qualitative risk codings), every main-table
      column with no search parameter (status, text of every concept, based on, parent,
      occurrence period, mitigation, extension and the display / logical-identifier details of
      every reference) and the four per-field `risk_assessment_*_reference_type` enums (the
      shared `subject_reference_type` / `encounter_reference_type` stay).

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_risk_assessment() logic (but keeping a reference's raw string, so an
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
from decimal import Decimal, InvalidOperation
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'u8f3b0d6e492'
down_revision: Union[str, None] = 't7e2a9c5d381'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "risk_assessment"


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
_TYPE_NAMES = {t.upper(): t for t in ("Patient", "Group", "Encounter", "Condition", "Practitioner",
                                      "PractitionerRole", "Device", "Observation", "DiagnosticReport",
                                      "DocumentReference", "RelatedPerson", "Organization")}


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
        ref_type = str(row[f"{prefix}_type"])
        raw = f"{_TYPE_NAMES.get(ref_type.upper(), ref_type)}/{row[prefix + '_id']}"
    return {
        "reference": raw,
        "display": row[f"{prefix}_display"],
        "identifier": _fallback_identifier(row, prefix),
    }


def _rows_of(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


def _quantity(row, prefix):
    value = row[f"{prefix}_value"]
    if value is None:
        return None
    return {"value": float(value), "unit": row[f"{prefix}_unit"], "system": row[f"{prefix}_system"],
            "code": row[f"{prefix}_code"]}


def _range(row, prefix):
    out = {}
    for side in ("low", "high"):
        quantity = _quantity(row, f"{prefix}_{side}")
        if quantity:
            out[side] = quantity
    return out or None


def _note(n):
    note = {"time": _iso(n["time"]), "text": n["text"]}
    author = _prune(_old_reference(n, "author"))
    if author:
        note["authorReference"] = author
    elif n["author_string"]:
        note["authorString"] = n["author_string"]
    return note


def _prediction(bind, p):
    pid = p["id"]
    entry = {
        "outcome": _concept(_rows_of(bind, f"{P}_pred_outcome_coding", f"{P}_prediction_id", pid), p["outcome_text"]),
        "qualitativeRisk": _concept(_rows_of(bind, f"{P}_pred_qual_risk_coding", f"{P}_prediction_id", pid),
                                    p["qualitative_risk_text"]),
        "relativeRisk": float(p["relative_risk"]) if p["relative_risk"] is not None else None,
        "rationale": p["rationale"],
    }
    if p["probability_decimal"] is not None:
        entry["probabilityDecimal"] = float(p["probability_decimal"])
    else:
        entry["probabilityRange"] = _range(p, "probability_range")
    if p["when_period_start"] or p["when_period_end"]:
        entry["whenPeriod"] = _period(p["when_period_start"], p["when_period_end"])
    else:
        entry["whenRange"] = _range(p, "when_range")
    return entry


def _build_content(bind, r):
    pk = r["id"]
    identifiers = []
    for i in _rows_of(bind, f"{P}_identifier", f"{P}_pk", pk):
        identifiers.append({
            "use": i["use"],
            "type": _concept(_rows_of(bind, f"{P}_identifier_coding", f"{P}_identifier_id", i["id"]), i["type_text"]),
            "system": i["system"], "value": i["value"],
            "period": _period(i["period_start"], i["period_end"]),
            "assigner": _old_reference(i, "assigner"),
        })
    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": identifiers,
        "status": r["status_text"],
        "subject": _old_reference(r, "subject"),
        "basedOn": _old_reference(r, "based_on"),
        "parent": _old_reference(r, "parent"),
        "encounter": _old_reference(r, "encounter"),
        "condition": _old_reference(r, "condition"),
        "performer": _old_reference(r, "performer"),
        "method": _concept(_rows_of(bind, f"{P}_method_coding", f"{P}_pk", pk), r["method_text"]),
        "code": _concept(_rows_of(bind, f"{P}_code_coding", f"{P}_pk", pk), r["code_text"]),
        "reasonCode": [
            _concept(_rows_of(bind, f"{P}_reason_code_coding", f"{P}_reason_code_id", x["id"]), x["text"])
            for x in _rows_of(bind, f"{P}_reason_code", f"{P}_pk", pk)
        ],
        "reasonReference": [_old_reference(x, "reference")
                            for x in _rows_of(bind, f"{P}_reason_reference", f"{P}_pk", pk)],
        "basis": [_old_reference(x, "reference") for x in _rows_of(bind, f"{P}_basis", f"{P}_pk", pk)],
        "prediction": [_prediction(bind, p) for p in _rows_of(bind, f"{P}_prediction", f"{P}_pk", pk)],
        "mitigation": r["mitigation"],
        "note": [_note(n) for n in _rows_of(bind, f"{P}_note", f"{P}_pk", pk)],
    }
    if r["occurrence_date_time"]:
        content["occurrenceDateTime"] = _iso(r["occurrence_date_time"])
    elif r["occurrence_period_start"] or r["occurrence_period_end"]:
        content["occurrencePeriod"] = _period(r["occurrence_period_start"], r["occurrence_period_end"])
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
_SUBJECT_TYPES = ("Patient", "Group")
_PERFORMER_TYPES = ("Practitioner", "PractitionerRole", "Device")


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
            f"INSERT INTO {P}_token ({P}_pk, param, system, code, display_norm, text_norm) "
            "VALUES (:pk, :param, :s, :c, :d, :t)"),
            {"pk": pk, "param": param, "s": c.get("system"), "c": c.get("code"), "d": _norm(c.get("display")),
             "t": text})


def _number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def _rebuild_index(bind):
    for row in _rows(bind, f"SELECT id, content FROM {P}"):
        pk, doc = row["id"], _json(row["content"])

        start, end = _bounds(doc.get("occurrenceDateTime"))
        columns = {
            "date_start": start, "date_end": end,
            **_ref_params("subject", doc.get("subject"), _SUBJECT_TYPES),
            **_ref_params("encounter", doc.get("encounter"), ("Encounter",)),
            **_ref_params("condition", doc.get("condition"), ("Condition",)),
            **_ref_params("performer", doc.get("performer"), _PERFORMER_TYPES),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(sa.text(f"UPDATE {P} SET {sets} WHERE id = :pk"), {**columns, "pk": pk})

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

        _insert_token(bind, pk, "method", doc.get("method"))
        for prediction in doc.get("prediction") or []:
            prediction = prediction or {}
            _insert_token(bind, pk, "risk", prediction.get("qualitativeRisk"))
            if prediction.get("probabilityDecimal") is not None:
                low = high = _number(prediction["probabilityDecimal"])
            else:
                probability = prediction.get("probabilityRange") or {}
                low = _number((probability.get("low") or {}).get("value"))
                high = _number((probability.get("high") or {}).get("value"))
            if low is not None or high is not None:
                bind.execute(sa.text(
                    f"INSERT INTO {P}_prediction ({P}_pk, probability_low, probability_high) VALUES (:pk, :lo, :hi)"),
                    {"pk": pk, "lo": low, "hi": high})


# Children first (grandchildren before their parents).
_OLD_CHILD_TABLES = (
    f"{P}_identifier_coding", f"{P}_identifier",
    f"{P}_pred_outcome_coding", f"{P}_pred_qual_risk_coding", f"{P}_prediction",
    f"{P}_reason_code_coding", f"{P}_reason_code", f"{P}_reason_reference",
    f"{P}_method_coding", f"{P}_code_coding", f"{P}_basis", f"{P}_note",
)

# The per-field enums of the old schema (the shared `subject_reference_type` /
# `encounter_reference_type` stay: other tables use them).
_OLD_ENUMS = (
    f"{P}_status", f"{P}_condition_reference_type", f"{P}_performer_reference_type",
    f"{P}_reason_reference_type", f"{P}_note_author_reference_type",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns and the index columns of
# the four kept references (their reference-type enums become plain strings).
_KEEP = {
    "id", "risk_assessment_id", "tenant_id", "created_by", "updated_by", "created_at", "updated_at", "content",
    *(f"{prefix}_{part}" for prefix in ("subject", "encounter", "condition", "performer")
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

    # The reference types were enums; they are plain strings now.
    for prefix in ('subject', 'encounter', 'condition', 'performer'):
        op.alter_column(P, f'{prefix}_type', type_=sa.String(), nullable=True, postgresql_using=f'{prefix}_type::text')
    for name in _OLD_ENUMS:
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # The public id's sequence is now its server default.
    op.execute(f"ALTER TABLE {P} ALTER COLUMN risk_assessment_id SET DEFAULT nextval('risk_assessment_pub_seq')")

    op.add_column(P, sa.Column('date_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column(P, sa.Column('date_end', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_risk_assessment_date', P, ['date_start', 'date_end'])

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
    op.create_index('ix_risk_assessment_token_param_code', f'{P}_token', ['param', 'code'])

    op.create_table(
        f'{P}_prediction',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('probability_low', sa.Numeric(), nullable=True),
        sa.Column('probability_high', sa.Numeric(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index(f'{P}_prediction', f'{P}_pk')

    _rebuild_index(bind)
    for column in ('subject_id', 'encounter_id', 'condition_id', 'performer_id'):
        op.create_index(f'ix_{P}_{column}', P, [column], if_not_exists=True)
    op.alter_column(P, 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "risk_assessment content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
