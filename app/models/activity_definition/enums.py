from enum import Enum


class ActivityDefinitionStatus(str, Enum):
    """PublicationStatus: draft | active | retired | unknown."""

    draft = "draft"
    active = "active"
    retired = "retired"
    unknown = "unknown"


class ActivityDefinitionSubjectReferenceType(str, Enum):
    """ActivityDefinition.subjectReference Reference(Group)."""

    Group = "Group"


class ActivityDefinitionContactRole(str, Enum):
    """ContactDetail role discriminator."""

    contact = "contact"
    author = "author"
    editor = "editor"
    reviewer = "reviewer"
    endorser = "endorser"


class ActivityDefinitionRelatedArtifactType(str, Enum):
    """RelatedArtifact.type: documentation | justification | citation | predecessor | successor | derived-from | depends-on | composed-of."""

    documentation = "documentation"
    justification = "justification"
    citation = "citation"
    predecessor = "predecessor"
    successor = "successor"
    derived_from = "derived-from"
    depends_on = "depends-on"
    composed_of = "composed-of"


class ActivityDefinitionKind(str, Enum):
    """RequestResourceType."""

    Appointment = "Appointment"
    AppointmentResponse = "AppointmentResponse"
    CarePlan = "CarePlan"
    Claim = "Claim"
    CommunicationRequest = "CommunicationRequest"
    Contract = "Contract"
    DeviceRequest = "DeviceRequest"
    EnrollmentRequest = "EnrollmentRequest"
    ImmunizationRecommendation = "ImmunizationRecommendation"
    MedicationRequest = "MedicationRequest"
    NutritionOrder = "NutritionOrder"
    ServiceRequest = "ServiceRequest"
    SupplyRequest = "SupplyRequest"
    Task = "Task"
    VisionPrescription = "VisionPrescription"


class ActivityDefinitionIntent(str, Enum):
    """RequestIntent: proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option."""

    proposal = "proposal"
    plan = "plan"
    directive = "directive"
    order = "order"
    original_order = "original-order"
    reflex_order = "reflex-order"
    filler_order = "filler-order"
    instance_order = "instance-order"
    option = "option"


class ActivityDefinitionPriority(str, Enum):
    """RequestPriority: routine | urgent | asap | stat."""

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


class ActivityDefinitionParticipantType(str, Enum):
    """ActivityParticipantType: patient | practitioner | related-person | device."""

    patient = "patient"
    practitioner = "practitioner"
    related_person = "related-person"
    device = "device"


class ActivityDefinitionProductReferenceType(str, Enum):
    """ActivityDefinition.product Reference(Medication | Substance)."""

    Medication = "Medication"
    Substance = "Substance"


class ActivityDefinitionQuantityComparator(str, Enum):
    """Quantity comparator: < | <= | >= | >."""

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"


class ActivityDefinitionLocationReferenceType(str, Enum):
    """ActivityDefinition.location Reference(Location)."""

    Location = "Location"


class ActivityDefinitionSpecimenRequirementReferenceType(str, Enum):
    """ActivityDefinition.specimenRequirement Reference(SpecimenDefinition)."""

    SpecimenDefinition = "SpecimenDefinition"


class ActivityDefinitionObservationRequirementReferenceType(str, Enum):
    """ActivityDefinition.observationRequirement Reference(ObservationDefinition)."""

    ObservationDefinition = "ObservationDefinition"


class ActivityDefinitionObservationResultRequirementReferenceType(str, Enum):
    """ActivityDefinition.observationResultRequirement Reference(ObservationDefinition)."""

    ObservationDefinition = "ObservationDefinition"


class ActivityDefinitionUseContextValueReferenceType(str, Enum):
    """UsageContext.valueReference allowed target resource types."""

    PlanDefinition = "PlanDefinition"
    ResearchStudy = "ResearchStudy"
    InsurancePlan = "InsurancePlan"
    HealthcareService = "HealthcareService"
    Group = "Group"
    Location = "Location"
    Organization = "Organization"


class ActivityDefinitionAssignerReferenceType(str, Enum):
    """ActivityDefinition.identifier.assigner Reference(Organization)."""

    Organization = "Organization"
