from enum import Enum


class CarePlanStatus(str, Enum):
    """FHIR CarePlan.status value set (code, required) —
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
    """FHIR CarePlan.intent value set (code, required) —
    http://hl7.org/fhir/care-plan-intent
    """

    proposal = "proposal"
    plan = "plan"
    order = "order"
    option = "option"


class CarePlanActivityStatus(str, Enum):
    """FHIR CarePlan.activity.detail.status value set (code, required) —
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
    """FHIR CarePlan.activity.detail.kind value set (code, required) —
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
    """FHIR CarePlan quantity comparator."""

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"


class CarePlanSubjectReferenceType(str, Enum):
    """CarePlan.subject Reference(Patient | Group)."""

    Patient = "Patient"
    Group = "Group"


class CarePlanEncounterReferenceType(str, Enum):
    """CarePlan.encounter Reference(Encounter)."""

    Encounter = "Encounter"


class CarePlanAuthorReferenceType(str, Enum):
    """CarePlan.author Reference(Patient | Practitioner | PractitionerRole | RelatedPerson | Organization | CareTeam)."""

    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"
    CareTeam = "CareTeam"


class CarePlanContributorReferenceType(str, Enum):
    """CarePlan.contributor Reference(Patient | Practitioner | PractitionerRole | RelatedPerson | Organization | CareTeam)."""

    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"
    CareTeam = "CareTeam"


class CarePlanCareTeamReferenceType(str, Enum):
    """CarePlan.careTeam Reference(CareTeam)."""

    CareTeam = "CareTeam"


class CarePlanAddressesReferenceType(str, Enum):
    """CarePlan.addresses Reference(Condition)."""

    Condition = "Condition"


class CarePlanGoalReferenceType(str, Enum):
    """CarePlan.goal Reference(Goal)."""

    Goal = "Goal"


class CarePlanBasedOnReferenceType(str, Enum):
    """CarePlan.basedOn Reference(CarePlan | ServiceRequest | NutritionOrder)."""

    CarePlan = "CarePlan"
    ServiceRequest = "ServiceRequest"
    NutritionOrder = "NutritionOrder"


class CarePlanReplacesReferenceType(str, Enum):
    """CarePlan.replaces Reference(CarePlan)."""

    CarePlan = "CarePlan"


class CarePlanPartOfReferenceType(str, Enum):
    """CarePlan.partOf Reference(CarePlan)."""

    CarePlan = "CarePlan"


class CarePlanActivityReferenceType(str, Enum):
    """CarePlan.activity.reference Reference(Appointment | CommunicationRequest | DeviceRequest | MedicationRequest | NutritionOrder | Task | ServiceRequest | VisionPrescription | RequestGroup)."""

    Appointment = "Appointment"
    CommunicationRequest = "CommunicationRequest"
    DeviceRequest = "DeviceRequest"
    MedicationRequest = "MedicationRequest"
    NutritionOrder = "NutritionOrder"
    Task = "Task"
    ServiceRequest = "ServiceRequest"
    VisionPrescription = "VisionPrescription"
    RequestGroup = "RequestGroup"


class CarePlanActivityDetailPerformerReferenceType(str, Enum):
    """CarePlan.activity.detail.performer Reference(Practitioner | PractitionerRole | Organization | RelatedPerson | Patient | CareTeam | HealthcareService | Device)."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"
    RelatedPerson = "RelatedPerson"
    Patient = "Patient"
    CareTeam = "CareTeam"
    HealthcareService = "HealthcareService"
    Device = "Device"


class CarePlanActivityDetailReasonReferenceType(str, Enum):
    """CarePlan.activity.detail.reasonReference Reference(Condition | Observation | DiagnosticReport | DocumentReference)."""

    Condition = "Condition"
    Observation = "Observation"
    DiagnosticReport = "DiagnosticReport"
    DocumentReference = "DocumentReference"


class CarePlanLocationReferenceType(str, Enum):
    """CarePlan.activity.detail.location Reference(Location)."""

    Location = "Location"


class CarePlanProductReferenceType(str, Enum):
    """CarePlan.activity.detail.product Reference(Medication | Substance)."""

    Medication = "Medication"
    Substance = "Substance"
