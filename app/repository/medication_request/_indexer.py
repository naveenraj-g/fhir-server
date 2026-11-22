"""
FHIR MedicationRequest document -> search index. The only write-side mapper.

MedicationRequest's whole resource is stored verbatim in MedicationRequestModel.content; this
module derives every *other* column and child row from it - exactly the values the FHIR R4
MedicationRequest search parameters filter on
(https://www.hl7.org/fhir/R4/medicationrequest.html#search), nothing more. See
MedicationRequestModel's docstring for the parameter -> storage table; the shared builders are
in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create and
patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.medication_request import (
    DISPENSER_TYPES,
    MEDICATION_TYPES,
    PERFORMER_TYPES,
    REQUESTER_TYPES,
    SUBJECT_TYPES,
    MedicationRequestIdentifier,
    MedicationRequestIntent,
    MedicationRequestPriority,
    MedicationRequestStatus,
    MedicationRequestTiming,
    MedicationRequestToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    relative,
    type_rows,
)

from ._shared import typed

# Of the targets of each element, these are resources here (the rest are stored as sent until
# they are rebuilt: a Group subject, a Device / CareTeam requester or performer, CarePlan
# basedOn, insurance, eventHistory).
_MODELED_SUBJECTS = ("Patient",)
_MODELED_REQUESTERS = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "Patient",
    "RelatedPerson",
)
_MODELED_PERFORMERS = (*_MODELED_REQUESTERS, "CareTeam")
_MODELED_REPORTERS = _MODELED_REQUESTERS  # reported[x]: Patient, Practitioner, PractitionerRole, RelatedPerson, Organization
_MODELED_BASED_ON = (
    "MedicationRequest",
    "ServiceRequest",
    "ImmunizationRecommendation",
    "CarePlan",
)
_MODELED_REASONS = ("Condition", "Observation")
# Reference(Any) `supportingInformation` targets that are existence-checked on write: the
# resources already rebuilt that supporting information can be.
_MODELED_INFORMATION = (
    "MedicationRequest",
    "Group",
    "CareTeam",
    "CarePlan",
    "ServiceRequest",
    "Medication",
    "Specimen",
    "Observation",
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "RelatedPerson",
    "Organization",
    "Location",
    "HealthcareService",
    "Encounter",
    "Appointment",
    "Condition",
    "Procedure",
    "DiagnosticReport",
    "AllergyIntolerance",
    "Immunization",
    "FamilyMemberHistory",
    "RiskAssessment",
    "ClinicalImpression",
)
# Annotation.author[x] reference targets in R4.
_NOTE_AUTHOR_TYPES = ("Practitioner", "Patient", "RelatedPerson", "Organization")

_STATUSES = {m.value for m in MedicationRequestStatus}
_INTENTS = {m.value for m in MedicationRequestIntent}
_PRIORITIES = {m.value for m in MedicationRequestPriority}


def local_references(document: dict) -> list[tuple[str, str, str]]:
    """(element label, resource type, relative reference) for every local reference that must
    exist in the caller's org on write: the identifiers' assigners (the resource's and the
    group identifier's), `subject` (a Patient), `encounter`, `requester`, `performer`,
    `recorder`, `reported[x]`, `medicationReference`, `dispenseRequest.performer`, `basedOn`,
    `priorPrescription`, `reasonReference` (Condition, Observation), `detectedIssue`,
    `supportingInformation` (any rebuilt resource) and every note's `authorReference`.
    Absolute URLs, logical (identifier-only) references and targets that are not resources on
    this server (a Group subject, a Device / CareTeam requester or performer, CarePlan
    basedOn, insurance, eventHistory) point elsewhere and are not checked."""
    refs = []

    def add(label, reference, resource_type):
        local = relative(reference, resource_type)
        if local:
            refs.append((label, resource_type, local))

    def add_typed(label, ref, allowed):
        parsed = typed((ref or {}).get("reference"), allowed)
        if parsed:
            refs.append((label, parsed[0], ref["reference"]))

    def assigner(label, identifier):
        add(
            label,
            ((identifier or {}).get("assigner") or {}).get("reference"),
            "Organization",
        )

    for identifier in document.get("identifier") or []:
        assigner("identifier.assigner", identifier)
    assigner("groupIdentifier.assigner", document.get("groupIdentifier"))
    add_typed("subject", document.get("subject"), _MODELED_SUBJECTS)
    add("encounter", (document.get("encounter") or {}).get("reference"), "Encounter")
    add_typed("requester", document.get("requester"), _MODELED_REQUESTERS)
    add_typed("performer", document.get("performer"), _MODELED_PERFORMERS)
    add_typed(
        "recorder", document.get("recorder"), ("Practitioner", "PractitionerRole")
    )
    add_typed(
        "reportedReference", document.get("reportedReference"), _MODELED_REPORTERS
    )
    add(
        "medicationReference",
        (document.get("medicationReference") or {}).get("reference"),
        "Medication",
    )
    add(
        "dispenseRequest.performer",
        ((document.get("dispenseRequest") or {}).get("performer") or {}).get(
            "reference"
        ),
        "Organization",
    )
    for ref in document.get("basedOn") or []:
        add_typed("basedOn", ref, _MODELED_BASED_ON)
    add(
        "priorPrescription",
        (document.get("priorPrescription") or {}).get("reference"),
        "MedicationRequest",
    )
    for ref in document.get("reasonReference") or []:
        add_typed("reasonReference", ref, _MODELED_REASONS)
    for ref in document.get("detectedIssue") or []:
        add("detectedIssue", (ref or {}).get("reference"), "DetectedIssue")
    for ref in document.get("supportingInformation") or []:
        add_typed("supportingInformation", ref, _MODELED_INFORMATION)
    for note in document.get("note") or []:
        add_typed(
            "note.authorReference",
            (note or {}).get("authorReference"),
            _NOTE_AUTHOR_TYPES,
        )
    return refs


def _ref_columns(prefix: str, ref: dict | None, allowed: tuple[str, ...]) -> dict:
    """The index columns of one 0..1 Reference: `{prefix}_reference` (the raw string),
    `{prefix}_type`/`{prefix}_id` (a relative `Type/<id>` of an allowed type) and
    `{prefix}_identifier_system`/`_value`."""
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
    """The half-open range a dateTime covers at its written precision, or (None, None)."""
    return period_bounds({"start": value, "end": value}) if value else (None, None)


def _code(value, allowed, enum):
    return enum(value) if value in allowed else None


def index_columns(document: dict) -> dict:
    """Search columns on the medication_request row itself."""
    authored_start, authored_end = _point(document.get("authoredOn"))
    return {
        "status": _code(document.get("status"), _STATUSES, MedicationRequestStatus),
        "intent": _code(document.get("intent"), _INTENTS, MedicationRequestIntent),
        "priority": _code(
            document.get("priority"), _PRIORITIES, MedicationRequestPriority
        ),
        "authored_start": authored_start,
        "authored_end": authored_end,
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("encounter", document.get("encounter"), ("Encounter",)),
        **_ref_columns("requester", document.get("requester"), REQUESTER_TYPES),
        **_ref_columns("performer", document.get("performer"), PERFORMER_TYPES),
        **_ref_columns(
            "medication", document.get("medicationReference"), MEDICATION_TYPES
        ),
        **_ref_columns(
            "dispenser",
            (document.get("dispenseRequest") or {}).get("performer"),
            DISPENSER_TYPES,
        ),
    }


def _concept(param: str, concept: dict | None) -> list:
    return (
        type_rows(partial(MedicationRequestToken, param=param), concept)
        if concept
        else []
    )


def _token_rows(document: dict) -> list:
    rows = []
    for category in document.get("category") or []:
        rows += _concept("category", category)
    rows += _concept("code", document.get("medicationCodeableConcept"))
    rows += _concept("intended-performertype", document.get("performerType"))
    return rows


def _timing_rows(document: dict) -> list:
    """One row per dosageInstruction.timing.event (a dateTime) of every dosage instruction."""
    rows = []
    for dosage in document.get("dosageInstruction") or []:
        timing = (dosage or {}).get("timing") or {}
        for event in timing.get("event") or []:
            start, end = _point(event)
            if start or end:
                rows.append(MedicationRequestTiming(event_start=start, event_end=end))
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by MedicationRequestModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(MedicationRequestIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "timings": _timing_rows(document),
    }
