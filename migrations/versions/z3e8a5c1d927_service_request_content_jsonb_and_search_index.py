"""service_request: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: z3e8a5c1d927
Revises: y2d7f4b0c816
Create Date: 2026-12-12 10:00:00.000000

Medplum-style storage for ServiceRequest (see ServiceRequestModel's docstring), same as the other
resources already moved (the latest being Specimen y2d7f4b0c816). The whole FHIR resource moves
into `service_request.content`; every column/table that survives is a search index for one of the
FHIR R4 ServiceRequest search parameters (or `_id` / `_lastUpdated`), derived from `content`:

  service_request: status / intent / priority (recreated as enums holding the real FHIR codes - the
      old ones stored `on_hold`, `original_order`, ...), authored_start/_end, occurrence_start/_end
      (the range occurrence[x] covers - a dateTime, a Period or a Timing), requisition_system/_value,
      the subject_* / encounter_* / requester_* columns (their `*_type` becomes a plain string); the
      public id gets its sequence as a server default; new: content.
  service_request_identifier: rebuilt as an index table
  service_request_token: new - category, code, body-site, performer-type
  service_request_reference: new - based-on, replaces, specimen, instantiates-canonical
  service_request_performer: new - one row per performer reference
  service_request_instantiates_uri: new - one row per URI
  dropped: every old child table, every main-table column with no search parameter and the per-field
      `service_request_*` enums (the shared `organization_reference_type` and
      `encounter_reference_type` stay).

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_service_request() logic (but keeping a reference's raw string, so an
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
from datetime import UTC, date, datetime, time, timedelta, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "z3e8a5c1d927"
down_revision: Union[str, None] = "y2d7f4b0c816"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "service_request"

_STATUS = ("draft", "active", "on-hold", "revoked", "completed", "entered-in-error", "unknown")
_INTENT = (
    "proposal",
    "plan",
    "directive",
    "order",
    "original-order",
    "reflex-order",
    "filler-order",
    "instance-order",
    "option",
)
_PRIORITY = ("routine", "urgent", "asap", "stat")


# -- shared helpers (frozen - never import application code here) --------------


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
    """The FHIR code for an old enum label (`on_hold` becomes `on-hold`)."""
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
    """(start, end) instants of a FHIR date/dateTime at its written precision - the half-open
    range it covers (frozen copy of app.fhir.search.values.parse_date). (None, None) if absent or
    unparseable."""
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
    """(start, end) of a Period: the first instant it covers and the first instant after it (None
    = open on that side). Frozen copy of app.repository._content_index.period_bounds."""
    period = period or {}
    start = _bounds(period.get("start"))[0] if period.get("start") else None
    end = _bounds(period.get("end"))[1] if period.get("end") else None
    return start, end


def _point(value):
    return _period_bounds({"start": value, "end": value}) if value else (None, None)


# -- upgrade: old columns/tables -> content (frozen copy of the old mapper) ------

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
    g = row.get
    raw = g(f"{prefix}_reference")
    if not raw and g(f"{prefix}_type") and g(f"{prefix}_id"):
        raw = f"{g(f'{prefix}_type')}/{g(f'{prefix}_id')}"
    return {
        "reference": raw,
        "display": g(f"{prefix}_display"),
        "identifier": _fallback_identifier(row, f"{prefix}_identifier"),
    }


def _rows_of(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


def _num(value):
    return float(value) if value is not None else None


def _quantity(row, prefix, comparator=True):
    g = row.get
    quantity = {
        "value": _num(g(f"{prefix}_value")),
        "unit": g(f"{prefix}_unit"),
        "system": g(f"{prefix}_system"),
        "code": g(f"{prefix}_code"),
    }
    if comparator and g(f"{prefix}_comparator"):
        quantity["comparator"] = _COMPARATORS.get(str(g(f"{prefix}_comparator")).lower())
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


def _cc_list(bind, r, table, text_col="text"):
    """A 0..* CodeableConcept held as `<table>` (text) + `<table>_coding`."""
    out = []
    for row in _rows_of(bind, f"{P}_{table}", f"{P}_pk", r["id"]):
        out.append(_concept(_rows_of(bind, f"{P}_{table}_coding", f"{P}_{table}_id", row["id"]), row[text_col]))
    return out


def _refs(bind, r, table):
    return [_ref(x, "reference") for x in _rows_of(bind, f"{P}_{table}", f"{P}_pk", r["id"])]


def _build_content(bind, r):
    pk = r["id"]
    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": [
            _identifier(bind, i, f"{P}_identifier_type_coding", f"{P}_identifier_id")
            for i in _rows_of(bind, f"{P}_identifier", f"{P}_pk", pk)
        ],
        "instantiatesCanonical": list(r["instantiates_canonical"] or []),
        "instantiatesUri": list(r["instantiates_uri"] or []),
        "basedOn": _refs(bind, r, "based_on"),
        "replaces": _refs(bind, r, "replaces"),
        "requisition": {
            "use": r["requisition_use"],
            "type": _concept(_rows_of(bind, f"{P}_requisition_type_coding", f"{P}_pk", pk), r["requisition_type_text"]),
            "system": r["requisition_system"],
            "value": r["requisition_value"],
            "period": _period(r["requisition_period_start"], r["requisition_period_end"]),
            "assigner": _ref(r, "requisition_assigner"),
        },
        "status": _hyphenate(r["status_text"]),
        "intent": _hyphenate(r["intent_text"]),
        "category": _cc_list(bind, r, "category"),
        "priority": _hyphenate(r["priority_text"]),
        "doNotPerform": r["do_not_perform"],
        "code": _concept(_rows_of(bind, f"{P}_code_coding", f"{P}_pk", pk), r["code_text"]),
        "orderDetail": _cc_list(bind, r, "order_detail"),
        "subject": _ref(r, "subject"),
        "encounter": _ref(r, "encounter"),
        "authoredOn": _iso(r["authored_on"]),
        "requester": _ref(r, "requester"),
        "performerType": _concept(
            _rows_of(bind, f"{P}_performer_type_coding", f"{P}_pk", pk), r["performer_type_text"]
        ),
        "performer": _refs(bind, r, "performer"),
        "locationCode": _cc_list(bind, r, "location_code"),
        "locationReference": _refs(bind, r, "location_reference"),
        "reasonCode": _cc_list(bind, r, "reason_code"),
        "reasonReference": _refs(bind, r, "reason_reference"),
        "insurance": _refs(bind, r, "insurance"),
        "supportingInfo": _refs(bind, r, "supporting_info"),
        "specimen": _refs(bind, r, "specimen"),
        "bodySite": _cc_list(bind, r, "body_site"),
        "note": [_note(n) for n in _rows_of(bind, f"{P}_note", f"{P}_pk", pk)],
        "patientInstruction": r["patient_instruction"],
        "relevantHistory": _refs(bind, r, "relevant_history"),
    }
    # quantity[x]: a Quantity, a Ratio or a Range - whichever the old row carries
    quantity = _quantity(r, "quantity_quantity")
    ratio = {
        "numerator": _quantity(r, "quantity_ratio_numerator"),
        "denominator": _quantity(r, "quantity_ratio_denominator"),
    }
    rng = {
        "low": _quantity(r, "quantity_range_low", comparator=False),
        "high": _quantity(r, "quantity_range_high", comparator=False),
    }
    if quantity:
        content["quantityQuantity"] = quantity
    elif _prune(ratio):
        content["quantityRatio"] = ratio
    elif _prune(rng):
        content["quantityRange"] = rng
    # occurrence[x]
    if r["occurrence_date_time"]:
        content["occurrenceDateTime"] = _iso(r["occurrence_date_time"])
    elif r["occurrence_period_start"] or r["occurrence_period_end"]:
        content["occurrencePeriod"] = _period(r["occurrence_period_start"], r["occurrence_period_end"])
    elif r["occurrence_timing"]:
        content["occurrenceTiming"] = _json(r["occurrence_timing"])
    # asNeeded[x]
    needed = _concept(_rows_of(bind, f"{P}_as_needed_coding", f"{P}_pk", pk), r["as_needed_codeable_concept_text"])
    if _prune(needed):
        content["asNeededCodeableConcept"] = needed
    elif r["as_needed_boolean"] is not None:
        content["asNeededBoolean"] = r["as_needed_boolean"]
    return _prune(content)


def _backfill_content(bind):
    # status / intent / priority are enums: cast them to text so the driver returns the label.
    for r in _rows(
        bind,
        f"SELECT *, status::text AS status_text, intent::text AS intent_text, "
        f"priority::text AS priority_text FROM {P}",
    ):
        bind.execute(
            sa.text(f"UPDATE {P} SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, dict(r)), default=str), "id": r["id"]},
        )


# -- upgrade: content -> search index (frozen copy of _indexer.py) ---------------

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_SUBJECT_TYPES = ("Patient", "Group", "Location", "Device")
_REQUESTER_TYPES = ("Practitioner", "PractitionerRole", "Organization", "Patient", "RelatedPerson", "Device")
_PERFORMER_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "CareTeam",
    "HealthcareService",
    "Patient",
    "Device",
    "RelatedPerson",
)
_REFERENCE_TYPES = {
    "based-on": ("CarePlan", "ServiceRequest", "MedicationRequest"),
    "replaces": ("ServiceRequest",),
    "specimen": ("Specimen",),
    "instantiates-canonical": ("ActivityDefinition", "PlanDefinition"),
}


def _typed(reference, allowed):
    match = _REF.match(reference or "")
    if match and match["type"] in allowed:
        return match["type"], int(match["id"])
    return None, None


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
    codings = [c for c in concept.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
    for c in codings or ([{}] if text else []):
        bind.execute(
            sa.text(
                f"INSERT INTO {P}_token ({P}_pk, param, system, code, display_norm, text_norm) "
                "VALUES (:pk, :param, :s, :c, :d, :t)"
            ),
            {"pk": pk, "param": param, "s": c.get("system"), "c": c.get("code"), "d": _norm(c.get("display")), "t": text},
        )


def _insert_identifier(bind, pk, identifier):
    if not (identifier.get("system") or identifier.get("value")):
        return
    itype = identifier.get("type") or {}
    for c in itype.get("coding") or [{}]:
        bind.execute(
            sa.text(
                f"INSERT INTO {P}_identifier ({P}_pk, system, value, type_system, type_code, type_text_norm, "
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
    rtype, rid = _typed(reference, _REFERENCE_TYPES[param])
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


def _occurrence_bounds(doc):
    if doc.get("occurrenceDateTime"):
        return _point(doc["occurrenceDateTime"])
    if doc.get("occurrencePeriod"):
        return _period_bounds(doc["occurrencePeriod"])
    timing = doc.get("occurrenceTiming")
    if timing:
        starts, ends = [], []
        for event in timing.get("event") or []:
            start, end = _point(event)
            if start:
                starts.append(start)
            if end:
                ends.append(end)
        if starts:
            return min(starts), max(ends)
        return _period_bounds((timing.get("repeat") or {}).get("boundsPeriod"))
    return None, None


def _rebuild_index(bind):
    for row in _rows(bind, f"SELECT id, content FROM {P}"):
        pk, doc = row["id"], _json(row["content"])
        authored_start, authored_end = _point(doc.get("authoredOn"))
        occurrence_start, occurrence_end = _occurrence_bounds(doc)
        requisition = doc.get("requisition") or {}
        status, intent, priority = doc.get("status"), doc.get("intent"), doc.get("priority")
        columns = {
            "authored_start": authored_start,
            "authored_end": authored_end,
            "occurrence_start": occurrence_start,
            "occurrence_end": occurrence_end,
            "requisition_system": requisition.get("system"),
            "requisition_value": requisition.get("value"),
            **_ref_params("subject", doc.get("subject"), _SUBJECT_TYPES),
            **_ref_params("encounter", doc.get("encounter"), ("Encounter",)),
            **_ref_params("requester", doc.get("requester"), _REQUESTER_TYPES),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(
                f"UPDATE {P} SET status = CAST(:status AS service_request_status), "
                f"intent = CAST(:intent AS service_request_intent), "
                f"priority = CAST(:priority AS service_request_priority), {sets} WHERE id = :pk"
            ),
            {
                **columns,
                "status": status if status in _STATUS else None,
                "intent": intent if intent in _INTENT else None,
                "priority": priority if priority in _PRIORITY else None,
                "pk": pk,
            },
        )

        for i in doc.get("identifier") or []:
            _insert_identifier(bind, pk, i)
        for category in doc.get("category") or []:
            _insert_token(bind, pk, "category", category)
        _insert_token(bind, pk, "code", doc.get("code"))
        for site in doc.get("bodySite") or []:
            _insert_token(bind, pk, "body-site", site)
        _insert_token(bind, pk, "performer-type", doc.get("performerType"))
        for param, element in (("based-on", "basedOn"), ("replaces", "replaces"), ("specimen", "specimen")):
            for ref in doc.get(element) or []:
                _insert_reference(bind, pk, param, ref)
        for canonical in doc.get("instantiatesCanonical") or []:
            _insert_reference(bind, pk, "instantiates-canonical", {"reference": canonical})
        for ref in doc.get("performer") or []:
            ref = ref or {}
            reference = ref.get("reference")
            identifier = ref.get("identifier") or {}
            if not (reference or identifier.get("value")):
                continue
            rtype, rid = _typed(reference, _PERFORMER_TYPES)
            bind.execute(
                sa.text(
                    f"INSERT INTO {P}_performer ({P}_pk, reference_reference, reference_type, reference_id, "
                    "reference_identifier_system, reference_identifier_value) VALUES (:pk, :r, :t, :i, :s, :v)"
                ),
                {
                    "pk": pk,
                    "r": reference,
                    "t": rtype,
                    "i": rid,
                    "s": identifier.get("system"),
                    "v": identifier.get("value"),
                },
            )
        for uri in doc.get("instantiatesUri") or []:
            if uri:
                bind.execute(
                    sa.text(f"INSERT INTO {P}_instantiates_uri ({P}_pk, uri) VALUES (:pk, :u)"),
                    {"pk": pk, "u": uri},
                )


# Main-table columns that survive unchanged: the id, the audit/tenant columns and the subject /
# encounter / requester index columns (their reference-type enums become plain strings). The
# status, date, requisition and content columns are new.
_REF_PARTS = ("reference", "type", "id", "identifier_system", "identifier_value")
_KEEP = {
    "id",
    "service_request_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
    *(f"{prefix}_{part}" for prefix in ("subject", "encounter", "requester") for part in _REF_PARTS),
}


def _fk():
    return sa.Column(f"{P}_pk", sa.BigInteger(), sa.ForeignKey(f"{P}.id"), nullable=False)


def _index(table, *columns):
    op.create_index(op.f("ix_" + table + "_" + columns[0]), table, list(columns))


def _reference_columns():
    return [
        sa.Column("reference_reference", sa.String(), nullable=True),
        sa.Column("reference_type", sa.String(), nullable=True),
        sa.Column("reference_id", sa.BigInteger(), nullable=True),
        sa.Column("reference_identifier_system", sa.String(), nullable=True),
        sa.Column("reference_identifier_value", sa.String(), nullable=True),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(P, sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child table (the prefix is unique to this resource).
    for (table,) in bind.execute(
        sa.text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema() "
            "AND table_name LIKE 'service\\_request\\_%' AND table_type = 'BASE TABLE'"
        )
    ).all():
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

    # The reference types were enums; they are plain strings now (the shared
    # `encounter_reference_type` enum stays for the other resources that use it).
    for prefix in ("subject", "encounter", "requester"):
        op.alter_column(
            P, f"{prefix}_type", type_=sa.String(), nullable=True, postgresql_using=f"{prefix}_type::text"
        )
    for (name,) in bind.execute(
        sa.text("SELECT typname FROM pg_type WHERE typtype = 'e' AND typname LIKE 'service\\_request\\_%'")
    ).all():
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # Service requests are searched by subject: one index on the pair instead of the lone id.
    op.execute(f"DROP INDEX IF EXISTS ix_{P}_subject_id")
    # The public id's sequence is now its server default.
    op.execute(f"ALTER TABLE {P} ALTER COLUMN service_request_id SET DEFAULT nextval('service_request_pub_seq')")

    # The audit columns as the shared mixin declares them (the original table was created with
    # looser ones): tenant/actor NOT NULL, timestamps nullable and indexed, and no UNIQUE on the
    # public id (the sequence keeps it unique).
    op.execute(f"UPDATE {P} SET tenant_id = '' WHERE tenant_id IS NULL")
    op.execute(f"UPDATE {P} SET created_by = '' WHERE created_by IS NULL")
    op.alter_column(P, "tenant_id", existing_type=sa.String(), nullable=False)
    op.alter_column(P, "created_by", existing_type=sa.String(), nullable=False)
    op.alter_column(P, "created_at", existing_type=sa.DateTime(timezone=True), nullable=True)
    op.alter_column(P, "updated_at", existing_type=sa.DateTime(timezone=True), nullable=True)
    op.execute(f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS service_request_service_request_id_key")
    for column in ("tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)

    # status / intent / priority: recreated as enums holding the real FHIR codes.
    for name, values in (("status", _STATUS), ("intent", _INTENT), ("priority", _PRIORITY)):
        postgresql.ENUM(*values, name=f"{P}_{name}").create(bind, checkfirst=True)
        op.add_column(
            P,
            sa.Column(name, postgresql.ENUM(*values, name=f"{P}_{name}", create_type=False), nullable=True),
        )
    for column in ("authored_start", "authored_end", "occurrence_start", "occurrence_end"):
        op.add_column(P, sa.Column(column, sa.DateTime(timezone=True), nullable=True))
    op.add_column(P, sa.Column("requisition_system", sa.String(), nullable=True))
    op.add_column(P, sa.Column("requisition_value", sa.String(), nullable=True))
    op.create_index("ix_service_request_authored", P, ["authored_start", "authored_end"])
    op.create_index("ix_service_request_occurrence", P, ["occurrence_start", "occurrence_end"])
    op.create_index("ix_service_request_subject_type_id", P, ["subject_type", "subject_id"])

    op.create_table(
        f"{P}_identifier",
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
    _index(f"{P}_identifier", f"{P}_pk")
    _index(f"{P}_identifier", "value")

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
    op.create_index("ix_service_request_token_param_code", f"{P}_token", ["param", "code"])

    op.create_table(
        f"{P}_reference",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("param", sa.String(), nullable=False),
        *_reference_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_reference", f"{P}_pk")
    op.create_index(
        "ix_service_request_reference_param_type_id", f"{P}_reference", ["param", "reference_type", "reference_id"]
    )

    op.create_table(
        f"{P}_performer",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        *_reference_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_performer", f"{P}_pk")
    op.create_index("ix_service_request_performer_type_id", f"{P}_performer", ["reference_type", "reference_id"])

    op.create_table(
        f"{P}_instantiates_uri",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("uri", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_instantiates_uri", f"{P}_pk")
    _index(f"{P}_instantiates_uri", "uri")

    _rebuild_index(bind)
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "service_request content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
