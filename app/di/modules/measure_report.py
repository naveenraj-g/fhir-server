from dependency_injector import containers, providers

from app.repository.measure_report import MeasureReportRepository
from app.services.measure_report import MeasureReportService


class MeasureReportContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    measure_report_repository = providers.Factory(
        MeasureReportRepository,
        session_factory=core.database.provided.session,
    )

    measure_report_service = providers.Factory(
        MeasureReportService,
        repository=measure_report_repository,
    )
