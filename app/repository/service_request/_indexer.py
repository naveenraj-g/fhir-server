"""
FHIR ServiceRequest document -> search index. The only write-side mapper.

ServiceRequest's whole resource is stored verbatim in ServiceRequestModel.content; this
module derives every *other* column and child row from it — exactly the values the FHIR
R4 ServiceRequest search parameters filter on
(https://www.hl7.org/fhir/R4/servicerequest.html#search), nothing more. See
ServiceRequestModel's docstring for the parameter -> storage table; the shared builders are
in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also stored), so create
and patch share one path: both hand over the full post-write document.
"""

from __future__ import annotations

from functools import partial

from app.models.service_request import (
    PERFORMER_TYPES,
    REQUESTER_TYPES,
    SUBJECT_TYPES,
    ServiceRequestIdentifier,
    ServiceRequestInstantiatesUri,
    ServiceRequestIntent,
    ServiceRequestPerformer,
    ServiceRequestPriority,
    ServiceRequestReference,
    ServiceRequestStatus,
    ServiceRequestToken,
)
from app.repository._content_index import (
    identifier_rows,
    period_bounds,
    relative,
    type_rows,
)

from ._shared import ref_type_and_id, typed

# Of the targets of each element, these are resources here (the rest are stored as sent until
# they are rebuilt: Group / Device subjects, CareTeam / Device performers, CarePlan /
# MedicationRequest basedOn, DocumentReference reasons, Coverage / ClaimResponse insurance,
# Provenance history).
_MODELED_SUBJECTS = ("Patient", "Location")
_MODELED_REQUESTERS = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "Patient",
    "RelatedPerson",
)
_MODELED_PERFORMERS = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "HealthcareService",
    "Patient",
    "RelatedPerson",
)
_MODELED_REASONS = ("Condition", "Observation", "DiagnosticReport")
# Reference(Any) `supportingInfo` targets that are existence-checked on write: the resources
# already rebuilt that supporting information can be.
_MODELED_INFORMATION = (
    "ServiceRequest",
    "Medication",
    "MedicationRequest",
    "Group",
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

_STATUSES = {m.value for m in ServiceRequestStatus}
_INTENTS = {m.value for m in ServiceRequestIntent}
_PRIORITIES = {m.value for m in ServiceRequestPriority}


def local_references(document: dict) -> list[tuple[str, str, str]]:
    """(element label, resource type, relative reference) for every local reference that
    must exist in the caller's org on write: the identifiers' assigners (the resource's and
    the requisition's), `subject` (a Patient or Location), `encounter`, `requester`, every
    `performer`, `basedOn` (ServiceRequest, MedicationRequest) / `replaces` (ServiceRequest), `specimen`, `locationReference`,
    `reasonReference` (Condition, Observation, DiagnosticReport), `supportingInfo` (any
    rebuilt resource) and every note's `authorReference`. Absolute URLs, logical
    (identifier-only) references and targets that are not resources on this server (a
    Group or Device subject, a CareTeam, CarePlan / MedicationRequest basedOn, a
    DocumentReference reason, insurance, relevantHistory) point elsewhere and are not
    checked."""
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
    assigner("requisition.assigner", document.get("requisition"))
    add_typed("subject", document.get("subject"), _MODELED_SUBJECTS)
    add("encounter", (document.get("encounter") or {}).get("reference"), "Encounter")
    add_typed("requester", document.get("requester"), _MODELED_REQUESTERS)
    for ref in document.get("performer") or []:
        add_typed("performer", ref, _MODELED_PERFORMERS)
    for ref in document.get("basedOn") or []:
        add_typed("basedOn", ref, ("ServiceRequest", "MedicationRequest"))
    for ref in document.get("replaces") or []:
        add("replaces", (ref or {}).get("reference"), "ServiceRequest")
    for ref in document.get("specimen") or []:
        add("specimen", (ref or {}).get("reference"), "Specimen")
    for ref in document.get("locationReference") or []:
        add("locationReference", (ref or {}).get("reference"), "Location")
    for ref in document.get("reasonReference") or []:
        add_typed("reasonReference", ref, _MODELED_REASONS)
    for ref in document.get("supportingInfo") or []:
        add_typed("supportingInfo", ref, _MODELED_INFORMATION)
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


def _occurrence_bounds(document: dict):
    """The range occurrence[x] covers: a dateTime as the range of its precision, a Period
    from its start to the instant after its end (NULL = open), a Timing from its earliest
    event to the instant after its latest (else its `repeat.boundsPeriod`)."""
    if document.get("occurrenceDateTime"):
        return _point(document["occurrenceDateTime"])
    if document.get("occurrencePeriod"):
        return period_bounds(document["occurrencePeriod"])
    timing = document.get("occurrenceTiming")
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


def _code(value, allowed, enum):
    return enum(value) if value in allowed else None


def index_columns(document: dict) -> dict:
    """Search columns on the service_request row itself."""
    authored_start, authored_end = _point(document.get("authoredOn"))
    occurrence_start, occurrence_end = _occurrence_bounds(document)
    requisition = document.get("requisition") or {}
    return {
        "status": _code(document.get("status"), _STATUSES, ServiceRequestStatus),
        "intent": _code(document.get("intent"), _INTENTS, ServiceRequestIntent),
        "priority": _code(
            document.get("priority"), _PRIORITIES, ServiceRequestPriority
        ),
        "authored_start": authored_start,
        "authored_end": authored_end,
        "occurrence_start": occurrence_start,
        "occurrence_end": occurrence_end,
        "requisition_system": requisition.get("system"),
        "requisition_value": requisition.get("value"),
        **_ref_columns("subject", document.get("subject"), SUBJECT_TYPES),
        **_ref_columns("encounter", document.get("encounter"), ("Encounter",)),
        **_ref_columns("requester", document.get("requester"), REQUESTER_TYPES),
    }


def _concept(param: str, concept: dict | None) -> list:
    return (
        type_rows(partial(ServiceRequestToken, param=param), concept) if concept else []
    )


def _token_rows(document: dict) -> list:
    rows = []
    for category in document.get("category") or []:
        rows += _concept("category", category)
    rows += _concept("code", document.get("code"))
    for site in document.get("bodySite") or []:
        rows += _concept("body-site", site)
    rows += _concept("performer-type", document.get("performerType"))
    return rows


def _reference_row(param: str, ref: dict | None) -> ServiceRequestReference | None:
    """One index row for a Reference with a `reference` or an `identifier` (display-only
    cannot be matched by a reference search)."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = ref_type_and_id(reference, param)
    return ServiceRequestReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _reference_rows(document: dict) -> list:
    rows = []
    for param, element in (
        ("based-on", "basedOn"),
        ("replaces", "replaces"),
        ("specimen", "specimen"),
    ):
        rows += [_reference_row(param, r) for r in document.get(element) or []]
    # instantiatesCanonical is a list of canonical URLs (strings), not References.
    for canonical in document.get("instantiatesCanonical") or []:
        rows.append(_reference_row("instantiates-canonical", {"reference": canonical}))
    return [r for r in rows if r]


def _performer_rows(document: dict) -> list:
    rows = []
    for performer in document.get("performer") or []:
        performer = performer or {}
        reference = performer.get("reference")
        identifier = performer.get("identifier") or {}
        if not (reference or identifier.get("value")):
            continue
        parsed = typed(reference, PERFORMER_TYPES)
        rows.append(
            ServiceRequestPerformer(
                reference_reference=reference,
                reference_type=parsed[0] if parsed else None,
                reference_id=parsed[1] if parsed else None,
                reference_identifier_system=identifier.get("system"),
                reference_identifier_value=identifier.get("value"),
            )
        )
    return rows


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by ServiceRequestModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(ServiceRequestIdentifier, i)
        ],
        "tokens": _token_rows(document),
        "references": _reference_rows(document),
        "performers": _performer_rows(document),
        "instantiates_uris": [
            ServiceRequestInstantiatesUri(uri=u)
            for u in document.get("instantiatesUri") or []
            if u
        ],
    }
