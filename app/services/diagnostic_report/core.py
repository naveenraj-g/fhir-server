from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
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
    """All DiagnosticReport business logic. Auth matches Observation/
    Questionnaire/QuestionnaireResponse/ServiceRequest/
    MedicationRequest: tenant scoping comes from the verified JWT's
    activeOrganizationId claim (actor.org_id), never a client-suppliable
    field, and there's no org-less/super-admin bypass — every operation
    requires an org-scoped actor. `user_id` is a plain,
    gateway-forwarded field."""

    def __init__(self, repository: DiagnosticReportRepository):
        self.repository = repository

    def _to_fhir(self, diagnostic_report: DiagnosticReportModel) -> dict:
        return to_fhir_diagnostic_report(diagnostic_report)

    def _to_plain(self, diagnostic_report: DiagnosticReportModel) -> dict:
        return to_plain_diagnostic_report(diagnostic_report)

    async def get_diagnostic_report_scoped(
        self, diagnostic_report_id: int, org_id: str | None
    ) -> DiagnosticReportModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError("DiagnosticReport operation requires an org-scoped token")
        diagnostic_report = await self.repository.get_by_diagnostic_report_id_in_org(
            diagnostic_report_id, org_id
        )
        if not diagnostic_report:
            raise NotFoundError("DiagnosticReport not found")
        return diagnostic_report

    async def list_diagnostic_reports(
        self,
        org_id: str | None = None,
        status: DiagnosticReportStatus | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[DiagnosticReportModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token — same
        invariant as get_diagnostic_report_scoped()."""
        if not org_id:
            raise PermissionDeniedError("DiagnosticReport operation requires an org-scoped token")
        return await self.repository.list(
            org_id=org_id,
            status=DiagnosticReportStatusModel[status.name] if status else None,
            subject=subject,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_diagnostic_report(
        self,
        payload: DiagnosticReportCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> DiagnosticReportModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a DiagnosticReport at all."""
        if not org_id:
            raise PermissionDeniedError("DiagnosticReport creation requires an org-scoped token")
        await self._validate_base_r4(payload_to_fhir_diagnostic_report(payload), org_id)
        diagnostic_report = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "DiagnosticReport created",
            extra={"event": "diagnostic_report.created", "diagnostic_report_id": diagnostic_report.diagnostic_report_id},
        )
        return diagnostic_report

    async def patch_diagnostic_report(
        self,
        diagnostic_report_id: int,
        payload: DiagnosticReportPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> DiagnosticReportModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a resource belonging to a different org both
        raise NotFoundError (404), never 403, so existence isn't leaked."""
        if not org_id:
            self._log_org_scope_miss("patch", diagnostic_report_id, org_id)
            raise NotFoundError("DiagnosticReport not found")
        existing = await self.repository.get_by_diagnostic_report_id_in_org(diagnostic_report_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", diagnostic_report_id, org_id)
            raise NotFoundError("DiagnosticReport not found")

        fragment, touched = patch_fragment_to_fhir_diagnostic_report(payload)
        merged = merge_patch_fragment(to_fhir_diagnostic_report(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(diagnostic_report_id, payload, updated_by)
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

    async def delete_diagnostic_report(self, diagnostic_report_id: int, org_id: str | None = None) -> None:
        """Same org_id ownership gate as patch_diagnostic_report."""
        if not org_id or not await self.repository.diagnostic_report_belongs_to_org(
            diagnostic_report_id, org_id
        ):
            self._log_org_scope_miss("delete", diagnostic_report_id, org_id)
            raise NotFoundError("DiagnosticReport not found")
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

    @staticmethod
    def _log_org_scope_miss(operation: str, diagnostic_report_id: int, org_id: str | None) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such resource" — so this
        log line is the only place the distinction is recorded."""
        logger.warning(
            "DiagnosticReport write rejected by org scope",
            extra={
                "event": "diagnostic_report.org_scope_miss",
                "operation": operation,
                "diagnostic_report_id": diagnostic_report_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
