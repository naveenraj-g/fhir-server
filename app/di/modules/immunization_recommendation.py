from dependency_injector import containers, providers

from app.repository.immunization_recommendation import ImmunizationRecommendationRepository
from app.services.immunization_recommendation import ImmunizationRecommendationService


class ImmunizationRecommendationContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    immunization_recommendation_repository = providers.Factory(
        ImmunizationRecommendationRepository,
        session_factory=core.database.provided.session,
    )

    immunization_recommendation_service = providers.Factory(
        ImmunizationRecommendationService,
        repository=immunization_recommendation_repository,
    )
