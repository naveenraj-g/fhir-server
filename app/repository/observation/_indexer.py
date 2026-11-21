"""
FHIR Observation document -> search index. The only write-side mapper.

Observation's whole resource is stored verbatim in ObservationModel.content; this module
derives every *other* column and child row from it — exactly the values the FHIR R4
Observation search parameters filter on
(https://www.hl7.org/fhir/R4/observation.html#search), nothing more. See ObservationModel's
docstring for the parameter -> storage table; the shared builders are in
app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.

The Observation itself is "slot" 0 and its n-th component is slot n: every token and value row
records its slot, so a composite search can pair a code with a value of the same element.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from functools import partial

from app.fhir.search.values import normalize
from app.models.observation import (
    BASED_ON_TYPES,
    DERIVED_FROM_TYPES,
    DEVICE_TYPES,
    HAS_MEMBER_TYPES,
    PART_OF_TYPES,
    PERFORMER_TYPES,
    SUBJECT_TYPES,
    ObservationIdentifier,
    ObservationReference,
    ObservationStatus,
    ObservationToken,
    ObservationValue,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    relative,
    type_rows,
)

from ._shared import any_typed, typed

_STATUSES = {m.value for m in ObservationStatus}
_AUTHOR_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "Patient",
    "RelatedPerson",
    "Organization",
)


# The resources already rebuilt on the engine — the only targets whose existence is checked on
# write (the others are stored as sent until they are rebuilt).
_REBUILT = (
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "Location",
    "RelatedPerson",
    "Encounter",
    "Appointment",
    "Condition",
    "Procedure",
    "DiagnosticReport",
    "AllergyIntolerance",
    "Immunization",
    "ImmunizationRecommendation",
    "ImmunizationEvaluation",
    "FamilyMemberHistory",
    "RiskAssessment",
    "ClinicalImpression",
    "DetectedIssue",
    "Observation",
)


def _registered(types: tuple[str, ...]) -> tuple[str, ...]:
    """The targets of an element that are rebuilt resources on this server."""
    return tuple(t for t in types if t in _REBUILT)


def local_references(document: dict) -> list[tuple[str, str, str]]:
    """(element label, resource type, relative reference) for every local reference that must
    exist in the caller's org on write: identifier.assigner, `subject` (a Patient or Location),
    `encounter`, every `basedOn`, `partOf`, `performer`, `hasMember`, `derivedFrom` and note
    `authorReference` whose type is a rebuilt resource. Absolute URLs, logical (identifier-only)
    references and targets that are not rebuilt resources (a Group, Device or Specimen, an
    ImagingStudy, a Media, a MedicationRequest, a ServiceRequest, `focus` — Reference(Any)) point
    elsewhere and are not checked."""
    refs = []

    def add(label, reference, resource_type):
        local = relative(reference, resource_type)
        if local:
            refs.append((label, resource_type, local))

    def add_typed(label, ref, allowed):
        parsed = typed((ref or {}).get("reference"), _registered(allowed))
        if parsed:
            refs.append((label, parsed[0], ref["reference"]))

    for identifier in document.get("identifier") or []:
        add(
            "identifier.assigner",
            (identifier.get("assigner") or {}).get("reference"),
            "Organization",
        )
    add_typed("subject", document.get("subject"), SUBJECT_TYPES)
    add("encounter", (document.get("encounter") or {}).get("reference"), "Encounter")
    for element, types in (
        ("basedOn", BASED_ON_TYPES),
        ("partOf", PART_OF_TYPES),
        ("performer", PERFORMER_TYPES),
        ("hasMember", HAS_MEMBER_TYPES),
        ("derivedFrom", DERIVED_FROM_TYPES),
    ):
        for ref in document.get(element) or []:
            add_typed(element, ref, types)
    for note in document.get("note") or []:
        add_typed(
            "note.authorReference", (note or {}).get("authorReference"), _AUTHOR_TYPES
        )
    return refs


def _ref_columns(prefix: str, ref: dict | None, allowed: tuple[str, ...]) -> dict:
    """The index columns of one 0..1 Reference: `{prefix}_reference` (the raw
    string), `{prefix}_type`/`{prefix}_id` (a relative `Type/<id>` of an
    allowed type) and `{prefix}_identifier_system`/`_value`."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    parsed = typed(reference, allowed)
    return {
        f"{prefix}_reference": reference,
        f"{prefix}_type": parsed[0] if parsed else None,
        f"{prefix}_id": parsed[1] if parsed else None,
        f"{prefix}_identifier_system": identifier.get("system"),
        f"{prefix}_identifier_value": identifier.get("value"),
    }


def _point(value):
    """The half-open range a dateTime / instant covers, or (None, None)."""
    return period_bounds({"start": value, "end": value}) if value else (None, None)


def _effective_bounds(document: dict):
    """The range effective[x] covers: a dateTime / instant as the range of its precision, a
    Period from its start to the instant after its end (NULL = open), a Timing from its earliest
    event to the instant after its latest (else its `repeat.boundsPeriod`)."""
    for key in ("effectiveDateTime", "effectiveInstant"):
        if document.get(key):
            return _point(document[key])
    if document.get("effectivePeriod"):
        return period_bounds(document["effectivePeriod"])
    timing = document.get("effectiveTiming")
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
        return period_bounds((timing.get("repeat") or {}).get("boundsPeriod"))
    return None, None


def index_columns(document: dict) -> dict:
    """Search columns on the observation row itself."""
    start, end = _effective_bounds(document)
    status = document.get("status")
    return {
        "status": ObservationStatus(status) if status in _STATUSES else None,
        "date_start": start,
        "date_end": end,
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("encounter", document.get("encounter"), ("Encounter",)),
        **_ref_columns("specimen", document.get("specimen"), ("Specimen",)),
        **_ref_columns("device", document.get("device"), DEVICE_TYPES),
    }


# ── tokens and values, element by element ────────────────────────────────────


def _concept(param: str, slot: int, concept: dict | None) -> list:
    return (
        type_rows(partial(ObservationToken, param=param, slot=slot), concept)
        if concept
        else []
    )


def _number(value) -> Decimal | None:
    """A JSON number as a Decimal (None if absent or not a number — the validator rejects a bad
    value before we get here)."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def _value_rows(
    element: dict, slot: int, quantity_param: str, *, searchable_text: bool
) -> list:
    """The ObservationValue rows of one element's value[x]: its Quantity, and (for the
    Observation only) its string / CodeableConcept text and dateTime / Period."""
    rows = []
    quantity = element.get("valueQuantity")
    if quantity and _number(quantity.get("value")) is not None:
        rows.append(
            ObservationValue(
                param=quantity_param,
                slot=slot,
                quantity_value=_number(quantity["value"]),
                quantity_system=quantity.get("system"),
                quantity_code=quantity.get("code"),
                quantity_unit=quantity.get("unit"),
            )
        )
    if not searchable_text:
        return rows
    for text in (
        element.get("valueString"),
        (element.get("valueCodeableConcept") or {}).get("text"),
    ):
        if text:
            rows.append(
                ObservationValue(
                    param="value-string", slot=slot, string_norm=normalize(text)
                )
            )
    if element.get("valueDateTime"):
        start, end = _point(element["valueDateTime"])
        rows.append(
            ObservationValue(
                param="value-date", slot=slot, date_start=start, date_end=end
            )
        )
    elif element.get("valuePeriod"):
        start, end = period_bounds(element["valuePeriod"])
        rows.append(
            ObservationValue(
                param="value-date", slot=slot, date_start=start, date_end=end
            )
        )
    return rows


def _token_rows(document: dict) -> list:
    rows = []
    for concept in document.get("category") or []:
        rows += _concept("category", 0, concept)
    rows += _concept("code", 0, document.get("code"))
    rows += _concept("method", 0, document.get("method"))
    rows += _concept("data-absent-reason", 0, document.get("dataAbsentReason"))
    rows += _concept("value-concept", 0, document.get("valueCodeableConcept"))
    for slot, component in enumerate(document.get("component") or [], start=1):
        component = component or {}
        rows += _concept("component-code", slot, component.get("code"))
        rows += _concept(
            "component-data-absent-reason", slot, component.get("dataAbsentReason")
        )
        rows += _concept(
            "component-value-concept", slot, component.get("valueCodeableConcept")
        )
    return rows


def _all_value_rows(document: dict) -> list:
    rows = _value_rows(document, 0, "value-quantity", searchable_text=True)
    for slot, component in enumerate(document.get("component") or [], start=1):
        rows += _value_rows(
            component or {}, slot, "component-value-quantity", searchable_text=False
        )
    return rows


def _reference_row(param: str, ref: dict | None) -> ObservationReference | None:
    """One index row for a Reference with a `reference` or an `identifier` (display-only cannot be
    matched by a reference search). Any relative `Type/<id>` names a type."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = any_typed(reference)
    return ObservationReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


_REFERENCE_ELEMENTS = (
    ("based-on", "basedOn"),
    ("part-of", "partOf"),
    ("focus", "focus"),
    ("has-member", "hasMember"),
    ("derived-from", "derivedFrom"),
    ("performer", "performer"),
)


def _reference_rows(document: dict) -> list:
    rows = [
        _reference_row(param, ref)
        for param, element in _REFERENCE_ELEMENTS
        for ref in document.get(element) or []
    ]
    return [r for r in rows if r]


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by ObservationModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(ObservationIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "values": _all_value_rows(document),
        "references": _reference_rows(document),
    }
