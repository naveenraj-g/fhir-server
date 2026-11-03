from enum import Enum


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
