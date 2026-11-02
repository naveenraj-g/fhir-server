from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.clinical_impression import ClinicalImpressionService


@inject
def get_clinical_impression_service(
    service: ClinicalImpressionService = Depends(
        Provide[Container.clinical_impression.clinical_impression_service]
    ),
) -> ClinicalImpressionService:
    return service
