"""condition: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: n1e6a3c9d725
Revises: m0d5f2b8c614
Create Date: 2026-11-30 10:00:00.000000

Medplum-style storage for Condition (see ConditionModel's docstring), same as the
other resources already moved (Organization 5b1969c2ec19, Location 8c41d2e7a9b3,
Practitioner a7d3f19c2b64, HealthcareService c9f5b2d7e813, Endpoint d1a6c3e8f924,
PractitionerRole e2b7d4f9a035, Schedule f3c8e5a1b947, Slot g4d9f6b2c058, Patient
h5e0a7c3d169, Appointment i6f1b8d4e27a, AppointmentResponse j7a2c9e5f381,
Encounter k8b3d0f6a492, RelatedPerson l9c4e1a7b503, AllergyIntolerance
m0d5f2b8c614). The whole FHIR resource moves into `condition.content`; every
column/table that survives is a search index for one of the FHIR R4 Condition
search parameters (or `_id` / `_lastUpdated`), derived from `content`:

  condition: recorded_date_start/_end, onset_date_start/_end and
      abatement_date_start/_end (the dateTime / Period as the range it covers),
      onset_age_* / abatement_age_* (an Age or a Range as low/high bounds with one
      unit), onset_string(+_norm) / abatement_string(+_norm), subject_*,
      encounter_*, asserter_* reference columns (`*_type` becomes a plain string,
      `subject_reference` nullable); the public id gets its sequence as a server
      default; new: content
  condition_identifier: rebuilt as an index table
  condition_token: new - body-site, category, clinical-status, code, evidence,
      severity, stage, verification-status
  condition_evidence_detail: rebuilt - one row per evidence.detail reference
  dropped: every old child table (clinical/verification status, severity and
      code codings, categories, body sites, stages with their codings and
      assessments, evidence with its codes and details, notes, identifier type
      codings), every main-table column with no search parameter (status/code
      texts, recorder, the identifier fallback, extension, the old onset /
      abatement shapes and the display / logical-identifier details of every
      reference) and the per-field reference-type / comparator enums
      (condition_quantity_comparator, condition_recorder_reference_type,
      condition_asserter_reference_type, condition_note_author_reference_type,
      condition_stage_assessment_reference_type). The shared subject_reference_type
      and encounter_reference_type enums are left alone.

upgrade: (1) builds `content` for every existing row from the old columns and
tables - a frozen copy of the old to_fhir_condition() logic (but keeping a
reference's raw string, so an absolute URL is not lost), so this migration never
depends on application code that has since changed; (2) drops the old child
tables/columns and creates the index tables; (3) rebuilds the index from
`content`.

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
revision: str = 'n1e6a3c9d725'
down_revision: Union[str, None] = 'm0d5f2b8c614'
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


def _period_bounds(period):
    """(start, end) of a Period: the first instant of `start`, the first instant
    after `end` (frozen copy of app.repository._content_index.period_bounds)."""
    period = period or {}
    start = _bounds(period.get("start"))[0] if period.get("start") else None
    end = _bounds(period.get("end"))[1] if period.get("end") else None
    return start, end


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


def _old_reference(row, prefix, raw_column=None):
    """`raw_column` names the column holding the raw reference string when it is not
    `{prefix}_reference` (a note's author keeps it in `author_reference`)."""
    raw = row[raw_column or f"{prefix}_reference"]
    if not raw and row[f"{prefix}_type"] and row[f"{prefix}_id"]:
        raw = f"{row[prefix + '_type']}/{row[prefix + '_id']}"
    return {
        "reference": raw,
        "display": row[f"{prefix}_display"],
        "identifier": _fallback_identifier(row, prefix),
    }


def _number(value):
    return float(value) if isinstance(value, Decimal) else value


def _quantity(r, prefix):
    if r[f"{prefix}_value"] is None:
        return None
    return {
        "value": _number(r[f"{prefix}_value"]),
        "comparator": _COMPARATOR_SYMBOLS.get(r[f"{prefix}_comparator"]),
        "unit": r[f"{prefix}_unit"], "system": r[f"{prefix}_system"], "code": r[f"{prefix}_code"],
    }


def _range_bound(r, prefix):
    if r[f"{prefix}_value"] is None:
        return None
    return {"value": _number(r[f"{prefix}_value"]), "unit": r[f"{prefix}_unit"],
            "system": r[f"{prefix}_system"], "code": r[f"{prefix}_code"]}


def _choice(r, element, name):
    """onset[x] / abatement[x]: the first populated shape, as the old mapper chose."""
    e = f"{element}_"
    if r[e + "date_time"]:
        return {f"{name}DateTime": _iso(r[e + "date_time"])}
    if r[e + "age_value"] is not None:
        return {f"{name}Age": _quantity(r, e + "age")}
    if r[e + "period_start"] or r[e + "period_end"]:
        return {f"{name}Period": _period(r[e + "period_start"], r[e + "period_end"])}
    if r[e + "range_low_value"] is not None or r[e + "range_high_value"] is not None:
        return {f"{name}Range": {"low": _range_bound(r, e + "range_low"), "high": _range_bound(r, e + "range_high")}}
    if r[e + "string"]:
        return {f"{name}String": r[e + "string"]}
    return {}


def _codings(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


def _annotation(n):
    ref = _old_reference(n, "author", raw_column="author_reference")
    has_ref = bool(ref["reference"] or ref["identifier"]["value"] or ref["identifier"]["system"])
    return {
        "authorReference": ref if has_ref else None,
        "authorString": None if has_ref else n["author_string"],
        "time": _iso(n["time"]),
        "text": n["text"],
    }


def _build_content(bind, r):
    pk = r["id"]
    identifiers = []
    for i in _rows(bind, "SELECT * FROM condition_identifier WHERE condition_pk = :pk ORDER BY id", pk=pk):
        identifiers.append({
            "use": i["use"],
            "type": _concept(_codings(bind, "condition_identifier_type_coding", "condition_identifier_id", i["id"]),
                             i["type_text"]),
            "system": i["system"], "value": i["value"],
            "period": _period(i["period_start"], i["period_end"]),
            "assigner": _old_reference(i, "assigner"),
        })

    def status(table, text):
        return _concept(_codings(bind, table, "condition_pk", pk), text)

    categories = [
        _concept(_codings(bind, "condition_category_coding", "condition_category_id", c["id"]), c["text"])
        for c in _codings(bind, "condition_category", "condition_pk", pk)
    ]
    body_sites = [
        _concept(_codings(bind, "condition_body_site_coding", "condition_body_site_id", b["id"]), b["text"])
        for b in _codings(bind, "condition_body_site", "condition_pk", pk)
    ]
    stages = []
    for s in _codings(bind, "condition_stage", "condition_pk", pk):
        stages.append({
            "summary": _concept(_codings(bind, "condition_stage_summary_coding", "condition_stage_id", s["id"]),
                                s["summary_text"]),
            "assessment": [_old_reference(a, "reference")
                           for a in _codings(bind, "condition_stage_assessment", "condition_stage_id", s["id"])],
            "type": _concept(_codings(bind, "condition_stage_type_coding", "condition_stage_id", s["id"]),
                             s["type_text"]),
        })
    evidence = []
    for e in _codings(bind, "condition_evidence", "condition_pk", pk):
        evidence.append({
            "code": [
                _concept(_codings(bind, "condition_evidence_code_coding", "condition_evidence_code_id", c["id"]),
                         c["text"])
                for c in _codings(bind, "condition_evidence_code", "condition_evidence_id", e["id"])
            ],
            "detail": [_old_reference(d, "reference")
                       for d in _codings(bind, "condition_evidence_detail", "condition_evidence_id", e["id"])],
        })
    notes = [_annotation(n) for n in _codings(bind, "condition_note", "condition_pk", pk)]

    return _prune({
        "extension": list(_json(r["extension"]) or []),
        "identifier": identifiers,
        "clinicalStatus": status("condition_clinical_status_coding", r["clinical_status_text"]),
        "verificationStatus": status("condition_verification_status_coding", r["verification_status_text"]),
        "category": categories,
        "severity": status("condition_severity_coding", r["severity_text"]),
        "code": status("condition_code_coding", r["code_text"]),
        "bodySite": body_sites,
        "subject": _old_reference(r, "subject"),
        "encounter": _old_reference(r, "encounter"),
        **_choice(r, "onset", "onset"),
        **_choice(r, "abatement", "abatement"),
        "recordedDate": _iso(r["recorded_date"]),
        "recorder": _old_reference(r, "recorder"),
        "asserter": _old_reference(r, "asserter"),
        "stage": stages,
        "evidence": evidence,
        "note": notes,
    })


def _backfill_content(bind):
    for r in _rows(bind, "SELECT * FROM condition"):
        bind.execute(
            sa.text("UPDATE condition SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, r)), "id": r["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_ACTOR_TYPES = ("Practitioner", "PractitionerRole", "Patient", "RelatedPerson")
_SUBJECT_TYPES = ("Patient", "Group")


def _ref_params(prefix, ref, allowed):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    match = _REF.match(reference or "")
    rtype, rid = (match["type"], int(match["id"])) if match and match["type"] in allowed else (None, None)
    return {f"{prefix}_reference": reference, f"{prefix}_type": rtype, f"{prefix}_id": rid,
            f"{prefix}_identifier_system": identifier.get("system"),
            f"{prefix}_identifier_value": identifier.get("value")}


def _dec(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _quantity_bounds(age, range_):
    if age:
        value = _dec(age.get("value"))
        return value, value, age.get("system"), age.get("code"), age.get("unit")
    if range_:
        low, high = range_.get("low") or {}, range_.get("high") or {}
        unit = low if low.get("value") is not None else high
        return _dec(low.get("value")), _dec(high.get("value")), unit.get("system"), unit.get("code"), unit.get("unit")
    return None, None, None, None, None


def _choice_columns(doc, element):
    if doc.get(f"{element}DateTime"):
        start, end = _bounds(doc[f"{element}DateTime"])
    else:
        start, end = _period_bounds(doc.get(f"{element}Period"))
    low, high, system, code, unit = _quantity_bounds(doc.get(f"{element}Age"), doc.get(f"{element}Range"))
    text = doc.get(f"{element}String")
    return {
        f"{element}_date_start": start, f"{element}_date_end": end,
        f"{element}_age_low": low, f"{element}_age_high": high, f"{element}_age_system": system,
        f"{element}_age_code": code, f"{element}_age_unit": unit,
        f"{element}_string": text, f"{element}_string_norm": _norm(text),
    }


def _insert_token(bind, pk, param, concept):
    if not concept:
        return
    text = _norm(concept.get("text"))
    codings = [c for c in concept.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
    for c in codings or ([{}] if text else []):
        bind.execute(sa.text(
            "INSERT INTO condition_token (condition_pk, param, system, code, display_norm, text_norm) "
            "VALUES (:pk, :param, :s, :c, :d, :t)"),
            {"pk": pk, "param": param, "s": c.get("system"), "c": c.get("code"), "d": _norm(c.get("display")),
             "t": text})


def _rebuild_index(bind):
    for row in _rows(bind, "SELECT id, content FROM condition"):
        pk, doc = row["id"], _json(row["content"])

        recorded_start, recorded_end = _bounds(doc.get("recordedDate"))
        columns = {
            "recorded_date_start": recorded_start, "recorded_date_end": recorded_end,
            **_choice_columns(doc, "onset"),
            **_choice_columns(doc, "abatement"),
            **_ref_params("subject", doc.get("subject"), _SUBJECT_TYPES),
            **_ref_params("encounter", doc.get("encounter"), ("Encounter",)),
            **_ref_params("asserter", doc.get("asserter"), _ACTOR_TYPES),
        }
        bind.execute(
            sa.text("UPDATE condition SET " + ", ".join(f"{k} = :{k}" for k in columns) + " WHERE id = :pk"),
            {**columns, "pk": pk})

        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO condition_identifier (condition_pk, system, value, type_system, "
                    "type_code, type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})

        _insert_token(bind, pk, "clinical-status", doc.get("clinicalStatus"))
        _insert_token(bind, pk, "verification-status", doc.get("verificationStatus"))
        _insert_token(bind, pk, "severity", doc.get("severity"))
        _insert_token(bind, pk, "code", doc.get("code"))
        for category in doc.get("category") or []:
            _insert_token(bind, pk, "category", category)
        for body_site in doc.get("bodySite") or []:
            _insert_token(bind, pk, "body-site", body_site)
        for stage in doc.get("stage") or []:
            _insert_token(bind, pk, "stage", stage.get("summary"))
        for evidence in doc.get("evidence") or []:
            for code in evidence.get("code") or []:
                _insert_token(bind, pk, "evidence", code)
            for detail in evidence.get("detail") or []:
                reference = detail.get("reference")
                identifier = detail.get("identifier") or {}
                if not (reference or identifier.get("value")):
                    continue
                match = _REF.match(reference or "")
                bind.execute(sa.text(
                    "INSERT INTO condition_evidence_detail (condition_pk, reference_reference, reference_type, "
                    "reference_id, reference_identifier_system, reference_identifier_value) "
                    "VALUES (:pk, :r, :t, :i, :s, :v)"),
                    {"pk": pk, "r": reference, "t": match["type"] if match else None,
                     "i": int(match["id"]) if match else None, "s": identifier.get("system"),
                     "v": identifier.get("value")})


# Children first (grandchildren before their parents).
_OLD_CHILD_TABLES = (
    "condition_evidence_detail",
    "condition_evidence_code_coding",
    "condition_evidence_code",
    "condition_evidence",
    "condition_stage_assessment",
    "condition_stage_summary_coding",
    "condition_stage_type_coding",
    "condition_stage",
    "condition_body_site_coding",
    "condition_body_site",
    "condition_category_coding",
    "condition_category",
    "condition_note",
    "condition_identifier_type_coding",
    "condition_identifier",
    "condition_clinical_status_coding",
    "condition_verification_status_coding",
    "condition_severity_coding",
    "condition_code_coding",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns and the
# index columns of the three references (the reference-type enums become plain strings).
_KEEP = {
    "id", "condition_id", "tenant_id", "created_by", "updated_by", "created_at", "updated_at", "content",
    *(f"{prefix}_{part}" for prefix in ("subject", "encounter", "asserter")
      for part in ("reference", "type", "id", "identifier_system", "identifier_value")),
}

_OLD_ENUMS = (
    "condition_quantity_comparator",
    "condition_recorder_reference_type",
    "condition_asserter_reference_type",
    "condition_note_author_reference_type",
    "condition_stage_assessment_reference_type",
)


def _fk():
    return sa.Column("condition_pk", sa.BigInteger(), sa.ForeignKey("condition.id"), nullable=False)


def _index(table, *columns):
    op.create_index(op.f("ix_" + table + "_" + columns[0]), table, list(columns))


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('condition', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are
    # rebuilt from it below.
    for table in _OLD_CHILD_TABLES:
        op.drop_table(table)
    existing = [r[0] for r in bind.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'condition' "
        "AND table_schema = current_schema()"))]
    for column in existing:
        if column not in _KEEP:
            op.drop_column('condition', column)

    # Their old single-column indexes go with the (kept) columns' new composite ones.
    op.execute("DROP INDEX IF EXISTS ix_condition_subject_id")
    op.execute("DROP INDEX IF EXISTS ix_condition_asserter_id")
    # `subject` is 1..1 in R4, but nullability is the validator's rule, not the database's.
    op.alter_column('condition', 'subject_reference', nullable=True)
    # The reference types were enums; they are plain strings now (the shared enum types stay).
    for prefix in ('subject', 'encounter', 'asserter'):
        op.alter_column('condition', f'{prefix}_type', type_=sa.String(), nullable=True,
                        postgresql_using=f'{prefix}_type::text')
    for enum in _OLD_ENUMS:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
    # The public id's sequence is now its server default.
    op.execute("ALTER TABLE condition ALTER COLUMN condition_id SET DEFAULT nextval('condition_pub_seq')")

    for column in ('recorded_date_start', 'recorded_date_end'):
        op.add_column('condition', sa.Column(column, sa.DateTime(timezone=True), nullable=True))
    for element in ('onset', 'abatement'):
        op.add_column('condition', sa.Column(f'{element}_date_start', sa.DateTime(timezone=True), nullable=True))
        op.add_column('condition', sa.Column(f'{element}_date_end', sa.DateTime(timezone=True), nullable=True))
        op.add_column('condition', sa.Column(f'{element}_age_low', sa.Numeric(), nullable=True))
        op.add_column('condition', sa.Column(f'{element}_age_high', sa.Numeric(), nullable=True))
        for part in ('system', 'code', 'unit'):
            op.add_column('condition', sa.Column(f'{element}_age_{part}', sa.String(), nullable=True))
        op.add_column('condition', sa.Column(f'{element}_string', sa.String(), nullable=True))
        op.add_column('condition', sa.Column(f'{element}_string_norm', sa.String(), nullable=True))
        op.create_index(f'ix_condition_{element}_date', 'condition', [f'{element}_date_start', f'{element}_date_end'])
    op.create_index('ix_condition_recorded_date', 'condition', ['recorded_date_start', 'recorded_date_end'])
    op.create_index('ix_condition_subject_type_id', 'condition', ['subject_type', 'subject_id'])
    op.create_index('ix_condition_asserter_type_id', 'condition', ['asserter_type', 'asserter_id'])

    op.create_table(
        'condition_identifier',
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
    _index('condition_identifier', 'condition_pk')
    _index('condition_identifier', 'value')

    op.create_table(
        'condition_token',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('param', sa.String(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index('condition_token', 'condition_pk')
    op.create_index('ix_condition_token_param_code', 'condition_token', ['param', 'code'])

    op.create_table(
        'condition_evidence_detail',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_identifier_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_value', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index('condition_evidence_detail', 'condition_pk')
    op.create_index('ix_condition_evidence_detail_type_id', 'condition_evidence_detail',
                    ['reference_type', 'reference_id'])

    _rebuild_index(bind)
    op.create_index('ix_condition_encounter_id', 'condition', ['encounter_id'], if_not_exists=True)
    op.alter_column('condition', 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "condition content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
