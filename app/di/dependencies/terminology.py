from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.terminology import TerminologyService
from app.terminology.client import TerminologyClient
from app.terminology.dispatch import get_terminology_client as _dispatch


@inject
def get_terminology_client(
    embedded_service: TerminologyService = Depends(
        Provide[Container.terminology.terminology_service]
    ),
) -> TerminologyClient:
    """FastAPI dependency wrapper around app/terminology/dispatch.py's
    backend swap — still resolves the embedded TerminologyService through
    DI (Provide[...]) so tests' container overrides keep working, then
    hands it to the dispatch function, which decides whether to actually
    use it or build a RemoteTerminologyClient instead."""
    return _dispatch(embedded_service)
