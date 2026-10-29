from enum import Enum


class QuestionnaireStatus(str, Enum):
    """FHIR R4 Questionnaire.status (1..1, required binding) —
    https://www.hl7.org/fhir/R4/valueset-publication-status.html

    No hyphenated codes here, so member name == member value both at this
    layer and at app.schemas.enums.QuestionnaireStatus — still a distinct
    class (not a reused import) for the same structural reason every other
    resource status gets its own model-layer copy (see
    app.models.encounter.enums.EncounterStatus): SQLAlchemy's `Enum(PyEnum)`
    binds one Postgres type per Python class.
    """

    draft = "draft"
    active = "active"
    retired = "retired"
    unknown = "unknown"


class QuestionnaireItemType(str, Enum):
    """FHIR R4 Questionnaire.item.type (1..1, required binding) —
    https://www.hl7.org/fhir/R4/valueset-item-type.html

    Member name intentionally equals member value, both underscore-only —
    `open-choice` is the one code that isn't a valid Python identifier as
    written, so it becomes `open_choice` here (and at the model layer, the
    true hyphenated FHIR code is rendered explicitly in
    app/fhir/mappers/questionnaire/fhir.py) — same key!=value-at-the-
    schema-layer-only shape as app.models.slot.enums.SlotStatus.
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
    open_choice = "open_choice"
    attachment = "attachment"
    reference = "reference"
    quantity = "quantity"


class QuestionnaireEnableBehavior(str, Enum):
    """FHIR R4 Questionnaire.item.enableBehavior (0..1, required binding
    when present) — https://www.hl7.org/fhir/R4/valueset-questionnaire-enable-behavior.html"""

    all = "all"
    any = "any"


class QuestionnaireItemOperator(str, Enum):
    """FHIR R4 Questionnaire.item.enableWhen.operator (1..1, required
    binding) — https://www.hl7.org/fhir/R4/valueset-questionnaire-enable-operator.html

    Member name uses a readable identifier since `=`/`!=`/`>`/`<`/`>=`/`<=`
    aren't valid Python identifiers (same key!=value-at-the-schema-layer
    shape as app.schemas.enums.EncounterLengthComparator) — this is the
    model-layer copy, so name == value here (both readable); the true FHIR
    symbol is rendered explicitly in app/fhir/mappers/questionnaire/fhir.py.
    """

    exists = "exists"
    eq = "eq"
    ne = "ne"
    gt = "gt"
    lt = "lt"
    ge = "ge"
    le = "le"


class QuestionnaireQuantityComparator(str, Enum):
    """FHIR R4 Quantity.comparator (0..1) — used by every Questionnaire
    field typed as a Quantity choice-type variant (item.enableWhen.answer[x],
    item.initial.value[x], UsageContext.value[x]).
    https://www.hl7.org/fhir/R4/datatypes.html#Quantity

    Resource-scoped copy, not the shared app.models.enums — mirrors
    app.models.encounter.enums.EncounterLengthComparator's own reasoning
    (a tiny, one-off 4-value set not otherwise reused in this codebase at
    the time either was written); member name == member value here
    (readable), the true `<`/`<=`/`>=`/`>` FHIR symbol lives only in
    app.schemas.enums.QuestionnaireQuantityComparator's `.value` and is
    rendered explicitly by the mapper.
    """

    lt = "lt"
    le = "le"
    ge = "ge"
    gt = "gt"


class QuestionnaireUseContextValueReferenceType(str, Enum):
    """Allowed reference types for UsageContext.value when it's a
    Reference — https://www.hl7.org/fhir/R4/metadatatypes.html#UsageContext.
    Only HealthcareService/Location/Organization are modeled resources in
    this system today; the other four are still enumerated (every allowed
    FHIR target type gets a member, per CLAUDE.md's Reference-field
    convention) and simply fail closed at the RESOURCE_REGISTRY existence
    check if ever referenced."""

    PlanDefinition = "PlanDefinition"
    ResearchStudy = "ResearchStudy"
    InsurancePlan = "InsurancePlan"
    HealthcareService = "HealthcareService"
    Group = "Group"
    Location = "Location"
    Organization = "Organization"
