from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.plan_definition import (
    merge_patch_fragment,
    patch_fragment_to_fhir_plan_definition,
    payload_to_fhir_plan_definition,
    to_fhir_plan_definition,
    to_plain_plan_definition,
)
from app.fhir.validation import validate_resource
from app.models.plan_definition import PlanDefinitionModel
from app.repository.plan_definition import PlanDefinitionRepository
from app.schemas.plan_definition import (
    PlanDefinitionCreateSchema,
    PlanDefinitionPatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All PlanDefinition business logic."""

    def __init__(self, repository: PlanDefinitionRepository):
        self.repository = repository

    def _to_fhir(self, plan_definition: PlanDefinitionModel) -> dict:
        return to_fhir_plan_definition(plan_definition)

    def _to_plain(self, plan_definition: PlanDefinitionModel) -> dict:
        return to_plain_plan_definition(plan_definition)

    async def get_plan_definition_scoped(
        self, plan_definition_id: int, org_id: str | None
    ) -> PlanDefinitionModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "PlanDefinition operation requires an org-scoped token"
            )
        plan_definition = (
            await self.repository.get_by_plan_definition_id_in_org(
                plan_definition_id, org_id
            )
        )
        if not plan_definition:
            raise NotFoundError("PlanDefinition not found")
        return plan_definition

    async def get_plan_definition(
        self, plan_definition_id: int, org_id: str | None = None
    ) -> PlanDefinitionModel:
        return await self.get_plan_definition_scoped(plan_definition_id, org_id)

    async def list_plan_definitions(
        self,
        org_id: str | None = None,
        name: str | None = None,
        title: str | None = None,
        status: str | None = None,
        url: str | None = None,
        version: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[PlanDefinitionModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "PlanDefinition operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            name=name,
            title=title,
            status=status,
            url=url,
            version=version,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_plan_definition(
        self,
        payload: PlanDefinitionCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> PlanDefinitionModel:
        if not org_id:
            raise PermissionDeniedError(
                "PlanDefinition creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "PlanDefinition creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_plan_definition(payload), org_id
        )
        pd = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "PlanDefinition created",
            extra={
                "event": "plan_definition.created",
                "plan_definition_id": pd.plan_definition_id,
            },
        )
        return pd

    async def patch_plan_definition(
        self,
        plan_definition_id: int,
        payload: PlanDefinitionPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> PlanDefinitionModel:
        if not org_id:
            self._log_org_scope_miss("patch", plan_definition_id, org_id)
            raise NotFoundError("PlanDefinition not found")
        existing = await self.repository.get_by_plan_definition_id_in_org(
            plan_definition_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", plan_definition_id, org_id)
            raise NotFoundError("PlanDefinition not found")

        fragment, touched = patch_fragment_to_fhir_plan_definition(payload)
        merged = merge_patch_fragment(
            to_fhir_plan_definition(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            plan_definition_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("PlanDefinition not found")
        logger.info(
            "PlanDefinition updated",
            extra={
                "event": "plan_definition.updated",
                "plan_definition_id": plan_definition_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_plan_definition(
        self, plan_definition_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.plan_definition_belongs_to_org(
            plan_definition_id, org_id
        ):
            self._log_org_scope_miss("delete", plan_definition_id, org_id)
            raise NotFoundError("PlanDefinition not found")
        deleted = await self.repository.delete(plan_definition_id)
        if not deleted:
            raise NotFoundError("PlanDefinition not found")
        logger.info(
            "PlanDefinition deleted",
            extra={
                "event": "plan_definition.deleted",
                "plan_definition_id": plan_definition_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource(
            "PlanDefinition", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "PlanDefinition failed base R4 validation",
                extra={"event": "plan_definition.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, plan_definition_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "PlanDefinition write rejected by org scope",
            extra={
                "event": "plan_definition.org_scope_miss",
                "operation": operation,
                "plan_definition_id": plan_definition_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
