from app.core.logging import get_logger
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
    """All QuestionnaireResponse business logic. Default (gateway-trusted)
    pattern — NOT part of the JWT auth rollout: `tenant_id`/`user_id`/
    `created_by`/`updated_by` all come straight off the validated request
    payload or an explicit, gateway-forwarded query/path parameter, never
    a verified token. There is accordingly no org-scoped 404-vs-403
    distinction here — `resolve_questionnaire_response()`
    (app/deps/questionnaire_response_deps.py) is a plain load-by-public-ID
    dependency with no ownership check, same as every other default-
    pattern resource's deps."""

    def __init__(self, repository: QuestionnaireResponseRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, questionnaire_response: QuestionnaireResponseModel) -> dict:
        return to_fhir_questionnaire_response(questionnaire_response)

    def _to_plain(self, questionnaire_response: QuestionnaireResponseModel) -> dict:
        return to_plain_questionnaire_response(questionnaire_response)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_by_questionnaire_response_id(
        self, questionnaire_response_id: int
    ) -> QuestionnaireResponseModel:
        questionnaire_response = await self.repository.get_by_questionnaire_response_id(
            questionnaire_response_id
        )
        if not questionnaire_response:
            raise NotFoundError("QuestionnaireResponse not found")
        return questionnaire_response

    async def get_me(
        self,
        user_id: str,
        tenant_id: str | None = None,
        status: QuestionnaireResponseStatus | None = None,
        questionnaire: str | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[QuestionnaireResponseModel], int | None]:
        """Scopes list() to the gateway-forwarded `user_id` query param —
        the default-pattern counterpart of an auth-rollout resource's
        actor-derived `/me`."""
        return await self.repository.get_me(
            user_id=user_id,
            tenant_id=tenant_id,
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
        tenant_id: str | None = None,
        user_id: str | None = None,
        status: QuestionnaireResponseStatus | None = None,
        questionnaire: str | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[QuestionnaireResponseModel], int | None]:
        return await self.repository.list(
            tenant_id=tenant_id,
            user_id=user_id,
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
        self, payload: QuestionnaireResponseCreateSchema
    ) -> QuestionnaireResponseModel:
        await self._validate_base_r4(payload_to_fhir_questionnaire_response(payload), payload.tenant_id)
        questionnaire_response = await self.repository.create_full(payload)
        logger.info(
            "QuestionnaireResponse created",
            extra={
                "event": "questionnaire_response.created",
                "questionnaire_response_id": questionnaire_response.questionnaire_response_id,
            },
        )
        return questionnaire_response

    async def patch_questionnaire_response(
        self, questionnaire_response_id: int, payload: QuestionnaireResponsePatchSchema
    ) -> QuestionnaireResponseModel:
        """The current row is fetched (rather than a lightweight existence
        check) because base R4 validation needs it: a PATCH payload is
        partial by nature, so it's merged onto the resource's current
        full FHIR representation before validating."""
        existing = await self.repository.get_by_questionnaire_response_id(questionnaire_response_id)
        if not existing:
            raise NotFoundError("QuestionnaireResponse not found")

        fragment, touched = patch_fragment_to_fhir_questionnaire_response(payload)
        merged = merge_patch_fragment(to_fhir_questionnaire_response(existing), fragment, touched)
        await self._validate_base_r4(merged, existing.tenant_id)

        updated = await self.repository.patch_full(questionnaire_response_id, payload)
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

    async def delete_questionnaire_response(self, questionnaire_response_id: int) -> None:
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
