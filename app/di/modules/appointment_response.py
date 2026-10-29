from dependency_injector import containers, providers

from app.repository.appointment_response import AppointmentResponseRepository
from app.services.appointment_response import AppointmentResponseService


class AppointmentResponseContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    appointment_response_repository = providers.Factory(
        AppointmentResponseRepository,
        session_factory=core.database.provided.session,
    )

    appointment_response_service = providers.Factory(
        AppointmentResponseService,
        repository=appointment_response_repository,
    )
