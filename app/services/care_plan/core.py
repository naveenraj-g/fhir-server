from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.care_plan import (
    merge_patch_fragment,
    patch_fragment_to_fhir_care_plan,
    payload_to_fhir_care_plan,
    to_fhir_care_plan,
    to_plain_care_plan,
)
from app.fhir.validation import validate_resource
from app.models.care_plan import CarePlanModel
from app.repository.care_plan import CarePlanRepository
from app.schemas.care_plan import (
    CarePlanCreateSchema,
    CarePlanPatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All CarePlan business logic."""

    def __init__(self, repository: CarePlanRepository):
        self.repository = repository

    def _to_fhir(self, care_plan: CarePlanModel) -> dict:
        return to_fhir_care_plan(care_plan)

    def _to_plain(self, care_plan: CarePlanModel) -> dict:
        return to_plain_care_plan(care_plan)

    async def get_care_plan_scoped(
        self, care_plan_id: int, org_id: str | None
    ) -> CarePlanModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError("CarePlan operation requires an org-scoped token")
        care_plan = await self.repository.get_by_care_plan_id_in_org(
            care_plan_id, org_id
        )
        if not care_plan:
            raise NotFoundError("CarePlan not found")
        return care_plan

    async def list_care_plans(
        self,
        org_id: str | None = None,
        status: str | None = None,
        intent: str | None = None,
        title: str | None = None,
        category: str | None = None,
        subject: str | None = None,
        encounter: str | None = None,
        author: str | None = None,
        based_on: str | None = None,
        replaces: str | None = None,
        part_of: str | None = None,
        addresses: str | None = None,
        goal: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[CarePlanModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError("CarePlan operation requires an org-scoped token")
        return await self.repository.list(
            org_id=org_id,
            status=status,
            intent=intent,
            title=title,
            category=category,
            subject=subject,
            encounter=encounter,
            author=author,
            based_on=based_on,
            replaces=replaces,
            part_of=part_of,
            addresses=addresses,
            goal=goal,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_care_plan(
        self,
        payload: CarePlanCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> CarePlanModel:
        if not org_id:
            raise PermissionDeniedError("CarePlan creation requires an org-scoped token")
        if not created_by:
            raise PermissionDeniedError("CarePlan creation requires an authenticated actor")

        await self._validate_base_r4(payload_to_fhir_care_plan(payload), org_id)
        cp = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "CarePlan created",
            extra={"event": "care_plan.created", "care_plan_id": cp.care_plan_id},
        )
        return cp

    async def patch_care_plan(
        self,
        care_plan_id: int,
        payload: CarePlanPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> CarePlanModel:
        if not org_id:
            self._log_org_scope_miss("patch", care_plan_id, org_id)
            raise NotFoundError("CarePlan not found")
        existing = await self.repository.get_by_care_plan_id_in_org(care_plan_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", care_plan_id, org_id)
            raise NotFoundError("CarePlan not found")

        fragment, touched = patch_fragment_to_fhir_care_plan(payload)
        merged = merge_patch_fragment(to_fhir_care_plan(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            care_plan_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("CarePlan not found")
        logger.info(
            "CarePlan updated",
            extra={
                "event": "care_plan.updated",
                "care_plan_id": care_plan_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_care_plan(self, care_plan_id: int, org_id: str | None = None) -> None:
        if not org_id or not await self.repository.care_plan_belongs_to_org(care_plan_id, org_id):
            self._log_org_scope_miss("delete", care_plan_id, org_id)
            raise NotFoundError("CarePlan not found")
        deleted = await self.repository.delete(care_plan_id)
        if not deleted:
            raise NotFoundError("CarePlan not found")
        logger.info(
            "CarePlan deleted",
            extra={"event": "care_plan.deleted", "care_plan_id": care_plan_id},
        )

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource("CarePlan", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "CarePlan failed base R4 validation",
                extra={"event": "care_plan.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(operation: str, care_plan_id: int, org_id: str | None) -> None:
        logger.warning(
            "CarePlan write rejected by org scope",
            extra={
                "event": "care_plan.org_scope_miss",
                "operation": operation,
                "care_plan_id": care_plan_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
