from dependency_injector import containers, providers

from app.repository.allergy_intolerance import AllergyIntoleranceRepository
from app.services.allergy_intolerance import AllergyIntoleranceService


class AllergyIntoleranceContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    allergy_intolerance_repository = providers.Factory(
        AllergyIntoleranceRepository,
        session_factory=core.database.provided.session,
    )

    allergy_intolerance_service = providers.Factory(
        AllergyIntoleranceService,
        repository=allergy_intolerance_repository,
    )
