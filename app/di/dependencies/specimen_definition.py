from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.specimen_definition import SpecimenDefinitionService


@inject
def get_specimen_definition_service(
    service: SpecimenDefinitionService = Depends(
        Provide[Container.specimen_definition.specimen_definition_service]
    ),
) -> SpecimenDefinitionService:
    return service
