from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.observation_definition import (
    merge_patch_fragment,
    patch_fragment_to_fhir_observation_definition,
    payload_to_fhir_observation_definition,
    to_fhir_observation_definition,
    to_plain_observation_definition,
)
from app.fhir.validation import validate_resource
from app.models.observation_definition import ObservationDefinitionModel
from app.repository.observation_definition import ObservationDefinitionRepository
from app.schemas.observation_definition import (
    ObservationDefinitionCreateSchema,
    ObservationDefinitionPatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All ObservationDefinition business logic."""

    def __init__(self, repository: ObservationDefinitionRepository):
        self.repository = repository

    def _to_fhir(self, observation_definition: ObservationDefinitionModel) -> dict:
        return to_fhir_observation_definition(observation_definition)

    def _to_plain(self, observation_definition: ObservationDefinitionModel) -> dict:
        return to_plain_observation_definition(observation_definition)

    async def get_observation_definition_scoped(
        self, observation_definition_id: int, org_id: str | None
    ) -> ObservationDefinitionModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "ObservationDefinition operation requires an org-scoped token"
            )
        observation_definition = (
            await self.repository.get_by_observation_definition_id_in_org(
                observation_definition_id, org_id
            )
        )
        if not observation_definition:
            raise NotFoundError("ObservationDefinition not found")
        return observation_definition

    async def list_observation_definitions(
        self,
        org_id: str | None = None,
        code: str | None = None,
        category: str | None = None,
        method: str | None = None,
        identifier: str | None = None,
        permitted_data_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ObservationDefinitionModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "ObservationDefinition operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            code=code,
            category=category,
            method=method,
            identifier=identifier,
            permitted_data_type=permitted_data_type,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_observation_definition(
        self,
        payload: ObservationDefinitionCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> ObservationDefinitionModel:
        if not org_id:
            raise PermissionDeniedError(
                "ObservationDefinition creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "ObservationDefinition creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_observation_definition(payload), org_id
        )
        od = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "ObservationDefinition created",
            extra={
                "event": "observation_definition.created",
                "observation_definition_id": od.observation_definition_id,
            },
        )
        return od

    async def patch_observation_definition(
        self,
        observation_definition_id: int,
        payload: ObservationDefinitionPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> ObservationDefinitionModel:
        if not org_id:
            self._log_org_scope_miss("patch", observation_definition_id, org_id)
            raise NotFoundError("ObservationDefinition not found")
        existing = await self.repository.get_by_observation_definition_id_in_org(
            observation_definition_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", observation_definition_id, org_id)
            raise NotFoundError("ObservationDefinition not found")

        fragment, touched = patch_fragment_to_fhir_observation_definition(payload)
        merged = merge_patch_fragment(
            to_fhir_observation_definition(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            observation_definition_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("ObservationDefinition not found")
        logger.info(
            "ObservationDefinition updated",
            extra={
                "event": "observation_definition.updated",
                "observation_definition_id": observation_definition_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_observation_definition(
        self, observation_definition_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.observation_definition_belongs_to_org(
            observation_definition_id, org_id
        ):
            self._log_org_scope_miss("delete", observation_definition_id, org_id)
            raise NotFoundError("ObservationDefinition not found")
        deleted = await self.repository.delete(observation_definition_id)
        if not deleted:
            raise NotFoundError("ObservationDefinition not found")
        logger.info(
            "ObservationDefinition deleted",
            extra={
                "event": "observation_definition.deleted",
                "observation_definition_id": observation_definition_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource(
            "ObservationDefinition", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "ObservationDefinition failed base R4 validation",
                extra={"event": "observation_definition.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, observation_definition_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "ObservationDefinition write rejected by org scope",
            extra={
                "event": "observation_definition.org_scope_miss",
                "operation": operation,
                "observation_definition_id": observation_definition_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
