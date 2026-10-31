from enum import Enum


class PlanDefinitionStatus(str, Enum):
    """PublicationStatus: draft | active | retired | unknown."""

    draft = "draft"
    active = "active"
    retired = "retired"
    unknown = "unknown"


class PlanDefinitionSubjectReferenceType(str, Enum):
    """PlanDefinition.subjectReference Reference(Group)."""

    Group = "Group"


class PlanDefinitionContactRole(str, Enum):
    """ContactDetail role discriminator."""

    contact = "contact"
    author = "author"
    editor = "editor"
    reviewer = "reviewer"
    endorser = "endorser"


class PlanDefinitionRelatedArtifactType(str, Enum):
    """RelatedArtifact.type: documentation | justification | citation | predecessor | successor | derived-from | depends-on | composed-of."""

    documentation = "documentation"
    justification = "justification"
    citation = "citation"
    predecessor = "predecessor"
    successor = "successor"
    derived_from = "derived-from"
    depends_on = "depends-on"
    composed_of = "composed-of"


class PlanDefinitionUseContextValueReferenceType(str, Enum):
    """UsageContext.valueReference allowed target types in R4."""

    PlanDefinition = "PlanDefinition"
    ResearchStudy = "ResearchStudy"
    InsurancePlan = "InsurancePlan"
    HealthcareService = "HealthcareService"
    Group = "Group"
    Location = "Location"
    Organization = "Organization"


class PlanDefinitionQuantityComparator(str, Enum):
    """Quantity comparator: < | <= | >= | >."""

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"


class PlanDefinitionActionPriority(str, Enum):
    """RequestPriority: routine | urgent | asap | stat."""

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


class PlanDefinitionActionGroupingBehavior(str, Enum):
    """ActionGroupingBehavior: visual-group | logical-group | sentence-group."""

    visual_group = "visual-group"
    logical_group = "logical-group"
    sentence_group = "sentence-group"


class PlanDefinitionActionSelectionBehavior(str, Enum):
    """ActionSelectionBehavior: any | all | all-or-none | exactly-one | at-most-one | one-or-more."""

    any = "any"
    all = "all"
    all_or_none = "all-or-none"
    exactly_one = "exactly-one"
    at_most_one = "at-most-one"
    one_or_more = "one-or-more"


class PlanDefinitionActionRequiredBehavior(str, Enum):
    """ActionRequiredBehavior: must | could | must-unless-documented."""

    must = "must"
    could = "could"
    must_unless_documented = "must-unless-documented"


class PlanDefinitionActionPrecheckBehavior(str, Enum):
    """ActionPrecheckBehavior: yes | no."""

    yes = "yes"
    no = "no"


class PlanDefinitionActionCardinalityBehavior(str, Enum):
    """ActionCardinalityBehavior: single | multiple."""

    single = "single"
    multiple = "multiple"


class PlanDefinitionActionConditionKind(str, Enum):
    """ActionConditionKind: applicability | start | stop."""

    applicability = "applicability"
    start = "start"
    stop = "stop"


class PlanDefinitionActionRelationshipType(str, Enum):
    """ActionRelationshipType: before-start | before | before-end | concurrent-with-start | concurrent | concurrent-with-end | after-start | after | after-end."""

    before_start = "before-start"
    before = "before"
    before_end = "before-end"
    concurrent_with_start = "concurrent-with-start"
    concurrent = "concurrent"
    concurrent_with_end = "concurrent-with-end"
    after_start = "after-start"
    after = "after"
    after_end = "after-end"


class PlanDefinitionActionParticipantType(str, Enum):
    """ActionParticipantType: patient | practitioner | related-person | device."""

    patient = "patient"
    practitioner = "practitioner"
    related_person = "related-person"
    device = "device"
