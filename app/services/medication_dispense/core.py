from datetime import date, datetime

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.medication_dispense import (
    merge_patch_fragment,
    patch_fragment_to_fhir_medication_dispense,
    payload_to_fhir_medication_dispense,
    to_fhir_medication_dispense,
    to_plain_medication_dispense,
)
from app.fhir.validation import validate_resource
from app.models.medication_dispense import (
    MedicationDispenseModel,
    MedicationDispenseStatus,
)
from app.repository.medication_dispense import MedicationDispenseRepository
from app.schemas.medication_dispense import (
    MedicationDispenseCreateSchema,
    MedicationDispensePatchSchema,
)

logger = get_logger(__name__)


class MedicationDispenseService:
    """All MedicationDispense business logic."""

    def __init__(self, repository: MedicationDispenseRepository):
        self.repository = repository

    def _to_fhir(self, model: MedicationDispenseModel) -> dict:
        return to_fhir_medication_dispense(model)

    def _to_plain(self, model: MedicationDispenseModel) -> dict:
        return to_plain_medication_dispense(model)

    async def get_medication_dispense_scoped(
        self, medication_dispense_id: int, org_id: str | None
    ) -> MedicationDispenseModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "MedicationDispense operation requires an org-scoped token"
            )
        model = await self.repository.get_by_medication_dispense_id_in_org(
            medication_dispense_id, org_id
        )
        if not model:
            raise NotFoundError("MedicationDispense not found")
        return model

    async def list_medication_dispenses(
        self,
        org_id: str | None = None,
        status: str | MedicationDispenseStatus | None = None,
        subject: str | None = None,
        patient: str | None = None,
        code: str | None = None,
        category: str | None = None,
        type: str | None = None,
        when_prepared_val: date | datetime | None = None,
        when_prepared_from: date | datetime | None = None,
        when_prepared_to: date | datetime | None = None,
        when_handed_over_val: date | datetime | None = None,
        when_handed_over_from: date | datetime | None = None,
        when_handed_over_to: date | datetime | None = None,
        identifier: str | None = None,
        destination: str | None = None,
        receiver: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[MedicationDispenseModel], int]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "MedicationDispense operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            status=status,
            subject=subject,
            patient=patient,
            code=code,
            category=category,
            type=type,
            when_prepared_val=when_prepared_val,
            when_prepared_from=when_prepared_from,
            when_prepared_to=when_prepared_to,
            when_handed_over_val=when_handed_over_val,
            when_handed_over_from=when_handed_over_from,
            when_handed_over_to=when_handed_over_to,
            identifier=identifier,
            destination=destination,
            receiver=receiver,
            limit=limit,
            offset=offset,
            sort=sort,
        )

    async def create_medication_dispense(
        self,
        payload: MedicationDispenseCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> MedicationDispenseModel:
        if not org_id:
            raise PermissionDeniedError(
                "MedicationDispense creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "MedicationDispense creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_medication_dispense(payload), org_id
        )
        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "MedicationDispense created",
            extra={
                "event": "medication_dispense.created",
                "medication_dispense_id": model.medication_dispense_id,
            },
        )
        return model

    async def patch_medication_dispense(
        self,
        medication_dispense_id: int,
        payload: MedicationDispensePatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> MedicationDispenseModel:
        if not org_id:
            self._log_org_scope_miss("patch", medication_dispense_id, org_id)
            raise NotFoundError("MedicationDispense not found")
        existing = await self.repository.get_by_medication_dispense_id_in_org(
            medication_dispense_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", medication_dispense_id, org_id)
            raise NotFoundError("MedicationDispense not found")

        fragment, touched = patch_fragment_to_fhir_medication_dispense(payload)
        merged = merge_patch_fragment(
            to_fhir_medication_dispense(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            medication_dispense_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("MedicationDispense not found")
        logger.info(
            "MedicationDispense updated",
            extra={
                "event": "medication_dispense.updated",
                "medication_dispense_id": medication_dispense_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_medication_dispense(
        self, medication_dispense_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.medication_dispense_belongs_to_org(
            medication_dispense_id, org_id
        ):
            self._log_org_scope_miss("delete", medication_dispense_id, org_id)
            raise NotFoundError("MedicationDispense not found")
        deleted = await self.repository.delete(medication_dispense_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("MedicationDispense not found")
        logger.info(
            "MedicationDispense deleted",
            extra={
                "event": "medication_dispense.deleted",
                "medication_dispense_id": medication_dispense_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "MedicationDispense", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "MedicationDispense failed base R4 validation",
                extra={
                    "event": "medication_dispense.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, medication_dispense_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "MedicationDispense write rejected by org scope",
            extra={
                "event": "medication_dispense.org_scope_miss",
                "operation": operation,
                "medication_dispense_id": medication_dispense_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
