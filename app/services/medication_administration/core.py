from datetime import date, datetime

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.medication_administration import (
    merge_patch_fragment,
    patch_fragment_to_fhir_medication_administration,
    payload_to_fhir_medication_administration,
    to_fhir_medication_administration,
    to_plain_medication_administration,
)
from app.fhir.validation import validate_resource
from app.models.medication_administration import (
    MedicationAdministrationModel,
    MedicationAdministrationStatus,
)
from app.repository.medication_administration import MedicationAdministrationRepository
from app.schemas.medication_administration import (
    MedicationAdministrationCreateSchema,
    MedicationAdministrationPatchSchema,
)

logger = get_logger(__name__)


class MedicationAdministrationService:
    """All MedicationAdministration business logic."""

    def __init__(self, repository: MedicationAdministrationRepository):
        self.repository = repository

    def _to_fhir(self, model: MedicationAdministrationModel) -> dict:
        return to_fhir_medication_administration(model)

    def _to_plain(self, model: MedicationAdministrationModel) -> dict:
        return to_plain_medication_administration(model)

    async def get_medication_administration_scoped(
        self, medication_administration_id: int, org_id: str | None
    ) -> MedicationAdministrationModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "MedicationAdministration operation requires an org-scoped token"
            )
        model = await self.repository.get_by_medication_administration_id_in_org(
            medication_administration_id, org_id
        )
        if not model:
            raise NotFoundError("MedicationAdministration not found")
        return model

    async def list_medication_administrations(
        self,
        org_id: str | None = None,
        status: str | MedicationAdministrationStatus | None = None,
        subject: str | None = None,
        patient: str | None = None,
        code: str | None = None,
        category: str | None = None,
        effective_val: date | datetime | None = None,
        effective_from: date | datetime | None = None,
        effective_to: date | datetime | None = None,
        identifier: str | None = None,
        request: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[MedicationAdministrationModel], int]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "MedicationAdministration operation requires an org-scoped token"
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
            request=request,
            limit=limit,
            offset=offset,
            sort=sort,
        )

    async def create_medication_administration(
        self,
        payload: MedicationAdministrationCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> MedicationAdministrationModel:
        if not org_id:
            raise PermissionDeniedError(
                "MedicationAdministration creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "MedicationAdministration creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_medication_administration(payload), org_id
        )
        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "MedicationAdministration created",
            extra={
                "event": "medication_administration.created",
                "medication_administration_id": model.medication_administration_id,
            },
        )
        return model

    async def patch_medication_administration(
        self,
        medication_administration_id: int,
        payload: MedicationAdministrationPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> MedicationAdministrationModel:
        if not org_id:
            self._log_org_scope_miss("patch", medication_administration_id, org_id)
            raise NotFoundError("MedicationAdministration not found")
        existing = await self.repository.get_by_medication_administration_id_in_org(
            medication_administration_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", medication_administration_id, org_id)
            raise NotFoundError("MedicationAdministration not found")

        fragment, touched = patch_fragment_to_fhir_medication_administration(payload)
        merged = merge_patch_fragment(
            to_fhir_medication_administration(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            medication_administration_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("MedicationAdministration not found")
        logger.info(
            "MedicationAdministration updated",
            extra={
                "event": "medication_administration.updated",
                "medication_administration_id": medication_administration_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_medication_administration(
        self, medication_administration_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.medication_administration_belongs_to_org(
            medication_administration_id, org_id
        ):
            self._log_org_scope_miss("delete", medication_administration_id, org_id)
            raise NotFoundError("MedicationAdministration not found")
        deleted = await self.repository.delete(medication_administration_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("MedicationAdministration not found")
        logger.info(
            "MedicationAdministration deleted",
            extra={
                "event": "medication_administration.deleted",
                "medication_administration_id": medication_administration_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "MedicationAdministration", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "MedicationAdministration failed base R4 validation",
                extra={
                    "event": "medication_administration.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, medication_administration_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "MedicationAdministration write rejected by org scope",
            extra={
                "event": "medication_administration.org_scope_miss",
                "operation": operation,
                "medication_administration_id": medication_administration_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
