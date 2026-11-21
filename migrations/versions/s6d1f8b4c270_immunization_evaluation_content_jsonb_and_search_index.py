"""immunization_evaluation: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: s6d1f8b4c270
Revises: r5c0e7a3b169
Create Date: 2026-12-05 10:00:00.000000

Medplum-style storage for ImmunizationEvaluation (see ImmunizationEvaluationModel's
docstring), same as the other resources already moved (Organization 5b1969c2ec19, Location
8c41d2e7a9b3, Practitioner a7d3f19c2b64, HealthcareService c9f5b2d7e813, Endpoint
d1a6c3e8f924, PractitionerRole e2b7d4f9a035, Schedule f3c8e5a1b947, Slot g4d9f6b2c058,
Patient h5e0a7c3d169, Appointment i6f1b8d4e27a, AppointmentResponse j7a2c9e5f381,
Encounter k8b3d0f6a492, RelatedPerson l9c4e1a7b503, AllergyIntolerance m0d5f2b8c614,
Condition n1e6a3c9d725, Procedure o2f7b4d0e836, DiagnosticReport p3a8c5e1f947,
Immunization q4b9d6f2a058, ImmunizationRecommendation r5c0e7a3b169). The whole FHIR
resource moves into `immunization_evaluation.content`; every column/table that survives is
a search index for one of the FHIR R4 ImmunizationEvaluation search parameters (or `_id` /
`_lastUpdated`), derived from `content`:

  immunization_evaluation: status (the Postgres enum already held the real FHIR codes, so it
      stays; only its NOT NULL goes), date_start/_end (the dateTime, the range it covers) and
      the patient_* and immunization_event_* reference columns (`*_type` becomes a plain
      string, `*_reference` becomes nullable); the public id keeps its sequence as a server
      default; new: content
  immunization_evaluation_identifier: rebuilt as an index table
  immunization_evaluation_token: new - dose-status, target-disease
  dropped: every old child table (identifier type, dose status, dose status reason and
      target disease codings), every main-table column with no search parameter (authority,
      extension, description, series, dose numbers, the text of every concept and the display
      / logical-identifier details of every reference), the two dose-choice CHECK constraints
      and the three per-field `immunization_evaluation_*_reference_type` enums.

upgrade: (1) builds `content` for every existing row from the old columns and tables - a
frozen copy of the old to_fhir_immunization_evaluation() logic (but keeping a reference's
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
revision: str = 's6d1f8b4c270'
down_revision: Union[str, None] = 'r5c0e7a3b169'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUS = ('completed', 'entered-in-error')


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


# The old reference-type enums were declared without `values_callable`, so Postgres holds the
# member NAMES (`PATIENT`), not the FHIR type names (`Patient`).
_TYPE_NAMES = {"PATIENT": "Patient", "ORGANIZATION": "Organization", "IMMUNIZATION": "Immunization"}


def _old_reference(row, prefix):
    raw = row[f"{prefix}_reference"]
    if not raw and row[f"{prefix}_type"] and row[f"{prefix}_id"]:
        ref_type = row[f"{prefix}_type"]
        raw = f"{_TYPE_NAMES.get(ref_type, ref_type)}/{row[prefix + '_id']}"
    return {
        "reference": raw,
        "display": row[f"{prefix}_display"],
        "identifier": _fallback_identifier(row, prefix),
    }


def _rows_of(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


P = "immunization_evaluation"


def _build_content(bind, r):
    pk = r["id"]
    identifiers = []
    for i in _rows_of(bind, f"{P}_identifier", f"{P}_pk", pk):
        identifiers.append({
            "use": i["use"],
            "type": _concept(_rows_of(bind, f"{P}_identifier_type_coding", "identifier_id", i["id"]), i["type_text"]),
            "system": i["system"], "value": i["value"],
            "period": _period(i["period_start"], i["period_end"]),
            "assigner": _old_reference(i, "assigner"),
        })
    reasons = [
        _concept(_rows_of(bind, f"{P}_dose_status_reason_coding", "dose_status_reason_id", x["id"]), x["text"])
        for x in _rows_of(bind, f"{P}_dose_status_reason", f"{P}_pk", pk)
    ]
    authority = _old_reference(r, "authority") if (r["authority_reference"] or r["authority_id"]) else None
    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": identifiers,
        "status": _hyphenate(r["status_text"]),
        "patient": _old_reference(r, "patient"),
        "date": _iso(r["date"]),
        "authority": authority,
        "targetDisease": _concept(_rows_of(bind, f"{P}_target_disease_coding", f"{P}_pk", pk),
                                  r["target_disease_text"]),
        "immunizationEvent": _old_reference(r, "immunization_event"),
        "doseStatus": _concept(_rows_of(bind, f"{P}_dose_status_coding", f"{P}_pk", pk), r["dose_status_text"]),
        "doseStatusReason": reasons,
        "description": r["description"],
        "series": r["series"],
    }
    if r["dose_number_positive_int"] is not None:
        content["doseNumberPositiveInt"] = r["dose_number_positive_int"]
    elif r["dose_number_string"]:
        content["doseNumberString"] = r["dose_number_string"]
    if r["series_doses_positive_int"] is not None:
        content["seriesDosesPositiveInt"] = r["series_doses_positive_int"]
    elif r["series_doses_string"]:
        content["seriesDosesString"] = r["series_doses_string"]
    return _prune(content)


def _backfill_content(bind):
    # `status` is an enum: cast it to text so the driver returns the label.
    for r in _rows(bind, f"SELECT *, status::text AS status_text FROM {P}"):
        bind.execute(
            sa.text(f"UPDATE {P} SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, r), default=str), "id": r["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")


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


def _rebuild_index(bind):
    for row in _rows(bind, f"SELECT id, content FROM {P}"):
        pk, doc = row["id"], _json(row["content"])

        start, end = _bounds(doc.get("date"))
        status = doc.get("status")
        columns = {
            "date_start": start, "date_end": end,
            **_ref_params("patient", doc.get("patient"), ("Patient",)),
            **_ref_params("immunization_event", doc.get("immunizationEvent"), ("Immunization",)),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(f"UPDATE {P} SET status = CAST(:status AS immunization_evaluation_status), {sets} WHERE id = :pk"),
            {**columns, "status": status if status in _STATUS else None, "pk": pk})

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

        _insert_token(bind, pk, "dose-status", doc.get("doseStatus"))
        _insert_token(bind, pk, "target-disease", doc.get("targetDisease"))


# Children first (grandchildren before their parents).
_OLD_CHILD_TABLES = (
    f"{P}_identifier_type_coding", f"{P}_identifier",
    f"{P}_dose_status_reason_coding", f"{P}_dose_status_reason",
    f"{P}_dose_status_coding", f"{P}_target_disease_coding",
)

# The per-field reference-type enums of the old schema (`immunization_evaluation_status` stays).
_OLD_ENUMS = (
    f"{P}_patient_reference_type", f"{P}_authority_reference_type", f"{P}_immunization_event_reference_type",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns, `status` and the
# index columns of the two kept references (their reference-type enums become plain strings).
_KEEP = {
    "id", "immunization_evaluation_id", "tenant_id", "created_by", "updated_by", "created_at", "updated_at",
    "content", "status",
    *(f"{prefix}_{part}" for prefix in ("patient", "immunization_event")
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
    for name in ("ck_immunization_evaluation_dose_number_choice", "ck_immunization_evaluation_series_doses_choice"):
        op.execute(f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS {name}")
    existing = [r[0] for r in bind.execute(sa.text(
        f"SELECT column_name FROM information_schema.columns WHERE table_name = '{P}' "
        "AND table_schema = current_schema()"))]
    for column in existing:
        if column not in _KEEP:
            op.drop_column(P, column)

    # The reference types were enums; they are plain strings now.
    for prefix in ('patient', 'immunization_event'):
        op.alter_column(P, f'{prefix}_type', type_=sa.String(), nullable=True, postgresql_using=f'{prefix}_type::text')
        op.alter_column(P, f'{prefix}_reference', nullable=True)
    op.alter_column(P, 'status', nullable=True)
    for name in _OLD_ENUMS:
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # The public id's sequence is its server default (as it already was).
    op.execute(f"ALTER TABLE {P} ALTER COLUMN immunization_evaluation_id "
               "SET DEFAULT nextval('immunization_evaluation_pub_seq')")

    op.add_column(P, sa.Column('date_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column(P, sa.Column('date_end', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_immunization_evaluation_date', P, ['date_start', 'date_end'])

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
    op.create_index('ix_immunization_evaluation_token_param_code', f'{P}_token', ['param', 'code'])

    _rebuild_index(bind)
    for column in ('patient_id', 'immunization_event_id'):
        op.create_index(f'ix_{P}_{column}', P, [column], if_not_exists=True)
    op.alter_column(P, 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "immunization_evaluation content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
