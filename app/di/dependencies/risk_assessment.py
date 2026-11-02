from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.risk_assessment import RiskAssessmentService


@inject
def get_risk_assessment_service(
    service: RiskAssessmentService = Depends(
        Provide[Container.risk_assessment.risk_assessment_service]
    ),
) -> RiskAssessmentService:
    return service
