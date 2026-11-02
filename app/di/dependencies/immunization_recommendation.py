from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.immunization_recommendation import ImmunizationRecommendationService


@inject
def get_immunization_recommendation_service(
    service: ImmunizationRecommendationService = Depends(
        Provide[Container.immunization_recommendation.immunization_recommendation_service]
    ),
) -> ImmunizationRecommendationService:
    return service
