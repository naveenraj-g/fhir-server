from datetime import date, datetime

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.immunization import (
    merge_patch_fragment,
    patch_fragment_to_fhir_immunization,
    payload_to_fhir_immunization,
    to_fhir_immunization,
    to_plain_immunization,
)
from app.fhir.validation import validate_resource
from app.models.immunization import ImmunizationModel, ImmunizationStatus
from app.repository.immunization import ImmunizationRepository
from app.schemas.immunization import (
    ImmunizationCreateSchema,
    ImmunizationPatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All Immunization business logic."""

    def __init__(self, repository: ImmunizationRepository):
        self.repository = repository

    def _to_fhir(self, model: ImmunizationModel) -> dict:
        return to_fhir_immunization(model)

    def _to_plain(self, model: ImmunizationModel) -> dict:
        return to_plain_immunization(model)

    async def get_immunization_scoped(
        self, immunization_id: int, org_id: str | None
    ) -> ImmunizationModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Immunization operation requires an org-scoped token"
            )
        model = await self.repository.get_by_immunization_id_in_org(
            immunization_id, org_id
        )
        if not model:
            raise NotFoundError("Immunization not found")
        return model

    async def list_immunizations(
        self,
        org_id: str | None = None,
        status: str | ImmunizationStatus | None = None,
        patient: str | None = None,
        vaccine_code: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        location: str | None = None,
        manufacturer: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ImmunizationModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "Immunization operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            status=status,
            patient=patient,
            vaccine_code=vaccine_code,
            date_val=date_val,
            date_from=date_from,
            date_to=date_to,
            location=location,
            manufacturer=manufacturer,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_immunization(
        self,
        payload: ImmunizationCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> ImmunizationModel:
        if not org_id:
            raise PermissionDeniedError(
                "Immunization creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "Immunization creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_immunization(payload), org_id
        )
        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "Immunization created",
            extra={
                "event": "immunization.created",
                "immunization_id": model.immunization_id,
            },
        )
        return model

    async def patch_immunization(
        self,
        immunization_id: int,
        payload: ImmunizationPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> ImmunizationModel:
        if not org_id:
            self._log_org_scope_miss("patch", immunization_id, org_id)
            raise NotFoundError("Immunization not found")
        existing = await self.repository.get_by_immunization_id_in_org(
            immunization_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", immunization_id, org_id)
            raise NotFoundError("Immunization not found")

        fragment, touched = patch_fragment_to_fhir_immunization(payload)
        merged = merge_patch_fragment(
            to_fhir_immunization(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            immunization_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("Immunization not found")
        logger.info(
            "Immunization updated",
            extra={
                "event": "immunization.updated",
                "immunization_id": immunization_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_immunization(
        self, immunization_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.immunization_belongs_to_org(
            immunization_id, org_id
        ):
            self._log_org_scope_miss("delete", immunization_id, org_id)
            raise NotFoundError("Immunization not found")
        deleted = await self.repository.delete(immunization_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("Immunization not found")
        logger.info(
            "Immunization deleted",
            extra={
                "event": "immunization.deleted",
                "immunization_id": immunization_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "Immunization", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "Immunization failed base R4 validation",
                extra={
                    "event": "immunization.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, immunization_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "Immunization write rejected by org scope",
            extra={
                "event": "immunization.org_scope_miss",
                "operation": operation,
                "immunization_id": immunization_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
