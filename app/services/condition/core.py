from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.condition import (
    merge_patch_fragment,
    patch_fragment_to_fhir_condition,
    payload_to_fhir_condition,
    to_fhir_condition,
    to_plain_condition,
)
from app.fhir.validation import validate_resource
from app.models.condition import ConditionModel
from app.repository.condition import ConditionRepository
from app.schemas.condition import ConditionCreateSchema, ConditionPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Condition business logic."""

    def __init__(self, repository: ConditionRepository):
        self.repository = repository

    def _to_fhir(self, condition: ConditionModel) -> dict:
        return to_fhir_condition(condition)

    def _to_plain(self, condition: ConditionModel) -> dict:
        return to_plain_condition(condition)

    async def get_condition_scoped(
        self, condition_id: int, org_id: str | None
    ) -> ConditionModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError("Condition operation requires an org-scoped token")
        condition = await self.repository.get_by_condition_id_in_org(condition_id, org_id)
        if not condition:
            raise NotFoundError("Condition not found")
        return condition

    async def list_conditions(
        self,
        org_id: str | None = None,
        clinical_status: str | None = None,
        verification_status: str | None = None,
        category: str | None = None,
        severity: str | None = None,
        code: str | None = None,
        subject: str | None = None,
        encounter: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ConditionModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError("Condition operation requires an org-scoped token")
        return await self.repository.list(
            org_id=org_id,
            clinical_status=clinical_status,
            verification_status=verification_status,
            category=category,
            severity=severity,
            code=code,
            subject=subject,
            encounter=encounter,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_condition(
        self,
        payload: ConditionCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> ConditionModel:
        if not org_id:
            raise PermissionDeniedError("Condition creation requires an org-scoped token")
        if not created_by:
            raise PermissionDeniedError("Condition creation requires an authenticated actor")

        await self._validate_base_r4(payload_to_fhir_condition(payload), org_id)
        condition = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "Condition created",
            extra={"event": "condition.created", "condition_id": condition.condition_id},
        )
        return condition

    async def patch_condition(
        self,
        condition_id: int,
        payload: ConditionPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> ConditionModel:
        if not org_id:
            self._log_org_scope_miss("patch", condition_id, org_id)
            raise NotFoundError("Condition not found")
        existing = await self.repository.get_by_condition_id_in_org(condition_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", condition_id, org_id)
            raise NotFoundError("Condition not found")

        fragment, touched = patch_fragment_to_fhir_condition(payload)
        merged = merge_patch_fragment(to_fhir_condition(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            condition_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("Condition not found")
        logger.info(
            "Condition updated",
            extra={
                "event": "condition.updated",
                "condition_id": condition_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_condition(self, condition_id: int, org_id: str | None = None) -> None:
        if not org_id or not await self.repository.condition_belongs_to_org(condition_id, org_id):
            self._log_org_scope_miss("delete", condition_id, org_id)
            raise NotFoundError("Condition not found")
        deleted = await self.repository.delete(condition_id)
        if not deleted:
            raise NotFoundError("Condition not found")
        logger.info(
            "Condition deleted",
            extra={"event": "condition.deleted", "condition_id": condition_id},
        )

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource("Condition", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Condition failed base R4 validation",
                extra={"event": "condition.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(operation: str, condition_id: int, org_id: str | None) -> None:
        logger.warning(
            "Condition write rejected by org scope",
            extra={
                "event": "condition.org_scope_miss",
                "operation": operation,
                "condition_id": condition_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
