from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.datatypes import merge_patch_fragment
from app.fhir.mappers.measure_report import (
    patch_fragment_to_fhir_measure_report,
    payload_to_fhir_measure_report,
    to_fhir_measure_report,
    to_plain_measure_report,
)
from app.fhir.validation import validate_resource
from app.models.measure_report import MeasureReportModel
from app.repository.measure_report import MeasureReportRepository
from app.schemas.measure_report import (
    MeasureReportCreateSchema,
    MeasureReportPatchSchema,
)

logger = get_logger(__name__)


class MeasureReportService:
    """All MeasureReport business logic."""

    def __init__(self, repository: MeasureReportRepository):
        self.repository = repository

    def _to_fhir(self, model: MeasureReportModel) -> dict:
        return to_fhir_measure_report(model)

    def _to_plain(self, model: MeasureReportModel) -> dict:
        return to_plain_measure_report(model)

    async def get_measure_report_scoped(
        self, measure_report_id: int, org_id: str | None
    ) -> MeasureReportModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token, else NotFoundError (404) if it belongs to a
        different org or doesn't exist."""
        if not org_id:
            raise PermissionDeniedError(
                "MeasureReport operation requires an org-scoped token"
            )
        model = await self.repository.get_by_measure_report_id_in_org(
            measure_report_id, org_id
        )
        if not model:
            raise NotFoundError("MeasureReport not found")
        return model

    async def list_measure_reports(
        self,
        org_id: str | None = None,
        identifier: str | None = None,
        status: str | None = None,
        type: str | None = None,
        measure: str | None = None,
        subject: str | None = None,
        reporter: str | None = None,
        date: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[MeasureReportModel], int]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "MeasureReport operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            identifier=identifier,
            status=status,
            type=type,
            measure=measure,
            subject=subject,
            reporter=reporter,
            date=date,
            limit=limit,
            offset=offset,
            sort=sort,
        )

    async def create_measure_report(
        self,
        payload: MeasureReportCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> MeasureReportModel:
        if not org_id:
            raise PermissionDeniedError(
                "MeasureReport creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "MeasureReport creation requires an authenticated actor"
            )

        await self._validate_base_r4(payload_to_fhir_measure_report(payload), org_id)
        model = await self.repository.create(payload, org_id, created_by)
        logger.info(
            "MeasureReport created",
            extra={
                "event": "measure_report.created",
                "measure_report_id": model.measure_report_id,
            },
        )
        return model

    async def patch_measure_report(
        self,
        measure_report_id: int,
        payload: MeasureReportPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> MeasureReportModel:
        if not org_id:
            self._log_org_scope_miss("patch", measure_report_id, org_id)
            raise NotFoundError("MeasureReport not found")
        existing = await self.repository.get_by_measure_report_id_in_org(
            measure_report_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", measure_report_id, org_id)
            raise NotFoundError("MeasureReport not found")

        fragment, touched = patch_fragment_to_fhir_measure_report(payload)
        merged = merge_patch_fragment(
            to_fhir_measure_report(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch(
            measure_report_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("MeasureReport not found")
        logger.info(
            "MeasureReport updated",
            extra={
                "event": "measure_report.updated",
                "measure_report_id": measure_report_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_measure_report(
        self, measure_report_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.measure_report_belongs_to_org(
            measure_report_id, org_id
        ):
            self._log_org_scope_miss("delete", measure_report_id, org_id)
            raise NotFoundError("MeasureReport not found")
        deleted = await self.repository.delete(measure_report_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("MeasureReport not found")
        logger.info(
            "MeasureReport deleted",
            extra={
                "event": "measure_report.deleted",
                "measure_report_id": measure_report_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource("MeasureReport", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "MeasureReport failed base R4 validation",
                extra={
                    "event": "measure_report.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, measure_report_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "MeasureReport write rejected by org scope",
            extra={
                "event": "measure_report.org_scope_miss",
                "operation": operation,
                "measure_report_id": measure_report_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
