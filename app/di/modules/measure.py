from dependency_injector import containers, providers

from app.repository.measure import MeasureRepository
from app.services.measure import MeasureService


class MeasureContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    measure_repository = providers.Factory(
        MeasureRepository,
        session_factory=core.database.provided.session,
    )

    measure_service = providers.Factory(
        MeasureService,
        repository=measure_repository,
    )
