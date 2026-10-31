from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.care_team import (
    merge_patch_fragment,
    patch_fragment_to_fhir_care_team,
    payload_to_fhir_care_team,
    to_fhir_care_team,
    to_plain_care_team,
)
from app.fhir.validation import validate_resource
from app.models.care_team import CareTeamModel
from app.repository.care_team import CareTeamRepository
from app.schemas.care_team import (
    CareTeamCreateSchema,
    CareTeamPatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All CareTeam business logic."""

    def __init__(self, repository: CareTeamRepository):
        self.repository = repository

    def _to_fhir(self, care_team: CareTeamModel) -> dict:
        return to_fhir_care_team(care_team)

    def _to_plain(self, care_team: CareTeamModel) -> dict:
        return to_plain_care_team(care_team)

    async def get_care_team_scoped(
        self, care_team_id: int, org_id: str | None
    ) -> CareTeamModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError("CareTeam operation requires an org-scoped token")
        care_team = await self.repository.get_by_care_team_id_in_org(
            care_team_id, org_id
        )
        if not care_team:
            raise NotFoundError("CareTeam not found")
        return care_team

    async def list_care_teams(
        self,
        org_id: str | None = None,
        status: str | None = None,
        name: str | None = None,
        category: str | None = None,
        subject: str | None = None,
        encounter: str | None = None,
        participant: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[CareTeamModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError("CareTeam operation requires an org-scoped token")
        return await self.repository.list(
            org_id=org_id,
            status=status,
            name=name,
            category=category,
            subject=subject,
            encounter=encounter,
            participant=participant,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_care_team(
        self,
        payload: CareTeamCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> CareTeamModel:
        if not org_id:
            raise PermissionDeniedError("CareTeam creation requires an org-scoped token")
        if not created_by:
            raise PermissionDeniedError("CareTeam creation requires an authenticated actor")

        await self._validate_base_r4(payload_to_fhir_care_team(payload), org_id)
        ct = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "CareTeam created",
            extra={"event": "care_team.created", "care_team_id": ct.care_team_id},
        )
        return ct

    async def patch_care_team(
        self,
        care_team_id: int,
        payload: CareTeamPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> CareTeamModel:
        if not org_id:
            self._log_org_scope_miss("patch", care_team_id, org_id)
            raise NotFoundError("CareTeam not found")
        existing = await self.repository.get_by_care_team_id_in_org(care_team_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", care_team_id, org_id)
            raise NotFoundError("CareTeam not found")

        fragment, touched = patch_fragment_to_fhir_care_team(payload)
        merged = merge_patch_fragment(to_fhir_care_team(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(
            care_team_id, payload, org_id, updated_by
        )
        if not updated:
            raise NotFoundError("CareTeam not found")
        logger.info(
            "CareTeam updated",
            extra={
                "event": "care_team.updated",
                "care_team_id": care_team_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_care_team(self, care_team_id: int, org_id: str | None = None) -> None:
        if not org_id or not await self.repository.care_team_belongs_to_org(care_team_id, org_id):
            self._log_org_scope_miss("delete", care_team_id, org_id)
            raise NotFoundError("CareTeam not found")
        deleted = await self.repository.delete(care_team_id)
        if not deleted:
            raise NotFoundError("CareTeam not found")
        logger.info(
            "CareTeam deleted",
            extra={"event": "care_team.deleted", "care_team_id": care_team_id},
        )

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource("CareTeam", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "CareTeam failed base R4 validation",
                extra={"event": "care_team.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(operation: str, care_team_id: int, org_id: str | None) -> None:
        logger.warning(
            "CareTeam write rejected by org scope",
            extra={
                "event": "care_team.org_scope_miss",
                "operation": operation,
                "care_team_id": care_team_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
