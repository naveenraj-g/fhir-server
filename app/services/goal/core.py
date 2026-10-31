from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.goal import (
    merge_patch_fragment,
    patch_fragment_to_fhir_goal,
    payload_to_fhir_goal,
    to_fhir_goal,
    to_plain_goal,
)
from app.fhir.validation import validate_resource
from app.models.goal import GoalModel
from app.repository.goal import GoalRepository
from app.schemas.goal import GoalCreateSchema, GoalPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Goal business logic."""

    def __init__(self, repository: GoalRepository):
        self.repository = repository

    def _to_fhir(self, model: GoalModel) -> dict:
        return to_fhir_goal(model)

    def _to_plain(self, model: GoalModel) -> dict:
        return to_plain_goal(model)

    async def get_goal_scoped(
        self, goal_id: int, org_id: str | None
    ) -> GoalModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Goal operation requires an org-scoped token"
            )
        model = await self.repository.get_by_goal_id_in_org(goal_id, org_id)
        if not model:
            raise NotFoundError("Goal not found")
        return model

    async def list_goals(
        self,
        org_id: str | None = None,
        subject: str | None = None,
        lifecycle_status: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[int, list[GoalModel]]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "Goal operation requires an org-scoped token"
            )
        items, total = await self.repository.list(
            org_id=org_id,
            subject=subject,
            lifecycle_status=lifecycle_status,
            limit=limit,
            offset=offset,
            sort=sort,
        )
        return total, items

    async def create_goal(
        self,
        payload: GoalCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> GoalModel:
        if not org_id:
            raise PermissionDeniedError(
                "Goal creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "Goal creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_goal(payload), org_id
        )

        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "Goal created",
            extra={
                "event": "goal.created",
                "goal_id": model.goal_id,
            },
        )
        return model

    async def patch_goal(
        self,
        goal_id: int,
        payload: GoalPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> GoalModel:
        if not org_id:
            self._log_org_scope_miss("patch", goal_id, org_id)
            raise NotFoundError("Goal not found")
        existing = await self.repository.get_by_goal_id_in_org(goal_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", goal_id, org_id)
            raise NotFoundError("Goal not found")

        if not updated_by:
            raise PermissionDeniedError(
                "Goal modification requires an authenticated actor"
            )

        fragment, touched = patch_fragment_to_fhir_goal(payload)
        current_fhir = self._to_fhir(existing)
        merged = merge_patch_fragment(current_fhir, fragment, touched)
        await self._validate_base_r4(merged, org_id)

        model = await self.repository.patch_full(
            goal_id, payload, org_id=org_id, updated_by=updated_by
        )
        logger.info(
            "Goal patched",
            extra={
                "event": "goal.patched",
                "goal_id": goal_id,
            },
        )
        return model

    async def delete_goal(
        self, goal_id: int, org_id: str | None = None
    ) -> None:
        if not org_id:
            self._log_org_scope_miss("delete", goal_id, org_id)
            raise NotFoundError("Goal not found")
        if not await self.repository.goal_belongs_to_org(
            goal_id, org_id
        ):
            self._log_org_scope_miss("delete", goal_id, org_id)
            raise NotFoundError("Goal not found")
        deleted = await self.repository.delete(goal_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("Goal not found")
        logger.info(
            "Goal deleted",
            extra={
                "event": "goal.deleted",
                "goal_id": goal_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "Goal", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "Goal failed base R4 validation",
                extra={
                    "event": "goal.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, goal_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "Goal write rejected by org scope",
            extra={
                "event": "goal.org_scope_miss",
                "operation": operation,
                "goal_id": goal_id,
                "org_id": org_id,
            },
        )


class GoalService(_CoreMixin):
    """Service orchestrating Goal operations."""
    pass
