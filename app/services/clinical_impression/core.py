from datetime import date, datetime

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.datatypes import merge_patch_fragment
from app.fhir.mappers.clinical_impression import (
    patch_fragment_to_fhir_clinical_impression,
    payload_to_fhir_clinical_impression,
    to_fhir_clinical_impression,
    to_plain_clinical_impression,
)
from app.fhir.validation import validate_resource
from app.models.clinical_impression import ClinicalImpressionModel
from app.repository.clinical_impression import ClinicalImpressionRepository
from app.schemas.clinical_impression import (
    ClinicalImpressionCreateSchema,
    ClinicalImpressionPatchSchema,
)

logger = get_logger(__name__)


class ClinicalImpressionService:
    """All ClinicalImpression business logic."""

    def __init__(self, repository: ClinicalImpressionRepository):
        self.repository = repository

    def _to_fhir(self, model: ClinicalImpressionModel) -> dict:
        return to_fhir_clinical_impression(model)

    def _to_plain(self, model: ClinicalImpressionModel) -> dict:
        return to_plain_clinical_impression(model)

    async def get_clinical_impression_scoped(
        self, clinical_impression_id: int, org_id: str | None
    ) -> ClinicalImpressionModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token, else NotFoundError (404) if it belongs to a
        different org or doesn't exist."""
        if not org_id:
            raise PermissionDeniedError(
                "ClinicalImpression operation requires an org-scoped token"
            )
        model = await self.repository.get_by_clinical_impression_id_in_org(
            clinical_impression_id, org_id
        )
        if not model:
            raise NotFoundError("ClinicalImpression not found")
        return model

    async def list_clinical_impressions(
        self,
        org_id: str | None = None,
        status: str | None = None,
        subject: str | None = None,
        encounter: str | None = None,
        assessor: str | None = None,
        date_val: date | datetime | str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[ClinicalImpressionModel], int]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "ClinicalImpression operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            limit=limit,
            offset=offset,
            sort=sort,
            status=status,
            subject=subject,
            encounter=encounter,
            assessor=assessor,
            date_val=date_val,
            identifier=identifier,
        )

    async def create_clinical_impression(
        self,
        payload: ClinicalImpressionCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> ClinicalImpressionModel:
        if not org_id:
            raise PermissionDeniedError(
                "ClinicalImpression creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "ClinicalImpression creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_clinical_impression(payload), org_id
        )
        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "ClinicalImpression created",
            extra={
                "event": "clinical_impression.created",
                "clinical_impression_id": model.clinical_impression_id,
            },
        )
        return model

    async def patch_clinical_impression(
        self,
        clinical_impression_id: int,
        payload: ClinicalImpressionPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> ClinicalImpressionModel:
        if not org_id:
            self._log_org_scope_miss("patch", clinical_impression_id, org_id)
            raise NotFoundError("ClinicalImpression not found")
        existing = await self.repository.get_by_clinical_impression_id_in_org(
            clinical_impression_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", clinical_impression_id, org_id)
            raise NotFoundError("ClinicalImpression not found")

        fragment, touched = patch_fragment_to_fhir_clinical_impression(payload)
        merged = merge_patch_fragment(
            to_fhir_clinical_impression(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            clinical_impression_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("ClinicalImpression not found")
        logger.info(
            "ClinicalImpression updated",
            extra={
                "event": "clinical_impression.updated",
                "clinical_impression_id": clinical_impression_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_clinical_impression(
        self, clinical_impression_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.clinical_impression_belongs_to_org(
            clinical_impression_id, org_id
        ):
            self._log_org_scope_miss("delete", clinical_impression_id, org_id)
            raise NotFoundError("ClinicalImpression not found")
        deleted = await self.repository.delete(clinical_impression_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("ClinicalImpression not found")
        logger.info(
            "ClinicalImpression deleted",
            extra={
                "event": "clinical_impression.deleted",
                "clinical_impression_id": clinical_impression_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "ClinicalImpression", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "ClinicalImpression failed base R4 validation",
                extra={
                    "event": "clinical_impression.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, clinical_impression_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "ClinicalImpression write rejected by org scope",
            extra={
                "event": "clinical_impression.org_scope_miss",
                "operation": operation,
                "clinical_impression_id": clinical_impression_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
