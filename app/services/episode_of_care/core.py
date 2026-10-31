from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.episode_of_care import (
    merge_patch_fragment,
    patch_fragment_to_fhir_episode_of_care,
    payload_to_fhir_episode_of_care,
    to_fhir_episode_of_care,
    to_plain_episode_of_care,
)
from app.fhir.validation import validate_resource
from app.models.episode_of_care import EpisodeOfCareModel
from app.repository.episode_of_care import EpisodeOfCareRepository
from app.schemas.episode_of_care import (
    EpisodeOfCareCreateSchema,
    EpisodeOfCarePatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All EpisodeOfCare business logic."""

    def __init__(self, repository: EpisodeOfCareRepository):
        self.repository = repository

    def _to_fhir(self, episode_of_care: EpisodeOfCareModel) -> dict:
        return to_fhir_episode_of_care(episode_of_care)

    def _to_plain(self, episode_of_care: EpisodeOfCareModel) -> dict:
        return to_plain_episode_of_care(episode_of_care)

    async def get_episode_of_care_scoped(
        self, episode_of_care_id: int, org_id: str | None
    ) -> EpisodeOfCareModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError("EpisodeOfCare operation requires an org-scoped token")
        episode_of_care = await self.repository.get_by_episode_of_care_id_in_org(
            episode_of_care_id, org_id
        )
        if not episode_of_care:
            raise NotFoundError("EpisodeOfCare not found")
        return episode_of_care

    async def list_episodes_of_care(
        self,
        org_id: str | None = None,
        status: str | None = None,
        patient: str | None = None,
        type: str | None = None,
        care_manager: str | None = None,
        organization: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[EpisodeOfCareModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError("EpisodeOfCare operation requires an org-scoped token")
        return await self.repository.list(
            org_id=org_id,
            status=status,
            patient=patient,
            type=type,
            care_manager=care_manager,
            organization=organization,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_episode_of_care(
        self,
        payload: EpisodeOfCareCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> EpisodeOfCareModel:
        if not org_id:
            raise PermissionDeniedError("EpisodeOfCare creation requires an org-scoped token")
        if not created_by:
            raise PermissionDeniedError("EpisodeOfCare creation requires an authenticated actor")

        await self._validate_base_r4(payload_to_fhir_episode_of_care(payload), org_id)
        eoc = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "EpisodeOfCare created",
            extra={"event": "episode_of_care.created", "episode_of_care_id": eoc.episode_of_care_id},
        )
        return eoc

    async def patch_episode_of_care(
        self,
        episode_of_care_id: int,
        payload: EpisodeOfCarePatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> EpisodeOfCareModel:
        if not org_id:
            self._log_org_scope_miss("patch", episode_of_care_id, org_id)
            raise NotFoundError("EpisodeOfCare not found")
        existing = await self.repository.get_by_episode_of_care_id_in_org(episode_of_care_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", episode_of_care_id, org_id)
            raise NotFoundError("EpisodeOfCare not found")

        fragment, touched = patch_fragment_to_fhir_episode_of_care(payload)
        merged = merge_patch_fragment(to_fhir_episode_of_care(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            episode_of_care_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("EpisodeOfCare not found")
        logger.info(
            "EpisodeOfCare updated",
            extra={
                "event": "episode_of_care.updated",
                "episode_of_care_id": episode_of_care_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_episode_of_care(self, episode_of_care_id: int, org_id: str | None = None) -> None:
        if not org_id or not await self.repository.episode_of_care_belongs_to_org(episode_of_care_id, org_id):
            self._log_org_scope_miss("delete", episode_of_care_id, org_id)
            raise NotFoundError("EpisodeOfCare not found")
        deleted = await self.repository.delete(episode_of_care_id)
        if not deleted:
            raise NotFoundError("EpisodeOfCare not found")
        logger.info(
            "EpisodeOfCare deleted",
            extra={"event": "episode_of_care.deleted", "episode_of_care_id": episode_of_care_id},
        )

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource("EpisodeOfCare", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "EpisodeOfCare failed base R4 validation",
                extra={"event": "episode_of_care.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(operation: str, episode_of_care_id: int, org_id: str | None) -> None:
        logger.warning(
            "EpisodeOfCare write rejected by org scope",
            extra={
                "event": "episode_of_care.org_scope_miss",
                "operation": operation,
                "episode_of_care_id": episode_of_care_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
