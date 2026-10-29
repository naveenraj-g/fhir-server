from fastapi import Depends, Path

from app.di.dependencies.diagnostic_report import get_diagnostic_report_service
from app.models.diagnostic_report import DiagnosticReportModel
from app.services.diagnostic_report import DiagnosticReportService


async def resolve_diagnostic_report(
    diagnostic_report_id: int = Path(..., ge=1, description="Public diagnostic_report identifier."),
    service: DiagnosticReportService = Depends(get_diagnostic_report_service),
) -> DiagnosticReportModel:
    """Loads a DiagnosticReport by its public ID, 404 if missing — no
    ownership check (default/gateway-trusted pattern)."""
    return await service.get_by_diagnostic_report_id(diagnostic_report_id)
