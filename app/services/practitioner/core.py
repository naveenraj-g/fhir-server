from app.core.config import settings
from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import BusinessRuleViolationError, NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.datatypes import merge_patch_fragment
from app.fhir.input_payload import fhir_create_document, fhir_patch_fragment
from app.fhir.mappers.practitioner import to_fhir_practitioner
from app.fhir.search import SearchContext, SearchRequest, parse_search
from app.fhir.validation import validate_resource
from app.models.practitioner import PractitionerModel
from app.repository.practitioner import PractitionerRepository
from app.repository.practitioner._indexer import user_id_of
from app.repository.practitioner.search import practitioner_search
from app.schemas.practitioner import PractitionerCreateSchema, PractitionerPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Practitioner business logic. Like Organization, create/patch take
    a FHIR R4 Practitioner as the request body and store it whole — see
    PractitionerCreateSchema's docstring. Auth is identical: org_id comes
    from the verified JWT's activeOrganizationId claim (actor.org_id), never
    a client-suppliable field, and there's no org-less/super-admin bypass.

    Unlike Organization, a Practitioner belongs to an individual end-user
    (`user_id`, carried as the user-id extension — see PractitionerModel),
    which scopes the `/me` search and is immutable after create."""

    def __init__(self, repository: PractitionerRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, practitioner: PractitionerModel) -> dict:
        return to_fhir_practitioner(practitioner)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_practitioner_scoped(
        self, practitioner_id: int, org_id: str | None
    ) -> PractitionerModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Practitioner operation requires an org-scoped token"
            )
        practitioner = await self.repository.get_by_practitioner_id_in_org(
            practitioner_id, org_id
        )
        if not practitioner:
            raise NotFoundError("Practitioner not found")
        return practitioner

    async def search_practitioners(
        self,
        query: list[tuple[str, str]],
        org_id: str | None,
        *,
        strict: bool = False,
        fhir_base: str | None = None,
        user_id: str | None = None,
    ) -> tuple[
        SearchRequest, list[PractitionerModel], int | None, list[PractitionerModel]
    ]:
        """FHIR R4 search. `query` is the raw (key, value) parameter list
        — parsed and validated here against the Practitioner search
        registry (SearchError -> 400 OperationOutcome). `strict` is
        `Prefer: handling=strict`. `user_id` (the `/me` route) additionally
        restricts the result to that end-user's own records. Raises
        PermissionDeniedError (403) for an org-less token — same invariant
        as get_practitioner_scoped().

        Returns (parsed request, matches, total, included (type, row))."""
        if not org_id:
            raise PermissionDeniedError(
                "Practitioner operation requires an org-scoped token"
            )
        request = parse_search(
            query,
            practitioner_search(),
            strict=strict,
            default_count=settings.pagination.default_limit,
            max_count=settings.pagination.max_limit,
        )
        ctx = SearchContext(tenant_id=org_id, fhir_base=fhir_base)
        rows, total, included = await self.repository.search(
            request, ctx, user_id=user_id
        )
        return request, rows, total, included

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_practitioner(
        self,
        payload: PractitionerCreateSchema,
        org_id: str | None,
        created_by: str | None,
        body: dict | None = None,
    ) -> PractitionerModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a Practitioner at all.

        `body` is the raw request JSON, which is what base R4 validation
        checks (see app.fhir.input_payload); falls back to the parsed
        payload for internal callers that have no raw body."""
        if not org_id:
            raise PermissionDeniedError(
                "Practitioner creation requires an org-scoped token"
            )
        # The body is already a FHIR Practitioner — validate it as sent,
        # then store exactly that document.
        document = fhir_create_document(self._raw(payload, body), "Practitioner")
        await self._validate_base_r4(document, org_id)
        practitioner = await self.repository.create_full(document, org_id, created_by)
        logger.info(
            "Practitioner created",
            extra={
                "event": "practitioner.created",
                "practitioner_id": practitioner.practitioner_id,
            },
        )
        return practitioner

    async def patch_practitioner(
        self,
        practitioner_id: int,
        payload: PractitionerPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
        body: dict | None = None,
    ) -> PractitionerModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a practitioner belonging to a different org both
        raise NotFoundError (404), never 403, so existence isn't leaked.

        The current row is fetched (rather than a lightweight existence
        check) because base R4 validation needs it: a PATCH payload is
        partial by nature, so it's merged onto the resource's current full
        FHIR representation before validating — see
        app.fhir.input_payload.fhir_patch_fragment()."""
        if not org_id:
            self._log_org_scope_miss("patch", practitioner_id, org_id)
            raise NotFoundError("Practitioner not found")
        existing = await self.repository.get_by_practitioner_id_in_org(
            practitioner_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", practitioner_id, org_id)
            raise NotFoundError("Practitioner not found")

        fragment, touched = fhir_patch_fragment(self._raw(payload, body))
        merged = merge_patch_fragment(to_fhir_practitioner(existing), fragment, touched)
        # user_id is immutable after create: a patch may not add, change or
        # drop the user-id extension.
        if user_id_of(merged) != existing.user_id:
            raise BusinessRuleViolationError(
                "The end-user id (user-id extension) is immutable after create."
            )
        await self._validate_base_r4(merged, org_id)

        # `merged` — the resource as it will look after this patch — is what
        # was just validated, and exactly what gets stored.
        updated = await self.repository.patch_full(practitioner_id, merged, updated_by)
        if not updated:
            raise NotFoundError("Practitioner not found")
        logger.info(
            "Practitioner updated",
            extra={
                "event": "practitioner.updated",
                "practitioner_id": practitioner_id,
                "fields": sorted(touched),
            },
        )
        return updated

    async def delete_practitioner(
        self, practitioner_id: int, org_id: str | None = None
    ) -> None:
        """Same org_id ownership gate as patch_practitioner."""
        if not org_id or not await self.repository.practitioner_belongs_to_org(
            practitioner_id, org_id
        ):
            self._log_org_scope_miss("delete", practitioner_id, org_id)
            raise NotFoundError("Practitioner not found")
        deleted = await self.repository.delete(practitioner_id)
        if not deleted:
            raise NotFoundError("Practitioner not found")
        logger.info(
            "Practitioner deleted",
            extra={
                "event": "practitioner.deleted",
                "practitioner_id": practitioner_id,
            },
        )

    # ── Validation helpers ────────────────────────────────────────────────

    @staticmethod
    def _raw(payload, body: dict | None) -> dict:
        """The client's request JSON as sent; when there isn't one (an
        internal caller), the parsed payload's supplied fields instead."""
        if body is not None:
            return body
        return payload.model_dump(mode="json", exclude_unset=True)

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
        errors = await validate_resource("Practitioner", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Practitioner failed base R4 validation",
                extra={"event": "practitioner.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(
        operation: str, practitioner_id: int, org_id: str | None
    ) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such practitioner" — so this
        log line is the only place the distinction is recorded. Worth WARNING
        because a repeated cross-org miss is a very different signal from a
        typo'd id."""
        logger.warning(
            "Practitioner write rejected by org scope",
            extra={
                "event": "practitioner.org_scope_miss",
                "operation": operation,
                "practitioner_id": practitioner_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
