from enum import Enum


class ServiceRequestStatus(str, Enum):
    """FHIR R4 ServiceRequest.status (1..1, required binding, modifier) —
    https://www.hl7.org/fhir/R4/valueset-request-status.html

    Member name uses underscores (`on_hold`, `entered_in_error`); the true
    hyphenated FHIR code is recovered in the mapper via `.replace("_", "-")`
    — same key!=value-at-the-schema-layer-only shape as
    app.models.questionnaire_response.enums.QuestionnaireResponseStatus.
    """

    draft = "draft"
    active = "active"
    on_hold = "on_hold"
    revoked = "revoked"
    completed = "completed"
    entered_in_error = "entered_in_error"
    unknown = "unknown"


class ServiceRequestIntent(str, Enum):
    """FHIR R4 ServiceRequest.intent (1..1, required binding, modifier) —
    https://www.hl7.org/fhir/R4/valueset-request-intent.html"""

    proposal = "proposal"
    plan = "plan"
    directive = "directive"
    order = "order"
    original_order = "original_order"
    reflex_order = "reflex_order"
    filler_order = "filler_order"
    instance_order = "instance_order"
    option = "option"


class ServiceRequestPriority(str, Enum):
    """FHIR R4 ServiceRequest.priority (0..1, required binding when
    present) — https://www.hl7.org/fhir/R4/valueset-request-priority.html
    No hyphenated codes — member name == member value."""

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


class ServiceRequestQuantityComparator(str, Enum):
    """FHIR R4 Quantity.comparator (0..1) — used by ServiceRequest.quantityQuantity
    and quantityRatio's numerator/denominator. Resource-scoped copy — see
    app.models.questionnaire.enums.QuestionnaireQuantityComparator's own
    docstring for why a universal concept still gets a fresh model-layer
    enum per resource. Member name == member value here (readable); the
    true `<`/`<=`/`>=`/`>` FHIR symbol lives only at the schema layer and
    is rendered explicitly by the mapper."""

    lt = "lt"
    le = "le"
    ge = "ge"
    gt = "gt"


class ServiceRequestBasedOnReferenceType(str, Enum):
    """Allowed reference types for ServiceRequest.basedOn
    (Reference(CarePlan | ServiceRequest | MedicationRequest)). Of these
    three, only ServiceRequest is a modeled resource in this system
    (registered in RESOURCE_REGISTRY) — CarePlan/MedicationRequest rows
    always rely on the identifier fallback instead; the existence check
    is only ever attempted for the ServiceRequest subset (see
    app.repository.service_request._shared._MODELED_BASED_ON_TYPES)."""

    CarePlan = "CarePlan"
    ServiceRequest = "ServiceRequest"
    MedicationRequest = "MedicationRequest"


class ServiceRequestSubjectReferenceType(str, Enum):
    """Allowed reference types for ServiceRequest.subject
    (Reference(Patient | Group | Location | Device)). Of these four, only
    Location is a modeled resource in this system — Patient/Group/Device
    rows always rely on the identifier fallback instead."""

    Patient = "Patient"
    Group = "Group"
    Location = "Location"
    Device = "Device"


class ServiceRequestRequesterReferenceType(str, Enum):
    """Allowed reference types for ServiceRequest.requester
    (Reference(Practitioner | PractitionerRole | Organization | Patient |
    RelatedPerson | Device)). Of these six, Practitioner/PractitionerRole/
    Organization are modeled resources in this system — Patient/
    RelatedPerson/Device rows always rely on the identifier fallback
    instead."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Device = "Device"


class ServiceRequestPerformerReferenceType(str, Enum):
    """Allowed reference types for ServiceRequest.performer
    (Reference(Practitioner | PractitionerRole | Organization | CareTeam |
    HealthcareService | Patient | Device | RelatedPerson)). Of these
    eight, Practitioner/PractitionerRole/Organization/HealthcareService
    are modeled resources in this system — CareTeam/Patient/Device/
    RelatedPerson rows always rely on the identifier fallback instead."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"
    CareTeam = "CareTeam"
    HealthcareService = "HealthcareService"
    Patient = "Patient"
    Device = "Device"
    RelatedPerson = "RelatedPerson"


class ServiceRequestReasonReferenceType(str, Enum):
    """Allowed reference types for ServiceRequest.reasonReference
    (Reference(Condition | Observation | DiagnosticReport |
    DocumentReference)). None of these four is a modeled resource in this
    system — the existence check is never attempted for this field."""

    Condition = "Condition"
    Observation = "Observation"
    DiagnosticReport = "DiagnosticReport"
    DocumentReference = "DocumentReference"


class ServiceRequestInsuranceReferenceType(str, Enum):
    """Allowed reference types for ServiceRequest.insurance
    (Reference(Coverage | ClaimResponse)). Neither is a modeled resource
    in this system."""

    Coverage = "Coverage"
    ClaimResponse = "ClaimResponse"


class ServiceRequestSpecimenReferenceType(str, Enum):
    """Allowed reference type for ServiceRequest.specimen
    (Reference(Specimen)). Not a modeled resource in this system — same
    single-target-but-unmodeled shape as
    app.models.appointment.enums.AppointmentBasedOnReferenceType (a real
    enum, with the existence check simply never attempted for it), kept
    local to this resource rather than promoted to the shared
    app.models.enums since nothing else references Specimen yet."""

    Specimen = "Specimen"


class ServiceRequestRelevantHistoryReferenceType(str, Enum):
    """Allowed reference type for ServiceRequest.relevantHistory
    (Reference(Provenance)). Not a modeled resource in this system — same
    reasoning as ServiceRequestSpecimenReferenceType above."""

    Provenance = "Provenance"


class ServiceRequestNoteAuthorReferenceType(str, Enum):
    """Allowed reference types for ServiceRequest.note.author[x]'s
    Reference variant (Reference(Practitioner | Patient | RelatedPerson |
    Organization), the alternative to a plain `authorString`). Only
    Practitioner/Organization are modeled resources in this system."""

    Practitioner = "Practitioner"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"
