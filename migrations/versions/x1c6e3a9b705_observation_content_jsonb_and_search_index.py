"""observation: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: x1c6e3a9b705
Revises: w0b5d2f8a614
Create Date: 2026-12-10 10:00:00.000000

Medplum-style storage for Observation (see ObservationModel's docstring), same as the other
resources already moved (Organization 5b1969c2ec19, Location 8c41d2e7a9b3, Practitioner
a7d3f19c2b64, HealthcareService c9f5b2d7e813, Endpoint d1a6c3e8f924, PractitionerRole
e2b7d4f9a035, Schedule f3c8e5a1b947, Slot g4d9f6b2c058, Patient h5e0a7c3d169, Appointment
i6f1b8d4e27a, AppointmentResponse j7a2c9e5f381, Encounter k8b3d0f6a492, RelatedPerson
l9c4e1a7b503, AllergyIntolerance m0d5f2b8c614, Condition n1e6a3c9d725, Procedure
o2f7b4d0e836, DiagnosticReport p3a8c5e1f947, Immunization q4b9d6f2a058,
ImmunizationRecommendation r5c0e7a3b169, ImmunizationEvaluation s6d1f8b4c270,
FamilyMemberHistory t7e2a9c5d381, RiskAssessment u8f3b0d6e492, ClinicalImpression
v9a4c1e7f503, DetectedIssue w0b5d2f8a614). The whole FHIR resource moves into
`observation.content`; every column/table that survives is a search index for one of the FHIR R4
Observation search parameters (or `_id` / `_lastUpdated`), derived from `content`:

  observation: status (recreated as an enum holding the real FHIR codes - the old one stored
      `entered_in_error`), date_start/_end (`effective[x]`, the range it covers) and the
      subject_*, encounter_*, specimen_* and device_* reference columns (`*_type` becomes a
      plain string); the public id gets its sequence as a server default; new: content.
  observation_identifier: rebuilt as an index table
  observation_token: new - category, code, method, data-absent-reason, value-concept and the
      component-code / component-data-absent-reason / component-value-concept forms, each row
      carrying a `slot` (0 = the Observation, n = its n-th component)
  observation_value: new - value-quantity, component-value-quantity, value-string and value-date
      rows, also by `slot`
  observation_reference: new - based-on, part-of, focus, has-member, derived-from, performer
  dropped: every old child table (the coding tables of code / value / data absent reason / body
      site / method, identifier, based on, part of, category, focus, performer, interpretation,
      note, reference range, has member, derived from and the whole component tree), every
      main-table column with no search parameter (the flattened value[x] and effective[x],
      issued, every concept's text, extension and the display / logical-identifier details of
      every reference) and the per-field `observation_*` enums (the shared
      `encounter_reference_type` stays).

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_observation() logic (but keeping a reference's raw string, so an
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
from decimal import Decimal, InvalidOperation
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'x1c6e3a9b705'
down_revision: Union[str, None] = 'w0b5d2f8a614'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "observation"

_STATUS = ('registered', 'preliminary', 'final', 'amended', 'corrected', 'cancelled', 'entered-in-error', 'unknown')


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


def _point(value):
    return _period_bounds({"start": value, "end": value}) if value else (None, None)


# ── upgrade: old columns/tables -> content (frozen copy of the old mapper) ───

_TYPE_NAMES = {t.upper(): t for t in (
    "Patient", "Group", "Device", "Location", "Encounter", "Specimen", "DeviceMetric", "CarePlan", "DeviceRequest",
    "ImmunizationRecommendation", "MedicationRequest", "NutritionOrder", "ServiceRequest", "MedicationAdministration",
    "MedicationDispense", "MedicationStatement", "Procedure", "Immunization", "ImagingStudy", "Practitioner",
    "PractitionerRole", "Organization", "CareTeam", "RelatedPerson", "Observation", "QuestionnaireResponse",
    "MolecularSequence", "DocumentReference", "Media")}
_COMPARATORS = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}


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


def _num(value):
    return float(value) if value is not None else None


def _quantity(row, prefix, comparator=False):
    quantity = {"value": _num(row[f"{prefix}_value"]), "unit": row[f"{prefix}_unit"],
                "system": row[f"{prefix}_system"], "code": row[f"{prefix}_code"]}
    if comparator and row.get(f"{prefix}_comparator"):
        quantity["comparator"] = _COMPARATORS.get(str(row[f"{prefix}_comparator"]).lower())
    quantity = {k: v for k, v in quantity.items() if v is not None}
    return quantity or None


def _value_x(bind, row, out, value_cc_table, fk):
    """The 11-variant value[x] choice, shared by the Observation and its components (the first
    variant that has data wins, in the old mapper's order)."""
    quantity = _quantity(row, "value_quantity", comparator=True)
    if quantity:
        out["valueQuantity"] = quantity
        return
    cc = _concept(_rows_of(bind, value_cc_table, fk, row["id"]), row["value_codeable_concept_text"])
    if _prune(cc):
        out["valueCodeableConcept"] = cc
        return
    if row["value_string"]:
        out["valueString"] = row["value_string"]
        return
    if row["value_boolean"] is not None:
        out["valueBoolean"] = row["value_boolean"]
        return
    if row["value_integer"] is not None:
        out["valueInteger"] = row["value_integer"]
        return
    low, high = _quantity(row, "value_range_low"), _quantity(row, "value_range_high")
    if low or high:
        out["valueRange"] = {"low": low, "high": high}
        return
    numerator = _quantity(row, "value_ratio_numerator", comparator=True)
    denominator = _quantity(row, "value_ratio_denominator", comparator=True)
    if numerator or denominator:
        out["valueRatio"] = {"numerator": numerator, "denominator": denominator}
        return
    origin = _quantity(row, "value_sampled_data_origin")
    if origin or row["value_sampled_data_period"] is not None or row["value_sampled_data_dimensions"] is not None:
        out["valueSampledData"] = {
            "origin": origin, "period": _num(row["value_sampled_data_period"]),
            "factor": _num(row["value_sampled_data_factor"]), "lowerLimit": _num(row["value_sampled_data_lower_limit"]),
            "upperLimit": _num(row["value_sampled_data_upper_limit"]),
            "dimensions": row["value_sampled_data_dimensions"], "data": row["value_sampled_data_data"],
        }
        return
    if row["value_time"]:
        out["valueTime"] = _iso(row["value_time"])
        return
    if row["value_date_time"]:
        out["valueDateTime"] = _iso(row["value_date_time"])
        return
    if row["value_period_start"] or row["value_period_end"]:
        out["valuePeriod"] = _period(row["value_period_start"], row["value_period_end"])


def _reference_range(bind, rr, prefix):
    """One reference range (`prefix` is `observation` or `observation_component`)."""
    fk = f"{prefix}_reference_range_id"
    applies = []
    for a in _rows_of(bind, f"{prefix}_reference_range_applies_to", fk, rr["id"]):
        applies.append(_concept(
            _rows_of(bind, f"{prefix}_reference_range_applies_to_coding",
                     f"{prefix}_reference_range_applies_to_id", a["id"]), a["text"]))
    return {
        "low": _quantity(rr, "low"), "high": _quantity(rr, "high"),
        "type": _concept(_rows_of(bind, f"{prefix}_reference_range_type_coding", fk, rr["id"]), rr["type_text"]),
        "appliesTo": applies,
        "age": {"low": _quantity(rr, "age_low"), "high": _quantity(rr, "age_high")},
        "text": rr["text"],
    }


def _component(bind, c):
    cid = c["id"]
    entry = {"code": _concept(_rows_of(bind, f"{P}_component_code_coding", f"{P}_component_id", cid), c["code_text"])}
    _value_x(bind, c, entry, f"{P}_component_value_codeable_concept_coding", f"{P}_component_id")
    entry["dataAbsentReason"] = _concept(
        _rows_of(bind, f"{P}_component_data_absent_reason_coding", f"{P}_component_id", cid),
        c["data_absent_reason_text"])
    entry["interpretation"] = [
        _concept(_rows_of(bind, f"{P}_component_interpretation_coding", f"{P}_component_interpretation_id", i["id"]),
                 i["text"])
        for i in _rows_of(bind, f"{P}_component_interpretation", f"{P}_component_id", cid)
    ]
    entry["referenceRange"] = [
        _reference_range(bind, rr, f"{P}_component")
        for rr in _rows_of(bind, f"{P}_component_reference_range", f"{P}_component_id", cid)
    ]
    return entry


def _note(n):
    note = {"time": _iso(n["time"]), "text": n["text"]}
    if n["author_string"]:
        note["authorString"] = n["author_string"]
    else:
        author = _prune(_ref(n, "author"))
        if author:
            note["authorReference"] = author
    return note


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
            "assigner": _ref(i, "assigner"),
        })

    def refs(table):
        return [_ref(x, "reference") for x in _rows_of(bind, f"{P}_{table}", f"{P}_pk", pk)]

    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": identifiers,
        "basedOn": refs("based_on"),
        "partOf": refs("part_of"),
        "status": _hyphenate(r["status_text"]),
        "category": [
            _concept(_rows_of(bind, f"{P}_category_coding", f"{P}_category_id", c["id"]), c["text"])
            for c in _rows_of(bind, f"{P}_category", f"{P}_pk", pk)
        ],
        "code": _concept(_rows_of(bind, f"{P}_code_coding", f"{P}_pk", pk), r["code_text"]),
        "subject": _ref(r, "subject"),
        "focus": refs("focus"),
        "encounter": _ref(r, "encounter"),
        "issued": _iso(r["issued"]),
        "performer": refs("performer"),
        "dataAbsentReason": _concept(_rows_of(bind, f"{P}_data_absent_reason_coding", f"{P}_pk", pk),
                                     r["data_absent_reason_text"]),
        "interpretation": [
            _concept(_rows_of(bind, f"{P}_interpretation_coding", f"{P}_interpretation_id", i["id"]), i["text"])
            for i in _rows_of(bind, f"{P}_interpretation", f"{P}_pk", pk)
        ],
        "note": [_note(n) for n in _rows_of(bind, f"{P}_note", f"{P}_pk", pk)],
        "bodySite": _concept(_rows_of(bind, f"{P}_body_site_coding", f"{P}_pk", pk), r["body_site_text"]),
        "method": _concept(_rows_of(bind, f"{P}_method_coding", f"{P}_pk", pk), r["method_text"]),
        "specimen": _ref(r, "specimen"),
        "device": _ref(r, "device"),
        "referenceRange": [
            _reference_range(bind, rr, P) for rr in _rows_of(bind, f"{P}_reference_range", f"{P}_pk", pk)
        ],
        "hasMember": refs("has_member"),
        "derivedFrom": refs("derived_from"),
        "component": [_component(bind, c) for c in _rows_of(bind, f"{P}_component", f"{P}_pk", pk)],
    }
    _value_x(bind, r, content, f"{P}_value_codeable_concept_coding", f"{P}_pk")
    if r["effective_date_time"]:
        content["effectiveDateTime"] = _iso(r["effective_date_time"])
    elif r["effective_period_start"] or r["effective_period_end"]:
        content["effectivePeriod"] = _period(r["effective_period_start"], r["effective_period_end"])
    elif r["effective_timing"]:
        content["effectiveTiming"] = dict(_json(r["effective_timing"]))
    elif r["effective_instant"]:
        content["effectiveInstant"] = _iso(r["effective_instant"])
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
_SUBJECT_TYPES = ("Patient", "Group", "Device", "Location")
_DEVICE_TYPES = ("Device", "DeviceMetric")


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


def _effective_bounds(doc):
    for key in ("effectiveDateTime", "effectiveInstant"):
        if doc.get(key):
            return _point(doc[key])
    if doc.get("effectivePeriod"):
        return _period_bounds(doc["effectivePeriod"])
    timing = doc.get("effectiveTiming")
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


def _insert_token(bind, pk, param, slot, concept):
    if not concept:
        return
    text = _norm(concept.get("text"))
    codings = [c for c in concept.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
    for c in codings or ([{}] if text else []):
        bind.execute(sa.text(
            f"INSERT INTO {P}_token ({P}_pk, param, slot, system, code, display_norm, text_norm) "
            "VALUES (:pk, :param, :slot, :s, :c, :d, :t)"),
            {"pk": pk, "param": param, "slot": slot, "s": c.get("system"), "c": c.get("code"),
             "d": _norm(c.get("display")), "t": text})


def _number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def _insert_value(bind, pk, param, slot, **cols):
    names = ["quantity_value", "quantity_system", "quantity_code", "quantity_unit", "string_norm", "date_start",
             "date_end"]
    bind.execute(sa.text(
        f"INSERT INTO {P}_value ({P}_pk, param, slot, {', '.join(names)}) "
        f"VALUES (:pk, :param, :slot, {', '.join(':' + n for n in names)})"),
        {"pk": pk, "param": param, "slot": slot, **{n: cols.get(n) for n in names}})


def _insert_values(bind, pk, element, slot, quantity_param, with_text):
    quantity = element.get("valueQuantity")
    if quantity and _number(quantity.get("value")) is not None:
        _insert_value(bind, pk, quantity_param, slot, quantity_value=_number(quantity["value"]),
                      quantity_system=quantity.get("system"), quantity_code=quantity.get("code"),
                      quantity_unit=quantity.get("unit"))
    if not with_text:
        return
    for text in (element.get("valueString"), (element.get("valueCodeableConcept") or {}).get("text")):
        if text:
            _insert_value(bind, pk, "value-string", slot, string_norm=_norm(text))
    if element.get("valueDateTime"):
        start, end = _point(element["valueDateTime"])
        _insert_value(bind, pk, "value-date", slot, date_start=start, date_end=end)
    elif element.get("valuePeriod"):
        start, end = _period_bounds(element["valuePeriod"])
        _insert_value(bind, pk, "value-date", slot, date_start=start, date_end=end)


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


_REFERENCE_ELEMENTS = (("based-on", "basedOn"), ("part-of", "partOf"), ("focus", "focus"),
                       ("has-member", "hasMember"), ("derived-from", "derivedFrom"), ("performer", "performer"))


def _rebuild_index(bind):
    for row in _rows(bind, f"SELECT id, content FROM {P}"):
        pk, doc = row["id"], _json(row["content"])

        start, end = _effective_bounds(doc)
        status = doc.get("status")
        columns = {
            "date_start": start, "date_end": end,
            **_ref_params("subject", doc.get("subject"), _SUBJECT_TYPES),
            **_ref_params("encounter", doc.get("encounter"), ("Encounter",)),
            **_ref_params("specimen", doc.get("specimen"), ("Specimen",)),
            **_ref_params("device", doc.get("device"), _DEVICE_TYPES),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(sa.text(f"UPDATE {P} SET status = CAST(:status AS observation_status), {sets} WHERE id = :pk"),
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

        for concept in doc.get("category") or []:
            _insert_token(bind, pk, "category", 0, concept)
        _insert_token(bind, pk, "code", 0, doc.get("code"))
        _insert_token(bind, pk, "method", 0, doc.get("method"))
        _insert_token(bind, pk, "data-absent-reason", 0, doc.get("dataAbsentReason"))
        _insert_token(bind, pk, "value-concept", 0, doc.get("valueCodeableConcept"))
        _insert_values(bind, pk, doc, 0, "value-quantity", True)
        for slot, component in enumerate(doc.get("component") or [], start=1):
            component = component or {}
            _insert_token(bind, pk, "component-code", slot, component.get("code"))
            _insert_token(bind, pk, "component-data-absent-reason", slot, component.get("dataAbsentReason"))
            _insert_token(bind, pk, "component-value-concept", slot, component.get("valueCodeableConcept"))
            _insert_values(bind, pk, component, slot, "component-value-quantity", False)
        for param, element in _REFERENCE_ELEMENTS:
            for ref in doc.get(element) or []:
                _insert_reference(bind, pk, param, ref)


# Every old Observation table (NOT `observation_definition*`, which belongs to another resource):
# the new index tables do not exist yet. Dropped with CASCADE, so order does not matter.
_OLD_TABLES = (
    "observation_code_coding", "observation_value_codeable_concept_coding", "observation_data_absent_reason_coding",
    "observation_body_site_coding", "observation_method_coding", "observation_identifier",
    "observation_identifier_type_coding", "observation_based_on", "observation_part_of", "observation_category",
    "observation_category_coding", "observation_focus", "observation_performer", "observation_interpretation",
    "observation_interpretation_coding", "observation_note", "observation_reference_range",
    "observation_reference_range_type_coding", "observation_reference_range_applies_to",
    "observation_reference_range_applies_to_coding", "observation_has_member", "observation_derived_from",
    "observation_component", "observation_component_code_coding", "observation_component_value_codeable_concept_coding",
    "observation_component_data_absent_reason_coding", "observation_component_interpretation",
    "observation_component_interpretation_coding", "observation_component_reference_range",
    "observation_component_reference_range_type_coding", "observation_component_reference_range_applies_to",
    "observation_component_reference_range_applies_to_coding",
)

# The per-field enums of the old schema (the shared `encounter_reference_type` stays). `observation_status`
# is recreated below with the real FHIR codes.
_OLD_ENUMS = (
    "observation_status", "observation_quantity_comparator", "observation_subject_reference_type",
    "observation_based_on_reference_type", "observation_part_of_reference_type",
    "observation_performer_reference_type", "observation_specimen_reference_type",
    "observation_device_reference_type", "observation_has_member_reference_type",
    "observation_derived_from_reference_type", "observation_note_author_reference_type",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns and the index columns of the
# four kept references (their reference-type enums become plain strings). `status` is dropped and recreated.
_KEEP = {
    "id", "observation_id", "tenant_id", "created_by", "updated_by", "created_at", "updated_at", "content",
    *(f"{prefix}_{part}" for prefix in ("subject", "encounter", "specimen", "device")
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

    for table in _OLD_TABLES:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
    existing = [r[0] for r in bind.execute(sa.text(
        f"SELECT column_name FROM information_schema.columns WHERE table_name = '{P}' "
        "AND table_schema = current_schema()"))]
    for column in existing:
        if column not in _KEEP:
            op.drop_column(P, column)

    # The reference types were enums; they are plain strings now.
    for prefix in ('subject', 'encounter', 'specimen', 'device'):
        op.alter_column(P, f'{prefix}_type', type_=sa.String(), nullable=True, postgresql_using=f'{prefix}_type::text')
    for name in _OLD_ENUMS:
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # Observations are searched by patient: one index on the pair instead of the lone id.
    op.execute(f"DROP INDEX IF EXISTS ix_{P}_subject_id")
    # The public id's sequence is now its server default.
    op.execute(f"ALTER TABLE {P} ALTER COLUMN observation_id SET DEFAULT nextval('observation_pub_seq')")

    # status: recreated as an enum holding the real FHIR codes.
    postgresql.ENUM(*_STATUS, name='observation_status').create(bind, checkfirst=True)
    op.add_column(P, sa.Column('status', postgresql.ENUM(*_STATUS, name='observation_status', create_type=False),
                               nullable=True))
    op.add_column(P, sa.Column('date_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column(P, sa.Column('date_end', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_observation_date', P, ['date_start', 'date_end'])
    op.create_index('ix_observation_subject_type_id', P, ['subject_type', 'subject_id'])

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
        sa.Column('slot', sa.Integer(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index(f'{P}_token', f'{P}_pk')
    op.create_index('ix_observation_token_param_code', f'{P}_token', ['param', 'code'])

    op.create_table(
        f'{P}_value',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('param', sa.String(), nullable=False),
        sa.Column('slot', sa.Integer(), nullable=False),
        sa.Column('quantity_value', sa.Numeric(), nullable=True),
        sa.Column('quantity_system', sa.String(), nullable=True),
        sa.Column('quantity_code', sa.String(), nullable=True),
        sa.Column('quantity_unit', sa.String(), nullable=True),
        sa.Column('string_norm', sa.String(), nullable=True),
        sa.Column('date_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('date_end', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index(f'{P}_value', f'{P}_pk')
    op.create_index('ix_observation_value_param_slot', f'{P}_value', ['param', 'slot'])

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
    op.create_index('ix_observation_reference_param_type_id', f'{P}_reference',
                    ['param', 'reference_type', 'reference_id'])

    _rebuild_index(bind)
    for column in ('id', 'encounter_id', 'specimen_id', 'device_id'):
        op.create_index(f'ix_{P}_{column}', P, [column], if_not_exists=True)
    op.create_index('ix_observation_status', P, ['status'], if_not_exists=True)
    op.alter_column(P, 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "observation content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
