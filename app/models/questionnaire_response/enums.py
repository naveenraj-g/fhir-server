from enum import Enum


class QuestionnaireResponseStatus(str, Enum):
    """FHIR R4 QuestionnaireResponse.status (1..1, required binding) —
    https://www.hl7.org/fhir/R4/valueset-questionnaire-answers-status.html

    Member name intentionally equals member value, both underscore-only —
    `in-progress` and `entered-in-error` aren't valid Python identifiers as
    written, so they become `in_progress`/`entered_in_error` here. The true
    hyphenated FHIR code is recovered in the mapper via a plain
    `.replace("_", "-")` (every member here has at most the one
    underscore-for-hyphen substitution that needs) — same
    key!=value-at-the-schema-layer-only shape as
    app.models.questionnaire.enums.QuestionnaireItemType.
    """

    in_progress = "in_progress"
    completed = "completed"
    amended = "amended"
    entered_in_error = "entered_in_error"
    stopped = "stopped"


class QuestionnaireResponseBasedOnReferenceType(str, Enum):
    """Allowed reference types for QuestionnaireResponse.basedOn
    (Reference(CarePlan | ServiceRequest)). Neither is a modeled resource
    in this system, so the existence check is never attempted for this
    field — the reference_identifier_* logical-reference fallback is, in
    practice, the only reliably populated set of columns. Stored as DB
    type name 'questionnaire_response_based_on_reference_type'."""

    CarePlan = "CarePlan"
    ServiceRequest = "ServiceRequest"


class QuestionnaireResponsePartOfReferenceType(str, Enum):
    """Allowed reference types for QuestionnaireResponse.partOf
    (Reference(Observation | Procedure)). Neither is a modeled resource in
    this system — same reasoning as the basedOn enum above. Stored as DB
    type name 'questionnaire_response_part_of_reference_type'."""

    Observation = "Observation"
    Procedure = "Procedure"


class QuestionnaireResponseAuthorReferenceType(str, Enum):
    """Allowed reference types for QuestionnaireResponse.author
    (Reference(Device | Practitioner | PractitionerRole | Patient |
    RelatedPerson | Organization)). Of these six, only Practitioner/
    PractitionerRole/Organization are modeled resources in this system
    (registered in RESOURCE_REGISTRY) — Device/Patient/RelatedPerson rows
    always rely on the identifier fallback instead; the existence check is
    only ever attempted for the three modeled types (see
    app.repository.questionnaire_response._shared's
    _MODELED_AUTHOR_TYPES). Stored as DB type name
    'questionnaire_response_author_reference_type'."""

    Device = "Device"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"


class QuestionnaireResponseSourceReferenceType(str, Enum):
    """Allowed reference types for QuestionnaireResponse.source
    (Reference(Patient | Practitioner | PractitionerRole |
    RelatedPerson)). Of these four, only Practitioner/PractitionerRole are
    modeled resources in this system — same reasoning as the author enum
    above. Stored as DB type name
    'questionnaire_response_source_reference_type'."""

    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"


class QuestionnaireResponseQuantityComparator(str, Enum):
    """FHIR R4 Quantity.comparator (0..1) — used by
    QuestionnaireResponseAnswer.value_quantity. Resource-scoped copy, not
    the shared app.models.enums — mirrors
    app.models.questionnaire.enums.QuestionnaireQuantityComparator's own
    reasoning (SQLAlchemy's Enum(PyEnum) binds one Postgres type per Python
    class, so sharing a universal concept like Quantity.comparator across
    resources still means a fresh model-layer enum per resource). Member
    name == member value here (readable); the true `<`/`<=`/`>=`/`>` FHIR
    symbol is rendered explicitly by the mapper."""

    lt = "lt"
    le = "le"
    ge = "ge"
    gt = "gt"
