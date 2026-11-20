from app.core.config import settings
from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.datatypes import merge_patch_fragment
from app.fhir.input_payload import fhir_create_document, fhir_patch_fragment
from app.fhir.mappers.immunization import to_fhir_immunization
from app.fhir.search import SearchContext, SearchRequest, parse_search
from app.fhir.validation import validate_resource
from app.models.immunization import ImmunizationModel
from app.repository.immunization import ImmunizationRepository
from app.repository.immunization.search import immunization_search
from app.schemas.immunization import ImmunizationCreateSchema, ImmunizationPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Immunization business logic. Like Organization, create/patch take
    a FHIR R4 Immunization as the request body and store it whole — see
    ImmunizationCreateSchema's docstring. Auth is identical: org_id comes
    from the verified JWT's activeOrganizationId claim (actor.org_id), never
    a client-suppliable field, and there's no org-less/super-admin bypass."""

    def __init__(self, repository: ImmunizationRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, immunization: ImmunizationModel) -> dict:
        return to_fhir_immunization(immunization)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_immunization_scoped(
        self, immunization_id: int, org_id: str | None
    ) -> ImmunizationModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Immunization operation requires an org-scoped token"
            )
        immunization = await self.repository.get_by_immunization_id_in_org(
            immunization_id, org_id
        )
        if not immunization:
            raise NotFoundError("Immunization not found")
        return immunization

    async def search_immunizations(
        self,
        query: list[tuple[str, str]],
        org_id: str | None,
        *,
        strict: bool = False,
        fhir_base: str | None = None,
    ) -> tuple[
        SearchRequest, list[ImmunizationModel], int | None, list[ImmunizationModel]
    ]:
        """FHIR R4 search. `query` is the raw (key, value) parameter list
        — parsed and validated here against the Immunization search
        registry (SearchError -> 400 OperationOutcome). `strict` is
        `Prefer: handling=strict`. Raises PermissionDeniedError (403) for an
        org-less token — same invariant as get_immunization_scoped().

        Returns (parsed request, matches, total, included (type, row))."""
        if not org_id:
            raise PermissionDeniedError(
                "Immunization operation requires an org-scoped token"
            )
        request = parse_search(
            query,
            immunization_search(),
            strict=strict,
            default_count=settings.pagination.default_limit,
            max_count=settings.pagination.max_limit,
        )
        ctx = SearchContext(tenant_id=org_id, fhir_base=fhir_base)
        rows, total, included = await self.repository.search(request, ctx)
        return request, rows, total, included

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_immunization(
        self,
        payload: ImmunizationCreateSchema,
        org_id: str | None,
        created_by: str | None,
        body: dict | None = None,
    ) -> ImmunizationModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create an Immunization at all.

        `body` is the raw request JSON, which is what base R4 validation
        checks (see app.fhir.input_payload); falls back to the parsed
        payload for internal callers that have no raw body."""
        if not org_id:
            raise PermissionDeniedError(
                "Immunization creation requires an org-scoped token"
            )
        # The body is already a FHIR Immunization — validate it as sent,
        # then store exactly that document.
        document = fhir_create_document(self._raw(payload, body), "Immunization")
        await self._validate_base_r4(document, org_id)
        immunization = await self.repository.create_full(document, org_id, created_by)
        logger.info(
            "Immunization created",
            extra={
                "event": "immunization.created",
                "immunization_id": immunization.immunization_id,
            },
        )
        return immunization

    async def patch_immunization(
        self,
        immunization_id: int,
        payload: ImmunizationPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
        body: dict | None = None,
    ) -> ImmunizationModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or an immunization belonging to a different org both
        raise NotFoundError (404), never 403, so existence isn't leaked.

        The current row is fetched (rather than a lightweight existence
        check) because base R4 validation needs it: a PATCH payload is
        partial by nature, so it's merged onto the resource's current full
        FHIR representation before validating — see
        app.fhir.input_payload.fhir_patch_fragment()."""
        if not org_id:
            self._log_org_scope_miss("patch", immunization_id, org_id)
            raise NotFoundError("Immunization not found")
        existing = await self.repository.get_by_immunization_id_in_org(
            immunization_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", immunization_id, org_id)
            raise NotFoundError("Immunization not found")

        fragment, touched = fhir_patch_fragment(self._raw(payload, body))
        merged = merge_patch_fragment(to_fhir_immunization(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        # `merged` — the resource as it will look after this patch — is what
        # was just validated, and exactly what gets stored.
        updated = await self.repository.patch_full(immunization_id, merged, updated_by)
        if not updated:
            raise NotFoundError("Immunization not found")
        logger.info(
            "Immunization updated",
            extra={
                "event": "immunization.updated",
                "immunization_id": immunization_id,
                "fields": sorted(touched),
            },
        )
        return updated

    async def delete_immunization(
        self, immunization_id: int, org_id: str | None = None
    ) -> None:
        """Same org_id ownership gate as patch_immunization."""
        if not org_id or not await self.repository.immunization_belongs_to_org(
            immunization_id, org_id
        ):
            self._log_org_scope_miss("delete", immunization_id, org_id)
            raise NotFoundError("Immunization not found")
        deleted = await self.repository.delete(immunization_id)
        if not deleted:
            raise NotFoundError("Immunization not found")
        logger.info(
            "Immunization deleted",
            extra={
                "event": "immunization.deleted",
                "immunization_id": immunization_id,
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
        errors = await validate_resource("Immunization", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Immunization failed base R4 validation",
                extra={"event": "immunization.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(
        operation: str, immunization_id: int, org_id: str | None
    ) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such immunization" — so this
        log line is the only place the distinction is recorded. Worth WARNING
        because a repeated cross-org miss is a very different signal from a
        typo'd id."""
        logger.warning(
            "Immunization write rejected by org scope",
            extra={
                "event": "immunization.org_scope_miss",
                "operation": operation,
                "immunization_id": immunization_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
