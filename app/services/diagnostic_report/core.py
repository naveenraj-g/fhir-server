from app.core.logging import get_logger
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.diagnostic_report import (
    merge_patch_fragment,
    patch_fragment_to_fhir_diagnostic_report,
    payload_to_fhir_diagnostic_report,
    to_fhir_diagnostic_report,
    to_plain_diagnostic_report,
)
from app.fhir.validation import validate_resource
from app.models.diagnostic_report import DiagnosticReportModel, DiagnosticReportStatus as DiagnosticReportStatusModel
from app.repository.diagnostic_report import DiagnosticReportRepository
from app.schemas.diagnostic_report import DiagnosticReportCreateSchema, DiagnosticReportPatchSchema
from app.schemas.enums import DiagnosticReportStatus

logger = get_logger(__name__)


class _CoreMixin:
    """All DiagnosticReport business logic. Default (gateway-trusted)
    pattern — same as Observation/QuestionnaireResponse/ServiceRequest/
    MedicationRequest: no org-scoped existence check or ownership
    enforcement at all."""

    def __init__(self, repository: DiagnosticReportRepository):
        self.repository = repository

    def _to_fhir(self, diagnostic_report: DiagnosticReportModel) -> dict:
        return to_fhir_diagnostic_report(diagnostic_report)

    def _to_plain(self, diagnostic_report: DiagnosticReportModel) -> dict:
        return to_plain_diagnostic_report(diagnostic_report)

    async def get_by_diagnostic_report_id(self, diagnostic_report_id: int) -> DiagnosticReportModel:
        diagnostic_report = await self.repository.get_by_diagnostic_report_id(diagnostic_report_id)
        if not diagnostic_report:
            raise NotFoundError("DiagnosticReport not found")
        return diagnostic_report

    async def get_me(
        self,
        user_id: str,
        tenant_id: str | None = None,
        status: DiagnosticReportStatus | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[DiagnosticReportModel], int | None]:
        return await self.repository.get_me(
            user_id=user_id,
            tenant_id=tenant_id,
            status=DiagnosticReportStatusModel[status.name] if status else None,
            subject=subject,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def list_diagnostic_reports(
        self,
        tenant_id: str | None = None,
        user_id: str | None = None,
        status: DiagnosticReportStatus | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[DiagnosticReportModel], int | None]:
        return await self.repository.list(
            tenant_id=tenant_id,
            user_id=user_id,
            status=DiagnosticReportStatusModel[status.name] if status else None,
            subject=subject,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_diagnostic_report(self, payload: DiagnosticReportCreateSchema) -> DiagnosticReportModel:
        await self._validate_base_r4(payload_to_fhir_diagnostic_report(payload), payload.tenant_id)
        diagnostic_report = await self.repository.create_full(payload)
        logger.info(
            "DiagnosticReport created",
            extra={"event": "diagnostic_report.created", "diagnostic_report_id": diagnostic_report.diagnostic_report_id},
        )
        return diagnostic_report

    async def patch_diagnostic_report(self, diagnostic_report_id: int, payload: DiagnosticReportPatchSchema) -> DiagnosticReportModel:
        existing = await self.repository.get_by_diagnostic_report_id(diagnostic_report_id)
        if not existing:
            raise NotFoundError("DiagnosticReport not found")

        fragment, touched = patch_fragment_to_fhir_diagnostic_report(payload)
        merged = merge_patch_fragment(to_fhir_diagnostic_report(existing), fragment, touched)
        await self._validate_base_r4(merged, existing.tenant_id)

        updated = await self.repository.patch_full(diagnostic_report_id, payload)
        if not updated:
            raise NotFoundError("DiagnosticReport not found")
        logger.info(
            "DiagnosticReport updated",
            extra={
                "event": "diagnostic_report.updated",
                "diagnostic_report_id": diagnostic_report_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_diagnostic_report(self, diagnostic_report_id: int) -> None:
        deleted = await self.repository.delete(diagnostic_report_id)
        if not deleted:
            raise NotFoundError("DiagnosticReport not found")
        logger.info(
            "DiagnosticReport deleted",
            extra={"event": "diagnostic_report.deleted", "diagnostic_report_id": diagnostic_report_id},
        )

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource("DiagnosticReport", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "DiagnosticReport failed base R4 validation",
                extra={"event": "diagnostic_report.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)
