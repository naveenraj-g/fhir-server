"""procedure: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: o2f7b4d0e836
Revises: n1e6a3c9d725
Create Date: 2026-12-01 10:00:00.000000

Medplum-style storage for Procedure (see ProcedureModel's docstring), same as the
other resources already moved (Organization 5b1969c2ec19, Location 8c41d2e7a9b3,
Practitioner a7d3f19c2b64, HealthcareService c9f5b2d7e813, Endpoint d1a6c3e8f924,
PractitionerRole e2b7d4f9a035, Schedule f3c8e5a1b947, Slot g4d9f6b2c058, Patient
h5e0a7c3d169, Appointment i6f1b8d4e27a, AppointmentResponse j7a2c9e5f381,
Encounter k8b3d0f6a492, RelatedPerson l9c4e1a7b503, AllergyIntolerance
m0d5f2b8c614, Condition n1e6a3c9d725). The whole FHIR resource moves into
`procedure.content`; every column/table that survives is a search index for one of
the FHIR R4 Procedure search parameters (or `_id` / `_lastUpdated`), derived from
`content`:

  procedure: status (the Postgres enum is recreated, holding the real FHIR codes),
      performed_date_start/_end (performed[x] as a dateTime or Period, the range
      it covers), subject_*, encounter_*, location_* reference columns (`*_type`
      becomes a plain string; `subject_reference` nullable); the public id gets its
      sequence as a server default; new: content
  procedure_identifier: rebuilt as an index table
  procedure_token: new - category, code, reason-code
  procedure_reference: new - based-on, instantiates-canonical, part-of,
      reason-reference
  procedure_performer: rebuilt - one row per performer.actor
  procedure_instantiates_uri: new - one row per instantiatesUri
  dropped: every other old child table (status reason / category / code / outcome
      codings, reason codes, body sites, complications, follow-ups, used codes,
      focal devices, notes, reports, complication details, used references,
      part-of / based-on / reason-reference rows, identifier type codings and the
      old performer table), every main-table column with no search parameter
      (texts, recorder, asserter, performed[x] other than dateTime / Period, the
      instantiates arrays, extension and the display / logical-identifier details
      of every reference) and every `procedure_*` enum (`procedure_status` is
      recreated with the real FHIR codes and every row's status is carried over).

upgrade: (1) builds `content` for every existing row from the old columns and
tables - a frozen copy of the old to_fhir_procedure() logic (but keeping a
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
revision: str = 'o2f7b4d0e836'
down_revision: Union[str, None] = 'n1e6a3c9d725'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUS = ('preparation', 'in-progress', 'not-done', 'on-hold', 'stopped', 'completed', 'entered-in-error', 'unknown')


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
    """The FHIR code for an old status label (a member name such as `in_progress`
    becomes `in-progress`; a real code passes through unchanged)."""
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


def _codings(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


def _concepts(bind, table, coding_table, coding_fk, pk):
    """A 0..* CodeableConcept held as `table` (text) + `coding_table` (codings)."""
    return [
        _concept(_codings(bind, coding_table, coding_fk, c["id"]), c["text"])
        for c in _codings(bind, table, "procedure_pk", pk)
    ]


def _references(bind, table, pk):
    return [_old_reference(x, "reference") for x in _codings(bind, table, "procedure_pk", pk)]


def _annotation(n):
    """A note's author has no logical-identifier columns in the old schema, only
    the raw reference, its type / id and a display."""
    raw = n["author_reference_reference"]
    if not raw and n["author_reference_type"] and n["author_reference_id"]:
        raw = f"{n['author_reference_type']}/{n['author_reference_id']}"
    author = {"reference": raw, "display": n["author_reference_display"]}
    return {
        "authorReference": author if raw else None,
        "authorString": None if raw else n["author_string"],
        "time": _iso(n["time"]),
        "text": n["text"],
    }


def _build_content(bind, r):
    pk = r["id"]
    identifiers = []
    for i in _rows(bind, "SELECT * FROM procedure_identifier WHERE procedure_pk = :pk ORDER BY id", pk=pk):
        identifiers.append({
            "use": i["use"],
            "type": _concept(_codings(bind, "procedure_identifier_type_coding", "identifier_id", i["id"]), i["type_text"]),
            "system": i["system"], "value": i["value"],
            "period": _period(i["period_start"], i["period_end"]),
            "assigner": _old_reference(i, "assigner"),
        })

    def single(table, text):
        return _concept(_codings(bind, table, "procedure_pk", pk), text)

    performers = []
    for p in _rows(bind, "SELECT * FROM procedure_performer WHERE procedure_pk = :pk ORDER BY id", pk=pk):
        performers.append({
            "function": _concept(_codings(bind, "procedure_performer_function_coding", "performer_id", p["id"]),
                                 p["function_text"]),
            "actor": _old_reference(p, "actor"),
            "onBehalfOf": _old_reference(p, "on_behalf_of"),
        })
    focal_devices = []
    for d in _rows(bind, "SELECT * FROM procedure_focal_device WHERE procedure_pk = :pk ORDER BY id", pk=pk):
        focal_devices.append({
            "action": _concept(_codings(bind, "procedure_focal_device_action_coding", "focal_device_id", d["id"]),
                               d["action_text"]),
            "manipulated": _old_reference(d, "manipulated"),
        })
    notes = [_annotation(n) for n in _codings(bind, "procedure_note", "procedure_pk", pk)]

    performed = {}
    if r["performed_date_time"]:
        performed["performedDateTime"] = _iso(r["performed_date_time"])
    elif r["performed_period_start"] or r["performed_period_end"]:
        performed["performedPeriod"] = _period(r["performed_period_start"], r["performed_period_end"])
    elif r["performed_string"]:
        performed["performedString"] = r["performed_string"]
    elif r["performed_age"]:
        performed["performedAge"] = _json(r["performed_age"])
    elif r["performed_range"]:
        performed["performedRange"] = _json(r["performed_range"])

    return _prune({
        "extension": list(_json(r["extension"]) or []),
        "identifier": identifiers,
        "instantiatesCanonical": list(r["instantiates_canonical"] or []),
        "instantiatesUri": list(r["instantiates_uri"] or []),
        "basedOn": _references(bind, "procedure_based_on", pk),
        "partOf": _references(bind, "procedure_part_of", pk),
        "status": _hyphenate(r["status_text"]),
        "statusReason": single("procedure_status_reason_coding", r["status_reason_text"]),
        "category": single("procedure_category_coding", r["category_text"]),
        "code": single("procedure_code_coding", r["code_text"]),
        "subject": _old_reference(r, "subject"),
        "encounter": _old_reference(r, "encounter"),
        **performed,
        "recorder": _old_reference(r, "recorder"),
        "asserter": _old_reference(r, "asserter"),
        "performer": performers,
        "location": _old_reference(r, "location"),
        "reasonCode": _concepts(bind, "procedure_reason_code", "procedure_reason_code_coding", "reason_code_id", pk),
        "reasonReference": _references(bind, "procedure_reason_reference", pk),
        "bodySite": _concepts(bind, "procedure_body_site", "procedure_body_site_coding", "body_site_id", pk),
        "outcome": single("procedure_outcome_coding", r["outcome_text"]),
        "report": _references(bind, "procedure_report", pk),
        "complication": _concepts(bind, "procedure_complication", "procedure_complication_coding", "complication_id", pk),
        "complicationDetail": _references(bind, "procedure_complication_detail", pk),
        "followUp": _concepts(bind, "procedure_follow_up", "procedure_follow_up_coding", "follow_up_id", pk),
        "note": notes,
        "focalDevice": focal_devices,
        "usedReference": _references(bind, "procedure_used_reference", pk),
        "usedCode": _concepts(bind, "procedure_used_code", "procedure_used_code_coding", "used_code_id", pk),
    })


def _backfill_content(bind):
    # `status` is an enum: cast it to text so the driver returns the label.
    for r in _rows(bind, "SELECT *, status::text AS status_text FROM procedure"):
        bind.execute(
            sa.text("UPDATE procedure SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, r)), "id": r["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_SUBJECT_TYPES = ("Patient", "Group")
_REFERENCE_TYPES = {
    "based-on": ("CarePlan", "ServiceRequest"),
    "instantiates-canonical": ("ActivityDefinition", "Measure", "OperationDefinition", "PlanDefinition", "Questionnaire"),
    "part-of": ("MedicationAdministration", "Observation", "Procedure"),
    "reason-reference": ("Condition", "DiagnosticReport", "DocumentReference", "Observation", "Procedure"),
}
_PERFORMER_TYPES = ("Practitioner", "PractitionerRole", "Organization", "Patient", "RelatedPerson", "Device")


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
            "INSERT INTO procedure_token (procedure_pk, param, system, code, display_norm, text_norm) "
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
        "INSERT INTO procedure_reference (procedure_pk, param, reference_reference, reference_type, reference_id, "
        "reference_identifier_system, reference_identifier_value) VALUES (:pk, :p, :r, :t, :i, :s, :v)"),
        {"pk": pk, "p": param, "r": reference, "t": rtype, "i": rid, "s": identifier.get("system"),
         "v": identifier.get("value")})


def _rebuild_index(bind):
    for row in _rows(bind, "SELECT id, content FROM procedure"):
        pk, doc = row["id"], _json(row["content"])

        if doc.get("performedDateTime"):
            start, end = _bounds(doc["performedDateTime"])
        else:
            start, end = _period_bounds(doc.get("performedPeriod"))
        status = doc.get("status")
        columns = {
            "performed_date_start": start, "performed_date_end": end,
            **_ref_params("subject", doc.get("subject"), _SUBJECT_TYPES),
            **_ref_params("encounter", doc.get("encounter"), ("Encounter",)),
            **_ref_params("location", doc.get("location"), ("Location",)),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(f"UPDATE procedure SET status = CAST(:status AS procedure_status), {sets} WHERE id = :pk"),
            {**columns, "status": status if status in _STATUS else None, "pk": pk})

        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO procedure_identifier (procedure_pk, system, value, type_system, "
                    "type_code, type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})

        _insert_token(bind, pk, "category", doc.get("category"))
        _insert_token(bind, pk, "code", doc.get("code"))
        for reason in doc.get("reasonCode") or []:
            _insert_token(bind, pk, "reason-code", reason)
        for ref in doc.get("basedOn") or []:
            _insert_reference(bind, pk, "based-on", ref)
        for ref in doc.get("partOf") or []:
            _insert_reference(bind, pk, "part-of", ref)
        for ref in doc.get("reasonReference") or []:
            _insert_reference(bind, pk, "reason-reference", ref)
        for canonical in doc.get("instantiatesCanonical") or []:
            _insert_reference(bind, pk, "instantiates-canonical", {"reference": canonical})
        for uri in doc.get("instantiatesUri") or []:
            if uri:
                bind.execute(sa.text("INSERT INTO procedure_instantiates_uri (procedure_pk, uri) VALUES (:pk, :u)"),
                             {"pk": pk, "u": uri})
        for performer in doc.get("performer") or []:
            actor = performer.get("actor") or {}
            reference = actor.get("reference")
            identifier = actor.get("identifier") or {}
            if not (reference or identifier.get("value")):
                continue
            rtype, rid = _typed(reference, _PERFORMER_TYPES)
            bind.execute(sa.text(
                "INSERT INTO procedure_performer (procedure_pk, reference_reference, reference_type, reference_id, "
                "reference_identifier_system, reference_identifier_value) VALUES (:pk, :r, :t, :i, :s, :v)"),
                {"pk": pk, "r": reference, "t": rtype, "i": rid, "s": identifier.get("system"),
                 "v": identifier.get("value")})


# Children first (grandchildren before their parents).
_OLD_CHILD_TABLES = (
    "procedure_reason_code_coding", "procedure_reason_code",
    "procedure_body_site_coding", "procedure_body_site",
    "procedure_complication_coding", "procedure_complication",
    "procedure_follow_up_coding", "procedure_follow_up",
    "procedure_used_code_coding", "procedure_used_code",
    "procedure_focal_device_action_coding", "procedure_focal_device",
    "procedure_performer_function_coding", "procedure_performer",
    "procedure_identifier_type_coding", "procedure_identifier",
    "procedure_note", "procedure_based_on", "procedure_part_of", "procedure_reason_reference",
    "procedure_report", "procedure_complication_detail", "procedure_used_reference",
    "procedure_status_reason_coding", "procedure_category_coding", "procedure_code_coding",
    "procedure_outcome_coding",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns and the
# index columns of the three references (the reference-type enums become plain strings).
_KEEP = {
    "id", "procedure_id", "tenant_id", "created_by", "updated_by", "created_at", "updated_at", "content",
    *(f"{prefix}_{part}" for prefix in ("subject", "encounter", "location")
      for part in ("reference", "type", "id", "identifier_system", "identifier_value")),
}


def _fk():
    return sa.Column("procedure_pk", sa.BigInteger(), sa.ForeignKey("procedure.id"), nullable=False)


def _index(table, *columns):
    op.create_index(op.f("ix_" + table + "_" + columns[0]), table, list(columns))


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('procedure', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are
    # rebuilt from it below.
    for table in _OLD_CHILD_TABLES:
        op.drop_table(table)
    existing = [r[0] for r in bind.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'procedure' "
        "AND table_schema = current_schema()"))]
    for column in existing:
        if column not in _KEEP:
            op.drop_column('procedure', column)

    # Their old single-column index goes with the new composite one.
    op.execute("DROP INDEX IF EXISTS ix_procedure_subject_id")
    # `subject` is 1..1 in R4, but nullability is the validator's rule, not the database's.
    op.alter_column('procedure', 'subject_reference', nullable=True)
    # The reference types were enums; they are plain strings now.
    for prefix in ('subject', 'encounter', 'location'):
        op.alter_column('procedure', f'{prefix}_type', type_=sa.String(), nullable=True,
                        postgresql_using=f'{prefix}_type::text')
    # Every procedure_* enum was only used by the old tables (status is recreated below).
    for (name,) in bind.execute(sa.text(
            "SELECT typname FROM pg_type WHERE typtype = 'e' AND typname LIKE 'procedure\\_%'")).all():
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # The public id's sequence is now its server default.
    op.execute("ALTER TABLE procedure ALTER COLUMN procedure_id SET DEFAULT nextval('procedure_pub_seq')")

    # status: recreated as an enum holding the real FHIR codes.
    postgresql.ENUM(*_STATUS, name='procedure_status').create(bind, checkfirst=True)
    op.add_column('procedure', sa.Column(
        'status', postgresql.ENUM(*_STATUS, name='procedure_status', create_type=False), nullable=True))
    op.add_column('procedure', sa.Column('performed_date_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('procedure', sa.Column('performed_date_end', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_procedure_performed_date', 'procedure', ['performed_date_start', 'performed_date_end'])
    op.create_index('ix_procedure_subject_type_id', 'procedure', ['subject_type', 'subject_id'])

    op.create_table(
        'procedure_identifier',
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
    _index('procedure_identifier', 'procedure_pk')
    _index('procedure_identifier', 'value')

    op.create_table(
        'procedure_token',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('param', sa.String(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index('procedure_token', 'procedure_pk')
    op.create_index('ix_procedure_token_param_code', 'procedure_token', ['param', 'code'])

    op.create_table(
        'procedure_reference',
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
    _index('procedure_reference', 'procedure_pk')
    op.create_index('ix_procedure_reference_param_type_id', 'procedure_reference',
                    ['param', 'reference_type', 'reference_id'])

    op.create_table(
        'procedure_performer',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_identifier_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_value', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index('procedure_performer', 'procedure_pk')
    op.create_index('ix_procedure_performer_type_id', 'procedure_performer', ['reference_type', 'reference_id'])

    op.create_table(
        'procedure_instantiates_uri',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('uri', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    _index('procedure_instantiates_uri', 'procedure_pk')
    _index('procedure_instantiates_uri', 'uri')

    _rebuild_index(bind)
    op.create_index('ix_procedure_encounter_id', 'procedure', ['encounter_id'], if_not_exists=True)
    op.create_index('ix_procedure_location_id', 'procedure', ['location_id'], if_not_exists=True)
    op.alter_column('procedure', 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "procedure content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
