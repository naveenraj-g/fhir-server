from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
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
    """All Observation business logic. Auth matches Questionnaire/
    QuestionnaireResponse/ServiceRequest/MedicationRequest: tenant
    scoping comes from the verified JWT's activeOrganizationId claim
    (actor.org_id), never a client-suppliable field, and there's no
    org-less/super-admin bypass — every operation requires an
    org-scoped actor. `user_id` is still a plain, gateway-forwarded
    field, so `get_me()` additionally scopes to the acting end-user."""

    def __init__(self, repository: ObservationRepository):
        self.repository = repository

    def _to_fhir(self, observation: ObservationModel) -> dict:
        return to_fhir_observation(observation)

    def _to_plain(self, observation: ObservationModel) -> dict:
        return to_plain_observation(observation)

    async def get_observation_scoped(
        self, observation_id: int, org_id: str | None
    ) -> ObservationModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError("Observation operation requires an org-scoped token")
        observation = await self.repository.get_by_observation_id_in_org(observation_id, org_id)
        if not observation:
            raise NotFoundError("Observation not found")
        return observation

    async def get_me(
        self,
        user_id: str,
        org_id: str | None = None,
        status: ObservationStatus | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ObservationModel], int | None]:
        """Scopes list() to the authenticated end-user's own user_id,
        always combined with the org-scoped actor's org_id."""
        if not org_id:
            raise PermissionDeniedError("Observation operation requires an org-scoped token")
        return await self.repository.get_me(
            user_id=user_id,
            org_id=org_id,
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
        org_id: str | None = None,
        status: ObservationStatus | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ObservationModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token — same
        invariant as get_observation_scoped()."""
        if not org_id:
            raise PermissionDeniedError("Observation operation requires an org-scoped token")
        return await self.repository.list(
            org_id=org_id,
            status=ObservationStatusModel[status.name] if status else None,
            subject=subject,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_observation(
        self,
        payload: ObservationCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> ObservationModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create an Observation at all."""
        if not org_id:
            raise PermissionDeniedError("Observation creation requires an org-scoped token")
        await self._validate_base_r4(payload_to_fhir_observation(payload), org_id)
        observation = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "Observation created",
            extra={"event": "observation.created", "observation_id": observation.observation_id},
        )
        return observation

    async def patch_observation(
        self,
        observation_id: int,
        payload: ObservationPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> ObservationModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a resource belonging to a different org both
        raise NotFoundError (404), never 403, so existence isn't leaked."""
        if not org_id:
            self._log_org_scope_miss("patch", observation_id, org_id)
            raise NotFoundError("Observation not found")
        existing = await self.repository.get_by_observation_id_in_org(observation_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", observation_id, org_id)
            raise NotFoundError("Observation not found")

        fragment, touched = patch_fragment_to_fhir_observation(payload)
        merged = merge_patch_fragment(to_fhir_observation(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(observation_id, payload, updated_by)
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

    async def delete_observation(self, observation_id: int, org_id: str | None = None) -> None:
        """Same org_id ownership gate as patch_observation."""
        if not org_id or not await self.repository.observation_belongs_to_org(observation_id, org_id):
            self._log_org_scope_miss("delete", observation_id, org_id)
            raise NotFoundError("Observation not found")
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

    @staticmethod
    def _log_org_scope_miss(operation: str, observation_id: int, org_id: str | None) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such resource" — so this
        log line is the only place the distinction is recorded."""
        logger.warning(
            "Observation write rejected by org scope",
            extra={
                "event": "observation.org_scope_miss",
                "operation": operation,
                "observation_id": observation_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
