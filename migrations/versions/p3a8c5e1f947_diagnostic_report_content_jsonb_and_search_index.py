"""diagnostic_report: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: p3a8c5e1f947
Revises: o2f7b4d0e836
Create Date: 2026-12-02 10:00:00.000000

Medplum-style storage for DiagnosticReport (see DiagnosticReportModel's docstring),
same as the other resources already moved (Organization 5b1969c2ec19, Location
8c41d2e7a9b3, Practitioner a7d3f19c2b64, HealthcareService c9f5b2d7e813, Endpoint
d1a6c3e8f924, PractitionerRole e2b7d4f9a035, Schedule f3c8e5a1b947, Slot
g4d9f6b2c058, Patient h5e0a7c3d169, Appointment i6f1b8d4e27a, AppointmentResponse
j7a2c9e5f381, Encounter k8b3d0f6a492, RelatedPerson l9c4e1a7b503,
AllergyIntolerance m0d5f2b8c614, Condition n1e6a3c9d725, Procedure o2f7b4d0e836).
The whole FHIR resource moves into `diagnostic_report.content`; every column/table
that survives is a search index for one of the FHIR R4 DiagnosticReport search
parameters (or `_id` / `_lastUpdated`), derived from `content`:

  diagnostic_report: status (the Postgres enum is recreated with the real FHIR
      codes - `entered-in-error`, where the old one had `entered_in_error`),
      effective_date_start/_end (effective[x] as a dateTime or Period, the range it
      covers), issued (kept, now indexed), subject_*, encounter_* reference columns
      (`*_type` becomes a plain string); the public id gets its sequence as a
      server default; new: content
  diagnostic_report_identifier: rebuilt as an index table
  diagnostic_report_token: new - category, code, conclusion
  diagnostic_report_reference: new - based-on, media, result, specimen
  diagnostic_report_performer: rebuilt - performer and results-interpreter, told
      apart by `param`
  dropped: every old child table (category / code / conclusion code codings,
      identifier type codings, based-on, specimen, result, imaging study, media,
      performer, results interpreter and presented form tables), every main-table
      column with no search parameter (code text, conclusion, extension and the
      display / logical-identifier details of every reference) and every
      `diagnostic_report_*` enum.

upgrade: (1) builds `content` for every existing row from the old columns and
tables - a frozen copy of the old to_fhir_diagnostic_report() logic (but keeping a
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
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'p3a8c5e1f947'
down_revision: Union[str, None] = 'o2f7b4d0e836'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUS = ('registered', 'partial', 'preliminary', 'final', 'amended', 'corrected', 'appended', 'cancelled',
           'entered-in-error', 'unknown')


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
    """The FHIR code for an old status label (`entered_in_error` becomes
    `entered-in-error`; a real code passes through unchanged)."""
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


def _period_bounds(period):
    """(start, end) of a Period: the first instant of `start`, the first instant
    after `end` (frozen copy of app.repository._content_index.period_bounds)."""
    period = period or {}
    start = _bounds(period.get("start"))[0] if period.get("start") else None
    end = _bounds(period.get("end"))[1] if period.get("end") else None
    return start, end


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


def _references(bind, table, pk):
    return [_old_reference(x, "reference") for x in _rows_of(bind, table, "diagnostic_report_pk", pk)]


def _attachment(p):
    """A presentedForm row (frozen copy of the old fhir_photo())."""
    return {
        "contentType": p["content_type"], "language": p["language"], "data": p["data"], "url": p["url"],
        "size": p["size"], "hash": p["hash"], "title": p["title"], "creation": _iso(p["creation"]),
    }


def _build_content(bind, r):
    pk = r["id"]
    identifiers = []
    for i in _rows_of(bind, "diagnostic_report_identifier", "diagnostic_report_pk", pk):
        identifiers.append({
            "use": i["use"],
            "type": _concept(
                _rows_of(bind, "diagnostic_report_identifier_type_coding", "diagnostic_report_identifier_id", i["id"]),
                i["type_text"]),
            "system": i["system"], "value": i["value"],
            "period": _period(i["period_start"], i["period_end"]),
            "assigner": _old_reference(i, "assigner"),
        })
    categories = [
        _concept(_rows_of(bind, "diagnostic_report_category_coding", "diagnostic_report_category_id", c["id"]), c["text"])
        for c in _rows_of(bind, "diagnostic_report_category", "diagnostic_report_pk", pk)
    ]
    conclusion_codes = [
        _concept(
            _rows_of(bind, "diagnostic_report_conclusion_code_coding", "diagnostic_report_conclusion_code_id", c["id"]),
            c["text"])
        for c in _rows_of(bind, "diagnostic_report_conclusion_code", "diagnostic_report_pk", pk)
    ]
    media = [
        {"comment": m["comment"], "link": _old_reference(m, "link")}
        for m in _rows_of(bind, "diagnostic_report_media", "diagnostic_report_pk", pk)
    ]
    code = _concept(_rows_of(bind, "diagnostic_report_code_coding", "diagnostic_report_pk", pk), r["code_text"])
    effective = {}
    if r["effective_date_time"]:
        effective["effectiveDateTime"] = _iso(r["effective_date_time"])
    elif r["effective_period_start"] or r["effective_period_end"]:
        effective["effectivePeriod"] = _period(r["effective_period_start"], r["effective_period_end"])

    return _prune({
        "extension": list(_json(r["extension"]) or []),
        "identifier": identifiers,
        "basedOn": _references(bind, "diagnostic_report_based_on", pk),
        "status": _hyphenate(r["status_text"]),
        "category": categories,
        "code": code,
        "subject": _old_reference(r, "subject"),
        "encounter": _old_reference(r, "encounter"),
        **effective,
        "issued": _iso(r["issued"]),
        "performer": _references(bind, "diagnostic_report_performer", pk),
        "resultsInterpreter": _references(bind, "diagnostic_report_results_interpreter", pk),
        "specimen": _references(bind, "diagnostic_report_specimen", pk),
        "result": _references(bind, "diagnostic_report_result", pk),
        "imagingStudy": _references(bind, "diagnostic_report_imaging_study", pk),
        "media": media,
        "conclusion": r["conclusion"],
        "conclusionCode": conclusion_codes,
        "presentedForm": [_attachment(p) for p in _rows_of(bind, "diagnostic_report_presented_form",
                                                           "diagnostic_report_pk", pk)],
    })


def _backfill_content(bind):
    # `status` is an enum: cast it to text so the driver returns the label.
    for r in _rows(bind, "SELECT *, status::text AS status_text FROM diagnostic_report"):
        bind.execute(
            sa.text("UPDATE diagnostic_report SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, r)), "id": r["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_SUBJECT_TYPES = ("Patient", "Group", "Device", "Location")
_PERFORMER_TYPES = ("Practitioner", "PractitionerRole", "Organization", "CareTeam")
_REFERENCE_TYPES = {
    "based-on": ("CarePlan", "ImmunizationRecommendation", "MedicationRequest", "NutritionOrder", "ServiceRequest"),
    "media": ("Media",),
    "result": ("Observation",),
    "specimen": ("Specimen",),
}


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
            "INSERT INTO diagnostic_report_token (diagnostic_report_pk, param, system, code, display_norm, text_norm) "
            "VALUES (:pk, :param, :s, :c, :d, :t)"),
            {"pk": pk, "param": param, "s": c.get("system"), "c": c.get("code"), "d": _norm(c.get("display")),
             "t": text})


def _insert_reference(bind, pk, param, ref):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return
    rtype, rid = _typed(reference, _REFERENCE_TYPES[param])
    bind.execute(sa.text(
        "INSERT INTO diagnostic_report_reference (diagnostic_report_pk, param, reference_reference, reference_type, "
        "reference_id, reference_identifier_system, reference_identifier_value) VALUES (:pk, :p, :r, :t, :i, :s, :v)"),
        {"pk": pk, "p": param, "r": reference, "t": rtype, "i": rid, "s": identifier.get("system"),
         "v": identifier.get("value")})


def _rebuild_index(bind):
    for row in _rows(bind, "SELECT id, content FROM diagnostic_report"):
        pk, doc = row["id"], _json(row["content"])

        if doc.get("effectiveDateTime"):
            start, end = _bounds(doc["effectiveDateTime"])
        else:
            start, end = _period_bounds(doc.get("effectivePeriod"))
        status = doc.get("status")
        columns = {
            "effective_date_start": start, "effective_date_end": end, "issued": _bounds(doc.get("issued"))[0],
            **_ref_params("subject", doc.get("subject"), _SUBJECT_TYPES),
            **_ref_params("encounter", doc.get("encounter"), ("Encounter",)),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(f"UPDATE diagnostic_report SET status = CAST(:status AS diagnostic_report_status), {sets} "
                    "WHERE id = :pk"),
            {**columns, "status": status if status in _STATUS else None, "pk": pk})

        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO diagnostic_report_identifier (diagnostic_report_pk, system, value, type_system, "
                    "type_code, type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})

        for category in doc.get("category") or []:
            _insert_token(bind, pk, "category", category)
        _insert_token(bind, pk, "code", doc.get("code"))
        for conclusion in doc.get("conclusionCode") or []:
            _insert_token(bind, pk, "conclusion", conclusion)
        for ref in doc.get("basedOn") or []:
            _insert_reference(bind, pk, "based-on", ref)
        for media in doc.get("media") or []:
            _insert_reference(bind, pk, "media", (media or {}).get("link"))
        for ref in doc.get("result") or []:
            _insert_reference(bind, pk, "result", ref)
        for ref in doc.get("specimen") or []:
            _insert_reference(bind, pk, "specimen", ref)
        for param, element in (("performer", "performer"), ("results-interpreter", "resultsInterpreter")):
            for ref in doc.get(element) or []:
                reference = (ref or {}).get("reference")
                identifier = (ref or {}).get("identifier") or {}
                if not (reference or identifier.get("value")):
                    continue
                rtype, rid = _typed(reference, _PERFORMER_TYPES)
                bind.execute(sa.text(
                    "INSERT INTO diagnostic_report_performer (diagnostic_report_pk, param, reference_reference, "
                    "reference_type, reference_id, reference_identifier_system, reference_identifier_value) "
                    "VALUES (:pk, :p, :r, :t, :i, :s, :v)"),
                    {"pk": pk, "p": param, "r": reference, "t": rtype, "i": rid, "s": identifier.get("system"),
                     "v": identifier.get("value")})


# Children first (grandchildren before their parents).
_OLD_CHILD_TABLES = (
    "diagnostic_report_category_coding", "diagnostic_report_category",
    "diagnostic_report_conclusion_code_coding", "diagnostic_report_conclusion_code",
    "diagnostic_report_identifier_type_coding", "diagnostic_report_identifier",
    "diagnostic_report_code_coding", "diagnostic_report_based_on", "diagnostic_report_specimen",
    "diagnostic_report_result", "diagnostic_report_imaging_study", "diagnostic_report_media",
    "diagnostic_report_performer", "diagnostic_report_results_interpreter", "diagnostic_report_presented_form",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns, `issued` and
# the index columns of the two references (the reference-type enums become plain strings).
_KEEP = {
    "id", "diagnostic_report_id", "tenant_id", "created_by", "updated_by", "created_at", "updated_at", "content",
    "issued",
    *(f"{prefix}_{part}" for prefix in ("subject", "encounter")
      for part in ("reference", "type", "id", "identifier_system", "identifier_value")),
}


def _fk():
    return sa.Column("diagnostic_report_pk", sa.BigInteger(), sa.ForeignKey("diagnostic_report.id"), nullable=False)


def _index(table, *columns):
    op.create_index(op.f("ix_" + table + "_" + columns[0]), table, list(columns))


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('diagnostic_report', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are
    # rebuilt from it below.
    for table in _OLD_CHILD_TABLES:
        op.drop_table(table)
    existing = [r[0] for r in bind.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'diagnostic_report' "
        "AND table_schema = current_schema()"))]
    for column in existing:
        if column not in _KEEP:
            op.drop_column('diagnostic_report', column)

    # Their old single-column index goes with the new composite one.
    op.execute("DROP INDEX IF EXISTS ix_diagnostic_report_subject_id")
    # The reference types were enums; they are plain strings now.
    for prefix in ('subject', 'encounter'):
        op.alter_column('diagnostic_report', f'{prefix}_type', type_=sa.String(), nullable=True,
                        postgresql_using=f'{prefix}_type::text')
    # Every diagnostic_report_* enum was only used by the old tables (status is recreated below).
    for (name,) in bind.execute(sa.text(
            "SELECT typname FROM pg_type WHERE typtype = 'e' AND typname LIKE 'diagnostic\\_report\\_%'")).all():
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # The public id's sequence is now its server default.
    op.execute("ALTER TABLE diagnostic_report ALTER COLUMN diagnostic_report_id "
               "SET DEFAULT nextval('diagnostic_report_pub_seq')")

    # status: recreated as an enum holding the real FHIR codes.
    postgresql.ENUM(*_STATUS, name='diagnostic_report_status').create(bind, checkfirst=True)
    op.add_column('diagnostic_report', sa.Column(
        'status', postgresql.ENUM(*_STATUS, name='diagnostic_report_status', create_type=False), nullable=True))
    op.add_column('diagnostic_report', sa.Column('effective_date_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('diagnostic_report', sa.Column('effective_date_end', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_diagnostic_report_effective_date', 'diagnostic_report',
                    ['effective_date_start', 'effective_date_end'])
    op.create_index('ix_diagnostic_report_subject_type_id', 'diagnostic_report', ['subject_type', 'subject_id'])

    op.create_table(
        'diagnostic_report_identifier',
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
    _index('diagnostic_report_identifier', 'diagnostic_report_pk')
    _index('diagnostic_report_identifier', 'value')

    op.create_table(
        'diagnostic_report_token',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('param', sa.String(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index('diagnostic_report_token', 'diagnostic_report_pk')
    op.create_index('ix_diagnostic_report_token_param_code', 'diagnostic_report_token', ['param', 'code'])

    for table, index in (('diagnostic_report_reference', 'ix_diagnostic_report_reference_param_type_id'),
                         ('diagnostic_report_performer', 'ix_diagnostic_report_performer_param_type_id')):
        op.create_table(
            table,
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
        _index(table, 'diagnostic_report_pk')
        op.create_index(index, table, ['param', 'reference_type', 'reference_id'])

    _rebuild_index(bind)
    op.create_index('ix_diagnostic_report_issued', 'diagnostic_report', ['issued'], if_not_exists=True)
    op.create_index('ix_diagnostic_report_encounter_id', 'diagnostic_report', ['encounter_id'], if_not_exists=True)
    op.alter_column('diagnostic_report', 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "diagnostic_report content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
