from datetime import date, datetime

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.medication import (
    merge_patch_fragment,
    patch_fragment_to_fhir_medication,
    payload_to_fhir_medication,
    to_fhir_medication,
    to_plain_medication,
)
from app.fhir.validation import validate_resource
from app.models.medication import (
    MedicationModel,
    MedicationStatus,
)
from app.repository.medication import MedicationRepository
from app.schemas.medication import (
    MedicationCreateSchema,
    MedicationPatchSchema,
)

logger = get_logger(__name__)


class MedicationService:
    """All Medication business logic."""

    def __init__(self, repository: MedicationRepository):
        self.repository = repository

    def _to_fhir(self, model: MedicationModel) -> dict:
        return to_fhir_medication(model)

    def _to_plain(self, model: MedicationModel) -> dict:
        return to_plain_medication(model)

    async def get_medication_scoped(
        self, medication_id: int, org_id: str | None
    ) -> MedicationModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Medication operation requires an org-scoped token"
            )
        model = await self.repository.get_by_medication_id_in_org(
            medication_id, org_id
        )
        if not model:
            raise NotFoundError("Medication not found")
        return model

    async def list_medications(
        self,
        org_id: str | None = None,
        code: str | None = None,
        status: str | MedicationStatus | None = None,
        manufacturer: str | None = None,
        form: str | None = None,
        ingredient: str | None = None,
        ingredient_code: str | None = None,
        lot_number: str | None = None,
        expiration_date: date | datetime | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[MedicationModel], int]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "Medication operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            code=code,
            status=status,
            manufacturer=manufacturer,
            form=form,
            ingredient=ingredient,
            ingredient_code=ingredient_code,
            lot_number=lot_number,
            expiration_date=expiration_date,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
        )

    async def create_medication(
        self,
        payload: MedicationCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> MedicationModel:
        if not org_id:
            raise PermissionDeniedError(
                "Medication creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "Medication creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_medication(payload), org_id
        )
        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "Medication created",
            extra={
                "event": "medication.created",
                "medication_id": model.medication_id,
            },
        )
        return model

    async def patch_medication(
        self,
        medication_id: int,
        payload: MedicationPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> MedicationModel:
        if not org_id:
            self._log_org_scope_miss("patch", medication_id, org_id)
            raise NotFoundError("Medication not found")
        existing = await self.repository.get_by_medication_id_in_org(
            medication_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", medication_id, org_id)
            raise NotFoundError("Medication not found")

        fragment, touched = patch_fragment_to_fhir_medication(payload)
        merged = merge_patch_fragment(
            to_fhir_medication(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            medication_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("Medication not found")
        logger.info(
            "Medication updated",
            extra={
                "event": "medication.updated",
                "medication_id": medication_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_medication(
        self, medication_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.medication_belongs_to_org(
            medication_id, org_id
        ):
            self._log_org_scope_miss("delete", medication_id, org_id)
            raise NotFoundError("Medication not found")
        deleted = await self.repository.delete(medication_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("Medication not found")
        logger.info(
            "Medication deleted",
            extra={
                "event": "medication.deleted",
                "medication_id": medication_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "Medication", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "Medication failed base R4 validation",
                extra={
                    "event": "medication.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, medication_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "Medication write rejected by org scope",
            extra={
                "event": "medication.org_scope_miss",
                "operation": operation,
                "medication_id": medication_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
