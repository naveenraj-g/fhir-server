from datetime import date, datetime

from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.family_member_history import (
    merge_patch_fragment,
    patch_fragment_to_fhir_family_member_history,
    payload_to_fhir_family_member_history,
    to_fhir_family_member_history,
    to_plain_family_member_history,
)
from app.fhir.validation import validate_resource
from app.models.family_member_history import (
    FamilyMemberHistoryModel,
    FamilyMemberHistoryStatus,
)
from app.repository.family_member_history import FamilyMemberHistoryRepository
from app.schemas.family_member_history import (
    FamilyMemberHistoryCreateSchema,
    FamilyMemberHistoryPatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All FamilyMemberHistory business logic."""

    def __init__(self, repository: FamilyMemberHistoryRepository):
        self.repository = repository

    def _to_fhir(self, model: FamilyMemberHistoryModel) -> dict:
        return to_fhir_family_member_history(model)

    def _to_plain(self, model: FamilyMemberHistoryModel) -> dict:
        return to_plain_family_member_history(model)

    async def get_family_member_history_scoped(
        self, family_member_history_id: int, org_id: str | None
    ) -> FamilyMemberHistoryModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "FamilyMemberHistory operation requires an org-scoped token"
            )
        model = await self.repository.get_by_family_member_history_id_in_org(
            family_member_history_id, org_id
        )
        if not model:
            raise NotFoundError("FamilyMemberHistory not found")
        return model

    async def list_family_member_histories(
        self,
        org_id: str | None = None,
        status: str | FamilyMemberHistoryStatus | None = None,
        patient: str | None = None,
        date_val: date | datetime | None = None,
        date_from: date | datetime | None = None,
        date_to: date | datetime | None = None,
        relationship: str | None = None,
        sex: str | None = None,
        code: str | None = None,
        identifier: str | None = None,
        instantiates: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[FamilyMemberHistoryModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "FamilyMemberHistory operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            status=status,
            patient=patient,
            date_val=date_val,
            date_from=date_from,
            date_to=date_to,
            relationship=relationship,
            sex=sex,
            code=code,
            identifier=identifier,
            instantiates=instantiates,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_family_member_history(
        self,
        payload: FamilyMemberHistoryCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> FamilyMemberHistoryModel:
        if not org_id:
            raise PermissionDeniedError(
                "FamilyMemberHistory creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "FamilyMemberHistory creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_family_member_history(payload), org_id
        )
        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "FamilyMemberHistory created",
            extra={
                "event": "family_member_history.created",
                "family_member_history_id": model.family_member_history_id,
            },
        )
        return model

    async def patch_family_member_history(
        self,
        family_member_history_id: int,
        payload: FamilyMemberHistoryPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> FamilyMemberHistoryModel:
        if not org_id:
            self._log_org_scope_miss("patch", family_member_history_id, org_id)
            raise NotFoundError("FamilyMemberHistory not found")
        existing = await self.repository.get_by_family_member_history_id_in_org(
            family_member_history_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", family_member_history_id, org_id)
            raise NotFoundError("FamilyMemberHistory not found")

        fragment, touched = patch_fragment_to_fhir_family_member_history(payload)
        merged = merge_patch_fragment(
            to_fhir_family_member_history(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            family_member_history_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("FamilyMemberHistory not found")
        logger.info(
            "FamilyMemberHistory updated",
            extra={
                "event": "family_member_history.updated",
                "family_member_history_id": family_member_history_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_family_member_history(
        self, family_member_history_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.family_member_history_belongs_to_org(
            family_member_history_id, org_id
        ):
            self._log_org_scope_miss("delete", family_member_history_id, org_id)
            raise NotFoundError("FamilyMemberHistory not found")
        deleted = await self.repository.delete(family_member_history_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("FamilyMemberHistory not found")
        logger.info(
            "FamilyMemberHistory deleted",
            extra={
                "event": "family_member_history.deleted",
                "family_member_history_id": family_member_history_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "FamilyMemberHistory", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "FamilyMemberHistory failed base R4 validation",
                extra={
                    "event": "family_member_history.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, family_member_history_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "FamilyMemberHistory write rejected by org scope",
            extra={
                "event": "family_member_history.org_scope_miss",
                "operation": operation,
                "family_member_history_id": family_member_history_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
