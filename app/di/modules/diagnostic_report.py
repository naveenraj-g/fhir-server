from dependency_injector import containers, providers

from app.repository.diagnostic_report import DiagnosticReportRepository
from app.services.diagnostic_report import DiagnosticReportService


class DiagnosticReportContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    diagnostic_report_repository = providers.Factory(
        DiagnosticReportRepository,
        session_factory=core.database.provided.session,
    )

    diagnostic_report_service = providers.Factory(
        DiagnosticReportService,
        repository=diagnostic_report_repository,
    )
