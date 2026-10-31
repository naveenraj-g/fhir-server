from datetime import date, datetime

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.allergy_intolerance import (
    merge_patch_fragment,
    patch_fragment_to_fhir_allergy_intolerance,
    payload_to_fhir_allergy_intolerance,
    to_fhir_allergy_intolerance,
    to_plain_allergy_intolerance,
)
from app.fhir.validation import validate_resource
from app.models.allergy_intolerance import (
    AllergyIntoleranceCriticality,
    AllergyIntoleranceModel,
    AllergyIntoleranceType,
)
from app.repository.allergy_intolerance import AllergyIntoleranceRepository
from app.schemas.allergy_intolerance import (
    AllergyIntoleranceCreateSchema,
    AllergyIntolerancePatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All AllergyIntolerance business logic."""

    def __init__(self, repository: AllergyIntoleranceRepository):
        self.repository = repository

    def _to_fhir(self, model: AllergyIntoleranceModel) -> dict:
        return to_fhir_allergy_intolerance(model)

    def _to_plain(self, model: AllergyIntoleranceModel) -> dict:
        return to_plain_allergy_intolerance(model)

    async def get_allergy_intolerance_scoped(
        self, allergy_intolerance_id: int, org_id: str | None
    ) -> AllergyIntoleranceModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "AllergyIntolerance operation requires an org-scoped token"
            )
        model = await self.repository.get_by_allergy_intolerance_id_in_org(
            allergy_intolerance_id, org_id
        )
        if not model:
            raise NotFoundError("AllergyIntolerance not found")
        return model

    async def list_allergy_intolerances(
        self,
        org_id: str | None = None,
        clinical_status: str | None = None,
        verification_status: str | None = None,
        type: str | AllergyIntoleranceType | None = None,
        category: str | None = None,
        criticality: str | AllergyIntoleranceCriticality | None = None,
        code: str | None = None,
        patient: str | None = None,
        severity: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        recorder: str | None = None,
        asserter: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[AllergyIntoleranceModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "AllergyIntolerance operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            clinical_status=clinical_status,
            verification_status=verification_status,
            type=type,
            category=category,
            criticality=criticality,
            code=code,
            patient=patient,
            severity=severity,
            date_val=date_val,
            date_from=date_from,
            date_to=date_to,
            recorder=recorder,
            asserter=asserter,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_allergy_intolerance(
        self,
        payload: AllergyIntoleranceCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> AllergyIntoleranceModel:
        if not org_id:
            raise PermissionDeniedError(
                "AllergyIntolerance creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "AllergyIntolerance creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_allergy_intolerance(payload), org_id
        )
        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "AllergyIntolerance created",
            extra={
                "event": "allergy_intolerance.created",
                "allergy_intolerance_id": model.allergy_intolerance_id,
            },
        )
        return model

    async def patch_allergy_intolerance(
        self,
        allergy_intolerance_id: int,
        payload: AllergyIntolerancePatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> AllergyIntoleranceModel:
        if not org_id:
            self._log_org_scope_miss("patch", allergy_intolerance_id, org_id)
            raise NotFoundError("AllergyIntolerance not found")
        existing = await self.repository.get_by_allergy_intolerance_id_in_org(
            allergy_intolerance_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", allergy_intolerance_id, org_id)
            raise NotFoundError("AllergyIntolerance not found")

        fragment, touched = patch_fragment_to_fhir_allergy_intolerance(payload)
        merged = merge_patch_fragment(
            to_fhir_allergy_intolerance(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            allergy_intolerance_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("AllergyIntolerance not found")
        logger.info(
            "AllergyIntolerance updated",
            extra={
                "event": "allergy_intolerance.updated",
                "allergy_intolerance_id": allergy_intolerance_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_allergy_intolerance(
        self, allergy_intolerance_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.allergy_intolerance_belongs_to_org(
            allergy_intolerance_id, org_id
        ):
            self._log_org_scope_miss("delete", allergy_intolerance_id, org_id)
            raise NotFoundError("AllergyIntolerance not found")
        deleted = await self.repository.delete(allergy_intolerance_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("AllergyIntolerance not found")
        logger.info(
            "AllergyIntolerance deleted",
            extra={
                "event": "allergy_intolerance.deleted",
                "allergy_intolerance_id": allergy_intolerance_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "AllergyIntolerance", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "AllergyIntolerance failed base R4 validation",
                extra={
                    "event": "allergy_intolerance.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, allergy_intolerance_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "AllergyIntolerance write rejected by org scope",
            extra={
                "event": "allergy_intolerance.org_scope_miss",
                "operation": operation,
                "allergy_intolerance_id": allergy_intolerance_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
