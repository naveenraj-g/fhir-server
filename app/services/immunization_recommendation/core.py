from datetime import date, datetime

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.datatypes import merge_patch_fragment
from app.fhir.mappers.immunization_recommendation import (
    patch_fragment_to_fhir_immunization_recommendation,
    payload_to_fhir_immunization_recommendation,
    to_fhir_immunization_recommendation,
    to_plain_immunization_recommendation,
)
from app.fhir.validation import validate_resource
from app.models.immunization_recommendation import ImmunizationRecommendationModel
from app.repository.immunization_recommendation import ImmunizationRecommendationRepository
from app.schemas.immunization_recommendation import (
    ImmunizationRecommendationCreateSchema,
    ImmunizationRecommendationPatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All ImmunizationRecommendation business logic."""

    def __init__(self, repository: ImmunizationRecommendationRepository):
        self.repository = repository

    def _to_fhir(self, model: ImmunizationRecommendationModel) -> dict:
        return to_fhir_immunization_recommendation(model)

    def _to_plain(self, model: ImmunizationRecommendationModel) -> dict:
        return to_plain_immunization_recommendation(model)

    async def get_immunization_recommendation_scoped(
        self, immunization_recommendation_id: int, org_id: str | None
    ) -> ImmunizationRecommendationModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "ImmunizationRecommendation operation requires an org-scoped token"
            )
        model = await self.repository.get_by_immunization_recommendation_id_in_org(
            immunization_recommendation_id, org_id
        )
        if not model:
            raise NotFoundError("ImmunizationRecommendation not found")
        return model

    async def list_immunization_recommendations(
        self,
        org_id: str | None = None,
        patient: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ImmunizationRecommendationModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "ImmunizationRecommendation operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            patient=patient,
            date_val=date_val,
            date_from=date_from,
            date_to=date_to,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_immunization_recommendation(
        self,
        payload: ImmunizationRecommendationCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> ImmunizationRecommendationModel:
        if not org_id:
            raise PermissionDeniedError(
                "ImmunizationRecommendation creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "ImmunizationRecommendation creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_immunization_recommendation(payload), org_id
        )
        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "ImmunizationRecommendation created",
            extra={
                "event": "immunization_recommendation.created",
                "immunization_recommendation_id": model.immunization_recommendation_id,
            },
        )
        return model

    async def patch_immunization_recommendation(
        self,
        immunization_recommendation_id: int,
        payload: ImmunizationRecommendationPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> ImmunizationRecommendationModel:
        if not org_id:
            self._log_org_scope_miss("patch", immunization_recommendation_id, org_id)
            raise NotFoundError("ImmunizationRecommendation not found")
        existing = await self.repository.get_by_immunization_recommendation_id_in_org(
            immunization_recommendation_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", immunization_recommendation_id, org_id)
            raise NotFoundError("ImmunizationRecommendation not found")

        fragment, touched = patch_fragment_to_fhir_immunization_recommendation(payload)
        merged = merge_patch_fragment(
            to_fhir_immunization_recommendation(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            immunization_recommendation_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("ImmunizationRecommendation not found")
        logger.info(
            "ImmunizationRecommendation updated",
            extra={
                "event": "immunization_recommendation.updated",
                "immunization_recommendation_id": immunization_recommendation_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_immunization_recommendation(
        self, immunization_recommendation_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.immunization_recommendation_belongs_to_org(
            immunization_recommendation_id, org_id
        ):
            self._log_org_scope_miss("delete", immunization_recommendation_id, org_id)
            raise NotFoundError("ImmunizationRecommendation not found")
        deleted = await self.repository.delete(immunization_recommendation_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("ImmunizationRecommendation not found")
        logger.info(
            "ImmunizationRecommendation deleted",
            extra={
                "event": "immunization_recommendation.deleted",
                "immunization_recommendation_id": immunization_recommendation_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "ImmunizationRecommendation", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "ImmunizationRecommendation failed base R4 validation",
                extra={
                    "event": "immunization_recommendation.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, immunization_recommendation_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "ImmunizationRecommendation write rejected by org scope",
            extra={
                "event": "immunization_recommendation.org_scope_miss",
                "operation": operation,
                "immunization_recommendation_id": immunization_recommendation_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
