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
