from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.flag import (
    merge_patch_fragment,
    patch_fragment_to_fhir_flag,
    payload_to_fhir_flag,
    to_fhir_flag,
    to_plain_flag,
)
from app.fhir.validation import validate_resource
from app.models.flag import FlagModel
from app.repository.flag import FlagRepository
from app.schemas.flag import FlagCreateSchema, FlagPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Flag business logic."""

    def __init__(self, repository: FlagRepository):
        self.repository = repository

    def _to_fhir(self, model: FlagModel) -> dict:
        return to_fhir_flag(model)

    def _to_plain(self, model: FlagModel) -> dict:
        return to_plain_flag(model)

    async def get_flag_scoped(
        self, flag_id: int, org_id: str | None
    ) -> FlagModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Flag operation requires an org-scoped token"
            )
        model = await self.repository.get_by_flag_id_in_org(flag_id, org_id)
        if not model:
            raise NotFoundError("Flag not found")
        return model

    async def list_flags(
        self,
        org_id: str | None = None,
        subject: str | None = None,
        status: str | None = None,
        encounter: str | None = None,
        author: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[int, list[FlagModel]]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "Flag operation requires an org-scoped token"
            )
        items, total = await self.repository.list(
            org_id=org_id,
            subject=subject,
            status=status,
            encounter=encounter,
            author=author,
            limit=limit,
            offset=offset,
            sort=sort,
        )
        return total, items

    async def create_flag(
        self,
        payload: FlagCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> FlagModel:
        if not org_id:
            raise PermissionDeniedError(
                "Flag creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "Flag creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_flag(payload), org_id
        )
        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "Flag created",
            extra={
                "event": "flag.created",
                "flag_id": model.flag_id,
            },
        )
        return model

    async def patch_flag(
        self,
        flag_id: int,
        payload: FlagPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> FlagModel:
        if not org_id:
            self._log_org_scope_miss("patch", flag_id, org_id)
            raise NotFoundError("Flag not found")
        existing = await self.repository.get_by_flag_id_in_org(flag_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", flag_id, org_id)
            raise NotFoundError("Flag not found")

        if not updated_by:
            raise PermissionDeniedError(
                "Flag update requires an authenticated actor"
            )

        fragment, touched = patch_fragment_to_fhir_flag(payload)
        merged = merge_patch_fragment(
            to_fhir_flag(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            flag_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("Flag not found")
        logger.info(
            "Flag updated",
            extra={
                "event": "flag.updated",
                "flag_id": flag_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_flag(
        self, flag_id: int, org_id: str | None = None
    ) -> None:
        if not org_id or not await self.repository.flag_belongs_to_org(
            flag_id, org_id
        ):
            self._log_org_scope_miss("delete", flag_id, org_id)
            raise NotFoundError("Flag not found")
        deleted = await self.repository.delete(flag_id, org_id=org_id)
        if not deleted:
            raise NotFoundError("Flag not found")
        logger.info(
            "Flag deleted",
            extra={
                "event": "flag.deleted",
                "flag_id": flag_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "Flag", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "Flag failed base R4 validation",
                extra={
                    "event": "flag.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, flag_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "Flag write rejected by org scope",
            extra={
                "event": "flag.org_scope_miss",
                "operation": operation,
                "flag_id": flag_id,
                "org_id": org_id,
            },
        )


class FlagService(_CoreMixin):
    """Service orchestrating Flag operations."""
    pass
