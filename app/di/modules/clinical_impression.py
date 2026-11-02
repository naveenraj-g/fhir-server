from dependency_injector import containers, providers

from app.repository.clinical_impression import ClinicalImpressionRepository
from app.services.clinical_impression import ClinicalImpressionService


class ClinicalImpressionContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    clinical_impression_repository = providers.Factory(
        ClinicalImpressionRepository,
        session_factory=core.database.provided.session,
    )

    clinical_impression_service = providers.Factory(
        ClinicalImpressionService,
        repository=clinical_impression_repository,
    )
