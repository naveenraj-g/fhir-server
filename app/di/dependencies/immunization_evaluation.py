from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.immunization_evaluation import ImmunizationEvaluationService


@inject
def get_immunization_evaluation_service(
    service: ImmunizationEvaluationService = Depends(
        Provide[Container.immunization_evaluation.immunization_evaluation_service]
    ),
) -> ImmunizationEvaluationService:
    return service
