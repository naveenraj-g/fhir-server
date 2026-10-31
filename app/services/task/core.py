from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.task import (
    merge_patch_fragment,
    patch_fragment_to_fhir_task,
    payload_to_fhir_task,
    to_fhir_task,
    to_plain_task,
)
from app.fhir.validation import validate_resource
from app.models.task import TaskModel
from app.repository.task import TaskRepository
from app.schemas.task import TaskCreateSchema, TaskPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Task business logic."""

    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def _to_fhir(self, model: TaskModel) -> dict:
        return to_fhir_task(model)

    def _to_plain(self, model: TaskModel) -> dict:
        return to_plain_task(model)

    async def get_task_scoped(
        self, task_id: int, org_id: str | None
    ) -> TaskModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Task operation requires an org-scoped token"
            )
        model = await self.repository.get_by_task_id_in_org(task_id, org_id)
        if not model:
            raise NotFoundError("Task not found")
        return model

    async def list_tasks(
        self,
        org_id: str | None = None,
        status: str | None = None,
        intent: str | None = None,
        priority: str | None = None,
        focus: str | None = None,
        for_: str | None = None,
        owner: str | None = None,
        requester: str | None = None,
        encounter: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[int, list[TaskModel]]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "Task operation requires an org-scoped token"
            )
        items, total = await self.repository.list(
            org_id=org_id,
            status=status,
            intent=intent,
            priority=priority,
            focus=focus,
            for_=for_,
            owner=owner,
            requester=requester,
            encounter=encounter,
            limit=limit,
            offset=offset,
            sort=sort,
        )
        return total, items

    async def create_task(
        self,
        payload: TaskCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> TaskModel:
        if not org_id:
            raise PermissionDeniedError(
                "Task creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "Task creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_task(payload), org_id
        )
        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "Task created",
            extra={
                "event": "task.created",
                "task_id": model.task_id,
            },
        )
        return model

    async def patch_task(
        self,
        task_id: int,
        payload: TaskPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> TaskModel:
        if not org_id:
            self._log_org_scope_miss("patch", task_id, org_id)
            raise NotFoundError("Task not found")
        existing = await self.repository.get_by_task_id_in_org(task_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", task_id, org_id)
            raise NotFoundError("Task not found")

        if not updated_by:
            raise PermissionDeniedError(
                "Task modification requires an authenticated actor"
            )

        fragment, touched = patch_fragment_to_fhir_task(payload)
        current_fhir = self._to_fhir(existing)
        merged = merge_patch_fragment(current_fhir, fragment, touched)
        await self._validate_base_r4(merged, org_id)

        model = await self.repository.patch_full(
            task_id, payload, org_id=org_id, updated_by=updated_by
        )
        logger.info(
            "Task patched",
            extra={
                "event": "task.patched",
                "task_id": task_id,
            },
        )
        return model

    async def delete_task(
        self, task_id: int, org_id: str | None = None
    ) -> None:
        if not org_id:
            self._log_org_scope_miss("delete", task_id, org_id)
            raise NotFoundError("Task not found")
        if not await self.repository.task_belongs_to_org(
            task_id, org_id
        ):
            self._log_org_scope_miss("delete", task_id, org_id)
            raise NotFoundError("Task not found")
        deleted = await self.repository.delete(task_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("Task not found")
        logger.info(
            "Task deleted",
            extra={
                "event": "task.deleted",
                "task_id": task_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "Task", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "Task failed base R4 validation",
                extra={
                    "event": "task.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, task_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "Task write rejected by org scope",
            extra={
                "event": "task.org_scope_miss",
                "operation": operation,
                "task_id": task_id,
                "org_id": org_id,
            },
        )


class TaskService(_CoreMixin):
    """Service orchestrating Task operations."""
    pass
