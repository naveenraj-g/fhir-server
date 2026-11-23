from app.core.config import settings
from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.datatypes import merge_patch_fragment
from app.fhir.input_payload import fhir_create_document, fhir_patch_fragment
from app.fhir.mappers.questionnaire_response import to_fhir_questionnaire_response
from app.fhir.search import SearchContext, SearchRequest, parse_search
from app.fhir.validation import validate_resource
from app.models.questionnaire_response import QuestionnaireResponseModel
from app.repository.questionnaire_response import QuestionnaireResponseRepository
from app.repository.questionnaire_response.search import questionnaire_response_search
from app.schemas.questionnaire_response import (
    QuestionnaireResponseCreateSchema,
    QuestionnaireResponsePatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All QuestionnaireResponse business logic. Like Organization, create/patch take
    a FHIR R4 QuestionnaireResponse as the request body and store it whole — see
    QuestionnaireResponseCreateSchema's docstring. Auth is identical: org_id comes
    from the verified JWT's activeOrganizationId claim (actor.org_id), never
    a client-suppliable field, and there's no org-less/super-admin bypass."""

    def __init__(self, repository: QuestionnaireResponseRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, questionnaire_response: QuestionnaireResponseModel) -> dict:
        return to_fhir_questionnaire_response(questionnaire_response)

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
        questionnaire_response = (
            await self.repository.get_by_questionnaire_response_id_in_org(
                questionnaire_response_id, org_id
            )
        )
        if not questionnaire_response:
            raise NotFoundError("QuestionnaireResponse not found")
        return questionnaire_response

    async def search_questionnaire_responses(
        self,
        query: list[tuple[str, str]],
        org_id: str | None,
        *,
        strict: bool = False,
        fhir_base: str | None = None,
    ) -> tuple[
        SearchRequest,
        list[QuestionnaireResponseModel],
        int | None,
        list[QuestionnaireResponseModel],
    ]:
        """FHIR R4 search. `query` is the raw (key, value) parameter list
        — parsed and validated here against the QuestionnaireResponse search
        registry (SearchError -> 400 OperationOutcome). `strict` is
        `Prefer: handling=strict`. Raises PermissionDeniedError (403) for an
        org-less token — same invariant as get_questionnaire_response_scoped().

        Returns (parsed request, matches, total, included (type, row))."""
        if not org_id:
            raise PermissionDeniedError(
                "QuestionnaireResponse operation requires an org-scoped token"
            )
        request = parse_search(
            query,
            questionnaire_response_search(),
            strict=strict,
            default_count=settings.pagination.default_limit,
            max_count=settings.pagination.max_limit,
        )
        ctx = SearchContext(tenant_id=org_id, fhir_base=fhir_base)
        rows, total, included = await self.repository.search(request, ctx)
        return request, rows, total, included

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_questionnaire_response(
        self,
        payload: QuestionnaireResponseCreateSchema,
        org_id: str | None,
        created_by: str | None,
        body: dict | None = None,
    ) -> QuestionnaireResponseModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a QuestionnaireResponse at all.

        `body` is the raw request JSON, which is what base R4 validation
        checks (see app.fhir.input_payload); falls back to the parsed
        payload for internal callers that have no raw body."""
        if not org_id:
            raise PermissionDeniedError(
                "QuestionnaireResponse creation requires an org-scoped token"
            )
        # The body is already a FHIR QuestionnaireResponse — validate it as sent,
        # then store exactly that document.
        document = fhir_create_document(
            self._raw(payload, body), "QuestionnaireResponse"
        )
        await self._validate_base_r4(document, org_id)
        questionnaire_response = await self.repository.create_full(
            document, org_id, created_by
        )
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
        body: dict | None = None,
    ) -> QuestionnaireResponseModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a questionnaire_response belonging to a different org both
        raise NotFoundError (404), never 403, so existence isn't leaked.

        The current row is fetched (rather than a lightweight existence
        check) because base R4 validation needs it: a PATCH payload is
        partial by nature, so it's merged onto the resource's current full
        FHIR representation before validating — see
        app.fhir.input_payload.fhir_patch_fragment()."""
        if not org_id:
            self._log_org_scope_miss("patch", questionnaire_response_id, org_id)
            raise NotFoundError("QuestionnaireResponse not found")
        existing = await self.repository.get_by_questionnaire_response_id_in_org(
            questionnaire_response_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", questionnaire_response_id, org_id)
            raise NotFoundError("QuestionnaireResponse not found")

        fragment, touched = fhir_patch_fragment(self._raw(payload, body))
        merged = merge_patch_fragment(
            to_fhir_questionnaire_response(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        # `merged` — the resource as it will look after this patch — is what
        # was just validated, and exactly what gets stored.
        updated = await self.repository.patch_full(
            questionnaire_response_id, merged, updated_by
        )
        if not updated:
            raise NotFoundError("QuestionnaireResponse not found")
        logger.info(
            "QuestionnaireResponse updated",
            extra={
                "event": "questionnaire_response.updated",
                "questionnaire_response_id": questionnaire_response_id,
                "fields": sorted(touched),
            },
        )
        return updated

    async def delete_questionnaire_response(
        self, questionnaire_response_id: int, org_id: str | None = None
    ) -> None:
        """Same org_id ownership gate as patch_questionnaire_response."""
        if (
            not org_id
            or not await self.repository.questionnaire_response_belongs_to_org(
                questionnaire_response_id, org_id
            )
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
    def _raw(payload, body: dict | None) -> dict:
        """The client's request JSON as sent; when there isn't one (an
        internal caller), the parsed payload's supplied fields instead."""
        if body is not None:
            return body
        return payload.model_dump(mode="json", exclude_unset=True, by_alias=True)

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        """Raises FhirValidationError (422) if `fhir_resource` fails
        validation against the most specific applicable layer of the
        base -> country -> organization profile chain (see
        docs/architecture/fhir-profiling-and-extensibility-strategy.md).
        Delegates to validate_resource(), which picks the actual backend
        (this project's own structural-only check, or the HL7 Java validator
        sidecar) per settings.fhir_validation.backend — see
        OrganizationService._validate_base_r4 for the full note."""
        errors = await validate_resource(
            "QuestionnaireResponse", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "QuestionnaireResponse failed base R4 validation",
                extra={
                    "event": "questionnaire_response.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(
        operation: str, questionnaire_response_id: int, org_id: str | None
    ) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such questionnaire_response" — so this
        log line is the only place the distinction is recorded. Worth WARNING
        because a repeated cross-org miss is a very different signal from a
        typo'd id."""
        logger.warning(
            "QuestionnaireResponse write rejected by org scope",
            extra={
                "event": "questionnaire_response.org_scope_miss",
                "operation": operation,
                "questionnaire_response_id": questionnaire_response_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
