from app.core.logging import get_logger
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.observation import (
    merge_patch_fragment,
    patch_fragment_to_fhir_observation,
    payload_to_fhir_observation,
    to_fhir_observation,
    to_plain_observation,
)
from app.fhir.validation import validate_resource
from app.models.observation import ObservationModel, ObservationStatus as ObservationStatusModel
from app.repository.observation import ObservationRepository
from app.schemas.enums import ObservationStatus
from app.schemas.observation import ObservationCreateSchema, ObservationPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Observation business logic. Default (gateway-trusted)
    pattern — same as QuestionnaireResponse/ServiceRequest/
    MedicationRequest: no org-scoped existence check or ownership
    enforcement at all."""

    def __init__(self, repository: ObservationRepository):
        self.repository = repository

    def _to_fhir(self, observation: ObservationModel) -> dict:
        return to_fhir_observation(observation)

    def _to_plain(self, observation: ObservationModel) -> dict:
        return to_plain_observation(observation)

    async def get_by_observation_id(self, observation_id: int) -> ObservationModel:
        observation = await self.repository.get_by_observation_id(observation_id)
        if not observation:
            raise NotFoundError("Observation not found")
        return observation

    async def get_me(
        self,
        user_id: str,
        tenant_id: str | None = None,
        status: ObservationStatus | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ObservationModel], int | None]:
        return await self.repository.get_me(
            user_id=user_id,
            tenant_id=tenant_id,
            status=ObservationStatusModel[status.name] if status else None,
            subject=subject,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def list_observations(
        self,
        tenant_id: str | None = None,
        user_id: str | None = None,
        status: ObservationStatus | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ObservationModel], int | None]:
        return await self.repository.list(
            tenant_id=tenant_id,
            user_id=user_id,
            status=ObservationStatusModel[status.name] if status else None,
            subject=subject,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_observation(self, payload: ObservationCreateSchema) -> ObservationModel:
        await self._validate_base_r4(payload_to_fhir_observation(payload), payload.tenant_id)
        observation = await self.repository.create_full(payload)
        logger.info(
            "Observation created",
            extra={"event": "observation.created", "observation_id": observation.observation_id},
        )
        return observation

    async def patch_observation(self, observation_id: int, payload: ObservationPatchSchema) -> ObservationModel:
        existing = await self.repository.get_by_observation_id(observation_id)
        if not existing:
            raise NotFoundError("Observation not found")

        fragment, touched = patch_fragment_to_fhir_observation(payload)
        merged = merge_patch_fragment(to_fhir_observation(existing), fragment, touched)
        await self._validate_base_r4(merged, existing.tenant_id)

        updated = await self.repository.patch_full(observation_id, payload)
        if not updated:
            raise NotFoundError("Observation not found")
        logger.info(
            "Observation updated",
            extra={
                "event": "observation.updated",
                "observation_id": observation_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_observation(self, observation_id: int) -> None:
        deleted = await self.repository.delete(observation_id)
        if not deleted:
            raise NotFoundError("Observation not found")
        logger.info(
            "Observation deleted",
            extra={"event": "observation.deleted", "observation_id": observation_id},
        )

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource("Observation", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Observation failed base R4 validation",
                extra={"event": "observation.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)
