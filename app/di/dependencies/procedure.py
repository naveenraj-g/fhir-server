from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.procedure import ProcedureService


@inject
def get_procedure_service(
    service: ProcedureService = Depends(
        Provide[Container.procedure.procedure_service]
    ),
) -> ProcedureService:
    return service
