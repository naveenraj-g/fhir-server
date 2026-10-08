from dependency_injector import containers, providers

from app.di.core import CoreContainer
from app.di.modules import (
    AllergyIntoleranceContainer,
    AppointmentContainer,
    AuditEventContainer,
    CarePlanContainer,
    ClaimContainer,
    ClaimResponseContainer,
    ConditionContainer,
    CoverageContainer,
    DeviceRequestContainer,
    DiagnosticReportContainer,
    DocumentReferenceContainer,
    EncounterContainer,
    EpisodeOfCareContainer,
    FhirProfileContainer,
    HealthcareServiceContainer,
    ImmunizationContainer,
    InsurancePlanContainer,
    InvoiceContainer,
    LocationContainer,
    MedicationContainer,
    MedicationRequestContainer,
    ObservationContainer,
    OrganizationContainer,
    PatientContainer,
    PractitionerContainer,
    PractitionerRoleContainer,
    ProcedureContainer,
    ProvenanceContainer,
    QuestionnaireResponseContainer,
    RelatedPersonContainer,
    ScheduleContainer,
    ServiceRequestContainer,
    SlotContainer,
    SpecimenContainer,
    TaskContainer,
    TerminologyContainer,
)


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["app"])

    core = providers.Container(CoreContainer)

    patient = providers.Container(
        PatientContainer,
        core=core,
    )

    practitioner = providers.Container(
        PractitionerContainer,
        core=core,
    )

    encounter = providers.Container(
        EncounterContainer,
        core=core,
    )

    appointment = providers.Container(
        AppointmentContainer,
        core=core,
    )

    questionnaire_response = providers.Container(
        QuestionnaireResponseContainer,
        core=core,
    )

    condition = providers.Container(
        ConditionContainer,
        core=core,
    )

    service_request = providers.Container(
        ServiceRequestContainer,
        core=core,
    )

    device_request = providers.Container(
        DeviceRequestContainer,
        core=core,
    )

    diagnostic_report = providers.Container(
        DiagnosticReportContainer,
        core=core,
    )

    medication_request = providers.Container(
        MedicationRequestContainer,
        core=core,
    )

    observation = providers.Container(
        ObservationContainer,
        core=core,
    )

    organization = providers.Container(
        OrganizationContainer,
        core=core,
    )

    procedure = providers.Container(
        ProcedureContainer,
        core=core,
    )

    schedule = providers.Container(
        ScheduleContainer,
        core=core,
    )

    practitioner_role = providers.Container(
        PractitionerRoleContainer,
        core=core,
    )

    slot = providers.Container(
        SlotContainer,
        core=core,
    )

    healthcare_service = providers.Container(
        HealthcareServiceContainer,
        core=core,
    )

    claim = providers.Container(
        ClaimContainer,
        core=core,
    )

    claim_response = providers.Container(
        ClaimResponseContainer,
        core=core,
    )

    invoice = providers.Container(
        InvoiceContainer,
        core=core,
    )

    location = providers.Container(
        LocationContainer,
        core=core,
    )

    coverage = providers.Container(
        CoverageContainer,
        core=core,
    )

    medication = providers.Container(
        MedicationContainer,
        core=core,
    )

    allergy_intolerance = providers.Container(
        AllergyIntoleranceContainer,
        core=core,
    )

    provenance = providers.Container(
        ProvenanceContainer,
        core=core,
    )

    task = providers.Container(
        TaskContainer,
        core=core,
    )

    care_plan = providers.Container(
        CarePlanContainer,
        core=core,
    )

    related_person = providers.Container(
        RelatedPersonContainer,
        core=core,
    )

    specimen = providers.Container(
        SpecimenContainer,
        core=core,
    )

    document_reference = providers.Container(
        DocumentReferenceContainer,
        core=core,
    )

    immunization = providers.Container(
        ImmunizationContainer,
        core=core,
    )

    audit_event = providers.Container(
        AuditEventContainer,
        core=core,
    )

    episode_of_care = providers.Container(
        EpisodeOfCareContainer,
        core=core,
    )

    terminology = providers.Container(
        TerminologyContainer,
        core=core,
    )

    insurance_plan = providers.Container(
        InsurancePlanContainer,
        core=core,
    )

    fhir_profile = providers.Container(
        FhirProfileContainer,
        core=core,
    )

    # Singleton database
    # database = providers.Singleton(
    #     Database,
    #     db_url=settings.FHIR_DATABASE_URL,
    # )

    # # Repository
    # patient_repository = providers.Factory(
    #     PatientRepository,
    #     session_factory=database.provided.session,
    # )
    # # Service
    # patient_service = providers.Factory(
    #     PatientService,
    #     repository=patient_repository,
    # )


# The one process-wide Container instance. Lives here, not in app/main.py,
# specifically so non-request-scoped internal modules (e.g.
# app/fhir/validation/java_validator.py, which isn't wired through FastAPI's
# Depends chain at all) can import this exact instance directly —
# `from app.di.container import container` — without reaching through
# app.main and creating a circular import (app.main already imports deep
# into app.routers -> ... -> java_validator.py). app/main.py imports this
# same object rather than constructing its own, so there is still only ever
# one Container (and therefore one core.database Singleton) per process;
# tests rely on that too (tests/conftest.py's `container.core.database.override(...)`
# must override the exact instance every code path actually reads from).
container = Container()
