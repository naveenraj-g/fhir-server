from dependency_injector import containers, providers

from app.di.core import CoreContainer
from app.di.modules import (
    FhirProfileContainer,
    HealthcareServiceContainer,
    LocationContainer,
    OrganizationContainer,
    PractitionerContainer,
    PractitionerRoleContainer,
    ScheduleContainer,
    SlotContainer,
    TerminologyContainer,
)


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["app"])

    core = providers.Container(CoreContainer)

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

    practitioner = providers.Container(
        PractitionerContainer,
        core=core,
    )

    practitioner_role = providers.Container(
        PractitionerRoleContainer,
        core=core,
    )

    schedule = providers.Container(
        ScheduleContainer,
        core=core,
    )

    slot = providers.Container(
        SlotContainer,
        core=core,
    )

    terminology = providers.Container(
        TerminologyContainer,
        core=core,
    )

    fhir_profile = providers.Container(
        FhirProfileContainer,
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
