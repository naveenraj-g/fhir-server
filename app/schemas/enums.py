from enum import Enum

# datatype enums


class AddressUse(str, Enum):
    """
    FHIR AddressUse value set.

    The purpose of this address.
    """

    home = "home"
    work = "work"
    temp = "temp"
    old = "old"
    billing = "billing"


class AddressType(str, Enum):
    """
    FHIR AddressType value set.

    The type of address.
    """

    postal = "postal"
    physical = "physical"
    both = "both"


class AdministrativeGender(str, Enum):
    """
    FHIR AdministrativeGender value set.

    The gender of a person for administrative purposes.
    """

    male = "male"
    female = "female"
    other = "other"
    unknown = "unknown"


class ContactPointSystem(str, Enum):
    """
    FHIR ContactPointSystem value set.

    Telecommunications form for contact point.
    """

    phone = "phone"
    fax = "fax"
    email = "email"
    pager = "pager"
    url = "url"
    sms = "sms"
    other = "other"


class ContactPointUse(str, Enum):
    """
    FHIR ContactPointUse value set.

    Purpose of the contact point.
    """

    home = "home"
    work = "work"
    temp = "temp"
    old = "old"
    mobile = "mobile"


class HumanNameUse(str, Enum):
    """
    FHIR HumanNameUse value set.

    Indicates the purpose of this name.
    """

    usual = "usual"  # The name normally used
    official = "official"  # Official/legal name
    temp = "temp"  # Temporary name
    nickname = "nickname"  # Nickname
    anonymous = "anonymous"  # Anonymous/pseudonym
    old = "old"  # Old/previous name
    maiden = "maiden"  # Maiden name


class IdentifierUse(str, Enum):
    """
    FHIR IdentifierUse value set.

    Indicates the purpose of the identifier.
    """

    usual = "usual"  # The identifier the resource owner normally uses
    official = (
        "official"  # The identifier considered official for legal/administrative use
    )
    temp = "temp"  # Temporary identifier
    secondary = "secondary"  # Additional identifier
    old = "old"  # No longer valid identifier


"""
------------------------------------------------------------------------------
------------------------------------------------------------------------------
"""
# backbone enums


class PatientLinkType(str, Enum):
    """
    FHIR Patient.link.type value set.
    """

    replaced_by = "replaced-by"
    replaces = "replaces"
    refer = "refer"
    seealso = "seealso"


class HealthcareServiceDayOfWeek(str, Enum):
    """
    FHIR DaysOfWeek value set — used by HealthcareService.availableTime.daysOfWeek.
    """

    mon = "mon"
    tue = "tue"
    wed = "wed"
    thu = "thu"
    fri = "fri"
    sat = "sat"
    sun = "sun"


class PractitionerRoleDayOfWeek(str, Enum):
    """
    FHIR DaysOfWeek value set — used by PractitionerRole.availableTime.daysOfWeek.
    """

    mon = "mon"
    tue = "tue"
    wed = "wed"
    thu = "thu"
    fri = "fri"
    sat = "sat"
    sun = "sun"


class AppointmentStatus(str, Enum):
    """
    FHIR Appointment.status value set —
    https://www.hl7.org/fhir/R4/valueset-appointmentstatus.html

    Member name uses underscores (valid Python identifiers can't contain
    hyphens); the stored `.value` is the true hyphenated FHIR wire code —
    same key!=value shape as SlotStatus above. The model-layer
    app.models.appointment.enums.AppointmentStatus is a *different* enum
    with matching member NAMES but underscore-only values — convert
    between them by member name, never by value.
    """

    proposed = "proposed"
    pending = "pending"
    booked = "booked"
    arrived = "arrived"
    fulfilled = "fulfilled"
    cancelled = "cancelled"
    noshow = "noshow"
    entered_in_error = "entered-in-error"
    checked_in = "checked-in"
    waitlist = "waitlist"


class AppointmentParticipantRequired(str, Enum):
    """
    FHIR Appointment.participant.required value set —
    https://www.hl7.org/fhir/R4/valueset-participantrequired.html
    """

    required = "required"
    optional = "optional"
    information_only = "information-only"


class AppointmentParticipationStatus(str, Enum):
    """
    FHIR Appointment.participant.status value set —
    https://www.hl7.org/fhir/R4/valueset-participationstatus.html
    """

    accepted = "accepted"
    declined = "declined"
    tentative = "tentative"
    needs_action = "needs-action"


class AppointmentResponseParticipantStatus(str, Enum):
    """
    FHIR AppointmentResponse.participantStatus value set —
    https://www.hl7.org/fhir/R4/valueset-participationstatus.html

    Same value set as AppointmentParticipationStatus above (Appointment's
    own participant.status) — kept as its own separate enum, consistent
    with this module's existing precedent of per-resource duplicates for
    an identical value set (see HealthcareServiceDayOfWeek vs
    PractitionerRoleDayOfWeek).
    """

    accepted = "accepted"
    declined = "declined"
    tentative = "tentative"
    needs_action = "needs-action"


class EncounterStatus(str, Enum):
    """
    FHIR Encounter.status value set (also used by
    Encounter.statusHistory.status) —
    https://www.hl7.org/fhir/R4/valueset-encounter-status.html

    Member name uses underscores (valid Python identifiers can't contain
    hyphens); the stored `.value` is the true hyphenated FHIR wire code —
    same key!=value shape as SlotStatus below. The model-layer
    app.models.encounter.enums.EncounterStatus is a *different* enum with
    matching member NAMES but underscore-only values — convert between
    them by member name, never by value.
    """

    planned = "planned"
    arrived = "arrived"
    triaged = "triaged"
    in_progress = "in-progress"
    onleave = "onleave"
    finished = "finished"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class EncounterLocationStatus(str, Enum):
    """
    FHIR Encounter.location.status value set —
    https://www.hl7.org/fhir/R4/valueset-encounter-location-status.html
    """

    planned = "planned"
    active = "active"
    reserved = "reserved"
    completed = "completed"


class EncounterLengthComparator(str, Enum):
    """
    FHIR Duration.comparator value set, used by Encounter.length —
    member name uses a readable identifier since `<`/`<=`/`>=`/`>` aren't
    valid Python identifiers; the stored `.value` is the true FHIR wire
    symbol. The model-layer app.models.encounter.enums.EncounterLengthComparator
    is a *different* enum with matching member NAMES but readable
    (lt/le/ge/gt) values — convert between them by member name.
    """

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"


class SlotStatus(str, Enum):
    """
    FHIR Slot.status value set — https://www.hl7.org/fhir/R4/valueset-slotstatus.html

    Member name uses underscores (valid Python identifiers can't contain
    hyphens); the stored `.value` is the true hyphenated FHIR wire code —
    same key!=value shape as PatientLinkType above. The model-layer
    app.models.slot.enums.SlotStatus is a *different* enum with matching
    member NAMES but underscore-only values (see that class's docstring
    for why) — convert between them by member name, e.g.
    `ModelSlotStatus[payload.status.name]`, never by value.
    """

    busy = "busy"
    free = "free"
    busy_unavailable = "busy-unavailable"
    busy_tentative = "busy-tentative"
    entered_in_error = "entered-in-error"


class QuestionnaireStatus(str, Enum):
    """
    FHIR Questionnaire.status value set —
    https://www.hl7.org/fhir/R4/valueset-publication-status.html

    No hyphenated codes — member name == member value here too, same as
    the model-layer app.models.questionnaire.enums.QuestionnaireStatus.
    """

    draft = "draft"
    active = "active"
    retired = "retired"
    unknown = "unknown"


class QuestionnaireItemType(str, Enum):
    """
    FHIR Questionnaire.item.type value set —
    https://www.hl7.org/fhir/R4/valueset-item-type.html

    Member name uses underscores (`open_choice`); the stored `.value` is
    the true hyphenated FHIR wire code (`open-choice`) — same key!=value
    shape as SlotStatus above. The model-layer
    app.models.questionnaire.enums.QuestionnaireItemType is a *different*
    enum with matching member NAMES but underscore-only values — convert
    between them by member name, never by value.
    """

    group = "group"
    display = "display"
    boolean = "boolean"
    decimal = "decimal"
    integer = "integer"
    date = "date"
    dateTime = "dateTime"
    time = "time"
    string = "string"
    text = "text"
    url = "url"
    choice = "choice"
    open_choice = "open-choice"
    attachment = "attachment"
    reference = "reference"
    quantity = "quantity"


class QuestionnaireEnableBehavior(str, Enum):
    """
    FHIR Questionnaire.item.enableBehavior value set —
    https://www.hl7.org/fhir/R4/valueset-questionnaire-enable-behavior.html
    """

    all = "all"
    any = "any"


class QuestionnaireItemOperator(str, Enum):
    """
    FHIR Questionnaire.item.enableWhen.operator value set —
    https://www.hl7.org/fhir/R4/valueset-questionnaire-enable-operator.html

    Member name uses a readable identifier since `=`/`!=`/`>`/`<`/`>=`/`<=`
    aren't valid Python identifiers — same key!=value shape as
    EncounterLengthComparator above. The model-layer
    app.models.questionnaire.enums.QuestionnaireItemOperator is a
    *different* enum with matching member NAMES but readable
    (eq/ne/gt/lt/ge/le) values — convert between them by member name.
    """

    exists = "exists"
    eq = "="
    ne = "!="
    gt = ">"
    lt = "<"
    ge = ">="
    le = "<="


class QuestionnaireQuantityComparator(str, Enum):
    """
    FHIR Duration/Quantity.comparator value set, used by every Quantity-
    typed choice-type variant on Questionnaire.item.enableWhen.answer[x],
    .item.initial.value[x], and UsageContext.value[x] —
    https://www.hl7.org/fhir/R4/datatypes.html#Quantity

    Member name uses a readable identifier since `<`/`<=`/`>=`/`>` aren't
    valid Python identifiers; the stored `.value` is the true FHIR wire
    symbol. The model-layer
    app.models.questionnaire.enums.QuestionnaireQuantityComparator is a
    *different* enum with matching member NAMES but readable (lt/le/ge/gt)
    values — convert between them by member name. Resource-scoped copy,
    not shared with app.models.encounter.enums.EncounterLengthComparator —
    see that model-layer class's own docstring for why.
    """

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"


class QuestionnaireResponseStatus(str, Enum):
    """
    FHIR QuestionnaireResponse.status value set —
    https://www.hl7.org/fhir/R4/valueset-questionnaire-answers-status.html

    Member name uses underscores (`in_progress`, `entered_in_error`); the
    stored `.value` is the true hyphenated FHIR wire code (`in-progress`,
    `entered-in-error`) — same key!=value shape as QuestionnaireItemType
    above. The model-layer
    app.models.questionnaire_response.enums.QuestionnaireResponseStatus is
    a *different* enum with matching member NAMES but underscore-only
    values — convert between them by member name, never by value.
    """

    in_progress = "in-progress"
    completed = "completed"
    amended = "amended"
    entered_in_error = "entered-in-error"
    stopped = "stopped"


class QuestionnaireResponseQuantityComparator(str, Enum):
    """
    FHIR Duration/Quantity.comparator value set, used by
    QuestionnaireResponse.item.answer.value[x]'s Quantity variant —
    https://www.hl7.org/fhir/R4/datatypes.html#Quantity

    Member name uses a readable identifier since `<`/`<=`/`>=`/`>` aren't
    valid Python identifiers; the stored `.value` is the true FHIR wire
    symbol. The model-layer
    app.models.questionnaire_response.enums.QuestionnaireResponseQuantityComparator
    is a *different* enum with matching member NAMES but readable
    (lt/le/ge/gt) values — convert between them by member name.
    Resource-scoped copy, not shared with QuestionnaireQuantityComparator
    above — see that class's own docstring for why.
    """

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"


class MedicationRequestStatus(str, Enum):
    """
    FHIR MedicationRequest.status value set (modifier) —
    https://www.hl7.org/fhir/R4/valueset-medicationrequest-status.html
    Same name!=value shape as ServiceRequestStatus below.
    """

    active = "active"
    on_hold = "on-hold"
    cancelled = "cancelled"
    completed = "completed"
    entered_in_error = "entered-in-error"
    stopped = "stopped"
    draft = "draft"
    unknown = "unknown"


class MedicationRequestIntent(str, Enum):
    """
    FHIR MedicationRequest.intent value set (modifier) —
    https://www.hl7.org/fhir/R4/valueset-medicationrequest-intent.html
    """

    proposal = "proposal"
    plan = "plan"
    order = "order"
    original_order = "original-order"
    reflex_order = "reflex-order"
    filler_order = "filler-order"
    instance_order = "instance-order"
    option = "option"


class MedicationRequestPriority(str, Enum):
    """
    FHIR MedicationRequest.priority value set —
    https://www.hl7.org/fhir/R4/valueset-request-priority.html
    No hyphenated codes — member name == member value.
    """

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


class MedicationRequestQuantityComparator(str, Enum):
    """
    FHIR Duration/Quantity.comparator value set, used by every flattened
    Quantity/Duration field on MedicationRequest.dispenseRequest.
    Resource-scoped copy. Member name uses a readable identifier; stored
    `.value` is the true FHIR wire symbol.
    """

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"


class ServiceRequestStatus(str, Enum):
    """
    FHIR ServiceRequest.status value set (modifier) —
    https://www.hl7.org/fhir/R4/valueset-request-status.html

    Member name uses underscores (`on_hold`, `entered_in_error`); the
    stored `.value` is the true hyphenated FHIR wire code. The model-layer
    app.models.service_request.enums.ServiceRequestStatus is a *different*
    enum with matching member NAMES but underscore-only values — convert
    between them by member name, never by value.
    """

    draft = "draft"
    active = "active"
    on_hold = "on-hold"
    revoked = "revoked"
    completed = "completed"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class ServiceRequestIntent(str, Enum):
    """
    FHIR ServiceRequest.intent value set (modifier) —
    https://www.hl7.org/fhir/R4/valueset-request-intent.html
    Same name!=value shape as ServiceRequestStatus above.
    """

    proposal = "proposal"
    plan = "plan"
    directive = "directive"
    order = "order"
    original_order = "original-order"
    reflex_order = "reflex-order"
    filler_order = "filler-order"
    instance_order = "instance-order"
    option = "option"


class ServiceRequestPriority(str, Enum):
    """
    FHIR ServiceRequest.priority value set —
    https://www.hl7.org/fhir/R4/valueset-request-priority.html
    No hyphenated codes — member name == member value.
    """

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


class ServiceRequestQuantityComparator(str, Enum):
    """
    FHIR Duration/Quantity.comparator value set, used by
    ServiceRequest.quantityQuantity and quantityRatio's numerator/
    denominator — https://www.hl7.org/fhir/R4/datatypes.html#Quantity
    Resource-scoped copy. Member name uses a readable identifier; stored
    `.value` is the true FHIR wire symbol.
    """

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"


class ObservationStatus(str, Enum):
    """
    FHIR Observation.status value set (modifier) —
    https://www.hl7.org/fhir/R4/valueset-observation-status.html
    """

    registered = "registered"
    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    corrected = "corrected"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class ObservationQuantityComparator(str, Enum):
    """
    FHIR Duration/Quantity.comparator value set, used by
    Observation.valueQuantity and valueRatio's numerator/denominator
    (both plain Quantity, unlike valueRange/valueSampledData's
    SimpleQuantity, which forbids comparator entirely) —
    https://www.hl7.org/fhir/R4/datatypes.html#Quantity
    Resource-scoped copy. Member name uses a readable identifier; stored
    `.value` is the true FHIR wire symbol.
    """

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"


class ConditionQuantityComparator(str, Enum):
    """
    FHIR Duration/Quantity.comparator value set, used by Condition onsetAge and abatementAge.
    """

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"


class DiagnosticReportStatus(str, Enum):
    """
    FHIR DiagnosticReport.status value set (modifier) --
    https://www.hl7.org/fhir/R4/valueset-diagnostic-report-status.html
    """

    registered = "registered"
    partial = "partial"
    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    corrected = "corrected"
    appended = "appended"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class SpecimenStatus(str, Enum):
    """
    FHIR Specimen.status value set (code, required) --
    https://www.hl7.org/fhir/R4/valueset-specimen-status.html
    """

    available = "available"
    unavailable = "unavailable"
    unsatisfactory = "unsatisfactory"
    entered_in_error = "entered-in-error"


class SpecimenQuantityComparator(str, Enum):
    """
    FHIR Duration/Quantity.comparator value set, used by Specimen collection duration and fastingStatus duration.
    """

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"


class DocumentReferenceStatus(str, Enum):
    """
    FHIR DocumentReference.status value set (code, required) --
    https://www.hl7.org/fhir/R4/valueset-document-reference-status.html
    """

    current = "current"
    superseded = "superseded"
    entered_in_error = "entered-in-error"


class DocumentReferenceDocStatus(str, Enum):
    """
    FHIR DocumentReference.docStatus value set (code, required) --
    http://hl7.org/fhir/composition-status
    """

    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    entered_in_error = "entered-in-error"


class DocumentRelationshipType(str, Enum):
    """
    FHIR DocumentReference.relatesTo.code value set (code, required) --
    http://hl7.org/fhir/document-relationship-type
    """

    replaces = "replaces"
    transforms = "transforms"
    signs = "signs"
    appends = "appends"


# CarePlan enums


class CarePlanStatus(str, Enum):
    """
    FHIR CarePlan.status value set (code, required) --
    http://hl7.org/fhir/request-status
    """

    draft = "draft"
    active = "active"
    on_hold = "on-hold"
    revoked = "revoked"
    completed = "completed"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class CarePlanIntent(str, Enum):
    """
    FHIR CarePlan.intent value set (code, required) --
    http://hl7.org/fhir/care-plan-intent
    """

    proposal = "proposal"
    plan = "plan"
    order = "order"
    option = "option"


class CarePlanActivityStatus(str, Enum):
    """
    FHIR CarePlan.activity.detail.status value set (code, required) --
    http://hl7.org/fhir/care-plan-activity-status
    """

    not_started = "not-started"
    scheduled = "scheduled"
    in_progress = "in-progress"
    on_hold = "on-hold"
    completed = "completed"
    cancelled = "cancelled"
    stopped = "stopped"
    unknown = "unknown"
    entered_in_error = "entered-in-error"


class CarePlanActivityKind(str, Enum):
    """
    FHIR CarePlan.activity.detail.kind value set (code, required) --
    http://hl7.org/fhir/care-plan-activity-kind
    """

    Appointment = "Appointment"
    CommunicationRequest = "CommunicationRequest"
    DeviceRequest = "DeviceRequest"
    MedicationRequest = "MedicationRequest"
    NutritionOrder = "NutritionOrder"
    Task = "Task"
    ServiceRequest = "ServiceRequest"
    VisionPrescription = "VisionPrescription"


class CarePlanQuantityComparator(str, Enum):
    """
    FHIR CarePlan quantity comparator.
    """

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"


# ---------------------------------------------------------------------------
# CareTeam enums
# ---------------------------------------------------------------------------


class CareTeamStatus(str, Enum):
    """
    FHIR CareTeam.status value set (code, required) --
    http://hl7.org/fhir/care-team-status
    """

    proposed = "proposed"
    active = "active"
    suspended = "suspended"
    inactive = "inactive"
    entered_in_error = "entered-in-error"


# ---------------------------------------------------------------------------
# EpisodeOfCare enums
# ---------------------------------------------------------------------------


class EpisodeOfCareStatus(str, Enum):
    """
    FHIR EpisodeOfCare.status value set (code, required) --
    http://hl7.org/fhir/episode-of-care-status
    """

    planned = "planned"
    waitlist = "waitlist"
    active = "active"
    onhold = "onhold"
    finished = "finished"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"


# ---------------------------------------------------------------------------
# FamilyMemberHistory enums
# ---------------------------------------------------------------------------


class FamilyMemberHistoryStatus(str, Enum):
    """
    FHIR FamilyMemberHistory.status value set (code, required) --
    https://www.hl7.org/fhir/R4/valueset-history-status.html
    """

    partial = "partial"
    completed = "completed"
    entered_in_error = "entered-in-error"
    health_unknown = "health-unknown"


class FamilyMemberHistoryQuantityComparator(str, Enum):
    """
    FHIR Duration/Quantity.comparator value set, used by FamilyMemberHistory age and onsetAge.
    """

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"


# ---------------------------------------------------------------------------
# MedicationStatement enums
# ---------------------------------------------------------------------------


class MedicationStatementStatus(str, Enum):
    """
    FHIR MedicationStatement.status value set (code, required) --
    https://www.hl7.org/fhir/R4/valueset-medication-statement-status.html
    """

    active = "active"
    completed = "completed"
    entered_in_error = "entered-in-error"
    intended = "intended"
    stopped = "stopped"
    on_hold = "on-hold"
    unknown = "unknown"
    not_taken = "not-taken"


# ---------------------------------------------------------------------------
# Immunization enums
# ---------------------------------------------------------------------------


class ImmunizationStatus(str, Enum):
    """
    FHIR Immunization.status value set (code, required) --
    https://www.hl7.org/fhir/R4/valueset-immunization-status.html
    """

    completed = "completed"
    entered_in_error = "entered-in-error"
    not_done = "not-done"


# ---------------------------------------------------------------------------
# SpecimenDefinition enums
# ---------------------------------------------------------------------------


class SpecimenDefinitionPreference(str, Enum):
    """Specimen preference: preferred | alternate."""

    preferred = "preferred"
    alternate = "alternate"


class SpecimenDefinitionQuantityComparator(str, Enum):
    """FHIR Quantity.comparator value set for SpecimenDefinition (< | <= | >= | >)."""

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"


class SpecimenDefinitionAdditiveReferenceType(str, Enum):
    """FHIR R4 target types for SpecimenDefinition additive reference."""

    Substance = "Substance"


# ---------------------------------------------------------------------------
# Measure enums
# ---------------------------------------------------------------------------


class MeasureStatus(str, Enum):
    """PublicationStatus: draft | active | retired | unknown."""

    draft = "draft"
    active = "active"
    retired = "retired"
    unknown = "unknown"


class MeasureSubjectReferenceType(str, Enum):
    """Measure.subject allowed reference targets in R4."""

    Group = "Group"


class MeasureContactRole(str, Enum):
    """ContactDetail role discriminator."""

    contact = "contact"
    author = "author"
    editor = "editor"
    reviewer = "reviewer"
    endorser = "endorser"


class MeasureRelatedArtifactType(str, Enum):
    """RelatedArtifact.type: documentation | justification | citation | predecessor | successor | derived-from | depends-on | composed-of."""

    documentation = "documentation"
    justification = "justification"
    citation = "citation"
    predecessor = "predecessor"
    successor = "successor"
    derived_from = "derived-from"
    depends_on = "depends-on"
    composed_of = "composed-of"


class MeasureUseContextValueReferenceType(str, Enum):
    """UsageContext.valueReference allowed target types in R4."""

    PlanDefinition = "PlanDefinition"
    ResearchStudy = "ResearchStudy"
    InsurancePlan = "InsurancePlan"
    HealthcareService = "HealthcareService"
    Group = "Group"
    Location = "Location"
    Organization = "Organization"
    Measure = "Measure"


class MeasureQuantityComparator(str, Enum):
    """Quantity comparator: < | <= | >= | >."""

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"


# ============================================================================
# MeasureReport enums
# ============================================================================


class MeasureReportStatus(str, Enum):
    """MeasureReport.status: complete | pending | error."""

    complete = "complete"
    pending = "pending"
    error = "error"


class MeasureReportType(str, Enum):
    """MeasureReport.type: individual | subject-list | summary | data-collection."""

    individual = "individual"
    subject_list = "subject-list"
    summary = "summary"
    data_collection = "data-collection"


class MeasureReportSubjectReferenceType(str, Enum):
    """MeasureReport.subject allowed reference targets in R4."""

    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Location = "Location"
    Device = "Device"
    RelatedPerson = "RelatedPerson"
    Group = "Group"


class MeasureReportReporterReferenceType(str, Enum):
    """MeasureReport.reporter allowed reference targets in R4."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"
    Location = "Location"


class MeasureReportSubjectResultsReferenceType(str, Enum):
    """MeasureReport population subjectResults allowed reference target in R4."""

    List = "List"


class MeasureReportQuantityComparator(str, Enum):
    """Quantity comparator: < | <= | >= | >."""

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"


class MedicationAdministrationStatus(str, Enum):
    """FHIR MedicationAdministration.status value set (code, required)."""

    in_progress = "in-progress"
    not_done = "not-done"
    on_hold = "on-hold"
    completed = "completed"
    entered_in_error = "entered-in-error"
    stopped = "stopped"
    unknown = "unknown"


class MedicationAdministrationSubjectReferenceType(str, Enum):
    Patient = "Patient"
    Group = "Group"


class MedicationAdministrationContextReferenceType(str, Enum):
    Encounter = "Encounter"
    EpisodeOfCare = "EpisodeOfCare"


class MedicationAdministrationMedicationReferenceType(str, Enum):
    Medication = "Medication"


class MedicationAdministrationPartOfReferenceType(str, Enum):
    MedicationAdministration = "MedicationAdministration"
    Procedure = "Procedure"


class MedicationAdministrationPerformerActorReferenceType(str, Enum):
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Device = "Device"


class MedicationAdministrationReasonReferenceType(str, Enum):
    Condition = "Condition"
    Observation = "Observation"
    DiagnosticReport = "DiagnosticReport"


class MedicationAdministrationRequestReferenceType(str, Enum):
    MedicationRequest = "MedicationRequest"


class MedicationAdministrationDeviceReferenceType(str, Enum):
    Device = "Device"


class MedicationAdministrationNoteAuthorReferenceType(str, Enum):
    Practitioner = "Practitioner"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"


class MedicationAdministrationEventHistoryReferenceType(str, Enum):
    Provenance = "Provenance"










