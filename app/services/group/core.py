from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.group import (
    merge_patch_fragment,
    patch_fragment_to_fhir_group,
    payload_to_fhir_group,
    to_fhir_group,
    to_plain_group,
)
from app.fhir.validation import validate_resource
from app.models.group import GroupModel, GroupType
from app.repository.group import GroupRepository
from app.schemas.group import GroupCreateSchema, GroupPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Group business logic."""

    def __init__(self, repository: GroupRepository):
        self.repository = repository

    def _to_fhir(self, group: GroupModel) -> dict:
        return to_fhir_group(group)

    def _to_plain(self, group: GroupModel) -> dict:
        return to_plain_group(group)

    async def get_group_scoped(
        self, group_id: int, org_id: str | None
    ) -> GroupModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError("Group operation requires an org-scoped token")
        group = await self.repository.get_by_group_id_in_org(group_id, org_id)
        if not group:
            raise NotFoundError("Group not found")
        return group

    async def list_groups(
        self,
        org_id: str | None = None,
        type: str | GroupType | None = None,
        actual: bool | None = None,
        active: bool | None = None,
        name: str | None = None,
        code: str | None = None,
        managing_entity: str | None = None,
        member: str | None = None,
        characteristic: str | None = None,
        characteristic_value: str | None = None,
        exclude: bool | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[GroupModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError("Group operation requires an org-scoped token")
        return await self.repository.list(
            org_id=org_id,
            type=type,
            actual=actual,
            active=active,
            name=name,
            code=code,
            managing_entity=managing_entity,
            member=member,
            characteristic=characteristic,
            characteristic_value=characteristic_value,
            exclude=exclude,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_group(
        self,
        payload: GroupCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> GroupModel:
        if not org_id:
            raise PermissionDeniedError("Group creation requires an org-scoped token")
        if not created_by:
            raise PermissionDeniedError("Group creation requires an authenticated actor")

        await self._validate_base_r4(payload_to_fhir_group(payload), org_id)
        group = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "Group created",
            extra={"event": "group.created", "group_id": group.group_id},
        )
        return group

    async def patch_group(
        self,
        group_id: int,
        payload: GroupPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> GroupModel:
        if not org_id:
            self._log_org_scope_miss("patch", group_id, org_id)
            raise NotFoundError("Group not found")
        existing = await self.repository.get_by_group_id_in_org(group_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", group_id, org_id)
            raise NotFoundError("Group not found")

        fragment, touched = patch_fragment_to_fhir_group(payload)
        merged = merge_patch_fragment(to_fhir_group(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            group_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("Group not found")
        logger.info(
            "Group updated",
            extra={
                "event": "group.updated",
                "group_id": group_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_group(self, group_id: int, org_id: str | None = None) -> None:
        if not org_id or not await self.repository.group_belongs_to_org(group_id, org_id):
            self._log_org_scope_miss("delete", group_id, org_id)
            raise NotFoundError("Group not found")
        deleted = await self.repository.delete(group_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("Group not found")
        logger.info(
            "Group deleted",
            extra={"event": "group.deleted", "group_id": group_id},
        )

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource("Group", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Group failed base R4 validation",
                extra={"event": "group.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(operation: str, group_id: int, org_id: str | None) -> None:
        logger.warning(
            "Group write rejected by org scope",
            extra={
                "event": "group.org_scope_miss",
                "operation": operation,
                "group_id": group_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
