"""care_plan: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: e8d3f0b6c472
Revises: d7c2e9a5b361
Create Date: 2026-12-14 10:00:00.000000

Medplum-style storage for CarePlan (see CarePlanModel's docstring), same as the other resources
already moved (Organization 5b1969c2ec19 ... ServiceRequest z3e8a5c1d927, Medication a4f9b6d2e038,
MedicationRequest b5a0c7e3f149, Group c6b1d8f4a250, CareTeam d7c2e9a5b361). The whole FHIR resource
moves into `care_plan.content`; every column/table that survives is a search index for one of the
FHIR R4 CarePlan search parameters (or `_id` / `_lastUpdated`), derived from `content`:

  care_plan: status and intent (recreated as enums holding the real FHIR codes - the old ones
      stored the Python member names, e.g. `on_hold`), period_start/_end (`period`, the half-open
      range it covers; the old columns held the raw instants, so they are recomputed), the
      subject_* and encounter_* columns (`*_type` become plain strings); the public id gets its
      sequence as a server default; new: content.
  care_plan_identifier: rebuilt as an index table
  care_plan_token: new - category, activity-code
  care_plan_reference: new - based-on, replaces, part-of, care-team, condition, goal,
      instantiates-canonical
  care_plan_instantiates_uri: new - one row per URI
  care_plan_performer: new - activity.detail.performer of every activity
  care_plan_activity: rebuilt as an index table - one row per activity with a reference or a
      schedule (activity-reference, activity-date)
  dropped: every old child table (identifier + type coding, category + codings, basedOn,
      replaces, partOf, contributor, careTeam, addresses, goal, note, and the whole activity tree
      with its outcome, progress, detail code / reason / goal / status reason / performer /
      product tables), every main-table column with no search parameter (title, description,
      created, author, instantiates arrays, extension and the display / logical-identifier
      details of every reference) and the per-field `care_plan_*` enums.

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_care_plan() logic (but keeping a reference's raw string, so an absolute
URL is not lost), so this migration never depends on application code that has since changed;
(2) drops the old child tables/columns and creates the index tables; (3) rebuilds the index from
`content`.

downgrade: not supported. Everything the old schema held is preserved in `content`, but rebuilding
the old normalized tables from it is not implemented - restore from a backup taken before
upgrading.
"""

import json
import re
import unicodedata
from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e8d3f0b6c472"
down_revision: Union[str, None] = "d7c2e9a5b361"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "care_plan"

_STATUS = (
    "draft",
    "active",
    "on-hold",
    "revoked",
    "completed",
    "entered-in-error",
    "unknown",
)
_INTENT = ("proposal", "plan", "order", "option")


# -- shared helpers (frozen - never import application code here) ---------------------------


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
    range it covers (frozen copy of app.fhir.search.values.parse_date). (None, None) if absent
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
    """(start, end) of a Period: the first instant it covers and the first instant after it (None
    = open on that side). Frozen copy of app.repository._content_index.period_bounds."""
    period = period or {}
    start = _bounds(period.get("start"))[0] if period.get("start") else None
    end = _bounds(period.get("end"))[1] if period.get("end") else None
    return start, end


def _point(value):
    return _period_bounds({"start": value, "end": value}) if value else (None, None)


# -- upgrade: old columns/tables -> content (frozen copy of the old mapper) -----------------

_TYPE_NAMES = {
    t.upper(): t
    for t in (
        "Patient",
        "Group",
        "Encounter",
        "Practitioner",
        "PractitionerRole",
        "RelatedPerson",
        "Organization",
        "CareTeam",
        "CarePlan",
        "Condition",
        "Goal",
        "Device",
        "Location",
        "HealthcareService",
        "Medication",
        "Substance",
        "Appointment",
        "CommunicationRequest",
        "DeviceRequest",
        "MedicationRequest",
        "NutritionOrder",
        "Task",
        "ServiceRequest",
        "VisionPrescription",
        "RequestGroup",
        "Observation",
        "DiagnosticReport",
        "DocumentReference",
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
    """The logical identifier of a Reference. Some old tables carry only part of these columns,
    so every one is read tolerantly."""
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


def _refs(bind, table, pk):
    return [_ref(x, "reference") for x in _rows_of(bind, table, f"{P}_pk", pk)]


def _num(value):
    return float(value) if isinstance(value, Decimal) else value


def _quantity(row, prefix):
    comparator = row.get(f"{prefix}_comparator_text")
    quantity = {
        "value": _num(row[f"{prefix}_value"]),
        "comparator": _COMPARATORS.get(str(comparator).lower(), comparator)
        if comparator
        else None,
        "unit": row[f"{prefix}_unit"],
        "system": row[f"{prefix}_system"],
        "code": row[f"{prefix}_code"],
    }
    quantity = {k: v for k, v in quantity.items() if v is not None}
    return quantity or None


def _identifier(bind, i):
    return {
        "use": i["use"],
        "type": _concept(
            _rows_of(bind, f"{P}_identifier_type_coding", "identifier_id", i["id"]),
            i["type_text"],
        ),
        "system": i["system"],
        "value": i["value"],
        "period": _period(i["period_start"], i["period_end"]),
        "assigner": _ref(i, "assigner"),
    }


def _annotation(n):
    note = {"time": _iso(n["time"]), "text": n["text"]}
    if n["author_string"]:
        note["authorString"] = n["author_string"]
    else:
        author = _prune(_ref(n, "author_reference"))
        if author:
            note["authorReference"] = author
    return note


def _detail(bind, a):
    aid = a["id"]
    kind = a.get("detail_kind_text")
    detail = {
        "kind": _TYPE_NAMES.get(str(kind).upper(), kind) if kind else None,
        "instantiatesCanonical": list(a["detail_instantiates_canonical"] or []),
        "instantiatesUri": list(a["detail_instantiates_uri"] or []),
        "code": _concept(
            _rows_of(bind, f"{P}_activity_detail_code_coding", "activity_id", aid),
            a["detail_code_text"],
        ),
        "reasonCode": [
            _concept(
                _rows_of(
                    bind,
                    f"{P}_activity_detail_reason_code_coding",
                    "reason_code_id",
                    rc["id"],
                ),
                rc["text"],
            )
            for rc in _rows_of(
                bind, f"{P}_activity_detail_reason_code", "activity_id", aid
            )
        ],
        "reasonReference": [
            _ref(x, "reference")
            for x in _rows_of(
                bind, f"{P}_activity_detail_reason_reference", "activity_id", aid
            )
        ],
        "goal": [
            _ref(x, "reference")
            for x in _rows_of(bind, f"{P}_activity_detail_goal", "activity_id", aid)
        ],
        "status": _hyphenate(a.get("detail_status_text")),
        "statusReason": _concept(
            _rows_of(
                bind, f"{P}_activity_detail_status_reason_coding", "activity_id", aid
            ),
            a["detail_status_reason_text"],
        ),
        "doNotPerform": a["detail_do_not_perform"],
        "scheduledTiming": _json(a["detail_scheduled_timing"]),
        "location": _ref(a, "detail_location"),
        "performer": [
            _ref(x, "reference")
            for x in _rows_of(
                bind, f"{P}_activity_detail_performer", "activity_id", aid
            )
        ],
        "productReference": _ref(a, "detail_product"),
        "dailyAmount": _quantity(a, "detail_daily_amount"),
        "quantity": _quantity(a, "detail_quantity"),
        "description": a["detail_description"],
    }
    if a["detail_scheduled_period_start"] or a["detail_scheduled_period_end"]:
        detail["scheduledPeriod"] = _period(
            a["detail_scheduled_period_start"], a["detail_scheduled_period_end"]
        )
    if a["detail_scheduled_string"]:
        detail["scheduledString"] = a["detail_scheduled_string"]
    product = _concept(
        _rows_of(bind, f"{P}_activity_detail_product_coding", "activity_id", aid),
        a["detail_product_codeable_concept_text"],
    )
    if _prune(product):
        detail["productCodeableConcept"] = product
    return detail


def _activity(bind, a):
    aid = a["id"]
    return {
        "outcomeCodeableConcept": [
            _concept(
                _rows_of(
                    bind,
                    f"{P}_activity_outcome_cc_coding",
                    "outcome_cc_id",
                    c["id"],
                ),
                c["text"],
            )
            for c in _rows_of(bind, f"{P}_activity_outcome_cc", "activity_id", aid)
        ],
        "outcomeReference": [
            _ref(x, "reference")
            for x in _rows_of(bind, f"{P}_activity_outcome_reference", "activity_id", aid)
        ],
        "progress": [
            _annotation(x)
            for x in _rows_of(bind, f"{P}_activity_progress", "activity_id", aid)
        ],
        "reference": _ref(a, "reference"),
        "detail": _detail(bind, a),
    }


def _build_content(bind, r):
    pk = r["id"]
    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": [
            _identifier(bind, i) for i in _rows_of(bind, f"{P}_identifier", f"{P}_pk", pk)
        ],
        "instantiatesCanonical": list(r["instantiates_canonical"] or []),
        "instantiatesUri": list(r["instantiates_uri"] or []),
        "basedOn": _refs(bind, f"{P}_based_on", pk),
        "replaces": _refs(bind, f"{P}_replaces", pk),
        "partOf": _refs(bind, f"{P}_part_of", pk),
        "status": _hyphenate(r["status_text"]),
        "intent": _hyphenate(r["intent_text"]),
        "category": [
            _concept(
                _rows_of(bind, f"{P}_category_coding", "category_id", c["id"]),
                c["text"],
            )
            for c in _rows_of(bind, f"{P}_category", f"{P}_pk", pk)
        ],
        "title": r["title"],
        "description": r["description"],
        "subject": _ref(r, "subject"),
        "encounter": _ref(r, "encounter"),
        "period": _period(r["period_start"], r["period_end"]),
        "created": _iso(r["created"]),
        "author": _ref(r, "author"),
        "contributor": _refs(bind, f"{P}_contributor", pk),
        "careTeam": _refs(bind, f"{P}_care_team", pk),
        "addresses": _refs(bind, f"{P}_addresses", pk),
        "goal": _refs(bind, f"{P}_goal", pk),
        "activity": [
            _activity(bind, a)
            for a in _rows(
                bind,
                f"SELECT *, detail_kind::text AS detail_kind_text, "
                f"detail_status::text AS detail_status_text, "
                f"detail_daily_amount_comparator::text AS detail_daily_amount_comparator_text, "
                f"detail_quantity_comparator::text AS detail_quantity_comparator_text "
                f"FROM {P}_activity WHERE {P}_pk = :v ORDER BY id",
                v=pk,
            )
        ],
        "note": [
            _annotation(n) for n in _rows_of(bind, f"{P}_note", f"{P}_pk", pk)
        ],
    }
    return _prune(content)


def _backfill_content(bind):
    # `status` / `intent` are enums: cast them to text so the driver returns the label.
    for r in _rows(
        bind,
        f"SELECT *, status::text AS status_text, intent::text AS intent_text FROM {P}",
    ):
        bind.execute(
            sa.text(f"UPDATE {P} SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {
                "c": json.dumps(_build_content(bind, dict(r)), default=str),
                "id": r["id"],
            },
        )


# -- upgrade: content -> search index (frozen copy of _indexer.py) --------------------------

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_SUBJECT_TYPES = ("Patient", "Group")
_ENCOUNTER_TYPES = ("Encounter",)
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
_ACTIVITY_TYPES = (
    "Appointment",
    "CommunicationRequest",
    "DeviceRequest",
    "MedicationRequest",
    "NutritionOrder",
    "Task",
    "ServiceRequest",
    "VisionPrescription",
    "RequestGroup",
)
_REFERENCE_PARAMS = (
    ("based-on", "basedOn", ("CarePlan",)),
    ("replaces", "replaces", ("CarePlan",)),
    ("part-of", "partOf", ("CarePlan",)),
    ("care-team", "careTeam", ("CareTeam",)),
    ("condition", "addresses", ("Condition",)),
    ("goal", "goal", ("Goal",)),
)
_CANONICAL_TYPES = (
    "PlanDefinition",
    "Questionnaire",
    "Measure",
    "ActivityDefinition",
    "OperationDefinition",
)


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


def _insert_identifier(bind, pk, identifier):
    if not (identifier.get("system") or identifier.get("value")):
        return
    itype = identifier.get("type") or {}
    for c in itype.get("coding") or [{}]:
        bind.execute(
            sa.text(
                f"INSERT INTO {P}_identifier ({P}_pk, system, value, type_system, type_code, "
                "type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"
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


def _insert_reference(bind, pk, param, ref, allowed):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return
    rtype, rid = _typed(reference, allowed)
    bind.execute(
        sa.text(
            f"INSERT INTO {P}_reference ({P}_pk, param, reference_reference, reference_type, "
            "reference_id, reference_identifier_system, reference_identifier_value) "
            "VALUES (:pk, :param, :r, :t, :i, :s, :v)"
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


def _insert_ref_row(bind, table, pk, ref, allowed, **extra):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    rtype, rid = _typed(reference, allowed)
    cols = {
        f"{P}_pk": pk,
        "reference_reference": reference,
        "reference_type": rtype,
        "reference_id": rid,
        "reference_identifier_system": identifier.get("system"),
        "reference_identifier_value": identifier.get("value"),
        **extra,
    }
    names = ", ".join(cols)
    marks = ", ".join(f":{k}" for k in cols)
    bind.execute(sa.text(f"INSERT INTO {table} ({names}) VALUES ({marks})"), cols)


def _scheduled_bounds(detail):
    if detail.get("scheduledPeriod"):
        return _period_bounds(detail["scheduledPeriod"])
    timing = detail.get("scheduledTiming")
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
        start, end = _period_bounds(doc.get("period"))
        status, intent = doc.get("status"), doc.get("intent")
        columns = {
            "period_start": start,
            "period_end": end,
            **_ref_params("subject", doc.get("subject"), _SUBJECT_TYPES),
            **_ref_params("encounter", doc.get("encounter"), _ENCOUNTER_TYPES),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(
                f"UPDATE {P} SET status = CAST(:status AS care_plan_status), "
                f"intent = CAST(:intent AS care_plan_intent), {sets} WHERE id = :pk"
            ),
            {
                **columns,
                "status": status if status in _STATUS else None,
                "intent": intent if intent in _INTENT else None,
                "pk": pk,
            },
        )

        for i in doc.get("identifier") or []:
            _insert_identifier(bind, pk, i)
        for category in doc.get("category") or []:
            _insert_token(bind, pk, "category", category)
        for param, element, allowed in _REFERENCE_PARAMS:
            for ref in doc.get(element) or []:
                _insert_reference(bind, pk, param, ref, allowed)
        for canonical in doc.get("instantiatesCanonical") or []:
            _insert_reference(
                bind,
                pk,
                "instantiates-canonical",
                {"reference": canonical},
                _CANONICAL_TYPES,
            )
        for uri in doc.get("instantiatesUri") or []:
            if uri:
                bind.execute(
                    sa.text(
                        f"INSERT INTO {P}_instantiates_uri ({P}_pk, uri) VALUES (:pk, :u)"
                    ),
                    {"pk": pk, "u": uri},
                )
        for activity in doc.get("activity") or []:
            activity = activity or {}
            detail = activity.get("detail") or {}
            _insert_token(bind, pk, "activity-code", detail.get("code"))
            for performer in detail.get("performer") or []:
                performer = performer or {}
                if performer.get("reference") or (performer.get("identifier") or {}).get(
                    "value"
                ):
                    _insert_ref_row(
                        bind, f"{P}_performer", pk, performer, _PERFORMER_TYPES
                    )
            ref = activity.get("reference") or {}
            sched_start, sched_end = _scheduled_bounds(detail)
            if (
                ref.get("reference")
                or (ref.get("identifier") or {}).get("value")
                or sched_start
                or sched_end
            ):
                _insert_ref_row(
                    bind,
                    f"{P}_activity",
                    pk,
                    ref,
                    _ACTIVITY_TYPES,
                    scheduled_start=sched_start,
                    scheduled_end=sched_end,
                )


# Every old CarePlan table, including the activity tree. The new index tables (identifier,
# activity) are dropped with them and recreated below; dropped with CASCADE, so order does not
# matter.
_OLD_TABLES = (
    "care_plan_identifier_type_coding",
    "care_plan_identifier",
    "care_plan_category_coding",
    "care_plan_category",
    "care_plan_based_on",
    "care_plan_replaces",
    "care_plan_part_of",
    "care_plan_contributor",
    "care_plan_care_team",
    "care_plan_addresses",
    "care_plan_goal",
    "care_plan_note",
    "care_plan_activity_outcome_cc_coding",
    "care_plan_activity_outcome_cc",
    "care_plan_activity_outcome_reference",
    "care_plan_activity_progress",
    "care_plan_activity_detail_code_coding",
    "care_plan_activity_detail_reason_code_coding",
    "care_plan_activity_detail_reason_code",
    "care_plan_activity_detail_reason_reference",
    "care_plan_activity_detail_goal",
    "care_plan_activity_detail_status_reason_coding",
    "care_plan_activity_detail_performer",
    "care_plan_activity_detail_product_coding",
    "care_plan_activity",
)

# The per-field enums of the old schema (the shared `identifier_use`, `organization_reference_type`
# enums stay). `care_plan_status` and `care_plan_intent` are recreated below with the real codes.
_OLD_ENUMS = (
    "care_plan_status",
    "care_plan_intent",
    "care_plan_activity_status",
    "care_plan_activity_kind",
    "care_plan_quantity_comparator",
    "care_plan_subject_reference_type",
    "care_plan_encounter_reference_type",
    "care_plan_author_reference_type",
    "care_plan_contributor_reference_type",
    "care_plan_care_team_reference_type",
    "care_plan_addresses_reference_type",
    "care_plan_goal_reference_type",
    "care_plan_based_on_reference_type",
    "care_plan_replaces_reference_type",
    "care_plan_part_of_reference_type",
    "care_plan_activity_reference_type",
    "care_plan_activity_detail_performer_reference_type",
    "care_plan_activity_detail_reason_reference_type",
    "care_plan_location_reference_type",
    "care_plan_product_reference_type",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns, the period and the
# subject / encounter index columns (their reference-type enums become plain strings).
_KEEP = {
    "id",
    "care_plan_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
    "period_start",
    "period_end",
    *(
        f"{ref}_{part}"
        for ref in ("subject", "encounter")
        for part in ("reference", "type", "id", "identifier_system", "identifier_value")
    ),
}


def _fk():
    return sa.Column(
        f"{P}_pk", sa.BigInteger(), sa.ForeignKey(f"{P}.id"), nullable=False
    )


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

    # The subject / encounter types were enums; they are plain strings now.
    for column in ("subject_type", "encounter_type"):
        op.alter_column(
            P,
            column,
            type_=sa.String(),
            nullable=True,
            postgresql_using=f"{column}::text",
        )
    for name in _OLD_ENUMS:
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # Care plans are searched by subject: one index on the pair instead of the lone id.
    op.execute(f"DROP INDEX IF EXISTS ix_{P}_subject_id")
    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {P} ALTER COLUMN care_plan_id SET DEFAULT nextval('care_plan_pub_seq')"
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
    op.execute(f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS care_plan_care_plan_id_key")
    for column in ("tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)

    # status / intent: recreated as enums holding the real FHIR codes.
    postgresql.ENUM(*_STATUS, name="care_plan_status").create(bind, checkfirst=True)
    postgresql.ENUM(*_INTENT, name="care_plan_intent").create(bind, checkfirst=True)
    op.add_column(
        P,
        sa.Column(
            "status",
            postgresql.ENUM(*_STATUS, name="care_plan_status", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        P,
        sa.Column(
            "intent",
            postgresql.ENUM(*_INTENT, name="care_plan_intent", create_type=False),
            nullable=True,
        ),
    )
    op.create_index("ix_care_plan_period", P, ["period_start", "period_end"])
    op.create_index("ix_care_plan_subject_type_id", P, ["subject_type", "subject_id"])

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
    op.create_index("ix_care_plan_token_param_code", f"{P}_token", ["param", "code"])

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
        "ix_care_plan_reference_param_type_id",
        f"{P}_reference",
        ["param", "reference_type", "reference_id"],
    )

    op.create_table(
        f"{P}_instantiates_uri",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("uri", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_instantiates_uri", f"{P}_pk")
    _index(f"{P}_instantiates_uri", "uri")

    op.create_table(
        f"{P}_performer",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        *_reference_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_performer", f"{P}_pk")
    op.create_index(
        "ix_care_plan_performer_type_id",
        f"{P}_performer",
        ["reference_type", "reference_id"],
    )

    op.create_table(
        f"{P}_activity",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        *_reference_columns(),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_activity", f"{P}_pk")
    op.create_index(
        "ix_care_plan_activity_type_id",
        f"{P}_activity",
        ["reference_type", "reference_id"],
    )
    op.create_index(
        "ix_care_plan_activity_scheduled",
        f"{P}_activity",
        ["scheduled_start", "scheduled_end"],
    )

    _rebuild_index(bind)
    for column in ("id", "encounter_id", "status", "intent"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "care_plan content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
