from datetime import date, datetime

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.medication_statement import (
    merge_patch_fragment,
    patch_fragment_to_fhir_medication_statement,
    payload_to_fhir_medication_statement,
    to_fhir_medication_statement,
    to_plain_medication_statement,
)
from app.fhir.validation import validate_resource
from app.models.medication_statement import (
    MedicationStatementModel,
    MedicationStatementStatus,
)
from app.repository.medication_statement import MedicationStatementRepository
from app.schemas.medication_statement import (
    MedicationStatementCreateSchema,
    MedicationStatementPatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All MedicationStatement business logic."""

    def __init__(self, repository: MedicationStatementRepository):
        self.repository = repository

    def _to_fhir(self, model: MedicationStatementModel) -> dict:
        return to_fhir_medication_statement(model)

    def _to_plain(self, model: MedicationStatementModel) -> dict:
        return to_plain_medication_statement(model)

    async def get_medication_statement_scoped(
        self, medication_statement_id: int, org_id: str | None
    ) -> MedicationStatementModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "MedicationStatement operation requires an org-scoped token"
            )
        model = await self.repository.get_by_medication_statement_id_in_org(
            medication_statement_id, org_id
        )
        if not model:
            raise NotFoundError("MedicationStatement not found")
        return model

    async def list_medication_statements(
        self,
        org_id: str | None = None,
        status: str | MedicationStatementStatus | None = None,
        subject: str | None = None,
        patient: str | None = None,
        code: str | None = None,
        category: str | None = None,
        effective_val: date | datetime | None = None,
        effective_from: date | datetime | None = None,
        effective_to: date | datetime | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[MedicationStatementModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "MedicationStatement operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            status=status,
            subject=subject,
            patient=patient,
            code=code,
            category=category,
            effective_val=effective_val,
            effective_from=effective_from,
            effective_to=effective_to,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_medication_statement(
        self,
        payload: MedicationStatementCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> MedicationStatementModel:
        if not org_id:
            raise PermissionDeniedError(
                "MedicationStatement creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "MedicationStatement creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_medication_statement(payload), org_id
        )
        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "MedicationStatement created",
            extra={
                "event": "medication_statement.created",
                "medication_statement_id": model.medication_statement_id,
            },
        )
        return model

    async def patch_medication_statement(
        self,
        medication_statement_id: int,
        payload: MedicationStatementPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> MedicationStatementModel:
        if not org_id:
            self._log_org_scope_miss("patch", medication_statement_id, org_id)
            raise NotFoundError("MedicationStatement not found")
        existing = await self.repository.get_by_medication_statement_id_in_org(
            medication_statement_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", medication_statement_id, org_id)
            raise NotFoundError("MedicationStatement not found")

        fragment, touched = patch_fragment_to_fhir_medication_statement(payload)
        merged = merge_patch_fragment(
            to_fhir_medication_statement(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            medication_statement_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("MedicationStatement not found")
        logger.info(
            "MedicationStatement updated",
            extra={
                "event": "medication_statement.updated",
                "medication_statement_id": medication_statement_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_medication_statement(
        self, medication_statement_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.medication_statement_belongs_to_org(
            medication_statement_id, org_id
        ):
            self._log_org_scope_miss("delete", medication_statement_id, org_id)
            raise NotFoundError("MedicationStatement not found")
        deleted = await self.repository.delete(medication_statement_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("MedicationStatement not found")
        logger.info(
            "MedicationStatement deleted",
            extra={
                "event": "medication_statement.deleted",
                "medication_statement_id": medication_statement_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "MedicationStatement", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "MedicationStatement failed base R4 validation",
                extra={
                    "event": "medication_statement.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, medication_statement_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "MedicationStatement write rejected by org scope",
            extra={
                "event": "medication_statement.org_scope_miss",
                "operation": operation,
                "medication_statement_id": medication_statement_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
