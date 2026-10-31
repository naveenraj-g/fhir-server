from dependency_injector import containers, providers

from app.di.core import CoreContainer
from app.di.modules import (
    ActivityDefinitionContainer,
    AllergyIntoleranceContainer,
    AppointmentContainer,
    AppointmentResponseContainer,
    CarePlanContainer,
    CareTeamContainer,
    ConditionContainer,
    ConsentContainer,
    DiagnosticReportContainer,
    DocumentReferenceContainer,
    EncounterContainer,
    EpisodeOfCareContainer,
    FhirProfileContainer,
    FlagContainer,
    GroupContainer,
    HealthcareServiceContainer,
    LocationContainer,
    MedicationRequestContainer,
    ObservationContainer,
    ObservationDefinitionContainer,
    OrganizationContainer,
    PatientContainer,
    PlanDefinitionContainer,
    PractitionerContainer,
    PractitionerRoleContainer,
    ProcedureContainer,
    RelatedPersonContainer,
    QuestionnaireContainer,
    QuestionnaireResponseContainer,
    ScheduleContainer,
    ServiceRequestContainer,
    SlotContainer,
    SpecimenContainer,
    TerminologyContainer,
    TaskContainer,
    GoalContainer,
    CommunicationRequestContainer,
)


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["app"])

    core = providers.Container(CoreContainer)

    activity_definition = providers.Container(
        ActivityDefinitionContainer,
        core=core,
    )

    allergy_intolerance = providers.Container(
        AllergyIntoleranceContainer,
        core=core,
    )

    appointment = providers.Container(
        AppointmentContainer,
        core=core,
    )

    appointment_response = providers.Container(
        AppointmentResponseContainer,
        core=core,
    )

    care_plan = providers.Container(
        CarePlanContainer,
        core=core,
    )

    care_team = providers.Container(
        CareTeamContainer,
        core=core,
    )

    condition = providers.Container(
        ConditionContainer,
        core=core,
    )

    consent = providers.Container(
        ConsentContainer,
        core=core,
    )

    encounter = providers.Container(
        EncounterContainer,
        core=core,
    )

    episode_of_care = providers.Container(
        EpisodeOfCareContainer,
        core=core,
    )

    group = providers.Container(
        GroupContainer,
        core=core,
    )

    organization = providers.Container(
        OrganizationContainer,
        core=core,
    )

    location = providers.Container(
        LocationContainer,
        core=core,
    )

    healthcare_service = providers.Container(
        HealthcareServiceContainer,
        core=core,
    )

    patient = providers.Container(
        PatientContainer,
        core=core,
    )

    plan_definition = providers.Container(
        PlanDefinitionContainer,
        core=core,
    )

    practitioner = providers.Container(
        PractitionerContainer,
        core=core,
    )

    practitioner_role = providers.Container(
        PractitionerRoleContainer,
        core=core,
    )

    procedure = providers.Container(
        ProcedureContainer,
        core=core,
    )

    observation = providers.Container(
        ObservationContainer,
        core=core,
    )

    observation_definition = providers.Container(
        ObservationDefinitionContainer,
        core=core,
    )

    diagnostic_report = providers.Container(
        DiagnosticReportContainer,
        core=core,
    )

    document_reference = providers.Container(
        DocumentReferenceContainer,
        core=core,
    )

    medication_request = providers.Container(
        MedicationRequestContainer,
        core=core,
    )

    questionnaire = providers.Container(
        QuestionnaireContainer,
        core=core,
    )

    questionnaire_response = providers.Container(
        QuestionnaireResponseContainer,
        core=core,
    )

    schedule = providers.Container(
        ScheduleContainer,
        core=core,
    )

    service_request = providers.Container(
        ServiceRequestContainer,
        core=core,
    )

    slot = providers.Container(
        SlotContainer,
        core=core,
    )

    specimen = providers.Container(
        SpecimenContainer,
        core=core,
    )

    terminology = providers.Container(
        TerminologyContainer,
        core=core,
    )


    related_person = providers.Container(
        RelatedPersonContainer,
        core=core,
    )

    flag = providers.Container(
        FlagContainer,
        core=core,
    )

    fhir_profile = providers.Container(
        FhirProfileContainer,
        core=core,
    )

    task = providers.Container(
        TaskContainer,
        core=core,
    )

    goal = providers.Container(
        GoalContainer,
        core=core,
    )

    communication_request = providers.Container(
        CommunicationRequestContainer,
        core=core,
    )


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
