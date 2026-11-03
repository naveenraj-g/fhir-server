from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.measure_report import MeasureReportService


@inject
def get_measure_report_service(
    service: MeasureReportService = Depends(
        Provide[Container.measure_report.measure_report_service]
    ),
) -> MeasureReportService:
    return service
