"""detected_issue: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: w0b5d2f8a614
Revises: v9a4c1e7f503
Create Date: 2026-12-09 10:00:00.000000

Medplum-style storage for DetectedIssue (see DetectedIssueModel's docstring), same as the other
resources already moved (Organization 5b1969c2ec19, Location 8c41d2e7a9b3, Practitioner
a7d3f19c2b64, HealthcareService c9f5b2d7e813, Endpoint d1a6c3e8f924, PractitionerRole
e2b7d4f9a035, Schedule f3c8e5a1b947, Slot g4d9f6b2c058, Patient h5e0a7c3d169, Appointment
i6f1b8d4e27a, AppointmentResponse j7a2c9e5f381, Encounter k8b3d0f6a492, RelatedPerson
l9c4e1a7b503, AllergyIntolerance m0d5f2b8c614, Condition n1e6a3c9d725, Procedure
o2f7b4d0e836, DiagnosticReport p3a8c5e1f947, Immunization q4b9d6f2a058,
ImmunizationRecommendation r5c0e7a3b169, ImmunizationEvaluation s6d1f8b4c270,
FamilyMemberHistory t7e2a9c5d381, RiskAssessment u8f3b0d6e492, ClinicalImpression
v9a4c1e7f503). The whole FHIR resource moves into `detected_issue.content`; every column/table
that survives is a search index for one of the FHIR R4 DetectedIssue search parameters (or `_id`
/ `_lastUpdated`), derived from `content`:

  detected_issue: identified_start/_end (`identified[x]`, a dateTime or a Period, the range it
      covers) and the patient_* and author_* reference columns (`*_type` becomes a plain
      string); the public id gets its sequence as a server default; new: content. R4 defines no
      `status` / `severity` search parameter for this resource, so those columns and the
      `detected_issue_status` / `detected_issue_severity` enums go (the values are kept in
      `content`).
  detected_issue_identifier: rebuilt as an index table
  detected_issue_token: new - code
  detected_issue_reference: new - implicated (Reference(Any))
  dropped: every old child table (identifier coding, code coding, implicated, evidence + its
      codes, code codings and details, mitigation + its action codings), every main-table column
      with no search parameter (status, severity, code text, detail, reference, extension and
      the display / logical-identifier details of every reference) and the three per-field
      `detected_issue_*_reference_type` enums.

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_detected_issue() logic (but keeping a reference's raw string, so an
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
revision: str = 'w0b5d2f8a614'
down_revision: Union[str, None] = 'v9a4c1e7f503'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "detected_issue"


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
    """(start, end) of a Period: the first instant it covers and the first instant after it (None =
    open on that side). Frozen copy of app.repository._content_index.period_bounds."""
    period = period or {}
    start = _bounds(period.get("start"))[0] if period.get("start") else None
    end = _bounds(period.get("end"))[1] if period.get("end") else None
    return start, end


# ── upgrade: old columns/tables -> content (frozen copy of the old mapper) ───

# The reference-type enums hold FHIR type names or their member names; map either to the FHIR
# type name when building a reference from a resolved type + id.
_TYPE_NAMES = {t.upper(): t for t in (
    "Patient", "Practitioner", "PractitionerRole", "Device", "RelatedPerson", "Organization", "Condition",
    "Encounter", "DiagnosticReport", "MedicationRequest", "Observation")}


def _coding(c):
    return {"system": c["system"], "version": c["version"], "code": c["code"],
            "display": c["display"], "userSelected": c["user_selected"]}


def _concept(codings, text):
    return {"coding": [_coding(c) for c in codings], "text": text}


def _fallback_identifier(row, prefix):
    return {
        "use": row[f"{prefix}_use"],
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


def _ref(row, prefix):
    """A Reference from the old `{prefix}_reference/_type/_id/_display/_identifier_*` columns."""
    raw = row[f"{prefix}_reference"]
    if not raw and row[f"{prefix}_type"] and row[f"{prefix}_id"]:
        ref_type = str(row[f"{prefix}_type"])
        raw = f"{_TYPE_NAMES.get(ref_type.upper(), ref_type)}/{row[f'{prefix}_id']}"
    return {"reference": raw, "display": row[f"{prefix}_display"],
            "identifier": _fallback_identifier(row, f"{prefix}_identifier")}


def _rows_of(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


def _evidence(bind, e):
    return {
        "code": [
            _concept(_rows_of(bind, f"{P}_evidence_code_coding", f"{P}_evidence_code_id", c["id"]), c["text"])
            for c in _rows_of(bind, f"{P}_evidence_code", f"{P}_evidence_id", e["id"])
        ],
        "detail": [_ref(d, "detail") for d in _rows_of(bind, f"{P}_evidence_detail", f"{P}_evidence_id", e["id"])],
    }


def _mitigation(bind, m):
    return {
        "action": _concept(_rows_of(bind, f"{P}_mitigation_action_coding", f"{P}_mitigation_id", m["id"]),
                           m["action_text"]),
        "date": _iso(m["date"]),
        "author": _ref(m, "author"),
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
            "assigner": _ref(i, "assigner"),
        })
    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": identifiers,
        "status": r["status_text"],
        "code": _concept(_rows_of(bind, f"{P}_code_coding", f"{P}_pk", pk), r["code_text"]),
        "severity": r["severity_text"],
        "patient": _ref(r, "patient"),
        "author": _ref(r, "author"),
        "implicated": [_ref(x, "implicated") for x in _rows_of(bind, f"{P}_implicated", f"{P}_pk", pk)],
        "evidence": [_evidence(bind, e) for e in _rows_of(bind, f"{P}_evidence", f"{P}_pk", pk)],
        "detail": r["detail"],
        "reference": r["reference"],
        "mitigation": [_mitigation(bind, m) for m in _rows_of(bind, f"{P}_mitigation", f"{P}_pk", pk)],
    }
    if r["identified_date_time"]:
        content["identifiedDateTime"] = _iso(r["identified_date_time"])
    elif r["identified_period_start"] or r["identified_period_end"]:
        content["identifiedPeriod"] = _period(r["identified_period_start"], r["identified_period_end"])
    return _prune(content)


def _backfill_content(bind):
    # `status` / `severity` are enums: cast them to text so the driver returns the label.
    for r in _rows(bind, f"SELECT *, status::text AS status_text, severity::text AS severity_text FROM {P}"):
        bind.execute(
            sa.text(f"UPDATE {P} SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, dict(r)), default=str), "id": r["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_AUTHOR_TYPES = ("Practitioner", "PractitionerRole", "Device")


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


def _insert_reference(bind, pk, param, ref):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return
    rtype, rid = _typed(reference, None)
    bind.execute(sa.text(
        f"INSERT INTO {P}_reference ({P}_pk, param, reference_reference, reference_type, reference_id, "
        "reference_identifier_system, reference_identifier_value) VALUES (:pk, :param, :r, :t, :i, :s, :v)"),
        {"pk": pk, "param": param, "r": reference, "t": rtype, "i": rid, "s": identifier.get("system"),
         "v": identifier.get("value")})


def _rebuild_index(bind):
    for row in _rows(bind, f"SELECT id, content FROM {P}"):
        pk, doc = row["id"], _json(row["content"])

        if doc.get("identifiedDateTime"):
            start, end = _bounds(doc["identifiedDateTime"])
        else:
            start, end = _period_bounds(doc.get("identifiedPeriod"))
        columns = {
            "identified_start": start, "identified_end": end,
            **_ref_params("patient", doc.get("patient"), ("Patient",)),
            **_ref_params("author", doc.get("author"), _AUTHOR_TYPES),
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

        _insert_token(bind, pk, "code", doc.get("code"))
        for ref in doc.get("implicated") or []:
            _insert_reference(bind, pk, "implicated", ref)


# The per-field enums of the old schema (the status and severity enums go too: neither has a
# search parameter).
_OLD_ENUMS = (
    f"{P}_status", f"{P}_severity", f"{P}_patient_reference_type", f"{P}_author_reference_type",
    f"{P}_mitigation_author_reference_type",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns and the index
# columns of the two kept references (their reference-type enums become plain strings).
_KEEP = {
    "id", "detected_issue_id", "tenant_id", "created_by", "updated_by", "created_at", "updated_at", "content",
    *(f"{prefix}_{part}" for prefix in ("patient", "author")
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
    # below. The new index tables do not exist yet, so every `detected_issue_*` table is old.
    old_tables = [r[0] for r in bind.execute(sa.text(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema() "
        "AND table_name LIKE 'detected\\_issue\\_%'"))]
    for table in old_tables:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
    existing = [r[0] for r in bind.execute(sa.text(
        f"SELECT column_name FROM information_schema.columns WHERE table_name = '{P}' "
        "AND table_schema = current_schema()"))]
    for column in existing:
        if column not in _KEEP:
            op.drop_column(P, column)

    # The reference types were enums; they are plain strings now.
    for prefix in ('patient', 'author'):
        op.alter_column(P, f'{prefix}_type', type_=sa.String(), nullable=True, postgresql_using=f'{prefix}_type::text')
    for name in _OLD_ENUMS:
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # The public id's sequence is now its server default.
    op.execute(f"ALTER TABLE {P} ALTER COLUMN detected_issue_id SET DEFAULT nextval('detected_issue_pub_seq')")

    op.add_column(P, sa.Column('identified_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column(P, sa.Column('identified_end', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_detected_issue_identified', P, ['identified_start', 'identified_end'])

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
    op.create_index('ix_detected_issue_token_param_code', f'{P}_token', ['param', 'code'])

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
    op.create_index('ix_detected_issue_reference_param_type_id', f'{P}_reference',
                    ['param', 'reference_type', 'reference_id'])

    _rebuild_index(bind)
    for column in ('id', 'patient_id', 'author_id'):
        op.create_index(f'ix_{P}_{column}', P, [column], if_not_exists=True)
    op.alter_column(P, 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "detected_issue content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
