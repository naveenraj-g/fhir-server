"""
FHIR Encounter document -> search index. The only write-side mapper.

Encounter's whole resource is stored verbatim in EncounterModel.content; this
module derives every *other* column and child row from it — exactly the values
the FHIR R4 Encounter search parameters filter on
(https://www.hl7.org/fhir/R4/encounter.html#search), nothing more. See
EncounterModel's docstring for the parameter -> storage table; the shared
builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from functools import partial

from app.fhir.search import normalize
from app.models.encounter import (
    PARTICIPANT_TYPES,
    REFERENCE_PARAMS,
    SUBJECT_TYPES,
    EncounterIdentifier,
    EncounterLocation,
    EncounterParticipant,
    EncounterReference,
    EncounterStatus,
    EncounterToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    relative,
    type_rows,
)

from ._shared import MODELED_PARTICIPANT_TYPES, ref_type_and_id, typed


def _elements(document: dict, path: str) -> list:
    """The values at a dotted path through lists: `diagnosis.condition` ->
    every diagnosis's condition."""
    values = [document]
    for key in path.split("."):
        nxt = []
        for v in values:
            item = v.get(key) if isinstance(v, dict) else None
            nxt.extend(item if isinstance(item, list) else [item])
        values = nxt
    return [v for v in values if v is not None]


def local_references(document: dict) -> list[tuple[str, str, str]]:
    """(element label, resource type, relative reference) for every local
    reference that must exist in the caller's org on write: identifier.assigner,
    subject (when a Patient), partOf, serviceProvider, appointment[],
    participant.individual (Practitioner / PractitionerRole), location.location,
    and hospitalization.origin / destination / preAdmissionIdentifier.assigner.
    Absolute URLs, logical (identifier-only) references and targets that are
    not resources on this server (Group, RelatedPerson, Account, EpisodeOfCare,
    ServiceRequest, Condition, ...) point elsewhere and are not checked."""
    refs = []

    def add(label, reference, resource_type):
        local = relative(reference, resource_type)
        if local:
            refs.append((label, resource_type, local))

    for identifier in document.get("identifier") or []:
        add(
            "identifier.assigner",
            (identifier.get("assigner") or {}).get("reference"),
            "Organization",
        )
    add("subject", (document.get("subject") or {}).get("reference"), "Patient")
    add("partOf", (document.get("partOf") or {}).get("reference"), "Encounter")
    add(
        "serviceProvider",
        (document.get("serviceProvider") or {}).get("reference"),
        "Organization",
    )
    for appointment in document.get("appointment") or []:
        add("appointment", appointment.get("reference"), "Appointment")
    for participant in document.get("participant") or []:
        reference = (participant.get("individual") or {}).get("reference")
        parsed = typed(reference, PARTICIPANT_TYPES)
        if parsed and parsed[0] in MODELED_PARTICIPANT_TYPES:
            refs.append(("participant.individual", parsed[0], reference))
    for location in document.get("location") or []:
        add(
            "location.location",
            (location.get("location") or {}).get("reference"),
            "Location",
        )
    for diagnosis in document.get("diagnosis") or []:
        for resource_type in ("Condition", "Procedure"):
            add(
                "diagnosis.condition",
                (diagnosis.get("condition") or {}).get("reference"),
                resource_type,
            )
    for reason in document.get("reasonReference") or []:
        for resource_type in ("Condition", "Procedure"):
            add("reasonReference", reason.get("reference"), resource_type)
    hospitalization = document.get("hospitalization") or {}
    for element in ("origin", "destination"):
        reference = (hospitalization.get(element) or {}).get("reference")
        for resource_type in ("Location", "Organization"):
            add(f"hospitalization.{element}", reference, resource_type)
    pre_admission = hospitalization.get("preAdmissionIdentifier") or {}
    add(
        "hospitalization.preAdmissionIdentifier.assigner",
        (pre_admission.get("assigner") or {}).get("reference"),
        "Organization",
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


def _decimal(value) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:  # the validator rejects a non-number before we get here
        return None


def index_columns(document: dict) -> dict:
    """Search columns on the encounter row itself."""
    status = document.get("status")
    try:
        status = EncounterStatus(status) if status else None
    except ValueError:
        status = None  # the validator rejects a bad code before we get here
    cls = document.get("class") or {}
    period_start, period_end = period_bounds(document.get("period"))
    length = document.get("length") or {}
    return {
        "status": status,
        "class_system": cls.get("system"),
        "class_code": cls.get("code"),
        "class_display_norm": normalize(cls.get("display")),
        "period_start": period_start,
        "period_end": period_end,
        "length_value": _decimal(length.get("value")),
        "length_system": length.get("system"),
        "length_code": length.get("code"),
        "length_unit": length.get("unit"),
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("part_of", document.get("partOf"), ("Encounter",)),
        **_ref_columns(
            "service_provider", document.get("serviceProvider"), ("Organization",)
        ),
    }


def _reference_row(param: str, ref: dict | None) -> EncounterReference | None:
    """One index row for a Reference with a `reference` or an `identifier`
    (display-only cannot be matched by a reference search)."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = ref_type_and_id(reference, param)
    return EncounterReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _individual_row(participant: dict) -> EncounterParticipant | None:
    individual = participant.get("individual") or {}
    reference = individual.get("reference")
    identifier = individual.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = typed(reference, PARTICIPANT_TYPES)
    return EncounterParticipant(
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _location_row(location: dict) -> EncounterLocation | None:
    ref = location.get("location") or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    period_start, period_end = period_bounds(location.get("period"))
    has_ref = bool(reference or identifier.get("value"))
    if not (has_ref or period_start or period_end):
        return None
    parsed = typed(reference, ("Location",))
    return EncounterLocation(
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
        period_start=period_start,
        period_end=period_end,
    )


# Token parameter -> the dotted element path its CodeableConcepts are read from.
_TOKEN_PATHS = {
    "type": "type",
    "reason-code": "reasonCode",
    "special-arrangement": "hospitalization.specialArrangement",
    "participant-type": "participant.type",
}


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by EncounterModel relationship name."""
    tokens = []
    for param, path in _TOKEN_PATHS.items():
        model = partial(EncounterToken, param=param)
        for concept in _elements(document, path):
            tokens.extend(type_rows(model, concept))
    references = []
    for param, path in REFERENCE_PARAMS.items():
        references += [
            r for ref in _elements(document, path) if (r := _reference_row(param, ref))
        ]
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(EncounterIdentifier, i)
        ],
        "tokens": tokens,
        "references": references,
        "participants": [
            r for p in document.get("participant") or [] if (r := _individual_row(p))
        ],
        "locations": [
            r for loc in document.get("location") or [] if (r := _location_row(loc))
        ],
    }
