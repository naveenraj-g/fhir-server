from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.activity_definition import (
    merge_patch_fragment,
    patch_fragment_to_fhir_activity_definition,
    payload_to_fhir_activity_definition,
    to_fhir_activity_definition,
    to_plain_activity_definition,
)
from app.fhir.validation import validate_resource
from app.models.activity_definition import ActivityDefinitionModel
from app.repository.activity_definition import ActivityDefinitionRepository
from app.schemas.activity_definition import (
    ActivityDefinitionCreateSchema,
    ActivityDefinitionPatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All ActivityDefinition business logic."""

    def __init__(self, repository: ActivityDefinitionRepository):
        self.repository = repository

    def _to_fhir(self, activity_definition: ActivityDefinitionModel) -> dict:
        return to_fhir_activity_definition(activity_definition)

    def _to_plain(self, activity_definition: ActivityDefinitionModel) -> dict:
        return to_plain_activity_definition(activity_definition)

    async def get_activity_definition_scoped(
        self, activity_definition_id: int, org_id: str | None
    ) -> ActivityDefinitionModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "ActivityDefinition operation requires an org-scoped token"
            )
        activity_definition = (
            await self.repository.get_by_activity_definition_id_in_org(
                activity_definition_id, org_id
            )
        )
        if not activity_definition:
            raise NotFoundError("ActivityDefinition not found")
        return activity_definition

    async def list_activity_definitions(
        self,
        org_id: str | None = None,
        name: str | None = None,
        title: str | None = None,
        status: str | None = None,
        kind: str | None = None,
        intent: str | None = None,
        priority: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ActivityDefinitionModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "ActivityDefinition operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            name=name,
            title=title,
            status=status,
            kind=kind,
            intent=intent,
            priority=priority,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_activity_definition(
        self,
        payload: ActivityDefinitionCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> ActivityDefinitionModel:
        if not org_id:
            raise PermissionDeniedError(
                "ActivityDefinition creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "ActivityDefinition creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_activity_definition(payload), org_id
        )
        ad = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "ActivityDefinition created",
            extra={
                "event": "activity_definition.created",
                "activity_definition_id": ad.activity_definition_id,
            },
        )
        return ad

    async def patch_activity_definition(
        self,
        activity_definition_id: int,
        payload: ActivityDefinitionPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> ActivityDefinitionModel:
        if not org_id:
            self._log_org_scope_miss("patch", activity_definition_id, org_id)
            raise NotFoundError("ActivityDefinition not found")
        existing = await self.repository.get_by_activity_definition_id_in_org(
            activity_definition_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", activity_definition_id, org_id)
            raise NotFoundError("ActivityDefinition not found")

        fragment, touched = patch_fragment_to_fhir_activity_definition(payload)
        merged = merge_patch_fragment(
            to_fhir_activity_definition(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            activity_definition_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("ActivityDefinition not found")
        logger.info(
            "ActivityDefinition updated",
            extra={
                "event": "activity_definition.updated",
                "activity_definition_id": activity_definition_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_activity_definition(
        self, activity_definition_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.activity_definition_belongs_to_org(
            activity_definition_id, org_id
        ):
            self._log_org_scope_miss("delete", activity_definition_id, org_id)
            raise NotFoundError("ActivityDefinition not found")
        deleted = await self.repository.delete(activity_definition_id)
        if not deleted:
            raise NotFoundError("ActivityDefinition not found")
        logger.info(
            "ActivityDefinition deleted",
            extra={
                "event": "activity_definition.deleted",
                "activity_definition_id": activity_definition_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource(
            "ActivityDefinition", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "ActivityDefinition failed base R4 validation",
                extra={"event": "activity_definition.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, activity_definition_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "ActivityDefinition write rejected by org scope",
            extra={
                "event": "activity_definition.org_scope_miss",
                "operation": operation,
                "activity_definition_id": activity_definition_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
