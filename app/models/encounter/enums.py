from enum import Enum


class EncounterStatus(str, Enum):
    """FHIR R4 Encounter.status (1..1, required binding) — also used by
    Encounter.statusHistory.status (1..1, same value set) —
    https://www.hl7.org/fhir/R4/valueset-encounter-status.html

    Member name intentionally equals member value (both underscore-only,
    not the true hyphenated FHIR code) — see
    app.models.slot.enums.SlotStatus's docstring for the full reasoning:
    SQLAlchemy's `Enum(PyEnum)` stores each member's `.name` in Postgres
    by default, so the real `entered-in-error`/`onleave` (sic, no hyphen)
    FHIR codes are rendered explicitly in
    app/fhir/mappers/encounter/fhir.py instead.
    """

    planned = "planned"
    arrived = "arrived"
    triaged = "triaged"
    in_progress = "in_progress"
    onleave = "onleave"
    finished = "finished"
    cancelled = "cancelled"
    entered_in_error = "entered_in_error"
    unknown = "unknown"


class EncounterLocationStatus(str, Enum):
    """FHIR R4 Encounter.location.status (0..1, required binding) —
    https://www.hl7.org/fhir/R4/valueset-encounter-location-status.html
    """

    planned = "planned"
    active = "active"
    reserved = "reserved"
    completed = "completed"


class EncounterParticipantIndividualReferenceType(str, Enum):
    """Allowed reference types for Encounter.participant.individual
    (0..1). FHIR R4 allows Practitioner|PractitionerRole|RelatedPerson —
    of these, only Practitioner and PractitionerRole are modeled resources
    in this system (registered in RESOURCE_REGISTRY); RelatedPerson rows
    will in practice always rely on the reference_identifier_* logical-
    reference fallback instead of a resolved reference_id — same
    situation as app.models.schedule.enums.ScheduleActorReferenceType.
    """

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"


class EncounterConditionOrProcedureReferenceType(str, Enum):
    """Allowed reference types for Encounter.diagnosis.condition (1..1).
    FHIR R4 allows Condition|Procedure — neither is a modeled resource in
    this system, so every row relies on the reference_identifier_*
    logical-reference fallback (or just the raw reference_reference
    string) instead of a resolved reference_id; the existence check is
    never attempted for this field at all — same situation as
    app.models.appointment.enums.AppointmentReasonReferenceType.
    """

    Condition = "Condition"
    Procedure = "Procedure"


class EncounterEpisodeOfCareReferenceType(str, Enum):
    """Allowed reference type for Encounter.episodeOfCare[] (0..*) — an
    EpisodeOfCare is the only allowed target. EpisodeOfCare is not a
    modeled resource in this system, so this reference's existence check
    is never attempted."""

    EpisodeOfCare = "EpisodeOfCare"


class EncounterBasedOnReferenceType(str, Enum):
    """Allowed reference type for Encounter.basedOn[] (0..*) — a
    ServiceRequest is the only allowed target. Not a modeled resource
    here; existence check never attempted — same as
    app.models.appointment.enums.AppointmentBasedOnReferenceType."""

    ServiceRequest = "ServiceRequest"


class EncounterReasonReferenceType(str, Enum):
    """Allowed reference types for Encounter.reasonReference[] (0..*).
    FHIR R4 allows Condition|Procedure|Observation|
    ImmunizationRecommendation — none are modeled resources in this
    system; existence check never attempted — same value set and
    reasoning as app.models.appointment.enums.AppointmentReasonReferenceType
    (kept as its own separate enum/DB type, not reused across resources,
    consistent with this codebase's per-resource-per-field convention)."""

    Condition = "Condition"
    Procedure = "Procedure"
    Observation = "Observation"
    ImmunizationRecommendation = "ImmunizationRecommendation"


class EncounterAccountReferenceType(str, Enum):
    """Allowed reference type for Encounter.account[] (0..*) — an Account
    is the only allowed target. Not a modeled resource here; existence
    check never attempted."""

    Account = "Account"


class EncounterHospitalizationReferenceType(str, Enum):
    """Allowed reference types for Encounter.hospitalization.origin
    (0..1) and .destination (0..1) — both share the same FHIR R4 target
    set, Location|Organization, both of which ARE modeled resources in
    this system, so this reference's existence check is actually
    enforced for both fields — unlike most other polymorphic references
    on this resource."""

    Location = "Location"
    Organization = "Organization"


class EncounterLengthComparator(str, Enum):
    """FHIR R4 Duration.comparator (0..1) for Encounter.length — a tiny,
    fixed 4-value set (`<|<=|>=|>`) that doesn't map to valid Python
    identifiers, so member name != member value here (readable identifier
    names, real FHIR symbols rendered explicitly in
    app/fhir/mappers/encounter/fhir.py) — same key!=value shape as
    app.schemas.enums.PatientLinkType, just at the model layer instead of
    the schema layer since this one-off 4-value set isn't reused anywhere
    else in this codebase.
    https://www.hl7.org/fhir/R4/datatypes.html#Quantity (comparator)
    """

    lt = "lt"
    le = "le"
    ge = "ge"
    gt = "gt"


class EncounterLocationReferenceType(str, Enum):
    """Allowed reference type for Encounter.location.location (1..1) — a
    Location is the only allowed target, and Location IS a modeled
    resource here, so this reference's existence check is enforced."""

    Location = "Location"
