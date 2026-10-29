from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.questionnaire_response import (
    merge_patch_fragment,
    patch_fragment_to_fhir_questionnaire_response,
    payload_to_fhir_questionnaire_response,
    to_fhir_questionnaire_response,
    to_plain_questionnaire_response,
)
from app.fhir.validation import validate_resource
from app.models.questionnaire_response import (
    QuestionnaireResponseModel,
    QuestionnaireResponseStatus as QuestionnaireResponseStatusModel,
)
from app.repository.questionnaire_response import QuestionnaireResponseRepository
from app.schemas.enums import QuestionnaireResponseStatus
from app.schemas.questionnaire_response import (
    QuestionnaireResponseCreateSchema,
    QuestionnaireResponsePatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All QuestionnaireResponse business logic. Auth matches
    Questionnaire: tenant scoping comes from the verified JWT's
    activeOrganizationId claim (actor.org_id), never a client-suppliable
    field, and there's no org-less/super-admin bypass — every operation
    requires an org-scoped actor. `user_id` is still a plain,
    gateway-forwarded field, so `get_me()` additionally scopes to the
    acting end-user."""

    def __init__(self, repository: QuestionnaireResponseRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, questionnaire_response: QuestionnaireResponseModel) -> dict:
        return to_fhir_questionnaire_response(questionnaire_response)

    def _to_plain(self, questionnaire_response: QuestionnaireResponseModel) -> dict:
        return to_plain_questionnaire_response(questionnaire_response)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_questionnaire_response_scoped(
        self, questionnaire_response_id: int, org_id: str | None
    ) -> QuestionnaireResponseModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "QuestionnaireResponse operation requires an org-scoped token"
            )
        questionnaire_response = await self.repository.get_by_questionnaire_response_id_in_org(
            questionnaire_response_id, org_id
        )
        if not questionnaire_response:
            raise NotFoundError("QuestionnaireResponse not found")
        return questionnaire_response

    async def get_me(
        self,
        user_id: str,
        org_id: str | None = None,
        status: QuestionnaireResponseStatus | None = None,
        questionnaire: str | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[QuestionnaireResponseModel], int | None]:
        """Scopes list() to the authenticated end-user's own user_id,
        always combined with the org-scoped actor's org_id."""
        if not org_id:
            raise PermissionDeniedError(
                "QuestionnaireResponse operation requires an org-scoped token"
            )
        return await self.repository.get_me(
            user_id=user_id,
            org_id=org_id,
            status=QuestionnaireResponseStatusModel[status.name] if status else None,
            questionnaire=questionnaire,
            subject=subject,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def list_questionnaire_responses(
        self,
        org_id: str | None = None,
        status: QuestionnaireResponseStatus | None = None,
        questionnaire: str | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[QuestionnaireResponseModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token — same
        invariant as get_questionnaire_response_scoped()."""
        if not org_id:
            raise PermissionDeniedError(
                "QuestionnaireResponse operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            status=QuestionnaireResponseStatusModel[status.name] if status else None,
            questionnaire=questionnaire,
            subject=subject,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_questionnaire_response(
        self,
        payload: QuestionnaireResponseCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> QuestionnaireResponseModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a QuestionnaireResponse at all."""
        if not org_id:
            raise PermissionDeniedError(
                "QuestionnaireResponse creation requires an org-scoped token"
            )
        await self._validate_base_r4(payload_to_fhir_questionnaire_response(payload), org_id)
        questionnaire_response = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "QuestionnaireResponse created",
            extra={
                "event": "questionnaire_response.created",
                "questionnaire_response_id": questionnaire_response.questionnaire_response_id,
            },
        )
        return questionnaire_response

    async def patch_questionnaire_response(
        self,
        questionnaire_response_id: int,
        payload: QuestionnaireResponsePatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> QuestionnaireResponseModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a resource belonging to a different org both
        raise NotFoundError (404), never 403, so existence isn't leaked.

        The current row is fetched (rather than a lightweight existence
        check) because base R4 validation needs it: a PATCH payload is
        partial by nature, so it's merged onto the resource's current
        full FHIR representation before validating."""
        if not org_id:
            self._log_org_scope_miss("patch", questionnaire_response_id, org_id)
            raise NotFoundError("QuestionnaireResponse not found")
        existing = await self.repository.get_by_questionnaire_response_id_in_org(
            questionnaire_response_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", questionnaire_response_id, org_id)
            raise NotFoundError("QuestionnaireResponse not found")

        fragment, touched = patch_fragment_to_fhir_questionnaire_response(payload)
        merged = merge_patch_fragment(to_fhir_questionnaire_response(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(questionnaire_response_id, payload, updated_by)
        if not updated:
            raise NotFoundError("QuestionnaireResponse not found")
        logger.info(
            "QuestionnaireResponse updated",
            extra={
                "event": "questionnaire_response.updated",
                "questionnaire_response_id": questionnaire_response_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_questionnaire_response(
        self, questionnaire_response_id: int, org_id: str | None = None
    ) -> None:
        """Same org_id ownership gate as patch_questionnaire_response."""
        if not org_id or not await self.repository.questionnaire_response_belongs_to_org(
            questionnaire_response_id, org_id
        ):
            self._log_org_scope_miss("delete", questionnaire_response_id, org_id)
            raise NotFoundError("QuestionnaireResponse not found")
        deleted = await self.repository.delete(questionnaire_response_id)
        if not deleted:
            raise NotFoundError("QuestionnaireResponse not found")
        logger.info(
            "QuestionnaireResponse deleted",
            extra={
                "event": "questionnaire_response.deleted",
                "questionnaire_response_id": questionnaire_response_id,
            },
        )

    # ── Validation helpers ────────────────────────────────────────────────

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource("QuestionnaireResponse", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "QuestionnaireResponse failed base R4 validation",
                extra={"event": "questionnaire_response.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(
        operation: str, questionnaire_response_id: int, org_id: str | None
    ) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such resource" — so this
        log line is the only place the distinction is recorded."""
        logger.warning(
            "QuestionnaireResponse write rejected by org scope",
            extra={
                "event": "questionnaire_response.org_scope_miss",
                "operation": operation,
                "questionnaire_response_id": questionnaire_response_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
