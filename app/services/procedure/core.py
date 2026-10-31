from datetime import date, datetime

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.procedure import (
    merge_patch_fragment,
    patch_fragment_to_fhir_procedure,
    payload_to_fhir_procedure,
    to_fhir_procedure,
    to_plain_procedure,
)
from app.fhir.validation import validate_resource
from app.models.procedure import ProcedureModel
from app.repository.procedure import ProcedureRepository
from app.schemas.procedure import ProcedureCreateSchema, ProcedurePatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Procedure business logic."""

    def __init__(self, repository: ProcedureRepository):
        self.repository = repository

    def _to_fhir(self, procedure: ProcedureModel) -> dict:
        return to_fhir_procedure(procedure)

    def _to_plain(self, procedure: ProcedureModel) -> dict:
        return to_plain_procedure(procedure)

    async def get_procedure_scoped(
        self, procedure_id: int, org_id: str | None
    ) -> ProcedureModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError("Procedure operation requires an org-scoped token")
        procedure = await self.repository.get_by_procedure_id_in_org(
            procedure_id, org_id
        )
        if not procedure:
            raise NotFoundError("Procedure not found")
        return procedure

    async def list_procedures(
        self,
        org_id: str | None = None,
        status: str | None = None,
        patient: str | None = None,
        subject: str | None = None,
        encounter: str | None = None,
        code: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        location: str | None = None,
        based_on: str | None = None,
        part_of: str | None = None,
        category: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ProcedureModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError("Procedure operation requires an org-scoped token")
        return await self.repository.list(
            org_id=org_id,
            status=status,
            patient=patient,
            subject=subject,
            encounter=encounter,
            code=code,
            date_val=date_val,
            date_from=date_from,
            date_to=date_to,
            location=location,
            based_on=based_on,
            part_of=part_of,
            category=category,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_procedure(
        self,
        payload: ProcedureCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> ProcedureModel:
        if not org_id:
            raise PermissionDeniedError("Procedure creation requires an org-scoped token")
        if not created_by:
            raise PermissionDeniedError("Procedure creation requires an authenticated actor")

        await self._validate_base_r4(payload_to_fhir_procedure(payload), org_id)
        proc = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "Procedure created",
            extra={"event": "procedure.created", "procedure_id": proc.procedure_id},
        )
        return proc

    async def patch_procedure(
        self,
        procedure_id: int,
        payload: ProcedurePatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> ProcedureModel:
        if not org_id:
            self._log_org_scope_miss("patch", procedure_id, org_id)
            raise NotFoundError("Procedure not found")
        existing = await self.repository.get_by_procedure_id_in_org(procedure_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", procedure_id, org_id)
            raise NotFoundError("Procedure not found")

        fragment, touched = patch_fragment_to_fhir_procedure(payload)
        merged = merge_patch_fragment(to_fhir_procedure(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            procedure_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("Procedure not found")
        logger.info(
            "Procedure updated",
            extra={
                "event": "procedure.updated",
                "procedure_id": procedure_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_procedure(self, procedure_id: int, org_id: str | None = None) -> None:
        if not org_id or not await self.repository.procedure_belongs_to_org(procedure_id, org_id):
            self._log_org_scope_miss("delete", procedure_id, org_id)
            raise NotFoundError("Procedure not found")
        deleted = await self.repository.delete(procedure_id)
        if not deleted:
            raise NotFoundError("Procedure not found")
        logger.info(
            "Procedure deleted",
            extra={"event": "procedure.deleted", "procedure_id": procedure_id},
        )

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource("Procedure", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Procedure failed base R4 validation",
                extra={"event": "procedure.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(operation: str, procedure_id: int, org_id: str | None) -> None:
        logger.warning(
            "Procedure write rejected by org scope",
            extra={
                "event": "procedure.org_scope_miss",
                "operation": operation,
                "procedure_id": procedure_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
