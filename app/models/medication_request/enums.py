from enum import Enum


class MedicationRequestStatus(str, Enum):
    """FHIR R4 MedicationRequest.status (1..1, required binding, modifier)
    — https://www.hl7.org/fhir/R4/valueset-medicationrequest-status.html
    Member name uses underscores (`on_hold`, `entered_in_error`); the true
    hyphenated FHIR code is recovered in the mapper via `.replace("_", "-")`
    — same shape as app.models.service_request.enums.ServiceRequestStatus."""

    active = "active"
    on_hold = "on_hold"
    cancelled = "cancelled"
    completed = "completed"
    entered_in_error = "entered_in_error"
    stopped = "stopped"
    draft = "draft"
    unknown = "unknown"


class MedicationRequestIntent(str, Enum):
    """FHIR R4 MedicationRequest.intent (1..1, required binding, modifier)
    — https://www.hl7.org/fhir/R4/valueset-medicationrequest-intent.html"""

    proposal = "proposal"
    plan = "plan"
    order = "order"
    original_order = "original_order"
    reflex_order = "reflex_order"
    filler_order = "filler_order"
    instance_order = "instance_order"
    option = "option"


class MedicationRequestPriority(str, Enum):
    """FHIR R4 MedicationRequest.priority (0..1, required binding when
    present) — https://www.hl7.org/fhir/R4/valueset-request-priority.html
    No hyphenated codes — member name == member value."""

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


class MedicationRequestQuantityComparator(str, Enum):
    """FHIR R4 Quantity.comparator (0..1) — used by every flattened
    Quantity/Duration/SimpleQuantity field on this resource
    (dispenseRequest's initialFill.quantity/initialFill.duration/
    dispenseInterval/quantity/expectedSupplyDuration). Resource-scoped
    copy — see app.models.questionnaire.enums.QuestionnaireQuantityComparator's
    own docstring for why a universal concept still gets a fresh
    model-layer enum per resource."""

    lt = "lt"
    le = "le"
    ge = "ge"
    gt = "gt"


class MedicationRequestReportedReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.reportedReference
    (Reference(Patient | Practitioner | PractitionerRole | RelatedPerson |
    Organization)). Of these five, Practitioner/PractitionerRole/
    Organization are modeled resources in this system."""

    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"


class MedicationRequestMedicationReferenceType(str, Enum):
    """Allowed reference type for MedicationRequest.medicationReference
    (Reference(Medication)). Not a modeled resource in this system — the
    existence check is never attempted for this field. Kept local
    (not promoted to the shared app.models.enums) since nothing else
    references Medication yet."""

    Medication = "Medication"


class MedicationRequestRequesterReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.requester
    (Reference(Practitioner | PractitionerRole | Organization | Patient |
    RelatedPerson | Device)). Of these six, Practitioner/PractitionerRole/
    Organization are modeled resources in this system. Resource-scoped
    copy — same shape as
    app.models.service_request.enums.ServiceRequestRequesterReferenceType,
    kept separate per this codebase's own duplication convention."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Device = "Device"


class MedicationRequestPerformerReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.performer
    (Reference(Practitioner | PractitionerRole | Organization | Patient |
    Device | RelatedPerson | CareTeam)). Of these seven, Practitioner/
    PractitionerRole/Organization are modeled resources in this system.
    Unlike ServiceRequest.performer (0..*), this is a single 0..1
    Reference field."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"
    Patient = "Patient"
    Device = "Device"
    RelatedPerson = "RelatedPerson"
    CareTeam = "CareTeam"


class MedicationRequestRecorderReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.recorder
    (Reference(Practitioner | PractitionerRole)). Both are modeled
    resources in this system — this field's existence check is always
    enforced (no "modeled subset" needed)."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"


class MedicationRequestBasedOnReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.basedOn
    (Reference(CarePlan | MedicationRequest | ServiceRequest |
    ImmunizationRecommendation)). Of these four, MedicationRequest
    (self-referential) and ServiceRequest are modeled resources in this
    system — CarePlan/ImmunizationRecommendation rows always rely on the
    identifier fallback instead."""

    CarePlan = "CarePlan"
    MedicationRequest = "MedicationRequest"
    ServiceRequest = "ServiceRequest"
    ImmunizationRecommendation = "ImmunizationRecommendation"


class MedicationRequestReasonReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.reasonReference
    (Reference(Condition | Observation)). Neither is a modeled resource
    in this system."""

    Condition = "Condition"
    Observation = "Observation"


class MedicationRequestInsuranceReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.insurance
    (Reference(Coverage | ClaimResponse)). Neither is a modeled resource
    in this system. Resource-scoped copy — same shape as
    app.models.service_request.enums.ServiceRequestInsuranceReferenceType."""

    Coverage = "Coverage"
    ClaimResponse = "ClaimResponse"


class MedicationRequestNoteAuthorReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.note.author[x]'s
    Reference variant (Reference(Practitioner | Patient | RelatedPerson |
    Organization)). Only Practitioner/Organization are modeled resources
    in this system."""

    Practitioner = "Practitioner"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"


class MedicationRequestDetectedIssueReferenceType(str, Enum):
    """Allowed reference type for MedicationRequest.detectedIssue
    (Reference(DetectedIssue)). Not a modeled resource in this system —
    kept local, same reasoning as
    app.models.service_request.enums.ServiceRequestSpecimenReferenceType."""

    DetectedIssue = "DetectedIssue"


class MedicationRequestEventHistoryReferenceType(str, Enum):
    """Allowed reference type for MedicationRequest.eventHistory
    (Reference(Provenance)). Not a modeled resource in this system."""

    Provenance = "Provenance"
