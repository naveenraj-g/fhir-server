from app.core.config import settings
from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.datatypes import merge_patch_fragment
from app.fhir.input_payload import fhir_create_document, fhir_patch_fragment
from app.fhir.mappers.questionnaire import to_fhir_questionnaire
from app.fhir.search import SearchContext, SearchRequest, parse_search
from app.fhir.validation import validate_resource
from app.models.questionnaire import QuestionnaireModel
from app.repository.questionnaire import QuestionnaireRepository
from app.repository.questionnaire.search import questionnaire_search
from app.schemas.questionnaire import (
    QuestionnaireCreateSchema,
    QuestionnairePatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All Questionnaire business logic. Like Organization, create/patch take
    a FHIR R4 Questionnaire as the request body and store it whole — see
    QuestionnaireCreateSchema's docstring. Auth is identical: org_id comes
    from the verified JWT's activeOrganizationId claim (actor.org_id), never
    a client-suppliable field, and there's no org-less/super-admin bypass."""

    def __init__(self, repository: QuestionnaireRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, questionnaire: QuestionnaireModel) -> dict:
        return to_fhir_questionnaire(questionnaire)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_questionnaire_scoped(
        self, questionnaire_id: int, org_id: str | None
    ) -> QuestionnaireModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Questionnaire operation requires an org-scoped token"
            )
        questionnaire = await self.repository.get_by_questionnaire_id_in_org(
            questionnaire_id, org_id
        )
        if not questionnaire:
            raise NotFoundError("Questionnaire not found")
        return questionnaire

    async def search_questionnaires(
        self,
        query: list[tuple[str, str]],
        org_id: str | None,
        *,
        strict: bool = False,
        fhir_base: str | None = None,
    ) -> tuple[
        SearchRequest, list[QuestionnaireModel], int | None, list[QuestionnaireModel]
    ]:
        """FHIR R4 search. `query` is the raw (key, value) parameter list
        — parsed and validated here against the Questionnaire search
        registry (SearchError -> 400 OperationOutcome). `strict` is
        `Prefer: handling=strict`. Raises PermissionDeniedError (403) for an
        org-less token — same invariant as get_questionnaire_scoped().

        Returns (parsed request, matches, total, included (type, row))."""
        if not org_id:
            raise PermissionDeniedError(
                "Questionnaire operation requires an org-scoped token"
            )
        request = parse_search(
            query,
            questionnaire_search(),
            strict=strict,
            default_count=settings.pagination.default_limit,
            max_count=settings.pagination.max_limit,
        )
        ctx = SearchContext(tenant_id=org_id, fhir_base=fhir_base)
        rows, total, included = await self.repository.search(request, ctx)
        return request, rows, total, included

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_questionnaire(
        self,
        payload: QuestionnaireCreateSchema,
        org_id: str | None,
        created_by: str | None,
        body: dict | None = None,
    ) -> QuestionnaireModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a Questionnaire at all.

        `body` is the raw request JSON, which is what base R4 validation
        checks (see app.fhir.input_payload); falls back to the parsed
        payload for internal callers that have no raw body."""
        if not org_id:
            raise PermissionDeniedError(
                "Questionnaire creation requires an org-scoped token"
            )
        # The body is already a FHIR Questionnaire — validate it as sent,
        # then store exactly that document.
        document = fhir_create_document(self._raw(payload, body), "Questionnaire")
        await self._validate_base_r4(document, org_id)
        questionnaire = await self.repository.create_full(document, org_id, created_by)
        logger.info(
            "Questionnaire created",
            extra={
                "event": "questionnaire.created",
                "questionnaire_id": questionnaire.questionnaire_id,
            },
        )
        return questionnaire

    async def patch_questionnaire(
        self,
        questionnaire_id: int,
        payload: QuestionnairePatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
        body: dict | None = None,
    ) -> QuestionnaireModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a questionnaire belonging to a different org both
        raise NotFoundError (404), never 403, so existence isn't leaked.

        The current row is fetched (rather than a lightweight existence
        check) because base R4 validation needs it: a PATCH payload is
        partial by nature, so it's merged onto the resource's current full
        FHIR representation before validating — see
        app.fhir.input_payload.fhir_patch_fragment()."""
        if not org_id:
            self._log_org_scope_miss("patch", questionnaire_id, org_id)
            raise NotFoundError("Questionnaire not found")
        existing = await self.repository.get_by_questionnaire_id_in_org(
            questionnaire_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", questionnaire_id, org_id)
            raise NotFoundError("Questionnaire not found")

        fragment, touched = fhir_patch_fragment(self._raw(payload, body))
        merged = merge_patch_fragment(
            to_fhir_questionnaire(existing), fragment, touched
        )
        await self._validate_base_r4(merged, org_id)

        # `merged` — the resource as it will look after this patch — is what
        # was just validated, and exactly what gets stored.
        updated = await self.repository.patch_full(questionnaire_id, merged, updated_by)
        if not updated:
            raise NotFoundError("Questionnaire not found")
        logger.info(
            "Questionnaire updated",
            extra={
                "event": "questionnaire.updated",
                "questionnaire_id": questionnaire_id,
                "fields": sorted(touched),
            },
        )
        return updated

    async def delete_questionnaire(
        self, questionnaire_id: int, org_id: str | None = None
    ) -> None:
        """Same org_id ownership gate as patch_questionnaire."""
        if not org_id or not await self.repository.questionnaire_belongs_to_org(
            questionnaire_id, org_id
        ):
            self._log_org_scope_miss("delete", questionnaire_id, org_id)
            raise NotFoundError("Questionnaire not found")
        deleted = await self.repository.delete(questionnaire_id)
        if not deleted:
            raise NotFoundError("Questionnaire not found")
        logger.info(
            "Questionnaire deleted",
            extra={
                "event": "questionnaire.deleted",
                "questionnaire_id": questionnaire_id,
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
        errors = await validate_resource("Questionnaire", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Questionnaire failed base R4 validation",
                extra={"event": "questionnaire.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(
        operation: str, questionnaire_id: int, org_id: str | None
    ) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such questionnaire" — so this
        log line is the only place the distinction is recorded. Worth WARNING
        because a repeated cross-org miss is a very different signal from a
        typo'd id."""
        logger.warning(
            "Questionnaire write rejected by org scope",
            extra={
                "event": "questionnaire.org_scope_miss",
                "operation": operation,
                "questionnaire_id": questionnaire_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
