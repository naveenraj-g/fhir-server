"""specimen: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: y2d7f4b0c816
Revises: x1c6e3a9b705
Create Date: 2026-12-11 10:00:00.000000

Medplum-style storage for Specimen (see SpecimenModel's docstring), same as the other resources
already moved (Organization 5b1969c2ec19, Location 8c41d2e7a9b3, Practitioner a7d3f19c2b64,
HealthcareService c9f5b2d7e813, Endpoint d1a6c3e8f924, PractitionerRole e2b7d4f9a035, Schedule
f3c8e5a1b947, Slot g4d9f6b2c058, Patient h5e0a7c3d169, Appointment i6f1b8d4e27a,
AppointmentResponse j7a2c9e5f381, Encounter k8b3d0f6a492, RelatedPerson l9c4e1a7b503,
AllergyIntolerance m0d5f2b8c614, Condition n1e6a3c9d725, Procedure o2f7b4d0e836,
DiagnosticReport p3a8c5e1f947, Immunization q4b9d6f2a058, ImmunizationRecommendation
r5c0e7a3b169, ImmunizationEvaluation s6d1f8b4c270, FamilyMemberHistory t7e2a9c5d381,
RiskAssessment u8f3b0d6e492, ClinicalImpression v9a4c1e7f503, DetectedIssue w0b5d2f8a614,
Observation x1c6e3a9b705). The whole FHIR resource moves into `specimen.content`; every
column/table that survives is a search index for one of the FHIR R4 Specimen search parameters (or
`_id` / `_lastUpdated`), derived from `content`:

  specimen: status (recreated as an enum holding the real FHIR codes - the old one stored
      `entered_in_error`), collected_start/_end (`collection.collected[x]`, the range it covers),
      accession_system / accession_value (new; the old `accession_identifier_*` columns go),
      the subject_* columns (`subject_type` becomes a plain string) and collector_* (new; the old
      `collection_collector_*` columns go); the public id gets its sequence as a server default;
      new: content.
  specimen_identifier: rebuilt as an index table
  specimen_container_identifier: rebuilt - container.identifier of every container
  specimen_token: new - type, bodysite, container (container.type of every container)
  specimen_reference: new - parent
  dropped: every old child table (collection method / body site / fasting status codings,
      container + its identifiers and codings, processing + its codings and additives, request,
      parent, condition + its codings, note, type coding, identifier + its type coding, accession
      identifier type coding), every main-table column with no search parameter (type text,
      received time, the whole flattened collection, extension and the display /
      logical-identifier details of every reference) and the per-field `specimen_*` enums (the
      shared `organization_reference_type` and `service_request_reference_type` stay).

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_specimen() logic (but keeping a reference's raw string, so an absolute URL
is not lost), so this migration never depends on application code that has since changed; (2)
drops the old child tables/columns and creates the index tables; (3) rebuilds the index from
`content`.

downgrade: not supported. Everything the old schema held is preserved in `content`, but rebuilding
the old normalized tables from it is not implemented - restore from a backup taken before
upgrading.
"""

import json
import re
import unicodedata
from datetime import UTC, date, datetime, time, timedelta, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "y2d7f4b0c816"
down_revision: Union[str, None] = "x1c6e3a9b705"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "specimen"

_STATUS = ("available", "unavailable", "unsatisfactory", "entered-in-error")


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
    if isinstance(value, (datetime, date, time)):
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
    """The FHIR code for an old status label (`entered_in_error` becomes `entered-in-error`)."""
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
        tz = timezone(
            sign * timedelta(hours=int(g["tz"][1:3]), minutes=int(g["tz"][4:6]))
        )
    try:
        low = datetime(
            int(g["y"]),
            int(g["m"] or 1),
            int(g["d"] or 1),
            int(g["H"] or 0),
            int(g["M"] or 0),
            int(g["S"] or 0),
            int(((g["f"] or ".0")[1:] + "000000")[:6]),
            tzinfo=tz,
        )
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


def _point(value):
    return _period_bounds({"start": value, "end": value}) if value else (None, None)


# ── upgrade: old columns/tables -> content (frozen copy of the old mapper) ───

_TYPE_NAMES = {
    t.upper(): t
    for t in (
        "Patient",
        "Group",
        "Device",
        "Substance",
        "Location",
        "Practitioner",
        "PractitionerRole",
        "Specimen",
        "ServiceRequest",
        "RelatedPerson",
        "Organization",
    )
}
_COMPARATORS = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}


def _coding(c):
    return {
        "system": c["system"],
        "version": c["version"],
        "code": c["code"],
        "display": c["display"],
        "userSelected": c["user_selected"],
    }


def _concept(codings, text):
    return {"coding": [_coding(c) for c in codings], "text": text}


def _fallback_identifier(row, prefix):
    """The logical identifier of a Reference. Some old tables carry only part of these columns, so
    every one is read tolerantly."""
    g = row.get
    return {
        "use": g(f"{prefix}_use"),
        "type": {
            "coding": [
                {
                    "system": g(f"{prefix}_type_system"),
                    "version": g(f"{prefix}_type_version"),
                    "code": g(f"{prefix}_type_code"),
                    "display": g(f"{prefix}_type_display"),
                    "userSelected": g(f"{prefix}_type_user_selected"),
                }
            ],
            "text": g(f"{prefix}_type_text"),
        },
        "system": g(f"{prefix}_system"),
        "value": g(f"{prefix}_value"),
        "period": _period(g(f"{prefix}_period_start"), g(f"{prefix}_period_end")),
    }


def _ref(row, prefix):
    """A Reference from the old `{prefix}_reference/_type/_id/_display/_identifier_*` columns."""
    raw = row[f"{prefix}_reference"]
    if not raw and row[f"{prefix}_type"] and row[f"{prefix}_id"]:
        ref_type = str(row[f"{prefix}_type"])
        raw = f"{_TYPE_NAMES.get(ref_type.upper(), ref_type)}/{row[f'{prefix}_id']}"
    return {
        "reference": raw,
        "display": row.get(f"{prefix}_display"),
        "identifier": _fallback_identifier(row, f"{prefix}_identifier"),
    }


def _rows_of(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


def _num(value):
    return float(value) if value is not None else None


def _quantity(row, prefix, comparator=False):
    quantity = {
        "value": _num(row[f"{prefix}_value"]),
        "unit": row[f"{prefix}_unit"],
        "system": row[f"{prefix}_system"],
        "code": row[f"{prefix}_code"],
    }
    if comparator and row.get(f"{prefix}_comparator"):
        quantity["comparator"] = _COMPARATORS.get(
            str(row[f"{prefix}_comparator"]).lower()
        )
    quantity = {k: v for k, v in quantity.items() if v is not None}
    return quantity or None


def _identifier(bind, i, type_table, type_fk):
    return {
        "use": i["use"],
        "type": _concept(_rows_of(bind, type_table, type_fk, i["id"]), i["type_text"]),
        "system": i["system"],
        "value": i["value"],
        "period": _period(i["period_start"], i["period_end"]),
        "assigner": _ref(i, "assigner"),
    }


def _note(n):
    note = {"time": _iso(n["time"]), "text": n["text"]}
    if n["author_string"]:
        note["authorString"] = n["author_string"]
    else:
        author = _prune(_ref(n, "author"))
        if author:
            note["authorReference"] = author
    return note


def _collection(bind, r):
    pk = r["id"]
    collection = {
        "collector": _ref(r, "collection_collector"),
        "duration": _quantity(r, "collection_duration", comparator=True),
        "quantity": _quantity(r, "collection_quantity"),
        "method": _concept(
            _rows_of(bind, f"{P}_collection_method_coding", f"{P}_pk", pk),
            r["collection_method_text"],
        ),
        "bodySite": _concept(
            _rows_of(bind, f"{P}_collection_body_site_coding", f"{P}_pk", pk),
            r["collection_body_site_text"],
        ),
    }
    if r["collection_collected_date_time"]:
        collection["collectedDateTime"] = _iso(r["collection_collected_date_time"])
    elif r["collection_collected_period_start"] or r["collection_collected_period_end"]:
        collection["collectedPeriod"] = _period(
            r["collection_collected_period_start"], r["collection_collected_period_end"]
        )
    fasting = _concept(
        _rows_of(bind, f"{P}_collection_fasting_status_coding", f"{P}_pk", pk),
        r["collection_fasting_status_text"],
    )
    if _prune(fasting):
        collection["fastingStatusCodeableConcept"] = fasting
    else:
        collection["fastingStatusDuration"] = _quantity(
            r, "collection_fasting_status_duration", comparator=True
        )
    return collection


def _processing(bind, p):
    entry = {
        "description": p["description"],
        "procedure": _concept(
            _rows_of(
                bind, f"{P}_processing_procedure_coding", f"{P}_processing_id", p["id"]
            ),
            p["procedure_text"],
        ),
        "additive": [
            _ref(a, "reference")
            for a in _rows_of(
                bind, f"{P}_processing_additive", f"{P}_processing_id", p["id"]
            )
        ],
    }
    if p["time_date_time"]:
        entry["timeDateTime"] = _iso(p["time_date_time"])
    elif p["time_period_start"] or p["time_period_end"]:
        entry["timePeriod"] = _period(p["time_period_start"], p["time_period_end"])
    return entry


def _container(bind, c):
    cid = c["id"]
    entry = {
        "identifier": [
            _identifier(
                bind,
                i,
                f"{P}_container_identifier_type_coding",
                f"{P}_container_identifier_id",
            )
            for i in _rows_of(
                bind, f"{P}_container_identifier", f"{P}_container_id", cid
            )
        ],
        "description": c["description"],
        "type": _concept(
            _rows_of(bind, f"{P}_container_type_coding", f"{P}_container_id", cid),
            c["type_text"],
        ),
        "capacity": _quantity(c, "capacity"),
        "specimenQuantity": _quantity(c, "specimen_quantity"),
    }
    additive = _concept(
        _rows_of(bind, f"{P}_container_additive_coding", f"{P}_container_id", cid),
        c["additive_codeable_concept_text"],
    )
    if _prune(additive):
        entry["additiveCodeableConcept"] = additive
    else:
        entry["additiveReference"] = _ref(c, "additive_reference")
    return entry


def _build_content(bind, r):
    pk = r["id"]
    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": [
            _identifier(bind, i, f"{P}_identifier_type_coding", f"{P}_identifier_id")
            for i in _rows_of(bind, f"{P}_identifier", f"{P}_pk", pk)
        ],
        "accessionIdentifier": {
            "use": r["accession_identifier_use"],
            "type": _concept(
                _rows_of(bind, f"{P}_accession_identifier_type_coding", f"{P}_pk", pk),
                r["accession_identifier_type_text"],
            ),
            "system": r["accession_identifier_system"],
            "value": r["accession_identifier_value"],
            "period": _period(
                r["accession_identifier_period_start"],
                r["accession_identifier_period_end"],
            ),
            "assigner": _ref(r, "accession_identifier_assigner"),
        },
        "status": _hyphenate(r["status_text"]),
        "type": _concept(
            _rows_of(bind, f"{P}_type_coding", f"{P}_pk", pk), r["type_text"]
        ),
        "subject": _ref(r, "subject"),
        "receivedTime": _iso(r["received_time"]),
        "parent": [
            _ref(x, "reference") for x in _rows_of(bind, f"{P}_parent", f"{P}_pk", pk)
        ],
        "request": [
            _ref(x, "reference") for x in _rows_of(bind, f"{P}_request", f"{P}_pk", pk)
        ],
        "collection": _collection(bind, r),
        "processing": [
            _processing(bind, p)
            for p in _rows_of(bind, f"{P}_processing", f"{P}_pk", pk)
        ],
        "container": [
            _container(bind, c) for c in _rows_of(bind, f"{P}_container", f"{P}_pk", pk)
        ],
        "condition": [
            _concept(
                _rows_of(bind, f"{P}_condition_coding", f"{P}_condition_id", c["id"]),
                c["text"],
            )
            for c in _rows_of(bind, f"{P}_condition", f"{P}_pk", pk)
        ],
        "note": [_note(n) for n in _rows_of(bind, f"{P}_note", f"{P}_pk", pk)],
    }
    return _prune(content)


def _backfill_content(bind):
    # `status` is an enum: cast it to text so the driver returns the label.
    for r in _rows(bind, f"SELECT *, status::text AS status_text FROM {P}"):
        bind.execute(
            sa.text(f"UPDATE {P} SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {
                "c": json.dumps(_build_content(bind, dict(r)), default=str),
                "id": r["id"],
            },
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_SUBJECT_TYPES = ("Patient", "Group", "Device", "Substance", "Location")
_COLLECTOR_TYPES = ("Practitioner", "PractitionerRole")


def _typed(reference, allowed):
    match = _REF.match(reference or "")
    return (
        (match["type"], int(match["id"]))
        if match and (allowed is None or match["type"] in allowed)
        else (None, None)
    )


def _ref_params(prefix, ref, allowed):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    rtype, rid = _typed(reference, allowed)
    return {
        f"{prefix}_reference": reference,
        f"{prefix}_type": rtype,
        f"{prefix}_id": rid,
        f"{prefix}_identifier_system": identifier.get("system"),
        f"{prefix}_identifier_value": identifier.get("value"),
    }


def _insert_token(bind, pk, param, concept):
    if not concept:
        return
    text = _norm(concept.get("text"))
    codings = [
        c
        for c in concept.get("coding") or []
        if c.get("system") or c.get("code") or c.get("display")
    ]
    for c in codings or ([{}] if text else []):
        bind.execute(
            sa.text(
                f"INSERT INTO {P}_token ({P}_pk, param, system, code, display_norm, text_norm) "
                "VALUES (:pk, :param, :s, :c, :d, :t)"
            ),
            {
                "pk": pk,
                "param": param,
                "s": c.get("system"),
                "c": c.get("code"),
                "d": _norm(c.get("display")),
                "t": text,
            },
        )


def _insert_identifier(bind, table, pk, identifier):
    if not (identifier.get("system") or identifier.get("value")):
        return
    itype = identifier.get("type") or {}
    for c in itype.get("coding") or [{}]:
        bind.execute(
            sa.text(
                f"INSERT INTO {table} ({P}_pk, system, value, type_system, type_code, type_text_norm, "
                "type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"
            ),
            {
                "pk": pk,
                "s": identifier.get("system"),
                "v": identifier.get("value"),
                "ts": c.get("system"),
                "tc": c.get("code"),
                "tt": _norm(itype.get("text")),
                "td": _norm(c.get("display")),
            },
        )


def _insert_reference(bind, pk, param, ref):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return
    rtype, rid = _typed(reference, None)
    bind.execute(
        sa.text(
            f"INSERT INTO {P}_reference ({P}_pk, param, reference_reference, reference_type, reference_id, "
            "reference_identifier_system, reference_identifier_value) VALUES (:pk, :param, :r, :t, :i, :s, :v)"
        ),
        {
            "pk": pk,
            "param": param,
            "r": reference,
            "t": rtype,
            "i": rid,
            "s": identifier.get("system"),
            "v": identifier.get("value"),
        },
    )


def _rebuild_index(bind):
    for row in _rows(bind, f"SELECT id, content FROM {P}"):
        pk, doc = row["id"], _json(row["content"])
        collection = doc.get("collection") or {}

        if collection.get("collectedDateTime"):
            start, end = _point(collection["collectedDateTime"])
        else:
            start, end = _period_bounds(collection.get("collectedPeriod"))
        accession = doc.get("accessionIdentifier") or {}
        status = doc.get("status")
        columns = {
            "collected_start": start,
            "collected_end": end,
            "accession_system": accession.get("system"),
            "accession_value": accession.get("value"),
            **_ref_params("subject", doc.get("subject"), _SUBJECT_TYPES),
            **_ref_params("collector", collection.get("collector"), _COLLECTOR_TYPES),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(
                f"UPDATE {P} SET status = CAST(:status AS specimen_status), {sets} WHERE id = :pk"
            ),
            {**columns, "status": status if status in _STATUS else None, "pk": pk},
        )

        for i in doc.get("identifier") or []:
            _insert_identifier(bind, f"{P}_identifier", pk, i)
        _insert_token(bind, pk, "type", doc.get("type"))
        _insert_token(bind, pk, "bodysite", collection.get("bodySite"))
        for container in doc.get("container") or []:
            container = container or {}
            _insert_token(bind, pk, "container", container.get("type"))
            for i in container.get("identifier") or []:
                _insert_identifier(bind, f"{P}_container_identifier", pk, i)
        for ref in doc.get("parent") or []:
            _insert_reference(bind, pk, "parent", ref)


# Every old Specimen table (NOT `specimen_definition*`, which belongs to another resource): the new
# index tables do not exist yet. Dropped with CASCADE, so order does not matter.
_OLD_TABLES = (
    "specimen_collection_method_coding",
    "specimen_collection_body_site_coding",
    "specimen_collection_fasting_status_coding",
    "specimen_container",
    "specimen_container_identifier",
    "specimen_container_identifier_type_coding",
    "specimen_container_type_coding",
    "specimen_container_additive_coding",
    "specimen_processing",
    "specimen_processing_procedure_coding",
    "specimen_processing_additive",
    "specimen_request",
    "specimen_parent",
    "specimen_condition",
    "specimen_condition_coding",
    "specimen_note",
    "specimen_type_coding",
    "specimen_identifier",
    "specimen_identifier_type_coding",
    "specimen_accession_identifier_type_coding",
)

# The per-field enums of the old schema (the shared `organization_reference_type` and
# `service_request_reference_type` stay). `specimen_status` is recreated below with the real FHIR codes.
_OLD_ENUMS = (
    "specimen_status",
    "specimen_subject_reference_type",
    "specimen_collector_reference_type",
    "specimen_quantity_comparator",
    "specimen_additive_reference_type",
    "specimen_parent_reference_type",
    "specimen_note_author_reference_type",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns and the subject index
# columns (its reference-type enum becomes a plain string). The collector, accession, status and date
# columns are new.
_KEEP = {
    "id",
    "specimen_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
    *(
        f"subject_{part}"
        for part in ("reference", "type", "id", "identifier_system", "identifier_value")
    ),
}


def _fk():
    return sa.Column(
        f"{P}_pk", sa.BigInteger(), sa.ForeignKey(f"{P}.id"), nullable=False
    )


def _index(table, *columns):
    op.create_index(op.f("ix_" + table + "_" + columns[0]), table, list(columns))


def _identifier_table(name):
    op.create_table(
        name,
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("system", sa.String(), nullable=True),
        sa.Column("value", sa.String(), nullable=True),
        sa.Column("type_system", sa.String(), nullable=True),
        sa.Column("type_code", sa.String(), nullable=True),
        sa.Column("type_text_norm", sa.String(), nullable=True),
        sa.Column("type_display_norm", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(name, f"{P}_pk")
    _index(name, "value")


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(
        P, sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    _backfill_content(bind)

    for table in _OLD_TABLES:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
    existing = [
        r[0]
        for r in bind.execute(
            sa.text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = '{P}' "
                "AND table_schema = current_schema()"
            )
        )
    ]
    for column in existing:
        if column not in _KEEP:
            op.drop_column(P, column)

    # The subject type was an enum; it is a plain string now.
    op.alter_column(
        P,
        "subject_type",
        type_=sa.String(),
        nullable=True,
        postgresql_using="subject_type::text",
    )
    for name in _OLD_ENUMS:
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # Specimens are searched by subject: one index on the pair instead of the lone id.
    op.execute(f"DROP INDEX IF EXISTS ix_{P}_subject_id")
    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {P} ALTER COLUMN specimen_id SET DEFAULT nextval('specimen_pub_seq')"
    )

    # The audit columns as the shared mixin declares them (the original table was created with
    # looser ones): tenant/actor NOT NULL, timestamps nullable and indexed, and no UNIQUE on the
    # public id (the sequence keeps it unique).
    op.execute(f"UPDATE {P} SET tenant_id = '' WHERE tenant_id IS NULL")
    op.execute(f"UPDATE {P} SET created_by = '' WHERE created_by IS NULL")
    op.alter_column(P, "tenant_id", existing_type=sa.String(), nullable=False)
    op.alter_column(P, "created_by", existing_type=sa.String(), nullable=False)
    op.alter_column(
        P, "created_at", existing_type=sa.DateTime(timezone=True), nullable=True
    )
    op.alter_column(
        P, "updated_at", existing_type=sa.DateTime(timezone=True), nullable=True
    )
    op.execute(f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS specimen_specimen_id_key")
    for column in ("tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)

    # status: recreated as an enum holding the real FHIR codes.
    postgresql.ENUM(*_STATUS, name="specimen_status").create(bind, checkfirst=True)
    op.add_column(
        P,
        sa.Column(
            "status",
            postgresql.ENUM(*_STATUS, name="specimen_status", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        P, sa.Column("collected_start", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        P, sa.Column("collected_end", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(P, sa.Column("accession_system", sa.String(), nullable=True))
    op.add_column(P, sa.Column("accession_value", sa.String(), nullable=True))
    for column, kind in (
        ("reference", sa.String()),
        ("type", sa.String()),
        ("id", sa.BigInteger()),
        ("identifier_system", sa.String()),
        ("identifier_value", sa.String()),
    ):
        op.add_column(P, sa.Column(f"collector_{column}", kind, nullable=True))
    op.create_index("ix_specimen_collected", P, ["collected_start", "collected_end"])
    op.create_index("ix_specimen_subject_type_id", P, ["subject_type", "subject_id"])

    _identifier_table(f"{P}_identifier")
    _identifier_table(f"{P}_container_identifier")

    op.create_table(
        f"{P}_token",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("param", sa.String(), nullable=False),
        sa.Column("system", sa.String(), nullable=True),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("display_norm", sa.String(), nullable=True),
        sa.Column("text_norm", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_token", f"{P}_pk")
    op.create_index("ix_specimen_token_param_code", f"{P}_token", ["param", "code"])

    op.create_table(
        f"{P}_reference",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("param", sa.String(), nullable=False),
        sa.Column("reference_reference", sa.String(), nullable=True),
        sa.Column("reference_type", sa.String(), nullable=True),
        sa.Column("reference_id", sa.BigInteger(), nullable=True),
        sa.Column("reference_identifier_system", sa.String(), nullable=True),
        sa.Column("reference_identifier_value", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_reference", f"{P}_pk")
    op.create_index(
        "ix_specimen_reference_param_type_id",
        f"{P}_reference",
        ["param", "reference_type", "reference_id"],
    )

    _rebuild_index(bind)
    for column in ("id", "collector_id", "accession_value", "status"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "specimen content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
