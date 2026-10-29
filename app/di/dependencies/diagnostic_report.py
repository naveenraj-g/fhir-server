from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.diagnostic_report import DiagnosticReportService


@inject
def get_diagnostic_report_service(
    service: DiagnosticReportService = Depends(Provide[Container.diagnostic_report.diagnostic_report_service]),
) -> DiagnosticReportService:
    return service
